# --- Frontend build ---
FROM node:20-alpine AS frontend
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# --- Backend runtime ---
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# install python deps
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy backend code
COPY backend/ .

# copy built frontend into Flask static
COPY --from=frontend /backend/static /app/static

# Railway target port is 8080
EXPOSE 8080
CMD ["gunicorn", "serve_spa:app", "-b", "0.0.0.0:8080", "--timeout", "120"]
