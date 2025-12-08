import os.path
import json
from icalendar import Calendar
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from src.config import CREDENTIALS_PATH, TOKEN_PATH, SCOPES
from src.ui.text_io import TextIO, Constants

class GCalClient:
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
        self.service = build('calendar', 'v3', credentials=self.creds)
        print("Authentication successful!\n")

    def add_ics_event(self, ics_string):
        """
        Parses an ICS string and adds it to the user's primary calendar.
        Returns the link to the created event.
        """

        ui = TextIO()

        try:
            # 1. Parse the ICS string using the icalendar library
            cal = Calendar.from_ical(ics_string)
            
            # We assume there is one event in the ICS string
            for component in cal.walk():
                if component.name == "VEVENT":
                    # 2. Map ICS fields to Google Calendar JSON Schema
                    event_body = {
                        'summary': str(component.get('summary')),
                        'description': str(component.get('description', '')),
                        'location': str(component.get('location', '')),
                        'start': {
                            'dateTime': component.get('dtstart').dt.isoformat(),
                            'timeZone': 'UTC', # Our AI generates UTC times
                        },
                        'end': {
                            'dateTime': component.get('dtend').dt.isoformat(),
                            'timeZone': 'UTC',
                        },
                    }

                    # 3. Insert into Google Calendar
                    created_event = self.service.events().insert(
                        calendarId='primary', 
                        body=event_body
                    ).execute()

                    return created_event.get('htmlLink')
                    
        except Exception as e:
            ui.show_error(f"Failed to add event to Google Calendar: {e}")
            return None