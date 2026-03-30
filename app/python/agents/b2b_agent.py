"""
PrintBot AI - B2B Corporate Agent
==================================
Handles bulk orders, corporate clients, wholesale pricing
Schedule: Every 4 hours
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
import json

from config.settings import config
from database.models import Order, Product, AgentLog, get_session


@dataclass
class CorporateClient:
    """Corporate client data"""
    id: int
    company_name: str
    contact_name: str
    email: str
    phone: str
    tax_id: str
    payment_terms: str  # net30, net60, etc.
    discount_tier: str  # bronze, silver, gold, platinum
    credit_limit: float
    current_balance: float
    is_approved: bool
    created_at: datetime


@dataclass
class BulkQuote:
    """Bulk order quote"""
    id: int
    client_id: int
    items: List[Dict]
    quantity: int
    unit_price: float
    discount_percent: float
    total_price: float
    status: str  # pending, approved, rejected, expired
    valid_until: datetime
    created_at: datetime


class B2BEmailCapture:
    """Email capture and lead nurturing system"""
    
    def __init__(self, db_session):
        self.session = db_session
        self.capture_triggers = [
            'exit_intent',
            'scroll_50_percent',
            'time_on_site_30_seconds',
            'add_to_cart',
            'view_product'
        ]
    
    async def capture_email(self, email: str, source: str, metadata: Dict = None) -> bool:
        """Capture email from visitor"""
        from database.models import EmailLead
        
        # Check if already captured
        existing = self.session.query(EmailLead).filter_by(email=email).first()
        if existing:
            # Update engagement
            existing.engagement_score += 1
            existing.last_engagement = datetime.utcnow()
            self.session.commit()
            return True
        
        # Create new lead
        lead = EmailLead(
            email=email,
            source=source,
            capture_trigger=metadata.get('trigger', 'manual'),
            page_url=metadata.get('page_url'),
            referrer=metadata.get('referrer'),
            user_agent=metadata.get('user_agent'),
            engagement_score=1,
            captured_at=datetime.utcnow()
        )
        
        self.session.add(lead)
        self.session.commit()
        
        # Trigger welcome sequence
        await self._send_welcome_email(lead)
        
        print(f"✅ Email captured: {email}")
        return True
    
    async def _send_welcome_email(self, lead):
        """Send welcome email to new lead"""
        # Would integrate with email service
        print(f"📧 Welcome email queued for {lead.email}")
    
    async def send_nurture_sequence(self, lead_id: int):
        """Send automated nurture sequence"""
        from database.models import EmailLead
        
        lead = self.session.query(EmailLead).get(lead_id)
        if not lead:
            return
        
        sequences = {
            'day_0': {
                'subject': 'Welcome! Here\'s 10% off your first order',
                'content': 'Welcome email with discount code'
            },
            'day_3': {
                'subject': 'Our bestselling designs this week',
                'content': 'Showcase popular products'
            },
            'day_7': {
                'subject': 'Limited time: Free shipping',
                'content': 'Free shipping offer'
            },
            'day_14': {
                'subject': 'We miss you! Come back for 15% off',
                'content': 'Win-back email'
            }
        }
        
        # Schedule emails based on capture date
        for day_key, email_data in sequences.items():
            day = int(day_key.split('_')[1])
            send_at = lead.captured_at + timedelta(days=day)
            
            # Would schedule with email service
            print(f"📧 Scheduled {day_key} email for {lead.email} at {send_at}")


class CorporatePricing:
    """Corporate and wholesale pricing tiers"""
    
    def __init__(self):
        self.tiers = {
            'bronze': {
                'min_quantity': 10,
                'discount': 0.15,
                'payment_terms': 'net30'
            },
            'silver': {
                'min_quantity': 50,
                'discount': 0.25,
                'payment_terms': 'net30'
            },
            'gold': {
                'min_quantity': 100,
                'discount': 0.35,
                'payment_terms': 'net60'
            },
            'platinum': {
                'min_quantity': 500,
                'discount': 0.45,
                'payment_terms': 'net60'
            }
        }
    
    def calculate_bulk_price(self, product: Product, quantity: int, tier: str = None) -> Dict:
        """Calculate bulk pricing"""
        base_price = product.selling_price
        
        # Determine tier if not specified
        if not tier:
            for tier_name, tier_data in sorted(self.tiers.items(), key=lambda x: x[1]['min_quantity'], reverse=True):
                if quantity >= tier_data['min_quantity']:
                    tier = tier_name
                    break
        
        tier_data = self.tiers.get(tier, self.tiers['bronze'])
        discount = tier_data['discount']
        
        unit_price = base_price * (1 - discount)
        total_price = unit_price * quantity
        savings = (base_price * quantity) - total_price
        
        return {
            'tier': tier,
            'quantity': quantity,
            'base_price': base_price,
            'unit_price': round(unit_price, 2),
            'total_price': round(total_price, 2),
            'discount_percent': discount * 100,
            'savings': round(savings, 2),
            'payment_terms': tier_data['payment_terms']
        }
    
    def generate_quote(self, client: CorporateClient, items: List[Dict]) -> BulkQuote:
        """Generate bulk quote for corporate client"""
        total_quantity = sum(item['quantity'] for item in items)
        
        # Get tier discount
        tier_data = self.tiers.get(client.discount_tier, self.tiers['bronze'])
        discount = tier_data['discount']
        
        # Calculate prices
        total_base = 0
        total_discounted = 0
        
        for item in items:
            product = self.session.query(Product).get(item['product_id'])
            if product:
                item_base = product.selling_price * item['quantity']
                item_discounted = item_base * (1 - discount)
                total_base += item_base
                total_discounted += item_discounted
        
        quote = BulkQuote(
            id=0,  # Would be set by database
            client_id=client.id,
            items=items,
            quantity=total_quantity,
            unit_price=round(total_discounted / total_quantity, 2) if total_quantity > 0 else 0,
            discount_percent=discount * 100,
            total_price=round(total_discounted, 2),
            status='pending',
            valid_until=datetime.utcnow() + timedelta(days=30),
            created_at=datetime.utcnow()
        )
        
        return quote


class B2BAgent:
    """
    Main B2B Corporate Agent
    Handles bulk orders, corporate clients, wholesale
    """
    
    def __init__(self, db_session):
        self.session = db_session
        self.email_capture = B2BEmailCapture(db_session)
        self.pricing = CorporatePricing()
        self.running = False
        
        # B2B settings
        self.min_bulk_quantity = 10
        self.auto_approve_threshold = 1000  # Auto-approve quotes under $1000
    
    async def run(self):
        """Main agent loop"""
        self.running = True
        print("🏢 B2B Corporate Agent started")
        
        while self.running:
            try:
                await self._process_cycle()
                await asyncio.sleep(4 * 3600)  # Every 4 hours
                
            except Exception as e:
                self._log_error(f"B2B agent error: {e}")
                await asyncio.sleep(600)
    
    async def _process_cycle(self):
        """Process one B2B cycle"""
        print("🏢 Running B2B cycle...")
        
        # 1. Process pending bulk quotes
        await self._process_bulk_quotes()
        
        # 2. Follow up on pending corporate orders
        await self._follow_up_corporate_orders()
        
        # 3. Check credit limits
        await self._check_credit_limits()
        
        # 4. Send nurture emails
        await self._process_nurture_sequences()
        
        print("🏢 B2B cycle complete")
    
    async def _process_bulk_quotes(self):
        """Process pending bulk quotes"""
        from database.models import BulkQuote
        
        pending_quotes = self.session.query(BulkQuote).filter(
            BulkQuote.status == 'pending',
            BulkQuote.valid_until > datetime.utcnow()
        ).all()
        
        for quote in pending_quotes:
            # Auto-approve small quotes
            if quote.total_price < self.auto_approve_threshold:
                quote.status = 'approved'
                self.session.commit()
                
                # Notify client
                await self._send_quote_approved_email(quote)
                
                print(f"✅ Auto-approved quote #{quote.id}: ${quote.total_price}")
            
            # Flag large quotes for manual review
            elif quote.total_price > 10000:
                await self._flag_for_manual_review(quote)
    
    async def _follow_up_corporate_orders(self):
        """Follow up on corporate orders"""
        # Find orders pending payment
        pending_orders = self.session.query(Order).filter(
            Order.financial_status == 'pending',
            Order.created_at < datetime.utcnow() - timedelta(days=7)
        ).all()
        
        for order in pending_orders:
            # Send payment reminder
            await self._send_payment_reminder(order)
    
    async def _check_credit_limits(self):
        """Check corporate client credit limits"""
        from database.models import CorporateClient
        
        clients = self.session.query(CorporateClient).filter(
            CorporateClient.is_approved == True
        ).all()
        
        for client in clients:
            if client.current_balance > client.credit_limit * 0.9:
                # Alert: approaching credit limit
                await self._send_credit_limit_alert(client)
    
    async def _process_nurture_sequences(self):
        """Process email nurture sequences"""
        from database.models import EmailLead
        
        # Get leads that need nurture emails
        leads = self.session.query(EmailLead).filter(
            EmailLead.engagement_score < 5,
            EmailLead.captured_at < datetime.utcnow() - timedelta(days=1)
        ).limit(50).all()
        
        for lead in leads:
            await self.email_capture.send_nurture_sequence(lead.id)
    
    # Email methods
    async def _send_quote_approved_email(self, quote):
        """Send quote approval email"""
        print(f"📧 Quote approval email for quote #{quote.id}")
    
    async def _send_payment_reminder(self, order):
        """Send payment reminder"""
        print(f"📧 Payment reminder for order #{order.order_number}")
    
    async def _send_credit_limit_alert(self, client):
        """Send credit limit alert"""
        print(f"📧 Credit limit alert for {client.company_name}")
    
    async def _flag_for_manual_review(self, quote):
        """Flag quote for manual review"""
        print(f"🚩 Quote #{quote.id} flagged for manual review")
    
    # Public API methods
    async def create_bulk_quote(self, client_id: int, items: List[Dict]) -> BulkQuote:
        """Create a bulk quote"""
        from database.models import CorporateClient
        
        client = self.session.query(CorporateClient).get(client_id)
        if not client:
            raise ValueError(f"Client {client_id} not found")
        
        quote = self.pricing.generate_quote(client, items)
        
        # Save to database
        db_quote = self._save_quote(quote)
        
        # Send quote email
        await self._send_quote_email(db_quote)
        
        return db_quote
    
    def _save_quote(self, quote: BulkQuote):
        """Save quote to database"""
        from database.models import BulkQuote as BulkQuoteModel
        
        db_quote = BulkQuoteModel(
            client_id=quote.client_id,
            items=json.dumps(quote.items),
            quantity=quote.quantity,
            unit_price=quote.unit_price,
            discount_percent=quote.discount_percent,
            total_price=quote.total_price,
            status=quote.status,
            valid_until=quote.valid_until,
            created_at=quote.created_at
        )
        
        self.session.add(db_quote)
        self.session.commit()
        
        return db_quote
    
    async def _send_quote_email(self, quote):
        """Send quote email to client"""
        print(f"📧 Quote email sent for quote #{quote.id}")
    
    def _log_action(self, action: str, status: str, details: Dict):
        """Log agent action"""
        log = AgentLog(
            agent_name='b2b',
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
        print("🛑 B2B Agent stopped")


# Standalone run function
async def run_b2b_agent():
    """Run B2B agent standalone"""
    from database.models import init_database
    from config.settings import config
    
    engine = init_database(config.database_path)
    session = get_session(engine)
    
    agent = B2BAgent(session)
    await agent.run()


if __name__ == "__main__":
    asyncio.run(run_b2b_agent())
