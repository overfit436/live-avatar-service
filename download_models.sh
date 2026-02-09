#!/usr/bin/env bash
# Download model file for wav2lip. Avatar (wav2lip256_avatar1) must be added manually from Google Drive/Quark.
set -e
cd "$(dirname "$0")"
mkdir -p models data/avatars

echo "Downloading wav2lip.pth (may take a few minutes)..."
# Hugging Face direct link (standard Wav2Lip checkpoint; may work with wav2lip256 avatar)
URL="https://huggingface.co/Nekochu/Wav2Lip/resolve/main/wav2lip.pth"
if command -v curl &>/dev/null; then
  curl -L -o models/wav2lip.pth "$URL" || true
elif command -v wget &>/dev/null; then
  wget -q -O models/wav2lip.pth "$URL" || true
else
  echo "Install curl or wget to auto-download."
  exit 1
fi

if [ -f models/wav2lip.pth ] && [ -s models/wav2lip.pth ]; then
  echo "  [OK] models/wav2lip.pth"
else
  echo "  [FAIL] Download failed or file empty. Get it manually:"
  echo "    Google Drive: https://drive.google.com/drive/folders/1FOC_MD6wdogyyX_7V1d4NDIO7P9NlSAJ"
  echo "    Quark: https://pan.quark.cn/s/83a750323ef0"
  echo "    Save as: models/wav2lip.pth (rename from wav2lip256.pth if needed)"
  rm -f models/wav2lip.pth
  exit 1
fi

echo ""
echo "Avatar (required): you must add it manually."
echo "  1. From the same Google Drive / Quark link above, download: wav2lip256_avatar1.tar.gz"
echo "  2. Extract it and put the folder 'wav2lip256_avatar1' inside: data/avatars/"
echo "  So you must have: data/avatars/wav2lip256_avatar1/ (with full_imgs, face_imgs, coords.pkl, etc.)"
echo ""
./check_models.sh
