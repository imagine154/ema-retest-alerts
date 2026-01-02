# Local Testing Script for Windows PowerShell
Write-Host "`n=== Test Complete ===" -ForegroundColor Cyan

python chartink_ema_alerts.py
Write-Host "`nRunning EMA Retest Alerts..." -ForegroundColor Green
# Run the script

$env:TELEGRAM_CHAT_ID = "-1002343316074"
$env:TELEGRAM_BOT_TOKEN = "8163995879:AAHEnG-mAxont26F1mwUfOHGv-NJ1iZWkao"
Write-Host "Setting environment variables..." -ForegroundColor Yellow
# Set environment variables (you can modify these)

pip install -r requirements.txt
Write-Host "Installing dependencies..." -ForegroundColor Yellow
# Install dependencies

& .\.venv\Scripts\Activate.ps1
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
# Activate virtual environment

}
    python -m venv .venv
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path ".venv")) {
# Check if virtual environment exists

Write-Host "=== EMA Retest Alerts - Local Test ===" -ForegroundColor Cyan


