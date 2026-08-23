#!/usr/bin/env bash
set -euo pipefail

: "${GOOGLE_CLOUD_PROJECT:?Set GOOGLE_CLOUD_PROJECT to the target GCP project id}"
RUN_REGION="${CLOUD_RUN_REGION:-me-central1}"
MODEL_LOCATION="${GOOGLE_CLOUD_LOCATION:-global}"
SERVICE="${RECOVERY_TASKMASTER_SERVICE:-recovery-taskmaster}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${APP_DIR}"

gcloud config set project "${GOOGLE_CLOUD_PROJECT}"
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com aiplatform.googleapis.com

gcloud run deploy "${SERVICE}" \
  --source . \
  --region "${RUN_REGION}" \
  --allow-unauthenticated \
  --set-env-vars "GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT},GOOGLE_CLOUD_LOCATION=${MODEL_LOCATION},RECOVERY_TASKMASTER_ROOT=/tmp/recovery-taskmaster"

gcloud run services describe "${SERVICE}" \
  --region "${RUN_REGION}" \
  --format='value(status.url)'
