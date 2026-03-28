"""
PrintBot AI - Competitor Spy Agent
===================================
Monitors competitor stores for trending designs and new products
Alerts when competitors add successful designs
Schedule: Every 12 hours
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
import json
import re
import hashlib

from ..config.settings import config
from ..database.models import AgentLog, get_session


@dataclass
class CompetitorProduct:
    """Competitor product data"""
    store_name: str
    product_url: str
    title: str
    price: float
    image_url: str
    first_seen: datetime
    last_seen: datetime
    estimated_sales: int = 0
    trend_score: float = 0.0


class CompetitorStoreMonitor:
    """Monitor a single competitor store"""
    
    def __init__(self, store_url: str, store_name: str):
        self.store_url = store_url
        self.store_name = store_name
        self.known_products: Set[str] = set()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    async def scan_store(self) -> List[CompetitorProduct]:
        """Scan store for products"""
        products = []
        
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(self.store_url, timeout=30) as response:
                    if response.status == 200:
                        html = await response.text()
                        products = self._extract_products(html)
        except Exception as e:
            print(f"❌ Error scanning {self.store_name}: {e}")
        
        return products
    
    def _extract_products(self, html: str) -> List[CompetitorProduct]:
        """Extract products from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        products = []
        
        # Common Shopify product selectors
        product_selectors = [
            '.product-card',
            '.product-item',
            '[data-product]',
            '.grid__item',
            '.product-grid-item'
        ]
        
        for selector in product_selectors:
            elements = soup.select(selector)
            for elem in elements[:20]:  # Limit to 20 products
                product = self._parse_product_element(elem)
                if product:
                    products.append(product)
        
        return products
    
    def _parse_product_element(self, elem) -> Optional[CompetitorProduct]:
        """Parse a single product element"""
        try:
            # Extract title
            title_elem = elem.select_one('.product-title, .product-card__title, h2, h3, .title')
            title = title_elem.get_text().strip() if title_elem else "Unknown"
            
            # Extract price
            price_elem = elem.select_one('.price, .product-price, .money')
            price = self._parse_price(price_elem.get_text() if price_elem else "0")
            
            # Extract image
            img_elem = elem.select_one('img')
            image_url = img_elem.get('src', '') if img_elem else ''
            
            # Extract URL
            link_elem = elem.select_one('a')
            product_url = link_elem.get('href', '') if link_elem else ''
            
            # Create product ID from URL
            product_id = hashlib.md5(product_url.encode()).hexdigest()[:12]
            
            return CompetitorProduct(
                store_name=self.store_name,
                product_url=product_url,
                title=title,
                price=price,
                image_url=image_url,
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow()
            )
            
        except Exception as e:
            return None
    
    def _parse_price(self, price_text: str) -> float:
        """Parse price from text"""
        cleaned = re.sub(r'[^\d.,]', '', price_text)
        try:
            return float(cleaned.replace(',', ''))
        except:
            return 0.0
    
    def detect_new_products(self, products: List[CompetitorProduct]) -> List[CompetitorProduct]:
        """Detect products we haven't seen before"""
        new_products = []
        
        for product in products:
            product_id = hashlib.md5(product.product_url.encode()).hexdigest()[:12]
            
            if product_id not in self.known_products:
                new_products.append(product)
                self.known_products.add(product_id)
        
        return new_products


class TrendAnalyzer:
    """Analyze competitor trends"""
    
    def __init__(self):
        self.trending_themes = {}
    
    def analyze_products(self, products: List[CompetitorProduct]) -> Dict:
        """Analyze products for trends"""
        # Extract common words/themes
        all_titles = ' '.join([p.title for p in products]).lower()
        words = re.findall(r'\b[a-z]{4,}\b', all_titles)
        
        # Count word frequency
        word_counts = {}
        for word in words:
            if word not in ['this', 'that', 'with', 'from', 'your', 'have']:
                word_counts[word] = word_counts.get(word, 0) + 1
        
        # Get top themes
        top_themes = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Analyze price ranges
        prices = [p.price for p in products if p.price > 0]
        avg_price = sum(prices) / len(prices) if prices else 0
        
        return {
            'top_themes': top_themes,
            'average_price': round(avg_price, 2),
            'price_range': {
                'min': min(prices) if prices else 0,
                'max': max(prices) if prices else 0
            },
            'total_products': len(products)
        }


