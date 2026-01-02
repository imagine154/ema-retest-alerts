# Docker Test Script for Windows PowerShell

Write-Host "=== EMA Retest Alerts - Docker Test ===" -ForegroundColor Cyan

# Build Docker image
Write-Host "`nBuilding Docker image..." -ForegroundColor Yellow
docker build -t ema-retest-alerts:test .

if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "Docker build successful!" -ForegroundColor Green

# Run Docker container
Write-Host "`nRunning Docker container..." -ForegroundColor Yellow
docker run --rm `
  -e TELEGRAM_BOT_TOKEN="8163995879:AAHEnG-mAxont26F1mwUfOHGv-NJ1iZWkao" `
  -e TELEGRAM_CHAT_ID="-1002343316074" `
  ema-retest-alerts:test

Write-Host "`n=== Docker Test Complete ===" -ForegroundColor Cyan

