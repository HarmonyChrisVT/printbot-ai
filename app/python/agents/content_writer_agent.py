"""
PrintBot AI - AI Content Writer Agent
======================================
Auto-generates SEO-optimized product descriptions, titles, and tags
A/B tests different versions for maximum conversion
Schedule: Runs when new products are created
"""
import asyncio
import openai
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
import re

from config.settings import config
from database.models import Product, AgentLog, get_session


@dataclass
class ContentVersion:
    """A/B test content version"""
    version_id: str
    title: str
    description: str
    tags: List[str]
    meta_title: str
    meta_description: str
    conversion_rate: float = 0.0
    impressions: int = 0
    clicks: int = 0


class SEOOptimizer:
    """SEO optimization for product content"""
    
    def __init__(self):
        self.keywords_cache = {}
        self.trending_keywords = [
            'trending', 'viral', 'popular', 'bestseller', 'must-have',
            'limited edition', 'exclusive', 'custom', 'personalized',
            'gift idea', 'unique', 'handmade', 'premium', 'quality'
        ]
    
    def optimize_title(self, base_title: str, product_type: str) -> str:
        """Optimize product title for SEO"""
        # Add power words
        power_words = ['Premium', 'Exclusive', 'Limited', 'Custom', 'Unique']
        
        # Keep under 70 characters for SEO
        optimized = base_title
        if len(optimized) < 50:
            power_word = power_words[hash(optimized) % len(power_words)]
            optimized = f"{power_word} {optimized}"
        
        # Add product type if not present
        if product_type and product_type.lower() not in optimized.lower():
            optimized = f"{optimized} | {product_type}"
        
        return optimized[:70]
    
    def generate_meta_description(self, description: str, title: str) -> str:
        """Generate SEO meta description"""
        # Extract first sentence or first 150 chars
        first_sentence = description.split('.')[0] if description else title
        meta = first_sentence[:150]
        
        if len(meta) < 120:
            meta += " | Shop now for exclusive designs!"
        
        return meta[:160]
    
    def generate_tags(self, title: str, description: str, product_type: str) -> List[str]:
        """Generate SEO tags"""
        tags = []
        
        # Extract keywords from title
        words = re.findall(r'\b[A-Za-z]{4,}\b', title.lower())
        tags.extend(words[:5])
        
        # Add product type
        if product_type:
            tags.append(product_type.lower())
        
        # Add trending keywords
        tags.extend(self.trending_keywords[:3])
        
        # Add category tags
        category_tags = {
            't-shirt': ['apparel', 'clothing', 'fashion', 'tee'],
            'hoodie': ['apparel', 'clothing', 'sweatshirt', 'casual'],
            'mug': ['home', 'kitchen', 'drinkware', 'gift'],
            'poster': ['art', 'decor', 'wall art', 'home decor'],
            'phone_case': ['accessories', 'tech', 'mobile', 'protection']
        }
        
        if product_type and product_type.lower() in category_tags:
            tags.extend(category_tags[product_type.lower()])
        
        # Remove duplicates and limit
        return list(set(tags))[:10]


