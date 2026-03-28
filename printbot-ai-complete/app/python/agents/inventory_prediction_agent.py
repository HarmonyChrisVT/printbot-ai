"""
Inventory Prediction Agent - Predict bestsellers and optimize inventory
"""

import os
import random
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict

from python.utils.logger import get_logger
from database.models import get_db_session, Product, Order

logger = get_logger(__name__)

class InventoryPredictionAgent:
    """AI agent that predicts bestsellers and optimizes inventory"""
    
    def __init__(self):
        self.prediction_models = {}
    
    async def configure(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Configure the inventory prediction agent"""
        return {'status': 'configured'}
    
    async def predict_bestsellers(self, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """Predict which products will be bestsellers"""
        logger.info(f"Predicting bestsellers for next {days_ahead} days")
        
        session = get_db_session()
        try:
            # Get all products
            products = session.query(Product).all()
            
            predictions = []
            for product in products:
                # Calculate prediction score based on multiple factors
                score = self._calculate_bestseller_score(product)
                
                predictions.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'current_sales': product.times_sold,
                    'views': product.views,
                    'prediction_score': round(score, 2),
                    'predicted_sales_next_30d': int(score * 10),
                    'confidence': 'high' if score > 0.7 else 'medium' if score > 0.4 else 'low',
                    'recommendation': self._get_recommendation(score),
                    'trending': score > 0.6
                })
            
            # Sort by prediction score
            predictions.sort(key=lambda x: x['prediction_score'], reverse=True)
            
            return predictions[:20]  # Top 20 predictions
            
        finally:
            session.close()
    
    def _calculate_bestseller_score(self, product: Product) -> float:
        """Calculate bestseller prediction score"""
        score = 0.0
        
        # Factor 1: Current sales velocity
        if product.times_sold > 0:
            score += min(product.times_sold / 10, 0.3)
        
        # Factor 2: View-to-sale conversion
        if product.views > 0:
            conversion = product.times_sold / product.views
            score += min(conversion * 10, 0.25)
        
        # Factor 3: Trending score from design
        score += (product.trending_score or 0) * 0.2
        
        # Factor 4: Time since creation (newer products get boost)
        days_since_creation = (datetime.now() - product.created_at).days if product.created_at else 0
        if days_since_creation < 7:
            score += 0.15  # New product boost
        
        # Factor 5: Random market factor (simulates unpredictability)
        score += random.uniform(-0.1, 0.1)
        
        return max(0, min(1, score))
    
    def _get_recommendation(self, score: float) -> str:
        """Get recommendation based on score"""
        if score >= 0.7:
            return 'push_heavy'  # Promote heavily
        elif score >= 0.5:
            return 'push_moderate'  # Moderate promotion
        elif score >= 0.3:
            return 'monitor'  # Watch and wait
        else:
            return 'consider_removal'  # Low performer
    
    async def get_inventory_alerts(self) -> List[Dict[str, Any]]:
        """Get inventory alerts and recommendations"""
        session = get_db_session()
        try:
            products = session.query(Product).all()
            
            alerts = []
            for product in products:
                # Check if product needs attention
                days_since_sale = self._days_since_last_sale(product.id)
                
                if days_since_sale > 30 and product.views > 50:
                    alerts.append({
                        'product_id': product.id,
                        'product_name': product.name,
                        'alert_type': 'high_views_no_sales',
                        'message': f"Product has {product.views} views but no sales in 30 days",
                        'recommendation': 'Consider price reduction or better marketing',
                        'severity': 'medium'
                    })
                
                if product.times_sold > 10 and product.views < 50:
                    alerts.append({
                        'product_id': product.id,
                        'product_name': product.name,
                        'alert_type': 'good_conversion_low_traffic',
                        'message': 'Product converts well but needs more traffic',
                        'recommendation': 'Increase social media promotion',
                        'severity': 'low'
                    })
            
            return alerts
            
        finally:
            session.close()
    
    def _days_since_last_sale(self, product_id: int) -> int:
        """Get days since last sale for a product"""
        session = get_db_session()
        try:
            last_order = session.query(Order).filter_by(
                product_id=product_id
            ).order_by(Order.created_at.desc()).first()
            
            if last_order and last_order.created_at:
                return (datetime.now() - last_order.created_at).days
            return 999  # Never sold
        finally:
            session.close()
    
    async def get_category_performance(self) -> Dict[str, Any]:
        """Get performance by product category/niche"""
        session = get_db_session()
        try:
            products = session.query(Product).all()
            
            # Group by niche
            niche_stats = defaultdict(lambda: {'sales': 0, 'views': 0, 'products': 0})
            
            for product in products:
                niche = product.niche or 'uncategorized'
                niche_stats[niche]['sales'] += product.times_sold
                niche_stats[niche]['views'] += product.views
                niche_stats[niche]['products'] += 1
            
            # Calculate performance metrics
            performance = []
            for niche, stats in niche_stats.items():
                conversion = stats['sales'] / stats['views'] if stats['views'] > 0 else 0
                performance.append({
                    'niche': niche,
                    'total_products': stats['products'],
                    'total_sales': stats['sales'],
                    'total_views': stats['views'],
                    'conversion_rate': round(conversion * 100, 2),
                    'performance_score': round(stats['sales'] / max(stats['products'], 1), 2)
                })
            
            # Sort by performance
            performance.sort(key=lambda x: x['performance_score'], reverse=True)
            
            return {
                'categories': performance,
                'top_performer': performance[0] if performance else None,
                'underperformer': performance[-1] if performance else None
            }
            
        finally:
            session.close()
    
    async def get_restock_recommendations(self) -> List[Dict[str, Any]]:
        """Get recommendations for restocking/promoting"""
        bestsellers = await self.predict_bestsellers()
        
        recommendations = []
        for product in bestsellers[:10]:
            if product['prediction_score'] >= 0.6:
                recommendations.append({
                    'product_id': product['product_id'],
                    'product_name': product['product_name'],
                    'action': 'increase_promotion',
                    'priority': 'high' if product['prediction_score'] >= 0.8 else 'medium',
                    'expected_sales': product['predicted_sales_next_30d'],
                    'suggested_actions': [
                        'Feature on homepage',
                        'Increase social media posts',
                        'Run targeted ads',
                        'Offer limited-time discount'
                    ]
                })
        
        return recommendations
