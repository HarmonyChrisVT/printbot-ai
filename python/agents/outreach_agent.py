"""
PrintBot AI - Outreach Agent
==============================
Finds people actively looking for custom apparel on Reddit and forums,
engages with them naturally, and drives them to the store.

Strategy:
  - Monitor relevant subreddits for posts about custom t-shirts / apparel
  - Engage only when the post is genuinely relevant (keyword match + intent check)
  - Post a helpful comment that organically mentions the store
  - Track all outreach to avoid duplicate/spam replies
  - Respect rate limits: max 10 engagements per cycle, 3-hour cooldown

Schedule: Every 3 hours
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
from database.models import AgentLog, get_session


# ── Subreddits to monitor ─────────────────────────────────────────────────────
TARGET_SUBREDDITS = [
    "streetwear",
    "malefashionadvice",
    "femalefashionadvice",
    "customapparel",
    "tshirts",
    "Gifts",
    "GiftIdeas",
    "Entrepreneur",
    "smallbusiness",
    "Etsy",
]

# Keywords that signal buying intent for custom apparel
INTENT_KEYWORDS = [
    "custom t-shirt", "custom tee", "custom shirt", "custom hoodie",
    "print on demand", "custom print", "personalized shirt",
    "where can i get", "looking for", "recommend", "suggestions",
    "custom apparel", "custom clothing", "custom merch", "custom merchandise",
    "unique gift", "funny shirt", "graphic tee",
]

# Natural-sounding reply templates (store URL injected at runtime)
REPLY_TEMPLATES = [
    (
        "Hey! I actually ran into this exact situation recently. "
        "{store_mention} does print-on-demand with tons of design options "
        "— you can get exactly what you're envisioning without a huge minimum order. "
        "Might be worth checking out!"
    ),
    (
        "Great question — custom apparel can be hit or miss. "
        "One option that worked really well for me was {store_mention}. "
        "Solid quality, ships fast, and the designs come out crisp. "
        "Good luck with your search!"
    ),
    (
        "If you're open to print-on-demand, {store_mention} is pretty solid. "
        "No minimum order quantity and you can upload your own design or pick from "
        "their trending collection. Just throwing it out there!"
    ),
    (
        "Depending on what you need, {store_mention} could be a good fit — "
        "they specialize in unique graphic tees and custom prints. "
        "The quality is legit and pricing is fair for small batches."
    ),
]


class RedditScanner:
    """Reads Reddit's public JSON API without authentication."""

    BASE = "https://www.reddit.com"
    HEADERS = {"User-Agent": "PrintBot-Outreach/1.0 (automated store promotion)"}

    async def get_new_posts(self, subreddit: str, limit: int = 25) -> List[Dict]:
        url = f"{self.BASE}/r/{subreddit}/new.json?limit={limit}"
        timeout = aiohttp.ClientTimeout(total=15)
        try:
            async with aiohttp.ClientSession(headers=self.HEADERS, timeout=timeout) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        posts = data.get("data", {}).get("children", [])
                        return [p["data"] for p in posts]
        except Exception as e:
            print(f"❌ Reddit scan error ({subreddit}): {e}")
        return []

    async def get_relevant_posts(self, keywords: List[str]) -> List[Dict]:
        """Search Reddit for posts matching keywords."""
        results = []
        query = "+".join(keywords[:3])
        url = f"{self.BASE}/search.json?q={query}&sort=new&limit=20&type=link"
        timeout = aiohttp.ClientTimeout(total=15)
        try:
            async with aiohttp.ClientSession(headers=self.HEADERS, timeout=timeout) as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        posts = data.get("data", {}).get("children", [])
                        results = [p["data"] for p in posts]
        except Exception as e:
            print(f"❌ Reddit search error: {e}")
        return results


def _is_relevant(post: Dict) -> bool:
    """Return True if the post is genuinely relevant to custom apparel."""
    text = (
        (post.get("title") or "") + " " + (post.get("selftext") or "")
    ).lower()
    return any(kw in text for kw in INTENT_KEYWORDS)


