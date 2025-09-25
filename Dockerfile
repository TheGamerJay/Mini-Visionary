# =========================================
# Dockerfile (single service: React + Flask)
# =========================================

# Stage 1: Frontend build (Vite)
FROM node:20-alpine AS fe
WORKDIR /fe

# Install frontend deps first for caching
COPY frontend/package*.json frontend/vite.config.* ./
RUN npm ci || npm i

# Copy source and build
COPY frontend/ .
RUN npm run build  # outputs /fe/dist

# Stage 2: Backend runtime (Flask + Gunicorn)
FROM python:3.11-slim AS be
WORKDIR /app

# Build args for version endpoint - prefer Railway, then GitHub, else 'dev'
ARG RAILWAY_GIT_COMMIT_SHA
ARG GITHUB_SHA
ENV GIT_SHA=${RAILWAY_GIT_COMMIT_SHA:-${GITHUB_SHA:-dev}}
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps (psycopg2, Pillow, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# Install Python deps first for better caching
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
 && pip install --no-cache-dir gunicorn==21.2.0 gevent

# Copy backend code
COPY backend/ /app/

# Embed built frontend into Flask static/
RUN rm -rf /app/static && mkdir -p /app/static
COPY --from=fe /fe/dist /app/static/

# Run on 8080 (Railway is set to 8080)
EXPOSE 8080
CMD ["sh", "-c", "gunicorn -w 2 -k gevent -b 0.0.0.0:8080 app:app"]