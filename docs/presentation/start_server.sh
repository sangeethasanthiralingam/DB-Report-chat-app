#!/bin/bash

echo "Starting DB Report Chat App Documentation Server..."
echo

# Change to project root directory (two levels up from presentation)
cd "$(dirname "$0")/../.."
echo "Current directory: $(pwd)"
echo

echo "Starting Python HTTP server..."
echo "Documentation will be available at: http://localhost:8000/docs/presentation/"
echo
echo "Press Ctrl+C to stop the server"
echo

python -m http.server 8000 