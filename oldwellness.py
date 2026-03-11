import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image
import datetime as dt
import pyodbc
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv('secrets.env')

st.set_page_config(layout='wide')

image = Image.open('wellness_image_1.png')
st.image(image)

server = os.environ.get('server_name')
database = os.environ.get('db_name')
username = os.environ.get('db_username')
password = os.environ.get('db_password')


conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};SERVER='
        + server
        +';DATABASE='
        + database
        +';UID='
        + username
        +';PWD='
        + password
        )


# conn = pyodbc.connect(
#         'DRIVER={ODBC Driver 17 for SQL Server};SERVER='
#         +st.secrets['server']
#         +';DATABASE='
#         +st.secrets['database']
#         +';UID='
#         +st.secrets['username']
#         +';PWD='
#         +st.secrets['password']
#         )

query1 = "SELECT * from vw_wellness_enrollee_portal_update"
query2 = 'select MemberNo, MemberName, Client, email, state, selected_provider, Wellness_benefits, selected_date, selected_session, date_submitted\
            FROM tbl_annual_wellness_enrollee_data a\
            where a.PolicyEndDate = (select max(PolicyEndDate) from tbl_annual_wellness_enrollee_data b where a.MemberNo = b.MemberNo)'
query3 = "select a.CODE, a.STATE, PROVIDER_NAME, a.ADDRESS,Provider_Name + ' - ' + Location as ProviderLoc, PROVIDER, name\
            from Updated_Wellness_Providers a\
            join tbl_Providerlist_stg b on a.CODE = b.code"
query4 = 'select * from vw_loyaltybeneficiaries'

@st.cache_data(ttl = dt.timedelta(hours=4))
def LOADING():
    wellness_df = pd.read_sql(query1, conn)
    wellness_providers = pd.read_sql(query3, conn)
    loyalty_beneficiaries = pd.read_sql(query4, conn)
    # conn.close()
    return wellness_df, wellness_providers, loyalty_beneficiaries

wellness_df, wellness_providers, loyalty_enrollees = LOADING()

filled_wellness_df = pd.read_sql(query2, conn)

wellness_df['memberno'] = wellness_df['memberno'].astype(int).astype(str)

filled_wellness_df['MemberNo'] = filled_wellness_df['MemberNo'].astype(str)

loyalty_enrollees['MemberNo'] = loyalty_enrollees['MemberNo'].astype(str)

st.subheader('Welcome to the AVON HMO Enrollee Annual Wellness Portal \nKindly note that you are only eligible to perform your Wellness check once within a policy year')

ladol_special = pd.read_csv('Ladol Special Wellness.csv')
#initialize session state to store user input
if 'user_data' not in st.session_state:
    st.session_state.user_data = {
        'email': '',
        'mobile_num': '',
        'state': 'ABIA',
        'selected_provider': 'ROSEVINE HOSPITAL  - 73 ABA OWERRI ROAD, ABA',
        'job_type': 'Mainly Desk Work',
        'gender': 'Male',
        'resp_1_a': 'Grand Parent(s)',
        'resp_1_b': 'Grand Parent(s)',
        'resp_1_c': 'Grand Parent(s)',
        'resp_1_d': 'Grand Parent(s)',
        'resp_1_e': 'Grand Parent(s)',
        'resp_1_f': 'Grand Parent(s)',
        'resp_1_g': 'Grand Parent(s)',
        'resp_1_h': 'Grand Parent(s)',
        'resp_1_i': 'Grand Parent(s)',
        'resp_1_j': 'Grand Parent(s)',
        'resp_1_k': 'Grand Parent(s)',
        'resp_2_a': 'Yes',
        'resp_2_b': 'Yes',
        'resp_2_c': 'Yes',
        'resp_2_d': 'Yes',
        'resp_2_e': 'Yes',
        'resp_2_f': 'Yes',
        'resp_2_g': 'Yes',
        'resp_2_h': 'Yes',
        'resp_2_i': 'Yes',
        'resp_3_a': 'Yes',
        'resp_3_b': 'Yes',
        'resp_3_c': 'Yes',
        'resp_3_d': 'Yes',
        'resp_3_e': 'Yes',
        'resp_3_f': 'Yes',
        'resp_4_a': 'Never',
        'resp_4_b': 'Never',
        'resp_4_c': 'Never',
        'resp_4_d': 'Never',
        'resp_4_e': 'Never',
        'resp_4_f': 'Never',
        'resp_4_g': 'Never',
        'resp_4_h': 'Never',
        'resp_4_i': 'Never',
        'resp_4_j': 'Never',
        'resp_4_k': 'Never',
        'resp_4_l': 'Never',
        'resp_4_m': 'Never',
        'resp_4_n': 'Never',
        'resp_4_o': 'Never',
        'resp_4_p': 'Never',
        'resp_4_q': 'Never',
        'resp_4_r': 'Never',
        'resp_4_s': 'Never',
        'resp_4_t': 'Never',     
    }

# Get enrollee ID from URL query parameters
query_params = st.query_params
default_enrollee_id = query_params.get("member", "")  # "member" comes from ?member=12345
enrollee_id = st.text_input('Please input your Member ID to confirm your eligibility', value=default_enrollee_id)
#enrollee_id = st.text_input('Kindly input your Member ID to confirm your eligibility')

#add a submit button
st.button("Submit", key="button1", help="Click or Press Enter")
enrollee_id = str(enrollee_id)


