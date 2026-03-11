import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
from dash import dash_table
import pandas as pd
import datetime as dt
import pyodbc
import os
import time
import base64
import threading as _threading
from azure.storage.blob import BlobServiceClient
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv

load_dotenv('secrets.env')

server   = os.environ.get('server_name')
database = os.environ.get('db_name')
username = os.environ.get('db_username')
password = os.environ.get('db_password')
conn_str = os.environ.get('conn_str')

# =============================================================================
# SQL QUERIES  (defined first — background thread references these)
# =============================================================================
query1 = "SELECT * from vw_wellness_enrollee_portal_update"
query2 = (
    "select MemberNo, MemberName, Client, PolicyEndDate, email, state, selected_provider, "
    "Wellness_benefits, selected_date, selected_session, date_submitted, "
    "IssuedPACode, PA_Tests, PA_Provider, PAIssueDate "
    "FROM demo_tbl_annual_wellness_enrollee_data "
    "WHERE PolicyEndDate >= DATEADD(MONTH, -3, GETDATE())"
)
query3 = (
    "select a.*, name as ProviderName "
    "from updated_wellness_providers a "
    "left join [dbo].[tbl_ProviderList_stg] b on a.code = b.code"
)
query4 = (
    "SELECT r.* "
    "FROM demo_tbl_enrollee_wellness_result_data r "
    "INNER JOIN demo_tbl_annual_wellness_enrollee_data a ON r.memberno = a.memberno "
    "WHERE r.date_submitted < a.PolicyStartDate OR r.date_submitted > a.PolicyEndDate"
)

# =============================================================================
# DB + CACHE  (thread-safe, 5-min TTL, pre-warms at server startup)
# =============================================================================
_cache      = {}
_cache_lock = _threading.Lock()
_CACHE_TTL  = 300  # seconds

def get_conn():
    return pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};SERVER=' + server +
        ';DATABASE=' + database + ';UID=' + username + ';PWD=' + password
    )

def cached_read_sql(query, ttl=_CACHE_TTL):
    now = time.time()
    with _cache_lock:
        if query in _cache:
            df, ts = _cache[query]
            if now - ts < ttl:
                return df.copy()
    conn = get_conn()
    df = pd.read_sql(query, conn)
    conn.close()
    with _cache_lock:
        _cache[query] = (df, now)
    return df.copy()

def invalidate_cache():
    with _cache_lock:
        _cache.clear()

def _prewarm():
    """Mirrors Streamlit's @st.cache_data — runs all queries at server startup."""
    try:
        for q in [query1, query2, query3, query4]:
            cached_read_sql(q)
        print("[cache] Pre-warm complete.")
    except Exception as e:
        print(f"[cache] Pre-warm warning: {e}")

# Fire the moment the module loads — non-blocking
_threading.Thread(target=_prewarm, daemon=True).start()


# =============================================================================
# HELPERS
# =============================================================================
PA_TESTS_OPTIONS = [
    {'label': v, 'value': v} for v in [
        'Physical Exam','Urinalysis','PCV','Blood Sugar','BP','Genotype','BMI','ECG',
        'Visual Acuity','Chest X-Ray','Cholesterol','Liver Function Test',
        'Electrolyte, Urea and Creatinine Test(E/U/Cr)','Stool Microscopy','Mammogram',
        'Prostrate Specific Antigen(PSA)','Cervical Smear','Stress ECG','Hepatitis B',
        'Lipid Profile Test','Breast Scan','Prostrate Cancer Screening','Lung Function',
        'Cardiac Risk Assessment','Hearing Test','Mantoux Test',
        'Full Blood Count(FBC)','Hemoglobulin Test',
    ]
]

def login_user(username_val, password_val):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM tbl_provider_wellness_submission_portal_users WHERE code = ?",
        username_val
    )
    user = cursor.fetchone()
    conn.close()
    if user and password_val:
        return user[0], user[1], user[2]
    return None, None, None

