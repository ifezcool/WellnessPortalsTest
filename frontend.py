import dash
from dash import dcc, html, Input, Output, State, callback_context
from dash_svg import Svg, Path
import dash_bootstrap_components as dbc
import pandas as pd
from datetime import datetime, timedelta

app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@400;500;600;700&display=swap",
        "https://cdn.jsdelivr.net/npm/lucide-static@0.344.0/font/lucide.min.css"
    ],
    suppress_callback_exceptions=True
)

server = app.server

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@400;500;600;700&display=swap');
    
    :root {
        --primary-color: #6B46C1;
        --secondary-color: #38B2AC;
        --primary-rgb: 107, 70, 193;
    }
    
    body {
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Playfair Display', serif;
    }
    
    .gradient-bg {
        background: linear-gradient(135deg, #faf5ff 0%, #ffffff 50%, #f0fdf4 100%);
    }
    
    .purple-skew {
        background: rgba(107, 70, 193, 0.05);
        transform: skewY(-3deg);
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 250px;
        content: '';
    }
    
    .green-blob {
        position: absolute;
        bottom: 0;
        right: 0;
        width: 400px;
        height: 400px;
        background: rgba(56, 178, 172, 0.05);
        border-radius: 50%;
        filter: blur(60px);
        pointer-events: none;
    }
    
    .logo-container {
        width: 64px;
        height: 64px;
        background: linear-gradient(135deg, #6B46C1, #805AD5);
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        transform: rotate(3deg);
        box-shadow: 0 10px 25px rgba(107, 70, 193, 0.25);
        margin: 0 auto;
    }
    
    .card-glass {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(107, 70, 193, 0.1);
        box-shadow: 0 25px 50px -12px rgba(107, 70, 193, 0.08);
    }
    
    .form-input {
        height: 48px;
        border: 2px solid #E9D8FD;
        border-radius: 12px;
        transition: all 0.2s;
    }
    
    .form-input:focus {
        border-color: #6B46C1;
        box-shadow: 0 0 0 3px rgba(107, 70, 193, 0.1);
    }
    
    .btn-primary-custom {
        background: linear-gradient(135deg, #6B46C1, #805AD5);
        border: none;
        height: 48px;
        font-weight: 600;
        border-radius: 12px;
        box-shadow: 0 10px 25px rgba(107, 70, 193, 0.25);
        transition: all 0.2s;
    }
    
    .btn-primary-custom:hover {
        transform: translateY(-2px);
        box-shadow: 0 15px 30px rgba(107, 70, 193, 0.3);
    }
    
    .header-purple {
        background: linear-gradient(135deg, #6B46C1, #805AD5);
    }
    
    .border-left-accent {
        border-left: 4px solid #38B2AC;
    }
    
    .status-card {
        border-top: 8px solid #48BB78;
    }
    
    .validity-banner {
        background: #FFFBEB;
        border: 1px solid #FCD34D;
        border-radius: 8px;
    }
    
    .logo-icon {
        width: 32px;
        height: 32px;
    }
</style>
"""

app.index_string = f'''
<!DOCTYPE html>
<html>
    <head>
        {{%metas%}}
        <title>Wellness Portal</title>
        {{%favicon%}}
        {{%css%}}
    </head>
    <body>
        {{%app_entry%}}
        <footer>
            {{%config%}}
            {{%scripts%}}
            {{%renderer%}}
        </footer>
        {CUSTOM_CSS}
    </body>
</html>
'''

DATA_STORE = {
    "member_no": None,
    "eligibility": None,
    "submission": None,
    "providers": pd.DataFrame([
        {"code": "LAG001", "providerLoc": "Lagos Central Hospital", "state": "LAGOS"},
        {"code": "LAG002", "providerLoc": "Victoria Island Medical Center", "state": "LAGOS"},
        {"code": "ABJ001", "providerLoc": "Abuja Diagnostic Center", "state": "ABUJA"},
        {"code": "ABJ002", "providerLoc": "Gwarinpa Hospital", "state": "ABUJA"},
        {"code": "PHC001", "providerLoc": "Port Harcourt Medical Centre", "state": "RIVERS"},
        {"code": "WAR001", "providerLoc": "Warri Central Hospital", "state": "DELTA"},
        {"code": "KAN001", "providerLoc": "Kano Specialist Hospital", "state": "KANO"},
        {"code": "IBD001", "providerLoc": "Ibadan General Hospital", "state": "OYO"},
    ])
}

welcome_layout = html.Div(
    className="gradient-bg min-vh-100 d-flex align-items-center justify-content-center p-4 position-relative overflow-hidden",
    children=[
        dcc.Location(id="url-welcome", refresh=True),

        html.Div(className="purple-skew"),
        html.Div(className="green-blob"),

        html.Div(
            className="position-relative w-100",
            style={"maxWidth": "480px", "zIndex": "10"},
            children=[
                html.Div([
                    html.Div(className="logo-container mb-4", children=[
                        Svg(
                            width="32", height="32", viewBox="0 0 24 24",
                            fill="none", stroke="white",
                            style={"strokeWidth": "2", "strokeLinecap": "round", "strokeLinejoin": "round"},
                            children=[
                                Path(d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"),
                                Path(d="m9 12 2 2 4-4")
                            ]
                        )
                    ]),
                    html.H1("Wellness Portal", className="text-4xl fw-bold mb-2", style={"color": "#44337A"}),
                    html.P("Check your eligibility and book your annual wellness checkup.",
                           className="text-lg mb-4", style={"color": "#718096"}),
                ], className="text-center mb-5"),

                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.Label("Member Number / Policy ID", className="fw-medium mb-2", style={"color": "#44337A"}),
                            dcc.Input(
                                id="member-no-input",
                                type="text",
                                placeholder="Enter your Member ID",
                                className="form-control form-input mb-3",
                                style={"fontSize": "18px"}
                            ),
                            html.Div(id="error-message", className="alert alert-danger d-none mb-3",
                                     style={"backgroundColor": "#FED7D7", "border": "1px solid #FEB2B2", "color": "#C53030"}),
                            html.Div(id="ineligible-message", className="alert mb-3 d-none",
                                     style={"backgroundColor": "#FFFBEB", "border": "1px solid #FCD34D", "color": "#92400E"}),

                            dbc.Button([
                                html.Span("Check Eligibility ", className="me-2"),
                                html.Span("→")
                            ], id="check-eligibility-btn", color="primary",
                               className="w-100 btn-primary-custom d-flex align-items-center justify-content-center",
                               style={"color": "white"}),
                        ], className="p-2")
                    ])
                ], className="card-glass border-0", style={"borderRadius": "24px"}),

                html.P(f"© {datetime.now().year} Wellness Portal. All rights reserved.",
                       className="text-center mt-4 small", style={"color": "rgba(113, 128, 150, 0.6)"})
            ]
        )
    ]
)

booking_layout = html.Div([
    dcc.Location(id="url-booking", refresh=True),

    html.Div([
        dbc.Row([
            dbc.Col([
                html.H1(id="welcome-name", className="text-white mb-2", style={"fontSize": "2.5rem"}),
                html.P("Complete the form below to book your annual wellness checkup. Your health is your greatest asset.",
                       className="text-white", style={"opacity": 0.9})
            ], className="position-relative z-10 mx-auto py-5", style={"maxWidth": "900px"})
        ], className="header-purple py-5 px-4 position-relative overflow-hidden"),

        html.Div([
            html.Div([
                html.Div([
                    dbc.Row([
                        dbc.Col([
                            html.H3("Confirm Your Details", className="fw-semibold"),
                            html.P("Please verify that the following information matches your records.", className="text-muted small mb-3")
                        ], width=12)
                    ]),
                    dbc.Row([
                        dbc.Col([
                            html.Span("Client/Company:", className="d-block text-muted small"),
                            html.Span(id="display-client", className="fw-medium")
                        ], md=6, xs=12, className="mb-2"),
                        dbc.Col([
                            html.Span("Policy Name:", className="d-block text-muted small"),
                            html.Span(id="display-policy", className="fw-medium")
                        ], md=6, xs=12, className="mb-2"),
                        dbc.Col([
                            html.Span("Policy Ends:", className="d-block text-muted small"),
                            html.Span(id="display-policy-end", className="fw-medium")
                        ], md=6, xs=12, className="mb-2"),
                        dbc.Col([
                            html.Span("Package:", className="d-block text-muted small"),
                            html.Span(id="display-package", className="fw-medium")
                        ], md=6, xs=12, className="mb-2"),
                    ])
                ], className="p-4")
            ], className="card border-left-accent mb-4")
        ], className="position-relative", style={"marginTop": "-40px", "zIndex": "20", "maxWidth": "900px", "margin": "auto"}),

        html.Div([
            dbc.Card([
                dbc.CardHeader([
                    html.H4([html.Span("📅 ", className="me-2"), "Booking Details"], className="mb-1"),
                    html.P("Select your preferred location and time for the checkup.", className="text-muted mb-0 small")
                ], className="bg-light"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.H6("Contact Information", className="text-muted text-uppercase small fw-bold border-bottom pb-2 mb-3"),

                            html.Label("Email Address", className="small fw-medium"),
                            dcc.Input(id="input-email", type="email", placeholder="you@company.com", className="form-control mb-3"),

                            html.Label("Mobile Number", className="small fw-medium"),
                            dcc.Input(id="input-mobile", type="text", placeholder="080...", className="form-control mb-3"),

                            html.Label("Gender", className="small fw-medium d-block mb-2"),
                            dbc.RadioItems(
                                id="input-gender",
                                options=[{"label": " Male ", "value": "Male"}, {"label": " Female ", "value": "Female"}],
                                value="Male",
                                inline=True,
                                className="mb-3"
                            ),

                            html.Label("Job Type", className="small fw-medium"),
                            dcc.Dropdown(
                                id="input-job-type",
                                options=[
                                    {"label": "Mainly Desk Work", "value": "Mainly Desk Work"},
                                    {"label": "Mainly Field Work", "value": "Mainly Field Work"},
                                    {"label": "Both Desk and Field Work", "value": "Both Desk and Field Work"}
                                ],
                                value="Mainly Desk Work",
                                className="mb-3"
                            )
                        ], md=6, xs=12),

                        dbc.Col([
                            html.H6("Appointment Details", className="text-muted text-uppercase small fw-bold border-bottom pb-2 mb-3"),

                            html.Label("State", className="small fw-medium"),
                            dcc.Dropdown(
                                id="input-state",
                                options=[
                                    {"label": "Lagos", "value": "LAGOS"},
                                    {"label": "Abuja", "value": "ABUJA"},
                                    {"label": "Rivers", "value": "RIVERS"},
                                    {"label": "Delta", "value": "DELTA"},
                                    {"label": "Kano", "value": "KANO"},
                                    {"label": "Oyo", "value": "OYO"}
                                ],
                                placeholder="Select a state",
                                className="mb-3"
                            ),

                            html.Label("Preferred Facility", className="small fw-medium"),
                            dcc.Dropdown(
                                id="input-facility",
                                options=[],
                                placeholder="Select state first",
                                className="mb-3"
                            ),

                            html.Label("Preferred Date", className="small fw-medium"),
                            dcc.DatePickerSingle(
                                id="input-date",
                                min_date_allowed=datetime.now(),
                                max_date_allowed=datetime.now() + timedelta(days=365),
                                placeholder="Pick a date",
                                className="mb-3"
                            ),

                            html.Label("Session", className="small fw-medium"),
                            dcc.Dropdown(
                                id="input-session",
                                options=[
                                    {"label": "Morning", "value": "Morning"},
                                    {"label": "Afternoon", "value": "Afternoon"}
                                ],
                                value="Morning",
                                className="mb-3"
                            )
                        ], md=6, xs=12)
                    ]),

                    html.Hr(className="my-4"),

                    dbc.Row([
                        dbc.Col([
                            html.Div(id="submission-error", className="alert alert-danger d-none")
                        ], width=12, md=6),
                        dbc.Col([
                            dbc.Button([
                                html.Span("Book Appointment ", className="me-2"),
                                html.Span("✓")
                            ], id="submit-booking-btn", color="primary",
                               className="btn-primary-custom float-end", style={"color": "white"})
                        ], width=12, md=6, className="text-md-end")
                    ])
                ])
            ], className="shadow-lg")
        ], className="px-4 pb-5", style={"maxWidth": "900px", "margin": "auto"})
    ], className="bg-light min-vh-100 pb-5")
])

status_layout = html.Div(
    className="min-vh-100 d-flex align-items-center justify-content-center p-4",
    style={"background": "#F7FAFC"},
    children=[
        dcc.Location(id="url-status", refresh=True),

        html.Div(
            className="w-100",
            children=[
                dbc.Card([
                    dbc.CardHeader([
                        html.Div(className="d-flex justify-content-center mb-3", style={"width": "100%"}, children=[
                            Svg(
                                width="40", height="40", viewBox="0 0 24 24",
                                fill="none", stroke="#48BB78",
                                style={"strokeWidth": "2", "strokeLinecap": "round", "strokeLinejoin": "round"},
                                children=[
                                    Path(d="M22 11.08V12a10 10 0 1 1-5.93-9.14"),
                                    Path(d="m9 11 3 3L22 4")
                                ]
                            )
                        ]),
                        html.H2("Booking Confirmed", className="text-center fw-bold"),
                        html.P("Your wellness appointment has been successfully scheduled.", className="text-center text-muted")
                    ], className="text-center pt-5 pb-2"),

                    dbc.CardBody([
                        dbc.Card([
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        html.Div([
                                            html.Span("BENEFICIARY", className="d-block text-muted small text-uppercase fw-bold"),
                                            html.Span(id="status-member-name", className="fw-bold d-block", style={"fontSize": "18px"}),
                                            html.Span(id="status-member-no", className="text-muted small")
                                        ])
                                    ], md=6, className="mb-3"),
                                    dbc.Col([
                                        html.Div([
                                            html.Span("FACILITY", className="d-block text-muted small text-uppercase fw-bold"),
                                            html.Span(id="status-facility", className="fw-bold d-block", style={"fontSize": "18px"})
                                        ])
                                    ], md=6, className="mb-3"),
                                    dbc.Col([
                                        html.Div([
                                            html.Span("DATE & TIME", className="d-block text-muted small text-uppercase fw-bold"),
                                            html.Span(id="status-date", className="fw-bold d-block", style={"fontSize": "18px"}),
                                            html.Span(id="status-session", className="text-muted small")
                                        ])
                                    ], md=6, className="mb-3"),
                                    dbc.Col([
                                        html.Div([
                                            html.Span("LOCATION STATE", className="d-block text-muted small text-uppercase fw-bold"),
                                            html.Span(id="status-state", className="fw-bold d-block", style={"fontSize": "18px"})
                                        ])
                                    ], md=6, className="mb-3"),
                                ])
                            ])
                        ], className="mb-4"),

                        html.Div(className="validity-banner p-3", children=[
                            html.Strong("⚠ Validity Period", className="d-block mb-1"),
                            html.Span("Please note that your annual wellness ticket is only valid until ", className="small"),
                            html.Span(id="validity-date", className="fw-bold")
                        ])
                    ]),

                    dbc.CardFooter([
                        dbc.Button(["Back to Home"], id="back-home-btn", outline=True, color="secondary", className="me-auto"),
                        dbc.Button(["Print Confirmation"], id="print-btn", outline=True, color="primary")
                    ], className="bg-light d-flex justify-content-between")
                ], className="shadow-xl status-card", style={"maxWidth": "700px", "borderRadius": "0", "overflow": "hidden"})
            ]
        )
    ]
)

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Div(id="page-content")
])

@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname")
)
def display_page(pathname):
    if pathname == "/" or pathname == "" or pathname is None:
        return welcome_layout
    elif pathname.startswith("/form/"):
        return booking_layout
    elif pathname.startswith("/status/"):
        return status_layout
    else:
        return welcome_layout

@app.callback(
    [Output("url", "pathname", allow_duplicate=True),
     Output("error-message", "children"),
     Output("error-message", "className"),
     Output("ineligible-message", "children"),
     Output("ineligible-message", "className")],
    Input("check-eligibility-btn", "n_clicks"),
    State("member-no-input", "value"),
    prevent_initial_call=True
)
def check_eligibility(n_clicks, member_no):
    if not member_no:
        return "/", "Member Number is required", "alert alert-danger mb-3", "", "d-none"

    mock_eligibility = {
        "MEM001": {"eligible": True, "memberName": "John Doe", "client": "United Bank for Africa",
                   "policyName": "UBA Premium Plan", "policyEndDate": "2025-12-31", "wellnessPackage": "Gold Plus"},
        "MEM002": {"eligible": False, "message": "Your policy has expired."},
        "MEM003": {"eligible": True, "memberName": "Jane Smith", "client": "Verteville Energy",
                   "policyName": "Total Energies Managed Care Plan", "policyEndDate": "2025-06-30", "wellnessPackage": "Executive"},
    }

    if member_no in mock_eligibility:
        data = mock_eligibility[member_no]
        DATA_STORE["member_no"] = member_no
        DATA_STORE["eligibility"] = data

        if data.get("eligible"):
            return f"/form/{member_no}", "", "d-none", "", "d-none"
        else:
            return "/", "", "d-none", data.get("message", "You are not currently eligible."), "alert mb-3"
    else:
        return "/", "We couldn't find a member with that ID. Please check and try again.", "alert alert-danger mb-3", "", "d-none"

@app.callback(
    [Output("display-client", "children"),
     Output("display-policy", "children"),
     Output("display-policy-end", "children"),
     Output("display-package", "children"),
     Output("welcome-name", "children"),
     Output("input-email", "value"),
     Output("input-state", "value")],
    Input("url-booking", "pathname")
)
def load_booking_data(pathname):
    eligibility = DATA_STORE.get("eligibility")
    if eligibility:
        first_name = eligibility.get("memberName", "Member").split()[0]
        return (
            eligibility.get("client", ""),
            eligibility.get("policyName", ""),
            eligibility.get("policyEndDate", ""),
            eligibility.get("wellnessPackage", ""),
            f"Welcome, {first_name}",
            "member@company.com",
            "LAGOS"
        )
    return "", "", "", "", "Welcome", "", ""

@app.callback(
    Output("input-facility", "options"),
    Input("input-state", "value")
)
def update_facilities(state):
    if not state:
        return []
    providers = DATA_STORE["providers"]
    filtered = providers[providers["state"] == state]
    return [{"label": row["providerLoc"], "value": row["providerLoc"]} for _, row in filtered.iterrows()]

@app.callback(
    [Output("url", "pathname", allow_duplicate=True),
     Output("submission-error", "children"),
     Output("submission-error", "className")],
    Input("submit-booking-btn", "n_clicks"),
    State("input-email", "value"),
    State("input-mobile", "value"),
    State("input-gender", "value"),
    State("input-job-type", "value"),
    State("input-state", "value"),
    State("input-facility", "value"),
    State("input-date", "date"),
    State("input-session", "value"),
    prevent_initial_call=True
)
def submit_booking(n_clicks, email, mobile, gender, job_type, state, facility, date, session):
    if not all([email, mobile, state, facility, date, session]):
        return "/form/", "Please fill in all required fields", "alert alert-danger mb-3"

    DATA_STORE["submission"] = {
        "memberName": DATA_STORE["eligibility"].get("memberName"),
        "memberNo": DATA_STORE["member_no"],
        "selectedProvider": facility,
        "selectedDate": date,
        "selectedSession": session,
        "state": state,
        "dateSubmitted": datetime.now().isoformat()
    }

    return f"/status/{DATA_STORE['member_no']}", "", "d-none"

@app.callback(
    [Output("status-member-name", "children"),
     Output("status-member-no", "children"),
     Output("status-facility", "children"),
     Output("status-date", "children"),
     Output("status-session", "children"),
     Output("status-state", "children"),
     Output("validity-date", "children")],
    Input("url-status", "pathname")
)
def load_status_data(pathname):
    submission = DATA_STORE.get("submission")
    if submission:
        valid_until = datetime.now() + timedelta(weeks=6)
        return (
            submission.get("memberName", ""),
            submission.get("memberNo", ""),
            submission.get("selectedProvider", ""),
            submission.get("selectedDate", ""),
            submission.get("selectedSession", ""),
            submission.get("state", ""),
            valid_until.strftime("%B %d, %Y")
        )
    return "", "", "", "", "", "", ""

@app.callback(
    Output("url", "pathname", allow_duplicate=True),
    Input("back-home-btn", "n_clicks"),
    prevent_initial_call=True
)
def go_home(n_clicks):
    DATA_STORE["member_no"] = None
    DATA_STORE["eligibility"] = None
    DATA_STORE["submission"] = None
    return "/"

if __name__ == "__main__":
    app.run(debug=True, port=8050)