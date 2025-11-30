import os.path
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

    def authenticate(self):
        """
        Reuse the existing authentication logic.
        Note: This relies on token.json having the correct Calendar scopes.
        """
        if os.path.exists(TOKEN_PATH):
            self.creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_PATH, SCOPES
                )
                self.creds = flow.run_local_server(port=0)
            
            with open(TOKEN_PATH, 'w') as token:
                token.write(self.creds.to_json())

        self.service = build('calendar', 'v3', credentials=self.creds)

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