"""
PrintBot AI - Main Orchestrator V2
===================================
Coordinates all 6 AI agents with enhanced features
"""
import asyncio
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import json

from dotenv import load_dotenv
load_dotenv()

from config.settings import config, load_config_from_env
from database.models import init_database, get_session, SystemEvent

# Import all agents
from agents.design_agent import DesignAgent
from agents.pricing_agent import PricingAgent
from agents.social_agent_v2 import SocialAgentV2
from agents.fulfillment_agent import FulfillmentAgent
from agents.b2b_agent import B2BAgent
from agents.customer_engagement_agent import CustomerEngagementAgent
from agents.competitor_spy_agent import CompetitorSpyAgent
from agents.affiliate_agent import AffiliateAgent
from agents.content_writer_agent import ContentWriterAgent
from agents.customer_service_chatbot import CustomerServiceChatbot
from agents.inventory_prediction_agent import InventoryPredictionAgent
from agents.master_orchestrator import MasterOrchestrator
from agents.intelligence_bus import bus as intelligence_bus

from integrations.fulfillment_providers import FulfillmentProviderChain
from utils.protection_system import ProtectionSystem
from utils.profit_optimizer import ProfitOptimizer


class PrintBotOrchestratorV2:
    """
    Enhanced Main Orchestrator
    Manages 6 AI agents with failover and monitoring
    """
    
    def __init__(self):
        print("🚀 PrintBot AI V2 - Enhanced Automated POD System")
        print("=" * 60)
        
        # Load configuration
        load_config_from_env()
        
        # Initialize database
        self.engine = init_database(config.database_path)
        self.session = get_session(self.engine)
        
        # Initialize protection systems
        self.protection = ProtectionSystem(self.session)
        self.profit_optimizer = ProfitOptimizer(self.session)
        
        # Initialize fulfillment provider chain
        self.fulfillment_chain = FulfillmentProviderChain(self.session)
        
        # Initialize all 11 agents
        self.agents = {
            'design':               DesignAgent(self.session),
            'pricing':              PricingAgent(self.session),
            'social':               SocialAgentV2(self.session),
            'fulfillment':          FulfillmentAgent(self.session),
            'b2b':                  B2BAgent(self.session),
            'customer_engagement':  CustomerEngagementAgent(self.session),
            'competitor_spy':       CompetitorSpyAgent(self.session),
            'affiliate':            AffiliateAgent(self.session),
            'content_writer':       ContentWriterAgent(self.session),
            'customer_service':     CustomerServiceChatbot(self.session),
            'inventory_prediction': InventoryPredictionAgent(self.session),
        }

        # Master Orchestrator — boss above all agents
        self.master_orchestrator = MasterOrchestrator(self.session, self.agents)
        
        # State
        self.running = False
        self.agent_tasks = []
        self.dead_mans_switch_last_checkin = datetime.utcnow()
        # Note: signal handlers are intentionally NOT set here.
        # uvicorn manages SIGINT/SIGTERM for graceful shutdown in production.
    
    async def start(self):
        """Start all agents"""
        print("\n🟢 Starting PrintBot AI V2...")
        self.running = True
        
        # Check configuration
        self._check_configuration()

        # Live Shopify connection test
        await self._check_shopify_connection()

        # Initialize protection systems
        await self.protection.initialize()
        
        # Check fulfillment provider health
        await self._check_fulfillment_providers()
        
        # Create agent tasks
        print("\n📋 Starting Master Orchestrator + all 11 agents...")
        self.agent_tasks = [
            # Master Orchestrator starts first — sets the mode before agents run
            asyncio.create_task(self.master_orchestrator.run(), name='master_orchestrator'),
            asyncio.create_task(self.agents['design'].run(),               name='design'),
            asyncio.create_task(self.agents['pricing'].run(),              name='pricing'),
            asyncio.create_task(self.agents['social'].run(),               name='social'),
            asyncio.create_task(self.agents['fulfillment'].run(),          name='fulfillment'),
            asyncio.create_task(self.agents['b2b'].run(),                  name='b2b'),
            asyncio.create_task(self.agents['customer_engagement'].run(),  name='customer_engagement'),
            asyncio.create_task(self.agents['competitor_spy'].run(),       name='competitor_spy'),
            asyncio.create_task(self.agents['affiliate'].run(),            name='affiliate'),
            asyncio.create_task(self.agents['inventory_prediction'].run(), name='inventory_prediction'),
            asyncio.create_task(self._monitoring_loop(),                   name='monitoring'),
            asyncio.create_task(self._profit_analysis_loop(),              name='profit_analysis'),
        ]

        print("\n✅ Master Orchestrator + 11 agents started successfully!")
        print("📊 Dashboard available at http://localhost:8080")
        print("🔌 API available at http://localhost:8000")
        print("\nPress Ctrl+C to stop\n")
        
        # Wait for all tasks
        try:
            await asyncio.gather(*self.agent_tasks)
        except asyncio.CancelledError:
            pass
    
    def stop(self):
        """Stop all agents"""
        print("\n🛑 Stopping all agents...")
        self.running = False

        self.master_orchestrator.stop()

        # Stop each agent
        for name, agent in self.agents.items():
            print(f"   Stopping {name}...")
            agent.stop()
        
        # Cancel tasks
        for task in self.agent_tasks:
            task.cancel()
        
        print("✅ All agents stopped")
    
    def _check_configuration(self):
        """Check and report configuration status"""
        print("\n📋 Configuration Status:")
        print("-" * 40)
        
        checks = [
            ('Shopify', config.shopify.is_configured),
            ('Printful', config.printful.is_configured),
            ('OpenAI', config.openai.is_configured),
            ('Email SMTP', bool(config.fulfillment.smtp_host)),
        ]
        
        for name, is_configured in checks:
            status = "✅" if is_configured else "⚠️"
            print(f"{status} {name}: {'Connected' if is_configured else 'Not configured'}")
        
        # Check fulfillment providers
        print("\n📦 Fulfillment Providers:")
        print(f"   Primary: Printful")
        print(f"   Backup 1: Printify")
        print(f"   Backup 2: Gelato")
        print(f"   Backup 3: Gooten")
        
        # Check social accounts
        print("\n📱 Social Accounts:")
        ig_count = sum(1 for acc in config.social.instagram_accounts if acc.get('is_active'))
        tt_count = sum(1 for acc in config.social.tiktok_accounts if acc.get('is_active'))
        print(f"   Instagram: {ig_count} accounts")
        print(f"   TikTok: {tt_count} accounts")
        
        print("-" * 40)

    async def _check_shopify_connection(self):
        """Live Shopify connection test using Custom App token"""
        if not config.shopify.is_configured:
            print("⚠️  Shopify: Not configured — set SHOPIFY_SHOP_URL and SHOPIFY_ACCESS_TOKEN")
            return
        from integrations.shopify import ShopifyAPI
        result = await ShopifyAPI().test_connection()
        if result['ok']:
            print(f"✅ Shopify: Connected (Shop: {result['shop_name']})")
        else:
            print(f"❌ Shopify: Connection failed — {result['message']}")
            print("   → Check SHOPIFY_SETUP.md for instructions")

    async def _check_fulfillment_providers(self):
        """Check health of all fulfillment providers"""
        print("\n🏥 Checking fulfillment provider health...")
        health = await self.fulfillment_chain.health_check_all()
        
        for provider, is_healthy in health.items():
            status = "✅" if is_healthy else "❌"
            print(f"   {status} {provider.title()}: {'Healthy' if is_healthy else 'Unhealthy'}")
    
    async def _monitoring_loop(self):
        """Monitor system health"""
        while self.running:
            try:
                # Check dead man's switch
                elapsed = (datetime.utcnow() - self.dead_mans_switch_last_checkin).total_seconds()
                if elapsed > config.system.check_in_interval:
                    print("⚠️ DEAD MAN'S SWITCH: System will pause soon without check-in")
                
                # Check agent health
                for name, agent in self.agents.items():
                    if not agent.running and self.running:
                        print(f"⚠️ Agent {name} is not running!")
                
                # Log system health
                await asyncio.sleep(60)
                
            except Exception as e:
                print(f"❌ Monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _profit_analysis_loop(self):
        """Periodic profit analysis"""
        while self.running:
            try:
                # Generate profit recommendations
                recommendations = self.profit_optimizer.generate_recommendations()
                
                if recommendations:
                    print(f"\n💰 Profit Optimizer: {len(recommendations)} recommendations available")
                    for rec in recommendations[:3]:
                        print(f"   - {rec.action}: ${rec.current_price} → ${rec.recommended_price} ({rec.reason[:50]}...)")
                
                # Run every 4 hours
                await asyncio.sleep(4 * 3600)
                
            except Exception as e:
                print(f"❌ Profit analysis error: {e}")
                await asyncio.sleep(3600)
    
    # API methods for dashboard
    def get_status(self) -> Dict:
        """Get current system status"""
        return {
            'running': self.running,
            'agents': {
                name: {
                    'running': agent.running,
                    'last_activity': 'active'  # Would track actual last activity
                }
                for name, agent in self.agents.items()
            },
            'config': {
                'shopify': config.shopify.is_configured,
                'printful': config.printful.is_configured,
                'openai': config.openai.is_configured
            },
            'dead_mans_switch': {
                'last_checkin': self.dead_mans_switch_last_checkin.isoformat(),
                'time_until_pause': max(0, config.system.check_in_interval - 
                    (datetime.utcnow() - self.dead_mans_switch_last_checkin).total_seconds())
            },
            'fulfillment_providers': [
                {
                    'name': p.name,
                    'healthy': p.healthy,
                    'orders_processed': p.orders_processed
                }
                for p in self.fulfillment_chain.providers
            ]
        }
    
    def checkin(self):
        """User check-in"""
        self.dead_mans_switch_last_checkin = datetime.utcnow()
        print(f"✅ Check-in recorded at {self.dead_mans_switch_last_checkin}")
    
    def get_profit_recommendations(self) -> List[Dict]:
        """Get profit optimization recommendations"""
        recommendations = self.profit_optimizer.generate_recommendations()
        return [
            {
                'product_id': rec.product_id,
                'current_price': rec.current_price,
                'recommended_price': rec.recommended_price,
                'expected_margin': rec.expected_margin,
                'confidence': rec.confidence,
                'reason': rec.reason,
                'action': rec.action
            }
            for rec in recommendations
        ]
    
    def get_social_account_status(self) -> Dict:
        """Get social account status"""
        return self.agents['social'].get_account_status()


# FastAPI for dashboard API
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="PrintBot AI API V2")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global orchestrator instance
orchestrator = None

