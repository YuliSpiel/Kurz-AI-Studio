#!/bin/bash
# Kurz AI Studio - Cloud Run Deployment Script
# Usage: ./deploy.sh [PROJECT_ID]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
PROJECT_ID="${1:-$(gcloud config get-value project)}"
REGION="asia-northeast3"  # Seoul
BACKEND_SERVICE="kurz-backend"
FRONTEND_SERVICE="kurz-frontend"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Kurz AI Studio - Cloud Run Deploy${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Project: ${YELLOW}$PROJECT_ID${NC}"
echo -e "Region: ${YELLOW}$REGION${NC}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI not installed${NC}"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check authentication
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1 > /dev/null; then
    echo -e "${RED}Error: Not authenticated with gcloud${NC}"
    echo "Run: gcloud auth login"
    exit 1
fi

# Enable required APIs
echo -e "${YELLOW}Enabling required APIs...${NC}"
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    secretmanager.googleapis.com \
    --project=$PROJECT_ID

# Check if secrets exist
echo -e "${YELLOW}Checking secrets...${NC}"
REQUIRED_SECRETS=(
    "JWT_SECRET"
    "GEMINI_API_KEY"
    "ELEVENLABS_API_KEY"
    "GOOGLE_CLIENT_ID"
    "GOOGLE_CLIENT_SECRET"
)

MISSING_SECRETS=()
for secret in "${REQUIRED_SECRETS[@]}"; do
    if ! gcloud secrets describe $secret --project=$PROJECT_ID &> /dev/null; then
        MISSING_SECRETS+=($secret)
    fi
done

if [ ${#MISSING_SECRETS[@]} -ne 0 ]; then
    echo -e "${RED}Missing secrets:${NC}"
    for secret in "${MISSING_SECRETS[@]}"; do
        echo "  - $secret"
    done
    echo ""
    echo "Create secrets with:"
    echo "  echo -n 'value' | gcloud secrets create SECRET_NAME --data-file=- --project=$PROJECT_ID"
    echo ""
    echo "Or run: ./setup-secrets.sh"
    exit 1
fi

# Build and deploy using Cloud Build
echo -e "${YELLOW}Starting Cloud Build...${NC}"
cd "$(dirname "$0")/../.."

gcloud builds submit \
    --config=deploy/cloudrun/cloudbuild.yaml \
    --project=$PROJECT_ID \
    --substitutions=_REGION=$REGION

# Get service URLs
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE --region=$REGION --project=$PROJECT_ID --format='value(status.url)')
FRONTEND_URL=$(gcloud run services describe $FRONTEND_SERVICE --region=$REGION --project=$PROJECT_ID --format='value(status.url)')

echo -e "Backend URL:  ${GREEN}$BACKEND_URL${NC}"
echo -e "Frontend URL: ${GREEN}$FRONTEND_URL${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Update Google OAuth redirect URI:"
echo "   $BACKEND_URL/api/auth/google/callback"
echo ""
echo "2. (Optional) Set up custom domain:"
echo "   gcloud run domain-mappings create --service=$FRONTEND_SERVICE --domain=yourdomain.com --region=$REGION"
