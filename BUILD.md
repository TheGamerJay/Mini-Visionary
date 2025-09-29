# Build Process

This document explains how to ensure the frontend is properly built and deployed.

## Quick Commands

### For Development
```bash
cd frontend
npm run dev
```

### For Production Build
```bash
cd frontend
npm run build:fresh    # Clean build with cache clearing
# OR
npm run build         # Standard build
```

### Automated Build with Verification
```bash
bash scripts/build-and-verify.sh
```

## How Deployment Works

1. **Local Development**: Changes are made to `frontend/src/` files
2. **Build Process**: Frontend is built into `backend/static/` folder
3. **Railway Deployment**: When you push to GitHub, Railway:
   - Runs the Dockerfile
   - Builds the frontend with `npm run build`
   - Copies built files to production
   - Serves via Flask backend

## Preventing Build Issues

The build process has been improved to prevent stale builds:

### Updated Scripts
- `npm run build` - Now builds directly to `../backend/static`
- `npm run build:fresh` - Clears old files first, then builds fresh

### Updated Dockerfile
- Clears npm cache with `npm ci --no-cache`
- Removes old dist files before building
- Ensures clean copy to production static folder

### Build Verification
- `scripts/build-and-verify.sh` validates the build
- Checks for required files (index.html, CSS, JS)
- Verifies login styling is included
- Shows build timestamp and file counts

## Troubleshooting

### If production site shows old design:
1. Run `bash scripts/build-and-verify.sh`
2. Commit and push the updated build files
3. Wait 2-3 minutes for Railway deployment
4. Clear browser cache (Ctrl+F5)

### Manual build process:
```bash
cd frontend
npm run build:fresh
cd ..
git add backend/static/
git commit -m "Update frontend build"
git push
```

## File Structure
```
Mini-Visionary-main/
├── frontend/           # React source code
│   ├── src/           # Your React components
│   └── package.json   # Updated with new build scripts
├── backend/
│   └── static/        # Built frontend files (served in production)
├── scripts/
│   └── build-and-verify.sh  # Build validation script
└── Dockerfile         # Updated with fresh build process
```