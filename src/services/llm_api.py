import ollama
import os
import json
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv
from src.prompts import CATEGORIZE_PROMPT, EVENT_EXTRACTION_PROMPT
from src.ui.text_io import TextIO, Constants

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
                "reasoning": {
                    "type": "string",
                    "description": "A brief explanation of the event details extracted."
                },
                "summary": {"type": "string"},
                "description": {"type": "string"},
                "location": {"type": "string"},
                "start": {
                    "type": "object",
                    "properties": {
                        "dateTime": {"type": "string"},
                        "timeZone": {"type": "string"}
                    },
                    "required": ["dateTime"]
                },
                "end": {
                    "type": "object",
                    "properties": {
                        "dateTime": {"type": "string"},
                        "timeZone": {"type": "string"}
                    },
                    "required": ["dateTime"]
                }
            },
            "required": ["reasoning", "summary", "start", "end", "description"]
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
        ui = TextIO()

        clean_body = email_body[:8000]
        date_str = email_date_str if email_date_str else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        prompt = EVENT_EXTRACTION_PROMPT.format(
            date_context=date_str,
            email_body=clean_body
        )

        try:
            response = ollama.chat(
                model=MODEL,
                messages=[{'role': 'user', 'content': prompt}],
                format=self.event_schema, 
                options={'temperature': 0.1} 
            )
            
            raw_json = response['message']['content']
            event_data = json.loads(raw_json)
            
            validated_data = self._validate_and_fix_event_data(event_data)
            return self._generate_ics_string(validated_data)

        except json.JSONDecodeError:
            ui.show_error("LLM failed to produce valid JSON.")
            return None
        except Exception as e:
            ui.show_error(f"LLM event error: {e}")
            return None

    def _validate_and_fix_event_data(self, data):
        try:
            # Parse ISO strings to Python datetime objects
            start_dt = datetime.fromisoformat(data['start']['dateTime'])
            end_dt = datetime.fromisoformat(data['end']['dateTime'])

            # Guardrail: If End is before or same as Start, fix it.
            if end_dt <= start_dt:
                end_dt = start_dt + timedelta(hours=1)
                # Update the data dictionary with the fixed time
                data['end']['dateTime'] = end_dt.isoformat()

        except (ValueError, KeyError):
            # Fallback: If parsing fails entirely, create a "now" event
            now = datetime.now()
            data['start']['dateTime'] = now.isoformat()
            data['end']['dateTime'] = (now + timedelta(hours=1)).isoformat()
        
        # Ensure optional fields exist to prevent KeyErrors later
        if 'location' not in data:
            data['location'] = ""
            
        return data

    def _generate_ics_string(self, data):
        def to_ics_format(iso_str):
            # Converts ISO 8601 (2023-10-27T14:00:00) to ICS format (20231027T140000)
            dt = datetime.fromisoformat(iso_str)
            return dt.strftime('%Y%m%dT%H%M%S')

        # Use helper to format dates safely
        start_str = to_ics_format(data['start']['dateTime'])
        end_str = to_ics_format(data['end']['dateTime'])
        
        now_stamp = datetime.now().strftime('%Y%m%dT%H%M%SZ')
        uid = str(uuid.uuid4())
        
        # Clean string fields to prevent ICS breakage (newlines can break headers)
        summary = data.get('summary', 'New Event').replace('\n', ' ')
        description = data.get('description', '').replace('\n', '\\n')
        location = data.get('location', '').replace('\n', ' ')

        # Construct ICS
        ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//MyGmailAgent//EN
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{now_stamp}
DTSTART;TZID=Local:{start_str}
DTEND;TZID=Local:{end_str}
SUMMARY:{summary}
DESCRIPTION:{description}
LOCATION:{location}
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR"""
        
        return ics_content
