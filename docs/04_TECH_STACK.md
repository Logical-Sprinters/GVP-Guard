# Proposed Technology Stack

This is a proposed next-stage stack, not a statement that every item is implemented.

## Vision
- Python 3.11+
- OpenCV
- Ultralytics YOLO11 nano/small after benchmarking
- ByteTrack; IoU tracker fallback
- Plate detector + EasyOCR; PaddleOCR backup

## Backend
- FastAPI
- Pydantic
- SQLAlchemy or Supabase client
- Background job queue only when needed

## Data
- PostgreSQL / Supabase
- Object storage for clips and images
- Local filesystem for development

## Frontend
- Next.js/React
- Tailwind CSS
- Leaflet + OpenStreetMap

## Quality
- Ruff/Black
- Pytest
- TypeScript ESLint
- Playwright for dashboard tests
- Docker for reproducible services

## Selection rules
- Prefer tools the team can run and debug.
- Benchmark before changing models.
- Do not switch frameworks near a demo without a measurable reason.
- Record exact model version, weights, hardware, resolution and FPS for every result.
