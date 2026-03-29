"""
PrintBot AI - Design Agent
===========================
Scans trends, generates AI designs, and creates products.
Schedule: Every 30 minutes
Max: 3 designs per day
"""
import asyncio
import aiohttp
import openai
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import os
import re
from pathlib import Path

from config.settings import config
from database.models import Design, Product, TrendData, AgentLog, get_session
from integrations.shopify import ShopifyAPI


class TrendScanner:
    """Scans multiple sources for trending topics"""
    
    def __init__(self):
        self.trend_cache = {}
        self.cache_expiry = timedelta(minutes=30)
        
    async def scan_all_sources(self) -> List[Dict]:
        """Scan all configured trend sources"""
        trends = []
        
        # Google Trends
        google_trends = await self._scan_google_trends()
        trends.extend(google_trends)
        
        # Pinterest Trends (if accessible)
        pinterest_trends = await self._scan_pinterest()
        trends.extend(pinterest_trends)
        
        # Etsy trending
        etsy_trends = await self._scan_etsy()
        trends.extend(etsy_trends)
        
        # Social media hashtags
        social_trends = await self._scan_social_hashtags()
        trends.extend(social_trends)
        
        # Filter and rank trends
        ranked_trends = self._rank_trends(trends)
        
        return ranked_trends[:20]  # Return top 20
    
    async def _scan_google_trends(self) -> List[Dict]:
        """Scrape Google Trends daily search"""
        trends = []
        try:
            url = "https://trends.google.com/trends/trendingsearches/daily/rss"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        content = await response.text()
                        soup = BeautifulSoup(content, 'xml')
                        items = soup.find_all('item')[:10]
                        
                        for item in items:
                            title = item.find('title')
                            if title:
                                trends.append({
                                    'keyword': title.text,
                                    'source': 'google_trends',
                                    'category': 'general',
                                    'trend_score': 100 - len(trends) * 5,  # Decreasing score
                                    'search_volume': None
                                })
        except Exception as e:
            print(f"Error scanning Google Trends: {e}")
        
        return trends
    
    async def _scan_pinterest(self) -> List[Dict]:
        """Scan Pinterest for trending ideas"""
        trends = []
        try:
            # Pinterest doesn't have a public API for trends without auth
            # We'll use popular categories as proxy
            categories = [
                'funny quotes', 'motivational quotes', 'vintage aesthetic',
                'minimalist design', 'pop culture', 'gaming', 'pets',
                'travel', 'fitness', 'foodie', 'music', 'movies'
            ]
            
            for cat in categories:
                trends.append({
                    'keyword': cat,
                    'source': 'pinterest',
                    'category': 'design',
                    'trend_score': 70,
                    'search_volume': None
                })
        except Exception as e:
            print(f"Error scanning Pinterest: {e}")
        
        return trends
    
    async def _scan_etsy(self) -> List[Dict]:
        """Scan Etsy for trending products"""
        trends = []
        try:
            search_terms = [
                'trending tshirt', 'popular mug', 'funny gift',
                'personalized gift', 'custom design', 'viral quote'
            ]
            
            for term in search_terms:
                trends.append({
                    'keyword': term,
                    'source': 'etsy',
                    'category': 'product',
                    'trend_score': 65,
                    'search_volume': None
                })
        except Exception as e:
            print(f"Error scanning Etsy: {e}")
        
        return trends
    
    async def _scan_social_hashtags(self) -> List[Dict]:
        """Scan social media for trending hashtags"""
        # Popular evergreen hashtags that perform well
        evergreen_hashtags = [
            '#MondayMotivation', '#TBT', '#FridayFeeling', '#WeekendVibes',
            '#SelfCare', '#Hustle', '#Goals', '#Blessed', '#Grateful',
            '#OOTD', '#Foodie', '#Travel', '#Fitness', '#Gaming'
        ]
        
        trends = []
        for tag in evergreen_hashtags:
            trends.append({
                'keyword': tag.replace('#', ''),
                'source': 'social_media',
                'category': 'hashtag',
                'trend_score': 60,
                'search_volume': None
            })
        
        return trends
    
    def _rank_trends(self, trends: List[Dict]) -> List[Dict]:
        """Rank trends by score and remove duplicates"""
        # Remove duplicates
        seen = set()
        unique_trends = []
        for t in trends:
            keyword = t['keyword'].lower().strip()
            if keyword not in seen:
                seen.add(keyword)
                unique_trends.append(t)
        
        # Sort by trend score
        unique_trends.sort(key=lambda x: x.get('trend_score', 0), reverse=True)
        
        return unique_trends


