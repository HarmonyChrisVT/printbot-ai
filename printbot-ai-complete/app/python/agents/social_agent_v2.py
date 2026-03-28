"""
Social Agent V2 - Enhanced social media with backup accounts and human emulation
"""

import os
import random
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from openai import AsyncOpenAI
from python.utils.logger import get_logger

logger = get_logger(__name__)

class HumanEmulatorV2:
    """Emulates human behavior with realistic delays"""
    
    def __init__(self):
        self.min_delay = 20      # 20 seconds minimum
        self.max_delay = 120     # 120 seconds maximum
        self.typing_speed_wpm = random.randint(35, 65)  # Human typing speed
    
    async def emulate_action(self, action_type: str = 'post'):
        """Emulate human action delay"""
        if action_type == 'post':
            delay = random.randint(self.min_delay, self.max_delay)
        elif action_type == 'scroll':
            delay = random.randint(5, 15)
        elif action_type == 'type':
            delay = random.randint(10, 30)
        else:
            delay = random.randint(self.min_delay, self.max_delay)
        
        logger.info(f"Human emulation: waiting {delay}s before {action_type}")
        await asyncio.sleep(delay)
    
    async def emulate_typing(self, text: str):
        """Emulate typing time"""
        words = len(text.split())
        typing_time = (words / self.typing_speed_wpm) * 60  # seconds
        # Add variance
        typing_time *= random.uniform(0.8, 1.3)
        await asyncio.sleep(min(typing_time, 60))  # Cap at 60s

class SocialAccountManager:
    """Manages multiple social accounts with auto-failover"""
    
    def __init__(self):
        self.accounts = {
            'instagram': [],
            'tiktok': [],
            'pinterest': []
        }
        self.primary_accounts = {}
    
    def add_account(self, platform: str, account_name: str, api_key: str, is_primary: bool = False):
        """Add a social account"""
        account = {
            'name': account_name,
            'api_key': api_key,
            'is_active': True,
            'is_primary': is_primary,
            'posts_today': 0,
            'last_post_time': None,
            'rate_limit_hits': 0
        }
        
        self.accounts[platform].append(account)
        
        if is_primary:
            self.primary_accounts[platform] = account
    
    def get_active_account(self, platform: str) -> Optional[Dict]:
        """Get an active account for the platform"""
        accounts = self.accounts.get(platform, [])
        
        # Try primary first
        if platform in self.primary_accounts:
            primary = self.primary_accounts[platform]
            if primary['is_active']:
                return primary
        
        # Find any active account
        for account in accounts:
            if account['is_active']:
                return account
        
        return None
    
    def mark_account_limited(self, platform: str, account_name: str):
        """Mark an account as rate limited"""
        for account in self.accounts.get(platform, []):
            if account['name'] == account_name:
                account['rate_limit_hits'] += 1
                if account['rate_limit_hits'] >= 3:
                    account['is_active'] = False
                    logger.warning(f"Account {account_name} on {platform} deactivated due to rate limits")
                break

