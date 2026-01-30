#!/bin/bash
# Daily LinkedIn Automation Script
# Runs automatically via cron to generate new posts

cd "/Users/musacomma/Agentic Workflow/linkedin_automation"

# Log file
LOG_FILE="logs/daily_automation_$(date +%Y%m%d).log"

echo "========================================" >> "$LOG_FILE"
echo "Daily Automation Started: $(date)" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Run the post generation
python3 RUN_linkedin_automation.py --action generate-posts >> "$LOG_FILE" 2>&1

echo "Completed: $(date)" >> "$LOG_FILE"
