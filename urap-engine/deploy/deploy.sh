#!/usr/bin/env bash
# URAP Engine — Cloud Run deploy script
# Usage: ./deploy/deploy.sh [--project PROJECT_ID] [--region REGION]
set -euo pipefail

# ── Config ────────────────────────────────────────────────────────────────────
PROJECT_ID="${GCLOUD_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${CLOUD_RUN_REGION:-us-central1}"
SERVICE_NAME="urap-engine"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# ── Parse flags ───────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --project) PROJECT_ID="$2"; shift 2 ;;
    --region)  REGION="$2";     shift 2 ;;
    *)         echo "Unknown flag: $1"; exit 1 ;;
  esac
done

if [[ -z "${PROJECT_ID}" ]]; then
  echo "ERROR: no GCP project set. Run: gcloud config set project YOUR_PROJECT_ID"
  exit 1
fi

IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "==> Project:  ${PROJECT_ID}"
echo "==> Region:   ${REGION}"
echo "==> Image:    ${IMAGE}"
echo ""

# ── Build & push ──────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENGINE_ROOT="$(dirname "${SCRIPT_DIR}")"

echo "==> Building Docker image..."
cd "${ENGINE_ROOT}"
TAG=$(git rev-parse --short HEAD 2>/dev/null || date +%Y%m%d%H%M%S)
IMAGE_TAGGED="${IMAGE}:${TAG}"

# Cloud Build inline config — avoids deprecated --dockerfile flag
gcloud builds submit \
  --config /dev/stdin \
  . << CLOUDBUILD
steps:
  - name: gcr.io/cloud-builders/docker
    args:
      - build
      - -f
      - deploy/Dockerfile
      - -t
      - ${IMAGE_TAGGED}
      - -t
      - ${IMAGE}:latest
      - .
images:
  - ${IMAGE_TAGGED}
  - ${IMAGE}:latest
CLOUDBUILD

# ── Deploy to Cloud Run ───────────────────────────────────────────────────────
echo "==> Deploying to Cloud Run..."

# Load env vars from .env if present (never bake secrets in image)
ENV_VARS=""
if [[ -f "${ENGINE_ROOT}/.env" ]]; then
  # Convert .env to comma-separated KEY=VALUE pairs, skip blanks and comments
  ENV_VARS=$(grep -v '^\s*#' "${ENGINE_ROOT}/.env" | grep -v '^\s*$' | grep '=' | \
             sed 's/[[:space:]]*$//' | tr '\n' ',' | sed 's/,$//')
fi

DEPLOY_ARGS=(
  run deploy "${SERVICE_NAME}"
  --image "${IMAGE_TAGGED}"
  --region "${REGION}"
  --platform managed
  --allow-unauthenticated
  --port 8080
  --memory 512Mi
  --cpu 1
  --min-instances 0
  --max-instances 10
  --concurrency 80
)

if [[ -n "${ENV_VARS}" ]]; then
  DEPLOY_ARGS+=(--set-env-vars "${ENV_VARS}")
fi

gcloud "${DEPLOY_ARGS[@]}"

# ── Report service URL ────────────────────────────────────────────────────────
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --region "${REGION}" \
  --format "value(status.url)")

echo ""
echo "✓ Deployed: ${SERVICE_URL}"
echo "  Health:   ${SERVICE_URL}/health"
echo "  Docs:     ${SERVICE_URL}/docs"
