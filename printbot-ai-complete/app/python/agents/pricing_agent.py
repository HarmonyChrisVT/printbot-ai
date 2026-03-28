"""
Pricing Agent - Dynamic pricing with competitor analysis
"""

import os
import random
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio

from python.utils.logger import get_logger

logger = get_logger(__name__)

class PricingAgent:
    """AI agent that sets optimal prices based on market analysis"""
    
    def __init__(self):
        self.min_margin = 0.25  # 25% minimum margin
        self.target_margin = 0.40  # 40% target margin
        self.max_margin = 0.65  # 65% maximum margin
        self.psychological_prices = [19.99, 24.99, 29.99, 34.99, 39.99, 44.99, 49.99]
    
    async def configure(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Configure the pricing agent"""
        self.min_margin = config.get('min_margin', 0.25)
        self.target_margin = config.get('target_margin', 0.40)
        return {'status': 'configured'}
    
    async def calculate_price(
        self, 
        base_cost: float, 
        niche: Optional[str] = None,
        design_concept: Optional[str] = None,
        competitor_prices: Optional[list] = None
    ) -> Dict[str, Any]:
        """Calculate optimal sale price"""
        
        logger.info(f"Calculating price for item with base cost: ${base_cost}")
        
        # Start with target margin
        target_price = base_cost / (1 - self.target_margin)
        
        # Adjust based on niche
        niche_multiplier = self._get_niche_multiplier(niche)
        adjusted_price = target_price * niche_multiplier
        
        # Check competitor prices if available
        if competitor_prices:
            avg_competitor = sum(competitor_prices) / len(competitor_prices)
            # Price slightly below average competitor
            adjusted_price = min(adjusted_price, avg_competitor * 0.95)
        
        # Apply psychological pricing
        final_price = self._apply_psychological_pricing(adjusted_price)
        
        # Calculate actual margin
        profit = final_price - base_cost
        margin = profit / final_price
        
        # Ensure minimum margin
        if margin < self.min_margin:
            final_price = base_cost / (1 - self.min_margin)
            final_price = self._apply_psychological_pricing(final_price)
            profit = final_price - base_cost
            margin = profit / final_price
        
        result = {
            'base_cost': round(base_cost, 2),
            'sale_price': round(final_price, 2),
            'profit': round(profit, 2),
            'profit_margin': round(margin, 4),
            'profit_percentage': round(margin * 100, 1),
            'niche_adjustment': niche_multiplier,
            'pricing_strategy': self._get_pricing_strategy(margin),
            'recommended_discount_price': round(final_price * 0.85, 2),
            'flash_sale_price': round(final_price * 0.70, 2),
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Price calculated: ${result['sale_price']} (margin: {result['profit_percentage']}%)")
        return result
    
    def _get_niche_multiplier(self, niche: Optional[str]) -> float:
        """Get price multiplier based on niche"""
        multipliers = {
            'luxury': 1.5,
            'fitness': 1.2,
            'gaming': 1.15,
            'pets': 1.25,
            'family': 1.1,
            'career': 1.15,
            'hobbies': 1.1,
            'travel': 1.2,
            'food': 1.05,
            'music': 1.15
        }
        return multipliers.get(niche, 1.0)
    
    def _apply_psychological_pricing(self, price: float) -> float:
        """Apply psychological pricing (e.g., $29.99 instead of $30)"""
        # Find nearest psychological price
        for psych_price in self.psychological_prices:
            if price <= psych_price:
                return psych_price
        
        # If above all, use .99 ending
        return int(price) - 0.01
    
    def _get_pricing_strategy(self, margin: float) -> str:
        """Determine pricing strategy based on margin"""
        if margin >= 0.50:
            return 'premium'
        elif margin >= 0.35:
            return 'standard'
        elif margin >= 0.25:
            return 'competitive'
        else:
            return 'aggressive'
    
    async def analyze_competitors(self, product_name: str, niche: str) -> Dict[str, Any]:
        """Analyze competitor pricing"""
        logger.info(f"Analyzing competitors for: {product_name}")
        
        # In production, this would scrape competitor sites
        # For now, return simulated data
        
        simulated_prices = {
            't-shirt': [24.99, 27.99, 22.99, 29.99, 25.99],
            'hoodie': [44.99, 49.99, 42.99, 54.99, 47.99],
            'mug': [14.99, 16.99, 12.99, 18.99, 15.99]
        }
        
        # Extract product type from name
        product_type = 't-shirt'  # default
        for pt in simulated_prices.keys():
            if pt in product_name.lower():
                product_type = pt
                break
        
        prices = simulated_prices.get(product_type, [24.99, 27.99, 22.99])
        
        return {
            'product_type': product_type,
            'competitor_prices': prices,
            'average_price': round(sum(prices) / len(prices), 2),
            'lowest_price': min(prices),
            'highest_price': max(prices),
            'recommended_position': 'middle',  # low, middle, high
            'timestamp': datetime.now().isoformat()
        }
    
    async def suggest_flash_sale(
        self, 
        product_id: int, 
        current_price: float,
        inventory_level: str = 'normal'
    ) -> Dict[str, Any]:
        """Suggest flash sale pricing"""
        
        # Different discounts based on inventory
        discounts = {
            'overstock': 0.50,  # 50% off
            'high': 0.35,       # 35% off
            'normal': 0.25,     # 25% off
            'low': 0.15         # 15% off
        }
        
        discount = discounts.get(inventory_level, 0.25)
        sale_price = current_price * (1 - discount)
        
        return {
            'original_price': round(current_price, 2),
            'sale_price': round(sale_price, 2),
            'discount_percentage': int(discount * 100),
            'discount_amount': round(current_price - sale_price, 2),
            'inventory_level': inventory_level,
            'urgency_level': 'high' if inventory_level == 'overstock' else 'medium',
            'recommended_duration_hours': 24 if inventory_level == 'overstock' else 48
        }