def display_member_results(conn_str, container_name, selected_provider,
                            selected_client, selected_member, policy_end_date):
    try:
        bsc = BlobServiceClient.from_connection_string(conn_str)
        cc  = bsc.get_container_client(container_name)
        pf  = selected_provider.replace(" ", "").lower()
        cf  = selected_client.replace(" ", "").lower()
        ped = policy_end_date.strftime("%Y-%m-%d") if hasattr(policy_end_date, 'strftime') else str(policy_end_date)
        prefix = f"{pf}/{cf}/{ped}/{selected_member.strip()}"
        links = [
            html.A(b.name.split("/")[-1],
                   href=f"https://{bsc.account_name}.blob.core.windows.net/{container_name}/{b.name}",
                   target="_blank")
            for b in cc.list_blobs(name_starts_with=prefix)
        ]
        return html.Div(links) if links else html.Div("No test results found.", style={'color':'orange'})
    except Exception as e:
        return html.Div(f"Error: {e}", style={'color':'red'})

def send_email_with_attachment(recipient_email, enrollee_name, provider_name,
                                test_date, subject, uploaded_files,
                                bcc_email='ifeoluwa.adeniyi@avonhealthcare.com'):
    sender_email   = 'noreply@avonhealthcare.com'
    email_password = os.environ.get('email_password')
    recipient_email = 'ifeoluwa.adeniyi@avonhealthcare.com'  # test override
    body = f"""
        Dear {enrollee_name},<br><br>
        Trust this message meets you well.<br><br>
        Following your recent wellness test at {provider_name} on {test_date},
        please find attached the results of the wellness tests conducted on you.<br><br>
        You are advised to review the results and consult with your primary healthcare
        provider for further advice.<br><br>
        Best Regards,<br>AVON HMO Medical Services
    """
    try:
        s = smtplib.SMTP('smtp.office365.com', 587)
        s.starttls()
        s.login(sender_email, email_password)
        msg = MIMEMultipart()
        msg['From']    = 'AVON HMO Medical Services'
        msg['To']      = recipient_email
        msg['Bcc']     = bcc_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        for fn, fd in uploaded_files:
            p = MIMEBase('application', 'octet-stream')
            p.set_payload(fd)
            encoders.encode_base64(p)
            p.add_header('Content-Disposition', f'attachment; filename={fn}')
            msg.attach(p)
        s.sendmail(sender_email, [recipient_email], msg.as_string())
        s.quit()
        return True, "Email sent successfully."
    except Exception as e:
        return False, f"Email error: {e}"


# =============================================================================
# APP
# =============================================================================
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True
)
#server_wsgi = app.server
server = app.server

# =============================================================================
# LOADING SCREEN  (shown on portal entry while data loads into stores)
# =============================================================================
def loading_screen(title_text):
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.Br(), html.Br(),
                html.H4(title_text, className="text-center", style={"color": "purple"}),
                html.Br(),
                dbc.Spinner(size="lg", color="primary",
                            children=html.Div(style={"height": "60px"})),
                html.P("Loading portal data, please wait…",
                       className="text-center text-muted mt-3"),
            ], width={"size": 4, "offset": 4})
        ])
    ], fluid=True, style={"minHeight": "60vh", "paddingTop": "15vh"})


# =============================================================================
# PORTAL LAYOUTS
# =============================================================================
def _nav_card(body_children):
    return dbc.Card([dbc.CardHeader("Navigation"), dbc.CardBody(body_children)], className="mb-3")

login_layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.Br(), html.Br(), html.Br(), html.Br(),
            dbc.Card([
                dbc.CardBody([
                    html.H2("Provider Wellness Result Submission Portal", className="text-center mb-4"),
                    html.P("Login with your username and password to access the portal.",
                           className="text-center text-muted"),
                    html.Br(),
                    dbc.Label("Username"),
                    dbc.Input(id="login-username", type="text", placeholder="Enter username"),
                    html.Br(),
                    dbc.Label("Password"),
                    dbc.Input(id="login-password", type="password", placeholder="Enter password"),
                    html.Br(),
                    dbc.Button("Login", id="login-button", color="primary", className="w-100"),
                    html.Br(),
                    html.Div(id="login-error", className="text-danger text-center")
                ])
            ], className="shadow-lg")
        ], width={"size": 6, "offset": 3})
    ])
], fluid=True, style={"backgroundColor": "#f8f9fa", "minHeight": "100vh", "paddingTop": "50px"})

