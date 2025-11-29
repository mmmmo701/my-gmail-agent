from src.services.gmail_api import GmailClient
from src.services.llm_api import OllamaClient

def main():
    print("--- Gmail AI Agent v0.2 ---")
    
    # 1. Setup Services
    gmail = GmailClient()
    ai = OllamaClient()
    
    # 2. Get Emails
    print("\nFetching unread emails...")
    messages = gmail.get_unread_emails(limit=5)

    if not messages:
        print("No unread emails found.")
        return

    print(f"Found {len(messages)} emails. Analyzing with AI...\n")

    # 3. Process Loop
    for msg in messages:
        details = gmail.get_email_details(msg['id'])
    
        full_text = f"Subject: {details['subject']}\n\n{details['body']}"
        analysis = ai.analyze_email(full_text)
        
        print("-" * 60)
        print(f"Date:     {details['date']}")
        print(f"From:     {details['sender']}")
        print(f"Summary:  {analysis['summary']}")
        print(f"Category: {analysis['category']}")
        print("-" * 60 + "\n")

if __name__ == "__main__":
    main()