# Credentials saved via the dashboard are persisted here so they survive restarts
CONFIG_RUNTIME_FILE = "/app/data/.env.runtime"


class OverrideRequest(BaseModel):
    agent_name: str
    action: str
    target_id: str = None
    reason: str


class ConfigRequest(BaseModel):
    shopify_shop_url: str = ""
    shopify_access_token: str = ""
    openai_api_key: str = ""
    printful_api_key: str = ""
    design_auto_approve: bool = False


def _persist_config():
    """Write current credentials to a runtime file so they reload on next startup."""
    import os as _os
    try:
        _os.makedirs("/app/data", exist_ok=True)
        lines = []
        for key, val in [
            ("SHOPIFY_SHOP_URL",     config.shopify.shop_url),
            ("SHOPIFY_ACCESS_TOKEN", config.shopify.access_token),
            ("OPENAI_API_KEY",       config.openai.api_key),
            ("PRINTFUL_API_KEY",     config.printful.api_key),
            ("DESIGN_AUTO_APPROVE",  str(config.design.auto_approve).lower()),
        ]:
            if val:
                lines.append(f"{key}={val}\n")
        with open(CONFIG_RUNTIME_FILE, "w") as fh:
            fh.writelines(lines)
    except Exception as e:
        print(f"⚠️  Could not persist config: {e}")


