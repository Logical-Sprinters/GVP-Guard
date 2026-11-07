# Step 4 Dataset Acquisition — Exact Sources (verified 2026-11-07)

The team needs a controlled dataset BEFORE Step 4 can begin. Below are specific,
free, downloadable datasets relevant to vehicle detection and Indian ANPR.
No field footage collection is required to start benchmarking.

---

## 1. Vehicle Detection (general, for YOLO11n baseline)

| Dataset | What it is | Size | Source |
|---------|-----------|------|--------|
| **COCO val2017** | 5,000 images, 80 classes including car/truck/bus | ~1 GB | `http://images.cocodataset.org/zips/val2017.zip` |
| **DETRAC** | Vehicle detection/tracking benchmark, multiple camera angles | ~2 GB | `https://detrac-db.hrvatin.net/` (registration required) |

Use COCO to verify YOLO11n detects cars/trucks/buses out of the box before any fine-tuning.

---

## 2. Indian License Plate Detection + OCR (specific to GVP-Guard use case)

These are the most relevant datasets for the ANPR portion of Step 4:

### a) Indian Truck License Plates Sample (FREE, ready to download)
- **470 photos**, 589 plate boxes with plate text, 29 Indian states, 43% night photos
- Two-line plates (69%), single-line plates, small plates (21% < 50 px)
- YOLO, COCO, and CSV labels included
- **Download:** https://www.kaggle.com/datasets/witvixsystem/indian-truck-license-plates-sample
- **Mirror:** https://huggingface.co/datasets/witvix/indian-truck-license-plates-sample (free; fill in a short access form)
- **Repo/docs:** https://github.com/witvix/indian-truck-license-plates

### b) Indian Number Plates Dataset (Hugging Face)
- Sample: ~200 images; Full: 15,000+ images, 10,000+ annotated, 700+ cities
- Pascal VOC / COCO / YOLO formats; includes `number_plate_text` attribute
- **Download:** https://huggingface.co/datasets/Dataclusterlabspvtltd/indian-number-plates-dataset

### c) VisionPlate_ANPR (IEEE Dataport)
- Indian vehicle classification + license plate detection + OCR dataset
- YOLOv8-formatted: `Indian_License_Plate_YOLOv8_Dataset.zip` (3.85 GB) with train/valid/test splits
- OCR dataset: clean + noisy plate crops for sequence modeling
- **Download:** https://dx.doi.org/10.21227/gzcb-rt97 (IEEE Dataport, login required)

### d) Indian License Plate Recognition Dataset (YOLO & OCR) (IEEE Dataport)
- YOLO detection dataset + CNN character recognition dataset
- Addresses hand-painted fonts, multi-line square formats, obstructions
- **Download:** https://dx.doi.org/10.21227/ee39-dp36 (IEEE Dataport, login required)

### e) Roboflow Indian Number Plate Dataset (used in published research)
- ~10,000 annotated images in YOLO format
- Published research achieved mAP@50 0.967 (YOLOv8) / 92.4% (YOLOv11) + 88.2% OCR accuracy
- **Download:** https://universe.roboflow.com/ (search "Indian number plate detection")

---

## 3. ANPR Surveillance (street-level)

| Dataset | Size | Source |
|---------|------|--------|
| ANPR 2 (Jayanth B) | 131,980 images, 7.3 GB | https://platform.ultralytics.com/jayanth-b/datasets/number-plate-dataset |

---

## Recommended Acquisition Order

1. **Week 1:** Download YOLO11n weights + COCO val2017. Verify vehicle detection works out of the box.
2. **Week 2:** Download Indian Truck License Plates sample (Kaggle/HF). Begin plate detection fine-tuning.
3. **Week 3:** Download VisionPlate_ANPR or Roboflow Indian dataset. Fine-tune plate detector + EasyOCR.
4. **Week 4:** Collect controlled Gandhidham footage (with GMC permission) for final validation.

---

## Dataset Integrity

- Record source URL, download date, license, and sample count in `models/dataset_manifest.json`
- Do NOT commit dataset files or weights to Git — record hashes only
- Split by camera/location (not random frames) per `docs/05_DATA_AND_ML_PLAN.md`
- Held-out test set is never touched during development