provider_layout = dbc.Container([
    dbc.Row([dbc.Col([
        html.H2("Provider Wellness Result Submission Portal", className="mt-3"),
        html.P(id="provider-welcome", className="text-muted"),
    ])]),
    dbc.Row([
        dbc.Col([_nav_card([
            html.P("Welcome to the Provider Wellness Result Submission Portal"),
            dbc.RadioItems(
                id="provider-nav-option",
                options=[
                    {"label": "View Wellness Enrollees and Benefits", "value": "view"},
                    {"label": "Submit Wellness Results",              "value": "submit"}
                ],
                value="view", inline=True
            ),
            html.Hr(),
            dbc.Button("Logout", id="logout-btn", color="danger", size="sm")
        ])], width=3),
        dbc.Col([html.Div(id="provider-content")], width=9)
    ])
], fluid=True)

claims_layout = dbc.Container([
    dbc.Row([dbc.Col([
        html.H2("Provider Wellness Result Review Portal",
                className="mt-3 text-center", style={"color": "purple"}),
        html.P(id="claims-welcome", className="text-center text-muted"),
    ])]),
    dbc.Row([
        dbc.Col([_nav_card([
            html.P("Welcome to the Provider Wellness Result Review Portal"),
            html.P("Please select a Provider to view Submitted Wellness Results"),
            dbc.Label("Select Provider", style={"color": "purple"}),
            dcc.Dropdown(id="claims-provider-select", placeholder="Select Provider"),
            html.Br(),
            dbc.Label("Select Member", style={"color": "purple"}),
            dcc.Dropdown(id="claims-member-select", placeholder="Select Member"),
            html.Hr(),
            dbc.Button("Logout", id="logout-btn", color="danger", size="sm")
        ])], width=3),
        dbc.Col([html.Div(id="claims-content")], width=9)
    ])
], fluid=True)

contact_layout = dbc.Container([
    dbc.Row([dbc.Col([
        html.H2("Wellness PA Code Authorisation and Results Review Portal",
                className="mt-3", style={"color": "purple"}),
        html.P(id="contact-welcome", className="text-muted"),
    ])]),
    dbc.Row([
        dbc.Col([_nav_card([
            html.P("Welcome to the Wellness PA Code Authorisation and Results Review Portal"),
            html.P("Kindly input Member ID to check Eligibility and Booking Status:",
                   style={"color": "purple"}),
            dbc.Input(id="contact-enrollee-id", type="text", placeholder="Enter Member ID here"),
            html.Br(),
            dbc.Button("Search", id="contact-search-button", color="primary"),
            html.Hr(),
            dbc.Button("Logout", id="logout-btn", color="danger", size="sm")
        ])], width=3),
        dbc.Col([
            dcc.Loading(type="default", children=html.Div(id="contact-content"))
        ], width=9)
    ])
], fluid=True)


# =============================================================================
# APP LAYOUT
# =============================================================================
app.layout = html.Div([
    dcc.Location(id="url", refresh=True),
    dcc.Store(id="auth-store", storage_type="session",
              data={"authenticated": False, "username": None, "providername": None}),
    # Triggers the data-load callback when set to False (portal entry)
    dcc.Store(id="data-ready-store", data=False),
    # Data stores populated once on portal entry — all callbacks read from these
    dcc.Store(id="store-q1", data=None),
    dcc.Store(id="store-q2", data=None),
    dcc.Store(id="store-q3", data=None),
    dcc.Store(id="store-q4", data=None),
    html.Div(id="main-content")
])


# =============================================================================
# CALLBACKS
# =============================================================================

# --- Step 1: Login — lightweight, no DB work ---
@app.callback(
    Output("auth-store",    "data"),
    Output("login-error",   "children"),
    Input("login-button",   "n_clicks"),
    State("login-username", "value"),
    State("login-password", "value"),
    prevent_initial_call=True,
)
def login(n_clicks, username_val, password_val):
    if n_clicks and username_val and password_val:
        user_name, providername, login_password = login_user(username_val, password_val)
        if user_name == username_val and password_val == login_password:
            return {"authenticated": True, "username": username_val, "providername": providername}, ""
        return dash.no_update, "Username/password is incorrect"
    return dash.no_update, ""


