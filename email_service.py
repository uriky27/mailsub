"""Email service integration with Google Gmail API."""
import base64
import io
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


class GmailService:
    """Gmail API service for sending encrypted files via email."""
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: Optional[str] = None,
    ):
        """
        Initialize Gmail service.
        
        Args:
            client_id: Google OAuth 2.0 Client ID
            client_secret: Google OAuth 2.0 Client Secret
            refresh_token: Optional existing refresh token
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.service = None
    
    def authenticate(self) -> None:
        """Authenticate with Google API using OAuth 2.0."""
        if self.refresh_token:
            # Use existing refresh token
            creds = self._get_credentials_from_refresh_token(self.refresh_token)
        else:
            # Initiate new OAuth flow
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json",
                SCOPES,
            )
            creds = flow.run_local_server(port=0)
            self.refresh_token = creds.refresh_token
        
        self.service = build("gmail", "v1", credentials=creds)
    
    def _get_credentials_from_refresh_token(self, refresh_token: str):
        """Recreate credentials from refresh token."""
        from google.oauth2.credentials import Credentials
        
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
        )
        creds.refresh(Request())
        return creds
    
    def send_encrypted_file(
        self,
        to_email: str,
        subject: str,
        body: str,
        encrypted_file_data: bytes,
        filename: str,
        from_email: str = "me",
    ) -> str:
        """
        Send email with encrypted file attachment.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body text
            encrypted_file_data: Encrypted file bytes
            filename: Filename for the attachment
            from_email: Sender email (default: "me" = authenticated user)
            
        Returns:
            Message ID from Gmail API
            
        Raises:
            Exception: If service not authenticated or send fails
        """
        if not self.service:
            raise Exception("Service not authenticated. Call authenticate() first.")
        
        # Create message
        message = MIMEMultipart()
        message["to"] = to_email
        message["from"] = from_email
        message["subject"] = subject
        
        # Add body
        message.attach(MIMEText(body, "plain"))
        
        # Add encrypted file as attachment
        attachment = MIMEApplication(encrypted_file_data)
        attachment.add_header("Content-Disposition", "attachment", filename=filename)
        message.attach(attachment)
        
        # Encode and send
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        result = self.service.users().messages().send(
            userId=from_email,
            body={"raw": raw_message},
        ).execute()
        
        return result["id"]
