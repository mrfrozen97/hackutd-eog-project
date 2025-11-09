#!/bin/bash
# Start the FastAPI backend server for witch routes

cd "$(dirname "$0")"

# Check if dependencies are installed
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
fi

# Start the server
echo "Starting Witch Routes API on http://localhost:8000"
python3 witch_routes_api.py
