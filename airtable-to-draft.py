import configparser
import requests
import base64
import json
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader

# Constants for file paths
TOKEN_FILE = "token.json"  # File to store Gmail API token

# Load settings from config.ini file
config = configparser.ConfigParser()
config.read('config.ini')

# Airtable settings loaded from config file
AIRTABLE_BASE_ID = config['Airtable']['AIRTABLE_BASE_ID']
AIRTABLE_API_KEY = config['Airtable']['AIRTABLE_API_KEY']
AIRTABLE_TABLE_NAME = config['Airtable']['AIRTABLE_TABLE_NAME']
VIEW_NAME = config['Airtable']['VIEW_NAME']

# Gmail settings loaded from config file
GMAIL_USER_ID = config['Gmail']['GMAIL_USER_ID']
EMAIL_CC = config['Gmail']['EMAIL_CC']
CREDENTIALS_FILE = config['Gmail']['CREDENTIALS_FILE']
SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]

def get_airtable_data():
    # Fetch data from Airtable using the API
    try:
        url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}?view={VIEW_NAME}"
        headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from Airtable: {e}")
        return None

def create_message(to, subject, body):
    # Create an email message in MIME format
    message = MIMEMultipart('alternative')
    message['to'] = to
    message['cc'] = EMAIL_CC
    message['subject'] = subject
    message.attach(MIMEText(body, 'html'))  # Attach email body in HTML format
    return {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

def get_gmail_credentials():
    # Get or refresh Gmail API credentials
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return creds

def create_email_draft(service, user_id, message):
    # Create a draft email in Gmail
    try:
        draft = service.users().drafts().create(userId=user_id, body={'message': message}).execute()
        print(f"Draft id: {draft['id']} created.")
    except HttpError as error:
        print(f"An error occurred while creating the draft: {error}")

def update_airtable_record(record_id):
    # Update the specified record in Airtable
    try:
        url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}/{record_id}"
        headers = {
            "Authorization": f"Bearer {AIRTABLE_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {"fields": {"DRAFTED": "YES"}}
        response = requests.patch(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        print(f"Record {record_id} updated successfully.")
    except requests.exceptions.RequestException as e:
        print(f"Error updating record in Airtable: {e}")

def main():
    # Main function to process records from Airtable and create email drafts
    airtable_data = get_airtable_data()
    if airtable_data:

        # Initialize Jinja2 environment
        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template('email_template.html')

        for record in airtable_data['records']:
            # Process each record
            record_id = record['id']
            fields = record['fields']

            # Extract email details from the record
            contact_name = fields.get('Contact Name', 'N/A')
            contact_email = fields.get('Contact Email', 'N/A')
            company_name = fields.get('Company Name', 'N/A')

            # Email content with HTML formatting
            email_subject = f"2024 Generative AI 年會贊助募集 x {company_name}"
            email_body = template.render(contact_name=contact_name, company_name=company_name)

            print(f"Preparing draft: {email_subject}")
            creds = get_gmail_credentials()
            try:
                service = build("gmail", "v1", credentials=creds)
                message = create_message(contact_email, email_subject, email_body)
                create_email_draft(service, GMAIL_USER_ID, message)
                # Update Airtable record after successful draft creation
                update_airtable_record(record_id)
            except HttpError as error:
                print(f"An error occurred: {error}")

if __name__ == "__main__":
    main()