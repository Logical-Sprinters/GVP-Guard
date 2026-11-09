#!/usr/bin/env python3
"""
Download YOLO11n / YOLO11s pretrained weights.

Sources:
- Official Ultralytics CDN (GitHub releases)
- Hugging Face mirror: https://huggingface.co/Ultralytics/YOLO11

Usage:
    python tools\download_weights.py --model yolo11n --out models\weights\yolo11n.pt
    python tools\download_weights.py --model yolo11s --out models\weights\yolo11s.pt
"""

import argparse
from pathlib import Path
import urllib.request

WEIGHTS = {
    "yolo11n": {
        "url": "https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo11n.pt",
        "hf": "https://huggingface.co/Ultralytics/YOLO11/resolve/main/yolo11n.pt",
        "size_mb": 5.6,
        "sha256": None,  # verify after download if needed
    },
    "yolo11s": {
        "url": "https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo11s.pt",
        "hf": "https://huggingface.co/Ultralytics/YOLO11/resolve/main/yolo11s.pt",
        "size_mb": 9.3,
        "sha256": None,
    },
    "yolo11n.onnx": {
        "url": "https://huggingface.co/Ultralytics/YOLO11/resolve/main/yolo11n.onnx",
        "hf": None,
        "size_mb": 5.6,
        "sha256": None,
    },
}


def parse_args():
    p = argparse.ArgumentParser(description="Download YOLO11 pretrained weights")
    p.add_argument("--model", choices=list(WEIGHTS.keys()), default="yolo11n",
                   help="Model variant to download")
    p.add_argument("--out", required=True, help="Output path for the weights file")
    p.add_argument("--mirror", choices=["github", "hf"], default="github",
                   help="Download mirror (github = Ultralytics CDN, hf = Hugging Face)")
    return p.parse_args()


def main():
    args = parse_args()
    info = WEIGHTS[args.model]
    url = info["url"] if args.mirror == "github" else info["hf"]
    if not url:
        raise SystemExit(f"No {args.mirror} URL for {args.model}")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    print(f"Downloading {args.model} from {url}")
    print(f"Saving to: {out}")
    print(f"Expected size: ~{info['size_mb']} MB")

    try:
        urllib.request.urlretrieve(url, str(out))
    except Exception as e:
        # Try the other mirror as fallback
        fallback = info["hf"] if args.mirror == "github" else info["url"]
        if fallback:
            print(f"Primary mirror failed ({e}), trying fallback: {fallback}")
            urllib.request.urlretrieve(fallback, str(out))
        else:
            raise

    size_mb = out.stat().st_size / (1024 * 1024)
    print(f"\nDownloaded: {out} ({size_mb:.2f} MB)")
    print(f"\nNext: python -c \"from ultralytics import YOLO; m=YOLO('{out}'); print('Model loaded')\"")


if __name__ == "__main__":
    main()