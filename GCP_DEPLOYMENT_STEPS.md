# GCP Deployment - Complete Step-by-Step Guide

## 🎯 Overview

This guide will walk you through deploying your EMA Retest Alerts application to Google Cloud Platform (GCP) using Cloud Run and Cloud Scheduler. The entire process takes approximately 20-30 minutes.

---

## 📋 Prerequisites

Before starting, ensure you have:

- ✅ Google Cloud account with billing enabled
- ✅ Project already pushed to GitHub: `https://github.com/imagine154/ema-retest-alerts`
- ✅ `gcloud` CLI installed on your computer
- ✅ Basic knowledge of command line operations

---

## 🚀 Deployment Process

### **Option 1: GitHub CI/CD (Recommended - Easiest)**
Push to GitHub → Automatic deployment

### **Option 2: Manual Deployment (Alternative)**
Manual build and deploy commands

---

# OPTION 1: GitHub CI/CD Deployment (Recommended)

This is the easiest method - every git push automatically deploys to GCP!

---

## Step 1: Install and Setup gcloud CLI

### 1.1 Check if gcloud is installed

```powershell
gcloud --version
```

**If not installed:**
- Download from: https://cloud.google.com/sdk/docs/install
- Install and restart your terminal

### 1.2 Login to Google Cloud

```powershell
gcloud auth login
```

This will open a browser window. Login with your Google account.

### 1.3 List your GCP projects

```powershell
gcloud projects list
```

**Output example:**
```
PROJECT_ID              NAME                PROJECT_NUMBER
my-project-123456       My Project          123456789012
```

**If you don't have a project, create one:**

```powershell
# Replace 'ema-alerts-prod' with your desired project ID
gcloud projects create ema-alerts-prod --name="EMA Alerts Production"
```

### 1.4 Set your project

```powershell
# Replace with your actual project ID from step 1.3
gcloud config set project YOUR_PROJECT_ID
```

**Example:**
```powershell
gcloud config set project ema-alerts-prod
```

### 1.5 Enable billing (if not already enabled)

Go to: https://console.cloud.google.com/billing

- Link your project to a billing account
- ⚠️ **Don't worry**: With ~$0.30/month usage, you'll likely stay within free tier

---

## Step 2: Enable Required GCP APIs

These APIs allow you to use Cloud Build, Cloud Run, Secret Manager, and Cloud Scheduler.

```powershell
gcloud services enable cloudbuild.googleapis.com run.googleapis.com cloudscheduler.googleapis.com secretmanager.googleapis.com
```

**Wait time:** ~1-2 minutes

**Expected output:**
```
Operation "operations/..." finished successfully.
```

---

## Step 3: Create Secrets for Telegram Credentials

Instead of hardcoding your Telegram credentials, we'll store them securely in GCP Secret Manager.

### 3.1 Create Telegram Bot Token Secret

```powershell
# When prompted, paste your Telegram bot token
echo -n "YOUR_TELEGRAM_BOT_TOKEN" | gcloud secrets create telegram-bot-token --data-file=-
```

**Replace** `YOUR_TELEGRAM_BOT_TOKEN` with your actual bot token (e.g., `8163995879:AAHEnG-mAxont26F1mwUfOHGv-NJ1iZWkao`)

**Example:**
```powershell
echo -n "8163995879:AAHEnG-mAxont26F1mwUfOHGv-NJ1iZWkao" | gcloud secrets create telegram-bot-token --data-file=-
```

**Expected output:**
```
Created secret [telegram-bot-token].
```

### 3.2 Create Telegram Chat ID Secret

```powershell
# Replace with your actual chat ID
echo -n "YOUR_TELEGRAM_CHAT_ID" | gcloud secrets create telegram-chat-id --data-file=-
```

**Example:**
```powershell
echo -n "-1002343316074" | gcloud secrets create telegram-chat-id --data-file=-
```

**Expected output:**
```
Created secret [telegram-chat-id].
```

### 3.3 Verify secrets were created

```powershell
gcloud secrets list
```

**Expected output:**
```
NAME                  CREATED              REPLICATION_POLICY  LOCATIONS
telegram-bot-token    2026-01-02T...       automatic           -
telegram-chat-id      2026-01-02T...       automatic           -
```

---

## Step 4: Grant Permissions to Access Secrets

Cloud Run needs permission to read the secrets you just created.

### 4.1 Get your project number

```powershell
gcloud projects describe YOUR_PROJECT_ID --format="value(projectNumber)"
```

**Example:**
```powershell
gcloud projects describe ema-alerts-prod --format="value(projectNumber)"
```

