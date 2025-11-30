# Prompt for categorizing emails

CATEGORIZE_PROMPT = """
You are an intelligent email assistant. 
Analyze the following email body and determine which category it belongs to:
1. Important: Emails that I need to take actions such as direct emails from boss/professors, bills.
2. Event: Club meetings, hackathons, event invitations, etc. Things that can go on my calendar.
3. Opportunity: Job offers, scholarships, etc. Things that I might want to follow up on but can't go on my calendar.
4. Unimportant: Newsletters, spam, marketing, generic notifications (including emails from educational platforms).

Email Body:
"{email_body}"

Provide your response in JSON format. 
STEP 1: In the 'reasoning' field, explain your thought process in 1 sentence.
STEP 2: In the 'category' field, select the best matching category.
"""


# -----------------------------------------------------------

# Prompt for extracting event details
# We use {date_context} to help the LLM resolve relative dates like "next Friday"

EVENT_EXTRACTION_PROMPT = """
You are an intelligent calendar assistant. Your goal is to extract a specific, schedule-ready event from the email provided below.

### CONTEXT
- **Current Reference Date/Time:** {date_context} (Use this to resolve relative dates like "tomorrow" or "next Friday").

### INSTRUCTIONS
1. **Title Generation:** Create a concise but descriptive title (3-7 words). Do not use generic titles like "Meeting." Instead, use "Project X Sync" or "Lunch with John."
2. **Date & Time Logic:**
   - Extract the start date and time.
   - Extract the end time. **CRITICAL:** If no end time or duration is mentioned, you MUST calculate the end time by adding exactly 1 hour to the start time.
   - The Start Time and End Time must NEVER be the same.
3. **Description:**
   - Summarize the "Why" (Agenda) and "Who" (Participants) from the email.
   - Include any specific location or video link details if present.
4. **Format:** Output ONLY valid JSON with no markdown formatting.

### JSON OUTPUT SCHEMA
{{
  "summary": "String (The Event Title)",
  "start": {{
    "dateTime": "ISO 8601 String (YYYY-MM-DDTHH:MM:SS)",
    "timeZone": "User's Local Timezone"
  }},
  "end": {{
    "dateTime": "ISO 8601 String (YYYY-MM-DDTHH:MM:SS)",
    "timeZone": "User's Local Timezone"
  }},
  "description": "String (The specific details)"
}}

### EMAIL CONTENT
{email_body}
"""