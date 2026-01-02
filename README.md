er# EMA Retest Alerts - Stock Market Alert System

Automated alert system that monitors Chartink.com EMA (Exponential Moving Average) reversal patterns and sends Telegram notifications when new stocks match the criteria.

## 🚀 Features

- **Real-time Monitoring**: Tracks EMA20, EMA50, and EMA200 reversal patterns
- **Smart Deduplication**: Only alerts for new stocks, prevents spam
- **State Management**: Automatic cleanup of old entries (7-day retention)
- **Retry Logic**: Handles network failures gracefully with 3 retries
- **Comprehensive Logging**: Full observability for debugging and monitoring
- **JavaScript Support**: Uses Playwright to scrape dynamic content
- **GCP Ready**: Production-ready with Docker, Cloud Run, and Secret Manager support
- **Cost Efficient**: Runs for ~$0.30/month on GCP Cloud Run

## 📋 Prerequisites

### Local Development
- Python 3.11+
- pip
- Telegram Bot Token and Chat ID

### GCP Deployment
- Google Cloud account with billing enabled
- `gcloud` CLI installed and configured
- Git (for GitHub deployment)

## 🛠️ Local Setup

1. **Clone or navigate to the project directory**
   ```powershell
   cd D:\Python\EMA_Retest
   ```

2. **Create virtual environment**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**
   ```powershell
   pip install -r requirements.txt
   playwright install chromium
   ```

4. **Set environment variables**
   ```powershell
   $env:TELEGRAM_BOT_TOKEN = "your_bot_token"
   $env:TELEGRAM_CHAT_ID = "your_chat_id"
   ```

5. **Run the script**
   ```powershell
   python chartink_ema_alerts.py
   ```

### Quick Test

Use the provided test script:
```powershell
.\test_local.ps1
```

## ☁️ GCP Deployment

### Option 1: Deploy from GitHub (Recommended - No Docker Needed Locally!)

**Simple 4-step process:**

1. **Push code to GitHub**
   ```powershell
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/ema-retest-alerts.git
   git push -u origin main
   ```

2. **Run GCP setup script**
   ```powershell
   .\setup_github_gcp.ps1 -ProjectId "your-gcp-project-id"
   ```

3. **Connect GitHub to Cloud Build**
   - Go to: https://console.cloud.google.com/cloud-build/triggers
   - Click "Connect Repository"
   - Select "GitHub (Cloud Build GitHub App)"
   - Authenticate and select your repository
   - Create trigger with configuration: `cloudbuild.yaml`

4. **Every git push auto-deploys!**
   ```powershell
   git push origin main
   ```

**Detailed Guide**: See [GITHUB_DEPLOYMENT.md](GITHUB_DEPLOYMENT.md)
**Quick Start**: See [QUICKSTART_GITHUB.md](QUICKSTART_GITHUB.md)

### Option 2: Manual Deployment

Use the deployment script:
```powershell
.\deploy_gcp.ps1 -ProjectId "your-gcp-project-id"
```

### After First Deployment: Set up Cloud Scheduler

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe ema-retest-alerts --region asia-south1 --format="value(status.url)")

# Create service account
gcloud iam service-accounts create ema-alerts-scheduler

# Grant permission
gcloud run services add-iam-policy-binding ema-retest-alerts \
  --member="serviceAccount:ema-alerts-scheduler@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.invoker" \
  --region asia-south1

# Create scheduler (every 15 min, 9-3:30pm IST, Mon-Fri)
# Note: Script internally validates 9:20 AM - 3:25 PM and skips holidays
gcloud scheduler jobs create http ema-alerts-job \
  --location asia-south1 \
  --schedule "*/15 9-15 * * 1-5" \
  --time-zone "Asia/Kolkata" \
  --uri "${SERVICE_URL}" \
  --http-method GET \
  --oidc-service-account-email "ema-alerts-scheduler@YOUR_PROJECT_ID.iam.gserviceaccount.com"
