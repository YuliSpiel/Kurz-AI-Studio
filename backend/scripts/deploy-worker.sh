#!/bin/bash
# Manual worker deployment script
# Usage: ./scripts/deploy-worker.sh

set -e

PROJECT_ID=${PROJECT_ID:-kurz-studio}
IMAGE_TAG=${IMAGE_TAG:-latest}
ZONE=${ZONE:-us-central1-a}
VM_NAME=${VM_NAME:-kurz-worker}

echo "=== Kurz Worker Docker Deployment ==="
echo "Project: $PROJECT_ID"
echo "Image: gcr.io/$PROJECT_ID/kurz-worker:$IMAGE_TAG"
echo "VM: $VM_NAME ($ZONE)"
echo ""

# Step 1: Build Docker image locally
echo "[1/4] Building Docker image..."
cd "$(dirname "$0")/.."
docker build --no-cache -f Dockerfile.worker -t gcr.io/$PROJECT_ID/kurz-worker:$IMAGE_TAG .

# Step 2: Push to GCR
echo "[2/4] Pushing to Google Container Registry..."
docker push gcr.io/$PROJECT_ID/kurz-worker:$IMAGE_TAG

# Step 3: SSH into VM and deploy
echo "[3/4] Deploying to VM..."
gcloud compute ssh $VM_NAME --zone=$ZONE --tunnel-through-iap --command="
# Configure docker to use gcloud credentials
gcloud auth configure-docker gcr.io --quiet

# Pull latest image
docker pull gcr.io/$PROJECT_ID/kurz-worker:$IMAGE_TAG

# Stop and remove existing container
docker stop kurz-celery 2>/dev/null || true
docker rm kurz-celery 2>/dev/null || true

# Run new container
docker run -d \
  --name kurz-celery \
  --restart unless-stopped \
  -e DATABASE_URL=\"\$(curl -s -H 'Metadata-Flavor: Google' http://metadata.google.internal/computeMetadata/v1/instance/attributes/DATABASE_URL)\" \
  -e REDIS_URL=\"\$(curl -s -H 'Metadata-Flavor: Google' http://metadata.google.internal/computeMetadata/v1/instance/attributes/REDIS_URL)\" \
  -e CELERY_BROKER_URL=\"\$(curl -s -H 'Metadata-Flavor: Google' http://metadata.google.internal/computeMetadata/v1/instance/attributes/REDIS_URL)\" \
  -e CELERY_RESULT_BACKEND=\"\$(curl -s -H 'Metadata-Flavor: Google' http://metadata.google.internal/computeMetadata/v1/instance/attributes/REDIS_URL)\" \
  -e GEMINI_API_KEY=\"\$(curl -s -H 'Metadata-Flavor: Google' http://metadata.google.internal/computeMetadata/v1/instance/attributes/GEMINI_API_KEY)\" \
  -e ELEVENLABS_API_KEY=\"\$(curl -s -H 'Metadata-Flavor: Google' http://metadata.google.internal/computeMetadata/v1/instance/attributes/ELEVENLABS_API_KEY)\" \
  -e OPENAI_API_KEY=\"\$(curl -s -H 'Metadata-Flavor: Google' http://metadata.google.internal/computeMetadata/v1/instance/attributes/OPENAI_API_KEY)\" \
  -e IMAGE_PROVIDER=gemini \
  -e TTS_PROVIDER=elevenlabs \
  -e MUSIC_PROVIDER=elevenlabs \
  -e ENV=production \
  -v /home/kurz/outputs:/app/app/data/outputs \
  gcr.io/$PROJECT_ID/kurz-worker:$IMAGE_TAG

# Verify
sleep 5
docker ps | grep kurz-celery
"

# Step 4: Verify
echo "[4/4] Verifying deployment..."
gcloud compute ssh $VM_NAME --zone=$ZONE --tunnel-through-iap --command="docker logs kurz-celery --tail 20"

echo ""
echo "=== Deployment Complete ==="
