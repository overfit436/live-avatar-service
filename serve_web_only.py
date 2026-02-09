#!/usr/bin/env python3
"""Serve only the web UI on port 8010. Use when the full app cannot start (e.g. missing models).
   For full digital human, run: python app.py --transport webrtc --model wav2lip --avatar_id wav2lip256_avatar1
"""
import http.server
import socketserver
import os
import json

WEB_DIR = os.path.join(os.path.dirname(__file__), "web")
BACKEND_MSG = (
    "Digital human backend is not running. "
    "Add model files (models/wav2lip.pth, data/avatars/) and run: ./run_local.sh"
)

class WebOnlyHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_POST(self):
        if self.path in ("/offer", "/record", "/human", "/humanaudio", "/set_audiotype", "/interrupt_talk", "/is_speaking"):
            body = json.dumps({"error": BACKEND_MSG}).encode()
            self.send_response(503)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        pass  # quiet

os.chdir(WEB_DIR)
PORT = int(os.environ.get("PORT", "8010"))
ALTERNATE_PORTS = [8011, 8012, 8888]
httpd = None
for try_port in [PORT] + [p for p in ALTERNATE_PORTS if p != PORT]:
    try:
        httpd = socketserver.TCPServer(("", try_port), WebOnlyHandler)
        PORT = try_port
        break
    except OSError as e:
        if e.errno != 98:  # Address already in use
            raise
        if try_port == PORT:
            print(f"Port {PORT} in use, trying alternate ports...")
if httpd is None:
    raise SystemExit("No port available (tried 8010, 8011, 8012, 8888). Stop other apps using these ports.")
print(f"Serving web UI at http://localhost:{PORT}/")
print(f"  e.g. http://localhost:{PORT}/webrtcapi.html")
print("  (Backend APIs will not work until the full app is run with models.)")
httpd.serve_forever()