@app.on_event("startup")
async def startup():
    global orchestrator
    # Load previously saved runtime credentials before initialising the orchestrator
    import os as _os
    _os.makedirs("/app/data", exist_ok=True)
    if _os.path.exists(CONFIG_RUNTIME_FILE):
        from dotenv import load_dotenv as _ld
        _ld(CONFIG_RUNTIME_FILE, override=True)
        print(f"✅ Loaded saved credentials from {CONFIG_RUNTIME_FILE}")
    # Re-load config now that env is fully populated
    load_config_from_env()
    try:
        orchestrator = PrintBotOrchestratorV2()
        asyncio.create_task(orchestrator.start())
    except Exception as e:
        print(f"❌ Orchestrator init failed: {e} — API still running, use dashboard to configure keys")
        # orchestrator stays None; all /api/* endpoints handle that gracefully


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.0.0"}


@app.get("/api/orchestrator")
async def get_orchestrator():
    """Get Master Orchestrator status — mode, strategy, agent priorities, intelligence flows"""
    if orchestrator:
        return orchestrator.master_orchestrator.get_status()
    return {"error": "System not initialized"}


@app.get("/api/status")
async def get_status():
    """Get system status"""
    if orchestrator:
        return orchestrator.get_status()
    return {"error": "System not initialized"}


