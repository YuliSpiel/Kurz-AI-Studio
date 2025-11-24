#!/bin/bash
# Kurz AI Studio - Secret Manager Setup
# Usage: ./setup-secrets.sh [PROJECT_ID]

set -e

PROJECT_ID="${1:-$(gcloud config get-value project)}"

echo "========================================="
echo "  Kurz AI Studio - Secret Setup"
echo "========================================="
echo ""
echo "Project: $PROJECT_ID"
echo ""

# Function to create or update secret
create_secret() {
    local name=$1
    local prompt=$2

    echo -n "$prompt: "
    read -s value
    echo ""

    if gcloud secrets describe $name --project=$PROJECT_ID &> /dev/null; then
        echo "$value" | gcloud secrets versions add $name --data-file=- --project=$PROJECT_ID
        echo "  Updated: $name"
    else
        echo "$value" | gcloud secrets create $name --data-file=- --project=$PROJECT_ID
        echo "  Created: $name"
    fi
}

# Generate JWT secret automatically
echo "Generating JWT_SECRET..."
JWT_SECRET=$(openssl rand -hex 32)
echo "$JWT_SECRET" | gcloud secrets create JWT_SECRET --data-file=- --project=$PROJECT_ID 2>/dev/null || \
    echo "$JWT_SECRET" | gcloud secrets versions add JWT_SECRET --data-file=- --project=$PROJECT_ID
echo "  Done: JWT_SECRET (auto-generated)"
echo ""

# Prompt for API keys
create_secret "GEMINI_API_KEY" "Enter GEMINI_API_KEY"
create_secret "ELEVENLABS_API_KEY" "Enter ELEVENLABS_API_KEY"
create_secret "GOOGLE_CLIENT_ID" "Enter GOOGLE_CLIENT_ID"
create_secret "GOOGLE_CLIENT_SECRET" "Enter GOOGLE_CLIENT_SECRET"

echo ""
echo "========================================="
echo "  Secrets setup complete!"
echo "========================================="
echo ""
echo "View secrets: gcloud secrets list --project=$PROJECT_ID"
