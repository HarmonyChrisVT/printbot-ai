"""
PrintBot AI - Social Agent
===========================
Manages social media presence, posts content, engages with audience.
Schedule: Every 6 hours
Platforms: Instagram, TikTok
"""
import asyncio
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import os
from pathlib import Path

from ..config.settings import config
from ..database.models import SocialPost, Product, AgentLog, get_session


class HumanEmulator:
    """Emulates human behavior with realistic delays and patterns"""
    
    def __init__(self):
        self.min_delay = config.social.human_delay_min
        self.max_delay = config.social.human_delay_max
    
    async def random_delay(self):
        """Wait for a random human-like duration"""
        delay = random.randint(self.min_delay, self.max_delay)
        await asyncio.sleep(delay)
    
    async def typing_delay(self, text: str):
        """Simulate typing time"""
        # Average typing speed: 40 WPM = ~200 chars/min = ~3.3 chars/sec
        chars_per_second = random.uniform(2.5, 5.0)
        delay = len(text) / chars_per_second
        await asyncio.sleep(delay)
    
    def generate_human_hours(self) -> List[int]:
        """Generate realistic active hours (not 24/7)"""
        # Peak social media hours
        peak_hours = [7, 8, 12, 13, 17, 18, 19, 20, 21, 22]
        # Off-peak but still active
        off_peak = [6, 9, 10, 11, 14, 15, 16, 23]
        
        # Randomly select hours to be active
        active_hours = random.sample(peak_hours, k=random.randint(4, 6))
        active_hours.extend(random.sample(off_peak, k=random.randint(2, 4)))
        
        return sorted(active_hours)


class ContentGenerator:
    """Generates social media content"""
    
    def __init__(self):
        self.caption_templates = {
            'funny': [
                "😂 {product_title} - Because life's too short for boring clothes!\n\n🔗 Link in bio!\n\n{hashtags}",
                "When you see it... 👀\n\n{product_title} is here to make your day!\n\n{hashtags}",
                "POV: You just found your new favorite {product_type} 😍\n\n{hashtags}"
            ],
            'motivational': [
                "✨ {product_title} - Wear your motivation!\n\nWhat's your goal for this week? 👇\n\n{hashtags}",
                "Dream big. Work hard. Look good doing it. 💪\n\n{product_title}\n\n{hashtags}",
                "Your daily reminder that you're amazing! 🌟\n\n{hashtags}"
            ],
            'aesthetic': [
                "vibes only ✨\n\n{product_title}\n\n{hashtags}",
                "aesthetic: unlocked 🔓\n\n{hashtags}",
                "this {product_type} tho 😮‍💨\n\n{hashtags}"
            ],
            'promotional': [
                "🚨 NEW DROP 🚨\n\n{product_title} is now available!\n\nLimited time - grab yours before they're gone!\n\n{hashtags}",
                "Flash sale alert! ⚡ {discount}% off for the next 24 hours!\n\n{hashtags}",
                "Tag someone who needs this! 👇\n\n{product_title}\n\n{hashtags}"
            ]
        }
        
        self.hashtag_sets = {
            'general': ["#printondemand", "#customapparel", "#uniquegifts", "#shoplocal", "#smallbusiness"],
            'funny': ["#funny", "#meme", "#lol", "#humor", "#funnytshirts", "#giftideas"],
            'motivational': ["#motivation", "#inspiration", "#hustle", "#goals", "#mindset", "#success"],
            'aesthetic': ["#aesthetic", "#vibes", "#style", "#fashion", "#ootd", "#instagood"],
            'trending': ["#trending", "#viral", "#explore", "#discover", "#musthave", "#trendy"]
        }
    
    def generate_caption(self, product: Product, style: str = 'funny') -> str:
        """Generate a caption for a product"""
        templates = self.caption_templates.get(style, self.caption_templates['funny'])
        template = random.choice(templates)
        
        hashtags = self._generate_hashtags(style)
        
        caption = template.format(
            product_title=product.title,
            product_type=product.product_type or 'item',
            hashtags=' '.join(hashtags),
            discount=random.choice([10, 15, 20, 25])
        )
        
        return caption
    
    def _generate_hashtags(self, style: str, count: int = 15) -> List[str]:
        """Generate relevant hashtags"""
        hashtags = []
        
        # Add style-specific hashtags
        hashtags.extend(self.hashtag_sets.get(style, self.hashtag_sets['general']))
        
        # Add general hashtags
        hashtags.extend(self.hashtag_sets['general'])
        
        # Add trending hashtags
        hashtags.extend(random.sample(self.hashtag_sets['trending'], k=3))
        
        # Shuffle and limit
        random.shuffle(hashtags)
        return hashtags[:count]
    
    def generate_comment_reply(self, comment: str, tone: str = 'friendly') -> str:
        """Generate a reply to a comment"""
        replies = {
            'friendly': [
                "Thanks so much! 🙏",
                "So glad you like it! 💕",
                "You made our day! 😊",
                "Appreciate the love! 🫶",
                "Thanks for the support! 🙌"
            ],
            'question': [
                "Great question! DM us for more details 📩",
                "Check our bio for the link! 🔗",
                "We'd love to help! Send us a message 💬",
                "Yes! Available now - link in bio 🛍️"
            ],
            'enthusiastic': [
                "YESSS! 🔥🔥🔥",
                "This! 💯",
                "Couldn't agree more! 🙌",
                "Absolutely! ✨"
            ]
        }
        
        # Determine tone based on comment
        if '?' in comment or 'how' in comment.lower():
            tone = 'question'
        elif any(word in comment.lower() for word in ['love', 'amazing', 'awesome', 'great']):
            tone = 'enthusiastic'
        
        return random.choice(replies.get(tone, replies['friendly']))


