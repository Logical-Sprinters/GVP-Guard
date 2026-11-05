# Data and Machine-Learning Plan

## Event taxonomy
- Normal pass
- Short stop
- Long stop without dumping
- Legal/ambiguous unloading
- Probable dumping
- Person-only deposit
- Waste present before arrival
- Object removed after temporary placement

## Annotation schema
For each clip: source/license, camera, date, lighting, weather, GVP polygon, vehicle boxes/tracks, person boxes, plate boxes, event start/end, object transfer and final label.

## Dataset split
Split by location/camera, not random frames, to prevent leakage. Maintain train, validation and held-out test sets.

## Controlled data collection
Use a permitted location, clean boxes/bags, fixed camera, varied angles/light and negative scenarios. Remove all staged material.

## Event model strategy
Start rule-based: zone + stop + scene change. Add learned cues only when data supports them. Compare against the simple baseline.

## ANPR strategy
Detect plate -> track -> score frames -> rectify/enhance -> OCR each frame -> majority agreement -> Indian-format validation -> manual review.

## Metrics
- Detection precision/recall/mAP
- Tracking ID switches
- Event precision/recall and false alerts per camera-hour
- Full plate and character accuracy
- Processing latency and FPS

## Data governance
Store provenance and consent/permission. Avoid faces where unnecessary. Do not use unlicensed footage or real registry data without authorization.
