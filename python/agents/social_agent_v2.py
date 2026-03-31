"""
PrintBot AI - Social Agent V2
==============================
Real Instagram + TikTok posting via official APIs.

Instagram: Meta Graph API (v21.0)
  Requires: INSTAGRAM_ACCESS_TOKEN + INSTAGRAM_USER_ID
  Flow: create media container → publish

TikTok: TikTok Content Posting API v2
  Requires: TIKTOK_ACCESS_TOKEN
  Flow: POST /v2/post/publish/content/init/ with PHOTO media type

Schedule: Every 6 hours
"""
import asyncio
import random
import aiohttp
import traceback
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from urllib.parse import quote

from config.settings import config
from database.models import SocialPost, Product, AgentLog, get_session

INSTAGRAM_GRAPH_BASE = "https://graph.facebook.com/v21.0"
TIKTOK_API_BASE      = "https://open.tiktokapis.com/v2"

# Fixed active-hour windows (UTC). Posts will only be created within these windows
# to mimic real human behaviour. Agent still wakes up every 6 h to check.
ACTIVE_HOURS_UTC = {8, 12, 14, 17, 19, 21}  # 8 am, noon, 2 pm, 5 pm, 7 pm, 9 pm


# ── Human-like delays ────────────────────────────────────────────────────────

class HumanEmulatorV2:
    async def random_delay(self, min_s: int = 5, max_s: int = 15):
        delay = random.randint(min_s, max_s)
        if random.random() < 0.1:
            delay = int(delay * random.uniform(1.5, 2.0))
        print(f"⏱️  Human delay: {delay}s")
        await asyncio.sleep(delay)

    def is_active_hour(self) -> bool:
        return datetime.utcnow().hour in ACTIVE_HOURS_UTC


# ── Instagram Graph API ──────────────────────────────────────────────────────

class InstagramAPI:
    """
    Posts images to Instagram via the Meta Graph API.

    Required env vars:
      INSTAGRAM_ACCESS_TOKEN  — long-lived token from Meta developer console
      INSTAGRAM_USER_ID       — numeric IG Business/Creator account ID
    """

    def __init__(self):
        self.token   = config.social.instagram_access_token
        self.user_id = config.social.instagram_user_id

    def _configured(self) -> bool:
        if not self.token or not self.user_id:
            print(
                "⚠️  Instagram not configured — set INSTAGRAM_ACCESS_TOKEN "
                "and INSTAGRAM_USER_ID in Railway environment variables."
            )
            return False
        return True

    async def post_image(self, image_url: str, caption: str) -> Optional[str]:
        """
        Two-step Meta Graph API flow:
          1. POST /{user_id}/media        → creation_id
          2. POST /{user_id}/media_publish → published post id
        Returns the published post id on success, None on failure.
        """
        if not self._configured():
            return None
        if not image_url:
            print("⚠️  Instagram: no image URL available — skipping post")
            return None

        try:
            async with aiohttp.ClientSession() as session:
                # Step 1: create media container
                create_url = f"{INSTAGRAM_GRAPH_BASE}/{self.user_id}/media"
                create_params = {
                    "image_url":    image_url,
                    "caption":      caption,
                    "access_token": self.token,
                }
                async with session.post(create_url, params=create_params, timeout=30) as resp:
                    body = await resp.json()
                    if resp.status != 200 or "id" not in body:
                        print(f"❌ Instagram container creation failed ({resp.status}): {body}")
                        return None
                    creation_id = body["id"]
                    print(f"📷 Instagram container created: {creation_id}")

                # Step 2: publish
                publish_url = f"{INSTAGRAM_GRAPH_BASE}/{self.user_id}/media_publish"
                publish_params = {
                    "creation_id":  creation_id,
                    "access_token": self.token,
                }
                async with session.post(publish_url, params=publish_params, timeout=30) as resp:
                    body = await resp.json()
                    if resp.status != 200 or "id" not in body:
                        print(f"❌ Instagram publish failed ({resp.status}): {body}")
                        return None
                    post_id = body["id"]
                    print(f"✅ Instagram post published: {post_id}")
                    return post_id

        except Exception as e:
            print(f"❌ Instagram API error: {e}")
            print(traceback.format_exc())
            return None


# ── TikTok Content Posting API ───────────────────────────────────────────────