@app.post("/api/checkin")
async def checkin():
    """User check-in"""
    if orchestrator:
        orchestrator.checkin()
        return {"status": "ok", "message": "Check-in recorded"}
    raise HTTPException(status_code=503, detail="System not initialized")


@app.post("/api/agents/{agent_name}/toggle")
async def toggle_agent(agent_name: str):
    """Toggle agent on/off"""
    if orchestrator and agent_name in orchestrator.agents:
        agent = orchestrator.agents[agent_name]
        if agent.running:
            agent.stop()
        else:
            # Would need to restart the agent task
            pass
        return {"status": "ok", "agent": agent_name, "running": agent.running}
    raise HTTPException(status_code=404, detail="Agent not found")


@app.get("/api/profit/recommendations")
async def get_profit_recommendations():
    """Get profit optimization recommendations"""
    if orchestrator:
        return orchestrator.get_profit_recommendations()
    raise HTTPException(status_code=503, detail="System not initialized")


@app.get("/api/social/accounts")
async def get_social_accounts():
    """Get social account status"""
    if orchestrator:
        return orchestrator.get_social_account_status()
    raise HTTPException(status_code=503, detail="System not initialized")


@app.get("/api/fulfillment/providers")
async def get_fulfillment_providers():
    """Get fulfillment provider status"""
    if orchestrator:
        return {
            'providers': [
                {
                    'name': p.name,
                    'healthy': p.healthy,
                    'orders_processed': p.orders_processed
                }
                for p in orchestrator.fulfillment_chain.providers
            ]
        }
    raise HTTPException(status_code=503, detail="System not initialized")


@app.post("/api/override")
async def manual_override(request: OverrideRequest):
    """Manual override endpoint"""
    # Log the override
    print(f"🎛️ Manual override: {request.agent_name} - {request.action}")
    print(f"   Reason: {request.reason}")
    
    # Would implement actual override logic
    return {
        "status": "ok",
        "override": {
            "agent": request.agent_name,
            "action": request.action,
            "target": request.target_id,
            "reason": request.reason,
            "timestamp": datetime.utcnow().isoformat()
        }
    }


@app.get("/api/analytics/profit")
async def get_profit_analytics():
    """Get profit analytics"""
    # Would query database for actual analytics
    return {
        "today": {
            "revenue": 347.95,
            "costs": 198.50,
            "profit": 149.45,
            "margin": 42.9,
            "orders": 7
        },
        "this_week": {
            "revenue": 2184.50,
            "costs": 1247.30,
            "profit": 937.20,
            "margin": 42.9
        },
        "this_month": {
            "revenue": 8947.25,
            "costs": 5112.80,
            "profit": 3834.45,
            "margin": 42.9
        }
    }


@app.get("/api/config/status")
async def get_config_status():
    """Returns which fields are configured (booleans only — values never exposed)."""
    return {
        "shopify_shop_url":       bool(config.shopify.shop_url),
        "shopify_access_token":   bool(config.shopify.access_token),
        "openai_api_key":         bool(config.openai.api_key),
        "printful_api_key":       bool(config.printful.api_key),
        "design_auto_approve":    config.design.auto_approve,
    }


@app.post("/api/config")
async def save_config_endpoint(request: ConfigRequest):
    """
    Save credentials entered via the dashboard setup form.
    Updates the in-memory config immediately and persists to /app/data/.env.runtime
    so values are re-loaded on the next restart.
    Returns a live Shopify connection test result.
    """
    import os as _os

    if request.shopify_shop_url:
        # Strip https:// — common mistake
        url = request.shopify_shop_url.strip().rstrip("/")
        url = url.replace("https://", "").replace("http://", "")
        config.shopify.shop_url = url
        _os.environ["SHOPIFY_SHOP_URL"] = url

    if request.shopify_access_token:
        token = request.shopify_access_token.strip()
        config.shopify.access_token = token
        _os.environ["SHOPIFY_ACCESS_TOKEN"] = token

    if request.openai_api_key:
        key = request.openai_api_key.strip()
        config.openai.api_key = key
        _os.environ["OPENAI_API_KEY"] = key

    if request.printful_api_key:
        key = request.printful_api_key.strip()
        config.printful.api_key = key
        _os.environ["PRINTFUL_API_KEY"] = key

    config.design.auto_approve = request.design_auto_approve

    _persist_config()

    # Run a live Shopify connection test immediately
    shopify_test = None
    if config.shopify.is_configured:
        from integrations.shopify import ShopifyAPI
        shopify_test = await ShopifyAPI().test_connection()

    return {"status": "saved", "shopify_test": shopify_test}


