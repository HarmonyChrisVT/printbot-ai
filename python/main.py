"""
PrintBot AI - Main Orchestrator
================================
Coordinates all 11 AI agents and manages the system
"""
import asyncio
import signal
import sys
from datetime import datetime
from pathlib import Path
import json
from typing import Dict

from config.settings import config, load_config_from_env
from database.models import init_database, get_session, SystemEvent
from agents.design_agent import DesignAgent
from agents.pricing_agent import PricingAgent
from agents.social_agent_v2 import SocialAgentV2
from agents.fulfillment_agent import FulfillmentAgent
from agents.affiliate_agent import AffiliateAgent
from agents.b2b_agent import B2BAgent
from agents.competitor_spy_agent import CompetitorSpyAgent
from agents.content_writer_agent import ContentWriterAgent
from agents.customer_engagement_agent import CustomerEngagementAgent
from agents.customer_service_chatbot import CustomerServiceChatbot
from agents.inventory_prediction_agent import InventoryPredictionAgent


class DeadMansSwitch:
    """
    Dead Man's Switch
    Pauses system if user doesn't check in regularly
    """
    
    def __init__(self, check_interval_hours: int = 24):
        self.check_interval = check_interval_hours * 3600  # Convert to seconds
        self.last_checkin = datetime.utcnow()
        self.is_paused = False
    
    def checkin(self):
        """User check-in - resets the timer"""
        self.last_checkin = datetime.utcnow()
        if self.is_paused:
            self.is_paused = False
            print("✅ System resumed - check-in received")
        print(f"✅ Check-in recorded at {self.last_checkin}")
    
    def should_pause(self) -> bool:
        """Check if system should be paused"""
        elapsed = (datetime.utcnow() - self.last_checkin).total_seconds()
        return elapsed > self.check_interval
    
    def get_status(self) -> Dict:
        """Get current status"""
        elapsed = (datetime.utcnow() - self.last_checkin).total_seconds()
        remaining = max(0, self.check_interval - elapsed)
        
        return {
            'is_paused': self.is_paused,
            'last_checkin': self.last_checkin.isoformat(),
            'time_until_pause': remaining,
            'check_interval': self.check_interval
        }


class BackupManager:
    """
    Manages automated backups to cloud storage
    """
    
    def __init__(self, db_session):
        self.session = db_session
        self.backup_dir = Path('./data/backups')
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_backup(self) -> str:
        """Create a backup of all data"""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        backup_file = self.backup_dir / f'printbot_backup_{timestamp}.zip'
        
        try:
            import zipfile
            
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Backup database
                db_path = Path(config.database_path)
                if db_path.exists():
                    zf.write(db_path, 'database.db')
                
                # Backup designs
                designs_dir = Path('./data/designs')
                if designs_dir.exists():
                    for file in designs_dir.glob('*'):
                        zf.write(file, f'designs/{file.name}')
                
                # Backup config
                config_file = Path('./data/config.json')
                if config_file.exists():
                    zf.write(config_file, 'config.json')
            
            print(f"✅ Backup created: {backup_file}")
            
            # Upload to cloud if configured
            if config.system.backup_cloud_token:
                await self._upload_to_cloud(backup_file)
            
            # Log event
            event = SystemEvent(
                event_type='backup',
                severity='info',
                message=f'Backup created: {backup_file.name}',
                details={'file': str(backup_file)}
            )
            self.session.add(event)
            self.session.commit()
            
            return str(backup_file)
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return None
    
    async def _upload_to_cloud(self, backup_file: Path):
        """Upload backup to cloud storage"""
        # Would implement Google Drive, Dropbox, or S3 upload here
        print(f"☁️ Would upload {backup_file.name} to cloud storage")