# --- Step 2: auth-store change → show loading screen (unauthenticated → login page) ---
@app.callback(
    Output("main-content", "children"),
    Input("auth-store",    "data"),
    prevent_initial_call=False,
)
def render_layout(auth_data):
    if not auth_data or not auth_data.get("authenticated", False):
        return login_layout

    u = auth_data.get("username", "")
    if u.startswith("234"):
        title = "Provider Wellness Result Submission Portal"
    elif u.startswith("claim"):
        title = "Provider Wellness Result Review Portal"
    elif u.startswith("contact"):
        title = "Wellness PA Code Authorisation and Results Review Portal"
    else:
        return login_layout

    # Show spinner while Step 3 fetches data
    return loading_screen(title)


# --- Step 3: auth-store authenticated → fetch all data into stores (spinner visible) ---
# Input is auth-store (not data-ready-store) to avoid circular trigger.
@app.callback(
    Output("store-q1",         "data"),
    Output("store-q2",         "data"),
    Output("store-q3",         "data"),
    Output("store-q4",         "data"),
    Output("data-ready-store", "data"),
    Input("auth-store",        "data"),
    prevent_initial_call=True,
)
def load_portal_data(auth_data):
    if not auth_data or not auth_data.get("authenticated"):
        # User logged out — clear stores and reset ready flag
        return None, None, None, None, False
    q1 = cached_read_sql(query1).to_dict('records')
    q2 = cached_read_sql(query2).to_dict('records')
    q3 = cached_read_sql(query3).to_dict('records')
    q4 = cached_read_sql(query4).to_dict('records')
    return q1, q2, q3, q4, True


# --- Step 4: data-ready-store=True → swap loading screen for real portal ---
@app.callback(
    Output("main-content",    "children", allow_duplicate=True),
    Input("data-ready-store", "data"),
    State("auth-store",       "data"),
    prevent_initial_call=True,
)
def show_portal(ready, auth_data):
    if not ready or not auth_data or not auth_data.get("authenticated"):
        return dash.no_update
    u = auth_data.get("username", "")
    if u.startswith("234"):
        return provider_layout
    elif u.startswith("claim"):
        return claims_layout
    elif u.startswith("contact"):
        return contact_layout
    return login_layout


# --- Logout ---
@app.callback(
    Output("auth-store",    "data", allow_duplicate=True),
    Output("url",           "href"),
    Input("logout-btn",     "n_clicks"),
    prevent_initial_call=True,
)
def logout(n_clicks):
    if n_clicks:
        invalidate_cache()
        return {"authenticated": False, "username": None, "providername": None}, "/"
    return dash.no_update, dash.no_update


# --- Welcome messages ---
@app.callback(Output("provider-welcome","children"), Input("auth-store","data"), prevent_initial_call=True)
def update_provider_welcome(d):
    return f"Logged in as {d.get('providername','')} ({d.get('username','')})" if d and d.get("authenticated") else ""

@app.callback(Output("claims-welcome","children"), Input("auth-store","data"), prevent_initial_call=True)
def update_claims_welcome(d):
    return f"Logged in as {d.get('providername','')} ({d.get('username','')})" if d and d.get("authenticated") else ""

@app.callback(Output("contact-welcome","children"), Input("auth-store","data"), prevent_initial_call=True)
def update_contact_welcome(d):
    return f"Logged in as {d.get('providername','')} ({d.get('username','')})" if d and d.get("authenticated") else ""


