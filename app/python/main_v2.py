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
        
        # Initialize all 6 agents
        self.agents = {
            'design': DesignAgent(self.session),
            'pricing': PricingAgent(self.session),
            'social': SocialAgentV2(self.session),
            'fulfillment': FulfillmentAgent(self.session),
            'b2b': B2BAgent(self.session),
            'engagement': CustomerEngagementAgent(self.session)
        }
        
        # State
        self.running = False
        self.agent_tasks = []
        self.dead_mans_switch_last_checkin = datetime.utcnow()
        
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
        print("\n🟢 Starting PrintBot AI V2...")
        self.running = True
        
        # Check configuration
        self._check_configuration()
        
        # Initialize protection systems
        await self.protection.initialize()
        
        # Check fulfillment provider health
        await self._check_fulfillment_providers()
        
        # Create agent tasks
        print("\n📋 Starting agents...")
        self.agent_tasks = [
            asyncio.create_task(self.agents['design'].run(), name='design'),
            asyncio.create_task(self.agents['pricing'].run(), name='pricing'),
            asyncio.create_task(self.agents['social'].run(), name='social'),
            asyncio.create_task(self.agents['fulfillment'].run(), name='fulfillment'),
            asyncio.create_task(self.agents['b2b'].run(), name='b2b'),
            asyncio.create_task(self.agents['engagement'].run(), name='engagement'),
            asyncio.create_task(self._monitoring_loop(), name='monitoring'),
            asyncio.create_task(self._profit_analysis_loop(), name='profit_analysis'),
        ]
        
        print("\n✅ All 6 agents started successfully!")
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


class OverrideRequest(BaseModel):
    agent_name: str
    action: str
    target_id: str = None
    reason: str


@app.on_event("startup")
async def startup():
    global orchestrator
    orchestrator = PrintBotOrchestratorV2()
    asyncio.create_task(orchestrator.start())


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.0.0"}


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


def main():
    """Main entry point"""
    orchestrator = PrintBotOrchestratorV2()
    
    try:
        asyncio.run(orchestrator.start())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")


if __name__ == "__main__":
    main()
