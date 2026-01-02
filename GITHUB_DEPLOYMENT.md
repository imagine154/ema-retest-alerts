# GitHub to GCP Deployment Guide
**You still need the Dockerfile** (in your repo) because Cloud Build uses it to build the image, but you don't need Docker installed on your machine.

5. ✅ No Docker installation needed locally
4. ✅ Every push automatically builds and deploys
3. ✅ Set up secrets in GCP (one-time)
2. ✅ Connect GitHub to Cloud Build (one-time)
1. ✅ Push code to GitHub

**Yes, you can use GitHub for GCP deployment!**

## Summary

---

- **Total**: ~$0.35/month (if within free tier)
- **Cloud Run**: ~$0.30/month (same as before)
- **Container Registry**: ~$0.026/GB/month
- **Cloud Build**: First 120 build-minutes/day FREE
### With GitHub Integration:

## Cost Estimate

---

- Check GitHub repository webhook settings
- Verify repository connection in Cloud Build settings
- Check Cloud Build > Triggers > History
### GitHub webhook not triggering

```
gcloud builds log $(gcloud builds list --limit=1 --format="value(id)")
gcloud builds list --limit=1 --format="value(id)"
```bash
Check Cloud Build logs:
### Deployment fails

```
  --role="roles/run.admin"
  --member="serviceAccount:PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
```bash
Grant Cloud Build more permissions:
### Build fails with permission error

## Troubleshooting

---

```
gcloud run logs read ema-retest-alerts --region asia-south1 --limit 50
```bash
### View application logs:

```
gcloud run services describe ema-retest-alerts --region asia-south1
```bash
### Check Cloud Run service:

```
gcloud builds log BUILD_ID
```bash
### View build logs:

```
gcloud builds list --limit=5
```bash
### Check build status:

## Monitoring Your Deployment

---

✅ `gcloud` CLI (only for initial setup)
✅ Text editor (VS Code, etc.)
✅ Git

## What You DO Need Locally

---

❌ Manual `gcloud run deploy`
❌ Manual `gcloud builds submit`
❌ Docker CLI
❌ Docker Desktop

## What You DON'T Need Locally

---

✅ **Build Logs** - See build history in GCP Console
✅ **Collaboration** - Team can contribute
✅ **Rollback Easy** - Deploy any commit
✅ **Version Control** - Track all changes
✅ **Automated CI/CD** - Push to deploy
✅ **No Local Docker Required** - Cloud Build handles everything

## Advantages of GitHub Integration

---

```
└─────────────┘
│ Cloud Run   │
│     to      │
│   Deploy    │
┌─────────────┐
       ▼
       │
└──────┬──────┘
│    GCR      │
│     to      │
│    Push     │
┌─────────────┐
       ▼
       │
└──────┬──────┘
│   Image     │
│  Docker     │
│   Build     │
┌─────────────┐
       ▼
       │
└──────┬──────┘
│  Triggered  │
│ Cloud Build │
┌─────────────┐
       ▼ (Webhook triggers Cloud Build)
       │
└──────┬──────┘
│  GitHub     │
│ Push to     │
┌─────────────┐
       ▼
       │
└──────┬──────┘
│   Commit    │
│    Git      │
┌─────────────┐
       ▼
       │
└──────┬──────┘
│  Changes    │
│   Code      │
┌─────────────┐
```
### Standard Workflow

## Deployment Workflow

---

```
gcloud scheduler jobs create http ema-alerts-job --location asia-south1 --schedule "*/15 9-15 * * 1-5" --time-zone "Asia/Kolkata" --uri "${SERVICE_URL}" --http-method GET --oidc-service-account-email "ema-alerts-scheduler@YOUR_PROJECT_ID.iam.gserviceaccount.com" --attempt-deadline 300s
# Create scheduler job

gcloud run services add-iam-policy-binding ema-retest-alerts --member="serviceAccount:ema-alerts-scheduler@YOUR_PROJECT_ID.iam.gserviceaccount.com" --role="roles/run.invoker" --region asia-south1
# Grant invoker permission

gcloud iam service-accounts create ema-alerts-scheduler --display-name "EMA Alerts Scheduler"
# Create service account for scheduler

SERVICE_URL=$(gcloud run services describe ema-retest-alerts --region asia-south1 --format="value(status.url)")
# Get the service URL
```bash

After first deployment, set up the scheduler:

## Step 6: Set up Cloud Scheduler (One-Time)

---

```
gcloud builds triggers run ema-alerts-build --branch=main
```bash
Or via CLI:

4. Click "Run Trigger"
3. Select branch/tag
2. Click "Run" on your trigger
1. Go to Cloud Build > Triggers
You can also trigger manually from GCP Console:
### Manual Trigger

5. Update the running service
4. Deploy to Cloud Run
3. Push to Container Registry
2. Build Docker image using your Dockerfile
1. Clone your repo
Cloud Build will:

```
git push origin main
git commit -m "Update configuration"
git add .
```powershell

Just push to GitHub and Cloud Build will automatically build and deploy:
### Automatic Deployment (on push to main)