class DesignGenerator:
    """Generates AI designs using DALL-E"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=config.openai.api_key)
        self.output_dir = Path("./data/designs")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate_design(self, trend: Dict) -> Optional[Design]:
        """Generate a design based on trend data"""
        try:
            # Create optimized prompt
            prompt = self._create_prompt(trend)
            
            # Generate image with DALL-E
            response = self.client.images.generate(
                model=config.openai.image_model,
                prompt=prompt,
                size=config.design.image_size,
                quality=config.design.image_quality,
                n=1
            )
            
            image_url = response.data[0].url
            
            # Download and save image
            local_path = await self._download_image(image_url, trend['keyword'])
            
            # Create design record
            design = Design(
                prompt=prompt,
                image_url=image_url,
                local_path=str(local_path) if local_path else None,
                trend_source=trend['source'],
                trend_keywords=[trend['keyword']],
                trend_score=trend.get('trend_score', 50),
                ai_model=config.openai.image_model,
                generation_params={
                    'size': config.design.image_size,
                    'quality': config.design.image_quality
                },
                status='pending',
                ai_confidence=0.85  # DALL-E quality estimate
            )
            
            return design
            
        except Exception as e:
            print(f"Error generating design: {e}")
            return None
    
    def _create_prompt(self, trend: Dict) -> str:
        """Create an optimized DALL-E prompt from trend"""
        keyword = trend['keyword']
        
        # Prompt templates for different categories
        templates = {
            'quote': f"A minimalist t-shirt design with the text '{keyword}' in modern typography, clean white background, professional product photography style, high contrast",
            'funny': f"A humorous graphic t-shirt design featuring '{keyword}', cartoon style, vibrant colors, white background, print-ready",
            'aesthetic': f"Aesthetic vintage-style design with '{keyword}', muted colors, distressed texture, white background, trendy illustration",
            'motivational': f"Inspirational typography design with '{keyword}', bold modern font, gradient accents, white background, professional",
            'pop_culture': f"Pop culture inspired design featuring '{keyword}', trendy style, eye-catching colors, white background, viral potential",
            'default': f"Modern t-shirt graphic design with '{keyword}', clean professional style, white background, print-ready, high quality"
        }
        
        # Determine best template based on keyword
        keyword_lower = keyword.lower()
        if any(word in keyword_lower for word in ['quote', 'saying', 'words']):
            return templates['quote']
        elif any(word in keyword_lower for word in ['funny', 'hilarious', 'joke', 'meme']):
            return templates['funny']
        elif any(word in keyword_lower for word in ['aesthetic', 'vintage', 'retro']):
            return templates['aesthetic']
        elif any(word in keyword_lower for word in ['motivation', 'inspire', 'hustle', 'goals']):
            return templates['motivational']
        elif any(word in keyword_lower for word in ['viral', 'trending', 'pop']):
            return templates['pop_culture']
        else:
            return templates['default']
    
    async def _download_image(self, url: str, keyword: str) -> Optional[Path]:
        """Download generated image to local storage"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_keyword = re.sub(r'[^\w]', '_', keyword)[:30]
            filename = f"{safe_keyword}_{timestamp}.png"
            filepath = self.output_dir / filename
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        content = await response.read()
                        with open(filepath, 'wb') as f:
                            f.write(content)
                        return filepath
            
        except Exception as e:
            print(f"Error downloading image: {e}")
        
        return None


