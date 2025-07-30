import email
import imaplib
import os
import json
from email.utils import parseaddr
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()
IMAP_SERVER = os.getenv("IMAP_SERVER")
IMAP_PORT = int(os.getenv("IMAP_PORT", 993))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

DOWNLOAD_FOLDER = "plotter_attachments"
METADATA_FOLDER = "plotter_metadata" # Folder for sender info
SENDER_FILE = "allowed_senders.txt"

# --- Helper Function ---
def load_allowed_senders(filename):
    """Loads a list of allowed senders from a text file."""
    if not os.path.exists(filename):
        print(f"❌ Error: Sender file '{filename}' not found.")
        return []
    with open(filename, "r") as f:
        return [line.strip() for line in f if line.strip()]

# --- Main Script ---
def download_attachments():
    """Connects to email, downloads attachments, and saves sender metadata."""
    if not all([IMAP_SERVER, EMAIL_USER, EMAIL_PASS]):
        print("❌ Error: IMAP_SERVER, EMAIL_USER, and EMAIL_PASS must be set in .env")
        return

    ALLOWED_SENDERS = load_allowed_senders(SENDER_FILE)
    if not ALLOWED_SENDERS:
        print("No allowed senders configured. Exiting.")
        return

    # Create directories if they don't exist
    for folder in [DOWNLOAD_FOLDER, METADATA_FOLDER]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    try:
        print(f"Connecting to {IMAP_SERVER} on port {IMAP_PORT}...")
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")
        print("✅ Successfully connected to inbox.")

        for sender in ALLOWED_SENDERS:
            status, messages = mail.search(None, f'(UNSEEN FROM "{sender}")')
            if status != "OK" or not messages[0]:
                continue

            print(f"Found new messages from {sender}. Processing...")
            for email_id in messages[0].split():
                _, msg_data = mail.fetch(email_id, "(RFC822)")
                msg = email.message_from_bytes(msg_data[0][1])
                
                # Extract sender's email address from the 'From' header
                sender_email = parseaddr(msg['From'])[1]

                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_maintype() == 'multipart' or part.get('Content-Disposition') is None:
                            continue

                        filename = part.get_filename()
                        if filename and (filename.lower().endswith(('.png', '.jpg', '.jpeg'))):
                            # Save the attachment
                            filepath = os.path.join(DOWNLOAD_FOLDER, filename)
                            with open(filepath, "wb") as f:
                                f.write(part.get_payload(decode=True))
                            print(f"  📥 Downloaded '{filename}'")

                            # Save the sender's email to a metadata file
                            base_name = os.path.splitext(filename)[0]
                            metadata_path = os.path.join(METADATA_FOLDER, f"{base_name}.json")
                            with open(metadata_path, 'w') as f:
                                json.dump({"sender": sender_email}, f)
                            print(f"  💾 Saved sender info to '{metadata_path}'")

                mail.store(email_id, '+FLAGS', '\\Seen')

    except Exception as e:
        print(f"❌ An error occurred: {e}")
    finally:
        if 'mail' in locals() and mail.state == 'SELECTED':
            mail.close()
            mail.logout()
            print("Disconnected from email server.")

if __name__ == "__main__":
    download_attachments()
