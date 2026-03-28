"""
Fulfillment Agent - Multi-provider order fulfillment with failover
"""

import os
import random
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from python.integrations.fulfillment_providers import FulfillmentProviderChain
from python.utils.logger import get_logger
from database.models import get_db_session, Order, Product

logger = get_logger(__name__)

class FulfillmentAgent:
    """AI agent that handles order fulfillment with multi-provider failover"""
    
    def __init__(self):
        self.provider_chain = FulfillmentProviderChain()
        self.providers = ['printful', 'printify', 'gelato', 'gooten']
        self.order_queue = []
    
    async def configure(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Configure the fulfillment agent"""
        # Setup API keys for each provider
        for provider in self.providers:
            key = config.get(f'{provider}_api_key')
            if key:
                self.provider_chain.set_api_key(provider, key)
        
        return {
            'status': 'configured',
            'providers': self.providers,
            'primary': 'printful'
        }
    
    async def process_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single order with failover"""
        logger.info(f"Processing order: {order_data.get('order_number')}")
        
        order_number = order_data.get('order_number')
        product_id = order_data.get('product_id')
        
        # Get product details
        session = get_db_session()
        try:
            product = session.query(Product).filter_by(id=product_id).first()
            if not product:
                return {'error': 'Product not found'}
            
            # Try each provider in sequence
            for provider in self.providers:
                try:
                    result = await self._submit_to_provider(provider, order_data, product)
                    
                    if result.get('success'):
                        # Update order in database
                        order = session.query(Order).filter_by(order_number=order_number).first()
                        if order:
                            order.status = 'processing'
                            order.provider = provider
                            order.updated_at = datetime.now()
                            session.commit()
                        
                        logger.info(f"Order {order_number} submitted to {provider}")
                        return {
                            'success': True,
                            'provider': provider,
                            'order_id': result.get('order_id'),
                            'estimated_ship_date': result.get('estimated_ship_date')
                        }
                    
                except Exception as e:
                    logger.warning(f"Provider {provider} failed: {e}")
                    continue
            
            # All providers failed
            logger.error(f"All providers failed for order {order_number}")
            return {'error': 'All fulfillment providers unavailable'}
            
        finally:
            session.close()
    
    async def _submit_to_provider(
        self, 
        provider: str, 
        order_data: Dict, 
        product: Product
    ) -> Dict[str, Any]:
        """Submit order to a specific provider"""
        # In production, this would make actual API calls
        # Simulate provider submission
        
        # Simulate occasional failure (10% chance)
        if random.random() < 0.1:
            raise Exception(f"{provider} API error")
        
        return {
            'success': True,
            'order_id': f"{provider}_{random.randint(100000, 999999)}",
            'estimated_ship_date': (datetime.now() + timedelta(days=3, hours=random.randint(0, 24))).isoformat()
        }
    
    async def process_pending_orders(self) -> Dict[str, Any]:
        """Process all pending orders"""
        session = get_db_session()
        try:
            pending_orders = session.query(Order).filter_by(status='pending').all()
            
            results = []
            for order in pending_orders:
                result = await self.process_order({
                    'order_number': order.order_number,
                    'product_id': order.product_id,
                    'customer_email': order.customer_email,
                    'customer_name': order.customer_name,
                    'shipping_address': order.shipping_address,
                    'quantity': order.quantity
                })
                results.append({
                    'order_number': order.order_number,
                    'result': result
                })
            
            return {
                'processed': len(results),
                'successful': len([r for r in results if r['result'].get('success')]),
                'failed': len([r for r in results if not r['result'].get('success')]),
                'details': results
            }
        finally:
            session.close()
    
    async def update_tracking(self) -> Dict[str, Any]:
        """Update tracking information for shipped orders"""
        session = get_db_session()
        try:
            processing_orders = session.query(Order).filter(
                Order.status.in_(['processing', 'shipped'])
            ).all()
            
            updated = 0
            for order in processing_orders:
                # Simulate tracking update
                if order.status == 'processing' and random.random() < 0.3:
                    # 30% chance order ships
                    order.status = 'shipped'
                    order.tracking_number = f"TRK{random.randint(100000000, 999999999)}"
                    order.tracking_url = f"https://track.example.com/{order.tracking_number}"
                    order.shipped_at = datetime.now()
                    updated += 1
                    
                    # Send tracking notification
                    await self._send_tracking_notification(order)
                    
                elif order.status == 'shipped' and random.random() < 0.2:
                    # 20% chance order delivers
                    order.status = 'delivered'
                    order.delivered_at = datetime.now()
                    updated += 1
            
            session.commit()
            
            return {
                'checked': len(processing_orders),
                'updated': updated
            }
        finally:
            session.close()
    
    async def _send_tracking_notification(self, order: Order):
        """Send tracking notification to customer"""
        logger.info(f"Sending tracking notification to {order.customer_email}")
        # In production, integrate with email service
    
    async def get_analytics(self) -> Dict[str, Any]:
        """Get fulfillment analytics"""
        session = get_db_session()
        try:
            total_orders = session.query(Order).count()
            pending = session.query(Order).filter_by(status='pending').count()
            processing = session.query(Order).filter_by(status='processing').count()
            shipped = session.query(Order).filter_by(status='shipped').count()
            delivered = session.query(Order).filter_by(status='delivered').count()
            
            total_revenue = session.query(Order).filter(
                Order.status.in_(['shipped', 'delivered'])
            ).with_entities(Order.total_amount).all()
            total_revenue = sum([r[0] for r in total_revenue]) if total_revenue else 0
            
            total_profit = session.query(Order).filter(
                Order.status.in_(['shipped', 'delivered'])
            ).with_entities(Order.profit).all()
            total_profit = sum([p[0] for p in total_profit]) if total_profit else 0
            
            avg_order = total_revenue / delivered if delivered > 0 else 0
            
            return {
                'total_orders': total_orders,
                'pending': pending,
                'processing': processing,
                'shipped': shipped,
                'delivered': delivered,
                'total_revenue': round(total_revenue, 2),
                'total_profit': round(total_profit, 2),
                'avg_order_value': round(avg_order, 2),
                'profit_margin': round(total_profit / total_revenue * 100, 1) if total_revenue > 0 else 0
            }
        finally:
            session.close()
    
    async def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all fulfillment providers"""
        return {
            provider: {
                'status': 'operational' if random.random() > 0.1 else 'degraded',
                'avg_fulfillment_time': f"{random.randint(2, 5)} days",
                'success_rate': f"{random.randint(95, 99)}%"
            }
            for provider in self.providers
        }
