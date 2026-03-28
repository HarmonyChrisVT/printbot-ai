"""
PrintBot AI - Affiliate Program Agent
======================================
Manages affiliate program
Tracks referrals, calculates commissions, processes payouts
Schedule: Weekly commission calculations
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
import secrets
import hashlib
import json

from ..config.settings import config
from ..database.models import Order, Sale, AgentLog, get_session


@dataclass
class Affiliate:
    """Affiliate partner data"""
    id: int
    name: str
    email: str
    referral_code: str
    commission_rate: float  # Percentage
    payout_method: str  # paypal, bank, etc.
    payout_details: Dict
    total_earned: float
    total_paid: float
    balance: float
    is_active: bool
    created_at: datetime


@dataclass
class Referral:
    """Referral transaction"""
    id: int
    affiliate_id: int
    referral_code: str
    order_id: int
    order_value: float
    commission: float
    status: str  # pending, approved, paid, rejected
    created_at: datetime
    approved_at: datetime = None


class AffiliateManager:
    """Manage affiliate program"""
    
    def __init__(self, db_session):
        self.session = db_session
        self.default_commission = 0.15  # 15% default
    
    def generate_referral_code(self, affiliate_name: str) -> str:
        """Generate unique referral code"""
        base = affiliate_name.lower().replace(' ', '')[:10]
        unique = secrets.token_hex(3)
        return f"{base}{unique}"
    
    async def create_affiliate(
        self,
        name: str,
        email: str,
        commission_rate: float = None,
        payout_method: str = 'paypal'
    ) -> Affiliate:
        """Create new affiliate"""
        from ..database.models import Affiliate as AffiliateModel
        
        referral_code = self.generate_referral_code(name)
        
        affiliate = AffiliateModel(
            name=name,
            email=email,
            referral_code=referral_code,
            commission_rate=commission_rate or self.default_commission,
            payout_method=payout_method,
            payout_details={},
            total_earned=0,
            total_paid=0,
            balance=0,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        self.session.add(affiliate)
        self.session.commit()
        
        print(f"✅ Created affiliate: {name} (Code: {referral_code})")
        
        # Send welcome email
        await self._send_welcome_email(affiliate)
        
        return affiliate
    
    async def track_referral(self, referral_code: str, order_id: int) -> bool:
        """Track a referral from order"""
        from ..database.models import Affiliate as AffiliateModel, Referral as ReferralModel
        
        # Find affiliate
        affiliate = self.session.query(AffiliateModel).filter_by(
            referral_code=referral_code,
            is_active=True
        ).first()
        
        if not affiliate:
            return False
        
        # Get order
        order = self.session.query(Order).get(order_id)
        if not order:
            return False
        
        # Calculate commission
        commission = order.total_price * affiliate.commission_rate
        
        # Create referral record
        referral = ReferralModel(
            affiliate_id=affiliate.id,
            referral_code=referral_code,
            order_id=order_id,
            order_value=order.total_price,
            commission=commission,
            status='pending',
            created_at=datetime.utcnow()
        )
        
        self.session.add(referral)
        
        # Update affiliate balance
        affiliate.balance += commission
        affiliate.total_earned += commission
        
        self.session.commit()
        
        print(f"✅ Tracked referral: {referral_code} → ${commission:.2f} commission")
        
        return True
    
    async def approve_referrals(self, days_old: int = 30):
        """Approve referrals after return period"""
        from ..database.models import Referral as ReferralModel
        
        cutoff = datetime.utcnow() - timedelta(days=days_old)
        
        pending = self.session.query(ReferralModel).filter(
            ReferralModel.status == 'pending',
            ReferralModel.created_at < cutoff
        ).all()
        
        for referral in pending:
            referral.status = 'approved'
            referral.approved_at = datetime.utcnow()
        
        self.session.commit()
        
        print(f"✅ Approved {len(pending)} referrals")
    
    async def process_payouts(self, min_payout: float = 50.0):
        """Process affiliate payouts"""
        from ..database.models import Affiliate as AffiliateModel
        
        affiliates = self.session.query(AffiliateModel).filter(
            AffiliateModel.balance >= min_payout,
            AffiliateModel.is_active == True
        ).all()
        
        for affiliate in affiliates:
            payout_amount = affiliate.balance
            
            # Process payout (would integrate with payment system)
            success = await self._send_payout(affiliate, payout_amount)
            
            if success:
                affiliate.balance = 0
                affiliate.total_paid += payout_amount
                
                # Mark referrals as paid
                from ..database.models import Referral as ReferralModel
                referrals = self.session.query(ReferralModel).filter(
                    ReferralModel.affiliate_id == affiliate.id,
                    ReferralModel.status == 'approved'
                ).all()
                
                for ref in referrals:
                    ref.status = 'paid'
                
                print(f"✅ Processed payout for {affiliate.name}: ${payout_amount:.2f}")
        
        self.session.commit()
    
    async def _send_welcome_email(self, affiliate):
        """Send welcome email to new affiliate"""
        email_content = f"""
