#!/usr/bin/env bash
# Check which port has the model loaded. Use the URL for the port where model_loaded is true.
# If both show model_loaded: false, stop other servers and run: ./run_local.sh
set -e
echo "Port 8010:"
curl -s -m 2 "http://localhost:8010/status" 2>/dev/null || echo '{"error":"no response"}'
echo ""
echo "Port 8011:"
curl -s -m 2 "http://localhost:8011/status" 2>/dev/null || echo '{"error":"no response"}'
echo ""
echo "Open the port where model_loaded is true, e.g. http://localhost:8010/webrtcapi.html"
