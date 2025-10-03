# --- Frontend build ---
FROM node:20-alpine AS frontend
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
# Clean any existing builds and create fresh build to dist folder
RUN rm -rf dist && npm run build:docker

# --- Backend runtime ---
FROM python:3.11-slim AS stage-1

# (1) sensible env defaults for reliable installs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=120

# (2) system deps + certs; keep image lean
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates build-essential gcc \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# (3) upgrade pip tooling first (fewer bugs, faster resolver)
RUN python -m pip install --upgrade pip setuptools wheel

# (4) copy only requirements to leverage layer cache
COPY backend/requirements.txt .

# (5) robust dependency install with retries
RUN pip install -r requirements.txt --retries 10 --progress-bar off

# copy backend code
COPY backend/ .

# copy built frontend into Flask static (clean copy)
RUN rm -rf /app/static/*
COPY --from=frontend /frontend/dist /app/static

# NOW overlay backend/static again so auth.html (and any hand-made files) survive
COPY backend/static/ /app/static/

# Railway target port is 8080
EXPOSE 8080
# Cache bust: 2025-09-30-04:10

# Healthcheck: use JSON endpoint for detailed diagnostics
HEALTHCHECK --interval=30s --timeout=5s --retries=5 CMD \
  curl -fsS http://localhost:8080/healthz | grep -q '"ok": true'

CMD ["gunicorn","serve_spa:app","--workers","2","--bind","0.0.0.0:8080","--log-level","info"]