class TikTokAPI:
    """
    Posts photo content to TikTok via the TikTok Content Posting API v2.

    Required env vars:
      TIKTOK_ACCESS_TOKEN  — OAuth2 token from TikTok for Developers app
    """

    def __init__(self):
        self.token = config.social.tiktok_access_token

    def _configured(self) -> bool:
        if not self.token:
            print(
                "⚠️  TikTok not configured — set TIKTOK_ACCESS_TOKEN "
                "in Railway environment variables."
            )
            return False
        return True

    async def post_photo(self, image_url: str, caption: str) -> Optional[str]:
        """
        POST to TikTok Content Posting API using PHOTO media type.
        Returns publish_id on success, None on failure.
        """
        if not self._configured():
            return None
        if not image_url:
            print("⚠️  TikTok: no image URL available — skipping post")
            return None

        url = f"{TIKTOK_API_BASE}/post/publish/content/init/"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json; charset=UTF-8",
        }
        payload = {
            "post_info": {
                "title":            caption[:150],  # TikTok caption limit
                "privacy_level":    "FOLLOWER_OF_CREATOR",
                "disable_comment":  False,
                "disable_duet":     False,
                "disable_stitch":   False,
            },
            "source_info": {
                "source":             "PULL_FROM_URL",
                "photo_cover_index":  0,
                "photo_images":       [image_url],
            },
            "post_mode":  "DIRECT_POST",
            "media_type": "PHOTO",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload, timeout=30) as resp:
                    body = await resp.json()
                    if resp.status != 200:
                        print(f"❌ TikTok post failed ({resp.status}): {body}")
                        return None
                    data = body.get("data", {})
                    publish_id = data.get("publish_id")
                    if not publish_id:
                        print(f"❌ TikTok: no publish_id in response: {body}")
                        return None
                    print(f"✅ TikTok photo posted: {publish_id}")
                    return publish_id

        except Exception as e:
            print(f"❌ TikTok API error: {e}")
            print(traceback.format_exc())
            return None


# ── Account manager (display / failover tracking only) ───────────────────────

class SocialAccountManager:
    def __init__(self, platform: str, accounts_config: List[Dict]):
        self.platform = platform
        self.accounts = list(accounts_config)

    def get_primary_username(self) -> str:
        for acc in self.accounts:
            if acc.get("is_primary"):
                return acc.get("username", "")
        return self.accounts[0].get("username", "") if self.accounts else ""

    def get_all_status(self) -> List[Dict]:
        return [
            {
                "username":    acc.get("username", ""),
                "is_active":   acc.get("is_active", False),
                "is_primary":  acc.get("is_primary", False),
            }
            for acc in self.accounts
        ]


# ── Main Social Agent ─────────────────────────────────────────────────────────

