from src.services.gmail_api import GmailClient
from src.services.gcal_api import GCalClient
from src.services.llm_api import OllamaClient
from src.utils.parser import EmailParser
from src.ui.text_io import TextIO, Constants

def get_full_text(email_body, subject):
    clean_body = EmailParser().parse(email_body)
    full_text = f"Subject: {subject}\n{clean_body}"
    return full_text

def main():
    ui = TextIO()
    ui.show_cover()
    
    gmail = GmailClient()
    gcal = GCalClient()
    ai = OllamaClient()
    
    messages = gmail.get_unread_emails(limit=10) # We can process more now!

    if not messages:
        ui.show_msg(Constants.NO_UNREAD)
        return

    ui.show_msg(Constants.CLASSIFYING)

    impt_msgs = []
    oppor_msgs = []

    for msg in messages:
        details = gmail.get_email_details(msg['id'])
        full_text = get_full_text(details['body'], details['subject'])
        
        category = ai.categorize_email(full_text)

        ui.show_categorized_email(category, details['subject'])

        if category == "Event":
            ui.show_msg(Constants.GENERATING_EVENT)
            ics_string = ai.create_event(full_text, details['date'])

            if ics_string:
                ui.show_msg(Constants.EVENT_CREATED)
                ui.show_event(ics_string)
                gcal.add_ics_event(ics_string)
                ui.show_msg(Constants.EVENT_ADDED)

        elif category == "Important":
            impt_msgs.append(details)

        elif category == "Opportunity":
            oppor_msgs.append(details)


if __name__ == "__main__":
    main()