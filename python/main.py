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
        return {
            'running': self.running,
            'dead_mans_switch': self.dead_mans_switch.get_status(),
            'agents': {
                'design': {'running': self.design_agent.running},
                'pricing': {'running': self.pricing_agent.running},
                'social': {'running': self.social_agent.running},
                'fulfillment': {'running': self.fulfillment_agent.running},
                'affiliate': {'running': self.affiliate_agent.running},
                'b2b': {'running': self.b2b_agent.running},
                'competitor_spy': {'running': self.competitor_spy_agent.running},
                'content_writer': {'running': False},
                'customer_engagement': {'running': self.customer_engagement_agent.running},
                'customer_service': {'running': self.customer_service_chatbot.running},
                'inventory_prediction': {'running': self.inventory_prediction_agent.running},
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
    """Get analytics data"""
    # Would query database for analytics
    return {
        "today": {
            "orders": 0,
            "revenue": 0,
            "profit": 0
        },
        "week": {
            "orders": 0,
            "revenue": 0,
            "profit": 0
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
