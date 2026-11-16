#!/usr/bin/env python3
"""
Step 4 — License Plate Detector Training

Converts COCO-format annotations (from witvix/indian-truck-license-plates-sample)
into YOLO format and fine-tunes YOLO11n for license plate detection.

Usage:
    python3 tools/train_plate_detector.py \\
        --coco tests/data/real_datasets/annotations_coco.json \\
        --images tests/data/real_datasets \\
        --data-yaml tests/data/real_datasets/data.yaml \\
        --weights yolo11n.pt \\
        --epochs 50 \\
        --imgsz 640 \\
        --output runs/plate_detector/

Prerequisites:
    pip install ultralytics opencv-python numpy pyyaml

Outputs:
    runs/plate_detector/weights/best.pt   — trained plate detector
    runs/plate_detector/weights/last.pt   — last checkpoint
    runs/plate_detector/results.csv       — training metrics
    models/dataset_manifest.json          — dataset provenance (created separately)

Claim discipline:
    This script produces a trained model. Report metrics only from the
    held-out test set — never from training/validation data.
"""

import argparse
import json
import os
import shutil
from pathlib import Path
from collections import defaultdict

try:
    from ultralytics import YOLO
    ULTRALYTICS_AVAILABLE = True
except ImportError:
    ULTRALYTICS_AVAILABLE = False


def parse_args():
    p = argparse.ArgumentParser(description="Train YOLO11n license plate detector")
    p.add_argument("--coco", required=True,
                   help="Path to COCO annotations JSON")
    p.add_argument("--images", required=True,
                   help="Directory containing images (or parent of images/)")
    p.add_argument("--data-yaml", required=True,
                   help="Path to data.yaml (will be overwritten with train/val split)")
    p.add_argument("--weights", default="yolo11n.pt",
                   help="Base YOLO weights (yolo11n.pt, yolo11s.pt, or path to .pt)")
    p.add_argument("--epochs", type=int, default=50,
                   help="Number of training epochs")
    p.add_argument("--imgsz", type=int, default=640,
                   help="Inference image size")
    p.add_argument("--batch", type=int, default=16,
                   help="Batch size")
    p.add_argument("--device", default="cpu",
                   help="cuda:0, cpu, or mps")
    p.add_argument("--output", default="runs/plate_detector",
                   help="Output directory for trained weights")
    p.add_argument("--val-split", type=float, default=0.2,
                   help="Fraction of images reserved for validation")
    return p.parse_args()


def convert_coco_to_yolo(coco_path: Path, images_dir: Path,
                         val_split: float = 0.2,
                         output_dir: Path = Path("yolo_dataset")):
    """
    Convert COCO annotations to YOLO format:
        <class_id> <x_center> <y_center> <width> <height>  (all normalised 0..1)
    Splits images into train/val by image id (deterministic, no leakage).
    Returns (train_images, val_images) lists of image file names.
    """
    with open(coco_path) as f:
        coco = json.load(f)

    # Build image_id -> annotations mapping
    img_anns = defaultdict(list)
    for ann in coco["annotations"]:
        img_anns[ann["image_id"]].append(ann)

    # Map COCO image ids to file names
    image_info = {img["id"]: img for img in coco["images"]}

    # Deterministic split by image id (sorted) — prevents leakage
    all_image_ids = sorted(image_info.keys())
    n_val = max(1, int(len(all_image_ids) * val_split))
    val_ids = set(all_image_ids[:n_val])
    train_ids = set(all_image_ids[n_val:])

    # Create YOLO directory structure
    for split in ("train", "val"):
        (output_dir / split / "images").mkdir(parents=True, exist_ok=True)
        (output_dir / split / "labels").mkdir(parents=True, exist_ok=True)

    train_files = []
    val_files = []

    for img_id in all_image_ids:
        info = image_info[img_id]
        file_name = info["file_name"]
        width = info["width"]
        height = info["height"]

        src_path = images_dir / file_name
        if not src_path.exists():
            # Try images/ subdirectory
            alt = images_dir / "images" / file_name
            if alt.exists():
                src_path = alt
            else:
                print(f"[warn] Image not found: {file_name}")
                continue

        split = "val" if img_id in val_ids else "train"
        dst_img = output_dir / split / "images" / file_name
        shutil.copy2(src_path, dst_img)

        # Write YOLO label file
        label_stem = Path(file_name).stem
        label_path = output_dir / split / "labels" / f"{label_stem}.txt"

        lines = []
        for ann in img_anns.get(img_id, []):
            # COCO bbox: [x, y, w, h] in absolute pixels
            x, y, w, h = ann["bbox"]
            # Convert to normalised YOLO: x_center, y_center, w, h (0..1)
            x_center = (x + w / 2.0) / width
            y_center = (y + h / 2.0) / height
            w_norm = w / width
            h_norm = h / height
            class_id = ann["category_id"] - 1  # COCO is 1-indexed, YOLO is 0-indexed
            lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {w_norm:.6f} {h_norm:.6f}")

        label_path.write_text("\n".join(lines))

        if split == "train":
            train_files.append(file_name)
        else:
            val_files.append(file_name)

    print(f"[convert] {len(train_files)} train images, {len(val_files)} val images")
    print(f"[convert] Output: {output_dir.resolve()}")
    return train_files, val_files


