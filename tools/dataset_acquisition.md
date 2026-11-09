# Step 4 — Controlled Dataset Acquisition

Sources for Indian plate + vehicle detection datasets. All are external
dependencies — download separately, do NOT commit large files to Git.

## Recommended first: Indian Truck License Plates sample

**GitHub:** https://github.com/witvix/indian-truck-license-plates  
- ~470 photos, 589 plate boxes with text, 29 Indian states, day/night  
- Labels: YOLO / COCO / CSV  
- Also on Kaggle and Hugging Face  
- Use the **sample** subset first for controlled benchmarking  

**Kaggle:** https://www.kaggle.com/datasets/witvixsystem/indian-truck-license-plates-sample

## Other Indian plate datasets

| Dataset | Source | Format | Notes |
|---------|--------|--------|-------|
| Indian Number Plates | https://huggingface.co/datasets/Dataclusterlabspvtltd/indian-number-plates-dataset | Pascal VOC / COCO / YOLO | ~200 sample images |
| VisionPlate_ANPR | IEEE Dataport | — | Research dataset |
| Roboflow Indian Number Plate | https://roboflow.com/ | YOLO | Public workspace |
| ANPR 2 | — | — | Additional ANPR source |
| COCO val2017 | https://cocodataset.org/#download | COCO | General vehicle detection (car, bus, truck, motorcycle) |

## Download steps

1. Pick a dataset (start with Indian Truck License Plates sample)
2. Download the archive (images + labels)
3. Extract to: `datasets/<name>/`
4. Expected layout:
   ```
   datasets/
     indian-truck-plates/
       images/
       labels/
       plates.csv (optional, plate text)
       README.md
   ```

## Claim discipline

Datasets are for controlled benchmarking only. Do NOT publish accuracy or
false-alert figures without documented tests (hardware, footage conditions,
sample size). Human review remains mandatory — no automatic fines.

## References

- Flashw03/Realtime-LicensePlateRecognitionML: YOLOv8 + EasyOCR Indian ALPR, mAP@50 0.967
- IEEE 10425814: YOLOv7x + EasyOCR Indian plates, 99% accuracy paper