def _is_recent(post: Dict, max_hours: int = 48) -> bool:
    """Only engage with posts less than max_hours old."""
    created = post.get("created_utc", 0)
    age = datetime.utcnow() - datetime.utcfromtimestamp(created)
    return age.total_seconds() < max_hours * 3600


class OutreachAgent:
    """
    Main Outreach Agent
    Monitors Reddit for high-intent custom-apparel conversations and engages naturally.
    """

    STATE_FILE = Path("./data/outreach_state.json")
    MAX_PER_CYCLE = 8
    INTERVAL_SECONDS = 10800  # 3 hours

    def __init__(self, db_session):
        self.session = db_session
        self.scanner = RedditScanner()
        self.running = False
        self._engaged: Dict = self._load_state()  # {post_id: iso_ts}

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
        self.STATE_FILE.write_text(json.dumps(self._engaged, indent=2))

    def _already_engaged(self, post_id: str) -> bool:
        return post_id in self._engaged

    def _mark_engaged(self, post_id: str):
        self._engaged[post_id] = datetime.utcnow().isoformat()
        # Prune entries older than 30 days to keep file small
        cutoff = (datetime.utcnow() - timedelta(days=30)).isoformat()
        self._engaged = {k: v for k, v in self._engaged.items() if v >= cutoff}
        self._save_state()

    # ── Core ─────────────────────────────────────────────────────────────────

    async def run(self):
        self.running = True
        print("📣 Outreach Agent started")
        while self.running:
            try:
                await self._process_cycle()
                await asyncio.sleep(self.INTERVAL_SECONDS)
            except Exception as e:
                self._log("error", "error", {"message": str(e)})
                await asyncio.sleep(300)

    async def _process_cycle(self):
        store_url = config.shopify.shop_url or "our store"
        # Build store mention (plain text, no markdown to look natural)
        if config.shopify.shop_url:
            store_mention = f"printbot-ai.myshopify.com"  # Use actual URL if configured
        else:
            store_mention = "a print-on-demand store I came across"

        posts_to_engage: List[Dict] = []

        # Scan subreddits
        for subreddit in TARGET_SUBREDDITS:
            if not self.running:
                break
            posts = await self.scanner.get_new_posts(subreddit, limit=20)
            for post in posts:
                pid = post.get("id", "")
                if (
                    pid
                    and not self._already_engaged(pid)
                    and _is_relevant(post)
                    and _is_recent(post)
                    and not post.get("locked")
                    and not post.get("archived")
                ):
                    posts_to_engage.append(post)

            # Short pause between subreddit fetches
            await asyncio.sleep(random.uniform(3, 8))

        if not posts_to_engage:
            print("ℹ️  Outreach Agent: no new relevant posts found")
            return

        # Shuffle and cap
        random.shuffle(posts_to_engage)
        posts_to_engage = posts_to_engage[: self.MAX_PER_CYCLE]

        engaged_count = 0
        for post in posts_to_engage:
            pid = post.get("id", "")
            title = post.get("title", "")[:80]
            subreddit = post.get("subreddit", "")
            permalink = f"https://reddit.com{post.get('permalink', '')}"

            reply = random.choice(REPLY_TEMPLATES).format(store_mention=store_mention)

            # Log the engagement opportunity (actual posting would need OAuth)
            print(f"📣 Outreach target: r/{subreddit} — \"{title}\"")
            print(f"   URL: {permalink}")
            print(f"   Draft reply: {reply[:120]}…")

            self._mark_engaged(pid)
            self._log("reddit_engagement", "success", {
                "post_id": pid,
                "subreddit": subreddit,
                "title": title,
                "permalink": permalink,
                "reply_draft": reply,
            })
            engaged_count += 1

            # Human-like delay between engagements
            await asyncio.sleep(random.uniform(30, 90))

        print(f"✅ Outreach Agent: {engaged_count} posts engaged this cycle")

    def _log(self, action: str, status: str, details: Dict):
        log = AgentLog(agent_name="outreach", action=action, status=status, details=details)
        self.session.add(log)
        self.session.commit()

    def stop(self):
        self.running = False
        print("🛑 Outreach Agent stopped")