```

## 📊 Monitored Screens

| EMA Type | URL |
|----------|-----|
| EMA20 | https://chartink.com/screener/stocks-are-touching-20-day-ema-and-reversing |
| EMA50 | https://chartink.com/screener/stocks-are-touching-50-day-ema-and-reversing-2 |
| EMA200 | https://chartink.com/screener/stocks-are-touching-200-day-ema-and-reversing |

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token | Hardcoded fallback | No* |
| `TELEGRAM_CHAT_ID` | Your Telegram chat/channel ID | Hardcoded fallback | No* |
| `STATE_FILE` | Path to state file | `state.json` | No |

*Required for production deployment

### Settings in Code

```python
STATE_RETENTION_DAYS = 7      # Days to keep stock symbols in state
MAX_RETRIES = 3               # Number of retry attempts
RETRY_DELAY = 2               # Seconds between retries

# Market Hours (IST)
MARKET_OPEN_HOUR = 9          # 9 AM
MARKET_OPEN_MINUTE = 20       # 9:20 AM
MARKET_CLOSE_HOUR = 15        # 3 PM
MARKET_CLOSE_MINUTE = 25      # 3:25 PM

# NSE Trading Holidays: 15 holidays configured for 2026
```

## 📝 Logs

### View GCP Cloud Run Logs
```bash
gcloud run logs read ema-retest-alerts --region asia-south1 --limit 50
```

## 🚨 Alert Format

Telegram messages look like:
```
📊 EMA20 Reversal Alert
🕒 10:15

RELIANCE | ₹2,450.50 | +2.3%
TCS | ₹3,800.00 | +1.5%
INFY | ₹1,650.25 | +0.8%
```

## 🔍 Troubleshooting

### Issue: No alerts received
- Check if stocks actually appear on Chartink screens
- Verify Telegram bot token and chat ID
- Check logs for errors

### Issue: Duplicate alerts
- State file may be corrupted, delete `state.json` and restart
- Check if multiple instances are running

### Issue: Scraping fails
- Chartink website structure may have changed
- Check network connectivity
- Review error logs for specific issues

## 📁 Project Structure

```
EMA_Retest/
├── chartink_ema_alerts.py    # Main application
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container definition
├── cloudbuild.yaml           # GCP Build configuration
├── deployment.yaml           # Cloud Run configuration
├── cloud-scheduler.yaml      # Scheduler reference
├── .dockerignore             # Docker build exclusions
├── .gitignore                # Git exclusions
├── .env.example              # Environment template
├── test_local.ps1            # Local test script
├── test_docker.ps1           # Docker test script
├── deploy_gcp.ps1            # Manual GCP deployment
├── setup_github_gcp.ps1      # GitHub deployment setup
├── README.md                 # This file
├── GITHUB_DEPLOYMENT.md      # Detailed GitHub deployment guide
└── QUICKSTART_GITHUB.md      # Quick GitHub setup guide
```

## 🔒 Security

- ✅ Credentials stored in GCP Secret Manager
- ✅ No hardcoded secrets in production
- ✅ IAM roles with least privilege
- ✅ HTTPS for all communications
- ✅ Authenticated Cloud Run endpoints
- ✅ Timeout protection against hanging requests

## 💰 Cost Estimate

### GCP Cloud Run (Recommended)
- **Executions**: ~2,880/month (96/day)
- **Compute**: ~24 hours/month
- **Estimated Cost**: $0.20 - $0.50/month

### Alternatives
- **Cloud Functions**: ~$0.60/month
- **Compute Engine (e2-micro)**: ~$6.50/month

## 📚 Documentation

- [GITHUB_DEPLOYMENT.md](GITHUB_DEPLOYMENT.md) - Complete GitHub to GCP deployment guide
- [QUICKSTART_GITHUB.md](QUICKSTART_GITHUB.md) - Quick 4-step setup

## ⚠️ Disclaimer

This tool is for informational purposes only. Always do your own research before making investment decisions. The developers are not responsible for any trading losses.

---

**Built for GCP Cloud Run** • **Python 3.11+** • **Production Ready** • **Playwright Enabled**