**Output example:**
```
123456789012
```

**Save this number** - you'll use it in the next commands.

### 4.2 Grant Cloud Run access to bot token secret

```powershell
# Replace PROJECT_NUMBER with the number from step 4.1
gcloud secrets add-iam-policy-binding telegram-bot-token --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"
```

**Example:**
```powershell
gcloud secrets add-iam-policy-binding telegram-bot-token --member="serviceAccount:123456789012-compute@developer.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"
```

**Expected output:**
```
Updated IAM policy for secret [telegram-bot-token].
```

### 4.3 Grant Cloud Run access to chat ID secret

```powershell
# Replace PROJECT_NUMBER with your number
gcloud secrets add-iam-policy-binding telegram-chat-id --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"
```

**Example:**
```powershell
gcloud secrets add-iam-policy-binding telegram-chat-id --member="serviceAccount:123456789012-compute@developer.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"
```

---

## Step 5: Grant Cloud Build Permissions

Cloud Build needs permission to deploy to Cloud Run.

### 5.1 Grant Cloud Build admin access to Cloud Run

```powershell
# Replace PROJECT_NUMBER with your number from step 4.1
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID --member="serviceAccount:PROJECT_NUMBER@cloudbuild.gserviceaccount.com" --role="roles/run.admin"
```

**Example:**
```powershell
gcloud projects add-iam-policy-binding ema-alerts-prod --member="serviceAccount:123456789012@cloudbuild.gserviceaccount.com" --role="roles/run.admin"
```

### 5.2 Grant Cloud Build service account user role

```powershell
# Replace PROJECT_NUMBER with your number
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID --member="serviceAccount:PROJECT_NUMBER@cloudbuild.gserviceaccount.com" --role="roles/iam.serviceAccountUser"
```

**Example:**
```powershell
gcloud projects add-iam-policy-binding ema-alerts-prod --member="serviceAccount:123456789012@cloudbuild.gserviceaccount.com" --role="roles/iam.serviceAccountUser"
```

**Expected output for both:**
```
Updated IAM policy for project [YOUR_PROJECT_ID].
```

---

## Step 6: Connect GitHub to Cloud Build

This is where the magic happens - GitHub will automatically trigger builds on every push!

### 6.1 Open Cloud Build Triggers page

```powershell
# This will open your browser to Cloud Build
start https://console.cloud.google.com/cloud-build/triggers?project=YOUR_PROJECT_ID
```

**Or manually navigate to:**
- https://console.cloud.google.com/cloud-build/triggers
- Select your project from the dropdown at the top

### 6.2 Connect your GitHub repository

**In the browser (Cloud Console):**

1. Click **"CREATE TRIGGER"** button
2. Click **"CONNECT REPOSITORY"**
3. Select source: **"GitHub (Cloud Build GitHub App)"**
4. Click **"CONTINUE"**
5. Click **"Authenticate"** - This opens GitHub
6. **In GitHub:** Authorize Google Cloud Build
7. Select your repository: **`imagine154/ema-retest-alerts`**
8. Click **"CONNECT"**
9. Click **"DONE"**

### 6.3 Create the Build Trigger

**Still in the browser:**

1. Click **"CREATE TRIGGER"** again (after connecting repo)
2. Fill in the following:

   **Name:** `ema-alerts-auto-deploy`
   
   **Description:** `Automatic deployment on push to main branch`
   
   **Event:** `Push to a branch`
   
   **Source → Repository:** `imagine154/ema-retest-alerts (GitHub App)`
   
   **Source → Branch:** `^main$` (exactly as shown)
   
   **Configuration → Type:** `Cloud Build configuration file (yaml or json)`
   
   **Configuration → Location:** `Repository` (default)
   
   **Configuration → Cloud Build configuration file location:** `/cloudbuild.yaml`
   
   **Advanced (expand) → Substitution variables:** Leave empty
   
   **Service account:** Leave as default

3. Click **"CREATE"**

**Expected result:**
- You'll see your trigger listed with a checkmark
- Status should show as "Enabled"

---

## Step 7: Trigger First Deployment

Now let's trigger your first deployment!

### 7.1 Make a small change to trigger deployment

```powershell
# In your project folder
cd D:\Python\EMA_Retest

# Make a small change (add a comment to README)
echo "`n<!-- Deployed to GCP on $(Get-Date -Format 'yyyy-MM-dd HH:mm') -->" >> README.md

