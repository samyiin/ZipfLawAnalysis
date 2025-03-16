import os
import os.path

# pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

import base64
from email.message import EmailMessage

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class SecreteLoader:
    '''
    Important to place the running file cwd to be the root directory
    '''
    def get_github_apikey(self, owner):
        file_name = 'Database/Secretes/github_apikey'
        try:
            with open(os.path.join(file_name, owner), 'r') as file:
            # Read the API key
                api_key = file.read().strip()
                return api_key
        except:
            print("Owner Name is Wrong!")
            return None

    def get_openai_api_key(self, owner):
        file_name = 'Database/Secretes/openai_apikey'
        try:
            with open(os.path.join(file_name, owner), 'r') as file:
                # Read the API key
                api_key = file.read().strip()
                return api_key
        except:
            print("Owner Name is Wrong!")
            return None

    def get_gemini_api_key(self, owner):
        file_name = 'Database/Secretes/gemini_apikey'
        try:
            with open(os.path.join(file_name, owner), 'r') as file:
                # Read the API key
                api_key = file.read().strip()
                return api_key
        except:
            print("Owner Name is Wrong!")
            return None

    def get_gmail_creds(self):
        """
        Important Note: You need to download the credential from your google cloud->console
        It is in APIs & Services > Credentials -> After creation, download the credentials JSON file
        Create a type "Desktop" app
        :return:
        """
        SCOPES = ["https://mail.google.com/"]
        token_path = 'Database/Secretes/gmail_credentials/token.json'
        credential_path = 'Database/Secretes/gmail_credentials/creds.json'
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credential_path, SCOPES
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(token_path, "w") as token:
                token.write(creds.to_json())
        return creds