# LiveTalking – Real-time Interactive Digital Human

<p align="center">
<img src="./assets/LiveTalking-logo.jpg" align="middle" width = "300"/>
</p>
<p align="center">
    <a href="./LICENSE"><img src="https://img.shields.io/badge/license-Apache%202-dfd.svg"></a>
    <a href="https://github.com/lipku/LiveTalking/releases"><img src="https://img.shields.io/github/v/release/lipku/LiveTalking?color=ffa"></a>
    <a href=""><img src="https://img.shields.io/badge/python-3.10+-aff.svg"></a>
    <a href=""><img src="https://img.shields.io/badge/os-linux%2C%20win%2C%20mac-pink.svg"></a>
    <a href="https://github.com/lipku/LiveTalking/graphs/contributors"><img src="https://img.shields.io/badge/github-contributors-c4f042?style=flat-square"></a>
    <a href="https://github.com/lipku/LiveTalking/network/members"><img src="https://img.shields.io/badge/github-forks-8ae8ff"></a>
    <a href="https://github.com/lipku/LiveTalking/stargazers"><img src="https://img.shields.io/badge/github-stars-ccf"></a>
</p>

Real-time interactive streaming digital human with synchronized audio and video dialogue. Suitable for commercial use.

**Demos:** [wav2lip](https://www.bilibili.com/video/BV1scwBeyELA/) | [ernerf](https://www.bilibili.com/video/BV1G1421z73r/) | [musetalk](https://www.bilibili.com/video/BV1gm421N7vQ/)

**Note:** The original project name was metahuman-stream; it was renamed to LiveTalking to avoid confusion with 3D digital human projects. The old links still work.

---

## News

- **2024.12.8** Improved multi-concurrency; GPU memory no longer scales with concurrent sessions.
- **2024.12.21** Added wav2lip and musetalk model warm-up to fix first-inference stutter. Thanks [@heimaojinzhangyz](https://github.com/heimaojinzhangyz).
- **2024.12.28** Added Ultralight-Digital-Human model. Thanks [@lijihua2017](https://github.com/lijihua2017).
- **2025.2.7** Added Fish-Speech TTS.
- **2025.2.21** Added open-source wav2lip256 model. Thanks @不蠢不蠢.
- **2025.3.2** Added Tencent TTS service.
- **2025.3.16** Mac GPU inference support. Thanks [@GcsSloop](https://github.com/GcsSloop).
- **2025.5.1** Simplified run parameters; ern erf model moved to git branch ernerf-rtmp.
- **2025.6.7** Added virtual camera output.
- **2025.7.5** Added Doubao TTS. Thanks [@ELK-milu](https://github.com/ELK-milu).
- **2025.7.26** MuseTalk v1.5 support.

---

## Features

1. **Multiple digital human models:** ern erf, MuseTalk, Wav2Lip, Ultralight-Digital-Human
2. **Voice cloning**
3. **Interruptible speech** – digital human can be interrupted while talking
4. **WebRTC and virtual camera** output
5. **Action scripting** – play custom video when not speaking
6. **Multi-concurrency** support

---

## 1. Installation

Tested on Ubuntu 24.04, Python 3.10, PyTorch 2.5.0, and CUDA 12.4.

### 1.1 Install dependencies

```bash
conda create -n nerfstream python=3.10
conda activate nerfstream
# If your CUDA version is not 12.4 (check with nvidia-smi), install the matching PyTorch from https://pytorch.org/get-started/previous-versions/
conda install pytorch==2.5.0 torchvision==0.20.0 torchaudio==2.5.0 pytorch-cuda=12.4 -c pytorch -c nvidia
pip install -r requirements.txt
```

- **FAQ:** [FAQ](https://livetalking-doc.readthedocs.io/zh-cn/latest/faq.html)
- **Linux CUDA setup:** <https://zhuanlan.zhihu.com/p/674972886>
- **Video connection issues:** <https://mp.weixin.qq.com/s/MVUkxxhV2cgMMHalphr2cg>

---

## 2. Quick Start

### Download models

- **Quark:** <https://pan.quark.cn/s/83a750323ef0>
- **Google Drive:** <https://drive.google.com/drive/folders/1FOC_MD6wdogyyX_7V1d4NDIO7P9NlSAJ?usp=sharing>

Then:

1. Copy **wav2lip256.pth** into this project’s **models/** folder (use as `models/wav2lip256.pth` or rename to `wav2lip.pth` if your app expects that name).
2. Download **wav2lip256_avatar1.tar.gz**, extract it, and copy the **wav2lip256_avatar1** folder into **data/avatars/**.

### Run

```bash
python app.py --transport webrtc --model wav2lip --avatar_id wav2lip256_avatar1
```

Or use the helper script:

```bash
./run_local.sh
```

**Server:** Open **TCP port 8010** and **UDP ports 1–65536** (or the port shown in the log).

**Clients:**

1. **Browser:** Open `http://<server-ip>:8010/webrtcapi.html`, click **Start** to play the digital human video, then type text in the box and submit to have the digital human speak it.
2. **Desktop client:** Download from <https://pan.quark.cn/s/d7192d8ac19b>.

**Quick try:** Use the [online image](https://www.compshare.cn/images/4458094e-a43d-45fe-9b57-de79253befe4?referral_code=3XW3852OBmnD089hMMrtuU&ytag=GPU_GitHub_livetalking) to create an instance and run.

**Hugging Face access:** If you cannot reach Hugging Face, before running:

```bash
export HF_ENDPOINT=https://hf-mirror.com
```

---

## 3. More usage

Full documentation: <https://livetalking-doc.readthedocs.io/>

---

## 4. Docker

You can run without local installation:

```bash
docker run --gpus all -it --network=host --rm registry.cn-beijing.aliyuncs.com/codewithgpu2/lipku-metahuman-stream:2K9qaMBu8v
```

Code is at `/root/metahuman-stream`. Run `git pull` for the latest code, then use the same commands as in sections 2 and 3.

**Pre-built images:**

- **UCloud:** <https://www.compshare.cn/images/4458094e-a43d-45fe-9b57-de79253befe4?referral_code=3XW3852OBmnD089hMMrtuU&ytag=GPU_GitHub_livetalking> — [UCloud guide](https://livetalking-doc.readthedocs.io/zh-cn/latest/ucloud/ucloud.html)
- **AutoDL:** <https://www.codewithgpu.com/i/lipku/livetalking/base> — [AutoDL guide](https://livetalking-doc.readthedocs.io/zh-cn/latest/autodl/README.html). AutoDL cannot open UDP ports; if video does not show, deploy an SRS or TURN relay.

---

## 5. Performance

- Performance depends on CPU and GPU: video encoding uses CPU (scales with resolution); lip-sync inference uses GPU.
- Idle concurrency is CPU-bound; concurrent speaking sessions are GPU-bound.
- In logs, **inferfps** = GPU inference FPS, **finalfps** = final stream FPS. Both should be ≥ 25 for real-time. If inferfps ≥ 25 but finalfps < 25, the CPU is the bottleneck.

**Approximate real-time performance:**

| Model        | GPU    | FPS  |
|-------------|--------|------|
| wav2lip256  | 3060   | 60   |
| wav2lip256  | 3080Ti | 120  |
| musetalk    | 3080Ti | 42   |
| musetalk    | 3090   | 45   |
| musetalk    | 4090   | 72   |

- **wav2lip256:** RTX 3060 or better.
- **musetalk:** RTX 3080 Ti or better.

---

## 6. Commercial edition

Extended features for users who need more than the open-source version:

1. High-definition Wav2Lip model
2. Full voice interaction with wake word or button to interrupt
3. Real-time subtitles and events for sentence start/end
4. Per-connection avatar and voice; faster avatar loading
5. Unlimited-length avatar videos
6. Real-time audio stream input API
7. Transparent digital human with dynamic background
8. Live avatar switching
9. Python client

Details: <https://livetalking-doc.readthedocs.io/zh-cn/latest/service.html>

---

## 7. Disclaimer

Videos based on this project and published on Bilibili, WeChat Video, Douyin, etc. should include the LiveTalking watermark and attribution.

---

If this project helps you, consider giving it a star. Contributions are welcome.

- Knowledge Planet: https://t.zsxq.com/7NMyO — FAQ, best practices, Q&A
- WeChat: Digital Human Technology (scan QR for official account)  
<img src="./assets/qrcode-wechat.jpg" align="middle" width="120" />
