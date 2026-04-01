"""
PrintBot AI - Pricing Agent
============================
Monitors competitors, adjusts prices dynamically.
Schedule: Every 2 hours
Strategy: Anchor 40%, floor 25% margin
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import json
import re

from config.settings import config
from database.models import Product, CompetitorPrice, AgentLog, get_session


class CompetitorScraper:
    """Scrapes competitor prices from various sources"""
    
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    async def scrape_competitor(self, url: str, product_type: str = "t-shirt") -> Optional[Dict]:
        """Scrape a single competitor website"""
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url, timeout=15) as response:
                    if response.status == 200:
                        html = await response.text()
                        return self._extract_prices(html, url, product_type)
        except Exception as e:
            print(f"Error scraping {url}: {e}")
        
        return None
    
    def _extract_prices(self, html: str, url: str, product_type: str) -> Dict:
        """Extract price data from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        
        prices = []
        
        # Common price selectors
        price_selectors = [
            '.price', '.product-price', '.current-price',
            '[data-price]', '.money', '.amount',
            '.sale-price', '.regular-price'
        ]
        
        for selector in price_selectors:
            elements = soup.select(selector)
            for elem in elements:
                text = elem.get_text().strip()
                price = self._parse_price(text)
                if price and 5 <= price <= 100:  # Reasonable t-shirt range
                    prices.append(price)
        
        # Also look for JSON-LD product data
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and 'offers' in data:
                    offer = data['offers']
                    if isinstance(offer, dict) and 'price' in offer:
                        price = float(offer['price'])
                        if 5 <= price <= 100:
                            prices.append(price)
            except:
                pass
        
        if prices:
            return {
                'url': url,
                'product_type': product_type,
                'min_price': min(prices),
                'max_price': max(prices),
                'avg_price': sum(prices) / len(prices),
                'price_count': len(prices),
                'scraped_at': datetime.utcnow()
            }
        
        return None
    
    def _parse_price(self, text: str) -> Optional[float]:
        """Parse price from text"""
        # Remove currency symbols and whitespace
        cleaned = re.sub(r'[^\d.,]', '', text)
        
        # Handle different decimal separators
        if ',' in cleaned and '.' in cleaned:
            if cleaned.rfind(',') > cleaned.rfind('.'):
                cleaned = cleaned.replace('.', '').replace(',', '.')
            else:
                cleaned = cleaned.replace(',', '')
        elif ',' in cleaned:
            cleaned = cleaned.replace(',', '.')
        
        try:
            return float(cleaned) if cleaned else None
        except:
            return None


class PriceOptimizer:
    """Optimizes prices based on costs and competition"""
    
    def __init__(self):
        self.anchor_margin = config.pricing.anchor_margin
        self.floor_margin = config.pricing.floor_margin
    
    def calculate_optimal_price(
        self,
        cost_price: float,
        competitor_avg: Optional[float] = None,
        current_price: Optional[float] = None
    ) -> Tuple[float, Dict]:
        """
        Calculate optimal selling price
        Returns: (new_price, reasoning)
        """
        reasoning = {
            'cost_price': cost_price,
            'anchor_margin': self.anchor_margin,
            'floor_margin': self.floor_margin,
            'competitor_avg': competitor_avg,
            'current_price': current_price,
            'factors': []
        }
        
        # Calculate anchor price (target)
        anchor_price = cost_price / (1 - self.anchor_margin)
        
        # Calculate floor price (minimum)
        floor_price = cost_price / (1 - self.floor_margin)
        
        # Start with anchor price
        optimal_price = anchor_price
        reasoning['factors'].append(f"Started with anchor price: ${anchor_price:.2f}")
        
        # Adjust based on competition if available
        if competitor_avg:
            if competitor_avg < floor_price:
                # Competitors are too cheap, stick to floor
                optimal_price = floor_price
                reasoning['factors'].append(f"Competitors underpricing (${competitor_avg:.2f}), using floor: ${floor_price:.2f}")
            elif competitor_avg > anchor_price * 1.2:
                # Competitors are much higher, we can increase
                optimal_price = min(competitor_avg * 0.95, anchor_price * 1.1)
                reasoning['factors'].append(f"Competitors higher (${competitor_avg:.2f}), pricing slightly below: ${optimal_price:.2f}")
            elif abs(competitor_avg - anchor_price) / anchor_price > config.pricing.price_adjustment_threshold:
                # Significant difference, adjust towards competition
                optimal_price = (anchor_price + competitor_avg) / 2
                reasoning['factors'].append(f"Adjusted toward competitor average: ${optimal_price:.2f}")
        
        # Apply psychological pricing
        if config.pricing.use_charm_pricing:
            optimal_price = self._apply_charm_pricing(optimal_price)
            reasoning['factors'].append(f"Applied charm pricing: ${optimal_price:.2f}")
        
        # Ensure we don't go below floor
        if optimal_price < floor_price:
            optimal_price = floor_price
            reasoning['factors'].append(f"Adjusted to floor price: ${floor_price:.2f}")
        
        # Calculate margin
        margin = (optimal_price - cost_price) / optimal_price
        reasoning['final_margin'] = margin
        
        return round(optimal_price, 2), reasoning
    
    def _apply_charm_pricing(self, price: float) -> float:
        """Apply psychological charm pricing (e.g., $27.99 instead of $28.00)"""
        if price < 10:
            # For prices under $10, use .99
            return int(price) + 0.99
        elif price < 50:
            # For mid-range, use .99 or .97
            return int(price) + 0.99
        else:
            # For higher prices, might use .95
            return int(price) + 0.99
    
    def calculate_bundle_price(self, unit_price: float, quantity: int) -> float:
        """Calculate bundle discount price"""
        if not config.pricing.bundle_enabled:
            return unit_price * quantity
        
        if quantity >= config.pricing.bundle_threshold:
            discount = 1 - config.pricing.bundle_discount
            return round(unit_price * quantity * discount, 2)
        
        return unit_price * quantity


