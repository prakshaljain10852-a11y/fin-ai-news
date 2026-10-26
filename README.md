# Telegram Newsletter Intelligence Bot - Setup Guide

## Overview
Fully automated system that fetches PDF newsletters from a private Telegram channel, analyzes them with AI, and delivers structured daily reports via Telegram Bot. Runs free on GitHub Actions.

## Architecture
```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Telegram       │     │  GitHub Actions  │     │  Telegram Bot   │
│  Channel        │────▶│  (Daily 7 AM)    │────▶│  (Your Chat)    │
│  (PDFs)         │     │  • Fetch PDFs    │     │  • Report       │
└─────────────────┘     │  • Extract Text  │     └─────────────────┘
                        │  • LLM Analysis  │
                        │  • Synthesize    │
                        └────────┬─────────┘
                                 │
                        ┌────────▼─────────┐
                        │  FCC Proxy /     │
                        │  LLM API         │
                        │  (Nemotron)      │
                        └──────────────────┘
```

## Prerequisites
1. **Telegram API credentials** - Get from https://my.telegram.org/apps
2. **Telegram Bot token** - Create via @BotFather
3. **Private channel access** - You must be a member
4. **LLM endpoint** - Your FCC proxy (localhost:8082) tunneled publicly, or free API (OpenRouter)

## Step-by-Step Setup

### 1. Clone & Configure Locally
```bash
cd telegram-newsletter-bot
cp config/.env.example .env
# Edit .env with your credentials
```

### 2. Get Telegram API Credentials
1. Go to https://my.telegram.org/apps
2. Create new application
3. Note `api_id` and `api_hash`

### 3. Create Telegram Bot
1. Message @BotFather
2. `/newbot` → follow prompts
3. Save the `BOT_TOKEN`
4. Message your bot, then get your chat ID:
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Find `"chat":{"id":YOUR_CHAT_ID}`

### 4. First Run (Local) - Generate Session
```bash
# Install deps
pip install -r requirements.txt

# Run once locally to authenticate and create session file
python -m src.main
```
- Enter phone number when prompted
- Enter OTP from Telegram
- This creates `newsletter_session.session` file

### 5. Deploy to GitHub Actions

#### A. Create GitHub Repository
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/telegram-newsletter-bot.git
git push -u origin main
```

#### B. Add Repository Secrets
Go to Settings → Secrets and variables → Actions → New repository secret:

| Secret Name | Value |
|------------|-------|
| `TELEGRAM_API_ID` | Your api_id (integer) |
| `TELEGRAM_API_HASH` | Your api_hash (string) |
| `TELEGRAM_PHONE` | Your phone with country code (e.g., +919876543210) |
| `TARGET_CHANNEL` | Channel username (e.g., @Economic_Times_Epapers) |
| `BOT_TOKEN` | Bot token from @BotFather |
| `REPORT_CHAT_ID` | Your numeric chat ID |
| `LLM_BASE_URL` | Public URL of your LLM endpoint |
| `LLM_API_KEY` | API key (or "dummy" for FCC) |
| `LLM_MODEL` | Model name (e.g., open_router/nvidia/nemotron-3-super-120b-a12b) |
| `TELEGRAM_SESSION` | Base64-encoded session file (see below) |

#### C. Encode Session File
```bash
# After local run creates newsletter_session.session
base64 -w 0 newsletter_session.session
# Copy output and add as TELEGRAM_SESSION secret
```

#### D. Make LLM Endpoint Public (Critical for GitHub Actions)
Your local FCC proxy (localhost:8082) isn't accessible from GitHub runners. Options:

**Option 1: Cloudflare Tunnel (Free, Recommended)**
```bash
# Install cloudflared
# Run tunnel pointing to localhost:8082
cloudflared tunnel --url http://localhost:8082
# Use the https://xxx.trycloudflare.com URL as LLM_BASE_URL
```

**Option 2: ngrok (Free tier)**
```bash
ngrok http 8082
# Use the https://xxx.ngrok.io URL
```

**Option 3: Deploy FCC Proxy to Cloud (Railway/Render/Fly.io)**
- Deploy the FCC proxy container to a free tier service
- Use that public URL

**Option 4: Use Free LLM API Directly**
- OpenRouter free tier: `https://openrouter.ai/api/v1`
- Get API key from OpenRouter
- Use model like `google/gemma-2-9b-it:free`

### 6. Test the Workflow
1. Go to Actions tab in GitHub
2. Click "Daily Newsletter Intelligence" workflow
3. Click "Run workflow" → "Run workflow"
4. Check logs for any errors

### 7. Verify Delivery
- Check your Telegram chat with the bot
- Should receive formatted daily report

## Customization

### Change Schedule
Edit `.github/workflows/daily-newsletter.yml`:
```yaml
on:
  schedule:
    - cron: '30 1 * * *'  # 7:00 AM IST = 1:30 AM UTC
```

### Add More Channels
Modify `src/fetcher.py` to accept multiple channels in `TARGET_CHANNEL` (comma-separated).

### Adjust Analysis Focus
Edit `SYSTEM_PROMPT` and `USER_PROMPT_TEMPLATE` in `src/analyzer.py`.

### Change Report Format
Modify `src/bot.py` formatting methods.

## Troubleshooting

### "Session expired" / Authentication errors
- Re-run locally to generate fresh session
- Update `TELEGRAM_SESSION` secret

### "LLM connection failed"
- Verify `LLM_BASE_URL` is publicly accessible
- Test: `curl -X POST $LLM_BASE_URL/chat/completions ...`
- Check tunnel is running

### "No PDFs found"
- Check `TARGET_CHANNEL` is correct (@username format)
- Verify channel actually has PDF attachments
- Check `DAYS_BACK` setting

### GitHub Actions timeout
- Reduce `MAX_MESSAGES_PER_RUN`
- Increase `timeout-minutes` in workflow

## Files Structure
```
telegram-newsletter-bot/
├── .github/workflows/daily-newsletter.yml  # GitHub Actions workflow
├── config/.env.example                     # Config template
├── requirements.txt                        # Python dependencies
├── src/
│   ├── config.py          # Settings management
│   ├── fetcher.py         # Telegram channel fetching
│   ├── pdf_extractor.py   # PDF text/table extraction
│   ├── analyzer.py        # LLM analysis
│   ├── bot.py             # Telegram Bot delivery
│   └── main.py            # Orchestrator
└── README.md               # This file
```

## Cost
- **GitHub Actions**: Free (2000 min/month on public repos)
- **Telegram**: Free
- **LLM**: Free via FCC proxy + tunnel, or OpenRouter free tier
- **Total**: $0/month

## Security Notes
- Never commit `.env` or `*.session` files
- Session file contains auth tokens - treat like password
- Rotate secrets periodically
- Bot only sends to your `REPORT_CHAT_ID`