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
    && rm -rf /var/lib/apt/lists/* \
    && fc-cache -fv

# Cache bust argument - change value to force rebuild
ARG CACHE_BUST=v5
RUN echo "Cache bust: $CACHE_BUST"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install email-validator==2.1.0 psycopg[binary]==3.2.3 && \
    pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directories
RUN mkdir -p app/data/uploads app/data/outputs app/data/samples

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
