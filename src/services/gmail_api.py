import os.path
import base64
import json
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

    def _load_saved_accounts(self):
        """
        Load all saved accounts from token.json.
        Returns a list of account dictionaries with 'email' and 'token_data' keys.
        """
        if not os.path.exists(TOKEN_PATH):
            return []
        
        try:
            with open(TOKEN_PATH, 'r') as f:
                data = json.load(f)
            
            # Handle both old single-account format and new multi-account format
            if isinstance(data, dict) and 'accounts' in data:
                # Multi-account format
                return data['accounts']
            elif isinstance(data, dict) and 'token' in data:
                # Old single-account format - convert to new format
                email = data.get('account', 'Unknown')
                return [{'email': email if email else 'Unknown', 'token_data': data}]
            else:
                return []
        except (json.JSONDecodeError, IOError):
            return []

    def _select_saved_account(self):
        """
        Display saved accounts and let user choose one.
        Returns the selected account data or None if user wants a new account.
        """
        saved_accounts = self._load_saved_accounts()
        
        if not saved_accounts:
            return None
        
        print(f"Found {len(saved_accounts)} saved account(s).")
        print("\nSelect an account:")
        for i, account in enumerate(saved_accounts, 1):
            print(f"  {i}. {account.get('email', 'Unknown')}")
        print(f"  {len(saved_accounts) + 1}. New account")
        
        while True:
            try:
                choice = int(input("\nEnter your choice (number): ").strip())
                if 1 <= choice <= len(saved_accounts):
                    selected_account = saved_accounts[choice - 1]
                    try:
                        # Try to create credentials from saved token
                        self.creds = Credentials.from_authorized_user_info(
                            selected_account['token_data'], SCOPES
                        )
                        # Refresh if expired
                        if self.creds.expired and self.creds.refresh_token:
                            self.creds.refresh(Request())
                        return selected_account
                    except Exception as e:
                        print(f"Failed to load account: {e}. Please select another or create a new account.")
                        return None
                elif choice == len(saved_accounts) + 1:
                    return None  # User wants a new account
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a valid number.")

    def _launch_browser_login(self):
        """
        Launch browser for OAuth login and return the new credentials.
        """
        print("Launching browser for login...")
        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_PATH, SCOPES
        )
        
        # prompt='select_account' forces Google to show the account picker
        # even if you are already logged in to one account in Chrome.
        self.creds = flow.run_local_server(
            port=0, 
            prompt='select_account'
        )
        
        return self.creds

    def _save_account(self, creds):
        """
        Save the account credentials to token.json in multi-account format.
        """
        try:
            creds_data = json.loads(creds.to_json())
            email = creds_data.get('account', 'Unknown')
            
            # Load existing accounts
            if os.path.exists(TOKEN_PATH):
                with open(TOKEN_PATH, 'r') as f:
                    try:
                        data = json.load(f)
                        if 'accounts' in data:
                            accounts = data['accounts']
                        else:
                            # Convert old format
                            accounts = [{'email': data.get('account', 'Unknown'), 'token_data': data}]
                    except json.JSONDecodeError:
                        accounts = []
            else:
                accounts = []
            
            # Check if account already exists and update it
            account_exists = False
            for account in accounts:
                if account.get('email') == email:
                    account['token_data'] = creds_data
                    account_exists = True
                    break
            
            # If new account, add it
            if not account_exists:
                accounts.append({'email': email, 'token_data': creds_data})
            
            # Save to file
            with open(TOKEN_PATH, 'w') as f:
                json.dump({'accounts': accounts}, f, indent=2)
            
            print(f"Account {email} saved successfully.")
        except Exception as e:
            print(f"Warning: Failed to save account properly: {e}")

    def authenticate(self):
        """
        Authenticate with Google Calendar API.
        Allows user to choose from saved accounts or create a new one.
        """
        # 1. Try to load a saved account
        selected_account = self._select_saved_account()
        
        # 2. If user selected a saved account and it worked, use it
        if self.creds and self.creds.valid:
            print(f"Using account: {selected_account.get('email', 'Unknown')}\n")
        else:
            # 3. Launch browser for new login
            self._launch_browser_login()
            self._save_account(self.creds)
        
        # 4. Build the service
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