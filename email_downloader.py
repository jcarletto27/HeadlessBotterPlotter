import os
import json
import time
from email.utils import parseaddr
from dotenv import load_dotenv
from imap_tools import MailBox, AND

# --- Configuration ---
load_dotenv()
IMAP_SERVER = os.getenv("IMAP_SERVER")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

DOWNLOAD_FOLDER = "plotter_attachments"
METADATA_FOLDER = "plotter_metadata"
SENDER_FILE = "allowed_senders.txt"
PROCESSED_FOLDER = "Processed"

# --- Helper Functions ---
def load_allowed_senders(filename):
    """Loads a list of allowed senders from a text file."""
    if not os.path.exists(filename):
        print(f"❌ Error: Sender file '{filename}' not found.")
        return []
    with open(filename, "r") as f:
        return [line.strip() for line in f if line.strip()]

def process_email(mailbox, msg):
    """Processes a single email message and then moves it."""
    print(f"\nProcessing email from {msg.from_} with subject: '{msg.subject}'")
    
    sender_email = parseaddr(msg.from_)[1]
    has_attachment = False

    for att in msg.attachments:
        if att.content_type in ["image/png", "image/jpeg"]:
            has_attachment = True
            filename = att.filename
            print(f"  📥 Found image attachment: '{filename}'")

            filepath = os.path.join(DOWNLOAD_FOLDER, filename)
            with open(filepath, "wb") as f:
                f.write(att.payload)
            
            base_name = os.path.splitext(filename)[0]
            metadata_path = os.path.join(METADATA_FOLDER, f"{base_name}.json")
            with open(metadata_path, 'w') as f:
                json.dump({"sender": sender_email}, f)
            print(f"  💾 Saved sender info for '{filename}'")

    if has_attachment:
        print(f"  -> Moving email to '{PROCESSED_FOLDER}' folder...")
        res = mailbox.move([msg.uid], PROCESSED_FOLDER)
        if res:
            print("  ✅ Email moved successfully.")
        else:
            print(f"  ❌ Failed to move email. Status: {res}")

# --- Main Function ---
def check_for_emails():
    """Connects to the inbox, processes all unread mail, and exits."""
    if not all([IMAP_SERVER, EMAIL_USER, EMAIL_PASS]):
        print("❌ Error: IMAP_SERVER, EMAIL_USER, and EMAIL_PASS must be set in .env")
        return

    ALLOWED_SENDERS = load_allowed_senders(SENDER_FILE)
    if not ALLOWED_SENDERS:
        print("No allowed senders configured. Exiting.")
        return

    for folder in [DOWNLOAD_FOLDER, METADATA_FOLDER]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    try:
        print("Connecting to mailbox to check for unread mail...")
        with MailBox(IMAP_SERVER).login(EMAIL_USER, EMAIL_PASS) as mailbox:
            if not mailbox.folder.exists(PROCESSED_FOLDER):
                print(f"❌ Error: The folder '{PROCESSED_FOLDER}' does not exist on the mail server.")
                return

            print("✅ Connection successful. Fetching messages...")
            
            # Fetch all unread messages from allowed senders and process them.
            # The script will exit after this loop completes.
            messages = list(mailbox.fetch(AND(seen=False, from_=ALLOWED_SENDERS), mark_seen=False))
            if not messages:
                print("No new messages found.")
            else:
                print(f"Found {len(messages)} new message(s).")
                for msg in messages:
                    process_email(mailbox, msg)
        
        print("Email check complete.")

    except Exception as e:
        print(f"An error occurred: {e}.")

if __name__ == "__main__":
    check_for_emails()