def write_data_yaml(data_yaml_path: Path, dataset_dir: Path,
                    train_files: list, val_files: list):
    """Write data.yaml for YOLO training."""
    content = f"""path: {dataset_dir.resolve()}
train: images  # relative to path; YOLO reads all images in train/images
val: images
nc: 1
names:
  0: license_plate
"""
    data_yaml_path.write_text(content)
    print(f"[yaml] Written {data_yaml_path}")


def train_model(weights: str, data_yaml: Path, epochs: int,
                imgsz: int, batch: int, device: str, output_dir: Path):
    """Fine-tune YOLO11n on the plate detection dataset."""
    if not ULTRALYTICS_AVAILABLE:
        print("[error] ultralytics not installed. Run: pip install ultralytics")
        return None

    print(f"[train] Loading base weights: {weights}")
    model = YOLO(weights)

    print(f"[train] Starting fine-tuning: epochs={epochs}, imgsz={imgsz}, batch={batch}, device={device}")
    results = model.train(
        data=str(data_yaml),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device=device,
        project=str(output_dir.parent),
        name=output_dir.name,
        verbose=True,
    )

    best_weights = output_dir / "weights" / "best.pt"
    if best_weights.exists():
        print(f"[ok] Best weights: {best_weights}")
    else:
        print(f"[warn] best.pt not found at {best_weights}")

    return model


def main():
    args = parse_args()

    coco_path = Path(args.coco)
    images_dir = Path(args.images)
    data_yaml_path = Path(args.data_yaml)
    output_dir = Path(args.output)

    if not coco_path.exists():
        raise SystemExit(f"COCO annotations not found: {coco_path}")
    if not images_dir.exists():
        raise SystemExit(f"Images directory not found: {images_dir}")

    print("=== Step 4: License Plate Detector Training ===")
    print(f"COCO: {coco_path}")
    print(f"Images: {images_dir}")
    print(f"Base weights: {args.weights}")
    print(f"Epochs: {args.epochs}, imgsz: {args.imgsz}, batch: {args.batch}, device: {args.device}")
    print()

    # Step 1: Convert COCO -> YOLO format
    train_files, val_files = convert_coco_to_yolo(
        coco_path, images_dir, args.val_split,
        output_dir / "yolo_dataset"
    )

    # Step 2: Write data.yaml
    dataset_dir = output_dir / "yolo_dataset"
    write_data_yaml(data_yaml_path, dataset_dir, train_files, val_files)

    # Step 3: Train
    if ULTRALYTICS_AVAILABLE:
        train_model(args.weights, data_yaml_path, args.epochs,
                    args.imgsz, args.batch, args.device, output_dir)
    else:
        print("\n[skip] Training skipped — ultralytics not installed.")
        print("       Install with: pip install ultralytics")
        print(f"       Then re-run: python3 {Path(__file__).resolve()} --coco {coco_path} --images {images_dir} --data-yaml {data_yaml_path}")


if __name__ == "__main__":
    main()