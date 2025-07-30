#!/bin/bash

# This script generates the correct crontab entry for running the
# process_and_plot.sh script every minute.

# Get the absolute path to the current directory
CURRENT_DIR=$(pwd)
SCRIPT_PATH="$CURRENT_DIR/process_and_plot.sh"
LOG_PATH="$CURRENT_DIR/cron.log"

# The command to be added to the crontab
CRON_COMMAND="* * * * * $SCRIPT_PATH >> $LOG_PATH 2>&1"

# --- Instructions ---
echo "✅ Your crontab entry has been generated."
echo ""
echo "---"
echo "1. Open your crontab file by running this command:"
echo "   crontab -e"
echo ""
echo "2. Copy the following line and paste it at the end of the file:"
echo "---"
echo ""
echo "$CRON_COMMAND"
echo ""

