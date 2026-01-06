# Script to update GCP Cloud Run environment variables
# Run this in Google Cloud Shell or with gcloud CLI installed

# Get the values from .env
$botToken = "8163995879:AAHEnG-mAxont26F1mwUfOHGv-NJ1iZWkao"
$chatId = "-1002343316074"

Write-Host "Step 1: Getting current service description..."
gcloud run services describe ema-retest-alerts --region=asia-south1 --format=yaml | Out-File temp-service.yaml

Write-Host "`nStep 2: Updating service with plain environment variables (removing secrets)..."
gcloud run services replace temp-service.yaml

Write-Host "`nStep 3: Setting environment variables as plain text..."
gcloud run services update ema-retest-alerts `
  --region=asia-south1 `
  --set-env-vars="TELEGRAM_BOT_TOKEN=$botToken,TELEGRAM_CHAT_ID=$chatId" `
  --clear-secrets

Write-Host "`n✅ Environment variables updated successfully!"
Write-Host "Bot Token: $botToken"
Write-Host "Chat ID: $chatId"

# Clean up temp file
Remove-Item temp-service.yaml -ErrorAction SilentlyContinue

