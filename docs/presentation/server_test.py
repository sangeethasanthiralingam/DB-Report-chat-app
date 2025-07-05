#!/usr/bin/env python3
"""
Simple HTTP server test for DB Report Chat App documentation presentation.
This script helps diagnose file serving issues.
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

def get_project_root():
    """Get the project root directory."""
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent
    return project_root

def test_file_access():
    """Test if key files are accessible."""
    project_root = get_project_root()
    
    test_files = [
        project_root / "README.md",
        project_root / "docs" / "ARCHITECTURE.md",
        project_root / "docs" / "API.md",
        project_root / "docs" / "CONFIGURATION.md",
        project_root / "docs" / "DEVELOPER_HINTS.md",
        project_root / "docs" / "REQUEST_RESPONSE_FLOW.md",
        project_root / "docs" / "TESTING.md",
        project_root / "docs" / "CHART_BEHAVIOR.md",
        project_root / "docs" / "PROMPT_MATRIX.md"
    ]
    
    print("Testing file accessibility:")
    print("=" * 50)
    
    for file_path in test_files:
        if file_path.exists():
            print(f"✅ {file_path.relative_to(project_root)}")
        else:
            print(f"❌ {file_path.relative_to(project_root)} - NOT FOUND")
    
    print()

def start_server(port=8000):
    """Start the HTTP server."""
    project_root = get_project_root()
    
    print(f"Starting HTTP server...")
    print(f"Project root: {project_root}")
    print(f"Server URL: http://localhost:{port}")
    print(f"Presentation URL: http://localhost:{port}/docs/presentation/")
    print()
    print("Available files:")
    print("=" * 50)
    
    # List available files
    for file_path in project_root.rglob("*.md"):
        relative_path = file_path.relative_to(project_root)
        print(f"📄 {relative_path}")
    
    print()
    print("Press Ctrl+C to stop the server")
    print()
    
    # Change to project root directory
    os.chdir(project_root)
    
    # Create server
    handler = http.server.SimpleHTTPRequestHandler
    
    # Add custom headers for better debugging
    class CustomHandler(handler):
        def end_headers(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            super().end_headers()
        
        def log_message(self, format, *args):
            # Log all requests for debugging
            print(f"[{self.log_date_time_string()}] {format % args}")
    
    try:
        with socketserver.TCPServer(("", port), CustomHandler) as httpd:
            print(f"Server started successfully on port {port}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"Error: Port {port} is already in use")
            print("Please stop any existing server or use a different port")
        else:
            print(f"Error starting server: {e}")

if __name__ == "__main__":
    print("DB Report Chat App - Documentation Server Test")
    print("=" * 50)
    
    # Test file access first
    test_file_access()
    
    # Get port from command line or use default
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    
    # Start server
    start_server(port) 