# --- Frontend build ---
FROM node:20-alpine AS frontend
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci --no-cache
COPY frontend/ .
# Clean any existing builds and create fresh build to dist folder
RUN rm -rf dist && npm run build:docker

# --- Backend runtime ---
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# install python deps
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy backend code
COPY backend/ .

# copy built frontend into Flask static (clean copy)
RUN rm -rf /app/backend/static/*
COPY --from=frontend /frontend/dist /app/backend/static

# NOW overlay backend/static again so auth.html (and any hand-made files) survive
COPY backend/static/ /app/backend/static/

# Ensure curl is installed for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Railway target port is 8080
EXPOSE 8080

# Healthcheck: verify auth pages are NOT the SPA and return 200
HEALTHCHECK --interval=30s --timeout=5s --retries=5 CMD \
  bash -lc '\
  set -e ; \
  curl -fsS http://localhost:8080/auth.html | grep -qi "Mini Visionary — You Envision it, We Generate It" && \
  curl -fsS http://localhost:8080/terms.html | grep -qi "Mini Visionary — Terms of Service" && \
  curl -fsS http://localhost:8080/privacy.html | grep -qi "Mini Visionary — Privacy Policy" \
  '

CMD ["gunicorn","-b","0.0.0.0:8080","--chdir","backend","serve_spa:app"]