Welcome to our Affiliate Program, {affiliate.name}!

Your referral code: {affiliate.referral_code}
Commission rate: {affiliate.commission_rate * 100}%

Share your code and earn on every sale!

Track your earnings: [Dashboard Link]
"""
        print(f"📧 Welcome email sent to {affiliate.email}")
    
    async def _send_payout(self, affiliate, amount: float) -> bool:
        """Send payout to affiliate"""
        # Would integrate with PayPal, Stripe, etc.
        print(f"💰 Payout to {affiliate.name}: ${amount:.2f} via {affiliate.payout_method}")
        return True
    
    def get_affiliate_stats(self, affiliate_id: int) -> Dict:
        """Get stats for an affiliate"""
        from ..database.models import Affiliate as AffiliateModel, Referral as ReferralModel
        
        affiliate = self.session.query(AffiliateModel).get(affiliate_id)
        if not affiliate:
            return None
        
        referrals = self.session.query(ReferralModel).filter_by(affiliate_id=affiliate_id).all()
        
        return {
            'name': affiliate.name,
            'referral_code': affiliate.referral_code,
            'commission_rate': affiliate.commission_rate,
            'total_earned': affiliate.total_earned,
            'total_paid': affiliate.total_paid,
            'current_balance': affiliate.balance,
            'total_referrals': len(referrals),
            'conversion_rate': len([r for r in referrals if r.status == 'paid']) / len(referrals) * 100 if referrals else 0
        }


class AffiliateAgent:
    """
    Affiliate Program Agent
    Manages affiliate program automatically
    """
    
    def __init__(self, db_session):
        self.session = db_session
        self.manager = AffiliateManager(db_session)
        self.running = False
    
    async def run(self):
        """Main agent loop"""
        self.running = True
        print("🤝 Affiliate Program Agent started")
        
        while self.running:
            try:
                # Weekly tasks
                await self._weekly_tasks()
                await asyncio.sleep(7 * 24 * 3600)  # Weekly
                
            except Exception as e:
                self._log_error(f"Affiliate agent error: {e}")
                await asyncio.sleep(24 * 3600)
    
    async def _weekly_tasks(self):
        """Run weekly affiliate tasks"""
        print("\n🤝 Running weekly affiliate tasks...")
        
        # Approve referrals past return period
        await self.manager.approve_referrals(days_old=30)
        
        # Process payouts
        await self.manager.process_payouts(min_payout=50.0)
        
        # Generate report
        await self._generate_weekly_report()
    
    async def _generate_weekly_report(self):
        """Generate weekly affiliate report"""
        from ..database.models import Affiliate as AffiliateModel
        
        affiliates = self.session.query(AffiliateModel).filter_by(is_active=True).all()
        
        print("\n📊 Weekly Affiliate Report")
        print("-" * 40)
        print(f"Total Affiliates: {len(affiliates)}")
        
        total_earned = sum(a.total_earned for a in affiliates)
        total_paid = sum(a.total_paid for a in affiliates)
        
        print(f"Total Earned: ${total_earned:.2f}")
        print(f"Total Paid: ${total_paid:.2f}")
        print(f"Outstanding Balance: ${total_earned - total_paid:.2f}")
        
        # Top affiliates
        top_affiliates = sorted(affiliates, key=lambda a: a.total_earned, reverse=True)[:5]
        print("\n🏆 Top Affiliates:")
        for i, aff in enumerate(top_affiliates, 1):
            print(f"   {i}. {aff.name}: ${aff.total_earned:.2f}")
    
    def _log_action(self, action: str, status: str, details: Dict):
        """Log agent action"""
        log = AgentLog(
            agent_name='affiliate',
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
        print("🛑 Affiliate Agent stopped")


# Standalone run
async def run_affiliate_agent():
    """Run affiliate agent standalone"""
    from ..database.models import init_database
    from ..config.settings import config
    
    engine = init_database(config.database_path)
    session = get_session(engine)
    
    agent = AffiliateAgent(session)
    await agent.run()


if __name__ == "__main__":
    asyncio.run(run_affiliate_agent())
