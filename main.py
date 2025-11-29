from src.services.gmail_api import GmailClient
from src.services.llm_api import OllamaClient
from src.utils.parser import EmailParser

def main():
    print("--- Gmail Classifier (High Speed) ---")
    
    gmail = GmailClient()
    ai = OllamaClient()
    
    messages = gmail.get_unread_emails(limit=10) # We can process more now!

    if not messages:
        print("No unread emails.")
        return

    print(f"Classifying {len(messages)} emails...\n")

    impt_msgs = []
    oppor_msgs = []

    for msg in messages:
        details = gmail.get_email_details(msg['id'])
        clean_body = EmailParser().parse(details['body'])
        
        # Combine Subject + Body for the AI
        full_text = f"Subject: {details['subject']}\n{clean_body}"
        
        category = ai.categorize_email(full_text)

        print(f"[{category.upper()}] {details['subject']}")

        if category == "Event":
            print("Generating Calendar Event...")
            # Pass the email date so the AI knows when "tomorrow" is
            ics_string = ai.create_event(full_text, details['date'])
            
            if ics_string:
                # Save to file
                filename = f"event_{msg['id']}.ics"
                with open(filename, "w") as f:
                    f.write(ics_string)
                print(f"-> Saved calendar invite: {filename}")

        elif category == "Important":
            impt_msgs.append(details)

        elif category == "Opportunity":
            oppor_msgs.append(details)

        # TODO: generate important and opportunity summaries after creating events

        print("-" * 40)

if __name__ == "__main__":
    main()