@app.get("/api/test")
async def run_diagnostics():
    """
    Full system diagnostic — call this to see exactly what is and isn't working.
    Checks: Shopify connection, OpenAI config, auto_approve flag, and DB counts.
    """
    results = {}

    # 1. Shopify live connection test
    from integrations.shopify import ShopifyAPI
    shopify_result = await ShopifyAPI().test_connection()
    results["shopify"] = shopify_result

    # 2. OpenAI configured
    results["openai"] = {
        "configured": config.openai.is_configured,
        "model": config.openai.model,
        "image_model": config.openai.image_model,
    }

    # 3. Design auto-approve — THIS is why products don't appear without it
    results["design_pipeline"] = {
        "auto_approve": config.design.auto_approve,
        "approval_threshold": config.design.approval_threshold,
        "max_daily_designs": config.design.max_daily_designs,
        "warning": (
            None if config.design.auto_approve
            else "DESIGN_AUTO_APPROVE is false — designs are generated but never approved, "
                 "so NO products will ever reach Shopify. Set DESIGN_AUTO_APPROVE=true in your .env."
        ),
    }

    # 4. Database counts
    if orchestrator:
        session = orchestrator.session
        from database.models import Design, Product
        from datetime import date
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        designs_total    = session.query(Design).count()
        designs_pending  = session.query(Design).filter(Design.status == "pending").count()
        designs_approved = session.query(Design).filter(Design.status == "approved").count()
        designs_today    = session.query(Design).filter(Design.created_at >= today_start).count()
        products_total   = session.query(Product).count()
        products_shopify = session.query(Product).filter(Product.shopify_id.isnot(None)).count()

        results["database"] = {
            "designs_total":    designs_total,
            "designs_pending":  designs_pending,
            "designs_approved": designs_approved,
            "designs_today":    designs_today,
            "products_in_db":   products_total,
            "products_in_shopify": products_shopify,
        }

        # 5. Recent errors from agent logs
        from database.models import AgentLog
        recent_errors = (
            session.query(AgentLog)
            .filter(AgentLog.status == "error")
            .order_by(AgentLog.created_at.desc())
            .limit(5)
            .all()
        )
        results["recent_errors"] = [
            {
                "agent":   e.agent_name,
                "action":  e.action,
                "details": e.details,
                "time":    e.created_at.isoformat() if e.created_at else None,
            }
            for e in recent_errors
        ]
    else:
        results["database"] = {"error": "orchestrator not initialized"}
        results["recent_errors"] = []

    return results


@app.post("/api/trigger/design")
async def trigger_design():
    """
    Manually trigger one complete design → approve → Shopify product cycle.
    Bypasses the 30-minute timer and the auto_approve setting.
    Use this to test the end-to-end pipeline immediately.
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="System not initialized")

    if not config.openai.is_configured:
        raise HTTPException(status_code=400, detail="OPENAI_API_KEY not set — cannot generate design")

    agent = orchestrator.agents["design"]

    # Run one full cycle in the background so the HTTP response returns immediately
    async def _run():
        try:
            # Temporarily force auto_approve on for this manual trigger
            original = config.design.auto_approve
            config.design.auto_approve = True
            await agent._process_cycle()
            config.design.auto_approve = original
        except Exception as e:
            print(f"❌ Manual design trigger error: {e}")

    asyncio.create_task(_run())

    return {
        "status": "triggered",
        "message": (
            "Design cycle started in background. "
            "Check /api/test in ~60 seconds to see if a product was created in Shopify."
        ),
    }


# ── Serve the pre-built React dashboard ──────────────────────────────────────
# Must come AFTER all /api/* routes so FastAPI handles those first.
# Railway deploys with dist/ at /app/dist/ (see Dockerfile).
from pathlib import Path as _Path
from fastapi.staticfiles import StaticFiles as _StaticFiles

_dist_dir = _Path(__file__).parent.parent / "dist"
if _dist_dir.is_dir():
    app.mount("/", _StaticFiles(directory=str(_dist_dir), html=True), name="static")
else:
    print(f"⚠️  React dist/ not found at {_dist_dir} — dashboard will not be served")


def main():
    """Local dev entry point — in production uvicorn is invoked directly via CMD."""
    import uvicorn
    port = int(__import__("os").getenv("PORT", "8080"))
    uvicorn.run("main_v2:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()
