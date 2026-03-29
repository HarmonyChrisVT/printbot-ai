"""
PrintBot AI - Social Agent V2
==============================
Enhanced social media with backup accounts and auto-switch
Platforms: Instagram (3 accounts), TikTok (3 accounts)
Human emulation: 20-120 second delays
Schedule: Every 6 hours
"""
import asyncio
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import json
from dataclasses import dataclass

from config.settings import config
from database.models import SocialPost, Product, AgentLog, get_session


@dataclass
class AccountStatus:
    """Social account status"""
    platform: str
    username: str
    is_active: bool
    is_primary: bool
    is_banned: bool
    last_post: datetime
    daily_actions: int
    failure_count: int


class HumanEmulatorV2:
    """Enhanced human behavior emulation"""
    
    def __init__(self):
        # Updated delays: 20-120 seconds as requested
        self.min_delay = 20
        self.max_delay = 120
        self.typing_wpm_range = (35, 55)  # Human typing speed
        self.active_hours = self._generate_active_hours()
    
    async def random_delay(self, min_override: int = None, max_override: int = None):
        """Wait for a random human-like duration (20-120 seconds)"""
        min_d = min_override or self.min_delay
        max_d = max_override or self.max_delay
        delay = random.randint(min_d, max_d)
        
        # Add some randomness to feel more human
        if random.random() < 0.1:  # 10% chance of longer delay
            delay = int(delay * random.uniform(1.5, 2.5))
        
        print(f"⏱️  Human delay: {delay}s")
        await asyncio.sleep(delay)
    
    async def typing_delay(self, text: str):
        """Simulate realistic typing time"""
        wpm = random.randint(*self.typing_wpm_range)
        chars_per_minute = wpm * 5  # Average word length
        chars_per_second = chars_per_minute / 60
        
        # Add pauses for thinking
        thinking_pauses = len(text) // 20  # Pause every ~20 chars
        thinking_time = thinking_pauses * random.uniform(0.5, 2.0)
        
        typing_time = len(text) / chars_per_second
        total_delay = typing_time + thinking_time
        
        await asyncio.sleep(total_delay)
    
    async def scroll_delay(self):
        """Simulate scrolling pause"""
        delay = random.uniform(2, 8)
        await asyncio.sleep(delay)
    
    async def engagement_delay(self):
        """Delay between engagement actions"""
        # Shorter delays for likes/comments
        delay = random.randint(10, 45)
        await asyncio.sleep(delay)
    
    def _generate_active_hours(self) -> List[int]:
        """Generate realistic active hours"""
        # Peak social media hours with some randomness
        peak_hours = [7, 8, 12, 13, 17, 18, 19, 20, 21, 22]
        off_peak = [6, 9, 10, 11, 14, 15, 16, 23]
        
        # Randomly select hours
        active = random.sample(peak_hours, k=random.randint(4, 7))
        active.extend(random.sample(off_peak, k=random.randint(2, 4)))
        
        return sorted(set(active))
    
    def is_active_hour(self) -> bool:
        """Check if current hour is an active hour"""
        current_hour = datetime.utcnow().hour
        return current_hour in self.active_hours
    
    def get_next_active_hour(self) -> int:
        """Get next active hour"""
        current_hour = datetime.utcnow().hour
        for hour in self.active_hours:
            if hour > current_hour:
                return hour
        return self.active_hours[0]  # Wrap to tomorrow


class SocialAccountManager:
    """Manages multiple social accounts with auto-failover"""
    
    def __init__(self, platform: str, accounts_config: List[Dict]):
        self.platform = platform
        self.accounts: List[AccountStatus] = []
        self.current_account_index = 0
        
        # Initialize accounts from config
        for i, acc_config in enumerate(accounts_config):
            self.accounts.append(AccountStatus(
                platform=platform,
                username=acc_config.get('username', f'account_{i}'),
                is_active=acc_config.get('is_active', False),
                is_primary=acc_config.get('is_primary', i == 0),
                is_banned=False,
                last_post=None,
                daily_actions=0,
                failure_count=0
            ))
    
    def get_active_account(self) -> Optional[AccountStatus]:
        """Get the current active account"""
        # Try primary first
        for account in self.accounts:
            if account.is_primary and account.is_active and not account.is_banned:
                return account
        
        # Then try any active account
        for account in self.accounts:
            if account.is_active and not account.is_banned:
                return account
        
        return None
    
    def get_backup_account(self) -> Optional[AccountStatus]:
        """Get a backup account if primary fails"""
        primary = self.get_active_account()
        if not primary:
            return None
        
        for account in self.accounts:
            if account != primary and account.is_active and not account.is_banned:
                return account
        
        return None
    
    def mark_account_failed(self, username: str):
        """Mark an account as failed"""
        for account in self.accounts:
            if account.username == username:
                account.failure_count += 1
                if account.failure_count >= 3:
                    account.is_banned = True
                    print(f"🚫 Account @{username} marked as banned")
                    
                    # Switch to backup
                    backup = self.get_backup_account()
                    if backup:
                        print(f"🔄 Switched to backup account @{backup.username}")
                break
    
    def reset_daily_counters(self):
        """Reset daily action counters"""
        for account in self.accounts:
            account.daily_actions = 0
    
    def get_all_status(self) -> List[Dict]:
        """Get status of all accounts"""
        return [
            {
                'username': acc.username,
                'is_active': acc.is_active,
                'is_primary': acc.is_primary,
                'is_banned': acc.is_banned,
                'daily_actions': acc.daily_actions,
                'failure_count': acc.failure_count
            }
            for acc in self.accounts
        ]


