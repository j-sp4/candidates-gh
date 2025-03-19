#!/bin/bash

# Check if the dashboard API is running
if pgrep -f "python dashboard_api.py" > /dev/null
then
    echo "Dashboard API is already running."
else
    echo "Starting dashboard API..."
    nohup python dashboard_api.py > dashboard_api.log 2>&1 &
    echo "Dashboard API started with PID $!"
fi

# Check if the Next.js server is running
if pgrep -f "npm run dev" > /dev/null
then
    echo "Next.js server is already running."
else
    echo "Starting Next.js server..."
    cd dashboard
    nohup npm run dev > ../nextjs_server.log 2>&1 &
    echo "Next.js server started with PID $!"
fi

echo "All services are now running." 