# Script to fix GCP secrets
# Run this to update your secrets with clean values

Write-Host "This script will help you update your GCP secrets with clean values" -ForegroundColor Cyan
Write-Host ""

# Get the current secret values to verify
Write-Host "Current secret versions:" -ForegroundColor Yellow
gcloud secrets versions list telegram-bot-token --limit=1
gcloud secrets versions list telegram-chat-id --limit=1
Write-Host ""

Write-Host "To fix the secrets, run these commands with your ACTUAL values:" -ForegroundColor Green
Write-Host ""
Write-Host "1. Update Telegram Bot Token:" -ForegroundColor Cyan
Write-Host '   echo -n "YOUR_ACTUAL_BOT_TOKEN" | gcloud secrets versions add telegram-bot-token --data-file=-' -ForegroundColor White
Write-Host ""
Write-Host "2. Update Telegram Chat ID:" -ForegroundColor Cyan
Write-Host '   echo -n "YOUR_ACTUAL_CHAT_ID" | gcloud secrets versions add telegram-chat-id --data-file=-' -ForegroundColor White
Write-Host ""
Write-Host "IMPORTANT: Replace YOUR_ACTUAL_BOT_TOKEN and YOUR_ACTUAL_CHAT_ID with your actual values" -ForegroundColor Red
Write-Host "Note: The 'echo -n' flag prevents adding newlines" -ForegroundColor Yellow
Write-Host ""
Write-Host "After updating secrets, trigger a new deployment:" -ForegroundColor Green
Write-Host "   git commit --allow-empty -m 'Trigger rebuild' && git push" -ForegroundColor White

