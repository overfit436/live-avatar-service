# How to Add Model Files (Fix "Backend not running" / "Model file could not be loaded")

The digital human needs the **project’s** wav2lip256 checkpoint (not the standard Wav2Lip from Hugging Face or other repos).

## 1. Download the files

Use **one** of these:

- **Google Drive:** https://drive.google.com/drive/folders/1FOC_MD6wdogyyX_7V1d4NDIO7P9NlSAJ  
- **Quark (夸克云盘):** https://pan.quark.cn/s/83a750323ef0  

From that **same** folder you need:

| File you download        | What to do with it |
|--------------------------|---------------------|
| **wav2lip256.pth**       | Put it in `models/wav2lip256.pth` (keep the name). **Must** be from this project’s Drive/Quark folder — standard Wav2Lip checkpoints will not load. |
| `wav2lip256_avatar1.tar.gz` | Extract it and copy the **entire folder** `wav2lip256_avatar1` into `data/avatars/` |

So you should end up with:

```
metahuman-stream/
  models/
    wav2lip256.pth       ← from project Google Drive/Quark only
  data/
    avatars/
      wav2lip256_avatar1/   ← contents of the tar.gz
        (full_imgs, face_imgs, coords.pkl, ...)
```

## 2. Run the backend

```bash
cd /home/abdul.rehman/sui/metahuman-stream
./run_local.sh
```

Then open **http://localhost:8010/webrtcapi.html**, click **Start**, and use the text box to make the digital human speak.

## Optional: face detector (s3fd)

If the app later asks for a face detector, put `s3fd.pth` at:

`wav2lip/face_detection/detection/sfd/s3fd.pth`

Some setups download it automatically from the project’s URL.
