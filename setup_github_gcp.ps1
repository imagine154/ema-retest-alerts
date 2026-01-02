# Quick GitHub to GCP Setup Script

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectId,

    [Parameter(Mandatory=$false)]
    [string]$Region = "asia-south1"
)

Write-Host "=== GitHub to GCP Setup ===" -ForegroundColor Cyan
Write-Host "Project: $ProjectId" -ForegroundColor Yellow
Write-Host "Region: $Region`n" -ForegroundColor Yellow

# Set project
Write-Host "Setting GCP project..." -ForegroundColor Yellow
gcloud config set project $ProjectId

# Enable required APIs
Write-Host "`nEnabling required APIs..." -ForegroundColor Yellow
gcloud services enable `
  cloudbuild.googleapis.com `
  run.googleapis.com `
  cloudscheduler.googleapis.com `
  secretmanager.googleapis.com `
  sourcerepo.googleapis.com

# Get project number
$projectNumber = gcloud projects describe $ProjectId --format="value(projectNumber)"
Write-Host "Project Number: $projectNumber" -ForegroundColor Green

# Create secrets if they don't exist
Write-Host "`nSetting up secrets..." -ForegroundColor Yellow
$botTokenExists = gcloud secrets list --filter="name:telegram-bot-token" --format="value(name)"
if (-not $botTokenExists) {
    Write-Host "Enter your Telegram Bot Token:" -ForegroundColor Cyan
    $botToken = Read-Host -MaskInput
    echo -n $botToken | gcloud secrets create telegram-bot-token --data-file=-
    Write-Host "Bot token secret created" -ForegroundColor Green
}

$chatIdExists = gcloud secrets list --filter="name:telegram-chat-id" --format="value(name)"
if (-not $chatIdExists) {
    Write-Host "Enter your Telegram Chat ID:" -ForegroundColor Cyan
    $chatId = Read-Host
    echo -n $chatId | gcloud secrets create telegram-chat-id --data-file=-
    Write-Host "Chat ID secret created" -ForegroundColor Green
}

# Grant Cloud Run access to secrets
Write-Host "`nGranting Cloud Run access to secrets..." -ForegroundColor Yellow
gcloud secrets add-iam-policy-binding telegram-bot-token `
  --member="serviceAccount:${projectNumber}-compute@developer.gserviceaccount.com" `
  --role="roles/secretmanager.secretAccessor" 2>$null

gcloud secrets add-iam-policy-binding telegram-chat-id `
  --member="serviceAccount:${projectNumber}-compute@developer.gserviceaccount.com" `
  --role="roles/secretmanager.secretAccessor" 2>$null

# Grant Cloud Build permissions
Write-Host "`nGranting Cloud Build permissions..." -ForegroundColor Yellow
gcloud projects add-iam-policy-binding $ProjectId `
  --member="serviceAccount:${projectNumber}@cloudbuild.gserviceaccount.com" `
  --role="roles/run.admin" 2>$null

gcloud projects add-iam-policy-binding $ProjectId `
  --member="serviceAccount:${projectNumber}@cloudbuild.gserviceaccount.com" `
  --role="roles/iam.serviceAccountUser" 2>$null

Write-Host "`n=== Setup Complete! ===" -ForegroundColor Green
Write-Host "`nNext Steps:" -ForegroundColor Cyan
Write-Host "1. Push your code to GitHub" -ForegroundColor White
Write-Host "   git init" -ForegroundColor Gray
Write-Host "   git add ." -ForegroundColor Gray
Write-Host "   git commit -m 'Initial commit'" -ForegroundColor Gray
Write-Host "   git remote add origin https://github.com/YOUR_USERNAME/ema-retest-alerts.git" -ForegroundColor Gray
Write-Host "   git push -u origin main`n" -ForegroundColor Gray

Write-Host "2. Connect GitHub to Cloud Build:" -ForegroundColor White
Write-Host "   - Go to: https://console.cloud.google.com/cloud-build/triggers?project=$ProjectId" -ForegroundColor Gray
Write-Host "   - Click 'Connect Repository'" -ForegroundColor Gray
Write-Host "   - Select 'GitHub (Cloud Build GitHub App)'" -ForegroundColor Gray
Write-Host "   - Authenticate and select your repository" -ForegroundColor Gray
Write-Host "   - Create trigger with configuration: cloudbuild.yaml`n" -ForegroundColor Gray

Write-Host "3. After first deployment, set up Cloud Scheduler:" -ForegroundColor White
Write-Host "   See GITHUB_DEPLOYMENT.md for detailed instructions`n" -ForegroundColor Gray

Write-Host "For detailed guide, see: GITHUB_DEPLOYMENT.md" -ForegroundColor Cyan

