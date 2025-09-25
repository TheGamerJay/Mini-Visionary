#!/usr/bin/env bash
# =========================================
# scripts/embed_frontend.sh  (optional local helper)
# Usage: bash scripts/embed_frontend.sh
# Builds the frontend and copies it into backend/ for local Flask runs.
# =========================================
set -euo pipefail

echo "==> Building frontend…"
npm --prefix frontend ci
npm --prefix frontend run build

echo "==> Embedding into backend/static + backend/templates…"
rm -rf backend/static backend/templates
mkdir -p backend/static backend/templates
cp -r frontend/dist/assets backend/static/
cp -r frontend/dist/* backend/static/ || true
mv backend/static/index.html backend/templates/index.html

echo "==> Done. You can now run:  (cd backend && python app.py)"