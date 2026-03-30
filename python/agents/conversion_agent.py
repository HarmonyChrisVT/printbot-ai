"""
PrintBot AI - Conversion Agent
================================
Recovers abandoned carts with escalating discounts and urgency tactics.

Escalation schedule:
  1 hr  -> 10% off discount code
  24 hr -> 15% off discount code
  72 hr -> 20% off (final chance)

Also creates time-limited flash-sale discount codes and retargets past visitors.
Schedule: Every 15 minutes
"""
import asyncio
import aiohttp
import smtplib
import json
import random
import string
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import List, Dict, Optional

from config.settings import config
from database.models import AgentLog, get_session


# ──────────────────────────────────────────────
# Discount tiers: (hours_elapsed, pct, label)
# ──────────────────────────────────────────────
CART_RECOVERY_TIERS = [
    (1,  10, "stage_1"),
    (24, 15, "stage_2"),
    (72, 20, "stage_3"),
]


class ShopifyCartRecovery:
    """Reads abandoned checkouts and creates discount codes via Shopify API."""

    def __init__(self):
        self.base_url = f"https://{config.shopify.shop_url}/admin/api/{config.shopify.api_version}"
        self.headers = {
            "X-Shopify-Access-Token": config.shopify.access_token,
            "Content-Type": "application/json",
        }

    async def get_abandoned_checkouts(self, since: datetime) -> List[Dict]:
        """Return checkouts created after `since` that haven't converted."""
        url = f"{self.base_url}/checkouts.json"
        params = {
            "status": "open",
            "created_at_min": since.isoformat(),
            "limit": 100,
        }
        timeout = aiohttp.ClientTimeout(total=15)
        try:
            async with aiohttp.ClientSession(headers=self.headers, timeout=timeout) as session:
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("checkouts", [])
        except Exception as e:
            print(f"❌ Shopify abandoned checkouts error: {e}")
        return []

    async def create_discount_code(self, pct: int, checkout_token: str) -> Optional[str]:
        """Create a time-limited percentage discount code and return the code string."""
        code = "SAVE" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
        expires_at = (datetime.utcnow() + timedelta(hours=48)).isoformat()

        # Create a price rule first
        rule_url = f"{self.base_url}/price_rules.json"
        rule_payload = {
            "price_rule": {
                "title": f"Cart Recovery {pct}% - {checkout_token[:8]}",
                "target_type": "line_item",
                "target_selection": "all",
                "allocation_method": "across",
                "value_type": "percentage",
                "value": f"-{pct}.0",
                "customer_selection": "all",
                "once_per_customer": True,
                "usage_limit": 1,
                "starts_at": datetime.utcnow().isoformat(),
                "ends_at": expires_at,
            }
        }
        timeout = aiohttp.ClientTimeout(total=15)
        try:
            async with aiohttp.ClientSession(headers=self.headers, timeout=timeout) as session:
                async with session.post(rule_url, json=rule_payload) as resp:
                    if resp.status not in (200, 201):
                        return None
                    rule = (await resp.json()).get("price_rule", {})
                    rule_id = rule.get("id")

                if not rule_id:
                    return None

                # Attach the discount code to the rule
                code_url = f"{self.base_url}/price_rules/{rule_id}/discount_codes.json"
                code_payload = {"discount_code": {"code": code}}
                async with session.post(code_url, json=code_payload) as resp2:
                    if resp2.status in (200, 201):
                        return code
        except Exception as e:
            print(f"❌ Discount code creation error: {e}")
        return None


class CartEmailSender:
    """Sends branded HTML cart-recovery emails."""

    def _build_html(
        self,
        customer_name: str,
        items: List[Dict],
        discount_code: str,
        discount_pct: int,
        stage: int,
        checkout_url: str,
    ) -> str:
        item_rows = "".join(
            f"<tr><td style='padding:8px'>{i.get('title','Item')}</td>"
            f"<td style='padding:8px;text-align:right'>${float(i.get('price',0)):.2f}</td></tr>"
            for i in items
        )

        urgency_copy = {
            1: "You left something behind — your cart is waiting!",
            2: "Still thinking? Here's an extra nudge just for you.",
            3: "⚠️ Last chance — your cart expires in 48 hours.",
        }
        headline = urgency_copy.get(stage, "Your cart is waiting!")

        return f"""
        <html><body style="font-family:Arial,sans-serif;max-width:600px;margin:auto;color:#333">
          <div style="background:#6d28d9;padding:24px;text-align:center">
            <h1 style="color:#fff;margin:0">PrintBot AI</h1>
          </div>
          <div style="padding:32px">
            <h2>{headline}</h2>
            <p>Hi {customer_name},</p>
            <p>You left some great items in your cart. Use the code below to get
               <strong>{discount_pct}% off</strong> — valid for 48 hours only.</p>
            <div style="background:#f3f4f6;border-radius:8px;padding:20px;text-align:center;margin:24px 0">
              <p style="margin:0;font-size:12px;color:#6b7280">YOUR DISCOUNT CODE</p>
              <p style="margin:8px 0;font-size:28px;font-weight:bold;letter-spacing:4px;color:#6d28d9">
                {discount_code}
              </p>
              <p style="margin:0;font-size:12px;color:#ef4444">Expires in 48 hours</p>
            </div>
            <table style="width:100%;border-collapse:collapse;margin-bottom:24px">
              <thead><tr style="background:#f9fafb">
                <th style="padding:8px;text-align:left">Item</th>
                <th style="padding:8px;text-align:right">Price</th>
              </tr></thead>
              <tbody>{item_rows}</tbody>
            </table>
            <div style="text-align:center">
              <a href="{checkout_url}"
                 style="background:#6d28d9;color:#fff;padding:14px 32px;border-radius:8px;
                        text-decoration:none;font-weight:bold;font-size:16px;display:inline-block">
                Complete My Order →
              </a>
            </div>
          </div>
          <div style="padding:16px;text-align:center;font-size:12px;color:#9ca3af">
            You're receiving this because you started a checkout.
            <a href="#" style="color:#9ca3af">Unsubscribe</a>
          </div>
        </body></html>
        """

    def send(
        self,
        to_email: str,
        customer_name: str,
        items: List[Dict],
        discount_code: str,
        discount_pct: int,
        stage: int,
        checkout_url: str,
    ) -> bool:
        if not config.fulfillment.smtp_host:
            print(f"⚠️  SMTP not configured — skipping cart email to {to_email}")
            return False
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = config.fulfillment.smtp_user
            msg["To"] = to_email
            stage_subject = {
                1: f"You left something! Here's {discount_pct}% off 🎁",
                2: f"Still interested? Extra {discount_pct}% off just for you",
                3: f"⚠️ Final offer: {discount_pct}% off — expires soon",
            }
            msg["Subject"] = stage_subject.get(stage, f"{discount_pct}% off your cart")
            html = self._build_html(customer_name, items, discount_code, discount_pct, stage, checkout_url)
            msg.attach(MIMEText(html, "html"))

            with smtplib.SMTP(config.fulfillment.smtp_host, config.fulfillment.smtp_port) as smtp:
                smtp.starttls()
                smtp.login(config.fulfillment.smtp_user, config.fulfillment.smtp_password)
                smtp.sendmail(config.fulfillment.smtp_user, to_email, msg.as_string())
            print(f"📧 Cart recovery email (stage {stage}) sent to {to_email}")
            return True
        except Exception as e:
            print(f"❌ Cart email error: {e}")
            return False