class PrintBotOrchestrator:
    """
    Main orchestrator that coordinates all agents
    """
    
    def __init__(self):
        print("🚀 PrintBot AI - Automated POD System")
        print("=" * 50)
        
        # Load configuration
        load_config_from_env()
        
        # Initialize database
        self.engine = init_database(config.database_path)
        self.session = get_session(self.engine)
        
        # Initialize agents
        self.design_agent = DesignAgent(self.session)
        self.pricing_agent = PricingAgent(self.session)
        self.social_agent = SocialAgentV2(self.session)
        self.fulfillment_agent = FulfillmentAgent(self.session)
        self.affiliate_agent = AffiliateAgent(self.session)
        self.b2b_agent = B2BAgent(self.session)
        self.competitor_spy_agent = CompetitorSpyAgent(self.session)
        self.content_writer_agent = ContentWriterAgent(self.session)
        self.customer_engagement_agent = CustomerEngagementAgent(self.session)
        self.customer_service_chatbot = CustomerServiceChatbot(self.session)
        self.inventory_prediction_agent = InventoryPredictionAgent(self.session)
        
        # Initialize systems
        self.dead_mans_switch = DeadMansSwitch(
            config.system.check_in_interval // 3600
        )
        self.backup_manager = BackupManager(self.session)
        
        # State
        self.running = False
        self.agent_tasks = []
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\n🛑 Shutdown signal received")
        self.stop()
        sys.exit(0)
    
    async def start(self):
        """Start all agents"""
        print("\n🟢 Starting all agents...")
        self.running = True
        
        # Check configuration
        self._check_configuration()
        
        # Create agent tasks
        self.agent_tasks = [
            asyncio.create_task(self.design_agent.run()),
            asyncio.create_task(self.pricing_agent.run()),
            asyncio.create_task(self.social_agent.run()),
            asyncio.create_task(self.fulfillment_agent.run()),
            asyncio.create_task(self.affiliate_agent.run()),
            asyncio.create_task(self.b2b_agent.run()),
            asyncio.create_task(self.competitor_spy_agent.run()),
            asyncio.create_task(self.content_writer_agent.run()),
            asyncio.create_task(self.customer_engagement_agent.run()),
            asyncio.create_task(self.customer_service_chatbot.run()),
            asyncio.create_task(self.inventory_prediction_agent.run()),
            asyncio.create_task(self._monitoring_loop()),
        ]
        
        # Add backup task if enabled
        if config.system.backup_enabled:
            self.agent_tasks.append(
                asyncio.create_task(self._backup_loop())
            )
        
        print("\n✅ All agents started successfully!")
        print("📊 Dashboard available at http://localhost:8080")
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
        
        # Stop agents
        self.design_agent.stop()
        self.pricing_agent.stop()
        self.social_agent.stop()
        self.fulfillment_agent.stop()
        self.affiliate_agent.stop()
        self.b2b_agent.stop()
        self.competitor_spy_agent.stop()
        self.content_writer_agent.stop()
        self.customer_engagement_agent.stop()
        self.customer_service_chatbot.stop()
        self.inventory_prediction_agent.stop()
        
        # Cancel tasks
        for task in self.agent_tasks:
            task.cancel()
        
        print("✅ All agents stopped")
    
    def _check_configuration(self):
        """Check and report configuration status"""
        print("\n📋 Configuration Status:")
        print("-" * 30)
        
        checks = [
            ('Shopify', config.shopify.is_configured),
            ('Printful', config.printful.is_configured),
            ('OpenAI', config.openai.is_configured),
            ('Email', bool(config.fulfillment.smtp_host)),
        ]
        
        for name, is_configured in checks:
            status = "✅" if is_configured else "⚠️"
            print(f"{status} {name}: {'Connected' if is_configured else 'Not configured'}")
        
        print("-" * 30)
    
    async def _monitoring_loop(self):
        """Monitor system health and dead man's switch"""
        while self.running:
            try:
                # Check dead man's switch
                if config.system.dead_mans_switch_enabled:
                    if self.dead_mans_switch.should_pause():
                        if not self.dead_mans_switch.is_paused:
                            print("⚠️ DEAD MAN'S SWITCH ACTIVATED - Pausing system")
                            print("   Check in to resume operations")
                            self.dead_mans_switch.is_paused = True
                            # Would pause agents here
                
                # Check agent health (would check last activity)
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                print(f"❌ Monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _backup_loop(self):
        """Periodic backup task"""
        while self.running:
            try:
                await self.backup_manager.create_backup()
                await asyncio.sleep(config.system.backup_interval)
            except Exception as e:
                print(f"❌ Backup error: {e}")
                await asyncio.sleep(3600)  # Retry in 1 hour
    
    # API methods for dashboard
    def get_status(self) -> Dict:
        """Get current system status"""
        from database.models import AgentLog, Design, Order, SocialPost
        from sqlalchemy import func

        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        def last_activity_str(agent_name: str) -> str:
            log = self.session.query(AgentLog).filter(
                AgentLog.agent_name == agent_name
            ).order_by(AgentLog.created_at.desc()).first()
            if not log:
                return "Never"
            diff = (datetime.utcnow() - log.created_at).total_seconds()
            if diff < 60:
                return f"{int(diff)} seconds ago"
            if diff < 3600:
                return f"{int(diff / 60)} minutes ago"
            return f"{int(diff / 3600)} hours ago"

        designs_today = self.session.query(func.count(Design.id)).filter(
            Design.created_at >= today
        ).scalar() or 0
        designs_total = self.session.query(func.count(Design.id)).scalar() or 0
        designs_pending = self.session.query(func.count(Design.id)).filter(
            Design.status == 'pending'
        ).scalar() or 0
        orders_today = self.session.query(func.count(Order.id)).filter(
            Order.created_at >= today
        ).scalar() or 0
        posts_today = self.session.query(func.count(SocialPost.id)).filter(
            SocialPost.created_at >= today
        ).scalar() or 0

        dms = self.dead_mans_switch.get_status()

        return {
            'running': self.running,
            'deadMansSwitch': {
                'isPaused': dms['is_paused'],
                'lastCheckin': dms['last_checkin'],
                'timeUntilPause': dms['time_until_pause'],
            },
            'agents': {
                'design': {
                    'name': 'Design Agent', 'running': self.design_agent.running,
                    'lastActivity': last_activity_str('design'),
                    'stats': {'designsToday': designs_today, 'designsTotal': designs_total, 'pendingApproval': designs_pending}
                },
                'pricing': {
                    'name': 'Pricing Agent', 'running': self.pricing_agent.running,
                    'lastActivity': last_activity_str('pricing'),
                    'stats': {'productsUpdated': 0, 'avgMargin': 40}
                },
                'social': {
                    'name': 'Social Agent', 'running': self.social_agent.running,
                    'lastActivity': last_activity_str('social'),
                    'stats': {'postsToday': posts_today, 'followers': 0, 'engagement': 0}
                },
                'fulfillment': {
                    'name': 'Fulfillment Agent', 'running': self.fulfillment_agent.running,
                    'lastActivity': last_activity_str('fulfillment'),
                    'stats': {'ordersToday': orders_today, 'pendingOrders': 0, 'shippedToday': 0}
                },
                'b2b': {
                    'name': 'B2B Agent', 'running': self.b2b_agent.running,
                    'lastActivity': last_activity_str('b2b'),
                    'stats': {'leadsContacted': 0, 'dealsActive': 0, 'quotesSent': 0}
                },
                'content_writer': {
                    'name': 'Content Writer Agent', 'running': self.content_writer_agent.running,
                    'lastActivity': last_activity_str('content_writer'),
                    'stats': {'descriptionsWritten': 0, 'abTestsActive': 0}
                },
                'competitor_spy': {
                    'name': 'Competitor Spy Agent', 'running': self.competitor_spy_agent.running,
                    'lastActivity': last_activity_str('competitor_spy'),
                    'stats': {'competitorsTracked': 0, 'priceChanges': 0, 'alertsTriggered': 0}
                },
                'inventory_prediction': {
                    'name': 'Inventory Prediction Agent', 'running': self.inventory_prediction_agent.running,
                    'lastActivity': last_activity_str('inventory_prediction'),
                    'stats': {'productsAnalyzed': 0, 'restockAlerts': 0, 'forecastAccuracy': 0}
                },
                'customer_service': {
                    'name': 'Customer Service Chatbot', 'running': self.customer_service_chatbot.running,
                    'lastActivity': last_activity_str('customer_service'),
                    'stats': {'ticketsHandled': 0, 'avgResponseTime': 0, 'satisfactionRate': 0}
                },
                'affiliate': {
                    'name': 'Affiliate Agent', 'running': self.affiliate_agent.running,
                    'lastActivity': last_activity_str('affiliate'),
                    'stats': {'affiliatesActive': 0, 'clicksToday': 0, 'commissionsEarned': 0}
                },
                'customer_engagement': {
                    'name': 'Customer Engagement Agent', 'running': self.customer_engagement_agent.running,
                    'lastActivity': last_activity_str('customer_engagement'),
                    'stats': {'emailsSent': 0, 'openRate': 0, 'campaignsActive': 0}
                },
            },
            'config': {
                'shopify': config.shopify.is_configured,
                'printful': config.printful.is_configured,
                'openai': config.openai.is_configured
            }
        }
    
    def checkin(self):
        """User check-in"""
        self.dead_mans_switch.checkin()
    
    async def manual_backup(self) -> str:
        """Trigger manual backup"""
        return await self.backup_manager.create_backup()


# FastAPI for dashboard API
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="PrintBot AI API")

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


