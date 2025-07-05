#!/bin/bash

echo "Starting DB Report Chat App Documentation Presentation..."
echo

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "Starting server from project root..."
echo "Current directory: $PROJECT_ROOT"
echo

# Change to project root directory
cd "$PROJECT_ROOT"

echo "Starting HTTP server on port 8000..."
echo

# Function to open browser
open_browser() {
    if command -v xdg-open > /dev/null; then
        xdg-open "http://localhost:8000/docs/presentation/" &
    elif command -v open > /dev/null; then
        open "http://localhost:8000/docs/presentation/" &
    else
        echo "Please open http://localhost:8000/docs/presentation/ in your browser"
    fi
}

# Open browser after a short delay
(sleep 2 && open_browser) &

echo "Server is running at: http://localhost:8000"
echo "Presentation is at: http://localhost:8000/docs/presentation/"
echo
echo "Press Ctrl+C to stop the server"
echo

# Start the server
python3 -m http.server 8000 