class InstagramAPI:
    """Instagram API wrapper"""
    
    def __init__(self, account: Dict):
        self.username = account.get('username')
        self.password = account.get('password')
        self.api_key = account.get('api_key')
        self.is_active = account.get('is_active', False)
    
    async def post_image(self, image_path: str, caption: str) -> Optional[str]:
        """Post an image to Instagram"""
        # This would use Instagram Basic Display API or Graph API
        # For now, return mock post ID
        print(f"📷 Would post to Instagram @{self.username}: {caption[:50]}...")
        return f"mock_post_{datetime.now().timestamp()}"
    
    async def like_post(self, post_id: str) -> bool:
        """Like a post"""
        print(f"❤️ Would like post {post_id}")
        return True
    
    async def comment_on_post(self, post_id: str, comment: str) -> bool:
        """Comment on a post"""
        print(f"💬 Would comment on {post_id}: {comment[:50]}...")
        return True
    
    async def follow_user(self, user_id: str) -> bool:
        """Follow a user"""
        print(f"👤 Would follow user {user_id}")
        return True
    
    async def send_dm(self, user_id: str, message: str) -> bool:
        """Send direct message"""
        print(f"📩 Would DM {user_id}: {message[:50]}...")
        return True
    
    async def get_notifications(self) -> List[Dict]:
        """Get notifications (likes, comments, follows)"""
        # Mock notifications
        return []


class TikTokAPI:
    """TikTok API wrapper"""
    
    def __init__(self, account: Dict):
        self.username = account.get('username')
        self.password = account.get('password')
        self.api_key = account.get('api_key')
        self.is_active = account.get('is_active', False)
    
    async def post_video(self, video_path: str, caption: str) -> Optional[str]:
        """Post a video to TikTok"""
        print(f"🎵 Would post to TikTok @{self.username}: {caption[:50]}...")
        return f"mock_video_{datetime.now().timestamp()}"
    
    async def like_video(self, video_id: str) -> bool:
        """Like a video"""
        print(f"❤️ Would like TikTok {video_id}")
        return True
    
    async def comment_on_video(self, video_id: str, comment: str) -> bool:
        """Comment on a video"""
        print(f"💬 Would comment on TikTok {video_id}")
        return True


