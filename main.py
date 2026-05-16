#!/usr/bin/env python3
"""
Simple HTTP server for Lenny's Recommendations
Serves static files (HTML, CSS, JS, images, JSON)
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

class CORSRequestHandler(SimpleHTTPRequestHandler):
    """HTTP request handler with CORS support"""

    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        return super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

def run_server(port=8000):
    """Start the HTTP server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, CORSRequestHandler)
    print(f"Server running on http://0.0.0.0:{port}")
    print(f"Netflix version: http://0.0.0.0:{port}/index.html")
    print(f"Quiet version: http://0.0.0.0:{port}/index-quiet.html")
    httpd.serve_forever()

if __name__ == '__main__':
    # Change to script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Start server (Replit uses port 8000 by default)
    run_server(port=8000)