# Commit and push
git add README.md
git commit -m "Trigger first GCP deployment"
git push origin main
```

### 7.2 Monitor the build

**Option A: Command Line**
```powershell
gcloud builds list --limit=5
```

**Option B: Browser (Recommended)**
```powershell
start https://console.cloud.google.com/cloud-build/builds?project=YOUR_PROJECT_ID
```

**What you'll see:**
- Build starts immediately after push
- Status: "Building" → "Success" (takes 5-8 minutes)
- Steps: Build Docker → Push to Registry → Deploy to Cloud Run

**Build logs show:**
```
Step 1: Building Docker image...
Step 2: Pushing image...
Step 3: Deploying to Cloud Run...
Step 4: Deployment complete!
```

### 7.3 Wait for build to complete

**Time:** ~5-8 minutes for first build

**Check status:**
```powershell
# Check latest build status
gcloud builds list --limit=1 --format="table(id,status,startTime,duration)"
```

**Wait until status shows:** `SUCCESS`

---

## Step 8: Verify Cloud Run Deployment

### 8.1 List Cloud Run services

```powershell
gcloud run services list --region=asia-south1
```

**Expected output:**
```
SERVICE               REGION        URL                                          LAST DEPLOYED
ema-retest-alerts     asia-south1   https://ema-retest-alerts-xxxxx-as.a.run.app 2026-01-02
```

### 8.2 Get service URL

```powershell
gcloud run services describe ema-retest-alerts --region=asia-south1 --format="value(status.url)"
```

**Save this URL** - you'll need it for the scheduler!

**Example output:**
```
https://ema-retest-alerts-a3k5m2n7pq-as.a.run.app
```

### 8.3 Test the service manually (Optional)

```powershell
# Get authentication token
$TOKEN = gcloud auth print-identity-token

# Test the service
curl -H "Authorization: Bearer $TOKEN" YOUR_SERVICE_URL
```

**Replace** `YOUR_SERVICE_URL` with the URL from step 8.2

**Expected:** Service runs and returns logs (or check Cloud Run logs)

---

## Step 9: Create Service Account for Cloud Scheduler

Cloud Scheduler needs permission to invoke your Cloud Run service.

### 9.1 Create service account

```powershell
gcloud iam service-accounts create ema-alerts-scheduler --display-name="EMA Alerts Scheduler"
```

**Expected output:**
```
Created service account [ema-alerts-scheduler].
```

### 9.2 Grant invoker permission

```powershell
# Replace YOUR_PROJECT_ID with your actual project ID
gcloud run services add-iam-policy-binding ema-retest-alerts --member="serviceAccount:ema-alerts-scheduler@YOUR_PROJECT_ID.iam.gserviceaccount.com" --role="roles/run.invoker" --region=asia-south1
```

**Example:**
```powershell
gcloud run services add-iam-policy-binding ema-retest-alerts --member="serviceAccount:ema-alerts-scheduler@ema-alerts-prod.iam.gserviceaccount.com" --role="roles/run.invoker" --region=asia-south1
```

**Expected output:**
```
Updated IAM policy for service [ema-retest-alerts].
```

---

## Step 10: Create Cloud Scheduler Job

This scheduler will run your script every 15 minutes during market hours.

### 10.1 Create the scheduler job

```powershell
# Replace YOUR_SERVICE_URL with the URL from step 8.2
# Replace YOUR_PROJECT_ID with your project ID

gcloud scheduler jobs create http ema-alerts-job --location=asia-south1 --schedule="*/15 9-15 * * 1-5" --time-zone="Asia/Kolkata" --uri="YOUR_SERVICE_URL" --http-method=GET --oidc-service-account-email="ema-alerts-scheduler@YOUR_PROJECT_ID.iam.gserviceaccount.com" --attempt-deadline=300s
```

**Full Example:**
```powershell
gcloud scheduler jobs create http ema-alerts-job --location=asia-south1 --schedule="*/15 9-15 * * 1-5" --time-zone="Asia/Kolkata" --uri="https://ema-retest-alerts-a3k5m2n7pq-as.a.run.app" --http-method=GET --oidc-service-account-email="ema-alerts-scheduler@ema-alerts-prod.iam.gserviceaccount.com" --attempt-deadline=300s
```

**Expected output:**
```
Created job [ema-alerts-job].
```

**Schedule Breakdown:**
- `*/15`: Every 15 minutes
- `9-15`: Between 9 AM and 3 PM (covers 9:00-15:45)
- `* * 1-5`: Every day of month, every month, Monday-Friday
- `Asia/Kolkata`: IST timezone

**Note:** Script internally checks for exact hours (9:20 AM - 3:25 PM) and holidays

### 10.2 Verify scheduler job

```powershell
gcloud scheduler jobs describe ema-alerts-job --location=asia-south1
```

**Expected output:**
```
attemptDeadline: 300s
httpTarget:
  httpMethod: GET
  oidcToken:
    serviceAccountEmail: ema-alerts-scheduler@...
  uri: https://ema-retest-alerts-...
