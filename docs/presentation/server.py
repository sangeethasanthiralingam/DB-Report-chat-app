#!/usr/bin/env python3
"""
Simple HTTP server for DB Report Chat App Documentation Presentation
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

def main():
    # Change to the project root directory (two levels up from presentation)
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)
    
    # Set up the server
    PORT = 8000
    
    # Create a custom handler that serves files from the correct locations
    class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def translate_path(self, path):
            # Handle requests for presentation files
            if path.startswith('/presentation/'):
                # Remove /presentation/ prefix and serve from docs/presentation
                clean_path = path[13:]  # Remove '/presentation/'
                if clean_path == '' or clean_path == '/':
                    clean_path = 'index.html'
                return os.path.join('docs', 'presentation', clean_path)
            
            # Handle requests for markdown files in docs directory
            if path.startswith('/docs/') and path.endswith('.md'):
                # Serve markdown files from docs directory
                clean_path = path[6:]  # Remove '/docs/' prefix
                return os.path.join('docs', clean_path)
            
            # Handle requests for README.md in root
            if path == '/README.md':
                return 'README.md'
            
            # Default behavior for other files
            return super().translate_path(path)
        
        def end_headers(self):
            # Add CORS headers for local development
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            super().end_headers()
    
    try:
        with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
            print(f"🚀 DB Report Chat App Documentation Server")
            print(f"📍 Serving at: http://localhost:{PORT}")
            print(f"📁 Root directory: {project_root}")
            print(f"📖 Documentation: http://localhost:{PORT}/docs/presentation/")
            print(f"🔧 Press Ctrl+C to stop the server")
            print("-" * 50)
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Port {PORT} is already in use. Try a different port:")
            print(f"   python docs/presentation/server.py --port 8001")
        else:
            print(f"❌ Error starting server: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main() 