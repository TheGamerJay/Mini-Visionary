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

# Railway target port is 8080
EXPOSE 8080
CMD ["gunicorn","-b","0.0.0.0:8080","--chdir","backend","serve_spa:app"]
