"""
Design Agent - Scans trends and generates AI designs
"""

import os
import json
import random
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

from openai import AsyncOpenAI
from python.utils.logger import get_logger

logger = get_logger(__name__)

class DesignAgent:
    """AI agent that creates trending designs for print-on-demand products"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.niches = [
            'fitness', 'pets', 'travel', 'food', 'gaming', 'music',
            'motivation', 'funny', 'family', 'career', 'hobbies', 'sports'
        ]
        self.product_types = [
            't-shirt', 'hoodie', 'mug', 'poster', 'phone_case', 'tote_bag'
        ]
    
    async def configure(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Configure the design agent"""
        self.niche = config.get('niche', 'general')
        return {'status': 'configured', 'niche': self.niche}
    
    async def scan_trends(self, niche: Optional[str] = None) -> List[Dict[str, Any]]:
        """Scan for trending design ideas"""
        target_niche = niche or self.niche or random.choice(self.niches)
        
        logger.info(f"Scanning trends for niche: {target_niche}")
        
        # Use AI to generate trending concepts
        prompt = f"""Generate 5 trending design concepts for print-on-demand {target_niche} merchandise.
        
        For each concept, provide:
        1. A catchy design name
        2. A detailed visual description for image generation
        3. Target audience
        4. Why it's trending
        5. Suggested tags (5-7 tags)
        
        Format as JSON array."""
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a trend analysis expert for print-on-demand businesses."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8
            )
            
            content = response.choices[0].message.content
            # Extract JSON from response
            try:
                trends = json.loads(content)
            except:
                # Try to extract JSON from markdown code block
                import re
                json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
                if json_match:
                    trends = json.loads(json_match.group(1))
                else:
                    trends = []
            
            logger.info(f"Found {len(trends)} trending concepts")
            return trends
            
        except Exception as e:
            logger.error(f"Trend scanning error: {e}")
            return []
    
    async def generate_design(
        self, 
        prompt: Optional[str] = None, 
        use_trending: bool = True,
        product_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a complete design"""
        
        # Get trending concept if requested
        if use_trending and not prompt:
            trends = await self.scan_trends()
            if trends:
                selected = random.choice(trends)
                concept = selected
            else:
                concept = self._generate_fallback_concept()
        elif prompt:
            concept = await self._expand_concept(prompt)
        else:
            concept = self._generate_fallback_concept()
        
        product = product_type or random.choice(self.product_types)
        
        logger.info(f"Generating design: {concept.get('name', 'Untitled')} for {product}")
        
        # Generate the actual image
        image_url = await self._generate_image(concept.get('visual_description', concept.get('description', '')))
        
        # Generate mockups
        mockup_urls = await self._generate_mockups(image_url, product)
        
        # Calculate base cost
        base_cost = self._get_base_cost(product)
        
        design_result = {
            'name': concept.get('name', f'Trending {product.title()} Design'),
            'concept': concept.get('description', ''),
            'visual_description': concept.get('visual_description', ''),
            'product_type': product,
            'design_url': image_url,
            'mockup_urls': mockup_urls,
            'base_cost': base_cost,
            'tags': concept.get('tags', []),
            'niche': concept.get('niche', 'general'),
            'trending_score': random.uniform(0.6, 0.95),
            'target_audience': concept.get('target_audience', 'General audience'),
            'why_trending': concept.get('why_trending', 'Popular design style'),
            'created_at': datetime.now().isoformat()
        }
        
        logger.info(f"Design generated: {design_result['name']}")
        return design_result
    
    async def _expand_concept(self, prompt: str) -> Dict[str, Any]:
        """Expand a simple prompt into a full concept"""
        ai_prompt = f"""Expand this design idea into a full concept:
        
        Idea: {prompt}
        
        Provide:
        1. A catchy name
        2. Detailed visual description for AI image generation
        3. Target audience
        4. 5-7 relevant tags
        
        Format as JSON."""
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a creative design expert."},
                    {"role": "user", "content": ai_prompt}
                ],
                temperature=0.8
            )
            
            content = response.choices[0].message.content
            try:
                concept = json.loads(content)
            except:
                concept = {
                    'name': prompt[:50],
                    'description': prompt,
                    'visual_description': prompt,
                    'tags': prompt.split()[:5]
                }
            
            return concept
            
        except Exception as e:
            logger.error(f"Concept expansion error: {e}")
            return {
                'name': prompt[:50],
                'description': prompt,
                'visual_description': prompt,
                'tags': prompt.split()[:5]
            }
    
    async def _generate_image(self, description: str) -> str:
        """Generate image using DALL-E"""
        try:
            # Enhance prompt for better results
            enhanced_prompt = f"""Professional print-on-demand design: {description}
            
            Style: Clean, high-quality, suitable for printing on merchandise.
            Background: Transparent or solid color.
            Format: Centered composition, ready for product placement."""
            
            response = await self.client.images.generate(
                model="dall-e-3",
                prompt=enhanced_prompt[:1000],
                size="1024x1024",
                quality="standard",
                n=1
            )
            
            return response.data[0].url
            
        except Exception as e:
            logger.error(f"Image generation error: {e}")
            # Return placeholder
            return f"https://via.placeholder.com/1024x1024?text=Design+Placeholder"
    
    async def _generate_mockups(self, design_url: str, product_type: str) -> List[str]:
        """Generate product mockups"""
        # In production, this would use a mockup API
        # For now, return placeholder mockups
        return [
            f"https://via.placeholder.com/600x600?text={product_type.title()}+Mockup+1",
            f"https://via.placeholder.com/600x600?text={product_type.title()}+Mockup+2",
            f"https://via.placeholder.com/600x600?text={product_type.title()}+Mockup+3"
        ]
    
    def _get_base_cost(self, product_type: str) -> float:
        """Get base cost for product type"""
        costs = {
            't-shirt': 8.50,
            'hoodie': 18.00,
            'mug': 5.50,
            'poster': 6.00,
            'phone_case': 7.00,
            'tote_bag': 9.00
        }
        return costs.get(product_type, 8.00)
    
    def _generate_fallback_concept(self) -> Dict[str, Any]:
        """Generate a fallback concept if AI fails"""
        templates = [
            {
                'name': 'Stay Wild',
                'description': 'Nature-inspired adventure design',
                'visual_description': 'Mountain silhouette with sun rays, retro style',
                'tags': ['nature', 'adventure', 'outdoors', 'mountains', 'travel'],
                'niche': 'travel'
            },
            {
                'name': 'Coffee & Code',
                'description': 'Programmer humor design',
                'visual_description': 'Coffee cup with code symbols, minimalist style',
                'tags': ['coding', 'programming', 'coffee', 'developer', 'tech'],
                'niche': 'career'
            },
            {
                'name': 'Dog Mom Life',
                'description': 'Pet parent pride design',
                'visual_description': 'Cute dog paw prints with heart, playful style',
                'tags': ['dogs', 'pets', 'dog mom', 'animals', 'cute'],
                'niche': 'pets'
            }
        ]
        return random.choice(templates)
