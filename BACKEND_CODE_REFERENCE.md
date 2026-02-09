# Code for "Backend not running" message and how to run the real backend

## 1. Where the message is defined (server)

**File: `serve_web_only.py`**

```python
BACKEND_MSG = (
    "Digital human backend is not running. "
    "Add model files (models/wav2lip.pth, data/avatars/) and run: ./run_local.sh"
)

# When the browser POSTs to /offer, the server returns:
def do_POST(self):
    if self.path in ("/offer", "/record", "/human", ...):
        body = json.dumps({"error": BACKEND_MSG}).encode()
        self.send_response(503)
        self.send_header("Content-Type", "application/json")
        ...
        self.wfile.write(body)
```

So the **message text** comes from `BACKEND_MSG` in `serve_web_only.py`. The stub server returns `503` and `{"error": "..."}` for `/offer`, `/human`, etc.

---

## 2. Where the message is shown (browser)

**File: `web/client.js`**

When you click **Start**, the page POSTs to `/offer`. The client expects JSON; if the server returns an error it shows it in an alert:

```javascript
// After fetch('/offer', ...)
.then((response) => {
    return response.json().then((data) => {
        if (!response.ok || data.error) {
            throw new Error(data.error || 'Connection failed (backend may not be running).');
        }
        return data;
    }).catch((e) => {
        if (e.message && (e.message.includes('Backend') || e.message.includes('Connection failed'))) throw e;
        throw new Error('Backend not running. Add model files and run ./run_local.sh to use the digital human.');
    });
})
// ...
.catch((e) => {
    // ...
    alert(e.message || e);   // <-- this shows the message in the popup
});
```

So the **popup text** is either `data.error` from the server (same as `BACKEND_MSG`) or the fallback string in `client.js`.

---

## 3. Code to run the real backend (full digital human)

**File: `run_local.sh`**

```bash
#!/usr/bin/env bash
# Run LiveTalking/metahuman-stream locally with WebRTC.
# Requires: model file at models/wav2lip.pth and avatar at data/avatars/wav2lip256_avatar1

set -e
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  echo "Creating venv and installing dependencies..."
  uv venv && source .venv/bin/activate && uv pip install -r requirements.txt
fi

source .venv/bin/activate

# Optional: use HuggingFace mirror if needed
# export HF_ENDPOINT=https://hf-mirror.com

python app.py --transport webrtc --model wav2lip --avatar_id wav2lip256_avatar1 --listenport 8010
```

**Equivalent one-line command (from project root):**

```bash
cd /home/abdul.rehman/sui/metahuman-stream && source .venv/bin/activate && python app.py --transport webrtc --model wav2lip --avatar_id wav2lip256_avatar1 --listenport 8010
```

**What you must have first:**

- `models/wav2lip.pth` (download `wav2lip256.pth` and rename)
- `data/avatars/wav2lip256_avatar1/` (extract `wav2lip256_avatar1.tar.gz` into `data/avatars/`)

Download links:  
Google Drive: https://drive.google.com/drive/folders/1FOC_MD6wdogyyX_7V1d4NDIO7P9NlSAJ  
Quark: https://pan.quark.cn/s/83a750323ef0

---

## 4. Summary

| What | Code location |
|------|----------------|
| Message text (server) | `serve_web_only.py` → `BACKEND_MSG` |
| Returning the error | `serve_web_only.py` → `do_POST()` for `/offer`, etc. |
| Showing the alert (browser) | `web/client.js` → `negotiate()` → `.catch()` → `alert(e.message)` |
| Running the real backend | `./run_local.sh` or the `python app.py ...` command above |

Once the model files are in place and you run `./run_local.sh` (or the `python app.py` command), the same page at `http://localhost:8010/webrtcapi.html` will talk to the real backend and the digital human will work instead of showing "Backend not running".