if enrollee_id:
    if enrollee_id in filled_wellness_df['MemberNo'].values:
        policystart = wellness_df.loc[wellness_df['memberno'] == enrollee_id, 'PolicyStartDate'].values[0]
        policyend = wellness_df.loc[wellness_df['memberno'] == enrollee_id, 'PolicyEndDate'].values[0]
        submitted_date = np.datetime_as_string(filled_wellness_df.loc[filled_wellness_df['MemberNo'] == enrollee_id, 'date_submitted'].values[0], unit='D')
        final_submit_date = dt.datetime.strptime(submitted_date, "%Y-%m-%d").date()
    else:
        final_submit_date = None
        if enrollee_id in wellness_df['memberno'].values:
            policystart = wellness_df.loc[wellness_df['memberno'] == enrollee_id, 'PolicyStartDate'].values[0]
            policyend = wellness_df.loc[wellness_df['memberno'] == enrollee_id, 'PolicyEndDate'].values[0]
        else:
            policystart = None
            policyend = None   

    # st.write(policystart, policyend, final_submit_date)
    if (enrollee_id in filled_wellness_df['MemberNo'].values) and (policystart <= final_submit_date <= policyend):
        member_name = filled_wellness_df.loc[filled_wellness_df['MemberNo'] == enrollee_id, 'MemberName'].values[0]
        clientname = filled_wellness_df.loc[filled_wellness_df['MemberNo'] == enrollee_id, 'Client'].values[0]
        package = filled_wellness_df.loc[filled_wellness_df['MemberNo'] == enrollee_id, 'Wellness_benefits'].values[0]
        member_email = filled_wellness_df.loc[filled_wellness_df['MemberNo'] == enrollee_id, 'email'].values[0]
        provider = filled_wellness_df.loc[filled_wellness_df['MemberNo'] == enrollee_id, 'selected_provider'].values[0]
        app_date = filled_wellness_df.loc[filled_wellness_df['MemberNo'] == enrollee_id, 'selected_date'].values[0]
        app_session = filled_wellness_df.loc[filled_wellness_df['MemberNo'] == enrollee_id, 'selected_session'].values[0]
        
        #change the submitted_date to date format, add 6 weeks and return the date in this format e.g Wednesday, 31st December 2021
        six_weeks = dt.datetime.strptime(submitted_date, "%Y-%m-%d").date() + dt.timedelta(weeks=6)
        six_weeks = six_weeks.strftime('%A, %d %B %Y')
        # .strftime('%A, %d %B %Y')
               

        filled_message = f'Dear {member_name}.\n \n Please note that you have already booked your wellness appointment on {submitted_date}\
              and your booking confirmation has been sent to {member_email} as provided.\n\n Find your booking information below:\n\n Wellness\
                  Facility: {provider}.\n\n Wellness Benefits: {package}.\n\n Appointment Date: {app_date} - {app_session}.\n\n Kindly contact your\
                    Client Manager if you wish change your booking appointment.\n\n Note that your annual wellness is only valid till {six_weeks}.\n\n Thank you for choosing AVON HMO.'
        st.info(f'Dear {member_name}.\n\n'
                f'Please note that you have already booked your wellness appointment on {submitted_date} and your booking confirmation has been sent to {member_email} as provided\n\n'
                f'Wellness Facility: {provider}.\n\n'
                f'Wellness Benefits: {package}.\n\n'
                f'Appointment Date: {app_date} - {app_session}.\n\n'
                f'Kindly note that your wellness result will only be available two (2) weeks after your visit to the provider for your wellness test.\n\n'
                f'Kindly contact your Client Manager if you wish change your booking appointment/wellness center.\n\n'
                f'###Note that your annual wellness is only valid till {six_weeks}.\n\n'
                ,icon="✅")
        
        

    elif (enrollee_id in wellness_df['memberno'].values) & (final_submit_date is None or final_submit_date <= policystart):
        enrollee_name = wellness_df.loc[wellness_df['memberno'] == enrollee_id, 'membername'].values[0]
        client = wellness_df.loc[wellness_df['memberno'] == enrollee_id, 'Client'].values[0]
        policy = wellness_df.loc[wellness_df['memberno'] == enrollee_id, 'PolicyName'].values[0]
        package = wellness_df.loc[wellness_df['memberno'] == enrollee_id, 'WellnessPackage'].values[0]
        age = int(wellness_df.loc[wellness_df['memberno'] == enrollee_id, 'Age'].values[0])
        relation = wellness_df.loc[wellness_df['memberno'] == enrollee_id, 'Relation'].values[0]

        # st.write(wellness_providers.loc[wellness_providers['STATE'] == 'SOKOTO', 'PROVIDER'].unique())

        #write a code to assign 6weeks from the current date to a variable
        six_week_dt = dt.date.today() + dt.timedelta(weeks=6)
        #convert six_weeks to this date format e.g Wednesday, 31st December 2021
        six_weeks = six_week_dt.strftime('%A, %d %B %Y')
        
        st.markdown(
            f"""
            Dear {enrollee_name}.<br><br>

            <b style="color: purple;">
                Kindly confirm that your enrollment details match the info displayed below.<br><br>
                Also note that by proceeding to fill this form, you consent to the collection and processing of your data for the purpose of this wellness screening exercise.<br>
                You understand that your results may be shared with the HMO for claims management and care coordination, 
                and that your data will be handled in accordance with Avon HMO’s Privacy Policy.
            </b><br><br>

            <b>Please note that once you complete this form, you only have till {six_weeks} to complete your wellness check.</b>
            """,
            unsafe_allow_html=True
        )

        st.info(
            f'Company: {client}.\n\n Policy: {policy}.\n\n Policy End Date: {policyend}.\n\n '
            f'Please contact your Client Manager if this information does not match your enrollment details.'
        )

        # #add a submit button
        # proceed = st.button("PROCEED", help="Click to proceed")
        # if proceed:
        st.subheader('Kindly fill all the fields below to proceed')

        email = st.text_input('Input a Valid Email Address', st.session_state.user_data['email'])
        mobile_num = st.text_input('Input a Valid Mobile Number', st.session_state.user_data['mobile_num'])
        gender = st.radio('Sex', options=['Male', 'Female'], index=['Male', 'Female'].index(st.session_state.user_data['gender']))

        #add a branching to show different job types for TOTAL ENERGIES MANAGED CARE PLAN and other policies
        if policy == 'TOTAL ENERGIES MANAGED CARE PLAN':
            job_type = st.selectbox('Nature of Work', placeholder='Select your Work Category', index=None, options=['Offshore Personnel', 'Fire Team', 'MERT', 'Lab Personnel', 'Admin and Others'])
        else:
            job_type = st.selectbox('Occupation Type', placeholder='Pick your Work Category', index=None, options=['Mainly Desk Work', 'Mainly Field Work', 'Desk and Field Work', 'Physical Outdoor Work', 'Physical Indoor Work'])
        
        
        if client == 'UNITED BANK FOR AFRICA':
            excluded_state = 'HQ'
            available_states = wellness_providers['STATE'].unique()
            available_states = [state for state in available_states if state != excluded_state]
            # add_state = 'UBA HQ'
            # add_state = list(available_states) + [add_state]
            state = st.selectbox('Your Current Location', placeholder='Pick your Current State of Residence', index=None, options=available_states)
        elif client == 'VERTEVILLE ENERGY':
            available_states = ['LAGOS', 'BORNO', 'DELTA', 'RIVERS']
            state = st.selectbox('Your Current Location', placeholder='Pick your Current State of Residence', index=None, options=available_states)
        elif client == 'PETROSTUFF NIGERIA LIMITED':
            available_states = ['LAGOS', 'ABUJA', 'RIVERS']
            state = st.selectbox('Your Current Location', placeholder='Pick your Current State of Residence', index=None, options=available_states)
        elif client == 'TRANSCORP HILTON HOTEL ABUJA':
            available_states = ['ABUJA']
            state = st.selectbox('Your Current Location', options=available_states)
        elif client == 'REX INSURANCE LTD':
            available_states = ['LAGOS', 'RIVERS', 'DELTA', 'OYO', 'KADUNA', 'KANO']
            state = st.selectbox('Your Current Location', placeholder='Pick your Current State of Residence', index=None, options=available_states)
        else:
            excluded_state = 'HQ'
            available_states = wellness_providers['STATE'].unique()
            available_states = [state for state in available_states if state != excluded_state]
            state = st.selectbox('Your Current Location', placeholder='Pick your Current State of Residence', index=None, options=available_states)

        #create a list of sterling bank enrollees that have a different wellness package
        sterling_bank_enrollees = [100552, 101401, 45492, 45509, 45537, 45704, 45711, 45712, 45747, 45748, 67106, 67113, 67132, 67133, 80701, 105096, 45532]
        #convert the sterling_bank_enrollees list to a string
        sterling_bank_enrollees = [str(i) for i in sterling_bank_enrollees]

        if client == 'UNITED BANK FOR AFRICA' and state == 'UBA HQ':
            available_provider = ['UBA Head Office (CERBA Onsite) - Marina, Lagos Island']
            selected_provider = st.selectbox('Pick your Preferred Wellness Facility',placeholder='Select a Provider', index=None, options=available_provider)

        elif client == 'UNITED BANK FOR AFRICA' and state == 'RIVERS':
            available_provider = ['PONYX HOSPITALS LTD - Plot 26,presidential estate, GRA phase iii, opp. NDDC H/Qrts, port- harcourt/ Aba expressway',
                                  'UNION DIAGNOSTICS - Finima Street, PortHarcourt, Rivers']
            selected_provider = st.selectbox('Pick your Preferred Wellness Facility', placeholder='Select a Provider', index=None, options=available_provider)
        elif client == 'STANDARD CHARTERED BANK NIGERIA LIMITED' and state == 'LAGOS':
            available_provider = wellness_providers.loc[wellness_providers['STATE'] == state, 'PROVIDER'].unique()
            additional_provider = 'Onsite - SCB Head Office - 142, Ahmadu Bello Way, Victoria Island'
            available_provider = list(available_provider) + [additional_provider]
            selected_provider = st.selectbox('Pick your Preferred Wellness Facility',placeholder='Select a Provider', index=None, options=available_provider)
        
        elif client == 'STANDARD CHARTERED BANK NIGERIA LIMITED' and state == 'RIVERS ':
            available_provider = wellness_providers.loc[wellness_providers['STATE'] == state, 'PROVIDER'].unique()
            additional_provider = 'Onsite - SCB Office, 143, Port Harcourt Aba Express Road (F-0)'
            available_provider = list(available_provider) + [additional_provider]
            selected_provider = st.selectbox('Pick your Preferred Wellness Facility',placeholder='Select a Provider', index=None, options=available_provider)

        elif client == 'STANDARD CHARTERED BANK NIGERIA LIMITED' and state == 'FCT':
            available_provider = wellness_providers.loc[wellness_providers['STATE'] == state, 'PROVIDER'].unique()
            additional_provider = 'Onsite - SCB Office, 374 Ademola Adetokunbo Crescent Wuse II, Beside Visa/Airtel Building'
            available_provider = list(available_provider) + [additional_provider]
            selected_provider = st.selectbox('Pick your Preferred Wellness Facility',placeholder='Select a Provider', index=None, options=available_provider)
        elif client == 'TRANSCORP POWER UGHELLI' and state == 'DELTA':
            available_provider = wellness_providers.loc[wellness_providers['STATE'] == state, 'PROVIDER'].unique()
            additional_provider = 'AVON MEDICAL SITE CLINIC, Ughelli'
            available_provider = list(available_provider) + [additional_provider]
            selected_provider = st.selectbox('Pick your Preferred Wellness Facility', placeholder='Select a Provider', index=None, options=available_provider)
        elif client == 'TRANS AFAM POWER PLANT LIMITED' and state == 'RIVERS':
            available_provider = wellness_providers.loc[wellness_providers['STATE'] == state, 'PROVIDER'].unique()
            additional_provider = 'AVON MEDICAL SITE CLINIC, Afam'
            available_provider = list(available_provider) + [additional_provider]
            selected_provider = st.selectbox('Pick your Preferred Wellness Facility', placeholder='Select a Provider', index=None, options=available_provider)
        elif client == 'TULIP COCOA PROCESSING' and state == 'OGUN':
            available_provider = wellness_providers.loc[wellness_providers['STATE'] == state, 'PROVIDER'].unique()
            additional_provider = 'AMAZING GRACE HOSPITAL - 7, Iloro Street, Ijebu-Ode, Ogun State'
            available_provider = list(available_provider) + [additional_provider]
            selected_provider = st.selectbox('Pick your Preferred Wellness Facility', placeholder='Select a Provider', index=None, options=available_provider)
        elif (client in ['HEIRS HOLDINGS', 'TRANSCORP PLC', 'TONY ELUMELU FOUNDATION']) and state == 'LAGOS' and relation in ['MEMBER', 'FEMALE MEMBER', 'MALE MEMBER']:
            # available_provider = wellness_providers.loc[wellness_providers['STATE'] == state, 'PROVIDER'].unique()
            available_provider = ['AVON Medical - Onsite']
            # available_provider = list(available_provider) + [additional_provider]
            selected_provider = st.selectbox('Assigned Wellness Facility', options=available_provider)
        # elif client == 'TRANSCORP PLC' and state == 'LAGOS':
        #     available_provider = wellness_providers.loc[wellness_providers['STATE'] == state, 'PROVIDER'].unique()
        #     additional_provider = 'AVON Medical - Onsite'
        #     available_provider = list(available_provider) + [additional_provider]
        #     selected_provider = st.selectbox('Pick your Preferred Wellness Facility', placeholder='Select a Provider', index=None, options=available_provider)
        elif client == 'AFRILAND PROPERTIES PLC' and state == 'LAGOS':
            available_provider = wellness_providers.loc[wellness_providers['STATE'] == state, 'PROVIDER'].unique()
            additional_provider = 'AVON Medical - Onsite'
            available_provider = list(available_provider) + [additional_provider]
            selected_provider = st.selectbox('Pick your Preferred Wellness Facility', placeholder='Select a Provider', index=None, options=available_provider)
        elif client == 'TRANSCORP HOTELS ABUJA' and state == 'FCT':
            available_provider = wellness_providers.loc[wellness_providers['STATE'] == state, 'PROVIDER'].unique()
            additional_provider = 'AVON Medical - Onsite'
            available_provider = list(available_provider) + [additional_provider]
            selected_provider = st.selectbox('Pick your Preferred Wellness Facility', placeholder='Select a Provider', index=None, options=available_provider)
        elif client == 'PIVOT GIS LIMITED' and state == 'LAGOS':
            available_provider = wellness_providers.loc[wellness_providers['STATE'] == state, 'PROVIDER'].unique()
            additional_provider = ['MECURE HEALTHCARE, OSHODI - Debo Industrial Cmpd, Plot 6, Block H, Oshodi Industrial Scheme',
                                  'MECURE HEALTHCARE, LEKKI - Niyi Okunubi Street, Off Admiralty way. Lekki phase 1',
                                  'CLINIX HEALTHCARE, ILUPEJU - Plot B, BLKXII, Alhaji Adejumo Avenue, Ilupeju, Lagos',
                                  'CLINIX HEALTHCARE, FESTAC - Dele Orisabiyi Street, Amuwo Odofin, Lagos'
                                    ]
            available_provider = list(available_provider) + additional_provider
            selected_provider = st.selectbox('Pick your Preferred Wellness Facility', placeholder='Select a Provider', index=None, options=available_provider)
        elif client == 'VERTEVILLE ENERGY' and state == 'LAGOS':
            available_provider = ['Union Diagnostics, V/I - 5 Eletu Ogabi Street, Off Adeola Odeku, Victoria Island, Lagos', 'CERBA Lancet, V/I - 3 Babatunde Jose Street, Adetokunbo Ademola']
            selected_provider = st.selectbox('Pick your Preferred Wellness Facility', placeholder='Select a Provider', index=None, options=available_provider)
        elif client == 'VERTEVILLE ENERGY' and state == 'DELTA':
            selected_provider = st.selectbox('Pick your Preferred Wellness Facility', placeholder='Select a Provider', index=None, options=['Union Diagnostics and Clinical Services - Onsite'])
        elif client == 'VERTEVILLE ENERGY' and state == 'BORNO':
            selected_provider = st.selectbox('Pick your Preferred Wellness Facility', placeholder='Select a Provider', index=None, options=['Kanem Hospital and Maternity - 152 Tafewa Balewa road, Opp Lamisula Police station, Mafoni ward, Maiduguri.'])
        elif client == 'VERTEVILLE ENERGY' and state == 'RIVERS':
            selected_provider = st.selectbox('Pick your Preferred Wellness Facility', placeholder='Select a Provider', index=None, options=['Union Diagnostic - Port-Harcourt: 2, Finima Street, Old GRA, Opp. Leventis bus-stop)'])
        elif client == 'PETROSTUFF NIGERIA LIMITED' and state == 'LAGOS':
            selected_provider = st.selectbox('Pick your Preferred Wellness Facility', placeholder='Select a Provider', index=None,
                                              options=['BEACON HEALTH - No 70, Fatai Arobieke Street, Lekki Phase 1, Lagos',
                                                       'AFRIGLOBAL MEDICARE DIAGNOSTIC CENTRE - 8 Mobolaji Bank Anthony Way Ikeja',
                                                       'UNION DIAGNOSTICS - 5,Eletu Ogabi street off Adeola odeku V.I'
                                                       ])
        elif client == 'PETROSTUFF NIGERIA LIMITED' and state == 'ABUJA':
            selected_provider = st.selectbox('Pick your Preferred Wellness Facility', placeholder='Select a Provider', index=None,
                                              options=['BODY AFFAIRS DIAGNOSTICS - 1349, Ahmadu Bello Way, Garki 2, Abuja'
                                                       ])
        elif client == 'PETROSTUFF NIGERIA LIMITED' and state == 'RIVERS':
            provider_options = [
            'PONYX HOSPITALS LTD'
            ]
            provider_addresses = {
            'PONYX HOSPITALS LTD': 'Plot 26, Presidential Estate, GRA Phase III, opp. NDDC H/Qrts, Port-Harcourt/Aba Expressway'
            }
            selected_provider_name = st.selectbox('Pick your Preferred Wellness Facility', placeholder='Select a Provider', index=None, options=provider_options)
            selected_provider = f"{selected_provider_name} - {provider_addresses[selected_provider_name]}" if selected_provider_name else ""
        elif client == 'TRANSCORP HILTON HOTEL ABUJA' and state == 'ABUJA':
            selected_provider = st.selectbox('Pick your Preferred Wellness Facility', options=['TRANSCORP/E-CLINIC WELLNESS'])

        #CUSTOMISED BRANCHING FOR REX INSURANCE LTD
        elif client == 'REX INSURANCE LTD' and state == 'LAGOS':
            available_provider = ['AFRIGLOBAL MEDICARE DIAGNOSTIC CENTRE - Plot 1192A Kasumu Ekemode St, Victoria Island, Lagos', 'CLINIX HEALTHCARE - Plot B, BLKXII, Alhaji Adejumo Avenue, Ilupeju, Lagos']
            selected_provider = st.selectbox('Pick your Preferred Wellness Facility', placeholder='Select a Provider', index=None, options=available_provider)
        elif client == 'REX INSURANCE LTD' and state == 'RIVERS':
            available_provider = ['PONYX HOSPITALS LTD - Plot 26, Presidential Estate, GRA Phase III, opp. NDDC H/Qrts, Port-Harcourt/Aba Expressway']
            selected_provider = st.selectbox('Pick your Preferred Wellness Facility', placeholder='Select a Provider', index=None, options=available_provider)
        elif client == 'REX INSURANCE LTD' and state == 'DELTA':
            available_provider = ['ECHOLAB - 375B Nnebisi Road, Umuagu, Asaba, Delta']
            selected_provider = st.selectbox('Pick your Preferred Wellness Facility', placeholder='Select a Provider', index=None, options=available_provider)
        elif client == 'REX INSURANCE LTD' and state == 'OYO':
            available_provider = ['BEACONHEALTH - 1, C.S Ola Street, Opposite Boldlink Ltd, Henry Tee Bus Stop, Ring Road, Ibadan']
            selected_provider = st.selectbox('Pick your Preferred Wellness Facility', placeholder='Select a Provider', index=None, options=available_provider)
        elif client == 'REX INSURANCE LTD' and state == 'KADUNA':
            available_provider = ['HARMONY HOSPITAL LTD - 74, Narayi Road, Barnawa, Kaduna']
            selected_provider = st.selectbox('Pick your Preferred Wellness Facility', placeholder='Select a Provider', index=None, options=available_provider)
        elif client == 'REX INSURANCE LTD' and state == 'KANO':
            available_provider = ['RAYSCAN DIAGNOSTICS LTD - Plot 4 Gyadi Court Road, Kano']
            selected_provider = st.selectbox('Pick your Preferred Wellness Facility', placeholder='Select a Provider', index=None, options=available_provider)
        else:
            available_provider = wellness_providers.loc[wellness_providers['STATE'] == state, 'ProviderLoc'].unique()
            select_provider = st.selectbox('Pick your Preferred Wellness Facility', placeholder='Select a Provider', index=None, options=available_provider)
            provider_match = wellness_providers.loc[wellness_providers['ProviderLoc'] == select_provider, 'PROVIDER'].values
            if provider_match.size > 0:
                selected_provider = provider_match[0]
            else:
                selected_provider = ""
                # st.warning("No provider found for the selected facility. Please select another option.")
 
        
        if client == 'UNITED BANK FOR AFRICA':
            if age >= 30 and gender == 'Female':
                benefits = 'Physical Exam, Blood Pressure Check, Fasting Blood Sugar, BMI, Urinalysis, Cholesterol, Genotype, Chest X-Ray, Cholesterol, Liver Function Test, Electrolyte,Urea and Creatinine Test(E/U/Cr), Packed Cell Volume(PCV), ECG, Visual Acuity, Mantoux Test, Cervical Smear, Mammogram'
            elif age >= 40 and gender == 'Male':
                benefits = 'Physical Exam, Blood Pressure Check, Fasting Blood Sugar, BMI, Urinalysis, Cholesterol, Genotype, Chest X-Ray, Cholesterol, Liver Function Test, Electrolyte,Urea and Creatinine Test(E/U/Cr), Packed Cell Volume(PCV), ECG, Visual Acuity, Mantoux Test, Prostrate Specific Antigen'
            else:
                benefits = 'Physical Exam, Blood Pressure Check, Fasting Blood Sugar, BMI, Urinalysis, Cholesterol, Genotype, Chest X-Ray, Cholesterol, Liver Function Test, Electrolyte,Urea and Creatinine Test(E/U/Cr), Packed Cell Volume(PCV), ECG, Visual Acuity, Mantoux Test'
        
        # elif client == 'PETROSTUFF NIGERIA LIMITED' and policy == 'PLUS PLAN 2019':
        #     benefits = 'Physical Examination, BP, BMI, Blood Sugar, Urinalysis, Genotype, Cholesterol, Mantoux/TB Test, Chest X-ray, Full Blood Count, Liver Function Test, Lipid Profile, Stool Microscopy, ECG, Hepatitis B Screening, HIV Screening, E/U/Cr'
        # elif client == 'PETROSTUFF NIGERIA LIMITED' and policy == 'PRESTIGE PLAN 2019':
        #     benefits = 'Physical Examination, BP, BMI, Blood Sugar, Urinalysis, Genotype, Cholesterol, Mantoux/TB Test, Chest X-ray, Full Blood Count, Liver Function Test, Lipid Profile, Stool Microscopy, ECG, Hepatitis B Screening, HIV Screening, E/U/Cr, PSA Men 40+'
        # elif client == 'PETROSTUFF NIGERIA LIMITED' and policy == 'PRESTIGE PLUS PLAN 2019':
        #     benefits = 'Physical Examination, BP, BMI, Blood Sugar, Urinalysis, Genotype, Cholesterol, Mantoux/TB Test, Chest X-ray, Full Blood Count, Liver Function Test, Lipid Profile, Stool Microscopy, ECG, Hepatitis B Screening, HIV Screening, E/U/Cr, PSA Men 40+'
        
        #create a different benefits for specific sterling bank enrollees based on their enrollee_id
        elif enrollee_id in sterling_bank_enrollees:
            benefits = 'Physical Exam, BP, Blood Sugar, Urinalysis, Chest X-Ray, Stool Microscopy, Cholesterol, Prostate Specific Antigen(PSA)'
        
        #create a different benefits for the customer experience loyalty reward
        elif enrollee_id in loyalty_enrollees['MemberNo'].values:
            benefits = (loyalty_enrollees.loc[loyalty_enrollees['MemberNo'] == enrollee_id, 'Eligible Services'].values[0] 
                        + "\nAdditional Test: " 
                        + loyalty_enrollees.loc[loyalty_enrollees['MemberNo'] == enrollee_id, 'Additional Services'].values[0]
                        )
            #create a different benefits package for etranzact enrollees based on their gender and age
        elif policy == 'TOTAL ENERGIES MANAGED CARE PLAN':
            if job_type == 'Offshore Personnel':
                benefits = 'Complete physical examination, Urinalysis, Fasting Blood Sugar, FBC, Lipid Profile, E/U/Cr, CRP, Liver Function test, Resting ECG, Audiometry, Chest X-ray indicated only at examiners request'
            elif job_type in ('Fire Team', 'MERT', 'Lab Personnel'):
                benefits = 'Complete physical examination, Urinalysis, Fasting Blood Sugar, FBC, Lipid Profile, E/U/Cr, CRP, Liver Function test, Resting ECG, Spirometry, Chest X-ray indicated only at examiners request'
            else:
                benefits = 'Complete physical examination, Urinalysis, Fasting Blood Sugar, FBC, Lipid Profile, E/U/Cr, CRP, Liver Function test, Resting ECG'
        # elif 
        elif client == 'ETRANZACT':
            if policy not in ('PLUS PLAN 2019', 'ETRANZACT PLUS PLAN NEW'):
                if age > 40 and gender == 'Male':
                    benefits = 'Physical Examination, Blood Pressure Check, Fasting Blood Sugar, Stool Microscopy, BMI, Urinalysis, Cholesterol, Genotype, Packed Cell Volume, Chest X-Ray, ECG, Liver Function Test, E/U/Cr, PSA'
                elif age > 40 and gender == 'Female':
                    benefits = 'Physical Examination, Blood Pressure Check, Fasting Blood Sugar, Stool Microscopy, BMI, Urinalysis, Cholesterol, Genotype, Packed Cell Volume, Chest X-Ray, ECG, Liver Function Test, E/U/Cr, Mamogram every 2 Years'
                elif 30 < age <= 40 and gender == 'Female':
                    benefits = 'Physical Examination, Blood Pressure Check, Fasting Blood Sugar, Stool Microscopy, BMI, Urinalysis, Cholesterol, Genotype, Packed Cell Volume, Chest X-Ray, ECG, Liver Function Test, E/U/Cr, Breast Scan every 2 Years'
                else:
                    benefits = 'Physical Examination, Blood Pressure Check, Fasting Blood Sugar, Stool Microscopy, BMI, Urinalysis, Cholesterol, Genotype, Packed Cell Volume, Chest X-Ray, ECG, Liver Function Test, E/U/Cr'
            else:
                benefits = package
        elif client == 'LADOL' and enrollee_id in ladol_special['MemberNo'].astype(str).values:
            benefits = ladol_special.loc[ladol_special['MemberNo'].astype(str) == enrollee_id, 'Eligible Tests'].values[0]
        else:
            benefits = package

        if client == 'PIVOT   GIS LIMITED':
            current_date = dt.date.today()
            # Define the maximum date as '2023-12-18' as a datetime.date object
            max_date = dt.date(2024, 12, 31)
            # Display a date picker
            selected_date = st.date_input("Select Your Preferred Appointment Date", min_value=current_date,max_value=max_date)
        elif client == 'UNITED BANK FOR AFRICA':
            if selected_provider == 'UBA Head Office (CERBA Onsite) - Marina, Lagos Island':
                selected_date = dt.date(2024, 1, 1)
            else:
                current_date = dt.date.today()
                # Define the maximum date as '2023-12-18' as a datetime.date object
                max_date = dt.date(2028, 2, 1)
                # Display a date picker
                selected_date = st.date_input("Select Your Preferred Appointment Date", min_value=current_date,max_value=max_date)
        else:
            max_date = dt.date(2027, 12, 31)
            selected_date = st.date_input('Pick Your Preferred Appointment Date',max_value=max_date)


        if (state == 'LAGOS') or (state == 'UBA HQ'):
            if selected_provider == 'UBA Head Office (CERBA Onsite) - Marina, Lagos Island':
                st.info('The date for your Wellness Exercise will be communicated to you by your HR. Kindly fill the questionaire below to complete your wellness booking')
                selected_date_str = 'To be Communicated by the HR'
                session = ''
                
            elif (selected_provider == 'CERBA LANCET NIGERIA - Ikeja - Aviation Plaza, Ground Floor, 31 Kodesoh Street, Ikeja') or (selected_provider == 'CERBA LANCET NIGERIA - Victoria Island - 3 Babatunde Jose Street Off Ademola Adetokunbo street, V/I'):        
                selected_date_str = selected_date.strftime('%Y-%m-%d')

                booked_sessions_from_db = filled_wellness_df.loc[(filled_wellness_df['selected_date'] == selected_date_str) &
                                                                (filled_wellness_df['selected_provider'] == selected_provider),
                                                                'selected_session'].values.tolist()

                available_sessions = ['08:00 AM - 09:00 AM', '09:00 AM - 10:00 AM', '10:00 AM - 11:00 AM', '11:00 AM - 12:00 PM',
                                        '12:00 PM - 01:00 PM', '01:00 PM - 02:00 PM', '02:00 PM - 03:00 PM', '03:00 PM - 04:00 PM']
                # Create a dictionary to keep track of the number of bookings for each session
                session_bookings_count = {session: booked_sessions_from_db.count(session) for session in available_sessions}

                # Filter available sessions to only include those with less than 3 bookings
                available_sessions = [session for session in available_sessions if session_bookings_count[session] < 3]
                st.info('Please note that the Facilities are opened between the 8:00 am and 5:00 pm, Monday - Friday and 8:00 am - 2:00 pm on \
                        Saturdays.\n\n If you notice any missing session between their opening hours, this implies that the missing session has been\
                        fully booked and no longer available for the selected date')
                
                if not available_sessions:
                    st.warning("All sessions for the selected date at this facility are fully booked. Please select another date or facility.")
                else:
                    session = st.radio('Select your preferred time from the list of available sessions below', options=available_sessions)
                    st.info('Fill the questionaire below to complete your wellness booking')
            else:
                selected_date_str = selected_date.strftime('%Y-%m-%d')
                session = ''
                st.info('Fill the questionaire below to complete your wellness booking')

        else:
            selected_date_str = selected_date.strftime('%Y-%m-%d')
            session = ''
            st.info('Fill the questionaire below to complete your wellness booking')

        # Define a list of Family Medical History Conditions
        questions1 = [
            'a. HYPERTENSION (HIGH BLOOD PRESSURE)',
            'b. DIABETES',
            'c. CANCER (ANY TYPE)',
            'd. ASTHMA',
            'e. ARTHRITIS',
            'f. HIGH CHOLESTEROL',
            'g. HEART ATTACK',
            'h. EPILEPSY',
            'i. TUBERCLOSIS',
            'j. SUBSTANCE DEPENDENCY',
            'k. MENTAL ILLNESS',
        ]

        # Define the generic options
        options1 = ["Grand Parent(s)", "Parent(s)", "Uncle/Aunty", "Nobody"]

        # Label the section accordingly
        st.title("1. Family Medical History")
        st.subheader('Have any of your family members experienced any of the following conditions?')


        # Create a dictionary to store user responses
        user_responses1 = {}

        for question1 in questions1:
            st.markdown(f"**{question1}**")  # Display the question in bold

            # Use radio buttons for these set of questions with a unique key
            unique_key1 = f"{question1}_response"
            response1 = st.radio(f'Response to {question1}', options1, key=unique_key1, label_visibility='collapsed')

            # Store the response in the dictionary
            user_responses1[question1] = response1

        # Assign the user's responses to a variable
        resp_1_a = user_responses1['a. HYPERTENSION (HIGH BLOOD PRESSURE)']
        resp_1_b = user_responses1['b. DIABETES']
        resp_1_c = user_responses1['c. CANCER (ANY TYPE)']
        resp_1_d = user_responses1['d. ASTHMA']
        resp_1_e = user_responses1['e. ARTHRITIS']
        resp_1_f = user_responses1['f. HIGH CHOLESTEROL']
        resp_1_g = user_responses1['g. HEART ATTACK']
        resp_1_h = user_responses1['h. EPILEPSY']
        resp_1_i = user_responses1['i. TUBERCLOSIS']
        resp_1_j = user_responses1['j. SUBSTANCE DEPENDENCY']
        resp_1_k = user_responses1['k. MENTAL ILLNESS']
        


        # Define a list of personal medical history questions
        questions2 = [
            'i. HYPERTENSION (HIGH BLOOD PRESSURE)',
            'ii. DIABETES',
            'iii. CANCER (ANY TYPE)',
            'iv. ASTHMA',
            'v. ULCER',
            'vi. POOR VISION',
            'vii. ALLERGY',
            'viii. ARTHRITIS/LOW BACK PAIN',
            'ix. ANXIETY/DEPRESSION',
        ]

        # Define the generic responses for these set of questions
        options2 = ['Yes', 'No', 'Yes, but not on Medication']

        # Label the section accordingly
        st.title("2. Personal Medical History")
        st.subheader('Do you have any of the following condition(s) that you are managing?')

        # Create a dictionary to store user responses
        user_responses2 = {}

        for question2 in questions2:
            st.markdown(f"**{question2}**")  # Display the question in bold

            # Use radio buttons for these set of questions with a unique key
            unique_key2 = f"{question2}_response"
            response2 = st.radio(f'Response to {question2}', options2, key=unique_key2, label_visibility='collapsed')

            # Store the response in the dictionary
            user_responses2[question2] = response2

        # Assign the user's responses to a variable
        resp_2_a = user_responses2['i. HYPERTENSION (HIGH BLOOD PRESSURE)']
        resp_2_b = user_responses2['ii. DIABETES']
        resp_2_c = user_responses2['iii. CANCER (ANY TYPE)']
        resp_2_d = user_responses2['iv. ASTHMA']
        resp_2_e = user_responses2['v. ULCER']
        resp_2_f = user_responses2['vi. POOR VISION']
        resp_2_g = user_responses2['vii. ALLERGY']
        resp_2_h = user_responses2['viii. ARTHRITIS/LOW BACK PAIN']
        resp_2_i = user_responses2['ix. ANXIETY/DEPRESSION']
        
        # Define a list of surgery related survey questions
        questions3 = [
            'i. CEASAREAN SECTION',
            'ii. FRACTURE REPAIR',
            'iii. HERNIA',
            'iv. LUMP REMOVAL',
            'v. APPENDICETOMY',
            'vi. SPINE SURGERY',
        ]

        # Define the generic options for these set of questions
        options3 = ['Yes', 'No']

        # Create a Streamlit app
        st.title("3. Personal Surgical History")
        st.subheader('Have you ever had surgery for any of the following?')

        # Create a dictionary to store user responses
        user_responses3 = {}

        for question3 in questions3:
            st.markdown(f"**{question3}**")  # Display the question in bold

            # Use radio buttons for these set of questions with a unique key
            unique_key3 = f"{question3}_response"
            response3 = st.radio(f'Response to {question2}', options3, key=unique_key3, label_visibility='collapsed')

            # Store the response in the dictionary
            user_responses3[question3] = response3

        # Assign the user's responses to a variable
        resp_3_a = user_responses3['i. CEASAREAN SECTION']
        resp_3_b = user_responses3['ii. FRACTURE REPAIR']
        resp_3_c = user_responses3['iii. HERNIA']
        resp_3_d = user_responses3['iv. LUMP REMOVAL']
        resp_3_e = user_responses3['v. APPENDICETOMY']
        resp_3_f = user_responses3['vi. SPINE SURGERY']

        
        # Define a list of emotional wellness related survey questions
        questions4 = [
            'a. I avoid eating foods that are high in fat',
            'b. I have been avoiding the use or minimise my exposure to alcohol',
            'c. I have been avoiding the use of tobacco products',
            'd. I am physically fit and exercise at least 30 minutes every day',
            'e. I have been eating vegetables and fruits at least 3 times weekly',
            'f. I drink 6-8 glasses of water a day',
            'g. I maintain my weight within the recommendation for my weight, age and height',
            'h. My blood pressure is within normal range without the use of drugs',
            'i. My cholesterol level is within the normal range',
            'j. I easily make decisions without worry',
            'k. I enjoy more than 5 hours of sleep at night',
            'l. I enjoy my work and life',
            'm. I enjoy the support from friends and family',
            'n. I feel bad about myself or that I am a failure or have let myself or my family down',
            'o. I have poor appetite or I am over-eating',
            'p. I feel down, depressed, hopeless, tired or have little energy',
            'q. I have trouble falling asleep, staying asleep, or sleeping too much',
            'r. I have no interest or pleasure in doing things',
            's. I have trouble concentrating on things, such as reading the newspaper, or watching TV',
            't. I think I would be better off dead or better off hurting myself in some way',
        ]

        # Define the generic options for these set of questions
        options4 = ['Never', 'Occasional', 'Always', 'I Do Not Know']

        # Create a Streamlit app
        st.title("4. Health Survey Questionnaire")
        st.subheader('Kindly provide valid responses to the following questions')

        # Create a dictionary to store user responses
        user_responses4 = {}

        for question4 in questions4:
            st.markdown(f"**{question4}**")  # Display the question in bold

            # Use radio buttons for Likert scale with a unique key
            unique_key4 = f"{question4}_response"
            response4 = st.radio(f'Response to {question4}', options4, key=unique_key4, label_visibility='collapsed')

            # Store the response in the dictionary
            user_responses4[question4] = response4

        # Assign the user's responses to a variable
        resp_4_a = user_responses4['a. I avoid eating foods that are high in fat']
        resp_4_b = user_responses4['b. I have been avoiding the use or minimise my exposure to alcohol']
        resp_4_c = user_responses4['c. I have been avoiding the use of tobacco products']
        resp_4_d = user_responses4['d. I am physically fit and exercise at least 30 minutes every day']
        resp_4_e = user_responses4['e. I have been eating vegetables and fruits at least 3 times weekly']
        resp_4_f = user_responses4['f. I drink 6-8 glasses of water a day']
        resp_4_g = user_responses4['g. I maintain my weight within the recommendation for my weight, age and height']
        resp_4_h = user_responses4['h. My blood pressure is within normal range without the use of drugs']
        resp_4_i = user_responses4['i. My cholesterol level is within the normal range']
        resp_4_j = user_responses4['j. I easily make decisions without worry']
        resp_4_k = user_responses4['k. I enjoy more than 5 hours of sleep at night']
        resp_4_l = user_responses4['l. I enjoy my work and life']
        resp_4_m = user_responses4['m. I enjoy the support from friends and family']
        resp_4_n = user_responses4['n. I feel bad about myself or that I am a failure or have let myself or my family down']
        resp_4_o = user_responses4['o. I have poor appetite or I am over-eating']
        resp_4_p = user_responses4['p. I feel down, depressed, hopeless, tired or have little energy']
        resp_4_q = user_responses4['q. I have trouble falling asleep, staying asleep, or sleeping too much']
        resp_4_r = user_responses4['r. I have no interest or pleasure in doing things']
        resp_4_s = user_responses4['s. I have trouble concentrating on things, such as reading the newspaper, or watching TV']
        resp_4_t = user_responses4['t. I think I would be better off dead or better off hurting myself in some way']
        

        # Submit button
        if st.button("Submit", help="Click to submit"):
            st.session_state.user_data['member_number'] = enrollee_id
            st.session_state.user_data['EnrolleeName'] = enrollee_name
            st.session_state.user_data['client'] = client
            st.session_state.user_data['policy'] = policy
            st.session_state.user_data['policystart'] = policystart
            st.session_state.user_data['policyend'] = policyend
            st.session_state.user_data['email'] = email
            st.session_state.user_data['mobile_num'] = mobile_num
            st.session_state.user_data['age'] = age
            st.session_state.user_data['state'] = state
            st.session_state.user_data['selected_provider'] = selected_provider
            st.session_state.user_data['job_type'] = job_type
            st.session_state.user_data['gender'] = gender
            st.session_state.user_data['wellness_benefit'] = benefits
            st.session_state.user_data['selected_date_str'] = selected_date_str
            st.session_state.user_data['session'] = session
            st.session_state.user_data['resp_1_a'] = resp_1_a
            st.session_state.user_data['resp_1_b'] = resp_1_b
            st.session_state.user_data['resp_1_c'] = resp_1_c
            st.session_state.user_data['resp_1_d'] = resp_1_d
            st.session_state.user_data['resp_1_e'] = resp_1_e
            st.session_state.user_data['resp_1_f'] = resp_1_f
            st.session_state.user_data['resp_1_g'] = resp_1_g
            st.session_state.user_data['resp_1_h'] = resp_1_h
            st.session_state.user_data['resp_1_i'] = resp_1_i
            st.session_state.user_data['resp_1_j'] = resp_1_j
            st.session_state.user_data['resp_1_k'] = resp_1_k
            st.session_state.user_data['resp_2_a'] = resp_2_a
            st.session_state.user_data['resp_2_b'] = resp_2_b
            st.session_state.user_data['resp_2_c'] = resp_2_c
            st.session_state.user_data['resp_2_d'] = resp_2_d
            st.session_state.user_data['resp_2_e'] = resp_2_e
            st.session_state.user_data['resp_2_f'] = resp_2_f
            st.session_state.user_data['resp_2_g'] = resp_2_g
            st.session_state.user_data['resp_2_h'] = resp_2_h
            st.session_state.user_data['resp_2_i'] = resp_2_i
            st.session_state.user_data['resp_3_a'] = resp_3_a
            st.session_state.user_data['resp_3_b'] = resp_3_b
            st.session_state.user_data['resp_3_c'] = resp_3_c
            st.session_state.user_data['resp_3_d'] = resp_3_d
            st.session_state.user_data['resp_3_e'] = resp_3_e
            st.session_state.user_data['resp_3_f'] = resp_3_f
            st.session_state.user_data['resp_4_a'] = resp_4_a
            st.session_state.user_data['resp_4_b'] = resp_4_b
            st.session_state.user_data['resp_4_c'] = resp_4_c
            st.session_state.user_data['resp_4_d'] = resp_4_d
            st.session_state.user_data['resp_4_e'] = resp_4_e
            st.session_state.user_data['resp_4_f'] = resp_4_f
            st.session_state.user_data['resp_4_g'] = resp_4_g
            st.session_state.user_data['resp_4_h'] = resp_4_h
            st.session_state.user_data['resp_4_i'] = resp_4_i
            st.session_state.user_data['resp_4_j'] = resp_4_j
            st.session_state.user_data['resp_4_k'] = resp_4_k
            st.session_state.user_data['resp_4_l'] = resp_4_l
            st.session_state.user_data['resp_4_m'] = resp_4_m
            st.session_state.user_data['resp_4_n'] = resp_4_n
            st.session_state.user_data['resp_4_o'] = resp_4_o
            st.session_state.user_data['resp_4_p'] = resp_4_p
            st.session_state.user_data['resp_4_q'] = resp_4_q
            st.session_state.user_data['resp_4_r'] = resp_4_r
            st.session_state.user_data['resp_4_s'] = resp_4_s
            st.session_state.user_data['resp_4_t'] = resp_4_t

            #initialise an empty list to store missing fields
            missing_fields = []

            #check each required field
            if not email:
                missing_fields.append('Email')
            if not mobile_num:
                missing_fields.append('Mobile Number')
            if not state:
                missing_fields.append('Your Current Location')
            if not selected_provider:
                missing_fields.append('Preferred Wellness Facility')
            
            if missing_fields:
                st.error(f"The following field(s) are required: {', '.join(missing_fields)}")
            else:

                cursor = conn.cursor()
                try:
                    # Define an SQL INSERT statement to add data to your database table
                    insert_query = """
                    INSERT INTO [dbo].[tbl_annual_wellness_enrollee_data] (MemberNo, MemberName, client, policy,policystartdate, policyenddate, email, mobile_num, job_type, age, state, selected_provider,
                    sex, wellness_benefits, selected_date, selected_session,
                    [HIGH BLOOD PRESSURE - Family],[Diabetes - Family],[Cancer - Family],[Asthma - Family],[Arthritis - Family]
                    ,[High Cholesterol],[Heart Attack - Family],[Epilepsy - Family],[Tuberclosis - Family],[Substance Dependency - Family]
                    ,[Mental Illness - Family],[HIGH BLOOD PRESSURE - Personal],[Diabetes - Personal],[Cancer - Personal],[Asthma - Personal]
                    ,[Ulcer - Personal],[Poor Vision - Personal],[Allergy - Personal],[Arthritis/Low Back Pain - Personal],[Anxiety/Depression - Personal]
                    ,[CEASAREAN SECTION],[FRACTURE REPAIR],[HERNIA],[LUMP REMOVAL] ,[APPENDICETOMY],[SPINE SURGERY],[I AVOID EATING FOODS THAT ARE HIGH IN FAT]
                    ,[I AVOID THE USE OR MINIMISE MY EXPOSURE TO ALCOHOL],[I AVOID THE USE OF TOBACCO PRODUCTS],[I AM PHYSICALLY FIT AND EXERCISE AT LEAST 30 MINUTES EVERY DAY]
                    ,[I EAT VEGETABLES AND FRUITS AT LEAST 3 TIMES WEEKLY],[I DRINK 6-8 GLASSES OF WATER A DAY],[I MAINTAIN MY WEIGHT WITHIN THE RECOMMENDATION FOR MY WEIGHT, AGE AND HEIGHT]
                    ,[MY BLOOD PRESSURE IS WITHIN NORMAL RANGE WITHOUT THE USE OF DRUGS],[MY CHOLESTEROL LEVEL IS WITHIN THE NORMAL RANGE]
                    ,[I EASILY MAKE DECISIONS WITHOUT WORRY],[I ENJOY MORE THAN 5 HOURS OF SLEEP AT NIGHT],[I ENJOY MY WORK AND LIFE]
                    ,[I ENJOY THE SUPPORT FROM FRIENDS AND FAMILY],[I FEEL BAD ABOUT MYSELF OR THAT I AM A FAILURE OR HAVE LET MYSELF OR MY FAMILY DOWN]
                    ,[I HAVE POOR APPETITE OR I AM OVER-EATING],[I FEEL DOWN, DEPRESSED, HOPELESS, TIRED OR HAVE LITTLE ENERGY]
                    ,[I HAVE TROUBLE FALLING ASLEEP, STAYING ASLEEP, OR SLEEPING TOO MUCH],[I HAVE NO INTEREST OR PLEASURE IN DOING THINGS]
                    ,[I HAVE TROUBLE CONCENTRATING ON THINGS, SUCH AS READING THE NEWSPAPER, OR WATCHING TV]
                    ,[THOUGHT THAT I WOULD BE BETTER OFF DEAD OR BETTER OFF HURTING MYSELF IN SOME WAY],
                    date_submitted)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """

                    # Execute the INSERT statement with the user's data
                    cursor.execute(insert_query, (
                        st.session_state.user_data['member_number'],
                        st.session_state.user_data['EnrolleeName'],
                        st.session_state.user_data['client'],
                        st.session_state.user_data['policy'],
                        st.session_state.user_data['policystart'],
                        st.session_state.user_data['policyend'],
                        st.session_state.user_data['email'],
                        st.session_state.user_data['mobile_num'],
                        st.session_state.user_data['job_type'],
                        st.session_state.user_data['age'],
                        st.session_state.user_data['state'],
                        st.session_state.user_data['selected_provider'],
                        st.session_state.user_data['gender'],
                        st.session_state.user_data['wellness_benefit'],
                        st.session_state.user_data['selected_date_str'],
                        st.session_state.user_data['session'],
                        st.session_state.user_data['resp_1_a'],
                        st.session_state.user_data['resp_1_b'],
                        st.session_state.user_data['resp_1_c'],
                        st.session_state.user_data['resp_1_d'],
                        st.session_state.user_data['resp_1_e'],
                        st.session_state.user_data['resp_1_f'],
                        st.session_state.user_data['resp_1_g'],
                        st.session_state.user_data['resp_1_h'],
                        st.session_state.user_data['resp_1_i'],
                        st.session_state.user_data['resp_1_j'],
                        st.session_state.user_data['resp_1_k'],
                        st.session_state.user_data['resp_2_a'],
                        st.session_state.user_data['resp_2_b'],
                        st.session_state.user_data['resp_2_c'],
                        st.session_state.user_data['resp_2_d'],
                        st.session_state.user_data['resp_2_e'],
                        st.session_state.user_data['resp_2_f'],
                        st.session_state.user_data['resp_2_g'],
                        st.session_state.user_data['resp_2_h'],
                        st.session_state.user_data['resp_2_i'],
                        st.session_state.user_data['resp_3_a'],
                        st.session_state.user_data['resp_3_b'],
                        st.session_state.user_data['resp_3_c'],
                        st.session_state.user_data['resp_3_d'],
                        st.session_state.user_data['resp_3_e'],
                        st.session_state.user_data['resp_3_f'],
                        st.session_state.user_data['resp_4_a'],
                        st.session_state.user_data['resp_4_b'],
                        st.session_state.user_data['resp_4_c'],
                        st.session_state.user_data['resp_4_d'],
                        st.session_state.user_data['resp_4_e'],
                        st.session_state.user_data['resp_4_f'],
                        st.session_state.user_data['resp_4_g'],
                        st.session_state.user_data['resp_4_h'],
                        st.session_state.user_data['resp_4_i'],
                        st.session_state.user_data['resp_4_j'],
                        st.session_state.user_data['resp_4_k'],
                        st.session_state.user_data['resp_4_l'],
                        st.session_state.user_data['resp_4_m'],
                        st.session_state.user_data['resp_4_n'],
                        st.session_state.user_data['resp_4_o'],
                        st.session_state.user_data['resp_4_p'],
                        st.session_state.user_data['resp_4_q'],
                        st.session_state.user_data['resp_4_r'],
                        st.session_state.user_data['resp_4_s'],
                        st.session_state.user_data['resp_4_t'],
                        dt.datetime.now()
                    ))

                    # Commit the transaction to save the data to the database
                    conn.commit()

                    # Provide feedback to the user
                    st.info(f'Thank you {enrollee_name}.\n\n'
                        f'Your annual wellness has been successfully booked.\n\n'
                        f'###Please note that you have from now till {six_weeks} to complete your annual wellness exercise.')

                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

                finally:
                    # Close the cursor and the database connection
                    cursor.close()
                    conn.close()

                    recipient_email = email
                    subject = 'AVON ENROLLEE WELLNESS APPOINTMENT CONFIRMATION'
                    # Create a table (HTML format) with some sample data
                    msg_befor_table = f'''
                    Dear {enrollee_name},<br><br>
                    We hope you are staying safe.<br><br>
                    You have been scheduled for a wellness screening at your selected provider, see the below table for details.<br><br>
                    '''
                    #create a table with the booking information
                    wellness_table = {
                        "Appointment Date": [selected_date_str + ' - ' + session],
                        "Wellness Facility": [selected_provider],
                        "Wellness Benefits": [benefits]
                    }

                    #convert the wellness_table to a html table
                    wellness_table_html = pd.DataFrame(wellness_table).to_html(index=False, escape=False, justify='center')

                    #initialise an empty table
                    table_html = f"""
                    <style>
                    table {{
                            border: 1px solid #1C6EA4;
                            background-color: #EEEEEE;
                            width: 100%;
                            text-align: left;
                            border-collapse: collapse;
                            }}
                            table td, table th {{
                            border: 1px solid #AAAAAA;
                            padding: 3px 2px;
                            }}
                            table tbody td {{
                            font-size: 13px;
                            }}
                            table thead {{
                            background: #59058D;
                            border-bottom: 2px solid #444444;
                            }}
                            table thead th {{
                            font-size: 15px;
                            font-weight: bold;
                            color: #FFFFFF;
                            border-left: 2px solid #D0E4F5;
                            }}
                            table thead th:first-child {{
                            border-left: none;
                            }}
                    </style>
                    <table>
                    {wellness_table_html}
                    </table>
                    """

                    # table_html += f"""
                    # <tr>
                    #     <td>{selected_date_str} - {session}</td>
                    #     <td>{selected_provider}</td>
                    #     <td>{benefits}</td>
                    # </tr>
                    # """

                    # table_html += "</table>" #close the table

                    #customised text for upcountry
                    text_after_table = f'''
                    <br>Kindly note the following requirements for your wellness exercise:<br><br>

                    -Present at the hospital with your Avon member ID number ({enrollee_id})/ Ecard.<br>
                    -Provide the facility with your valid email address to mail your result.<br>
                    -Visit your designated centers between the hours of 8 am - 11 am any day of the week from the scheduled date communicated.<br>
                    -Arrive at the facility fasting i.e. last meals should be before 9 pm the previous night and nothing should be eaten that morning before the test.
                    You are allowed to drink up to two cups of water.<br><br>

                    For the best results of your screening, it is advisable for blood tests to be done on or before 10 am.<br><br>
                    Your results will be strictly confidential and will be sent to you directly via your email. You are advised to review
                    your results with your primary care provider for relevant medical advice.<br><br>

                    <b>Kindly note that your wellness result will only be available two (2) weeks after your visit to the provider for your wellness check.</b><br><br>

                    Should you require assistance at any time or wish to make any complaint about the service at any of the facilities, 
                    please contact our Call-Center at 0700-277-9800  or send us a chat on WhatsApp at 0912-603-9532. 
                    You can also send us an email at callcentre@avonhealthcare.com. Please be assured that an agent would always be on standby to assist you.<br><br>

                    Thank you for choosing Avon HMO,<br><br>

                    Medical Services.<br>

                    '''

                    #customised text for Lagos enrollees
                    text_after_table1 = f'''
                    <br>Kindly note that wellness exercise at your selected facility is strictly by appointment and
                    and you are expected to be available at the facility on the appointment date as selected by you.<br><br>
                    Also, note that you will be required to:<br><br>

                    -Present at the facility with your Avon member ID number ({enrollee_id})/ Ecard.<br>
                    -Provide the facility with your valid email address to mail your result.<br>
                    -You are advised to be present at your selected facility 15 mins before your scheduled time.<br><br>
                    
                    Your results will be strictly confidential and will be sent to you directly via your email. You are advised to review
                    your results with your primary care provider for relevant medical advice.<br><br>

                    <b>Kindly note that your wellness result will only be available two (2) weeks after your visit to the provider for your wellness check.</b><br><br>

                    Should you require assistance at any time or wish to make any complaint about the service at any of the facilities, 
                    please contact our Call-Center at 0700-277-9800  or send us a chat on WhatsApp at 0912-603-9532. 
                    You can also send us an email at callcentre@avonhealthcare.com. Please be assured that an agent would always be on standby to assist you.<br><br>

                    Thank you for choosing Avon HMO,<br><br>

                    Medical Services.<br>

                    '''
                    head_office_msg = f'''
                    Dear {enrollee_name},<br><br>
                    We hope you are staying safe.<br><br>
                    You have been scheduled for a wellness screening at {selected_provider}.<br><br>
                    Find listed below your wellness benefits:<br><br><b>{benefits}</b>.<br><br>
                    Kindly note the following regarding your wellness appointment:<br><br>
                    - HR will reach out to you with a scheduled date and time for your annual wellness.<br><br>
                    - Once scheduled, you are to present your Avon HMO ID card or member ID - {enrollee_id} at the point of accessing your annual wellness check.<br><br>
                    - The wellness exercise will take place at the designated floor which will be communicated to you by the HR between 9 am and 4 pm from Monday – Friday. <br><br>
                    - For the most accurate fasting blood sugar test results, it is advisable for blood tests to be done before 10am. <br><br>
                    - Staff results will be sent to the email addresses provided by them to the wellness providers.<br><br>
                    - There will be consultation with a physician to review immediate test results on-site while other test results that are not readily available will be reviewed by a physician at your Primary Care Provider.<br><br>
                    
                    Should you require assistance at any time or wish to make any complaint about the service rendered during this wellness exercise,
                    please contact our Call-Center at 0700-277-9800 or send us a chat on WhatsApp at 0912-603-9532.
                    You can also send us an email at callcentre@avonhealthcare.com. Please be assured that an agent would always be on standby to assist you.<br><br>
                    Thank you for choosing Avon HMO.<br><br>
                    Medical Services.<br>
                    '''

                    pivotgis_msg = f'''
                    <br>Kindly note that this wellness activation is only valid till the 31st of December, 2023.<br><br>
                    Also, note that you will be required to:<br><br>

                    -Present at the hospital with your Avon member ID number ({enrollee_id})/ Ecard.<br>
                    -Provide the facility with your valid email address to mail your result.<br>
                    -You are advised to be present at your selected facility 15 mins before your scheduled time.<br><br>
                    
                    Your results will be strictly confidential and will be sent to you directly via your email. You are advised to review
                    your results with your primary care provider for relevant medical advice.<br><br>

                    <b>Kindly note that your wellness result will only be available two (2) weeks after your visit to the provider for your wellness check.</b><br><br>

                    Should you require assistance at any time or wish to make any complaint about the service at any of the facilities, 
                    please contact our Call-Center at 0700-277-9800  or send us a chat on WhatsApp at 0912-603-9532. 
                    You can also send us an email at callcentre@avonhealthcare.com. Please be assured that an agent would always be on standby to assist you.<br><br>

                    Thank you for choosing Avon HMO,<br><br>

                    Medical Services.<br>
                    '''

                    # html_string = f'''<!DOCTYPE html>
                    #     <html lang="en">
                    #     <head>
                    #         <meta charset="UTF-8">
                    #         <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    #         <title>Email Message</title>
                    #         <style>
                    #             /* Define your styles here */

                    #             .email-container {{
                    #                 max-width: 600px;
                    #                 margin: 0 auto;
                    #                 padding: 20px;
                    #                 border: 1px solid #ccc;
                    #                 border-radius: 10px;
                    #             }}
                    #             .company-logo {{
                    #                 max-width: 150px;
                    #                 height: auto;
                    #                 margin-bottom: 20px;
                    #             }}
                    #             .table-container {{
                    #                 border: 1px solid #1C6EA4;
                    #                 background-color: #EEEEEE;
                    #                 width: 100%;
                    #                 text-align: left;
                    #                 border-collapse: collapse;
                    #                 margin-bottom: 20px;
                    #             }}
                    #             .table-container td, .table-container th {{
                    #                 border: 1px solid #AAAAAA;
                    #                 padding: 3px 2px;
                    #             }}
                    #             .table-container tbody td {{
                    #                 font-size: 13px;
                    #             }}
                    #             .table-container thead {{
                    #                 background: #59058D;
                    #                 border-bottom: 2px solid #444444;
                    #             }}
                    #             .table-container thead th {{
                    #                 font-size: 15px;
                    #                 font-weight: bold;
                    #                 color: #FFFFFF;
                    #                 border-left: 2px solid #D0E4F5;
                    #             }}
                    #             .table-container thead th:first-child {{
                    #                 border-left: none;
                    #             }}
                    #         </style>
                    #     </head>
                    #     <body>
                    #         <div class="email-container">
                    #             <img src="wellness_image.png" alt="Company Logo" class="company-logo">
                    #             <div class="table-container">
                    #                 <!-- Your table HTML goes here -->
                    #                 <table>
                    #                     {wellness_table_html}
                    #                 </table>
                    #             </div>
                    #             <!-- Additional text after the table -->
                    #             <p>{text_after_table}</p>
                    #         </div>
                    #     </body>
                    #     </html>
                    #     '''

                    #put the table and text together in a text border with an image added

                    upcountry_message = msg_befor_table + table_html + text_after_table
                    cerba_message = msg_befor_table + table_html + text_after_table1
                    pivot_msg = msg_befor_table + table_html + pivotgis_msg
                
                    myemail = 'noreply@avonhealthcare.com'
                    password = os.environ.get('emailpassword')
                    # password = st.secrets["emailpassword"]
                    #add a condition to use the citron_bcc_list whenever any of the CITRON wellness providers is selected by the enrollee
                    if (selected_provider == 'ECHOLAB - Opposite mararaba medical centre, Tipper Garage, Mararaba') or (selected_provider == 'TOBIS CLINIC - Chief Melford Okilo Road Opposite Sobaz Filling Station, Akenfa –Epie') or (selected_provider == 'ECHOLAB - 375B Nnebisi Road, Umuagu, Asaba'):
                        bcc_email_list = ['ademola.atolagbe@avonhealthcare.com', 'client.services@avonhealthcare.com',
                                    'callcentre@avonhealthcare.com','medicalservicesdepartment@avonhealthcare.com', 
                                    'adeoluwa@citron-health.com', 'hello@citron-health.com']
                    else:
                        bcc_email_list = ['ademola.atolagbe@avonhealthcare.com', 'client.services@avonhealthcare.com',
                                    'callcentre@avonhealthcare.com','medicalservicesdepartment@avonhealthcare.com']
                        
                    to_email_list =[recipient_email]

                    try:
                        server = smtplib.SMTP('smtp.office365.com', 587)
                        server.starttls()

                        #login to outlook account
                        server.login(myemail, password)

                        #create a MIMETesxt object for the email message
                        msg = MIMEMultipart()
                        msg['From'] = 'AVON HMO Client Services'
                        msg['To'] = recipient_email
                        msg['Bcc'] = ', '.join(bcc_email_list)
                        msg['Subject'] = subject
                        if client == 'UNITED BANK FOR AFRICA':
                            if selected_provider == 'UBA Head Office - Marina, Lagos Island.':
                                msg.attach(MIMEText(head_office_msg, 'html'))
                            # elif selected_provider == 'UBA FESTAC Branch.':
                            #     msg.attach(MIMEText(festac_office_msg, 'html'))
                            elif (selected_provider == 'CERBA LANCET NIGERIA - Ikeja - Aviation Plaza, Ground Floor, 31 Kodesoh Street, Ikeja') or (selected_provider == 'CERBA LANCET NIGERIA - Victoria Island - 3 Babatunde Jose Street Off Ademola Adetokunbo street, V/I'):
                                msg.attach(MIMEText(cerba_message, 'html'))
                            else:
                                msg.attach(MIMEText(upcountry_message, 'html'))
                        else:
                            msg.attach(MIMEText(upcountry_message, 'html'))


                        all_recipients = to_email_list + bcc_email_list
                        #send the email
                        server.sendmail(myemail, all_recipients, msg.as_string())
                        server.quit()

                        st.success(f'A confirmation Email has been sent to your provided email\n\n'
                                   f'Kindly note that your wellness result will only be available two (2) weeks after your visit to the provider for your wellness check.')
                    except Exception as e:
                        st.error(f'An error occurred: {e}')
       
    elif enrollee_id not in wellness_df['memberno'].values:
        st.info('You are not eligible to participate, please contact your HR or Client Manager')
else:
    st.write('You must input your Member number to continue')