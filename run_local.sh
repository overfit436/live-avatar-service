#!/usr/bin/env bash
# Run the backend (app.py). Server starts with or without model files.
# Without models: server runs and returns a clear message when you click Start.
# With models: add models/wav2lip256.pth and data/avatars/wav2lip256_avatar1/ for full digital human.
# Download: https://pan.quark.cn/s/83a750323ef0 or https://drive.google.com/drive/folders/1FOC_MD6wdogyyX_7V1d4NDIO7P9NlSAJ
# If you see "Model files not loaded": stop any other server on 8010/8011, then run this again and use the URL it prints.

set -e
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  echo "Creating venv and installing dependencies..."
  uv venv && source .venv/bin/activate && uv pip install -r requirements.txt
fi

source .venv/bin/activate

# Optional: use HuggingFace mirror if needed
# export HF_ENDPOINT=https://hf-mirror.com

# If 8010 is busy, backend will try 8011, 8012, 8888
python app.py --transport webrtc --model wav2lip --avatar_id wav2lip256_avatar1 --listenport 8010
