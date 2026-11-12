#!/usr/bin/env python3
"""
Generate synthetic test videos for the 7 golden scenarios (GS-01 to GS-07).

Uses real car crops from image-3.png composited on a road background so that
YOLO11n can detect them as vehicles. Person figures are drawn with OpenCV.

Scenarios:
  GS-01: Normal pass - car passes through zone without stopping (no incident)
  GS-02: Long stop, no deposit - car stops >2s, no person overlap (incident, reject)
  GS-03: Person deposits object - car stops, person overlaps (incident, review)
  GS-04: Waste already present - waste object before vehicle arrives (no incident)
  GS-05: Plate unreadable - car stops + person overlap, plate text garbage (incident, review)
  GS-06: Network fails - car stops + person overlap (incident, queue for sync)
  GS-07: Duplicate event - same vehicle detected multiple times (one incident only)
"""

import cv2
import numpy as np
import os
import sys

# Add repo path for car crops
CAR_CROP_DIR = "/home/user/repo/tests/data"
OUTPUT_DIR = "/home/user/repo/tests/data/scenarios"

WIDTH, HEIGHT = 640, 480
FPS = 25
DURATION_SEC = 6  # each video is 6 seconds
TOTAL_FRAMES = FPS * DURATION_SEC

# GVP polygon zone (normalized [0..1]) - matches test harness default
POLYGON = [
    {"x": 0.10, "y": 0.60},
    {"x": 0.90, "y": 0.60},
    {"x": 0.90, "y": 1.00},
    {"x": 0.10, "y": 1.00},
]

def polygon_pts():
    """Return polygon points in pixel coordinates."""
    return np.array([[int(p["x"] * WIDTH), int(p["y"] * HEIGHT)] for p in POLYGON], dtype=np.int32)

def create_road_background():
    """Create a simple road scene background."""
    img = np.ones((HEIGHT, WIDTH, 3), dtype=np.uint8) * 255
    # Sky
    img[0:int(HEIGHT * 0.55), :] = [180, 210, 255]  # light blue sky
    # Road
    img[int(HEIGHT * 0.55):, :] = [60, 60, 60]  # gray road
    # Lane markings (dashed white line)
    for x in range(0, WIDTH, 60):
        cv2.line(img, (x, int(HEIGHT * 0.75)), (min(x + 30, WIDTH), int(HEIGHT * 0.75)), (255, 255, 255), 3)
    # Zone boundary line
    cv2.line(img, (int(POLYGON[0]["x"] * WIDTH), int(POLYGON[0]["y"] * HEIGHT)),
             (int(POLYGON[1]["x"] * WIDTH), int(POLYGON[1]["y"] * HEIGHT)), (0, 255, 0), 2)
    return img

def load_car_crops():
    """Load car crops from image-3.png extractions."""
    crops = []
    for f in sorted(os.listdir(CAR_CROP_DIR)):
        if f.startswith("car_") and f.endswith(".png"):
            path = os.path.join(CAR_CROP_DIR, f)
            crop = cv2.imread(path)
            if crop is not None:
                crops.append(crop)
                print(f"  Loaded car crop: {f} {crop.shape}")
    return crops