name: projects/.../locations/asia-south1/jobs/ema-alerts-job
schedule: */15 9-15 * * 1-5
state: ENABLED
timeZone: Asia/Kolkata
```

---

## Step 11: Test the Complete Setup

### 11.1 Manually trigger the scheduler job

```powershell
gcloud scheduler jobs run ema-alerts-job --location=asia-south1
```

**Expected output:**
```
Triggering job [ema-alerts-job]...done.
```

### 11.2 Check Cloud Run logs

```powershell
gcloud run logs read ema-retest-alerts --region=asia-south1 --limit=50
```

**Expected logs:**
```
2026-01-02 XX:XX:XX - __main__ - INFO - === Starting EMA Retest Alert Script ===
2026-01-02 XX:XX:XX - __main__ - INFO - Market is open - Current time: XX:XX:XX
2026-01-02 XX:XX:XX - __main__ - INFO - Processing EMA20 screen...
2026-01-02 XX:XX:XX - __main__ - INFO - Fetched X symbols from table 2
...
```

**If market is closed, you'll see:**
```
2026-01-02 XX:XX:XX - __main__ - INFO - Market closed: Weekend/After hours/Holiday
2026-01-02 XX:XX:XX - __main__ - INFO - Script execution skipped - Market is closed
```

### 11.3 Check Telegram for alerts

If market is open and stocks are found, you should receive Telegram messages like:

```
📊 EMA20 Reversal Alert
🕒 10:15

RELIANCE | ₹2,450.50 | +2.3%
TCS | ₹3,800.00 | +1.5%
```

---

## Step 12: Monitor and Maintain

### 12.1 View recent builds

```powershell
gcloud builds list --limit=10
```

### 12.2 View Cloud Run service details

```powershell
gcloud run services describe ema-retest-alerts --region=asia-south1
```

### 12.3 View scheduler job executions

```powershell
gcloud scheduler jobs describe ema-alerts-job --location=asia-south1
```

### 12.4 View logs in real-time

```powershell
gcloud run logs tail ema-retest-alerts --region=asia-south1
```

Press `Ctrl+C` to stop tailing logs.

---

## 🎉 Deployment Complete!

Your EMA Retest Alerts system is now fully deployed and automated!

### What Happens Now:

1. **Every 15 minutes** (during market hours): Cloud Scheduler triggers your service
2. **Script checks**: Market hours, holidays, weekends
3. **If market is open**: Scrapes Chartink, sends Telegram alerts
4. **At 3:20 PM+**: State resets for next day
5. **Every git push**: Automatically rebuilds and redeploys

### Summary of Resources Created:

| Resource | Name | Purpose |
|----------|------|---------|
| Secrets | telegram-bot-token, telegram-chat-id | Secure credential storage |
| Cloud Run Service | ema-retest-alerts | Runs your application |
| Cloud Build Trigger | ema-alerts-auto-deploy | Auto-deploy on git push |
| Service Account | ema-alerts-scheduler | Scheduler authentication |
| Cloud Scheduler Job | ema-alerts-job | Runs every 15 min |

### Cost Estimate:

#### GCP Free Tier Breakdown:

**Cloud Run (Always Free Tier):**
- Free: 2 million requests/month
- Free: 360,000 GB-seconds memory/month
- Free: 180,000 vCPU-seconds/month
- **Your usage**: ~2,880 requests/month (96/day × 30 days)
- **Your memory**: ~9,600 GB-seconds/month (2 GB × 80 seconds × 60 runs)
- **Your CPU**: ~9,600 vCPU-seconds/month
- **Cost**: **$0.00** ✅ (Well within free tier!)

**Cloud Scheduler:**
- Free: 3 jobs
- **Your usage**: 1 job
- **Cost**: **$0.00** ✅ (Free tier!)

**Secret Manager:**
- Free: 6 active secret versions
- $0.06 per secret version per month after that
- **Your usage**: 2 secrets (bot token, chat ID)
- **Cost**: **$0.00** ✅ (Within free tier!)

**Cloud Build:**
- Free: 120 build-minutes/day
- **Your usage**: ~40 build-minutes/month (8 min/build × ~5 builds)
- **Cost**: **$0.00** ✅ (Free tier!)

**Container Registry Storage:**
- Free: 0.5 GB storage
- **Your usage**: ~200-300 MB (Docker images)
- **Cost**: **$0.00** ✅ (Free tier!)

**Networking (Egress):**
- Free: 1 GB/month to worldwide destinations (excluding China & Australia)
- **Your usage**: ~50-100 MB/month (API calls to Telegram)
- **Cost**: **$0.00** ✅ (Free tier!)

---

#### **Total Monthly Cost: $0.00** 🎉

**All services stay within GCP's Always Free tier!**

**Note:** These are based on:
- 96 executions/day (every 15 min, 6 hours × 4 times/hour)
- ~80 seconds per execution (scraping 3 Chartink screens)
- 2 GB memory, 2 vCPU per instance
- 5 deployments/month (code updates)

Your usage is approximately **5-10% of free tier limits** - extremely safe!

---

## 🔧 Useful Commands Reference

### View Logs
```powershell
# Last 50 log entries
gcloud run services logs read ema-retest-alerts --region=asia-south1 --limit=50

