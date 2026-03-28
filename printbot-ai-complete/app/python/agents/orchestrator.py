"""
Agent Orchestrator - Coordinates all 11 AI Agents
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import random

from python.agents.design_agent import DesignAgent
from python.agents.pricing_agent import PricingAgent
from python.agents.social_agent_v2 import SocialAgentV2
from python.agents.fulfillment_agent import FulfillmentAgent
from python.agents.b2b_agent import B2BAgent
from python.agents.content_writer_agent import ContentWriterAgent
from python.agents.competitor_spy_agent import CompetitorSpyAgent
from python.agents.inventory_prediction_agent import InventoryPredictionAgent
from python.agents.customer_service_chatbot import CustomerServiceChatbot
from python.agents.affiliate_agent import AffiliateAgent
from python.agents.customer_engagement_agent import CustomerEngagementAgent
from python.utils.logger import get_logger

logger = get_logger(__name__)

class AgentOrchestrator:
    """Central orchestrator for all AI agents"""
    
    def __init__(self):
        self.agents = {}
        self.agent_status = {}
        self.running = False
        self._init_agents()
    
    def _init_agents(self):
        """Initialize all 11 agents"""
        logger.info("Initializing all AI agents...")
        
        self.agents = {
            'design': DesignAgent(),
            'pricing': PricingAgent(),
            'social': SocialAgentV2(),
            'fulfillment': FulfillmentAgent(),
            'b2b': B2BAgent(),
            'content_writer': ContentWriterAgent(),
            'competitor_spy': CompetitorSpyAgent(),
            'inventory_prediction': InventoryPredictionAgent(),
            'customer_service': CustomerServiceChatbot(),
            'affiliate': AffiliateAgent(),
            'customer_engagement': CustomerEngagementAgent()
        }
        
        # Initialize all agent statuses
        for name in self.agents:
            self.agent_status[name] = {
                'status': 'idle',
                'last_action': None,
                'last_action_time': None,
                'actions_today': 0,
                'errors_today': 0
            }
        
        logger.info(f"All {len(self.agents)} agents initialized!")
    
    async def get_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        return {
            'status': 'running' if self.running else 'ready',
            'timestamp': datetime.now().isoformat(),
            'total_agents': len(self.agents),
            'agents': self.agent_status,
            'system_health': self._calculate_health()
        }
    
    def _calculate_health(self) -> str:
        """Calculate overall system health"""
        if not self.agent_status:
            return 'unknown'
        
        error_count = sum(1 for s in self.agent_status.values() if s['errors_today'] > 0)
        total_agents = len(self.agent_status)
        
        if error_count == 0:
            return 'excellent'
        elif error_count < total_agents * 0.2:
            return 'good'
        elif error_count < total_agents * 0.5:
            return 'fair'
        else:
            return 'poor'
    
    async def setup_store(self, store_name: str, niche: str, platforms: list, auto_mode: bool = True) -> Dict[str, Any]:
        """Initial store setup"""
        logger.info(f"Setting up store: {store_name} in niche: {niche}")
        
        # Update agent status
        for name in self.agents:
            self.agent_status[name]['status'] = 'configuring'
        
        # Configure each agent
        results = {}
        for name, agent in self.agents.items():
            try:
                if hasattr(agent, 'configure'):
                    result = await agent.configure({
                        'store_name': store_name,
                        'niche': niche,
                        'platforms': platforms,
                        'auto_mode': auto_mode
                    })
                    results[name] = result
                self.agent_status[name]['status'] = 'ready'
            except Exception as e:
                logger.error(f"Error configuring {name} agent: {e}")
                self.agent_status[name]['status'] = 'error'
                self.agent_status[name]['errors_today'] += 1
        
        logger.info("Store setup complete!")
        return {
            'store_name': store_name,
            'niche': niche,
            'platforms': platforms,
            'auto_mode': auto_mode,
            'agent_configs': results
        }
    
    async def generate_product(self, prompt: Optional[str] = None, use_trending: bool = True) -> Dict[str, Any]:
        """Generate a new product using the design agent"""
        self.agent_status['design']['status'] = 'working'
        self.agent_status['content_writer']['status'] = 'working'
        
        try:
            # Step 1: Generate design
            design_result = await self.agents['design'].generate_design(
                prompt=prompt,
                use_trending=use_trending
            )
            
            # Step 2: Generate product description
            description = await self.agents['content_writer'].write_product_description(
                product_name=design_result['name'],
                design_concept=design_result['concept'],
                niche=design_result.get('niche', 'general')
            )
            
            # Step 3: Calculate pricing
            pricing = await self.agents['pricing'].calculate_price(
                base_cost=design_result['base_cost'],
                niche=design_result.get('niche'),
                design_concept=design_result['concept']
            )
            
            product = {
                'name': design_result['name'],
                'description': description,
                'design_url': design_result['design_url'],
                'mockup_urls': design_result.get('mockup_urls', []),
                'base_cost': design_result['base_cost'],
                'sale_price': pricing['sale_price'],
                'profit_margin': pricing['profit_margin'],
                'tags': design_result.get('tags', []),
                'niche': design_result.get('niche', 'general'),
                'trending_score': design_result.get('trending_score', 0)
            }
            
            self.agent_status['design']['last_action'] = 'generated_product'
            self.agent_status['design']['last_action_time'] = datetime.now().isoformat()
            self.agent_status['design']['actions_today'] += 1
            
            return product
            
        except Exception as e:
            logger.error(f"Product generation error: {e}")
            self.agent_status['design']['errors_today'] += 1
            raise
        finally:
            self.agent_status['design']['status'] = 'idle'
            self.agent_status['content_writer']['status'] = 'idle'
    
    async def create_social_post(self, platform: str, content_type: str = 'product') -> Dict[str, Any]:
        """Create a social media post"""
        self.agent_status['social']['status'] = 'working'
        
        try:
            result = await self.agents['social'].create_post(
                platform=platform,
                content_type=content_type
            )
            
            self.agent_status['social']['last_action'] = f'posted_to_{platform}'
            self.agent_status['social']['last_action_time'] = datetime.now().isoformat()
            self.agent_status['social']['actions_today'] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Social post error: {e}")
            self.agent_status['social']['errors_today'] += 1
            raise
        finally:
            self.agent_status['social']['status'] = 'idle'
    
    async def get_profit_analytics(self) -> Dict[str, Any]:
        """Get profit analytics from all sources"""
        try:
            # Get fulfillment analytics
            fulfillment_data = await self.agents['fulfillment'].get_analytics()
            
            # Get social analytics
            social_data = await self.agents['social'].get_analytics()
            
            # Get affiliate analytics
            affiliate_data = await self.agents['affiliate'].get_analytics()
            
            # Get engagement analytics
            engagement_data = await self.agents['customer_engagement'].get_analytics()
            
            return {
                'fulfillment': fulfillment_data,
                'social': social_data,
                'affiliate': affiliate_data,
                'engagement': engagement_data,
                'summary': {
                    'total_revenue': fulfillment_data.get('total_revenue', 0),
                    'total_profit': fulfillment_data.get('total_profit', 0),
                    'total_orders': fulfillment_data.get('total_orders', 0),
                    'avg_order_value': fulfillment_data.get('avg_order_value', 0),
                    'social_reach': social_data.get('total_reach', 0),
                    'affiliate_sales': affiliate_data.get('total_sales', 0)
                }
            }
        except Exception as e:
            logger.error(f"Analytics error: {e}")
            return {'error': str(e)}
    
    async def manual_override(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Manual override for any agent action"""
        logger.info(f"Manual override: {action} with params: {params}")
        
        action_parts = action.split('_', 1)
        agent_name = action_parts[0]
        agent_action = action_parts[1] if len(action_parts) > 1 else 'execute'
        
        if agent_name not in self.agents:
            return {'error': f'Unknown agent: {agent_name}'}
        
        agent = self.agents[agent_name]
        
        # Check if agent has the requested action
        if hasattr(agent, agent_action):
            method = getattr(agent, agent_action)
            if callable(method):
                try:
                    result = await method(**params)
                    return {'success': True, 'result': result}
                except Exception as e:
                    logger.error(f"Override action error: {e}")
                    return {'error': str(e)}
        
        # Try generic execute method
        if hasattr(agent, 'execute'):
            try:
                result = await agent.execute(action=agent_action, **params)
                return {'success': True, 'result': result}
            except Exception as e:
                logger.error(f"Override execute error: {e}")
                return {'error': str(e)}
        
        return {'error': f'Action {agent_action} not found on agent {agent_name}'}
    
    async def run_auto_mode(self):
        """Run all agents in automatic mode"""
        self.running = True
        logger.info("Starting auto mode...")
        
        while self.running:
            try:
                # Check for new orders to fulfill
                await self.agents['fulfillment'].process_pending_orders()
                
                # Check for abandoned carts
                await self.agents['customer_engagement'].check_abandoned_carts()
                
                # Check for orders needing review requests
                await self.agents['customer_engagement'].send_review_requests()
                
                # Update order tracking
                await self.agents['fulfillment'].update_tracking()
                
                # Process chatbot messages
                await self.agents['customer_service'].process_pending_messages()
                
                # Run competitor spy (once per day)
                if datetime.now().hour == 2:  # 2 AM
                    await self.agents['competitor_spy'].spy_all_competitors()
                
                # Generate inventory predictions (once per day)
                if datetime.now().hour == 3:  # 3 AM
                    await self.agents['inventory_prediction'].predict_bestsellers()
                
                # Wait before next cycle
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Auto mode error: {e}")
                await asyncio.sleep(60)
    
    def stop_auto_mode(self):
        """Stop auto mode"""
        self.running = False
        logger.info("Auto mode stopped")