class SocialAgentV2:
    """
    Social Agent — real Instagram + TikTok posting.
    Runs a full cycle every 6 hours during UTC active hours.
    """

    def __init__(self, db_session):
        self.session = db_session
        self.human   = HumanEmulatorV2()

        self.instagram_manager = SocialAccountManager(
            "instagram", config.social.instagram_accounts
        )
        self.tiktok_manager = SocialAccountManager(
            "tiktok", config.social.tiktok_accounts
        )

        self.instagram = InstagramAPI()
        self.tiktok    = TikTokAPI()
        self.running   = False
        self.last_reset = datetime.utcnow()

    async def run(self):
        self.running = True
        print("📱 Social Agent V2 started")
        print(f"   Instagram configured: {config.social.instagram_configured}")
        print(f"   TikTok configured:    {config.social.tiktok_configured}")

        if not config.social.instagram_configured and not config.social.tiktok_configured:
            print(
                "⚠️  Social Agent: neither Instagram nor TikTok credentials are set.\n"
                "   Add INSTAGRAM_ACCESS_TOKEN + INSTAGRAM_USER_ID (and/or TIKTOK_ACCESS_TOKEN)\n"
                "   to Railway environment variables, then redeploy."
            )

        while self.running:
            try:
                # Reset daily counters at midnight
                if datetime.utcnow() - self.last_reset > timedelta(days=1):
                    self.last_reset = datetime.utcnow()

                if self.human.is_active_hour():
                    await self._process_cycle()
                else:
                    current_h = datetime.utcnow().hour
                    next_h = min((h for h in sorted(ACTIVE_HOURS_UTC) if h > current_h),
                                 default=min(ACTIVE_HOURS_UTC))
                    print(f"⏳ Social Agent: outside active hours (current={current_h}h UTC), "
                          f"next window at {next_h}h UTC")

                await asyncio.sleep(6 * 3600)

            except Exception as e:
                self._log_action("run_error", "error", {"message": str(e), "trace": traceback.format_exc()})
                await asyncio.sleep(600)

    async def _process_cycle(self):
        print("📱 Social Agent: running posting cycle…")
        await self._create_posts()
        print("📱 Social Agent: cycle complete")

    async def _create_posts(self):
        """Post each un-posted approved product to Instagram and TikTok."""
        products = (
            self.session.query(Product)
            .filter(Product.is_active == True, Product.is_approved == True)
            .order_by(Product.updated_at.desc())
            .limit(5)
            .all()
        )

        if not products:
            print("📱 Social Agent: no approved products to post yet")
            self._log_action("create_posts", "warning", {"message": "no approved products"})
            return

        for product in products:
            # Skip products posted to either platform in the last 7 days
            recent = self.session.query(SocialPost).filter(
                SocialPost.product_id == product.id,
                SocialPost.posted_at >= datetime.utcnow() - timedelta(days=7),
            ).first()
            if recent:
                continue

            # Use Shopify CDN URL if available (permanent), else fall back to design_url
            image_url = product.design_url or ""
            if not image_url:
                print(f"⚠️  Product '{product.title}' has no image URL — skipping")
                continue

            caption = self._generate_caption(product)

            # ── Instagram ────────────────────────────────────────────────────
            if config.social.instagram_configured:
                await self.human.random_delay(5, 15)
                ig_post_id = await self.instagram.post_image(image_url, caption)
                if ig_post_id:
                    self._save_post(product, "instagram",
                                    self.instagram_manager.get_primary_username(),
                                    caption, ig_post_id)
                    self._log_action("instagram_post", "success", {
                        "product_id": product.id,
                        "product_title": product.title,
                        "post_id": ig_post_id,
                    })
                else:
                    self._log_action("instagram_post", "error", {
                        "product_id": product.id,
                        "product_title": product.title,
                        "image_url": image_url,
                        "error": "Instagram API returned None — check token/user_id and image URL",
                    })
            else:
                self._log_action("instagram_post", "warning",
                                 {"message": "INSTAGRAM_ACCESS_TOKEN or INSTAGRAM_USER_ID not set"})

            # ── TikTok ───────────────────────────────────────────────────────
            if config.social.tiktok_configured:
                await self.human.random_delay(5, 15)
                tt_post_id = await self.tiktok.post_photo(image_url, caption)
                if tt_post_id:
                    self._save_post(product, "tiktok",
                                    self.tiktok_manager.get_primary_username(),
                                    caption, tt_post_id)
                    self._log_action("tiktok_post", "success", {
                        "product_id": product.id,
                        "product_title": product.title,
                        "publish_id": tt_post_id,
                    })
                else:
                    self._log_action("tiktok_post", "error", {
                        "product_id": product.id,
                        "product_title": product.title,
                        "image_url": image_url,
                        "error": "TikTok API returned None — check TIKTOK_ACCESS_TOKEN",
                    })
            else:
                self._log_action("tiktok_post", "warning",
                                 {"message": "TIKTOK_ACCESS_TOKEN not set"})

    def _generate_caption(self, product: Product) -> str:
        templates = [
            f"✨ {product.title}\n\nShop now — link in bio! 👆\n\n#trending #fashion #style #printOnDemand",
            f"🔥 New drop: {product.title}\n\nGrab yours before it's gone!\n\n#newdrop #musthave #tshirt",
            f"💫 Loving this {product.product_type or 'design'}!\n\nWhat do you think? 👇\n\n#ootd #aesthetic #custom",
        ]
        return random.choice(templates)

    def _save_post(self, product: Product, platform: str,
                   username: str, caption: str, post_id: str):
        post = SocialPost(
            platform=platform,
            account_username=username,
            content_type="image",
            caption=caption,
            product_id=product.id,
            product_url=f"https://{config.shopify.shop_url}/products/{product.shopify_id}"
                        if product.shopify_id else None,
            status="posted",
            posted_at=datetime.utcnow(),
            external_post_id=post_id,
        )
        self.session.add(post)
        self.session.commit()

    def _log_action(self, action: str, status: str, details: dict):
        log = AgentLog(
            agent_name="social",   # use 'social' so health monitor queries find it
            action=action,
            status=status,
            details=details,
        )
        self.session.add(log)
        self.session.commit()
        if status == "error":
            print(f"❌ Social Agent [{action}]: {details}")

    def get_account_status(self) -> Dict:
        return {
            "instagram": {
                "configured": config.social.instagram_configured,
                "user_id": config.social.instagram_user_id or "not set",
                "accounts": self.instagram_manager.get_all_status(),
            },
            "tiktok": {
                "configured": config.social.tiktok_configured,
                "accounts": self.tiktok_manager.get_all_status(),
            },
        }

    def stop(self):
        self.running = False
        print("🛑 Social Agent V2 stopped")


# Standalone run
async def run_social_agent_v2():
    from database.models import init_database
    engine = init_database(config.database_path)
    session = get_session(engine)
    agent = SocialAgentV2(session)
    await agent.run()


if __name__ == "__main__":
    asyncio.run(run_social_agent_v2())