class SocialAgentV2:
    """Enhanced social media agent with human emulation and backup accounts"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.emulator = HumanEmulatorV2()
        self.account_manager = SocialAccountManager()
        self.platforms = ['instagram', 'tiktok', 'pinterest']
        self.posts_today = 0
        self.max_posts_per_day = 15
    
    async def configure(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Configure the social agent"""
        # Setup Instagram accounts
        for i, key in enumerate(config.get('instagram_api_keys', [])):
            self.account_manager.add_account(
                'instagram',
                f"instagram_account_{i+1}",
                key,
                is_primary=(i == 0)
            )
        
        # Setup TikTok accounts
        for i, key in enumerate(config.get('tiktok_api_keys', [])):
            self.account_manager.add_account(
                'tiktok',
                f"tiktok_account_{i+1}",
                key,
                is_primary=(i == 0)
            )
        
        # Setup Pinterest accounts
        for i, key in enumerate(config.get('pinterest_api_keys', [])):
            self.account_manager.add_account(
                'pinterest',
                f"pinterest_account_{i+1}",
                key,
                is_primary=(i == 0)
            )
        
        return {'status': 'configured', 'accounts': self.account_manager.accounts}
    
    async def create_post(
        self, 
        platform: str, 
        content_type: str = 'product',
        product_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Create a social media post with human emulation"""
        
        if self.posts_today >= self.max_posts_per_day:
            return {'error': 'Daily post limit reached'}
        
        # Get active account
        account = self.account_manager.get_active_account(platform)
        if not account:
            return {'error': f'No active accounts available for {platform}'}
        
        logger.info(f"Creating {content_type} post for {platform} using {account['name']}")
        
        # Step 1: Emulate human delay before posting
        await self.emulator.emulate_action('post')
        
        # Step 2: Generate content
        content = await self._generate_content(platform, content_type, product_data)
        
        # Step 3: Emulate typing
        await self.emulator.emulate_typing(content['caption'])
        
        # Step 4: Post to platform
        post_result = await self._post_to_platform(platform, account, content)
        
        if post_result.get('rate_limited'):
            self.account_manager.mark_account_limited(platform, account['name'])
            # Try with backup account
            return await self.create_post(platform, content_type, product_data)
        
        self.posts_today += 1
        account['posts_today'] += 1
        account['last_post_time'] = datetime.now()
        
        return {
            'success': True,
            'platform': platform,
            'account': account['name'],
            'content': content,
            'post_url': post_result.get('url'),
            'posted_at': datetime.now().isoformat()
        }
    
    async def _generate_content(
        self, 
        platform: str, 
        content_type: str,
        product_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Generate social media content using AI"""
        
        platform_tones = {
            'instagram': 'visual-focused, trendy, engaging',
            'tiktok': 'fun, energetic, viral-worthy',
            'pinterest': 'inspirational, searchable, keyword-rich'
        }
        
        tone = platform_tones.get(platform, 'engaging')
        
        if content_type == 'product' and product_data:
            prompt = f"""Create a {platform} post for this product:
            
            Product: {product_data.get('name', '')}
            Description: {product_data.get('description', '')}
            Tags: {', '.join(product_data.get('tags', []))}
            
            Tone: {tone}
            
            Provide:
            1. Engaging caption (include relevant hashtags)
            2. Call-to-action
            3. Best posting time recommendation
            
            Format as JSON."""
        else:
            prompt = f"""Create an engaging {platform} post about print-on-demand merchandise.
            
            Tone: {tone}
            
            Provide:
            1. Engaging caption (include relevant hashtags)
            2. Call-to-action
            3. Best posting time recommendation
            
            Format as JSON."""
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": f"You are a social media expert for {platform}."},
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
                    'caption': content[:500],
                    'hashtags': '#printondemand #custommerch',
                    'call_to_action': 'Shop now!',
                    'best_time': '7 PM'
                }
        except Exception as e:
            logger.error(f"Content generation error: {e}")
            return {
                'caption': 'Check out our latest designs! 🎨',
                'hashtags': '#printondemand #custommerch #newarrival',
                'call_to_action': 'Link in bio!',
                'best_time': '7 PM'
            }
    
    async def _post_to_platform(
        self, 
        platform: str, 
        account: Dict, 
        content: Dict
    ) -> Dict[str, Any]:
        """Post to social platform"""
        # In production, this would use actual API calls
        # For now, simulate posting
        
        # Simulate occasional rate limiting (5% chance)
        if random.random() < 0.05:
            return {'rate_limited': True, 'retry_after': 3600}
        
        # Simulate post URL
        post_id = f"post_{random.randint(100000, 999999)}"
        
        urls = {
            'instagram': f"https://instagram.com/p/{post_id}",
            'tiktok': f"https://tiktok.com/@{account['name']}/video/{post_id}",
            'pinterest': f"https://pinterest.com/pin/{post_id}"
        }
        
        return {
            'success': True,
            'url': urls.get(platform, f"https://{platform}.com/{post_id}"),
            'post_id': post_id
        }
    
    async def schedule_posts(self, posts: List[Dict]) -> Dict[str, Any]:
        """Schedule multiple posts"""
        scheduled = []
        
        for post in posts:
            # Add random delay between scheduled posts
            delay = random.randint(30, 180)
            await asyncio.sleep(0.1)  # Don't block
            
            scheduled.append({
                'platform': post['platform'],
                'scheduled_time': (datetime.now() + timedelta(minutes=delay)).isoformat(),
                'content_type': post.get('content_type', 'product')
            })
        
        return {'scheduled': scheduled, 'total': len(scheduled)}
    
    async def get_analytics(self) -> Dict[str, Any]:
        """Get social media analytics"""
        # In production, this would fetch real analytics
        return {
            'total_posts': self.posts_today,
            'total_reach': random.randint(1000, 10000),
            'total_engagement': random.randint(100, 1000),
            'engagement_rate': round(random.uniform(2, 8), 2),
            'followers_gained': random.randint(10, 100),
            'top_performing_platform': random.choice(self.platforms),
            'accounts_status': {
                platform: len([a for a in accounts if a['is_active']])
                for platform, accounts in self.account_manager.accounts.items()
            }
        }
