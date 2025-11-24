# Backend Dockerfile for Cloud Run
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (including Korean fonts for video rendering)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libfontconfig1 \
    fonts-nanum \
    fonts-noto-cjk \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && fc-cache -fv

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend/ .

# Create data directories
RUN mkdir -p app/data/uploads app/data/outputs app/data/samples

# Cloud Run uses PORT environment variable
ENV PORT=8080
EXPOSE 8080

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