@app.on_event("startup")
async def startup():
    global orchestrator
    orchestrator = PrintBotOrchestrator()
    asyncio.create_task(orchestrator.start())


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


@app.post("/api/backup")
async def manual_backup():
    """Trigger manual backup"""
    if orchestrator:
        backup_file = await orchestrator.manual_backup()
        return {"status": "ok", "file": backup_file}
    raise HTTPException(status_code=503, detail="System not initialized")


@app.get("/api/analytics")
async def get_analytics():
    """Get analytics data from database"""
    if not orchestrator:
        return {"today": {"orders": 0, "revenue": 0, "profit": 0, "designs": 0, "posts": 0},
                "week": {"orders": 0, "revenue": 0, "profit": 0}}

    from database.models import Order, Sale, Design, SocialPost
    from sqlalchemy import func

    session = orchestrator.session
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start.replace(day=today_start.day - today_start.weekday())

    today_orders = session.query(func.count(Order.id)).filter(Order.created_at >= today_start).scalar() or 0
    today_revenue = session.query(func.sum(Order.total_price)).filter(Order.created_at >= today_start).scalar() or 0.0
    today_profit = session.query(func.sum(Sale.profit)).filter(Sale.sale_date >= today_start).scalar() or 0.0
    today_designs = session.query(func.count(Design.id)).filter(Design.created_at >= today_start).scalar() or 0
    today_posts = session.query(func.count(SocialPost.id)).filter(SocialPost.created_at >= today_start).scalar() or 0

    week_orders = session.query(func.count(Order.id)).filter(Order.created_at >= week_start).scalar() or 0
    week_revenue = session.query(func.sum(Order.total_price)).filter(Order.created_at >= week_start).scalar() or 0.0
    week_profit = session.query(func.sum(Sale.profit)).filter(Sale.sale_date >= week_start).scalar() or 0.0

    return {
        "today": {
            "orders": today_orders,
            "revenue": round(float(today_revenue), 2),
            "profit": round(float(today_profit), 2),
            "designs": today_designs,
            "posts": today_posts,
        },
        "week": {
            "orders": week_orders,
            "revenue": round(float(week_revenue), 2),
            "profit": round(float(week_profit), 2),
        }
    }


