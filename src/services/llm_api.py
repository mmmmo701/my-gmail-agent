import ollama
import os
import json
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv
from src.prompts import CATEGORIZE_PROMPT, EVENT_EXTRACTION_PROMPT

load_dotenv()

MODEL = os.getenv("OLLAMA_MODEL", "phi3")

class OllamaClient:
    def __init__(self):
        self.category_schema = {
            "type": "object",
            "properties": {
                "reasoning": {
                    "type": "string",
                    "description": "A brief explanation of why this category fits."
                },
                "category": {
                    "type": "string",
                    "enum": ["Important", "Event", "Opportunity", "Unimportant"]
                }
            },
            "required": ["reasoning", "category"] 
        }

        # Schema for Event Extraction (Strict typing)
        self.event_schema = {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "Short title of the event"},
                "start_time": {"type": "string", "description": "ISO 8601 format (YYYY-MM-DD HH:MM:SS)"},
                "end_time": {"type": "string", "description": "ISO 8601 format (YYYY-MM-DD HH:MM:SS)"},
                "location": {"type": "string", "description": "Physical location or URL"},
                "description": {"type": "string", "description": "Brief details about the event"}
            },
            "required": ["summary", "start_time", "end_time", "location", "description"]
        }

    def categorize_email(self, email_body):
        clean_body = email_body[:3000]
        
        prompt = CATEGORIZE_PROMPT.format(email_body=clean_body)

        try:
            response = ollama.chat(
                model=MODEL,
                messages=[{'role': 'user', 'content': prompt}],
                format=self.category_schema,
                options={'temperature': 0} # Keep 0 for consistency
            )
            
            response_json = json.loads(response['message']['content'])
            
            # Debugging: Print the reasoning to see why it's failing
            print(f"Reasoning: {response_json.get('reasoning')}")
            print(f"Category: {response_json.get('category')}")

            return response_json['category']
            
        except Exception as e:
            print(f"LLM Error (Category): {e}")
            return "Unimportant"
        
    def create_event(self, email_body, email_date_str=None):
        """
        Extracts event details and returns an ICS string.
        """
        clean_body = email_body[:4000]
        
        # Determine the reference date for the prompt
        date_str = email_date_str if email_date_str else datetime.now().strftime('%Y-%m-%d')
        
        # Use the imported prompt template
        prompt = EVENT_EXTRACTION_PROMPT.format(
            date_context=date_str,
            email_body=clean_body
        )

        try:
            # 1. Extract Data as JSON
            response = ollama.chat(
                model=MODEL,
                messages=[{'role': 'user', 'content': prompt}],
                format=self.event_schema,
                options={'temperature': 0} 
            )
            
            event_data = json.loads(response['message']['content'])
            
            # 2. Convert to ICS Format
            return self._generate_ics_string(event_data)

        except Exception as e:
            print(f"LLM Error (Event): {e}")
            return None

    def _generate_ics_string(self, data):
        """
        Converts the JSON dictionary to a valid .ics string.
        """
        def format_date_for_ics(iso_date_str):
            try:
                # Try parsing the ISO format output by the LLM
                dt = datetime.fromisoformat(iso_date_str)
                return dt.strftime('%Y%m%dT%H%M%S')
            except ValueError:
                # Fallback if LLM outputs weird date format
                return datetime.now().strftime('%Y%m%dT%H%M%S')

        start = format_date_for_ics(data.get('start_time', ''))
        end = format_date_for_ics(data.get('end_time', ''))
        now = datetime.now().strftime('%Y%m%dT%H%M%SZ')
        uid = str(uuid.uuid4())

        ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//MyGmailAgent//EN
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{now}
DTSTART:{start}
DTEND:{end}
SUMMARY:{data['summary']}
DESCRIPTION:{data['description']}
LOCATION:{data['location']}
END:VEVENT
END:VCALENDAR"""
        
        return ics_content