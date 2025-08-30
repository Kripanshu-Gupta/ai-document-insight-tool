import http.server
import socketserver
import os

# Set the port for the frontend server
PORT = 5500

# The directory where your index.html and image are located
# ".." means the parent directory of this script's location.
# Since this script is in /backend, the parent is /ai-document-tool
DIRECTORY = ".." 

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Frontend server running at http://localhost:{PORT}")
    print("Open this URL in your browser.")
    httpd.serve_forever()

