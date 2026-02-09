#!/usr/bin/env bash
# Check if model files are in place for running the digital human.
cd "$(dirname "$0")"

echo "Checking model files..."
MISSING=0

if [ -f "models/wav2lip.pth" ]; then
  echo "  [OK] models/wav2lip.pth"
else
  echo "  [MISSING] models/wav2lip.pth  (download wav2lip256.pth and rename it to wav2lip.pth)"
  MISSING=1
fi

if [ -d "data/avatars/wav2lip256_avatar1" ]; then
  echo "  [OK] data/avatars/wav2lip256_avatar1/"
else
  echo "  [MISSING] data/avatars/wav2lip256_avatar1/  (extract wav2lip256_avatar1.tar.gz into data/avatars/)"
  MISSING=1
fi

if [ "$MISSING" -eq 0 ]; then
  echo ""
  echo "All required files present. Run: ./run_local.sh"
  exit 0
else
  echo ""
  echo "See SETUP_MODELS.md for download links and steps."
  exit 1
fi