class ConversionAgent:
    """
    Main Conversion Agent
    Recovers abandoned carts with escalating discounts and urgency emails.
    """

    STATE_FILE = Path("./data/conversion_state.json")

    def __init__(self, db_session):
        self.session = db_session
        self.shopify = ShopifyCartRecovery()
        self.mailer = CartEmailSender()
        self.running = False
        self._state: Dict = self._load_state()

    # ── State persistence ────────────────────────────────────────────────────

    def _load_state(self) -> Dict:
        """Load sent-email history from disk."""
        self.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        if self.STATE_FILE.exists():
            try:
                return json.loads(self.STATE_FILE.read_text())
            except Exception:
                pass
        return {}  # {checkout_token: {stage_1: iso_ts, stage_2: iso_ts, ...}}

    def _save_state(self):
        self.STATE_FILE.write_text(json.dumps(self._state, indent=2))

    def _already_sent(self, token: str, stage: str) -> bool:
        return stage in self._state.get(token, {})

    def _mark_sent(self, token: str, stage: str):
        self._state.setdefault(token, {})[stage] = datetime.utcnow().isoformat()
        self._save_state()

    # ── Core logic ───────────────────────────────────────────────────────────

    async def run(self):
        """Main agent loop."""
        self.running = True
        print("💰 Conversion Agent started")
        while self.running:
            try:
                await self._process_cycle()
                await asyncio.sleep(900)  # Every 15 minutes
            except Exception as e:
                self._log("error", "error", {"message": str(e)})
                await asyncio.sleep(60)

    async def _process_cycle(self):
        if not config.shopify.is_configured:
            return

        # Look back 5 days for abandoned carts
        since = datetime.utcnow() - timedelta(days=5)
        checkouts = await self.shopify.get_abandoned_checkouts(since)
        if not checkouts:
            return

        emails_sent = 0
        for checkout in checkouts:
            token = checkout.get("token", "")
            email = checkout.get("email", "")
            if not email:
                continue

            created_at_str = checkout.get("created_at", "")
            try:
                created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00")).replace(tzinfo=None)
            except Exception:
                continue

            hours_elapsed = (datetime.utcnow() - created_at).total_seconds() / 3600
            customer_name = checkout.get("billing_address", {}).get("first_name", "there")
            items = checkout.get("line_items", [])
            checkout_url = checkout.get("abandoned_checkout_url", "")

            # Determine which stage to send
            for hours_trigger, pct, stage_key in CART_RECOVERY_TIERS:
                if hours_elapsed >= hours_trigger and not self._already_sent(token, stage_key):
                    # Only send the lowest due stage (don't skip ahead)
                    code = await self.shopify.create_discount_code(pct, token)
                    if not code:
                        code = f"SAVE{pct}NOW"  # Fallback generic code

                    stage_num = CART_RECOVERY_TIERS.index((hours_trigger, pct, stage_key)) + 1
                    sent = self.mailer.send(
                        to_email=email,
                        customer_name=customer_name,
                        items=items,
                        discount_code=code,
                        discount_pct=pct,
                        stage=stage_num,
                        checkout_url=checkout_url,
                    )
                    if sent:
                        self._mark_sent(token, stage_key)
                        emails_sent += 1
                        self._log("cart_recovery_email", "success", {
                            "checkout_token": token[:12],
                            "stage": stage_key,
                            "discount_pct": pct,
                            "email": email,
                        })
                    break  # One stage per cycle per cart

        if emails_sent:
            print(f"📬 Conversion Agent: {emails_sent} cart-recovery email(s) sent")

    def _log(self, action: str, status: str, details: Dict):
        log = AgentLog(agent_name="conversion", action=action, status=status, details=details)
        self.session.add(log)
        self.session.commit()

    def stop(self):
        self.running = False
        print("🛑 Conversion Agent stopped")