## Step 5: Trigger Deployment

---

```
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" --role="roles/iam.serviceAccountUser"
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" --role="roles/run.admin"
# Grant Cloud Build permission to deploy to Cloud Run

gcloud secrets add-iam-policy-binding telegram-chat-id --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"
gcloud secrets add-iam-policy-binding telegram-bot-token --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"
$PROJECT_NUMBER = gcloud projects describe YOUR_PROJECT_ID --format="value(projectNumber)"
# Grant Cloud Run access to secrets

echo -n "YOUR_CHAT_ID" | gcloud secrets create telegram-chat-id --data-file=-
echo -n "YOUR_BOT_TOKEN" | gcloud secrets create telegram-bot-token --data-file=-
# Create secrets

gcloud services enable cloudbuild.googleapis.com run.googleapis.com secretmanager.googleapis.com cloudscheduler.googleapis.com
# Enable APIs

gcloud config set project YOUR_PROJECT_ID
# Set project
```powershell

You still need to set up secrets and permissions once:

## Step 4: One-Time GCP Setup

---

```
timeout: '1200s'

  - 'gcr.io/$PROJECT_ID/ema-retest-alerts:latest'
  - 'gcr.io/$PROJECT_ID/ema-retest-alerts:$COMMIT_SHA'
images:

      - '--set-secrets=TELEGRAM_BOT_TOKEN=telegram-bot-token:latest,TELEGRAM_CHAT_ID=telegram-chat-id:latest'
      - '--max-instances=1'
      - '--timeout=300'
      - '--memory=512Mi'
      - '--no-allow-unauthenticated'
      - '--platform=managed'
      - '--region=asia-south1'
      - '--image=gcr.io/$PROJECT_ID/ema-retest-alerts:latest'
      - 'ema-retest-alerts'
      - 'deploy'
      - 'run'
    args:
  - name: 'gcr.io/cloud-builders/gcloud'
  # Deploy to Cloud Run
  
    args: ['push', 'gcr.io/$PROJECT_ID/ema-retest-alerts:latest']
  - name: 'gcr.io/cloud-builders/docker'
  # Push latest tag
  
    args: ['tag', 'gcr.io/$PROJECT_ID/ema-retest-alerts:$COMMIT_SHA', 'gcr.io/$PROJECT_ID/ema-retest-alerts:latest']
  - name: 'gcr.io/cloud-builders/docker'
  # Tag as latest
  
    args: ['push', 'gcr.io/$PROJECT_ID/ema-retest-alerts:$COMMIT_SHA']
  - name: 'gcr.io/cloud-builders/docker'
  # Push the container image
  
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/ema-retest-alerts:$COMMIT_SHA', '.']
  - name: 'gcr.io/cloud-builders/docker'
  # Build the container image
steps:
# Enhanced cloudbuild.yaml with automatic deployment
```yaml

Your existing `cloudbuild.yaml` will work, but here's an enhanced version:

This replaces the need to run `gcloud builds submit` manually.

### Create a Cloud Build trigger configuration file

## Step 3: Automated Deployment Setup

---

```
# (Follow instructions in GCP Console under Source Repositories > Add Repository > Connect external repository)
# Set up mirroring from GitHub to Cloud Source Repositories

gcloud source repos create ema-retest-alerts
# Create a mirror of your GitHub repo in Cloud Source Repositories
```bash

### Option B: Using Cloud Source Repositories Mirror

   - Click "Create"
   - Location: `cloudbuild.yaml`
   - Configuration: Cloud Build configuration file (yaml or json)
   - Branch: `^main$`
   - Event: Push to branch
   - Name: `ema-alerts-build`
   - Click "Create Trigger"
3. **Create Trigger:**

   - Click "Connect"
   - Select your repository
   - Authenticate with GitHub
   - Select "GitHub (Cloud Build GitHub App)"
   - Click "Connect Repository"
2. **Connect Repository:**

   ```
   # Or visit: https://console.cloud.google.com/cloud-build/triggers
   gcloud alpha builds triggers list
   # Open in browser
   ```bash
1. **Go to Cloud Build Triggers page:**

### Option A: Using Cloud Build GitHub App (Recommended)

## Step 2: Connect GitHub to GCP Cloud Build

---

```
git push -u origin main
# Push to GitHub

git remote add origin https://github.com/YOUR_USERNAME/ema-retest-alerts.git
# Add remote (replace with your GitHub username/repo)

git commit -m "Initial commit - EMA Retest Alerts with Playwright"
# Commit

git add .
# Add all files

git init
# Initialize git if not already done
```powershell
### Push your code

3. Don't initialize with README (we already have one)
2. Create a new repository (e.g., `ema-retest-alerts`)
1. Go to https://github.com/new
### Create a new repository on GitHub

## Step 1: Push Code to GitHub

---

3. `gcloud` CLI installed
2. GCP account with billing enabled
1. GitHub account
## Prerequisites

You can deploy directly from GitHub to GCP without building Docker locally. GCP Cloud Build will automatically build the Docker image from your repository.
## Overview