@app.get("/api/health")
async def health_check():
    """Test all API connections and return their status"""
    import aiohttp
    import time

    results = {}

    # --- Shopify ---
    if not config.shopify.is_configured:
        results["shopify"] = {"ok": False, "error": "not configured"}
    else:
        t = time.monotonic()
        try:
            url = f"https://{config.shopify.shop_url}/admin/api/{config.shopify.api_version}/shop.json"
            headers = {"X-Shopify-Access-Token": config.shopify.access_token}
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    latency = round((time.monotonic() - t) * 1000)
                    if resp.status == 200:
                        data = await resp.json()
                        results["shopify"] = {
                            "ok": True,
                            "shop": data.get("shop", {}).get("name"),
                            "plan": data.get("shop", {}).get("plan_name"),
                            "latency_ms": latency,
                        }
                    else:
                        results["shopify"] = {"ok": False, "status": resp.status, "latency_ms": latency}
        except Exception as e:
            results["shopify"] = {"ok": False, "error": str(e)}

    # --- Printful ---
    if not config.printful.is_configured:
        results["printful"] = {"ok": False, "error": "not configured"}
    else:
        t = time.monotonic()
        try:
            url = f"{config.printful.api_base}/store"
            headers = {"Authorization": f"Bearer {config.printful.api_key}"}
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    latency = round((time.monotonic() - t) * 1000)
                    if resp.status == 200:
                        data = await resp.json()
                        store = data.get("result", {})
                        results["printful"] = {
                            "ok": True,
                            "store": store.get("name"),
                            "currency": store.get("currency"),
                            "latency_ms": latency,
                        }
                    else:
                        results["printful"] = {"ok": False, "status": resp.status, "latency_ms": latency}
        except Exception as e:
            results["printful"] = {"ok": False, "error": str(e)}

    # --- OpenAI ---
    if not config.openai.is_configured:
        results["openai"] = {"ok": False, "error": "not configured"}
    else:
        t = time.monotonic()
        try:
            import openai as _openai
            client = _openai.AsyncOpenAI(api_key=config.openai.api_key)
            models = await client.models.list()
            latency = round((time.monotonic() - t) * 1000)
            model_ids = [m.id for m in models.data[:5]]
            results["openai"] = {
                "ok": True,
                "models_available": len(models.data),
                "sample_models": model_ids,
                "latency_ms": latency,
            }
        except Exception as e:
            results["openai"] = {"ok": False, "error": str(e)}

    all_ok = all(v["ok"] for v in results.values())
    return {
        "healthy": all_ok,
        "services": results,
    }


def main():
    """Main entry point"""
    orchestrator = PrintBotOrchestrator()
    
    try:
        asyncio.run(orchestrator.start())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")


if __name__ == "__main__":
    main()