class InstagramAPIV2:
    """Enhanced Instagram API with account switching"""
    
    def __init__(self, account_manager: SocialAccountManager):
        self.account_manager = account_manager
        self.human = HumanEmulatorV2()
    
    async def post_image(self, image_path: str, caption: str) -> Optional[str]:
        """Post image with failover to backup accounts"""
        account = self.account_manager.get_active_account()
        if not account:
            print("❌ No active Instagram accounts available")
            return None
        
        try:
            # Human-like delay before posting
            await self.human.random_delay(30, 90)
            
            # Would use Instagram API here
            print(f"📷 Posted to Instagram @{account.username}")
            
            account.last_post = datetime.utcnow()
            account.daily_actions += 1
            
            return f"post_{datetime.utcnow().timestamp()}"
            
        except Exception as e:
            print(f"❌ Instagram post failed: {e}")
            self.account_manager.mark_account_failed(account.username)
            
            # Try backup account
            backup = self.account_manager.get_backup_account()
            if backup:
                print(f"🔄 Retrying with backup @{backup.username}")
                return await self.post_image(image_path, caption)
            
            return None
    
    async def like_post(self, post_id: str) -> bool:
        """Like a post"""
        await self.human.engagement_delay()
        
        account = self.account_manager.get_active_account()
        if not account:
            return False
        
        print(f"❤️ Liked post via @{account.username}")
        account.daily_actions += 1
        return True
    
    async def comment_on_post(self, post_id: str, comment: str) -> bool:
        """Comment on a post"""
        await self.human.typing_delay(comment)
        await self.human.engagement_delay()
        
        account = self.account_manager.get_active_account()
        if not account:
            return False
        
        print(f"💬 Commented via @{account.username}")
        account.daily_actions += 1
        return True
    
    async def follow_user(self, user_id: str) -> bool:
        """Follow a user"""
        await self.human.random_delay(20, 60)
        
        account = self.account_manager.get_active_account()
        if not account:
            return False
        
        print(f"👤 Followed user via @{account.username}")
        account.daily_actions += 1
        return True


class TikTokAPIV2:
    """Enhanced TikTok API with account switching"""
    
    def __init__(self, account_manager: SocialAccountManager):
        self.account_manager = account_manager
        self.human = HumanEmulatorV2()
    
    async def post_video(self, video_path: str, caption: str) -> Optional[str]:
        """Post video with failover"""
        account = self.account_manager.get_active_account()
        if not account:
            print("❌ No active TikTok accounts available")
            return None
        
        try:
            await self.human.random_delay(45, 120)
            
            print(f"🎵 Posted to TikTok @{account.username}")
            
            account.last_post = datetime.utcnow()
            account.daily_actions += 1
            
            return f"video_{datetime.utcnow().timestamp()}"
            
        except Exception as e:
            print(f"❌ TikTok post failed: {e}")
            self.account_manager.mark_account_failed(account.username)
            
            backup = self.account_manager.get_backup_account()
            if backup:
                return await self.post_video(video_path, caption)
            
            return None


