#!/bin/bash
set -e

echo "🔨 Building frontend with fresh build..."
cd frontend
npm run build:fresh

echo "✅ Verifying build contains expected assets..."
if [ ! -f "../backend/static/index.html" ]; then
    echo "❌ Error: index.html not found in build!"
    exit 1
fi

if [ ! -d "../backend/static/assets" ]; then
    echo "❌ Error: assets directory not found in build!"
    exit 1
fi

CSS_FILES=$(find ../backend/static/assets -name "*.css" | wc -l)
JS_FILES=$(find ../backend/static/assets -name "*.js" | wc -l)

if [ "$CSS_FILES" -eq 0 ]; then
    echo "❌ Error: No CSS files found in build!"
    exit 1
fi

if [ "$JS_FILES" -eq 0 ]; then
    echo "❌ Error: No JS files found in build!"
    exit 1
fi

echo "✅ Build verification passed!"
echo "   - CSS files: $CSS_FILES"
echo "   - JS files: $JS_FILES"
echo "   - Build timestamp: $(date)"

echo "🔍 Checking for login styling..."
if grep -q "login-card" ../backend/static/assets/*.css; then
    echo "✅ Login styling found in CSS build"
else
    echo "❌ Warning: Login styling not found in CSS build"
fi

echo "🎉 Fresh build completed and verified!"