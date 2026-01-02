# Quick Start: Deploy from GitHub to GCP

## TL;DR - What You Need

✅ **Keep the Dockerfile** - GCP Cloud Build uses it to build your container
✅ **Push to GitHub** - No Docker installation needed on your machine
✅ **One-time GCP setup** - Secrets and permissions
✅ **Auto-deploy** - Every git push triggers build and deployment

❌ **Don't need Docker locally** - Cloud Build handles it
❌ **Don't need manual builds** - GitHub webhook triggers automatically

---

## Simple 4-Step Process

### Step 1: Push to GitHub (5 minutes)

```powershell
# In your project folder
git init
git add .
git commit -m "Initial commit - EMA Retest Alerts"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/ema-retest-alerts.git
git push -u origin main
```

### Step 2: Setup GCP (5 minutes)

Run the setup script:
```powershell
.\setup_github_gcp.ps1 -ProjectId "your-gcp-project-id"
```

This will:
- Enable required APIs
- Create secrets for Telegram credentials
- Set up permissions

### Step 3: Connect GitHub to Cloud Build (2 minutes)

1. Go to: https://console.cloud.google.com/cloud-build/triggers
2. Click **"Connect Repository"**
3. Select **"GitHub (Cloud Build GitHub App)"**
4. Authenticate with GitHub
5. Select your `ema-retest-alerts` repository
6. Click **"Create Trigger"**:
   - Name: `ema-alerts-auto-deploy`
   - Event: **Push to branch**
   - Branch: `^main$`
   - Configuration: **Cloud Build configuration file**
   - Location: `cloudbuild.yaml`
7. Click **"Create"**

### Step 4: Deploy! (Automatic)

Just push to GitHub:
```powershell
git add .
git commit -m "Deploy to GCP"
git push origin main
```

Cloud Build automatically:
1. ✅ Builds Docker image
2. ✅ Pushes to Container Registry
3. ✅ Deploys to Cloud Run

View progress: https://console.cloud.google.com/cloud-build/builds

---

## After First Deployment: Setup Scheduler (One-time, 2 minutes)

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe ema-retest-alerts --region asia-south1 --format="value(status.url)")

# Create service account
gcloud iam service-accounts create ema-alerts-scheduler --display-name "EMA Alerts Scheduler"

# Grant permission
gcloud run services add-iam-policy-binding ema-retest-alerts \
  --member="serviceAccount:ema-alerts-scheduler@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.invoker" \
  --region asia-south1

# Create scheduler (runs every 15 min, 9-3:30pm IST, Mon-Fri)
gcloud scheduler jobs create http ema-alerts-job \
  --location asia-south1 \
  --schedule "*/15 9-15 * * 1-5" \
  --time-zone "Asia/Kolkata" \
  --uri "${SERVICE_URL}" \
  --http-method GET \
  --oidc-service-account-email "ema-alerts-scheduler@YOUR_PROJECT_ID.iam.gserviceaccount.com"
```

---

## That's It! 

### From now on:
```powershell
# Make code changes
git add .
git commit -m "Your changes"
git push origin main
# ← Automatically builds and deploys!
```

### Monitor:
- **Builds**: https://console.cloud.google.com/cloud-build/builds
- **Logs**: `gcloud run logs read ema-retest-alerts --region asia-south1`
- **Service**: https://console.cloud.google.com/run

---

## FAQ

**Q: Do I need Docker installed?**
A: No! Cloud Build uses your Dockerfile but runs in GCP's infrastructure.

**Q: Do I need the Dockerfile?**
A: Yes, keep it in your repo. Cloud Build needs it to know how to build your container.

**Q: What happens on git push?**
A: GitHub webhook → Cloud Build trigger → Build image → Deploy to Cloud Run (all automatic)

**Q: How much does it cost?**
A: ~$0.30-0.50/month (Cloud Build has 120 free build-minutes/day)

**Q: Can I rollback?**
A: Yes! Deploy any previous commit by triggering that build in Cloud Build console.

**Q: How do I see build errors?**
A: Cloud Build > Builds > Click on failed build > View logs

---

## Next Steps

- ✅ Test locally first: `python chartink_ema_alerts.py`
- ✅ Push to GitHub
- ✅ Setup GCP (one-time)
- ✅ Connect GitHub to Cloud Build
- ✅ First push triggers deployment
- ✅ Setup Cloud Scheduler
- ✅ Monitor in GCP Console

**Full details**: See `GITHUB_DEPLOYMENT.md`