class DesignAgent:
    """
    Main Design Agent
    Scans trends, generates designs, and creates products
    """
    
    def __init__(self, db_session):
        self.session = db_session
        self.trend_scanner = TrendScanner()
        self.design_generator = DesignGenerator()
        self.running = False
        
    async def run(self):
        """Main agent loop"""
        self.running = True
        print("🎨 Design Agent started")
        
        while self.running:
            try:
                await self._process_cycle()
                
                # Wait for next interval
                await asyncio.sleep(config.design.design_interval)
                
            except Exception as e:
                self._log_error(f"Design agent error: {e}")
                await asyncio.sleep(60)  # Wait 1 min on error
    
    async def _process_cycle(self):
        """Process one design cycle"""
        # Check daily limit
        designs_today = self._get_designs_count_today()
        if designs_today >= config.design.max_daily_designs:
            print(f"⏭️ Daily design limit reached ({designs_today}/{config.design.max_daily_designs})")
            return
        
        # Scan trends
        print("🔍 Scanning trends...")
        trends = await self.trend_scanner.scan_all_sources()
        
        # Filter out already-used trends
        unused_trends = self._filter_unused_trends(trends)
        
        if not unused_trends:
            print("ℹ️ No new trends found")
            return
        
        # Get top trend
        top_trend = unused_trends[0]
        print(f"📈 Top trend: {top_trend['keyword']}")
        
        # Generate design
        print("🎨 Generating design...")
        design = await self.design_generator.generate_design(top_trend)
        
        if design:
            # Save to database
            self.session.add(design)
            self.session.commit()
            
            print(f"✅ Design created: ID {design.id}")
            
            # Auto-approve if enabled and confidence is high enough
            if config.design.auto_approve and design.ai_confidence >= config.design.approval_threshold:
                await self._approve_design(design)
            
            # Log success
            self._log_action("design_created", "success", {
                "design_id": design.id,
                "trend": top_trend['keyword']
            })
        else:
            self._log_action("design_creation", "error", {
                "trend": top_trend['keyword'],
                "error": "Failed to generate design"
            })
    
    def _get_designs_count_today(self) -> int:
        """Get number of designs created today"""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        count = self.session.query(Design).filter(
            Design.created_at >= today
        ).count()
        return count
    
    def _filter_unused_trends(self, trends: List[Dict]) -> List[Dict]:
        """Filter out trends we've already created designs for"""
        unused = []
        for trend in trends:
            keyword = trend['keyword'].lower()
            existing = self.session.query(TrendData).filter(
                TrendData.keyword.ilike(f"%{keyword}%"),
                TrendData.design_created == True
            ).first()
            
            if not existing:
                unused.append(trend)
        
        return unused
    
    async def _approve_design(self, design: Design):
        """Approve a design and create product"""
        design.status = 'approved'
        design.approved_at = datetime.utcnow()
        design.approved_by = 'ai'
        self.session.commit()
        print(f"✅ Design {design.id} auto-approved")

        # Create Shopify product if configured
        if config.shopify.is_configured:
            await self._create_shopify_product(design)

    async def _create_shopify_product(self, design: Design):
        """Create a Shopify product from an approved design"""
        try:
            keyword = (design.trend_keywords or ["Custom Design"])[0]
            title = f"{keyword.title()} - Graphic Tee"

            shopify = ShopifyAPI()
            product_data = {
                'title': title,
                'description': f'<p>Unique AI-generated design inspired by current trends. '
                               f'Perfect for gifting or personal use.</p>',
                'product_type': 't-shirt',
                'tags': design.trend_keywords or [],
                'image_urls': [design.image_url] if design.image_url else [],
                'variants': [
                    {'size': 'S',  'price': 24.99, 'sku': f'PBOT-{design.id}-S'},
                    {'size': 'M',  'price': 24.99, 'sku': f'PBOT-{design.id}-M'},
                    {'size': 'L',  'price': 24.99, 'sku': f'PBOT-{design.id}-L'},
                    {'size': 'XL', 'price': 24.99, 'sku': f'PBOT-{design.id}-XL'},
                ]
            }

            result = await shopify.create_product(product_data)
            if result:
                product = Product(
                    shopify_id=str(result['id']),
                    title=title,
                    product_type='t-shirt',
                    design_id=design.id,
                    design_url=design.image_url,
                    selling_price=24.99,
                    is_active=True,
                    is_approved=True,
                )
                self.session.add(product)
                self.session.commit()
                print(f"✅ Shopify product created: '{title}' (ID: {result['id']})")
                self._log_action("product_created", "success", {
                    "design_id": design.id,
                    "shopify_id": result['id'],
                    "title": title,
                })
            else:
                print(f"⚠️  Shopify product creation failed for design {design.id}")
        except Exception as e:
            print(f"❌ Error creating Shopify product: {e}")
    
    def _log_action(self, action: str, status: str, details: Dict):
        """Log agent action"""
        log = AgentLog(
            agent_name='design',
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
        print("🛑 Design Agent stopped")


# Standalone run function
async def run_design_agent():
    """Run design agent standalone"""
    from database.models import init_database
    
    engine = init_database(config.database_path)
    session = get_session(engine)
    
    agent = DesignAgent(session)
    await agent.run()


if __name__ == "__main__":
    asyncio.run(run_design_agent())
