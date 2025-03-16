import base64
from email.message import EmailMessage
from email.mime.text import MIMEText

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from Utils.Secrete import SecreteLoader


class GmailCloudService:
    def __init__(self):
        """
        Important Note: You need to download the credential from your google cloud->console
        It is in APIs & Services > Credentials
        Create a type "Desktop" app credentials
        After creation, download the credentials JSON file
        Put under Database/Secretes/gmail_credentials/creds.json
        """
        self.creds = SecreteLoader().get_gmail_creds()
        self.service = build("gmail", "v1", credentials=self.creds)
        self.from_email = "hsin-chun.yin@mail.huji.ac.il"

    def send_email(self, to_email_address, subject, content, content_is_html=False):
        try:
            # message = MIMEText(content, 'html')
            message = EmailMessage()
            if content_is_html:
                message.set_content(content, subtype='html')
            else:
                message.set_content(content)
            message["To"] = to_email_address
            message["From"] = self.from_email
            message["Subject"] = subject

            # encoded message
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

            create_message = {"raw": encoded_message}
            # pylint: disable=E1101
            send_message = (
                self.service.users()
                .messages()
                .send(userId="me", body=create_message)
                .execute()
            )
            # print(f'Message Id: {send_message["id"]}')

        except HttpError as error:
            print(f"An error occurred: {error}")
            send_message = None
