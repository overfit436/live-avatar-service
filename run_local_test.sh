#!/usr/bin/env bash
# Run the web UI locally for testing (no model required).
# Open in browser: http://localhost:8010/webrtcapi.html or http://localhost:8010/dashboard.html
# Note: Digital human / WebRTC backend won't work until you run the full app with models (./run_local.sh).

set -e
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  echo "Creating venv and installing dependencies..."
  uv venv && source .venv/bin/activate && uv pip install -r requirements.txt
fi

source .venv/bin/activate

echo "Starting web UI at http://localhost:8010/"
echo "  Test page: http://localhost:8010/webrtcapi.html"
echo "  Dashboard: http://localhost:8010/dashboard.html"
echo "  (Press Ctrl+C to stop)"
python serve_web_only.py
