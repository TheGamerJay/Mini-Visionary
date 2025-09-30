# Kill all Python Flask processes
Write-Host "Stopping all Python processes..." -ForegroundColor Yellow
Get-Process | Where-Object {$_.ProcessName -eq 'python' -or $_.ProcessName -eq 'pythonw'} | Stop-Process -Force
Start-Sleep -Seconds 2

Write-Host "All Python processes stopped." -ForegroundColor Green
Write-Host ""
Write-Host "Now you can start a fresh Flask server with:" -ForegroundColor Cyan
Write-Host "cd backend && python app.py" -ForegroundColor White
