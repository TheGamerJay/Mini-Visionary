# Deployment Guide for Mini Visionary

## Production Server Deployment

The latest code includes critical fixes for profile avatar uploads and 405 errors. To deploy to production:

### 1. SSH into Production Server
```bash
ssh your-user@minivisionary.soulbridgeai.com
```

### 2. Navigate to Project Directory
```bash
cd /path/to/Mini-Visionary
# Common paths: /var/www/mini-visionary, /opt/mini-visionary, ~/mini-visionary
```

### 3. Pull Latest Code
```bash
git fetch origin
git pull origin main
```

### 4. Restart Flask Application

**If using systemd:**
```bash
sudo systemctl restart mini-visionary
sudo systemctl status mini-visionary
```

**If using supervisor:**
```bash
sudo supervisorctl restart mini-visionary
sudo supervisorctl status mini-visionary
```

**If using PM2:**
```bash
pm2 restart mini-visionary
pm2 logs mini-visionary
```

**If using Docker:**
```bash
docker-compose restart
docker-compose logs -f
```

**If running manually:**
```bash
# Find the process
ps aux | grep "python.*app.py"

# Kill it
kill <PID>

# Start it again
cd backend
python app.py
```

### 5. Verify Deployment

Test the profile upload endpoint:
```bash
curl -i -X OPTIONS https://minivisionary.soulbridgeai.com/api/library/profile
```

Should return:
- Status: 204 or 200
- Header: `Allow: GET, POST, PUT, PATCH, OPTIONS`

Test that errors return JSON:
```bash
curl -i -X DELETE https://minivisionary.soulbridgeai.com/api/library/profile
```

Should return:
- Status: 405
- Content-Type: `application/json`
- Body: `{"ok": false, "error": "METHOD_NOT_ALLOWED", "allow": [...]}`

## What's New in This Deployment

### Profile Avatar Upload Fixes
- ✅ Multipart file upload support (up to 20MB)
- ✅ Files saved to disk instead of database
- ✅ JSON error handlers (no more HTML error pages)
- ✅ `strict_slashes=False` for route flexibility
- ✅ Support for PATCH, POST, PUT methods
- ✅ Proper CORS preflight handling

### Files Changed
- `backend/app.py` - Added JSON error handlers
- `backend/app_library.py` - Updated profile endpoint
- `backend/static/profile.html` - Robust upload with method retry

## Troubleshooting

### Still getting 405 errors?
1. Verify code was pulled: `git log -1 --oneline` should show: `64cddf5 Fix 405 errors`
2. Verify Flask restarted: `sudo systemctl status mini-visionary` or check logs
3. Check if proxy (Nginx/Apache) is blocking methods - see below

### Nginx Configuration
If using Nginx, ensure it allows all methods:

```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

    # Don't restrict methods
    # Remove any: limit_except GET POST { deny all; }

    # Ensure CORS headers pass through
    proxy_hide_header Access-Control-Allow-Origin;
    add_header Access-Control-Allow-Origin $http_origin always;
    add_header Access-Control-Allow-Methods "GET, POST, PUT, PATCH, DELETE, OPTIONS" always;
    add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;

    # Handle OPTIONS preflight
    if ($request_method = OPTIONS) {
        return 204;
    }
}
```

### Apache Configuration
If using Apache, ensure mod_proxy allows methods:

```apache
<Location /api>
    ProxyPass http://127.0.0.1:8000/api
    ProxyPassReverse http://127.0.0.1:8000/api

    # Allow all methods
    <LimitExcept GET POST PUT PATCH DELETE OPTIONS>
        Require all granted
    </LimitExcept>
</Location>
```

### Check Flask Logs
```bash
# systemd
sudo journalctl -u mini-visionary -f

# supervisor
tail -f /var/log/supervisor/mini-visionary.log

# pm2
pm2 logs mini-visionary

# manual
tail -f /path/to/mini-visionary/backend/logs/app.log
```

## Quick Test After Deployment

Visit in browser:
1. https://minivisionary.soulbridgeai.com/static/profile.html
2. Try uploading an avatar
3. Should work without 405 errors
4. File should save to server disk

## Rollback (If Needed)

```bash
cd /path/to/Mini-Visionary
git log --oneline -5  # Find previous commit
git checkout <previous-commit-hash>
sudo systemctl restart mini-visionary
```

## Contact

If deployment issues persist, check:
- Server logs
- Nginx/Apache error logs
- Database connectivity
- File permissions on `backend/static/uploads/`