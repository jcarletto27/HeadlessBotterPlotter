# Plotter Bot: Automated Email-to-GCode Workflow

This project automates the process of converting image attachments from emails into G-code suitable for a pen plotter. It's designed to run as a complete workflow, from checking an inbox to streaming the final commands to a GRBL-powered device.

When an email is received from an approved sender with a PNG or JPG attachment, the system will:


1. Download the image.


2. Trace the image into an SVG vector file.


3. Convert the SVG into G-code, using plotter settings from a config file.


4. Stream the G-code to the plotter.


5. Send a completion email back to the original sender with the traced SVG file attached.


## Features


- **Email Monitoring**: Securely checks an IMAP email account for new messages from a whitelist of approved senders.


- **Automated Image Processing**: Converts raster images (PNG, JPG) into vector-based SVG files.


- **G-Code Generation**: Compiles SVG files into plotter-ready G-code, applying custom settings for pen height, feed rate, and plot area.


- **Hardware Integration**: Streams the generated G-code directly to a GRBL device connected via USB.


- **Email Notifications**: Automatically sends a confirmation email to the original sender upon job completion, with the final SVG file attached.


## Setup and Installation

Follow these steps to set up the project environment and install the required dependencies.

### 1. Create a Virtual Environment

It is highly recommended to run this project in a Python virtual environment to manage its dependencies separately.

```
# Create the virtual environment
python3 -m venv .venv

# Activate the virtual environment
# On macOS and Linux:
source .venv/bin/activate

# On Windows:
# .\.venv\Scripts\activate

```

### 2. Install Required Modules

With your virtual environment activated, install all the necessary Python libraries using pip.

```
pip install Pillow vtracer python-dotenv pyserial svg-to-gcode

```

## Configuration

Before running the workflow, you need to configure your credentials, plotter settings, and email permissions.

### 1. Environment Variables (`.env`)

Create a `.env` file in the root of the project. This file stores your sensitive credentials for both receiving and sending emails.

```
# Email Receiving (IMAP)
EMAIL_USER="your_email@gmail.com"
EMAIL_PASS="your_16_digit_app_password"
IMAP_SERVER="imap.gmail.com"
IMAP_PORT="993"

# Email Sending (SMTP)
SMTP_SERVER="smtp.gmail.com"
SMTP_PORT=587
SMTP_USER="your_email@gmail.com"
SMTP_PASS="your_16_digit_app_password"

```

### 2. Allowed Senders (`allowed_senders.txt`)

Create a file named `allowed_senders.txt` and add the email addresses of everyone who is permitted to send jobs to the plotter, with one email per line.

```
sender1@example.com
colleague@work.com

```

### 3. Plotter Settings (`config.ini`)

Run the `image_to_gcode_converter.py` script once to generate a default `config.ini` file. Then, edit this file to match your plotter's specific hardware settings.

```
[GCodeSettings]
pen_down_position_mm = 0
pen_travel_position_mm = 5
pen_feed_rate_mm_min = 1000
max_plot_x = 200
min_plot_x = 0
max_plot_y = 200
min_plot_y = 0
usb_port = /dev/ttyUSB0
baud_rate = 115200

```

### 4. G-Code Preamble/Postamble (Optional)

You can create `preamble.gcode` and `postamble.gcode` files to add custom commands to the start and end of every job (e.g., `G28` to home the machine).

## Usage

Once everything is configured, you can run the entire workflow with a single command.

First, make the script executable:

```
chmod +x run_workflow.sh

```

Then, run the workflow:

```
./run_workflow.sh

```

## Scripts Overview


- `email_downloader.py`: Connects to the email server, finds valid emails, downloads image attachments, and saves the sender's email address to a metadata file.


- `image_to_gcode_converter.py`: Converts the downloaded images into SVG and then into G-code, applying settings from `config.ini`.


- `gcode_streamer.py`: Sends the G-code to the plotter and emails the original sender with the final SVG.


- `run_workflow.sh`: A simple bash script that executes the three Python scripts in the correct order.


- `.gitignore`: Prevents sensitive files and generated output from being committed to version control.