def draw_person(img, cx, cy, scale=1.0):
    """Draw a simple person figure. Returns the person bounding box."""
    # Head (circle)
    head_r = int(18 * scale)
    cv2.circle(img, (cx, cy - head_r - 5), head_r, (200, 150, 100), -1)
    # Body (rectangle)
    body_w = int(20 * scale)
    body_h = int(35 * scale)
    cv2.rectangle(img, (cx - body_w // 2, cy - head_r - 5),
                  (cx + body_w // 2, cy - head_r - 5 + body_h), (100, 100, 200), -1)
    # Arms
    cv2.line(img, (cx - body_w // 2 - 5, cy - head_r - 5 + 10),
             (cx - body_w // 2 - 15, cy - head_r - 5 + 25), (100, 100, 200), 4)
    cv2.line(img, (cx + body_w // 2 + 5, cy - head_r - 5 + 10),
             (cx + body_w // 2 + 15, cy - head_r - 5 + 25), (100, 100, 200), 4)
    # Legs
    cv2.line(img, (cx - 8, cy - head_r - 5 + body_h),
             (cx - 8, cy - head_r - 5 + body_h + 20), (80, 80, 80), 4)
    cv2.line(img, (cx + 8, cy - head_r - 5 + body_h),
             (cx + 8, cy - head_r - 5 + body_h + 20), (80, 80, 80), 4)
    # Return bounding box
    return (cx - body_w // 2 - 15, cy - head_r - 5 - head_r,
            cx + body_w // 2 + 15, cy - head_r - 5 + body_h + 20)

def composite_car(background, car_crop, cx, cy, scale=1.0):
    """Composite a car crop onto the background at (cx, cy)."""
    h, w = car_crop.shape[:2]
    new_w = int(w * scale)
    new_h = int(h * scale)
    resized = cv2.resize(car_crop, (new_w, new_h))
    
    x1 = cx - new_w // 2
    y1 = cy - new_h // 2
    x2 = x1 + new_w
    y2 = y1 + new_h
    
    # Clip to bounds
    if x1 < 0 or y1 < 0 or x2 > WIDTH or y2 > HEIGHT:
        return None, (x1, y1, x2, y2)
    
    # Simple alpha blend (just paste, cars are opaque)
    background[y1:y2, x1:x2] = resized
    return background, (x1, y1, x2, y2)

def generate_video(filename, scene_setup, car_crops):
    """Generate a single scenario video."""
    print(f"\nGenerating {filename}...")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, FPS, (WIDTH, HEIGHT))
    
    poly = polygon_pts()
    
    for frame_idx in range(TOTAL_FRAMES):
        img = create_road_background()
        # Draw zone polygon
        cv2.polylines(img, [poly], True, (0, 255, 0), 2)
        
        t = frame_idx / FPS  # time in seconds
        
        # Execute scene setup
        scene_setup(img, frame_idx, t, car_crops)
        
        out.write(img)
    
    out.release()
    print(f"  Saved: {filename} ({TOTAL_FRAMES} frames @ {FPS} fps)")

# --- Scenario setups ---

def gs01_normal_pass(img, frame_idx, t, car_crops):
    """GS-01: Car passes through zone without stopping -> no incident."""
    car = car_crops[0] if car_crops else None
    if car is None:
        return
    # Car enters from left, moves right through zone, exits
    x = int(-200 + (frame_idx / TOTAL_FRAMES) * (WIDTH + 400))
    cy = int(HEIGHT * 0.78)
    result, box = composite_car(img, car, x, cy, scale=0.35)
    if result is None:
        # Car partially out of bounds, draw at clipped position
        x = max(0, min(WIDTH, x))
        cy = max(0, min(HEIGHT, cy))
        composite_car(img, car, x, cy, scale=0.35)

def gs02_long_stop_no_deposit(img, frame_idx, t, car_crops):
    """GS-02: Car stops in zone for >2s, no person -> incident, reject."""
    car = car_crops[0] if len(car_crops) > 0 else None
    car2 = car_crops[1] if len(car_crops) > 1 else car
    
    if car is None:
        return
    
    # Car enters zone at t=1s, stops at t=2s until t=5s, exits at t=5.5s
    if t < 1.0:
        x = int(-100 + (t / 1.0) * 300)
        cy = int(HEIGHT * 0.78)
        composite_car(img, car, x, cy, scale=0.35)
    elif t < 2.0:
        # Moving into stop position
        x = int(200 + (t - 1.0) * 100)
        cy = int(HEIGHT * 0.78)
        composite_car(img, car, x, cy, scale=0.35)
    elif t < 5.0:
        # Stopped in zone
        x = 300
        cy = int(HEIGHT * 0.78)
        composite_car(img, car, x, cy, scale=0.35)
    else:
        # Exiting
        x = int(300 + (t - 5.0) * 200)
        cy = int(HEIGHT * 0.78)
        if x < WIDTH + 200:
            composite_car(img, car, x, cy, scale=0.35)

def gs03_person_deposits(img, frame_idx, t, car_crops):
    """GS-03: Car stops, person overlaps with car -> incident, review."""
    car = car_crops[0] if car_crops else None
    if car is None:
        return
    
    if t < 1.5:
        x = int(-100 + (t / 1.5) * 400)
        cy = int(HEIGHT * 0.78)
        composite_car(img, car, x, cy, scale=0.35)
    elif t < 4.5:
        # Car stopped in zone
        x = 300
        cy = int(HEIGHT * 0.78)
        composite_car(img, car, x, cy, scale=0.35)
        # Person appears near car (overlapping) from t=2.5 to t=4.0
        if 2.5 <= t <= 4.0:
            px = 300 + int(10 * np.sin((t - 2.5) * 5))
            py = int(HEIGHT * 0.72)
            pbox = draw_person(img, px, py, scale=0.8)
    else:
        x = int(300 + (t - 4.5) * 200)
        cy = int(HEIGHT * 0.78)
        if x < WIDTH + 200:
            composite_car(img, car, x, cy, scale=0.35)

def gs04_waste_present(img, frame_idx, t, car_crops):
    """GS-04: Waste object present before vehicle arrives -> no incident."""
    car = car_crops[0] if car_crops else None
    if car is None:
        return
    
    # Draw waste object (brown rectangle) in zone from start
    waste_box = (250, int(HEIGHT * 0.80), 330, int(HEIGHT * 0.90))
    cv2.rectangle(img, (waste_box[0], waste_box[1]), (waste_box[2], waste_box[3]), (101, 67, 33), -1)
    cv2.rectangle(img, (waste_box[0], waste_box[1]), (waste_box[2], waste_box[3]), (0, 0, 0), 2)
    
    # Car passes through without stopping near waste
    if t < 2.0:
        x = int(-100 + (t / 2.0) * 500)
        cy = int(HEIGHT * 0.70)
        composite_car(img, car, x, cy, scale=0.35)
    else:
        x = int(400 + (t - 2.0) * 200)
        cy = int(HEIGHT * 0.70)
        if x < WIDTH + 200:
            composite_car(img, car, x, cy, scale=0.35)

def gs05_plate_unreadable(img, frame_idx, t, car_crops):
    """GS-05: Car stops, person overlaps, plate unreadable -> incident, review."""
    car = car_crops[0] if car_crops else None
    if car is None:
        return
    
    if t < 1.0:
        x = int(-100 + (t / 1.0) * 400)
        cy = int(HEIGHT * 0.78)
        composite_car(img, car, x, cy, scale=0.35)
    elif t < 5.0:
        x = 300
        cy = int(HEIGHT * 0.78)
        composite_car(img, car, x, cy, scale=0.35)
        # Person overlaps with car
        if 1.5 <= t <= 4.5:
            px = 300
            py = int(HEIGHT * 0.72)
            draw_person(img, px, py, scale=0.8)
    else:
        x = int(300 + (t - 5.0) * 200)
        cy = int(HEIGHT * 0.78)
        if x < WIDTH + 200:
            composite_car(img, car, x, cy, scale=0.35)

def gs06_network_fail(img, frame_idx, t, car_crops):
    """GS-06: Car stops, person overlaps -> incident, queue for sync."""
    car = car_crops[0] if car_crops else None
    if car is None:
        return
    
    if t < 1.5:
        x = int(-100 + (t / 1.5) * 400)
        cy = int(HEIGHT * 0.78)
        composite_car(img, car, x, cy, scale=0.35)
    elif t < 5.0:
        x = 300
        cy = int(HEIGHT * 0.78)
        composite_car(img, car, x, cy, scale=0.35)
        # Person overlaps
        if 2.0 <= t <= 4.0:
            px = 300
            py = int(HEIGHT * 0.72)
            draw_person(img, px, py, scale=0.8)
    else:
        x = int(300 + (t - 5.0) * 200)
        cy = int(HEIGHT * 0.78)
        if x < WIDTH + 200:
            composite_car(img, car, x, cy, scale=0.35)

def gs07_duplicate_event(img, frame_idx, t, car_crops):
    """GS-07: Same vehicle detected multiple times -> one incident only."""
    car = car_crops[0] if car_crops else None
    if car is None:
        return
    
    # Car enters, stops briefly, leaves, then re-enters (duplicate detection)
    if t < 2.0:
        x = int(-100 + (t / 2.0) * 400)
        cy = int(HEIGHT * 0.78)
        composite_car(img, car, x, cy, scale=0.35)
    elif t < 3.0:
        # Stopped briefly
        x = 300
        cy = int(HEIGHT * 0.78)
        composite_car(img, car, x, cy, scale=0.35)
    elif t < 4.0:
        # Exiting
        x = int(300 + (t - 3.0) * 400)
        cy = int(HEIGHT * 0.78)
        if x < WIDTH + 200:
            composite_car(img, car, x, cy, scale=0.35)
    elif t < 5.0:
        # Re-entering (same vehicle, duplicate)
        x = int(-100 + (t - 4.0) * 400)
        cy = int(HEIGHT * 0.78)
        composite_car(img, car, x, cy, scale=0.35)
    else:
        x = int(300 + (t - 5.0) * 200)
        cy = int(HEIGHT * 0.78)
        if x < WIDTH + 200:
            composite_car(img, car, x, cy, scale=0.35)

SCENARIOS = {
    "GS-01": ("gs01_normal_pass.mp4", gs01_normal_pass, False, None, 1.0),
    "GS-02": ("gs02_long_stop_no_deposit.mp4", gs02_long_stop_no_deposit, True, "Reject", 10.0),
    "GS-03": ("gs03_person_deposits.mp4", gs03_person_deposits, True, "Review", 5.0),
    "GS-04": ("gs04_waste_present.mp4", gs04_waste_present, False, None, 1.0),
    "GS-05": ("gs05_plate_unreadable.mp4", gs05_plate_unreadable, True, "Review", 5.0),
    "GS-06": ("gs06_network_fail.mp4", gs06_network_fail, True, None, 5.0),
    "GS-07": ("gs07_duplicate_event.mp4", gs07_duplicate_event, True, None, 5.0),
}

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    car_crops = load_car_crops()
    if not car_crops:
        print("ERROR: No car crops found! Run car extraction first.")
        sys.exit(1)
    
    print(f"Loaded {len(car_crops)} car crops")
    
    scenarios_json = {"notes": "Synthetic test footage for GS-01 to GS-07", "scenarios": []}
    
    for gs_id, (filename, setup_fn, expected_incident, expected_decision, max_stop) in SCENARIOS.items():
        filepath = os.path.join(OUTPUT_DIR, filename)
        generate_video(filepath, setup_fn, car_crops)
        
        scenarios_json["scenarios"].append({
            "id": gs_id,
            "name": filename.replace(".mp4", "").replace("gs", "").title(),
            "video": filepath,
            "expected_incident": expected_incident,
            "expected_decision": expected_decision,
            "max_stop_secs": max_stop,
            "notes": f"Synthetic video for {gs_id}",
        })
    
    # Write scenarios JSON
    scenarios_path = os.path.join(OUTPUT_DIR, "scenarios.json")
    with open(scenarios_path, "w") as f:
        import json
        json.dump(scenarios_json, f, indent=2)
    print(f"\nScenarios manifest written to: {scenarios_path}")

if __name__ == "__main__":
    main()
