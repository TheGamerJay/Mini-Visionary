# --- Frontend build ---
FROM node:20-alpine AS frontend
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build -- --outDir=dist

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
COPY --from=frontend /frontend/dist /app/static

# Railway target port is 8080
EXPOSE 8080
CMD ["gunicorn", "wsgi_runner:app", "-b", "0.0.0.0:8080", "--timeout", "120"]