class PricingAgent:
    """
    Main Pricing Agent
    Monitors competitors and adjusts prices
    """
    
    def __init__(self, db_session):
        self.session = db_session
        self.scraper = CompetitorScraper()
        self.optimizer = PriceOptimizer()
        self.running = False
        
    async def run(self):
        """Main agent loop"""
        self.running = True
        print("💰 Gordon Gecko is online — greed is good, prices are better")
        
        while self.running:
            try:
                await self._process_cycle()
                
                # Wait for next interval
                await asyncio.sleep(config.pricing.competitor_check_interval)
                
            except Exception as e:
                self._log_error(f"Pricing agent error: {e}")
                await asyncio.sleep(300)  # Wait 5 min on error
    
    async def _process_cycle(self):
        """Process one pricing cycle"""
        print("💰 Running pricing analysis...")
        
        # Scrape competitor prices
        competitor_data = await self._scrape_competitors()
        
        # Get all active products
        products = self.session.query(Product).filter(
            Product.is_active == True
        ).all()
        
        updated_count = 0
        
        for product in products:
            try:
                # Get relevant competitor prices
                relevant_competitors = self._get_relevant_competitors(
                    competitor_data, product
                )
                
                competitor_avg = None
                if relevant_competitors:
                    competitor_avg = sum(c['avg_price'] for c in relevant_competitors) / len(relevant_competitors)
                
                # Calculate new price
                new_price, reasoning = self.optimizer.calculate_optimal_price(
                    cost_price=product.cost_price or 10.0,
                    competitor_avg=competitor_avg,
                    current_price=product.selling_price
                )
                
                # Update if price changed significantly
                if product.selling_price is None or abs(new_price - product.selling_price) > 0.5:
                    old_price = product.selling_price
                    product.selling_price = new_price
                    product.margin_percent = reasoning['final_margin']
                    product.updated_at = datetime.utcnow()
                    
                    self.session.commit()
                    updated_count += 1
                    
                    print(f"💰 Updated '{product.title}': ${old_price} → ${new_price}")
                    
                    # Log price change
                    self._log_action("price_update", "success", {
                        "product_id": product.id,
                        "old_price": old_price,
                        "new_price": new_price,
                        "reasoning": reasoning
                    })
                    
                    # Update Shopify if configured
                    if config.shopify.is_configured:
                        await self._update_shopify_price(product)
                
            except Exception as e:
                print(f"Error updating price for product {product.id}: {e}")
                continue
        
        print(f"💰 Pricing cycle complete. Updated {updated_count} products.")
    
    async def _scrape_competitors(self) -> List[Dict]:
        """Scrape all configured competitors"""
        results = []
        
        for url in config.pricing.competitor_urls:
            try:
                data = await self.scraper.scrape_competitor(url)
                if data:
                    results.append(data)
                    
                    # Save to database
                    competitor_price = CompetitorPrice(
                        competitor_name=self._extract_domain(url),
                        competitor_url=url,
                        product_name="general",
                        price=data['avg_price']
                    )
                    self.session.add(competitor_price)
                    
            except Exception as e:
                print(f"Error scraping {url}: {e}")
        
        self.session.commit()
        return results
    
    def _get_relevant_competitors(self, competitor_data: List[Dict], product: Product) -> List[Dict]:
        """Get competitor data relevant to a specific product"""
        # For now, return all competitors
        # Could be enhanced with product type matching
        return competitor_data
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain name from URL"""
        match = re.search(r'https?://([^/]+)', url)
        return match.group(1) if match else url
    
    async def _update_shopify_price(self, product: Product):
        """Update price on Shopify"""
        try:
            from integrations.shopify import ShopifyAPI
            shopify = ShopifyAPI()
            await shopify.update_product_price(
                product.shopify_id,
                product.selling_price,
                product.compare_at_price
            )
            product.last_synced = datetime.utcnow()
            self.session.commit()
            
        except Exception as e:
            print(f"Error updating Shopify price: {e}")
    
    def _log_action(self, action: str, status: str, details: Dict):
        """Log agent action"""
        log = AgentLog(
            agent_name='pricing',
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
        print("🛑 Gordon Gecko has left the building")


# Standalone run function
async def run_pricing_agent():
    """Run pricing agent standalone"""
    from database.models import init_database
    
    engine = init_database(config.database_path)
    session = get_session(engine)
    
    agent = PricingAgent(session)
    await agent.run()


if __name__ == "__main__":
    asyncio.run(run_pricing_agent())
