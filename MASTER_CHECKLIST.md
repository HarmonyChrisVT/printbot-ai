# PrintBot AI — Master Checklist

> Last updated: 2026-03-29

---

## 1. GitHub Repository

**Repo:** https://github.com/HarmonyChrisVT/printbot-ai
**Branch:** `main`
**Clone URL:** `https://github.com/HarmonyChrisVT/printbot-ai.git`

---

## 2. Railway Deployment URL

Railway auto-assigns a URL on first deploy. To find yours:

1. Go to https://railway.app/dashboard
2. Open the **printbot-ai** project
3. Click the service → **Settings** → copy the public domain

It will look like: `https://printbot-ai-production-XXXX.up.railway.app`

> If no Railway project exists yet: click **New Project → Deploy from GitHub repo → HarmonyChrisVT/printbot-ai**. Railway will detect the `Dockerfile` automatically.

---

## 3. API Keys Required

Set all of these as **Railway Environment Variables** (Project → Variables tab).

### REQUIRED — System will not start without these

| Variable | Where to Get It |
|---|---|
| `SHOPIFY_SHOP_URL` | Your store subdomain, e.g. `my-store.myshopify.com` (no https://) |
| `SHOPIFY_ACCESS_TOKEN` | Shopify Admin → Apps → Develop Apps → create app → Admin API access token |
| `SHOPIFY_API_KEY` | Same app page as above (API key field) |
| `SHOPIFY_API_SECRET` | Same app page as above (API secret key field) |
| `PRINTFUL_API_KEY` | https://www.printful.com/dashboard/settings/api → Generate token |
| `PRINTFUL_STORE_ID` | Printful Dashboard URL contains the store ID, or API: GET /stores |
| `OPENAI_API_KEY` | https://platform.openai.com/api-keys → Create new secret key |

**Shopify app scopes required** — when creating the Shopify app, grant ALL of:
- `write_products`, `read_products`
- `write_orders`, `read_orders`
- `read_fulfillments`, `write_fulfillments`

### OPTIONAL — Social media posting (Social Agent)

| Variable | Where to Get It |
|---|---|
| `INSTAGRAM_USERNAME_0` | Your primary Instagram username |
| `INSTAGRAM_PASSWORD_0` | Your primary Instagram password |
| `INSTAGRAM_API_KEY_0` | Optional — Meta Graph API token if using official API |
| `INSTAGRAM_USERNAME_1` | Backup account (leave blank if unused) |
| `INSTAGRAM_PASSWORD_1` | Backup account password |
| `TIKTOK_USERNAME_0` | Primary TikTok username |
| `TIKTOK_PASSWORD_0` | Primary TikTok password |

### OPTIONAL — Email notifications (Fulfillment Agent)

| Variable | Example Value |
|---|---|
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | `yourname@gmail.com` |
| `SMTP_PASSWORD` | Gmail App Password (https://myaccount.google.com/apppasswords) |
| `NOTIFICATION_EMAIL` | Email address to receive order alerts |

### OPTIONAL — System

| Variable | Purpose |
|---|---|
| `EMERGENCY_CONTACT` | Phone/email for dead man's switch alerts |
| `BACKUP_CLOUD_TOKEN` | Google Drive / Dropbox token for weekly backups |
| `DATABASE_PATH` | Default: `/app/data/printbot.db` — only change if needed |

---

## 4. Resuming This Project in a New Claude Code Session

### Step 1 — Open the project folder

```
cd "C:\Users\vermo\Desktop\Kimi_Agent_Automated Store AI Agents"
```

Or in WSL:
```bash
cd "/mnt/c/Users/vermo/Desktop/Kimi_Agent_Automated Store AI Agents"
```

### Step 2 — Launch Claude Code

```bash
claude
```

### Step 3 — Use this prompt to get Claude Code up to speed

Paste this exactly at the start of the session:

```
This is PrintBot AI, a fully automated print-on-demand store system deployed on Railway via Docker.
GitHub repo: https://github.com/HarmonyChrisVT/printbot-ai (branch: main)
Working directory: /mnt/c/Users/vermo/Desktop/Kimi_Agent_Automated Store AI Agents

Architecture:
- FastAPI backend at python/main.py (port 8000 internal)
- nginx reverse proxy listening on $PORT (Railway injects this), proxies /api/ to uvicorn
- React dashboard at src/App.tsx and app/src/App.tsx (BOTH must be kept in sync)
- Pre-built dist/ at root is served by the root Dockerfile
- app/ subdirectory has its own Dockerfile that builds from app/src/
- SQLite database at /app/data/printbot.db (directory created at startup)
- All Python imports are absolute (from config.settings import ...) not relative
- 11 agents all initialized in PrintBotOrchestrator in python/main.py

Recent work completed:
- All 11 agents activated and showing in dashboard
- /api/health endpoint added (tests Shopify, Printful, OpenAI connections)
- /api/checkin POST endpoint wired up with UI feedback
- Shopify integration fixed: ClientTimeout, verify_scopes(), get_locations(), modern fulfillment_orders flow

Read MASTER_CHECKLIST.md for full project status and pending tasks.
```

### Step 4 — Git push credentials

The GitHub token is embedded in the remote URL. Run this if you need to re-authenticate:

```bash
git remote set-url origin https://YOUR_GITHUB_TOKEN@github.com/HarmonyChrisVT/printbot-ai.git
```

---

## 5. Agent Status

### Working (code complete, deployed)

| Agent | File | Status | Notes |
|---|---|---|---|
| **Design Agent** | `python/agents/design_agent.py` | Code complete | Generates designs with DALL-E 3, uploads mockups. Requires `OPENAI_API_KEY`. |
| **Pricing Agent** | `python/agents/pricing_agent.py` | Code complete | Dynamic pricing with competitor scraping, charm pricing, bundle discounts. |
| **Fulfillment Agent** | `python/agents/fulfillment_agent.py` | Code complete | Polls orders every 5 min, submits to Printful. Sends tracking emails if SMTP configured. |
| **Social Agent V2** | `python/agents/social_agent_v2.py` | Code complete | Instagram/TikTok posting. Works better with official API keys; login-based is fragile. |
| **Affiliate Agent** | `python/agents/affiliate_agent.py` | Code complete | Manages affiliate program and commission tracking. |
| **B2B Agent** | `python/agents/b2b_agent.py` | Code complete | Outreach to bulk/wholesale buyers. |
| **Competitor Spy Agent** | `python/agents/competitor_spy_agent.py` | Code complete | Scrapes competitor listings and prices. |
| **Content Writer Agent** | `python/agents/content_writer_agent.py` | Code complete | Writes product descriptions, blog posts, ad copy. Requires `OPENAI_API_KEY`. |
| **Customer Engagement Agent** | `python/agents/customer_engagement_agent.py` | Code complete | Follow-up emails, review requests, loyalty campaigns. |
| **Customer Service Chatbot** | `python/agents/customer_service_chatbot.py` | Code complete | Handles order status and FAQ replies via AI. |
| **Inventory Prediction Agent** | `python/agents/inventory_prediction_agent.py` | Code complete | Forecasts demand, triggers Printful restocks. |

### Infrastructure Status

| Component | Status | Notes |
|---|---|---|
| Docker build | Working | `Dockerfile` at repo root |
| nginx + uvicorn | Working | nginx on `$PORT`, proxies to uvicorn on 8000 |
| SQLite DB | Working | `/app/data/` created at startup |
| React dashboard | Working | Shows all 11 agents, live status polling |
| `/api/health` | Working | Tests all 3 API connections, returns JSON status |
| `/api/checkin` | Working | Dead man's switch check-in with UI feedback |
| Shopify integration | Working | Modern fulfillment_orders API, scope verification |
| Printful integration | Working | Order submission and tracking sync |
| OpenAI integration | Working | `openai>=1.40.0` fixes `proxies` bug |

### Known Limitations / Not Yet Tested End-to-End

- **Social Agent**: Instagram/TikTok unofficial login is brittle — official API credentials (`INSTAGRAM_API_KEY_0`) strongly recommended.
- **Scope verification**: `verify_scopes()` is available on `ShopifyAPI` but not called automatically at startup — add a startup check if you want it to gate the launch.
- **Dead man's switch notifications**: `EMERGENCY_CONTACT` is stored but outbound SMS/email for the switch is not yet implemented.
- **Cloud backup**: `BACKUP_CLOUD_TOKEN` is read from env but the backup upload logic is a stub — needs implementing if you want off-site backups.
- **TikTok agent**: Uses credential-based login (no official API) — prone to 2FA challenges in production.

---

## 6. Quick Smoke Test After Deploy

Once Railway shows the deploy as **Active**, hit these endpoints:

```bash
# Health check — should return 200 with API statuses
curl https://YOUR_RAILWAY_URL/api/health

# System status
curl https://YOUR_RAILWAY_URL/api/status

# Dashboard (opens in browser)
open https://YOUR_RAILWAY_URL
```

Expected `/api/health` response when all keys are set:
```json
{
  "status": "healthy",
  "shopify": {"connected": true},
  "printful": {"connected": true},
  "openai": {"connected": true}
}
```