class ContentWriterAgent:
    """
    AI Content Writer Agent
    Generates SEO-optimized product content
    """
    
    def __init__(self, db_session):
        self.session = db_session
        self.client = openai.OpenAI(api_key=config.openai.api_key)
        self.seo = SEOOptimizer()
        self.running = False
    
    async def generate_product_content(
        self,
        design_prompt: str,
        product_type: str,
        generate_variants: int = 2
    ) -> List[ContentVersion]:
        """Generate multiple content versions for A/B testing"""
        
        versions = []
        
        for i in range(generate_variants):
            # Generate content with GPT-4
            content = await self._generate_with_ai(design_prompt, product_type, i)
            
            # Optimize for SEO
            title = self.seo.optimize_title(content['title'], product_type)
            meta_desc = self.seo.generate_meta_description(content['description'], title)
            tags = self.seo.generate_tags(title, content['description'], product_type)
            
            version = ContentVersion(
                version_id=f"v{i+1}_{datetime.utcnow().timestamp()}",
                title=title,
                description=content['description'],
                tags=tags,
                meta_title=title[:60],
                meta_description=meta_desc
            )
            
            versions.append(version)
        
        return versions
    
    async def _generate_with_ai(
        self,
        design_prompt: str,
        product_type: str,
        variant: int
    ) -> Dict[str, str]:
        """Generate content using OpenAI"""
        
        tones = ['enthusiastic', 'professional', 'casual', 'luxury']
        tone = tones[variant % len(tones)]
        
        system_prompt = f"""You are an expert e-commerce copywriter. 
Create compelling, SEO-friendly product content for a {product_type}.
Use a {tone} tone. Focus on benefits, not just features.
Include a call-to-action."""
        
        user_prompt = f"""Design concept: "{design_prompt}"

Create:
1. A catchy product title (under 60 characters)
2. A compelling product description (150-200 words)
3. 3-5 bullet points highlighting key features

Format as JSON:
{{
    "title": "...",
    "description": "...",
    "bullet_points": ["...", "..."]
}}"""
        
        try:
            response = self.client.chat.completions.create(
                model=config.openai.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7 + (variant * 0.1),  # Vary temperature for diversity
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            
            # Parse JSON response
            try:
                parsed = json.loads(content)
                return {
                    'title': parsed.get('title', 'Custom Design Product'),
                    'description': self._format_description(parsed)
                }
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return self._parse_fallback(content)
                
        except Exception as e:
            print(f"❌ Content generation error: {e}")
            return self._get_fallback_content(design_prompt)
    
    def _format_description(self, parsed: Dict) -> str:
        """Format description with HTML"""
        description = parsed.get('description', '')
        bullets = parsed.get('bullet_points', [])
        
        html = f"<p>{description}</p>"
        
        if bullets:
            html += "<ul>"
            for bullet in bullets:
                html += f"<li>{bullet}</li>"
            html += "</ul>"
        
        html += "<p><strong>Order yours today!</strong></p>"
        
        return html
    
    def _parse_fallback(self, content: str) -> Dict[str, str]:
        """Fallback parsing if JSON fails"""
        lines = content.split('\n')
        title = lines[0][:60] if lines else "Custom Design Product"
        description = '<p>' + ' '.join(lines[1:])[:500] + '</p>'
        
        return {'title': title, 'description': description}
    
    def _get_fallback_content(self, design_prompt: str) -> Dict[str, str]:
        """Get fallback content if AI fails"""
        return {
            'title': f"Custom Design: {design_prompt[:40]}",
            'description': f"""
            <p>Show off your unique style with this custom design featuring "{design_prompt}".</p>
            <ul>
                <li>Premium quality materials</li>
                <li>Vibrant, long-lasting print</li>
                <li>Perfect gift for any occasion</li>
            </ul>
            <p><strong>Order yours today!</strong></p>
            """
        }
    
    async def update_product_content(self, product_id: int, version: ContentVersion):
        """Update product with new content"""
        product = self.session.query(Product).get(product_id)
        if not product:
            return False
        
        product.title = version.title
        product.description = version.description
        product.tags = version.tags
        product.meta_title = version.meta_title
        product.meta_description = version.meta_description
        product.content_version = version.version_id
        
        self.session.commit()
        
        print(f"✅ Updated product {product_id} with content version {version.version_id}")
        return True
    
    async def run_ab_test_analysis(self):
        """Analyze A/B test results and pick winners"""
        # Would analyze conversion rates and automatically switch to winning version
        pass

    async def run(self):
        """Main agent loop — watches for approved products without content and writes it"""
        self.running = True
        print("✍️  Shakespeare is sharpening his quill — words that SELL incoming")
        while self.running:
            try:
                await self._process_cycle()
                await asyncio.sleep(120)  # Check every 2 minutes
            except Exception as e:
                print(f"❌ Shakespeare dropped his quill: {e}")
                await asyncio.sleep(60)

    async def _process_cycle(self):
        """Write content for any approved products that are missing titles/descriptions"""
        from database.models import Product, AgentLog
        products = self.session.query(Product).filter(
            Product.is_approved == True,
            Product.description == None
        ).limit(15).all()

        for product in products:
            try:
                design_prompt = product.title or "trending graphic design"
                versions = await self.generate_product_content(
                    design_prompt=design_prompt,
                    product_type=product.product_type or "t-shirt",
                    generate_variants=1,
                )
                if versions:
                    await self.update_product_content(product.id, versions[0])
                    log = AgentLog(agent_name='content_writer', action='content_written',
                                   status='success', details={'product_id': product.id})
                    self.session.add(log)
                    self.session.commit()
            except Exception as e:
                print(f"❌ Content writing failed for product {product.id}: {e}")

    def stop(self):
        """Stop the agent"""
        self.running = False
        print("🛑 Shakespeare has exited stage left")


# Standalone run
async def run_content_writer_agent():
    """Run content writer agent standalone"""
    from database.models import init_database
    from config.settings import config
    
    engine = init_database(config.database_path)
    session = get_session(engine)
    
    agent = ContentWriterAgent(session)
    
    # Test generation
    versions = await agent.generate_product_content(
        design_prompt="Funny cat meme with coffee",
        product_type="t-shirt",
        generate_variants=2
    )
    
    for v in versions:
        print(f"\nVersion: {v.version_id}")
        print(f"Title: {v.title}")
        print(f"Tags: {v.tags}")


if __name__ == "__main__":
    asyncio.run(run_content_writer_agent())