class CompetitorSpyAgent:
    """
    Competitor Spy Agent
    Monitors competitors and alerts on new trends
    """
    
    def __init__(self, db_session):
        self.session = db_session
        self.monitors: List[CompetitorStoreMonitor] = []
        self.trend_analyzer = TrendAnalyzer()
        self.running = False
        
        # Initialize monitors from config
        self._initialize_monitors()
    
    def _initialize_monitors(self):
        """Initialize competitor monitors"""
        # Default competitors to monitor
        default_competitors = [
            # These would be configured by user
        ]
        
        for comp in default_competitors:
            self.add_competitor(comp['url'], comp['name'])
    
    def add_competitor(self, url: str, name: str):
        """Add a competitor to monitor"""
        monitor = CompetitorStoreMonitor(url, name)
        self.monitors.append(monitor)
        print(f"✅ Added competitor: {name}")
    
    async def run(self):
        """Main agent loop"""
        self.running = True
        print("🕵️ Competitor Spy Agent started")
        print(f"   Monitoring {len(self.monitors)} competitors")
        
        while self.running:
            try:
                await self._scan_all_competitors()
                await asyncio.sleep(12 * 3600)  # Every 12 hours
                
            except Exception as e:
                self._log_error(f"Spy agent error: {e}")
                await asyncio.sleep(3600)
    
    async def _scan_all_competitors(self):
        """Scan all competitor stores"""
        print("\n🕵️ Scanning competitors...")
        
        all_new_products = []
        all_trends = []
        
        for monitor in self.monitors:
            print(f"   Scanning {monitor.store_name}...")
            
            # Scan store
            products = await monitor.scan_store()
            
            # Detect new products
            new_products = monitor.detect_new_products(products)
            
            if new_products:
                print(f"   🆕 Found {len(new_products)} new products!")
                all_new_products.extend(new_products)
            
            # Analyze trends
            trends = self.trend_analyzer.analyze_products(products)
            all_trends.append({
                'store': monitor.store_name,
                'trends': trends
            })
        
        # Generate insights
        if all_new_products:
            await self._alert_new_products(all_new_products)
        
        await self._generate_trend_report(all_trends)
    
    async def _alert_new_products(self, products: List[CompetitorProduct]):
        """Alert about new competitor products"""
        print(f"\n🚨 NEW COMPETITOR PRODUCTS DETECTED!")
        
        for product in products[:5]:  # Top 5
            print(f"\n   📦 {product.store_name}")
            print(f"      Title: {product.title}")
            print(f"      Price: ${product.price}")
            print(f"      URL: {product.product_url}")
        
        # Would send email notification
        self._log_action("new_products_detected", "info", {
            "count": len(products),
            "products": [{"title": p.title, "store": p.store_name} for p in products[:5]]
        })
    
    async def _generate_trend_report(self, all_trends: List[Dict]):
        """Generate trend analysis report"""
        print("\n📊 Competitor Trend Report")
        print("-" * 40)
        
        for store_data in all_trends:
            store = store_data['store']
            trends = store_data['trends']
            
            print(f"\n🏪 {store}:")
            print(f"   Products: {trends['total_products']}")
            print(f"   Avg Price: ${trends['average_price']}")
            print(f"   Top Themes: {', '.join([t[0] for t in trends['top_themes'][:3]])}")
    
    def get_competitor_summary(self) -> Dict:
        """Get summary of competitor monitoring"""
        return {
            'monitors_count': len(self.monitors),
            'competitors': [m.store_name for m in self.monitors],
            'total_tracked_products': sum(len(m.known_products) for m in self.monitors)
        }
    
    def _log_action(self, action: str, status: str, details: Dict):
        """Log agent action"""
        log = AgentLog(
            agent_name='competitor_spy',
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
        print("🛑 Competitor Spy Agent stopped")


# Standalone run
async def run_competitor_spy_agent():
    """Run spy agent standalone"""
    from ..database.models import init_database
    from ..config.settings import config
    
    engine = init_database(config.database_path)
    session = get_session(engine)
    
    agent = CompetitorSpyAgent(session)
    
    # Add test competitor
    agent.add_competitor(
        "https://example-store.myshopify.com/collections/all",
        "Example Store"
    )
    
    await agent.run()


if __name__ == "__main__":
    asyncio.run(run_competitor_spy_agent())
