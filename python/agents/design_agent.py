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
import random
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import os
import re
from pathlib import Path

from config.settings import config
from database.models import Design, Product, ProductVariant, TrendData, AgentLog, get_session


class TrendScanner:
    """Returns a randomized mix of design niches targeting multiple age groups."""

    # Each entry: (niche_key, age_group, category)
    NICHE_POOL = [
        # --- Gen Z (16-25) ---
        ('gen_z_internet_humor',      'gen_z',      'humor'),
        ('gen_z_gamer_life',          'gen_z',      'gaming'),
        ('gen_z_anime_fan',           'gen_z',      'pop_culture'),
        ('gen_z_mental_health_jokes', 'gen_z',      'humor'),
        ('gen_z_broke_but_cool',      'gen_z',      'humor'),
        ('gen_z_coffee_addict',       'gen_z',      'lifestyle'),
        ('gen_z_social_media_irony',  'gen_z',      'humor'),
        ('gen_z_plant_parent',        'gen_z',      'lifestyle'),
        ('gen_z_side_hustle',         'gen_z',      'motivation'),
        ('gen_z_nap_enthusiast',      'gen_z',      'humor'),
        ('gen_z_cat_obsessed',        'gen_z',      'pets'),
        ('gen_z_conspiracy_humor',    'gen_z',      'humor'),
        ('gen_z_adulting_fails',      'gen_z',      'humor'),
        ('gen_z_fomo_jokes',          'gen_z',      'humor'),
        ('gen_z_hot_take',            'gen_z',      'humor'),

        # --- Millennials (26-40) ---
        ('millennial_adulting_hard',  'millennial', 'humor'),
        ('millennial_wine_oclock',    'millennial', 'lifestyle'),
        ('millennial_90s_nostalgia',  'millennial', 'nostalgia'),
        ('millennial_wfh_life',       'millennial', 'humor'),
        ('millennial_student_debt',   'millennial', 'humor'),
        ('millennial_avocado_toast',  'millennial', 'humor'),
        ('millennial_inner_child',    'millennial', 'humor'),
        ('millennial_nap_goals',      'millennial', 'humor'),
        ('millennial_true_crime_fan', 'millennial', 'pop_culture'),
        ('millennial_dog_parent',     'millennial', 'pets'),
        ('millennial_gym_excuses',    'millennial', 'humor'),
        ('millennial_cancelled_plans','millennial', 'humor'),
        ('millennial_overthinking',   'millennial', 'humor'),
        ('millennial_barely_coping',  'millennial', 'humor'),
        ('millennial_coffee_survival','millennial', 'lifestyle'),

        # --- Gen X / Boomers (40+) ---
        ('older_retirement_countdown','older',      'humor'),
        ('older_not_old_vintage',     'older',      'humor'),
        ('older_dad_joke_champion',   'older',      'humor'),
        ('older_grandparent_pride',   'older',      'family'),
        ('older_tech_confused',       'older',      'humor'),
        ('older_back_in_my_day',      'older',      'humor'),
        ('older_fishing_obsessed',    'older',      'hobby'),
        ('older_golf_addict',         'older',      'hobby'),
        ('older_wine_connoisseur',    'older',      'lifestyle'),
        ('older_still_got_it',        'older',      'humor'),
        ('older_nap_is_self_care',    'older',      'humor'),
        ('older_gardening_expert',    'older',      'hobby'),
        ('older_classic_rock_fan',    'older',      'music'),
        ('older_proud_boomer',        'older',      'humor'),
        ('older_veteran_pride',       'older',      'patriotic'),

        # --- Cross-demographic evergreen ---
        ('universal_pet_lover',       'all',        'pets'),
        ('universal_sarcasm_expert',  'all',        'humor'),
        ('universal_introvert_life',  'all',        'humor'),
        ('universal_pizza_religion',  'all',        'food'),
        ('universal_monday_hate',     'all',        'humor'),
        ('universal_travel_addict',   'all',        'lifestyle'),
        ('universal_bookworm',        'all',        'hobby'),
        ('universal_night_owl',       'all',        'humor'),
        ('universal_sports_fan',      'all',        'sports'),
        ('universal_music_lover',     'all',        'music'),
    ]

    async def scan_all_sources(self) -> List[Dict]:
        """Return a randomized selection of niches for variety."""
        shuffled = self.NICHE_POOL.copy()
        random.shuffle(shuffled)
        trends = []
        for niche_key, age_group, category in shuffled[:20]:
            trends.append({
                'keyword': niche_key,
                'age_group': age_group,
                'category': category,
                'source': 'curated_pool',
                'trend_score': random.randint(70, 100),
            })
        return trends


