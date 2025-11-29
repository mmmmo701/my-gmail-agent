import os.path
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from src.config import CREDENTIALS_PATH, TOKEN_PATH, SCOPES

class GmailClient:
    def __init__(self):
        self.creds = None
        self.service = None
        self.authenticate()

    def authenticate(self):
        # 1. Check if we have a saved token
        if os.path.exists(TOKEN_PATH):
            print(f"Found saved credentials at {TOKEN_PATH}.")
            choice = input("Do you want to use the saved account? (y/n): ").strip().lower()
            
            if choice == 'y':
                self.creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
            else:
                print("Switching accounts...")
                self.creds = None  # Force re-login
        
        # 2. If no valid creds (or user chose 'n'), log in
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                print("Refreshing expired token...")
                self.creds.refresh(Request())
            else:
                print("Launching browser for login...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_PATH, SCOPES
                )
                
                # NEW: prompt='select_account' forces Google to show the account picker
                # even if you are already logged in to one account in Chrome.
                self.creds = flow.run_local_server(
                    port=0, 
                    prompt='select_account' 
                )
            
            # Save the new token
            with open(TOKEN_PATH, 'w') as token:
                token.write(self.creds.to_json())

        self.service = build('gmail', 'v1', credentials=self.creds)
        print("Authentication successful!\n")

    def get_unread_emails(self, limit=5):
        """Fetches a list of message IDs for unread emails."""
        results = self.service.users().messages().list(
            userId='me', 
            q='is:unread', 
            maxResults=limit
        ).execute()
        
        return results.get('messages', [])

    def get_email_details(self, message_id):
        """Fetches and parses a specific email."""
        msg = self.service.users().messages().get(
            userId='me', 
            id=message_id, 
            format='full'
        ).execute()

        payload = msg.get('payload', {})
        headers = payload.get('headers', [])

        email_data = {
            "id": message_id,
            "sender": self._extract_header(headers, "From"),
            "subject": self._extract_header(headers, "Subject"),
            "date": self._extract_header(headers, "Date"),  
            "body": self._parse_body(payload)
        }
        return email_data

    def _extract_header(self, headers, name):
        """Helper to find specific header values."""
        for header in headers:
            if header['name'] == name:
                return header['value']
        return ""

    def _parse_body(self, payload):
        """Recursively searches for text/plain content."""
        if 'body' in payload and 'data' in payload['body']:
            return self._decode_base64(payload['body']['data'])
        
        if 'parts' in payload:
            for part in payload['parts']:
                mime_type = part.get('mimeType')
                if mime_type == 'text/plain':
                    if 'data' in part['body']:
                        return self._decode_base64(part['body']['data'])
                if 'parts' in part:
                    return self._parse_body(part)
        
        return "(No plain text body found)"

    def _decode_base64(self, data):
        clean_data = data.replace('-', '+').replace('_', '/')
        return base64.b64decode(clean_data).decode('utf-8')