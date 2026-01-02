# GCP Deployment Script for Windows PowerShell

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectId,

    [Parameter(Mandatory=$false)]
    [string]$Region = "asia-south1",

    [Parameter(Mandatory=$false)]
    [string]$ServiceName = "ema-retest-alerts"
)

Write-Host "=== EMA Retest Alerts - GCP Deployment ===" -ForegroundColor Cyan
Write-Host "Project: $ProjectId" -ForegroundColor Yellow
Write-Host "Region: $Region" -ForegroundColor Yellow
Write-Host "Service: $ServiceName`n" -ForegroundColor Yellow

# Set project
Write-Host "Setting GCP project..." -ForegroundColor Yellow
gcloud config set project $ProjectId

# Enable required APIs
Write-Host "`nEnabling required GCP APIs..." -ForegroundColor Yellow
gcloud services enable `
  cloudbuild.googleapis.com `
  run.googleapis.com `
  cloudscheduler.googleapis.com `
  secretmanager.googleapis.com

# Create secrets (if they don't exist)
Write-Host "`nChecking secrets..." -ForegroundColor Yellow
$botTokenExists = gcloud secrets list --filter="name:telegram-bot-token" --format="value(name)"
if (-not $botTokenExists) {
    Write-Host "Creating telegram-bot-token secret..." -ForegroundColor Yellow
    Write-Host "Enter your Telegram Bot Token:"
    $botToken = Read-Host -AsSecureString
    $botTokenPlain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($botToken))
    echo -n $botTokenPlain | gcloud secrets create telegram-bot-token --data-file=-
}

$chatIdExists = gcloud secrets list --filter="name:telegram-chat-id" --format="value(name)"
if (-not $chatIdExists) {
    Write-Host "Creating telegram-chat-id secret..." -ForegroundColor Yellow
    Write-Host "Enter your Telegram Chat ID:"
    $chatId = Read-Host
    echo -n $chatId | gcloud secrets create telegram-chat-id --data-file=-
}

# Grant access to secrets
Write-Host "`nGranting secret access to Compute service account..." -ForegroundColor Yellow
$projectNumber = gcloud projects describe $ProjectId --format="value(projectNumber)"
$serviceAccount = "$projectNumber-compute@developer.gserviceaccount.com"

gcloud secrets add-iam-policy-binding telegram-bot-token `
  --member="serviceAccount:$serviceAccount" `
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding telegram-chat-id `
  --member="serviceAccount:$serviceAccount" `
  --role="roles/secretmanager.secretAccessor"

# Build container image
Write-Host "`nBuilding container image..." -ForegroundColor Yellow
gcloud builds submit --config cloudbuild.yaml

if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1
}

# Deploy to Cloud Run
Write-Host "`nDeploying to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy $ServiceName `
  --image gcr.io/$ProjectId/${ServiceName}:latest `
  --platform managed `
  --region $Region `
  --no-allow-unauthenticated `
  --memory 512Mi `
  --timeout 300 `
  --max-instances 1 `
  --set-secrets "TELEGRAM_BOT_TOKEN=telegram-bot-token:latest,TELEGRAM_CHAT_ID=telegram-chat-id:latest"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Deployment failed!" -ForegroundColor Red
    exit 1
}

# Get service URL
$serviceUrl = gcloud run services describe $ServiceName `
  --platform managed `
  --region $Region `
  --format "value(status.url)"

Write-Host "`nService deployed successfully!" -ForegroundColor Green
Write-Host "Service URL: $serviceUrl" -ForegroundColor Cyan

# Create service account for scheduler
Write-Host "`nCreating service account for Cloud Scheduler..." -ForegroundColor Yellow
$schedulerSA = "${ServiceName}-scheduler@${ProjectId}.iam.gserviceaccount.com"

gcloud iam service-accounts create "${ServiceName}-scheduler" `
  --display-name "$ServiceName Scheduler" 2>$null

# Grant invoker permission
gcloud run services add-iam-policy-binding $ServiceName `
  --member="serviceAccount:$schedulerSA" `
  --role="roles/run.invoker" `
  --region $Region

# Create Cloud Scheduler job
Write-Host "`nCreating Cloud Scheduler job (runs every 15 min during market hours)..." -ForegroundColor Yellow
gcloud scheduler jobs create http "${ServiceName}-job" `
  --location $Region `
  --schedule "*/15 9-15 * * 1-5" `
  --time-zone "Asia/Kolkata" `
  --uri $serviceUrl `
  --http-method GET `
  --oidc-service-account-email $schedulerSA `
  --attempt-deadline 300s 2>$null

if ($LASTEXITCODE -eq 0) {
    Write-Host "Scheduler job created successfully!" -ForegroundColor Green
} else {
    Write-Host "Scheduler job may already exist or failed to create." -ForegroundColor Yellow
}

# Summary
Write-Host "`n=== Deployment Complete ===" -ForegroundColor Cyan
Write-Host "Service URL: $serviceUrl" -ForegroundColor Yellow
Write-Host "Region: $Region" -ForegroundColor Yellow
Write-Host "Schedule: Every 15 minutes (9:00-15:00 IST, Mon-Fri)" -ForegroundColor Yellow
Write-Host "`nTo view logs:" -ForegroundColor Cyan
Write-Host "  gcloud run logs read $ServiceName --region $Region --limit 50" -ForegroundColor White
Write-Host "`nTo manually trigger:" -ForegroundColor Cyan
Write-Host "  gcloud scheduler jobs run ${ServiceName}-job --location $Region" -ForegroundColor White
Write-Host "`nTo view scheduler jobs:" -ForegroundColor Cyan
Write-Host "  gcloud scheduler jobs list --location $Region" -ForegroundColor White

