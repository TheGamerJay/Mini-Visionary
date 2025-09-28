#!/bin/bash

# start.sh - Mini-Visionary Railpack startup script
set -e

echo "Starting Mini-Visionary application..."

# Navigate to the application directory if needed
cd /app 2>/dev/null || cd "$(dirname "$0")" || true

# Install Python dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing Python dependencies..."
    pip install --no-cache-dir -r requirements.txt
elif [ -f "Mini-Visionary-main/requirements.txt" ]; then
    echo "Installing Python dependencies from Mini-Visionary-main..."
    pip install --no-cache-dir -r Mini-Visionary-main/requirements.txt
fi

# Navigate to the actual app directory
if [ -d "Mini-Visionary-main" ]; then
    cd Mini-Visionary-main
fi

# Build frontend if not already built
if [ -d "frontend" ] && [ ! -d "backend/static/assets" ]; then
    echo "Building frontend..."
    cd frontend
    if [ -f "package.json" ]; then
        npm install
        npm run build
        # Copy build to backend static
        mkdir -p ../backend/static
        cp -r dist/* ../backend/static/ 2>/dev/null || true
    fi
    cd ..
fi

# Initialize database
echo "Initializing database..."
cd backend
python -c "from models import init_db; init_db()" 2>/dev/null || echo "Database initialization skipped"

# Start the application with gunicorn
echo "Starting Flask application with gunicorn..."
exec gunicorn -b 0.0.0.0:${PORT:-8080} --timeout 60 --keep-alive 2 serve_spa:app