"""
PrintBot AI - Inventory Prediction Agent
=========================================
Predicts which designs will sell out
Auto-creates similar designs for bestsellers
Schedule: Daily analysis
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import statistics
import json

from config.settings import config
from database.models import Product, Sale, Design, AgentLog, get_session


@dataclass
class ProductPrediction:
    """Prediction for a product"""
    product_id: int
    product_name: str
    current_inventory: int
    daily_sales_rate: float
    days_until_stockout: float
    confidence: float
    recommendation: str  # 'reorder', 'create_similar', 'discount', 'monitor'
    predicted_demand_30d: int


class SalesForecaster:
    """Forecast future sales based on historical data"""
    
    def __init__(self, db_session):
        self.session = db_session
    
    def forecast_sales(self, product_id: int, days_ahead: int = 30) -> Dict:
        """Forecast sales for a product"""
        # Get historical sales
        sales = self.session.query(Sale).filter(
            Sale.product_id == product_id,
            Sale.sale_date >= datetime.utcnow() - timedelta(days=60)
        ).order_by(Sale.sale_date).all()
        
        if not sales:
            return {'forecast': 0, 'confidence': 0, 'trend': 'unknown'}
        
        # Calculate daily sales
        daily_sales = {}
        for sale in sales:
            day = sale.sale_date.date()
            daily_sales[day] = daily_sales.get(day, 0) + sale.quantity
        
        # Calculate metrics
        quantities = list(daily_sales.values())
        avg_daily = statistics.mean(quantities) if quantities else 0
        
        # Detect trend
        if len(quantities) >= 14:
            recent = statistics.mean(quantities[-7:])
            older = statistics.mean(quantities[-14:-7])
            trend = (recent - older) / older if older > 0 else 0
        else:
            trend = 0
        
        # Forecast with trend
        forecast = avg_daily * days_ahead * (1 + trend * 0.5)
        
        # Confidence based on data availability
        confidence = min(len(sales) / 30, 1.0)
        
        return {
            'forecast': max(0, round(forecast)),
            'daily_rate': avg_daily,
            'confidence': confidence,
            'trend': 'up' if trend > 0.1 else 'down' if trend < -0.1 else 'stable',
            'trend_strength': abs(trend)
        }


class SimilarDesignGenerator:
    """Generate similar designs for bestsellers"""
    
    def __init__(self, db_session):
        self.session = db_session
    
    def generate_variations(self, original_design_id: int, num_variations: int = 3) -> List[Dict]:
        """Generate design variations"""
        original = self.session.query(Design).get(original_design_id)
        if not original:
            return []
        
        variations = []
        
        # Variation strategies
        strategies = [
            {'modifier': 'alternative color scheme', 'suffix': ' (Color Variant)'},
            {'modifier': 'minimalist version', 'suffix': ' (Minimalist)'},
            {'modifier': 'vintage distressed style', 'suffix': ' (Vintage)'},
            {'modifier': 'bold typography focus', 'suffix': ' (Bold)'},
            {'modifier': 'pastel color palette', 'suffix': ' (Pastel)'},
        ]
        
        for i in range(min(num_variations, len(strategies))):
            strategy = strategies[i]
            
            new_prompt = f"{original.prompt}, {strategy['modifier']}"
            
            variation = {
                'prompt': new_prompt,
                'title_suffix': strategy['suffix'],
                'based_on_design_id': original_design_id,
                'variation_type': strategy['modifier']
            }
            
            variations.append(variation)
        
        return variations


class InventoryPredictionAgent:
    """
    Inventory Prediction Agent
    Predicts stockouts and recommends actions
    """
    
    def __init__(self, db_session):
        self.session = db_session
        self.forecaster = SalesForecaster(db_session)
        self.design_generator = SimilarDesignGenerator(db_session)
        self.running = False
        
        # Thresholds
        self.stockout_warning_days = 7
        self.bestseller_threshold = 10  # Sales in last 30 days
    
    async def run(self):
        """Main agent loop"""
        self.running = True
        print("📊 Inventory Prediction Agent started")
        
        while self.running:
            try:
                await self._analyze_inventory()
                await asyncio.sleep(24 * 3600)  # Daily
                
            except Exception as e:
                self._log_error(f"Prediction agent error: {e}")
                await asyncio.sleep(3600)
    
    async def _analyze_inventory(self):
        """Analyze all products for predictions"""
        print("\n📊 Running inventory prediction analysis...")
        
        products = self.session.query(Product).filter(
            Product.is_active == True
        ).all()
        
        predictions = []
        bestsellers = []
        slow_movers = []
        
        for product in products:
            prediction = self._predict_product(product)
            predictions.append(prediction)
            
            # Categorize
            if prediction.recommendation == 'create_similar':
                bestsellers.append(prediction)
            elif prediction.recommendation == 'discount':
                slow_movers.append(prediction)
        
        # Generate report
        await self._generate_prediction_report(predictions, bestsellers, slow_movers)
        
        # Take actions
        if bestsellers:
            await self._create_similar_designs(bestsellers)
        
        if slow_movers:
            await self._recommend_discounts(slow_movers)
    
    def _predict_product(self, product: Product) -> ProductPrediction:
        """Generate prediction for a single product"""
        # Get sales forecast
        forecast = self.forecaster.forecast_sales(product.id, 30)
        
        # Get current inventory
        inventory = sum(v.inventory_quantity for v in product.variants) if product.variants else 100
        
        # Calculate days until stockout
        daily_rate = forecast['daily_rate']
        days_until_stockout = inventory / daily_rate if daily_rate > 0 else float('inf')
        
        # Determine recommendation
        if days_until_stockout < self.stockout_warning_days and forecast['confidence'] > 0.5:
            recommendation = 'reorder'
        elif forecast['forecast'] > self.bestseller_threshold and forecast['trend'] == 'up':
            recommendation = 'create_similar'
        elif forecast['forecast'] < 3 and forecast['confidence'] > 0.3:
            recommendation = 'discount'
        else:
            recommendation = 'monitor'
        
        return ProductPrediction(
            product_id=product.id,
            product_name=product.title,
            current_inventory=inventory,
            daily_sales_rate=daily_rate,
            days_until_stockout=days_until_stockout,
            confidence=forecast['confidence'],
            recommendation=recommendation,
            predicted_demand_30d=forecast['forecast']
        )
    
    async def _generate_prediction_report(
        self,
        predictions: List[ProductPrediction],
        bestsellers: List[ProductPrediction],
        slow_movers: List[ProductPrediction]
    ):
        """Generate and send prediction report"""
        print("\n📈 Inventory Prediction Report")
        print("-" * 50)
        
        # Stockout warnings
        stockout_soon = [p for p in predictions if p.days_until_stockout < 7]
        if stockout_soon:
            print(f"\n⚠️  Stockout Warning ({len(stockout_soon)} products):")
            for p in stockout_soon[:5]:
                print(f"   • {p.product_name}: {p.days_until_stockout:.1f} days left")
        
        # Bestsellers
        if bestsellers:
            print(f"\n🔥 Bestsellers ({len(bestsellers)} products):")
            for p in bestsellers[:5]:
                print(f"   • {p.product_name}: {p.predicted_demand_30d} predicted sales")
        
        # Slow movers
        if slow_movers:
            print(f"\n🐌 Slow Movers ({len(slow_movers)} products):")
            for p in slow_movers[:5]:
                print(f"   • {p.product_name}: Consider discounting")
    
    async def _create_similar_designs(self, bestsellers: List[ProductPrediction]):
        """Auto-create similar designs for bestsellers"""
        print(f"\n🎨 Creating similar designs for {len(bestsellers)} bestsellers...")
        
        for prediction in bestsellers[:3]:  # Top 3
            product = self.session.query(Product).get(prediction.product_id)
            if product and product.design_id:
                variations = self.design_generator.generate_variations(product.design_id, 2)
                
                print(f"   📦 {product.title}:")
                for var in variations:
                    print(f"      → {var['variation_type']}")
                    # Would queue for design agent to create
    
    async def _recommend_discounts(self, slow_movers: List[ProductPrediction]):
        """Recommend discounts for slow-moving products"""
        print(f"\n💰 Discount Recommendations ({len(slow_movers)} products):")
        
        for prediction in slow_movers[:5]:
            product = self.session.query(Product).get(prediction.product_id)
            if product:
                suggested_discount = 0.20  # 20% off
                new_price = product.selling_price * (1 - suggested_discount)
                
                print(f"   • {product.title}: ${product.selling_price} → ${new_price:.2f} (20% off)")
    
    def get_prediction_summary(self) -> Dict:
        """Get summary of all predictions"""
        products = self.session.query(Product).filter(Product.is_active == True).all()
        
        predictions = [self._predict_product(p) for p in products]
        
        return {
            'total_products': len(predictions),
            'stockout_warnings': len([p for p in predictions if p.days_until_stockout < 7]),
            'bestsellers': len([p for p in predictions if p.recommendation == 'create_similar']),
            'slow_movers': len([p for p in predictions if p.recommendation == 'discount']),
            'avg_confidence': statistics.mean([p.confidence for p in predictions]) if predictions else 0
        }
    
    def _log_action(self, action: str, status: str, details: Dict):
        """Log agent action"""
        log = AgentLog(
            agent_name='inventory_prediction',
            action=action,
            status=status,
            details=details
        )
        self.session.add(log)
        self.session.commit()
    
    def _log_error(self, message: str):
        """Log error"""
        self._log_action("error", "error", {"message": message})
        print(f"❌ {message}")
    
    def stop(self):
        """Stop the agent"""
        self.running = False
        print("🛑 Inventory Prediction Agent stopped")


# Standalone run
async def run_inventory_prediction_agent():
    """Run prediction agent standalone"""
    from database.models import init_database
    from config.settings import config
    
    engine = init_database(config.database_path)
    session = get_session(engine)
    
    agent = InventoryPredictionAgent(session)
    await agent.run()


if __name__ == "__main__":
    asyncio.run(run_inventory_prediction_agent())
