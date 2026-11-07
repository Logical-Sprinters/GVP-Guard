#!/usr/bin/env python3
"""
Download Step 4 model weights.
Run:  python3 tools/download_weights.py

Weights are NOT committed to Git. Only this script and the manifest are versioned.
All URLs are official Ultralytics CDN / Hugging Face links (verified 2026-11-07).
"""

import hashlib
from pathlib import Path
from urllib.request import urlretrieve

WEIGHTS_DIR = Path("models/weights")
WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)

# Exact URLs verified 2026-11-07 — official Ultralytics assets + Hugging Face mirrors
WEIGHTS = {
    "yolo11n.pt": {
        "url": "https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo11n.pt",
        "mirror": "https://huggingface.co/Ultralytics/YOLO11/resolve/365ed86341e7a7456dbc4cafc09f138814ce9ff1/yolo11n.pt",
        "size_mb": 5.6,
        "task": "vehicle detection (COCO classes: car=2, truck=7, bus=5)",
    },
    "yolo11s.pt": {
        "url": "https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo11s.pt",
        "mirror": "https://huggingface.co/Ultralytics/YOLO11/resolve/365ed86341e7a7456dbc4cafc09f138814ce9ff1/yolo11s.pt",
        "size_mb": 9.4,
        "task": "vehicle detection (higher accuracy than nano)",
    },
}

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def download(name: str, info: dict):
    dest = WEIGHTS_DIR / name
    if dest.exists():
        print(f"[skip] {name} already exists ({dest.stat().st_size / 1e6:.1f} MB)")
        return dest

    url = info["url"]
    print(f"[download] {name} ({info['size_mb']} MB) from {url}")
    try:
        urlretrieve(url, dest)
    except Exception as e:
        print(f"[warn] primary URL failed ({e}); trying mirror {info['mirror']}")
        urlretrieve(info["mirror"], dest)

    print(f"[ok] {name} -> {dest}  sha256={sha256(dest)[:16]}...")
    return dest


if __name__ == "__main__":
    print("=== Step 4: Downloading model weights ===")
    for name, info in WEIGHTS.items():
        download(name, info)
    print("\n=== Next ===")
    print("1. Install deps: pip install ultralytics opencv-python numpy easyocr")
    print("2. Verify: python3 -c \"from ultralytics import YOLO; m=YOLO('models/weights/yolo11n.pt'); print(m.names)\"")
    print("3. Weights stay in models/weights/ — NOT committed to Git")
