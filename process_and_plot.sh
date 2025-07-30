#!/bin/bash

# This script processes any downloaded attachments, converts them to G-code,
# and sends them to the plotter. It's designed to be run periodically
# by a cron job (e.g., every minute).

echo "--- ⚙️ Starting Plotter Queue Processor ---"
echo ""

# Navigate to the script's directory to ensure correct file paths
cd "$(dirname "$0")"

# Step 1: Convert any new images to G-code
echo "--- 🎨 Step 1: Converting images to G-code... ---"
python3 image_to_gcode_converter.py
echo ""

# Step 2: Stream the next available G-code file to the plotter
echo "--- ✒️  Step 2: Streaming G-code to plotter... ---"
python3 gcode_streamer.py
echo ""

echo "--- ✅ Queue processing complete. ---"
