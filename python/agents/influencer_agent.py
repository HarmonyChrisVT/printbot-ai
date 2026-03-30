"""
PrintBot AI - Influencer Agent
================================
Automatically identifies micro-influencers in the apparel/fashion niche
on Instagram and TikTok, then sends collaboration requests offering free
products in exchange for posts.

Micro-influencer criteria:
  - Follower range: 1,000 – 100,000
  - Engagement rate: >= 2%
  - Niche keywords: fashion, streetwear, ootd, style, apparel

Outreach offer:
  - Free product (select from approved catalog)
  - No cash payment
  - Post requirement: 1 in-feed post + 1 story

Schedule: Every 6 hours
"""
import asyncio
import aiohttp
import json
import random
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

from config.settings import config
from database.models import AgentLog, Product, get_session


# ── Discovery config ──────────────────────────────────────────────────────────
FASHION_HASHTAGS = [
    "streetwear", "ootd", "fashionstyle", "outfitoftheday",
    "streetfashion", "fashionblogger", "styleinspiration",
    "graphictee", "tshirtdesign", "customapparel", "printlife",
    "hypebeast", "sneakerhead", "casualstyle", "mensfashion",
    "womensfashion", "fashioninfluencer", "contentcreator",
]

NICHE_KEYWORDS = [
    "fashion", "style", "ootd", "streetwear", "apparel",
    "clothing", "outfit", "tshirt", "hoodie", "merch",
]

MIN_FOLLOWERS = 1_000
MAX_FOLLOWERS = 100_000
MIN_ENGAGEMENT_RATE = 0.02  # 2 %

# DM / collaboration request templates
DM_TEMPLATES = [
    (
        "Hey {name}! 👋 Love your content — your style is exactly what we're "
        "looking for. We're PrintBot AI, a custom apparel brand, and we'd love "
        "to send you a free piece from our latest collection in exchange for an "
        "honest post. No strings attached — just genuine collab vibes. "
        "Interested? Drop us a reply! 🎨"
    ),
    (
        "Hi {name}! We've been following your feed and your aesthetic "
        "matches our brand perfectly. We'd love to gift you one of our "
        "custom graphic tees (your choice!) in exchange for a post/story "
        "when it arrives. Zero cash, just cool merch + exposure for both of us. "
        "Let us know if you're down! ✌️"
    ),
    (
        "Hey {name}! Quick collab offer — we're a print-on-demand brand "
        "that creates trending graphic apparel. We want to send you a free "
        "item (no purchase needed) and all we ask is one honest post. "
        "Our pieces are selling really well right now and we think your "
        "audience would dig them. Interested? 🔥"
    ),
]


class InstagramDiscovery:
    """
    Discovers micro-influencers by scraping public hashtag pages.
    Uses the unofficial Instagram web endpoint — respects rate limits carefully.
    """

    BASE = "https://www.instagram.com"
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "X-IG-App-ID": "936619743392459",
    }

    async def search_hashtag_users(self, hashtag: str) -> List[Dict]:
        """Return a list of candidate profiles from a hashtag's top posts."""
        url = f"{self.BASE}/api/v1/tags/{hashtag}/sections/"
        params = {
            "include_persistent": "true",
            "tab": "top",
            "max_id": "",
        }
        timeout = aiohttp.ClientTimeout(total=15)
        try:
            async with aiohttp.ClientSession(headers=self.HEADERS, timeout=timeout) as session:
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        sections = data.get("sections", [])
                        users = []
                        for section in sections:
                            for media in section.get("layout_content", {}).get("medias", []):
                                user = media.get("media", {}).get("user", {})
                                if user:
                                    users.append(user)
                        return users
        except Exception as e:
            print(f"⚠️  Instagram hashtag scan ({hashtag}): {e}")
        return []

    async def get_profile_stats(self, username: str) -> Optional[Dict]:
        """Fetch basic public profile stats."""
        url = f"{self.BASE}/{username}/?__a=1&__d=dis"
        timeout = aiohttp.ClientTimeout(total=15)
        try:
            async with aiohttp.ClientSession(headers=self.HEADERS, timeout=timeout) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        user = data.get("graphql", {}).get("user", {})
                        if not user:
                            return None
                        followers = user.get("edge_followed_by", {}).get("count", 0)
                        posts = user.get("edge_owner_to_timeline_media", {}).get("count", 0)
                        # Estimate engagement from recent likes
                        edges = user.get("edge_owner_to_timeline_media", {}).get("edges", [])
                        avg_likes = 0
                        if edges:
                            likes = [
                                e["node"].get("edge_liked_by", {}).get("count", 0)
                                for e in edges[:12]
                            ]
                            avg_likes = sum(likes) / len(likes) if likes else 0
                        engagement_rate = (avg_likes / followers) if followers > 0 else 0
                        return {
                            "username": username,
                            "full_name": user.get("full_name", ""),
                            "bio": user.get("biography", ""),
                            "followers": followers,
                            "following": user.get("edge_follow", {}).get("count", 0),
                            "posts": posts,
                            "avg_likes": round(avg_likes),
                            "engagement_rate": round(engagement_rate, 4),
                            "platform": "instagram",
                        }
        except Exception:
            pass
        return None


def _is_micro_influencer(profile: Dict) -> bool:
    followers = profile.get("followers", 0)
    er = profile.get("engagement_rate", 0)
    return MIN_FOLLOWERS <= followers <= MAX_FOLLOWERS and er >= MIN_ENGAGEMENT_RATE


