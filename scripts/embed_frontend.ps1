# =========================================
# scripts/embed_frontend.ps1  (optional local helper for Windows PowerShell)
# Usage: pwsh scripts/embed_frontend.ps1
# =========================================
Write-Host "==> Building frontend…" -ForegroundColor Cyan
npm --prefix frontend ci
npm --prefix frontend run build

Write-Host "==> Embedding into backend/static + backend/templates…" -ForegroundColor Cyan
Remove-Item backend\static, backend\templates -Recurse -Force -ErrorAction SilentlyContinue
New-Item backend\static -ItemType Directory | Out-Null
New-Item backend\templates -ItemType Directory | Out-Null
Copy-Item frontend\dist\assets -Destination backend\static -Recurse
Copy-Item frontend\dist\* -Destination backend\static -Recurse
Move-Item backend\static\index.html backend\templates\index.html -Force

Write-Host "==> Done. Run:  cd backend; python app.py" -ForegroundColor Green