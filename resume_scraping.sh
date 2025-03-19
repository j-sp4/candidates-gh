#!/bin/bash

# Check if the scraper is already running
if pgrep -f "python github_scraper_resumable.py" > /dev/null
then
    echo "GitHub scraper is already running."
else
    echo "Starting GitHub scraper from checkpoint..."
    nohup python github_scraper_resumable.py > scraper.log 2>&1 &
    echo "Scraper started with PID $!"
fi

echo "You can check the progress in scraper.log"
echo "Tail the log with: tail -f scraper.log" 