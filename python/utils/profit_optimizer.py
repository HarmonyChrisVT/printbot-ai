"""
PrintBot AI - Profit Optimizer
===============================
Advanced profit optimization strategies
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import statistics

from database.models import Product, Sale, Order, AnalyticsDaily, get_session
from config.settings import config


@dataclass
class ProfitRecommendation:
    """Profit optimization recommendation"""
    product_id: int
    current_price: float
    recommended_price: float
    expected_margin: float
    confidence: float
    reason: str
    action: str  # 'increase', 'decrease', 'bundle', 'promote'


class DemandForecaster:
    """Forecast demand based on historical data and trends"""
    
    def __init__(self, db_session):
        self.session = db_session
    
    def forecast_demand(self, product_id: int, days_ahead: int = 7) -> Dict:
        """Forecast demand for a product"""
        # Get historical sales
        sales = self.session.query(Sale).filter(
            Sale.product_id == product_id
        ).order_by(Sale.sale_date.desc()).limit(30).all()
        
        if not sales:
            return {'forecast': 0, 'confidence': 0}
        
        # Simple moving average
        quantities = [s.quantity for s in sales]
        avg_daily = statistics.mean(quantities) if quantities else 0
        
        # Trend detection
        if len(quantities) >= 7:
            recent = statistics.mean(quantities[:7])
            older = statistics.mean(quantities[7:14]) if len(quantities) >= 14 else recent
            trend = (recent - older) / older if older > 0 else 0
        else:
            trend = 0
        
        # Forecast with trend
        forecast = avg_daily * days_ahead * (1 + trend)
        
        # Confidence based on data availability
        confidence = min(len(sales) / 30, 1.0)
        
        return {
            'forecast': max(0, round(forecast)),
            'confidence': confidence,
            'trend': trend,
            'avg_daily': avg_daily
        }


class PriceElasticityAnalyzer:
    """Analyze price elasticity for optimal pricing"""
    
    def __init__(self, db_session):
        self.session = db_session
    
    def analyze_elasticity(self, product_id: int) -> Dict:
        """Analyze price elasticity for a product"""
        # Get price history and corresponding sales
        sales = self.session.query(Sale).filter(
            Sale.product_id == product_id
        ).order_by(Sale.sale_date).all()
        
        if len(sales) < 5:
            return {'elasticity': -1.0, 'confidence': 0.3}
        
        # Calculate price elasticity
        # Formula: % change in quantity / % change in price
        price_changes = []
        quantity_changes = []
        
        for i in range(1, len(sales)):
            prev_price = sales[i-1].revenue / sales[i-1].quantity if sales[i-1].quantity > 0 else 0
            curr_price = sales[i].revenue / sales[i].quantity if sales[i].quantity > 0 else 0
            
            if prev_price > 0 and curr_price > 0:
                price_change = (curr_price - prev_price) / prev_price
                qty_change = (sales[i].quantity - sales[i-1].quantity) / sales[i-1].quantity if sales[i-1].quantity > 0 else 0
                
                if price_change != 0:
                    elasticity = qty_change / price_change
                    price_changes.append(price_change)
                    quantity_changes.append(elasticity)
        
        if quantity_changes:
            avg_elasticity = statistics.mean(quantity_changes)
            confidence = min(len(quantity_changes) / 10, 1.0)
        else:
            avg_elasticity = -1.0  # Default: unit elastic
            confidence = 0.3
        
        return {
            'elasticity': avg_elasticity,
            'confidence': confidence,
            'is_elastic': abs(avg_elasticity) > 1
        }


class BundleOptimizer:
    """Optimize bundle offerings for increased AOV"""
    
    def __init__(self, db_session):
        self.session = db_session
    
    def find_bundle_opportunities(self) -> List[Dict]:
        """Find products that are frequently bought together"""
        # Get orders with multiple items
        from database.models import Order, OrderItem
        
        orders = self.session.query(Order).all()
        
        # Build co-occurrence matrix
        product_pairs = {}
        
        for order in orders:
            items = order.items
            if len(items) > 1:
                product_ids = [item.product_id for item in items if item.product_id]
                
                for i, pid1 in enumerate(product_ids):
                    for pid2 in product_ids[i+1:]:
                        pair = tuple(sorted([pid1, pid2]))
                        product_pairs[pair] = product_pairs.get(pair, 0) + 1
        
        # Find top pairs
        sorted_pairs = sorted(product_pairs.items(), key=lambda x: x[1], reverse=True)
        
        opportunities = []
        for (pid1, pid2), count in sorted_pairs[:5]:
            p1 = self.session.query(Product).get(pid1)
            p2 = self.session.query(Product).get(pid2)
            
            if p1 and p2:
                combined_price = p1.selling_price + p2.selling_price
                bundle_price = combined_price * (1 - config.pricing.bundle_discount)
                
                opportunities.append({
                    'product_1': p1,
                    'product_2': p2,
                    'times_bought_together': count,
                    'combined_price': combined_price,
                    'bundle_price': bundle_price,
                    'customer_savings': combined_price - bundle_price
                })
        
        return opportunities


class SeasonalAnalyzer:
    """Analyze seasonal trends for timing optimizations"""
    
    def __init__(self, db_session):
        self.session = db_session
    
    def get_seasonal_insights(self) -> Dict:
        """Get current seasonal insights"""
        now = datetime.utcnow()
        month = now.month
        
        # Define seasons
        seasons = {
            'winter': [12, 1, 2],
            'spring': [3, 4, 5],
            'summer': [6, 7, 8],
            'fall': [9, 10, 11]
        }
        
        current_season = next(s for s, months in seasons.items() if month in months)
        
        # Seasonal recommendations
        seasonal_trends = {
            'winter': {
                'trending': ['holiday gifts', 'cozy', 'new year', 'warmth'],
                'colors': ['red', 'green', 'gold', 'white'],
                'events': ['Christmas', 'New Year', "Valentine's Day"]
            },
            'spring': {
                'trending': ['fresh start', 'flowers', 'outdoors', 'fitness'],
                'colors': ['pastel', 'green', 'yellow', 'pink'],
                'events': ['Easter', 'Mother\'s Day', 'Spring Break']
            },
            'summer': {
                'trending': ['vacation', 'beach', 'sun', 'adventure'],
                'colors': ['bright', 'blue', 'orange', 'yellow'],
                'events': ['Summer Break', '4th of July', 'Back to School']
            },
            'fall': {
                'trending': ['cozy', 'pumpkin', 'halloween', 'thankful'],
                'colors': ['orange', 'brown', 'burgundy', 'gold'],
                'events': ['Halloween', 'Thanksgiving', 'Black Friday']
            }
        }
        
        return {
            'current_season': current_season,
            'trending_keywords': seasonal_trends[current_season]['trending'],
            'trending_colors': seasonal_trends[current_season]['colors'],
            'upcoming_events': seasonal_trends[current_season]['events']
        }


class ProfitOptimizer:
    """
    Main Profit Optimizer
    Combines all optimization strategies
    """
    
    def __init__(self, db_session):
        self.session = db_session
        self.demand_forecaster = DemandForecaster(db_session)
        self.elasticity_analyzer = PriceElasticityAnalyzer(db_session)
        self.bundle_optimizer = BundleOptimizer(db_session)
        self.seasonal_analyzer = SeasonalAnalyzer(db_session)
    
    def generate_recommendations(self) -> List[ProfitRecommendation]:
        """Generate profit optimization recommendations"""
        recommendations = []
        
        # Get all active products
        products = self.session.query(Product).filter(
            Product.is_active == True
        ).all()
        
        for product in products:
            # Analyze elasticity
            elasticity = self.elasticity_analyzer.analyze_elasticity(product.id)
            
            # Forecast demand
            demand = self.demand_forecaster.forecast_demand(product.id)
            
            # Generate recommendation based on analysis
            rec = self._create_recommendation(product, elasticity, demand)
            if rec:
                recommendations.append(rec)
        
        # Sort by expected impact
        recommendations.sort(key=lambda r: r.confidence * abs(r.recommended_price - r.current_price), reverse=True)
        
        return recommendations[:10]  # Top 10 recommendations
    
    def _create_recommendation(
        self,
        product: Product,
        elasticity: Dict,
        demand: Dict
    ) -> Optional[ProfitRecommendation]:
        """Create a recommendation for a product"""
        current_price = product.selling_price or 0
        cost_price = product.cost_price or 0
        
        if current_price == 0 or cost_price == 0:
            return None
        
        current_margin = (current_price - cost_price) / current_price
        
        # Determine recommendation
        if demand['trend'] > 0.2 and elasticity['elasticity'] > -0.8:
            # High demand, inelastic - can increase price
            recommended_price = current_price * 1.1
            action = 'increase'
            reason = f"High demand trend (+{demand['trend']*100:.0f}%) with inelastic pricing"
        
        elif demand['trend'] < -0.2:
            # Declining demand - consider promotion
            recommended_price = current_price * 0.95
            action = 'promote'
            reason = f"Declining demand ({demand['trend']*100:.0f}%) - promotional pricing recommended"
        
        elif elasticity['is_elastic'] and current_margin > 0.35:
            # Elastic demand, high margin - reduce price to increase volume
            recommended_price = current_price * 0.95
            action = 'decrease'
            reason = "Elastic demand - price reduction should increase volume"
        
        else:
            # No change needed
            return None
        
        # Ensure floor margin
        min_price = cost_price / (1 - config.pricing.floor_margin)
        recommended_price = max(recommended_price, min_price)
        
        # Calculate expected margin
        expected_margin = (recommended_price - cost_price) / recommended_price
        
        return ProfitRecommendation(
            product_id=product.id,
            current_price=current_price,
            recommended_price=round(recommended_price, 2),
            expected_margin=expected_margin,
            confidence=elasticity['confidence'] * demand['confidence'],
            reason=reason,
            action=action
        )
    
    def get_bundle_recommendations(self) -> List[Dict]:
        """Get bundle optimization recommendations"""
        return self.bundle_optimizer.find_bundle_opportunities()
    
    def get_seasonal_recommendations(self) -> Dict:
        """Get seasonal optimization recommendations"""
        return self.seasonal_analyzer.get_seasonal_insights()
    
    def calculate_profit_potential(self) -> Dict:
        """Calculate profit potential from optimizations"""
        recommendations = self.generate_recommendations()
        
        current_profit = 0
        potential_profit = 0
        
        for rec in recommendations:
            # Estimate daily sales
            demand = self.demand_forecaster.forecast_demand(rec.product_id, 1)
            daily_sales = demand['forecast']
            
            current_daily = daily_sales * (rec.current_price - (rec.current_price * (1 - rec.expected_margin)))
            potential_daily = daily_sales * (rec.recommended_price - (rec.recommended_price * (1 - rec.expected_margin)))
            
            current_profit += current_daily
            potential_profit += potential_daily
        
        return {
            'current_daily_profit': round(current_profit, 2),
            'potential_daily_profit': round(potential_profit, 2),
            'improvement': round((potential_profit - current_profit) / current_profit * 100, 1) if current_profit > 0 else 0,
            'recommendation_count': len(recommendations)
        }
