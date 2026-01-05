# Script to retrieve secret values from GCP Secret Manager

Write-Host "Retrieving secrets from GCP Secret Manager..." -ForegroundColor Cyan
Write-Host ""

Write-Host "=== Telegram Bot Token ===" -ForegroundColor Yellow
gcloud secrets versions access latest --secret="telegram-bot-token"
Write-Host ""

Write-Host "=== Telegram Chat ID ===" -ForegroundColor Yellow
gcloud secrets versions access latest --secret="telegram-chat-id"
Write-Host ""

Write-Host "Note: If the values look wrong (have quotes, newlines, etc.), you need to update them" -ForegroundColor Red