# --- Provider content — reads from store, zero DB calls ---
@app.callback(
    Output("provider-content",  "children"),
    Input("provider-nav-option","value"),
    State("store-q2",   "data"),
    State("store-q4",   "data"),
    State("auth-store", "data"),
    prevent_initial_call=True,
)
def update_provider_content(option, q2_data, q4_data, auth_data):
    if not auth_data or not q2_data or not auth_data.get("username","").startswith("234"):
        return ""

    filled_df = pd.DataFrame(q2_data)
    filled_df['ProviderName'] = filled_df['PA_Provider'].str.split('-').str[0].str.strip()
    filled_df['MemberNo']     = filled_df['MemberNo'].astype(str)

    result_df = pd.DataFrame(q4_data) if q4_data else pd.DataFrame(columns=['memberno'])
    if not result_df.empty:
        result_df['memberno'] = result_df['memberno'].astype(str)

    pn = auth_data.get("providername", "")
    if pn == 'CLINA LANCET LABOURATORIES':
        mask = filled_df['ProviderName'].str.contains('CERBA|UBA Head|CLINA', regex=True)
    elif 'ABACHA' in pn or 'DAMATURU' in pn:
        mask = filled_df['ProviderName'].str.contains('ABACHA')
    elif pn == 'ASHMED SPECIALIST':
        mask = filled_df['ProviderName'].str.contains('ASHMED', regex=False)
    else:
        mask = filled_df['ProviderName'] == pn

    pdf = filled_df[mask][['MemberNo','MemberName','IssuedPACode','PA_Tests']].copy()
    pdf['SubmissionStatus'] = pdf['MemberNo'].apply(
        lambda x: 'Submitted' if x in result_df['memberno'].values else 'Not Submitted'
    )
    pdf = pdf.sort_values('SubmissionStatus').reset_index(drop=True)

    if option == "view":
        return html.Div([
            html.H3("View Wellness Enrollees and Benefits"),
            dash_table.DataTable(
                data=pdf.to_dict('records'),
                columns=[{"name": i, "id": i} for i in pdf.columns],
                style_data_conditional=[
                    {"if": {"filter_query": '{SubmissionStatus} = "Submitted"',     "column_id": "SubmissionStatus"}, "backgroundColor": "green", "color": "white"},
                    {"if": {"filter_query": '{SubmissionStatus} = "Not Submitted"', "column_id": "SubmissionStatus"}, "backgroundColor": "red",   "color": "white"},
                ],
                style_table={"overflowX": "auto"}, page_size=20,
            )
        ])
    else:
        ns = pdf[pdf['SubmissionStatus'] == 'Not Submitted'].copy()
        ns['member'] = ns['MemberNo'].str.cat(ns['MemberName'], sep=' - ')
        return html.Div([
            html.H3("Submit Wellness Results"),
            html.P("Please select the enrollee you would like to submit wellness results for"),
            dbc.Label("Select Enrollee"),
            dcc.Dropdown(id="member-select", options=ns['member'].unique().tolist(), placeholder="Select Enrollee"),
            html.Br(),
            html.Div(id="submission-form")
        ])


@app.callback(
    Output("submission-form","children"),
    Input("member-select",  "value"),
    State("store-q2",       "data"),
    prevent_initial_call=True,
)
def show_submission_form(member, q2_data):
    if not member or not q2_data:
        return ""
    member_no = member.split(' - ')[0]
    df  = pd.DataFrame(q2_data)
    df['MemberNo'] = df['MemberNo'].astype(str)
    row = df[df['MemberNo'] == member_no].iloc[0]
    return html.Div([
        html.Br(),
        html.P(f"Submitting results for: {row['MemberName']}"),
        html.P(f"Policy End Date: {row['PolicyEndDate']}"),
        html.P("Please enter the PACode issued for the Enrollee Wellness Test"),
        dbc.Input(id="pa-code-input", type="text", placeholder="Enter PACode"),
        html.Br(),
        html.P("Please Select the Tests Conducted on the Enrollee"),
        dcc.Dropdown(id="tests-conducted", options=PA_TESTS_OPTIONS, multi=True,
                     placeholder="Select all Tests Conducted"),
        html.Br(),
        html.P("Please Enter the Date the Tests were Conducted"),
        dcc.DatePickerSingle(id="test-date-picker", placeholder="Enter Test Date"),
        html.Br(),
        html.P("Upload Test Results"),
        dcc.Upload(
            id="upload-results",
            children=html.Div(['Drag and Drop or ', html.A('Select Files')]),
            style={'width':'100%','height':'60px','lineHeight':'60px','borderWidth':'1px',
                   'borderStyle':'dashed','borderRadius':'5px','textAlign':'center','margin':'10px'},
            multiple=True
        ),
        html.Br(),
        dbc.Button("Submit Results", id="submit-results-btn", color="success"),
        html.Div(id="submission-message")
    ])