class DesignGenerator:
    """Generates AI designs using DALL-E"""
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(
            api_key=config.openai.api_key,
            timeout=120.0,
            max_retries=2,
        )
        self.output_dir = Path("./data/designs")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate_design(self, trend: Dict) -> Optional[Design]:
        """Generate a design based on trend data"""
        try:
            # Use GPT-4 to create a specific funny concept, then build the image prompt
            concept = await self._generate_concept(trend)
            prompt = concept['image_prompt']
            
            # Try DALL-E first, fall back to Pollinations.AI if billing limit hit
            image_url = None
            ai_model_used = config.openai.image_model
            try:
                response = await self.client.images.generate(
                    model=config.openai.image_model,
                    prompt=prompt,
                    size=config.design.image_size,
                    quality=config.design.image_quality,
                    n=1
                )
                image_url = response.data[0].url
                print(f"🎨 DALL-E image generated")
            except Exception as dalle_err:
                err_str = str(dalle_err)
                if 'billing_hard_limit_reached' in err_str or 'insufficient_quota' in err_str or 'billing' in err_str.lower():
                    print(f"⚠️  OpenAI billing limit hit — falling back to Pollinations.AI (free)")
                    image_url = await self._generate_pollinations(prompt, trend['keyword'])
                    ai_model_used = 'pollinations'
                else:
                    raise

            if not image_url:
                print(f"❌ Both DALL-E and Pollinations.AI failed for trend: {trend['keyword']}")
                return None

            # Download and save image
            local_path = await self._download_image(image_url, trend['keyword'])

            # Create design record — store concept metadata for use in product title/description
            design = Design(
                prompt=prompt,
                image_url=image_url,
                local_path=str(local_path) if local_path else None,
                trend_source=trend['source'],
                trend_keywords=[trend['keyword'], concept['title'], concept['slogan']],
                trend_score=trend.get('trend_score', 50),
                ai_model=ai_model_used,
                generation_params={
                    'size': config.design.image_size,
                    'quality': config.design.image_quality,
                    'title': concept['title'],
                    'slogan': concept['slogan'],
                    'description': concept['description'],
                    'age_group': trend.get('age_group', 'all'),
                    'tags': concept['tags'],
                },
                status='pending',
                ai_confidence=0.85 if ai_model_used != 'pollinations' else 0.75
            )

            return design

        except Exception as e:
            import traceback
            print(f"❌ Error generating design: {e}")
            print(traceback.format_exc())
            return None

    async def _generate_pollinations(self, prompt: str, keyword: str) -> Optional[str]:
        """Generate image via Pollinations.AI (free, no API key needed)"""
        try:
            import urllib.parse
            encoded_prompt = urllib.parse.quote(prompt)
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&model=flux"
            print(f"🌸 Pollinations.AI request: {url[:80]}...")

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=120) as response:
                    if response.status == 200:
                        # Pollinations returns the image directly — save it and return a local file:// URL
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        safe_keyword = re.sub(r'[^\w]', '_', keyword)[:30]
                        filepath = self.output_dir / f"{safe_keyword}_{timestamp}_pollinations.png"
                        content = await response.read()
                        with open(filepath, 'wb') as f:
                            f.write(content)
                        print(f"✅ Pollinations.AI image saved: {filepath}")
                        return str(filepath)  # use local path as the "url"
                    else:
                        print(f"❌ Pollinations.AI error: {response.status}")
                        return None
        except Exception as e:
            print(f"❌ Pollinations.AI exception: {e}")
            return None
    
    async def _generate_concept(self, trend: Dict) -> Dict:
        """Use GPT-4 to generate a specific, funny, print-ready t-shirt concept."""
        niche = trend['keyword']
        age_group = trend.get('age_group', 'all')
        category = trend.get('category', 'humor')

        age_desc = {
            'gen_z': 'Gen Z (ages 16-25) — use internet slang, meme culture, dry humor, self-aware irony',
            'millennial': 'Millennials (ages 26-40) — use relatable adulting humor, nostalgia, work-life balance jokes',
            'older': 'Gen X and Boomers (ages 40+) — use dad jokes, retirement humor, "back in my day" references, wholesome wit',
            'all': 'all age groups — use universally relatable humor that anyone can appreciate',
        }.get(age_group, 'all age groups')

        system_prompt = (
            "You are a viral t-shirt designer who creates funny, clever, print-ready apparel concepts. "
            "Your designs sell thousands of units because they are specific, witty, and immediately relatable. "
            "Never be generic. Every design should feel like it was made for a specific person who will laugh and say 'that's SO me'."
        )

        user_prompt = f"""Create a specific funny t-shirt design concept for the niche: "{niche}"
Target audience: {age_desc}

Return ONLY valid JSON with these exact fields:
{{
  "title": "Short punchy product title (5 words max, no 'Print on Demand')",
  "slogan": "The actual funny text that goes ON the shirt (must be funny, specific, and print-ready — 1-2 lines max)",
  "description": "2-sentence product description for the Shopify listing that sells the shirt",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "image_prompt": "Detailed DALL-E prompt: flat vector t-shirt graphic, white background, the slogan text prominently displayed in bold readable font, [describe any supporting illustration], print-ready, high contrast, no gradients, clean edges"
}}

Rules:
- The slogan must be FUNNY and SPECIFIC — not generic like "I love coffee"
- Use correct spelling and grammar
- The image_prompt must include the exact slogan text so DALL-E renders it on the design
- Tags should be relevant search terms people actually use"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.9,
                max_tokens=500,
            )
            raw = response.choices[0].message.content.strip()
            # Strip markdown code fences if present
            raw = re.sub(r'^```(?:json)?\s*', '', raw)
            raw = re.sub(r'\s*```$', '', raw)
            concept = json.loads(raw)
            print(f"💡 Concept: '{concept['slogan']}' → {concept['title']}")
            return concept
        except Exception as e:
            print(f"⚠️  GPT-4 concept generation failed: {e} — using fallback")
            return {
                'title': niche.replace('_', ' ').title(),
                'slogan': niche.replace('_', ' ').title(),
                'description': f"Funny t-shirt for {age_group}. High-quality print-on-demand.",
                'tags': [niche, age_group, category, 'funny', 'tshirt'],
                'image_prompt': f"Flat vector t-shirt graphic, bold text '{niche.replace('_', ' ').title()}', white background, print-ready, high contrast",
            }
    
    async def _download_image(self, url: str, keyword: str) -> Optional[Path]:
        """Download generated image to local storage"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_keyword = re.sub(r'[^\w]', '_', keyword)[:30]
            filename = f"{safe_keyword}_{timestamp}.png"
            filepath = self.output_dir / filename
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
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
        print("🎨 Picasso is awake and ready to create masterpieces")
        
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
        """Filter out niches used in the last 30 designs to ensure variety."""
        recent = self.session.query(Design).order_by(
            Design.created_at.desc()
        ).limit(30).all()
        recently_used = set()
        for d in recent:
            if d.trend_keywords:
                recently_used.add(d.trend_keywords[0].lower())

        unused = [t for t in trends if t['keyword'].lower() not in recently_used]
        return unused if unused else trends  # fallback: allow repeats if pool exhausted
    
    async def _approve_design(self, design: Design):
        """Approve a design and create product"""
        design.status = 'approved'
        design.approved_at = datetime.utcnow()
        design.approved_by = 'ai'
        self.session.commit()
        print(f"✅ Design {design.id} auto-approved")

        # Create Shopify product from approved design
        await self._create_product_from_design(design)

    async def _create_product_from_design(self, design: Design):
        """Create a product in Shopify and the local database from an approved design"""
        import base64
        from integrations.shopify import ShopifyAPI

        params = design.generation_params or {}
        title = params.get('title') or (design.trend_keywords[0] if design.trend_keywords else 'New Design')
        slogan = params.get('slogan', '')
        description_text = params.get('description', f'Funny t-shirt: {slogan}' if slogan else f'Unique graphic tee — {title}')
        tags = params.get('tags') or design.trend_keywords or []
        description = f"<p>{description_text}</p>"
        if slogan:
            description += f'<p><strong>"{slogan}"</strong></p>'
        description += "<p>Available in sizes S–2XL. High-quality print-on-demand.</p>"
        base_price = 24.99

        product_data = {
            'title': title,
            'description': description,
            'product_type': 'T-Shirt',
            'tags': tags,
            'variants': [
                {'size': 'S',  'price': base_price,      'sku': f'SKU-{design.id}-S'},
                {'size': 'M',  'price': base_price,      'sku': f'SKU-{design.id}-M'},
                {'size': 'L',  'price': base_price,      'sku': f'SKU-{design.id}-L'},
                {'size': 'XL', 'price': base_price + 2,  'sku': f'SKU-{design.id}-XL'},
                {'size': '2XL','price': base_price + 2,  'sku': f'SKU-{design.id}-2XL'},
            ]
        }

        # Prefer base64 attachment from the downloaded local file — DALL-E URLs
        # expire after ~1 hour and cannot be fetched by Shopify's servers reliably.
        if design.local_path and Path(design.local_path).exists():
            try:
                with open(design.local_path, 'rb') as f:
                    product_data['image_attachment'] = base64.b64encode(f.read()).decode('utf-8')
                print(f"📎 Using local image file for Shopify upload: {design.local_path}")
            except Exception as img_err:
                print(f"⚠️  Could not read local image, falling back to URL: {img_err}")
                product_data['image_urls'] = [design.image_url] if design.image_url else []
        else:
            # Fall back to DALL-E URL (works if called within ~1 hour of generation)
            product_data['image_urls'] = [design.image_url] if design.image_url else []
            if not product_data['image_urls']:
                print("⚠️  No image available for this design — product will have no image")

        shopify_product = None
        shopify_id = None
        if config.shopify.is_configured:
            shopify = ShopifyAPI()
            shopify_product = await shopify.create_product(product_data)
            if shopify_product:
                shopify_id = str(shopify_product['id'])
            else:
                print(f"❌ Shopify product creation FAILED for design {design.id} ('{title}'). "
                      f"Check the error above for the full Shopify API response.")

        # Use the permanent Shopify CDN URL for the product image if we got one back.
        # This URL is what the social agent will use to post — it never expires.
        if shopify_product and shopify_product.get('images'):
            product_image_url = shopify_product['images'][0].get('src') or design.image_url
            print(f"🖼️  Shopify CDN image URL captured for social posting")
        else:
            product_image_url = design.image_url

        # Save product to local database
        cost_price = 12.00  # Printful base cost for a standard t-shirt
        product = Product(
            shopify_id=shopify_id,
            title=title,
            description=description,
            product_type='T-Shirt',
            tags=design.trend_keywords or [],
            design_id=design.id,
            design_url=product_image_url,
            selling_price=base_price,
            cost_price=cost_price,
            is_active=True,
            is_approved=True,
        )
        self.session.add(product)
        self.session.flush()  # get product.id

        # Save variants
        for v in product_data['variants']:
            variant = ProductVariant(
                product_id=product.id,
                size=v['size'],
                sku=v['sku'],
                selling_price=v['price'],
                inventory_quantity=0,  # print-on-demand — no pre-stocked inventory
            )
            self.session.add(variant)

        self.session.commit()

        if shopify_id:
            print(f"✅ Product '{title}' created in Shopify (ID: {shopify_id})")
        else:
            print(f"⚠️  Product '{title}' saved locally (Shopify not configured or request failed)")

        self._log_action("product_created", "success" if shopify_id else "warning", {
            "design_id": design.id,
            "title": title,
            "shopify_id": shopify_id,
        })
    
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
        print("🛑 Picasso put down the brush")


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
