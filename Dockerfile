# Dockerfile for GVP-Guard FastAPI backend
# Multi-stage: build deps, then runtime image

FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies for uvloop (optional, for performance)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim AS runtime

WORKDIR /app

# Create non-root user for security
RUN groupadd -r gvpguard && useradd -r -g gvpguard -s /sbin/nologin gvpguard

# Install runtime dependencies (libglib for OpenCV)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY backend/ ./backend/
COPY index.html ./
COPY assets/ ./assets/

# Create data directory (SQLite + evidence storage)
RUN mkdir -p /app/backend/data /app/backend/data/evidence && \
    chown -R gvpguard:gvpguard /app

# Switch to non-root user
USER gvpguard

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    GVP_SECRET_KEY_FILE=/run/secrets/gvp_secret_key \
    PORT=8000

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

# Run the API server
CMD ["python3", "-m", "uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
