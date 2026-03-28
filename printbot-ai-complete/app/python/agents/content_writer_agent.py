"""
Content Writer Agent - SEO product descriptions and marketing copy
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime

from openai import AsyncOpenAI
from python.utils.logger import get_logger

logger = get_logger(__name__)

class ContentWriterAgent:
    """AI agent that writes SEO-optimized product descriptions and marketing content"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    async def configure(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Configure the content writer"""
        return {'status': 'configured'}
    
    async def write_product_description(
        self, 
        product_name: str,
        design_concept: str,
        niche: str,
        keywords: Optional[list] = None
    ) -> str:
        """Write SEO-optimized product description"""
        
        logger.info(f"Writing description for: {product_name}")
        
        prompt = f"""Write an SEO-optimized product description for:
        
        Product Name: {product_name}
        Design Concept: {design_concept}
        Niche: {niche}
        Target Keywords: {', '.join(keywords) if keywords else 'auto-generate'}
        
        Requirements:
        - 150-200 words
        - Include benefits and features
        - Use persuasive copywriting
        - Include target keywords naturally
        - End with a call-to-action
        
        Also provide:
        1. SEO title (60 chars max)
        2. Meta description (160 chars max)
        3. 5-7 relevant tags
        
        Format as JSON with 'description', 'seo_title', 'meta_description', 'tags'."""
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert e-commerce copywriter and SEO specialist."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            import json
            content = response.choices[0].message.content
            try:
                result = json.loads(content)
                return result.get('description', content)
            except:
                return content
                
        except Exception as e:
            logger.error(f"Description generation error: {e}")
            return f"Premium quality {product_name}. Perfect for {niche} enthusiasts. Order yours today!"
    
    async def write_ad_copy(
        self, 
        product_name: str,
        platform: str,
        audience: Optional[str] = None
    ) -> Dict[str, Any]:
        """Write ad copy for different platforms"""
        
        platform_specs = {
            'facebook': 'Engaging, visual, 125 chars primary text',
            'instagram': 'Short, hashtag-heavy, visual focus',
            'google': 'Keyword-rich, benefit-focused',
            'tiktok': 'Trendy, fun, call-to-action heavy'
        }
        
        spec = platform_specs.get(platform, 'General ad copy')
        
        prompt = f"""Write {platform} ad copy for:
        
        Product: {product_name}
        Target Audience: {audience or 'general'}
        Platform Specs: {spec}
        
        Provide:
        1. Headline (30 chars max)
        2. Primary text
        3. Call-to-action
        4. 3-5 relevant hashtags
        
        Format as JSON."""
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a digital marketing expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8
            )
            
            import json
            content = response.choices[0].message.content
            try:
                return json.loads(content)
            except:
                return {
                    'headline': product_name[:30],
                    'primary_text': f"Check out our amazing {product_name}!",
                    'call_to_action': 'Shop Now',
                    'hashtags': '#trending #musthave #shopnow'
                }
                
        except Exception as e:
            logger.error(f"Ad copy generation error: {e}")
            return {
                'headline': product_name[:30],
                'primary_text': f"Check out our amazing {product_name}!",
                'call_to_action': 'Shop Now',
                'hashtags': '#trending #musthave #shopnow'
            }
    
    async def write_email_campaign(
        self,
        campaign_type: str,
        products: list,
        segment: Optional[str] = None
    ) -> Dict[str, Any]:
        """Write email campaign content"""
        
        campaign_types = {
            'welcome': 'Welcome new subscribers',
            'promotional': 'Special offer or sale',
            'new_arrival': 'New product announcement',
            'abandoned_cart': 'Recover abandoned carts',
            'review_request': 'Ask for product reviews'
        }
        
        prompt = f"""Write an email campaign for:
        
        Type: {campaign_types.get(campaign_type, campaign_type)}
        Products: {', '.join([p['name'] for p in products])}
        Audience Segment: {segment or 'all subscribers'}
        
        Provide:
        1. Subject line (50 chars max, include emoji)
        2. Preview text (100 chars max)
        3. Email body (HTML format)
        4. Call-to-action button text
        
        Format as JSON."""
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an email marketing expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            import json
            content = response.choices[0].message.content
            try:
                return json.loads(content)
            except:
                return {
                    'subject': f"🎉 Don't Miss Out!",
                    'preview_text': 'Amazing deals inside...',
                    'body': '<p>Check out our latest products!</p>',
                    'cta': 'Shop Now'
                }
                
        except Exception as e:
            logger.error(f"Email campaign generation error: {e}")
            return {
                'subject': f"🎉 Don't Miss Out!",
                'preview_text': 'Amazing deals inside...',
                'body': '<p>Check out our latest products!</p>',
                'cta': 'Shop Now'
            }
    
    async def generate_blog_post(self, topic: str, keywords: list) -> Dict[str, Any]:
        """Generate a blog post for content marketing"""
        
        prompt = f"""Write a blog post about:
        
        Topic: {topic}
        Keywords: {', '.join(keywords)}
        
        Requirements:
        - 500-800 words
        - SEO-optimized
        - Include H2 and H3 headings
        - End with a call-to-action
        
        Provide:
        1. Title (60 chars max)
        2. Meta description
        3. Blog content (HTML)
        4. 3-5 internal link suggestions
        
        Format as JSON."""
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a content marketing expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            import json
            content = response.choices[0].message.content
            try:
                return json.loads(content)
            except:
                return {
                    'title': topic[:60],
                    'meta_description': f"Read about {topic}",
                    'content': f'<p>{topic} is an interesting subject...</p>',
                    'internal_links': []
                }
                
        except Exception as e:
            logger.error(f"Blog post generation error: {e}")
            return {
                'title': topic[:60],
                'meta_description': f"Read about {topic}",
                'content': f'<p>{topic} is an interesting subject...</p>',
                'internal_links': []
            }
