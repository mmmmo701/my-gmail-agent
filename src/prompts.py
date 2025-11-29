# Prompt for categorizing emails

CATEGORIZE_PROMPT = """
You are an intelligent email assistant. 
Analyze the following email body and determine which category it belongs to:
1. Important: Emails that I need to take actions such as direct emails from boss/professors, bills.
2. Event: Club meetings, hackathons, event invitations, etc. Things that can go on my calendar.
3. Opportunity: Job offers, hackathons, scholarships, etc. Things that I might want to follow up on but can't go on my calendar.
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

EVENT_EXTRACTION_PROMPT = """Extract event details from this email.
Reference Date: {date_context}
If end time is missing, assume 1 hour duration.
Use 24-hour format for times.

Email:
{email_body}"""