# 🤖 PrintBot AI - Automated Print-on-Demand System

A fully automated print-on-demand business system powered by 4 AI agents that design products, optimize pricing, manage social media, and handle fulfillment - all running 24/7 on autopilot.

![PrintBot AI Dashboard](docs/dashboard-preview.png)

## 🎯 What This System Does

PrintBot AI runs a complete print-on-demand business with minimal human intervention:

| Agent | Schedule | Function |
|-------|----------|----------|
| **🎨 Design** | Every 30 min | Scans trends → GPT-4 → DALL-E → Creates products (max 3/day) |
| **💰 Pricing** | Every 2 hrs | Competitor scraping → Dynamic pricing → 40% anchor, 25% floor margin |
| **📱 Social** | Every 6 hrs | Posts content → Instagram/TikTok → Auto-engagement |
| **📦 Fulfillment** | Every 5 min | Order polling → Printful API → Tracking emails |

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- API keys for Shopify, Printful, and OpenAI

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/printbot-ai.git
cd printbot-ai

# Run setup
python start.py --setup

# Edit configuration
nano .env

# Start the system
python start.py
```

The dashboard will be available at `http://localhost:8080`

## 📋 Configuration

Create a `.env` file with your API credentials:

```env
# Required
SHOPIFY_SHOP_URL=your-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=your_admin_api_token
PRINTFUL_API_KEY=your_printful_api_key
OPENAI_API_KEY=your_openai_api_key

# Optional - Social Media
INSTAGRAM_USERNAME_0=your_main_account
INSTAGRAM_PASSWORD_0=your_password

# Optional - Email Notifications
SMTP_HOST=smtp.gmail.com
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PrintBot AI System                        │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Design  │  │ Pricing  │  │  Social  │  │Fulfillment│   │
│  │  Agent   │  │  Agent   │  │  Agent   │  │  Agent    │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │             │             │             │           │
│       └─────────────┴──────┬──────┴─────────────┘           │
│                            │                                 │
│                    ┌───────┴───────┐                        │
│                    │  Orchestrator │                        │
│                    └───────┬───────┘                        │
│                            │                                 │
│       ┌────────────────────┼────────────────────┐           │
│       │                    │                    │           │
│  ┌────┴────┐        ┌─────┴─────┐       ┌─────┴────┐       │
│  │ Shopify │        │ Printful  │       │ Database │       │
│  └─────────┘        └───────────┘       └──────────┘       │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │              Protection & Monitoring                │   │
│  │  • Rate Limiting  • Fraud Detection  • Backups     │   │
│  └────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 🎨 Design Agent

The Design Agent automatically:
- Scans Google Trends, Pinterest, Etsy for trending topics
- Generates AI designs using DALL-E 3
- Creates product mockups
- Submits to Shopify for review (or auto-approves)

**Daily Limit**: 3 designs to maintain quality

## 💰 Pricing Agent

The Pricing Agent continuously:
- Scrapes competitor prices
- Calculates optimal prices using elasticity analysis
- Applies psychological pricing ($27.99 vs $28.00)
- Maintains 25-40% profit margins

**Pricing Strategy**:
- Anchor: 40% margin
- Floor: 25% margin (never go below)
- Charm pricing enabled
- Bundle discounts: 15% off for 2+ items

## 📱 Social Agent

The Social Agent manages:
- **Instagram**: 3 accounts (primary + 2 backups)
- **TikTok**: 3 accounts (primary + 2 backups)
- Auto-posting with human-like delays
- Auto-engagement (likes, comments, follows)
- Content generation with trending hashtags

**Daily Limits**: 100 actions to stay within platform rules

## 📦 Fulfillment Agent

The Fulfillment Agent handles:
- Order polling from Shopify (every 5 min)
- Printful order creation
- Tracking number sync
- Customer email notifications
- Backup provider switching (Printify, Gelato)

## 🛡️ Protection Systems

### Dead Man's Switch
- Pauses system if you don't check in within 24 hours
- Prevents runaway automation

### Rate Limiting
- Exponential backoff for API failures
- Platform compliance monitoring
- Prevents account bans

### Fraud Detection
- Flags suspicious orders
- High-value order alerts
- Multiple address detection

### Content Moderation
- AI-generated content screening
- Policy compliance checks
- Prevents inappropriate designs

### Automated Backups
- Weekly database backups
- Design file backups
- Cloud upload (Google Drive/Dropbox)

## 📊 Profit Optimization

The system includes advanced profit optimization:

- **Demand Forecasting**: Predicts sales based on trends
- **Price Elasticity**: Adjusts prices based on demand sensitivity
- **Bundle Optimization**: Identifies products frequently bought together
- **Seasonal Analysis**: Recommends trending keywords by season

## 📈 Analytics Dashboard

Monitor your business in real-time:

- Revenue & profit tracking
- Agent activity logs
- Order fulfillment status
- Social media engagement
- Competitor price tracking

## 🔧 Advanced Configuration

### Customizing Agent Schedules

Edit `python/config/settings.py`:

```python
@dataclass
class DesignConfig:
    max_daily_designs: int = 3
    design_interval: int = 1800  # 30 minutes
```

### Adding Competitors

```python
config.pricing.competitor_urls = [
    'https://competitor1.com/products',
    'https://competitor2.com/products'
]
```

### Backup Providers

```python
config.printful.backup_providers = [
    {"name": "printify", "enabled": True, "api_key": "..."},
    {"name": "gelato", "enabled": True, "api_key": "..."}
]
```

## 🚨 Troubleshooting

### Agents Not Starting
```bash
# Check logs
tail -f logs/printbot.log

# Verify configuration
python -c "from python.config import config; print(config.shopify.is_configured)"
```

### Rate Limiting
- The system automatically backs off when rate limited
- Check `api_health` in dashboard
- Adjust `max_daily_actions` if needed

### API Failures
- System switches to backup providers automatically
- Check integration status in dashboard
- Verify API keys in `.env`

## 📚 API Documentation

### REST API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | System status |
| `/api/checkin` | POST | Dead man's switch check-in |
| `/api/backup` | POST | Trigger manual backup |
| `/api/analytics` | GET | Analytics data |

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

## 🙏 Acknowledgments

- OpenAI for GPT-4 and DALL-E
- Shopify for the e-commerce platform
- Printful for print-on-demand fulfillment

---

**Disclaimer**: This system automates business operations. Always monitor your business, comply with platform terms of service, and ensure you have proper rights to sell designs.