@app.callback(
    Output("submission-message","children"),
    Input("submit-results-btn","n_clicks"),
    State("member-select",     "value"),
    State("pa-code-input",     "value"),
    State("tests-conducted",   "value"),
    State("test-date-picker",  "date"),
    State("upload-results",    "filename"),
    State("upload-results",    "contents"),
    State("store-q2",          "data"),
    State("auth-store",        "data"),
    prevent_initial_call=True,
)
def submit_results(n_clicks, member, pa_code, tests_conducted, test_date,
                   uploaded_filenames, uploaded_contents, q2_data, auth_data):
    if not n_clicks or not member:
        return ""
    missing = [f for f,v in [('PA Code',pa_code),('Tests Conducted',tests_conducted),
                               ('Test Date',test_date),('Uploaded File',uploaded_filenames)] if not v]
    if missing:
        return dbc.Alert(f"Compulsory fields missing: {', '.join(missing)}", color="danger")

    member_no = member.split(' - ')[0]
    df = pd.DataFrame(q2_data)
    df['MemberNo'] = df['MemberNo'].astype(str)
    row = df[df['MemberNo'] == member_no].iloc[0]
    ped = row['PolicyEndDate']
    ped_str = ped.strftime("%Y-%m-%d") if hasattr(ped, 'strftime') else str(ped)
    pname   = auth_data.get("providername","").replace(" ","").lower()
    cname   = row['Client'].replace(" ","").lower()
    folder  = f"{pname}/{cname}/{ped_str}/{member_no}"

    bsc  = BlobServiceClient.from_connection_string(conn_str)
    cont = 'annual-wellness-results'
    uploaded_files = []
    for fn, fc in zip(uploaded_filenames or [], uploaded_contents or []):
        # fc is a data URI: "data:<mime>;base64,<data>" — decode to bytes
        content_type, content_b64 = fc.split(',', 1)
        file_bytes = base64.b64decode(content_b64)
        blob_path  = f"{folder}/{member_no}_{fn}"
        bsc.get_blob_client(container=cont, blob=blob_path).upload_blob(file_bytes, overwrite=True)
        uploaded_files.append((fn, file_bytes))

    conn = get_conn()
    conn.cursor().execute(
        "INSERT INTO demo_tbl_enrollee_wellness_result_data "
        "(memberno,membername,providername,pacode,tests_conducted,test_date,test_result_link,date_submitted) "
        "VALUES (?,?,?,?,?,?,?,GETDATE())",
        member_no, row['MemberName'], auth_data.get("providername",""),
        pa_code, ', '.join(tests_conducted), test_date,
        f"https://{bsc.account_name}.blob.core.windows.net/{cont}/{folder}"
    )
    conn.commit(); conn.close()
    invalidate_cache()

    ok, msg = send_email_with_attachment(
        row['email'], row['MemberName'], auth_data.get("providername",""),
        test_date, 'AVON HMO ANNUAL TEST RESULTS', uploaded_files
    )
    return dbc.Alert("Results submitted. Email sent to enrollee.", color="success") \
           if ok else dbc.Alert(msg, color="danger")


# --- Claims portal — reads from store ---
@app.callback(
    Output("claims-provider-select","options"),
    Input("data-ready-store","data"),
    State("store-q4","data"),
    prevent_initial_call=True,
)
def load_claims_providers(ready, q4_data):
    if not ready or not q4_data:
        return []
    df = pd.DataFrame(q4_data)
    return [{"label": p, "value": p} for p in df['providername'].unique()]


@app.callback(
    Output("claims-member-select","options"),
    Input("claims-provider-select","value"),
    State("store-q4","data"),
    prevent_initial_call=True,
)
def load_claims_members(provider, q4_data):
    if not provider or not q4_data:
        return []
    df = pd.DataFrame(q4_data)
    df['memberno'] = df['memberno'].astype(str)
    df['member']   = df['memberno'].str.cat(df['membername'], sep=' - ')
    return [{"label": m, "value": m} for m in df[df['providername'] == provider]['member'].unique()]


