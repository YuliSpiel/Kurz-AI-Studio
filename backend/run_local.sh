#!/bin/bash

# Local development startup script

echo "Starting AutoShorts Backend..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env not found, copying from .env.example"
    cp .env.example .env
    echo "Please edit .env with your API keys before running!"
    exit 1
fi

# Start Redis if not running
if ! docker ps | grep -q redis; then
    echo "Starting Redis..."
    docker-compose up -d redis
fi

# Wait for Redis
echo "Waiting for Redis..."
sleep 2

# Start Celery worker in background
echo "Starting Celery worker..."
celery -A app.celery_app worker --loglevel=info --pool=solo &
CELERY_PID=$!

# Start FastAPI
echo "Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# Cleanup on exit
trap "kill $CELERY_PID; docker-compose down" EXIT
