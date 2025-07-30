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
PROCESSED_FOLDER = "Processed" # The email folder to move processed messages to

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
    print(f"\nProcessing new email from {msg.from_} with subject: '{msg.subject}'")
    
    sender_email = parseaddr(msg.from_)[1]
    has_attachment = False

    for att in msg.attachments:
        if att.content_type in ["image/png", "image/jpeg"]:
            has_attachment = True
            filename = att.filename
            print(f"  📥 Found image attachment: '{filename}'")

            # Save the attachment
            filepath = os.path.join(DOWNLOAD_FOLDER, filename)
            with open(filepath, "wb") as f:
                f.write(att.payload)
            
            # Save the sender's email to a metadata file
            base_name = os.path.splitext(filename)[0]
            metadata_path = os.path.join(METADATA_FOLDER, f"{base_name}.json")
            with open(metadata_path, 'w') as f:
                json.dump({"sender": sender_email}, f)
            print(f"  💾 Saved sender info for '{filename}'")

    # If we successfully processed at least one attachment, move the email.
    if has_attachment:
        print(f"  -> Moving email to '{PROCESSED_FOLDER}' folder...")
        res = mailbox.move([msg.uid], PROCESSED_FOLDER)
        if res:
            print("  ✅ Email moved successfully.")
        else:
            print(f"  ❌ Failed to move email. Status: {res}")


# --- Main Listener ---
def listen_for_emails():
    """Uses IMAP IDLE to wait for new emails and processes them as they arrive."""
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

    print("✅ Configuration loaded. Starting email listener...")
    
    # This outer loop makes the script resilient to network errors and timeouts.
    while True:
        try:
            # Establish a new connection in each iteration of the loop
            print("Attempting to connect to mailbox...")
            with MailBox(IMAP_SERVER).login(EMAIL_USER, EMAIL_PASS) as mailbox:
                if not mailbox.folder.exists(PROCESSED_FOLDER):
                    print(f"❌ Error: The folder '{PROCESSED_FOLDER}' does not exist on the mail server.")
                    print("Please create it and restart the script.")
                    return

                print("✅ Connection successful. Performing initial check for unread mail...")
                
                # Process any existing unread mail first
                for msg in mailbox.fetch(AND(seen=False, from_=ALLOWED_SENDERS), mark_seen=False):
                    process_email(mailbox, msg)

                print("🎧 Now listening for new emails...")
                
                # Wait for new messages. This will block until a new email arrives
                # or the connection is terminated by the server.
                responses = mailbox.idle.wait()
                
                # When wait() returns, it means there's new activity.
                # The loop will then restart, reconnect, and process all unread mail.
                print(f"New activity detected: {responses}. Restarting loop to process.")

        except KeyboardInterrupt:
            print("\nShutting down listener.")
            break
        except Exception as e:
            # This block catches any error, including connection drops or timeouts
            print(f"An error occurred: {e}. Reconnecting in 30 seconds...")
            time.sleep(30)

if __name__ == "__main__":
    listen_for_emails()