@app.callback(
    Output("claims-content","children"),
    Input("claims-member-select","value"),
    State("claims-provider-select","value"),
    State("store-q2","data"),
    prevent_initial_call=True,
)
def show_claims_content(member, provider, q2_data):
    if not member or not provider or not q2_data:
        return ""
    member_id = member.split(' - ')[0]
    df  = pd.DataFrame(q2_data)
    df['MemberNo'] = df['MemberNo'].astype(str)
    row = df.sort_values('date_submitted', ascending=False)\
            .drop_duplicates('MemberNo').reset_index(drop=True)
    row = row[row['MemberNo'] == member_id].iloc[0]
    return html.Div([
        html.H3(f"Test Results for {member}", style={"color":"green"}),
        html.H4(f"Client: {row['Client']}",                                  style={"color":"purple"}),
        html.H4(f"PA Code Issued to Provider: {row['IssuedPACode']}",        style={"color":"purple"}),
        html.H4(f"Wellness Tests PA Code was Issued for: {row['PA_Tests']}", style={"color":"purple"}),
        html.Hr(),
        html.H4("Results:"),
        display_member_results(conn_str, 'annual-wellness-results',
                               provider, row['Client'], member_id, row['PolicyEndDate'])
    ])


# --- Contact / PA portal search — reads entirely from store, instant ---
@app.callback(
    Output("contact-content",       "children"),
    Input("contact-search-button",  "n_clicks"),
    State("contact-enrollee-id",    "value"),
    State("store-q1",   "data"),
    State("store-q2",   "data"),
    State("store-q3",   "data"),
    State("store-q4",   "data"),
    State("auth-store", "data"),
    prevent_initial_call=True,
)
def search_enrollee(n_clicks, enrollee_id, q1_data, q2_data, q3_data, q4_data, auth_data):
    if not auth_data or not auth_data.get("authenticated"):
        return ""
    if not auth_data.get("username","").startswith("contact"):
        return ""
    if not n_clicks or not enrollee_id:
        return ""
    if not q2_data:
        return dbc.Alert("Portal data is still loading. Please wait a moment and try again.", color="warning")

    enrollee_id = enrollee_id.strip()

    filled_df = pd.DataFrame(q2_data)
    filled_df['ProviderName'] = filled_df['PA_Provider'].str.split('-').str[0].str.strip()
    filled_df['MemberNo']     = filled_df['MemberNo'].astype(str)

    wellness_df = pd.DataFrame(q1_data) if q1_data else pd.DataFrame(columns=['memberno'])
    if not wellness_df.empty:
        wellness_df['memberno'] = wellness_df['memberno'].astype(str)

    result_df = pd.DataFrame(q4_data) if q4_data else pd.DataFrame(columns=['memberno'])
    if not result_df.empty:
        result_df['memberno'] = result_df['memberno'].astype(str)

    if enrollee_id in filled_df['MemberNo'].values:
        row = filled_df[filled_df['MemberNo'] == enrollee_id].iloc[0]

        recent_df  = filled_df.sort_values('date_submitted', ascending=False)\
                               .drop_duplicates('MemberNo').reset_index(drop=True)
        policy_end = recent_df[recent_df['MemberNo'] == enrollee_id]['PolicyEndDate'].values[0]

        res_row    = result_df[result_df['memberno'] == enrollee_id]
        has_result = not res_row.empty

        booking = filled_df.loc[
            filled_df['MemberNo'] == enrollee_id,
            ['MemberNo','MemberName','Client','Wellness_benefits','selected_provider',
             'date_submitted','IssuedPACode','PA_Tests','PA_Provider','PAIssueDate']
        ].reset_index(drop=True).transpose()

        providers_df = pd.DataFrame(q3_data) if q3_data else pd.DataFrame(columns=['ProviderName'])
        prov_list = sorted(set(
            providers_df['ProviderName'].dropna().unique().tolist() +
            ['MECURE HEALTHCARE, OSHODI','MECURE HEALTHCARE, LEKKI',
             'CLINIX HEALTHCARE','TEEKAY HOSPITAL LIMITED','KANEM HOSPITAL AND MATERNITY']
        ))

        table_rows = [
            html.Tr([html.Td(idx, style={'fontWeight':'bold'}), html.Td(str(v[0]))])
            for idx, v in booking.iterrows()
        ]
        result_alert = (
            dbc.Alert(
                f"Wellness Results for {row['MemberName']} done by "
                f"{res_row['providername'].values[0]} submitted and sent to "
                f"{row['email']} on {res_row['date_submitted'].values[0]}",
                color="success"
            ) if has_result else
            dbc.Alert(
                f"Wellness Results for {row['MemberName']} not yet submitted. "
                "Please follow up with the provider.", color="danger"
            )
        )

        return html.Div([
            html.H4(f"Wellness Booking Details for {row['MemberName']}", style={"color":"purple"}),
            html.Table(table_rows, style={'width':'100%','borderCollapse':'collapse'}),
            html.Hr(),
            html.H4("Kindly Update Details of PA Code Issued to Provider for the Enrollee",
                    style={"color":"purple"}),
            dbc.Label("Input the Generated PA Code"),
            dbc.Input(id="contact-pacode", type="text", placeholder="Enter PA Code"),
            html.Br(),
            dbc.Label("Select the Tests Conducted"),
            dcc.Dropdown(id="contact-pa-tests", options=PA_TESTS_OPTIONS, multi=True),
            html.Br(),
            dbc.Label("Select the Wellness Provider"),
            dcc.Dropdown(id="contact-pa-provider",
                         options=[{'label':p,'value':p} for p in prov_list],
                         placeholder="Select Provider"),
            html.Br(),
            dbc.Label("Select the Date the PA was Issued"),
            dcc.DatePickerSingle(id="contact-pa-issue-date", placeholder="Select Date"),
            html.Br(),
            dbc.Button("PROCEED", id="contact-proceed-btn", color="primary"),
            html.Div(id="contact-pa-message"),
            html.Hr(),
            result_alert
        ])

    elif not wellness_df.empty and enrollee_id in wellness_df['memberno'].values:
        return dbc.Alert(
            "Enrollee has not booked a wellness test. "
            "Advise them to book via the Wellness Portal.", color="warning"
        )

    return dbc.Alert("Invalid Member ID or Enrollee not eligible for Wellness Test.", color="danger")