class SocialAgentV2:
    """
    Enhanced Social Agent V2
    Multi-account support with auto-failover
    """
    
    def __init__(self, db_session):
        self.session = db_session
        self.human = HumanEmulatorV2()
        
        # Initialize account managers
        self.instagram_manager = SocialAccountManager(
            'instagram',
            config.social.instagram_accounts
        )
        self.tiktok_manager = SocialAccountManager(
            'tiktok',
            config.social.tiktok_accounts
        )
        
        # Initialize APIs
        self.instagram = InstagramAPIV2(self.instagram_manager)
        self.tiktok = TikTokAPIV2(self.tiktok_manager)
        
        self.running = False
        self.last_reset = datetime.utcnow()
    
    async def run(self):
        """Main agent loop"""
        self.running = True
        print("📱 Social Agent V2 started")
        print(f"   Instagram accounts: {len(self.instagram_manager.accounts)}")
        print(f"   TikTok accounts: {len(self.tiktok_manager.accounts)}")
        
        while self.running:
            try:
                # Reset daily counters
                if datetime.utcnow() - self.last_reset > timedelta(days=1):
                    self.instagram_manager.reset_daily_counters()
                    self.tiktok_manager.reset_daily_counters()
                    self.last_reset = datetime.utcnow()
                
                # Only post during active hours
                if self.human.is_active_hour():
                    await self._process_cycle()
                else:
                    next_hour = self.human.get_next_active_hour()
                    print(f"⏳ Waiting for active hour ({next_hour}:00)")
                
                await asyncio.sleep(6 * 3600)  # Every 6 hours
                
            except Exception as e:
                self._log_error(f"Social agent error: {e}")
                await asyncio.sleep(600)
    
    async def _process_cycle(self):
        """Process one social media cycle"""
        print("📱 Running social media cycle...")
        
        # 1. Create posts
        await self._create_posts()
        
        # 2. Engage with audience
        await self._engage_with_audience()
        
        # 3. Growth activities
        await self._growth_activities()
        
        print("📱 Social cycle complete")
    
    async def _create_posts(self):
        """Create new social media posts"""
        products = self.session.query(Product).filter(
            Product.is_active == True,
            Product.is_approved == True
        ).order_by(Product.updated_at.desc()).limit(5).all()
        
        for product in products:
            # Check if already posted
            recent_post = self.session.query(SocialPost).filter(
                SocialPost.product_id == product.id,
                SocialPost.posted_at >= datetime.utcnow() - timedelta(days=7)
            ).first()
            
            if recent_post:
                continue
            
            # Generate caption
            caption = self._generate_caption(product)
            
            # Post to Instagram (with auto-failover)
            post_id = await self.instagram.post_image(product.design_url, caption)
            
            if post_id:
                social_post = SocialPost(
                    platform='instagram',
                    account_username=self.instagram_manager.get_active_account().username,
                    content_type='image',
                    caption=caption,
                    product_id=product.id,
                    status='posted',
                    posted_at=datetime.utcnow(),
                    external_post_id=post_id
                )
                self.session.add(social_post)
                self.session.commit()
    
    def _generate_caption(self, product: Product) -> str:
        """Generate social media caption"""
        templates = [
            f"✨ {product.title} - Perfect for any occasion!\n\nShop now - link in bio! 👆\n\n#trending #fashion #style",
            f"🔥 New arrival: {product.title}\n\nLimited stock - grab yours!\n\n#newdrop #musthave",
            f"💫 Obsessed with this {product.product_type or 'design'}!\n\nWhat do you think? 👇\n\n#ootd #aesthetic"
        ]
        return random.choice(templates)
    
    async def _engage_with_audience(self):
        """Engage with audience"""
        # Like posts
        for _ in range(random.randint(5, 15)):
            await self.instagram.like_post(f"post_{random.randint(1000, 9999)}")
            await self.human.engagement_delay()
    
    async def _growth_activities(self):
        """Growth-focused activities"""
        # Follow users
        for _ in range(random.randint(3, 8)):
            await self.instagram.follow_user(f"user_{random.randint(1000, 9999)}")
            await self.human.random_delay(30, 90)
    
    def get_account_status(self) -> Dict:
        """Get status of all accounts"""
        return {
            'instagram': self.instagram_manager.get_all_status(),
            'tiktok': self.tiktok_manager.get_all_status()
        }
    
    def _log_error(self, message: str):
        """Log error"""
        log = AgentLog(
            agent_name='social_v2',
            action='error',
            status='error',
            details={'message': message}
        )
        self.session.add(log)
        self.session.commit()
        print(f"❌ {message}")
    
    def stop(self):
        """Stop the agent"""
        self.running = False
        print("🛑 Social Agent V2 stopped")


# Standalone run
async def run_social_agent_v2():
    """Run social agent v2 standalone"""
    from database.models import init_database
    from config.settings import config
    
    engine = init_database(config.database_path)
    session = get_session(engine)
    
    agent = SocialAgentV2(session)
    await agent.run()


if __name__ == "__main__":
    asyncio.run(run_social_agent_v2())