# Real-time logs
gcloud run services logs tail ema-retest-alerts --region=asia-south1

# Filter logs by severity
gcloud run services logs read ema-retest-alerts --region=asia-south1 --filter="severity=ERROR"
```

### Manage Scheduler
```powershell
# Manually run scheduler
gcloud scheduler jobs run ema-alerts-job --location=asia-south1

# Pause scheduler
gcloud scheduler jobs pause ema-alerts-job --location=asia-south1

# Resume scheduler
gcloud scheduler jobs resume ema-alerts-job --location=asia-south1

# Delete scheduler
gcloud scheduler jobs delete ema-alerts-job --location=asia-south1
```

### Update Service
```powershell
# Just push to GitHub - it auto-deploys!
git add .
git commit -m "Your changes"
git push origin main
```

### View Service URL
```powershell
gcloud run services describe ema-retest-alerts --region=asia-south1 --format="value(status.url)"
```

### Check Build Status
```powershell
gcloud builds list --limit=1 --format="table(id,status,startTime,duration)"
```

---

## 🐛 Troubleshooting

### Issue: Build fails with "permission denied"

**Solution:**
```powershell
# Re-grant Cloud Build permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID --member="serviceAccount:PROJECT_NUMBER@cloudbuild.gserviceaccount.com" --role="roles/run.admin"
```

### Issue: Scheduler not triggering

**Solution:**
```powershell
# Check scheduler status
gcloud scheduler jobs describe ema-alerts-job --location=asia-south1

# Manually trigger to test
gcloud scheduler jobs run ema-alerts-job --location=asia-south1
```

### Issue: "Secret not found" error

**Solution:**
```powershell
# List secrets
gcloud secrets list

# Recreate if missing
echo -n "YOUR_BOT_TOKEN" | gcloud secrets create telegram-bot-token --data-file=-
```

### Issue: Can't access secrets from Cloud Run

**Solution:**
```powershell
# Re-grant access
gcloud secrets add-iam-policy-binding telegram-bot-token --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"
```

### Issue: No logs appearing

**Solution:**
```powershell
# Check if service is deployed
gcloud run services list --region=asia-south1

# Check recent builds
gcloud builds list --limit=5

# View build logs
gcloud builds log BUILD_ID
```

---

## 📞 Getting Help

### View Service Details
```powershell
gcloud run services describe ema-retest-alerts --region=asia-south1
```

### View IAM Policies
```powershell
# For secrets
gcloud secrets get-iam-policy telegram-bot-token

# For Cloud Run
gcloud run services get-iam-policy ema-retest-alerts --region=asia-south1
```

### Check Quotas
```powershell
gcloud compute project-info describe --project=YOUR_PROJECT_ID
```

---

## 🎯 Next Steps

1. ✅ **Monitor first few runs** during market hours
2. ✅ **Verify Telegram alerts** are being received
3. ✅ **Check logs** after market close to confirm state reset
4. ✅ **Set up alerting** (optional) for errors in Cloud Monitoring
5. ✅ **Document** your deployment for team members

---

## 🔒 Security Best Practices

✅ Credentials in Secret Manager (not in code)
✅ Cloud Run requires authentication
✅ Service account with minimal permissions
✅ Secrets accessible only to authorized services
✅ HTTPS only for all communications

---

**Congratulations! Your EMA Retest Alerts system is now live in production on GCP!** 🚀

**Repository**: https://github.com/imagine154/ema-retest-alerts
**Status**: Production Ready ✅
**Cost**: ~$0.35/month 💰
**Deployment**: Automated via GitHub CI/CD 🤖