class SocialAgent:
    """
    Main Social Agent
    Manages social media presence across platforms
    """
    
    def __init__(self, db_session):
        self.session = db_session
        self.human = HumanEmulator()
        self.content = ContentGenerator()
        
        # Initialize platform APIs
        self.instagram_accounts = [
            InstagramAPI(acc) for acc in config.social.instagram_accounts if acc.get('is_active')
        ]
        self.tiktok_accounts = [
            TikTokAPI(acc) for acc in config.social.tiktok_accounts if acc.get('is_active')
        ]
        
        self.running = False
        self.daily_actions = 0
        self.last_action_reset = datetime.utcnow()
    
    async def run(self):
        """Main agent loop"""
        self.running = True
        print("📱 Social Agent started")
        
        while self.running:
            try:
                # Reset daily action counter
                if datetime.utcnow() - self.last_action_reset > timedelta(days=1):
                    self.daily_actions = 0
                    self.last_action_reset = datetime.utcnow()
                
                # Check if we're within daily limits
                if self.daily_actions < config.social.max_daily_actions:
                    await self._process_cycle()
                else:
                    print("⏭️ Daily action limit reached")
                
                # Wait for next interval
                await asyncio.sleep(6 * 3600)  # 6 hours
                
            except Exception as e:
                self._log_error(f"Social agent error: {e}")
                await asyncio.sleep(600)  # Wait 10 min on error
    
    async def _process_cycle(self):
        """Process one social media cycle"""
        print("📱 Running social media cycle...")
        
        # 1. Create and schedule new posts
        await self._create_posts()
        
        # 2. Engage with audience (respond to comments, DMs)
        await self._engage_with_audience()
        
        # 3. Growth activities (like, comment, follow)
        await self._growth_activities()
        
        print("📱 Social cycle complete")
    
    async def _create_posts(self):
        """Create new social media posts"""
        # Get products that haven't been posted recently
        products = self.session.query(Product).filter(
            Product.is_active == True,
            Product.is_approved == True
        ).order_by(Product.updated_at.desc()).limit(5).all()
        
        for product in products:
            # Check if already posted recently
            recent_post = self.session.query(SocialPost).filter(
                SocialPost.product_id == product.id,
                SocialPost.posted_at >= datetime.utcnow() - timedelta(days=7)
            ).first()
            
            if recent_post:
                continue
            
            # Generate content
            caption = self.content.generate_caption(product, style=random.choice(['funny', 'motivational', 'aesthetic']))
            
            # Post to Instagram
            for ig in self.instagram_accounts:
                if ig.is_active and self.daily_actions < config.social.max_daily_actions:
                    await self.human.random_delay()
                    
                    post_id = await ig.post_image(product.design_url, caption)
                    
                    if post_id:
                        social_post = SocialPost(
                            platform='instagram',
                            account_username=ig.username,
                            content_type='image',
                            caption=caption,
                            product_id=product.id,
                            product_url=f"https://{config.shopify.shop_url}/products/{product.shopify_id}",
                            status='posted',
                            posted_at=datetime.utcnow(),
                            external_post_id=post_id
                        )
                        self.session.add(social_post)
                        self.daily_actions += 1
                        
                        self._log_action("instagram_post", "success", {
                            "product_id": product.id,
                            "username": ig.username
                        })
            
            # Post to TikTok (would need video content)
            # For now, skip TikTok or create slideshow
            
        self.session.commit()
    
    async def _engage_with_audience(self):
        """Respond to comments and DMs"""
        if not config.social.auto_comment:
            return
        
        for ig in self.instagram_accounts:
            if not ig.is_active:
                continue
            
            # Get notifications
            notifications = await ig.get_notifications()
            
            for notif in notifications:
                if self.daily_actions >= config.social.max_daily_actions:
                    break
                
                if notif.get('type') == 'comment':
                    reply = self.content.generate_comment_reply(notif.get('text', ''))
                    await self.human.typing_delay(reply)
                    await ig.comment_on_post(notif.get('post_id'), reply)
                    self.daily_actions += 1
    
    async def _growth_activities(self):
        """Perform growth-focused activities"""
        if self.daily_actions >= config.social.max_daily_actions:
            return
        
        # Like posts from target audience
        if config.social.auto_like:
            for ig in self.instagram_accounts:
                if ig.is_active and self.daily_actions < config.social.max_daily_actions:
                    await self.human.random_delay()
                    # Would search for relevant hashtags and like posts
                    self.daily_actions += 1
        
        # Follow relevant accounts
        if config.social.auto_follow:
            for ig in self.instagram_accounts:
                if ig.is_active and self.daily_actions < config.social.max_daily_actions:
                    await self.human.random_delay()
                    # Would find and follow target accounts
                    self.daily_actions += 1
    
    def _log_action(self, action: str, status: str, details: Dict):
        """Log agent action"""
        log = AgentLog(
            agent_name='social',
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
        print("🛑 Social Agent stopped")


# Standalone run function
async def run_social_agent():
    """Run social agent standalone"""
    from ..database.models import init_database
    
    engine = init_database(config.database_path)
    session = get_session(engine)
    
    agent = SocialAgent(session)
    await agent.run()


if __name__ == "__main__":
    asyncio.run(run_social_agent())