def _bio_is_relevant(profile: Dict) -> bool:
    bio = (profile.get("bio") or "").lower()
    return any(kw in bio for kw in NICHE_KEYWORDS)


class InfluencerAgent:
    """
    Main Influencer Agent
    Identifies micro-influencers and queues collaboration outreach.
    """

    STATE_FILE = Path("./data/influencer_state.json")
    MAX_PER_CYCLE = 10
    INTERVAL_SECONDS = 21600  # 6 hours

    def __init__(self, db_session):
        self.session = db_session
        self.ig_discovery = InstagramDiscovery()
        self.running = False
        self._outreach: Dict = self._load_state()
        # {username: {platform, followers, er, contacted_at, status}}

    # ── State ────────────────────────────────────────────────────────────────

    def _load_state(self) -> Dict:
        self.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        if self.STATE_FILE.exists():
            try:
                return json.loads(self.STATE_FILE.read_text())
            except Exception:
                pass
        return {}

    def _save_state(self):
        self.STATE_FILE.write_text(json.dumps(self._outreach, indent=2))

    def _already_contacted(self, username: str) -> bool:
        return username in self._outreach

    def _record_outreach(self, profile: Dict, status: str = "queued"):
        self._outreach[profile["username"]] = {
            "platform": profile.get("platform", "instagram"),
            "followers": profile.get("followers", 0),
            "engagement_rate": profile.get("engagement_rate", 0),
            "contacted_at": datetime.utcnow().isoformat(),
            "status": status,
        }
        self._save_state()

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _get_free_product_name(self) -> str:
        """Pick an active product to offer as the collab gift."""
        product = (
            self.session.query(Product)
            .filter(Product.is_active == True, Product.is_approved == True)
            .order_by(Product.created_at.desc())
            .first()
        )
        return product.title if product else "our latest graphic tee"

    def _build_dm(self, name: str, product_name: str) -> str:
        template = random.choice(DM_TEMPLATES)
        display_name = name.split()[0] if name else "there"
        return template.format(name=display_name, product=product_name)

    # ── Core ─────────────────────────────────────────────────────────────────

    async def run(self):
        self.running = True
        print("🌟 Influencer Agent started")
        while self.running:
            try:
                await self._process_cycle()
                await asyncio.sleep(self.INTERVAL_SECONDS)
            except Exception as e:
                self._log("error", "error", {"message": str(e)})
                await asyncio.sleep(300)

    async def _process_cycle(self):
        candidates: List[Dict] = []
        seen_usernames = set()

        # Scan Instagram hashtags
        hashtags_this_cycle = random.sample(FASHION_HASHTAGS, min(5, len(FASHION_HASHTAGS)))
        for hashtag in hashtags_this_cycle:
            if not self.running:
                break
            users = await self.ig_discovery.search_hashtag_users(hashtag)
            for user in users:
                username = user.get("username", "")
                if not username or username in seen_usernames:
                    continue
                if self._already_contacted(username):
                    continue
                seen_usernames.add(username)

                # Quick filter on raw data before fetching full profile
                follower_count = user.get("follower_count", 0)
                if not (MIN_FOLLOWERS <= follower_count <= MAX_FOLLOWERS):
                    continue

                candidates.append({
                    "username": username,
                    "full_name": user.get("full_name", ""),
                    "followers": follower_count,
                    "platform": "instagram",
                })
            await asyncio.sleep(random.uniform(10, 25))

        if not candidates:
            print("ℹ️  Influencer Agent: no new candidates found this cycle")
            return

        random.shuffle(candidates)
        to_contact = candidates[: self.MAX_PER_CYCLE]
        product_name = self._get_free_product_name()
        contacted = 0

        for candidate in to_contact:
            username = candidate["username"]
            name = candidate.get("full_name") or username

            # Fetch full profile to verify engagement rate
            profile = await self.ig_discovery.get_profile_stats(username)
            if profile is None:
                # Use partial data
                profile = candidate
                profile["engagement_rate"] = 0.0

            if not _is_micro_influencer(profile):
                continue

            # Build DM
            dm_text = self._build_dm(name, product_name)

            print(f"🌟 Influencer candidate: @{username} "
                  f"({profile.get('followers', 0):,} followers, "
                  f"{profile.get('engagement_rate', 0):.1%} ER)")
            print(f"   DM draft: {dm_text[:120]}…")

            self._record_outreach(profile, status="queued")
            self._log("influencer_outreach", "success", {
                "username": username,
                "platform": "instagram",
                "followers": profile.get("followers", 0),
                "engagement_rate": profile.get("engagement_rate", 0),
                "dm_draft": dm_text,
                "product_offered": product_name,
            })
            contacted += 1

            # Human-like delay between outreach
            await asyncio.sleep(random.uniform(45, 120))

        print(f"✅ Influencer Agent: {contacted} influencer(s) queued for outreach")

    def get_pipeline_stats(self) -> Dict:
        """Return stats about the influencer pipeline."""
        statuses: Dict[str, int] = {}
        for data in self._outreach.values():
            s = data.get("status", "unknown")
            statuses[s] = statuses.get(s, 0) + 1
        return {
            "total_identified": len(self._outreach),
            "queued": statuses.get("queued", 0),
            "contacted": statuses.get("contacted", 0),
            "responded": statuses.get("responded", 0),
            "converted": statuses.get("converted", 0),
        }

    def _log(self, action: str, status: str, details: Dict):
        log = AgentLog(agent_name="influencer", action=action, status=status, details=details)
        self.session.add(log)
        self.session.commit()

    def stop(self):
        self.running = False
        print("🛑 Influencer Agent stopped")
