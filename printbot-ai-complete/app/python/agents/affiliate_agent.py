"""
Affiliate Agent - Manage affiliate program and referrals
"""

import os
import random
import string
from typing import Dict, Any, List, Optional
from datetime import datetime

from python.utils.logger import get_logger
from database.models import get_db_session, Affiliate, Order

logger = get_logger(__name__)

class AffiliateAgent:
    """AI agent that manages the affiliate program"""
    
    def __init__(self):
        self.default_commission = 0.10  # 10% default
    
    async def configure(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Configure the affiliate agent"""
        self.default_commission = config.get('commission_rate', 0.10)
        return {'status': 'configured', 'commission': self.default_commission}
    
    async def create_affiliate(
        self, 
        name: str, 
        email: str,
        commission_rate: Optional[float] = None
    ) -> Dict[str, Any]:
        """Create a new affiliate"""
        
        # Generate unique referral code
        referral_code = self._generate_referral_code(name)
        
        session = get_db_session()
        try:
            affiliate = Affiliate(
                name=name,
                email=email,
                referral_code=referral_code,
                commission_rate=commission_rate or self.default_commission,
                is_active=True
            )
            
            session.add(affiliate)
            session.commit()
            
            logger.info(f"Created affiliate: {name} with code {referral_code}")
            
            return {
                'success': True,
                'affiliate_id': affiliate.id,
                'name': name,
                'referral_code': referral_code,
                'referral_link': f"https://yourstore.com/?ref={referral_code}",
                'commission_rate': affiliate.commission_rate
            }
        finally:
            session.close()
    
    def _generate_referral_code(self, name: str) -> str:
        """Generate a unique referral code"""
        # Use first 3 letters of name + random string
        prefix = name[:3].upper()
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        return f"{prefix}{suffix}"
    
    async def track_referral(self, referral_code: str, order_amount: float) -> Dict[str, Any]:
        """Track a referral sale"""
        session = get_db_session()
        try:
            affiliate = session.query(Affiliate).filter_by(
                referral_code=referral_code
            ).first()
            
            if not affiliate:
                return {'error': 'Invalid referral code'}
            
            # Calculate commission
            commission = order_amount * affiliate.commission_rate
            
            # Update affiliate stats
            affiliate.total_referrals += 1
            affiliate.total_sales += order_amount
            affiliate.total_commission += commission
            
            session.commit()
            
            logger.info(f"Tracked referral: {referral_code} - ${order_amount} sale, ${commission} commission")
            
            return {
                'success': True,
                'affiliate': affiliate.name,
                'order_amount': order_amount,
                'commission': round(commission, 2),
                'commission_rate': affiliate.commission_rate,
                'total_referrals': affiliate.total_referrals,
                'total_earned': round(affiliate.total_commission, 2)
            }
        finally:
            session.close()
    
    async def get_affiliate_dashboard(self, affiliate_id: int) -> Dict[str, Any]:
        """Get affiliate dashboard data"""
        session = get_db_session()
        try:
            affiliate = session.query(Affiliate).filter_by(id=affiliate_id).first()
            
            if not affiliate:
                return {'error': 'Affiliate not found'}
            
            # Calculate monthly stats (simulated)
            this_month_sales = affiliate.total_sales * 0.2  # Assume 20% is this month
            this_month_commission = affiliate.total_commission * 0.2
            
            return {
                'affiliate_id': affiliate.id,
                'name': affiliate.name,
                'referral_code': affiliate.referral_code,
                'referral_link': f"https://yourstore.com/?ref={affiliate.referral_code}",
                'status': 'active' if affiliate.is_active else 'inactive',
                'stats': {
                    'total_referrals': affiliate.total_referrals,
                    'total_sales': round(affiliate.total_sales, 2),
                    'total_commission': round(affiliate.total_commission, 2),
                    'this_month_sales': round(this_month_sales, 2),
                    'this_month_commission': round(this_month_commission, 2)
                },
                'commission_rate': affiliate.commission_rate,
                'pending_payout': round(affiliate.total_commission * 0.3, 2)  # Assume 30% pending
            }
        finally:
            session.close()
    
    async def get_all_affiliates(self) -> List[Dict[str, Any]]:
        """Get all affiliates"""
        session = get_db_session()
        try:
            affiliates = session.query(Affiliate).order_by(
                Affiliate.total_sales.desc()
            ).all()
            
            return [a.to_dict() for a in affiliates]
        finally:
            session.close()
    
    async def get_analytics(self) -> Dict[str, Any]:
        """Get affiliate program analytics"""
        session = get_db_session()
        try:
            affiliates = session.query(Affiliate).all()
            
            total_affiliates = len(affiliates)
            active_affiliates = len([a for a in affiliates if a.is_active])
            total_sales = sum([a.total_sales for a in affiliates])
            total_commission = sum([a.total_commission for a in affiliates])
            
            # Top performers
            top_affiliates = sorted(
                affiliates, 
                key=lambda a: a.total_sales, 
                reverse=True
            )[:5]
            
            return {
                'total_affiliates': total_affiliates,
                'active_affiliates': active_affiliates,
                'total_referral_sales': round(total_sales, 2),
                'total_commission_paid': round(total_commission, 2),
                'avg_commission_rate': self.default_commission,
                'top_performers': [
                    {
                        'name': a.name,
                        'sales': round(a.total_sales, 2),
                        'commission': round(a.total_commission, 2)
                    }
                    for a in top_affiliates
                ]
            }
        finally:
            session.close()
    
    async def generate_promo_materials(self, affiliate_id: int) -> Dict[str, Any]:
        """Generate promotional materials for an affiliate"""
        session = get_db_session()
        try:
            affiliate = session.query(Affiliate).filter_by(id=affiliate_id).first()
            
            if not affiliate:
                return {'error': 'Affiliate not found'}
            
            return {
                'affiliate_name': affiliate.name,
                'referral_code': affiliate.referral_code,
                'referral_link': f"https://yourstore.com/?ref={affiliate.referral_code}",
                'promo_materials': {
                    'banner_urls': [
                        f"https://yourstore.com/affiliates/banners/300x250/{affiliate.referral_code}.png",
                        f"https://yourstore.com/affiliates/banners/728x90/{affiliate.referral_code}.png"
                    ],
                    'email_template': f"""
                    Subject: Check out these amazing custom designs!
                    
                    Hi [Name],
                    
                    I found this awesome print-on-demand store and thought you'd love it!
                    
                    Use my link for exclusive access: https://yourstore.com/?ref={affiliate.referral_code}
                    
                    Best,
                    {affiliate.name}
                    """,
                    'social_posts': [
                        f"Love custom merch? Check this out! 👉 https://yourstore.com/?ref={affiliate.referral_code}",
                        f"Found my new favorite store for custom designs! 🎨 https://yourstore.com/?ref={affiliate.referral_code}"
                    ]
                }
            }
        finally:
            session.close()