@app.callback(
    Output("contact-pa-message",    "children"),
    Input("contact-proceed-btn",    "n_clicks"),
    State("contact-enrollee-id",    "value"),
    State("contact-pacode",         "value"),
    State("contact-pa-tests",       "value"),
    State("contact-pa-provider",    "value"),
    State("contact-pa-issue-date",  "date"),
    State("auth-store",             "data"),
    prevent_initial_call=True,
)
def update_pa_code(n_clicks, enrollee_id, pacode, pa_tests, pa_provider, pa_issue_date, auth_data):
    if not auth_data or not auth_data.get("authenticated"):
        return ""
    if not auth_data.get("username","").startswith("contact") or not n_clicks:
        return ""
    missing = [f for f,v in [('PA Code',pacode),('Tests Conducted',pa_tests),('Provider',pa_provider)] if not v]
    if missing:
        return dbc.Alert(f"Please fill: {', '.join(missing)}", color="danger")

    conn = get_conn()
    conn.cursor().execute(
        "UPDATE demo_tbl_annual_wellness_enrollee_data "
        "SET IssuedPACode=?, PA_Tests=?, PA_Provider=?, PAIssueDate=? "
        "WHERE MemberNo=? AND date_submitted=("
        "  SELECT MAX(date_submitted) FROM demo_tbl_annual_wellness_enrollee_data WHERE MemberNo=?)",
        pacode, ','.join(pa_tests), pa_provider, pa_issue_date, enrollee_id, enrollee_id
    )
    conn.commit(); conn.close()
    invalidate_cache()
    return dbc.Alert("PA Code successfully updated for the enrollee.", color="success")


if __name__ == '__main__':
    app.run(debug=True, port=8050)