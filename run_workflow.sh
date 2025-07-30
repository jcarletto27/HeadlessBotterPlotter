#!/bin/bash

# This script automates the plotter workflow by executing the three
# main Python scripts in sequence.
#
# To make this script executable, run the following command in your terminal:
# chmod +x run_workflow.sh
#
# To run the script, execute it from your terminal:
# ./run_workflow.sh

echo "--- 🤖 Starting Plotter Bot Workflow ---"
echo ""

# Step 1: Check email and download attachments
echo "--- 📧 Step 1: Checking for new emails... ---"
python3 email_downloader.py
echo ""

# Step 2: Convert downloaded images to G-code
echo "--- 🎨 Step 2: Converting images to G-code... ---"
python3 image_to_gcode_converter.py
echo ""

# Step 3: Stream G-code to the GRBL device
echo "--- ✒️  Step 3: Streaming G-code to plotter... ---"
python3 gcode_streamer.py
echo ""

echo "--- ✅ Workflow complete. ---"

