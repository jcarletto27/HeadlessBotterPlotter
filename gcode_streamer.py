import serial
import time
import os
import glob
import configparser

# --- Configuration ---
CONFIG_FILE = "config.ini"
GCODE_FOLDER = "plotter_gcode"
SENT_FOLDER = "sent_gcode"

def load_config(filename):
    """Loads settings from the config.ini file."""
    if not os.path.exists(filename):
        print(f"❌ Error: Configuration file '{filename}' not found.")
        print("Please run the 'image_to_gcode_converter.py' script first to generate it.")
        return None
    
    config = configparser.ConfigParser()
    config.read(filename)
    return config['GCodeSettings']

def stream_gcode():
    """Finds a G-code file and streams it to a GRBL device via USB."""
    # Load configuration
    config = load_config(CONFIG_FILE)
    if not config:
        return

    # Check for the required settings
    if 'usb_port' not in config or 'baud_rate' not in config:
        print("❌ Error: 'usb_port' and 'baud_rate' must be set in config.ini.")
        print("Please run 'image_to_gcode_converter.py' to update the config file.")
        return

    # Create the sent folder if it doesn't existimport serial
    import time
    import os
    import glob
    import configparser
    import smtplib
    import json
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase
    from email import encoders
    from dotenv import load_dotenv
    
    # --- Configuration ---
    load_dotenv()
    CONFIG_FILE = "config.ini"
    GCODE_FOLDER = "plotter_gcode"
    SVG_FOLDER = "plotter_svgs"
    METADATA_FOLDER = "plotter_metadata"
    SENT_FOLDER = "sent_gcode"
    
    # Email settings from .env
    SMTP_SERVER = os.getenv("SMTP_SERVER")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASS = os.getenv("SMTP_PASS")
    
    # --- Functions ---
    
    def load_config(filename):
        """Loads settings from the config.ini file."""
        if not os.path.exists(filename):
            print(f"❌ Error: Configuration file '{filename}' not found.")
            return None
        config = configparser.ConfigParser()
        config.read(filename)
        return config['GCodeSettings']
    
    def send_completion_email(recipient_email, gcode_filename, svg_attachment_path):
        """Sends an email with the SVG attachment to the specified recipient."""
        if not all([SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASS]):
            print("📧 Email sending settings not configured in .env file. Skipping email.")
            return
    
        if not recipient_email:
            print("📧 No recipient email found. Skipping email.")
            return
    
        # Create the email message
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = recipient_email
        msg['Subject'] = f"Plotter Job Complete: {gcode_filename}"
        body = f"The plotter has successfully completed the print job for '{gcode_filename}'.\n\nThe traced SVG file is attached."
        msg.attach(MIMEText(body, 'plain'))
    
        # Attach the SVG file, if it exists
        if os.path.exists(svg_attachment_path):
            with open(svg_attachment_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(svg_attachment_path)}")
            msg.attach(part)
        else:
            print(f"📧 SVG file not found at '{svg_attachment_path}'. Sending email without attachment.")
    
        # Send the email
        try:
            print(f"📧 Connecting to email server to notify {recipient_email}...")
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
            server.quit()
            print("✅ Email notification sent successfully.")
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
    
    def stream_gcode():
        """Finds a G-code file and streams it to a GRBL device via USB."""
        config = load_config(CONFIG_FILE)
        if not config or 'usb_port' not in config or 'baud_rate' not in config:
            print("❌ Error: Plotter settings missing in config.ini.")
            return
    
        if not os.path.exists(SENT_FOLDER):
            os.makedirs(SENT_FOLDER)
    
        gcode_files = glob.glob(os.path.join(GCODE_FOLDER, "*.gcode"))
        if not gcode_files:
            print("No new G-code files to stream.")
            return
        
        file_to_stream = gcode_files[0]
        base_filename = os.path.basename(file_to_stream)
        filename_no_ext = os.path.splitext(base_filename)[0]
        
        # Define paths for associated files
        svg_path = os.path.join(SVG_FOLDER, f"{filename_no_ext}.svg")
        metadata_path = os.path.join(METADATA_FOLDER, f"{filename_no_ext}.json")
    
        # Get the recipient's email from the metadata file
        recipient = None
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                recipient = metadata.get("sender")
        else:
            print(f"⚠️  Metadata file not found for '{base_filename}'. Cannot send email.")
    
        try:
            print(f"Connecting to {config['usb_port']} at {config['baud_rate']} baud...")
            s = serial.Serial(config['usb_port'], config['baud_rate'])
            s.write(b"\r\n\r\n")
            time.sleep(2)
            s.flushInput()
            print("✅ Successfully connected to GRBL device.")
            
            with open(file_to_stream, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(';') or not line: continue
                    print(f"Sending: {line}")
                    s.write((line + '\n').encode())
                    print(f"  Recv: {s.readline().decode().strip()}")
    
            print("🎉 G-code streaming complete.")
            
            # Send completion email
            send_completion_email(recipient, base_filename, svg_path)
    
            # Cleanup all processed files
            os.rename(file_to_stream, os.path.join(SENT_FOLDER, base_filename))
            print(f"Moved '{base_filename}' to '{SENT_FOLDER}'.")
            if os.path.exists(svg_path): os.remove(svg_path)
            if os.path.exists(metadata_path): os.remove(metadata_path)
    
        except serial.SerialException as e:
            print(f"❌ Serial Error: Could not connect to {config['usb_port']}. Check port/permissions. Details: {e}")
        except Exception as e:
            print(f"❌ An unexpected error occurred: {e}")
        finally:
            if 's' in locals() and s.is_open:
                s.close()
                print("Serial connection closed.")
    
    if __name__ == "__main__":
        stream_gcode()
    
    if not os.path.exists(SENT_FOLDER):
        os.makedirs(SENT_FOLDER)

    # Find the first available G-code file
    gcode_files = glob.glob(os.path.join(GCODE_FOLDER, "*.gcode"))
    if not gcode_files:
        print("No new G-code files to stream.")
        return
    
    file_to_stream = gcode_files[0]
    print(f"Found G-code file: '{os.path.basename(file_to_stream)}'")

    try:
        # Connect to the GRBL device
        print(f"Connecting to {config['usb_port']} at {config['baud_rate']} baud...")
        s = serial.Serial(config['usb_port'], config['baud_rate'])
        
        # Wake up GRBL
        s.write(b"\r\n\r\n")
        time.sleep(2)   # Wait for GRBL to initialize
        s.flushInput()  # Flush startup text in serial input

        print("✅ Successfully connected to GRBL device.")
        
        # Open G-code file and stream it
        with open(file_to_stream, "r") as f:
            for line in f:
                line = line.strip() # Strip all EOL characters for consistency
                if line.startswith(';') or not line:
                    continue # Skip comments and empty lines
                
                print(f"Sending: {line}")
                s.write((line + '\n').encode()) # Send g-code block
                grbl_out = s.readline().decode().strip() # Wait for GRBL response
                print(f"  Recv: {grbl_out}")

        print("🎉 G-code streaming complete.")
        
        # Move the sent file to the sent folder
        os.rename(file_to_stream, os.path.join(SENT_FOLDER, os.path.basename(file_to_stream)))
        print(f"Moved '{os.path.basename(file_to_stream)}' to '{SENT_FOLDER}' folder.")

    except serial.SerialException as e:
        print(f"❌ Serial Error: Could not connect to {config['usb_port']}. Please check the port and permissions.")
        print(f"   Details: {e}")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
    finally:
        if 's' in locals() and s.is_open:
            s.close()
            print("Serial connection closed.")

if __name__ == "__main__":
    stream_gcode()
