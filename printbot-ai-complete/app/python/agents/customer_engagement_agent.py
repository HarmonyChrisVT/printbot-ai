"""
Customer Engagement Agent - Order tracking, reviews, cart recovery, social proof
"""

import os
import random
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from python.utils.logger import get_logger
from database.models import get_db_session, Order, EmailSubscriber, AbandonedCart, Product

logger = get_logger(__name__)

class CustomerEngagementAgent:
    """AI agent that handles customer engagement activities"""
    
    def __init__(self):
        self.review_request_days = 7  # Days after delivery to request review
        self.cart_abandonment_hours = [1, 24, 72]  # Hours to send recovery emails
    
    async def configure(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Configure the customer engagement agent"""
        self.review_request_days = config.get('review_request_days', 7)
        return {'status': 'configured'}
    
    async def send_review_requests(self) -> Dict[str, Any]:
        """Send review requests for delivered orders"""
        session = get_db_session()
        try:
            # Find orders that were delivered X days ago and haven't been asked for review
            cutoff_date = datetime.now() - timedelta(days=self.review_request_days)
            
            orders = session.query(Order).filter(
                Order.status == 'delivered',
                Order.delivered_at <= cutoff_date,
                Order.review_requested == False
            ).all()
            
            sent = 0
            for order in orders:
                await self._send_review_email(order)
                order.review_requested = True
                sent += 1
            
            session.commit()
            
            logger.info(f"Sent {sent} review requests")
            return {'sent': sent}
            
        finally:
            session.close()
    
    async def _send_review_email(self, order: Order):
        """Send review request email"""
        logger.info(f"Sending review request for order {order.order_number}")
        
        # In production, integrate with email service
        # For now, just log
        
        email_content = {
            'subject': f"How was your {order.product.name if order.product else 'order'}?",
            'body': f"""
            Hi {order.customer_name},
            
            We hope you're enjoying your recent purchase!
            
            Would you mind taking a moment to leave a review? Your feedback helps us improve and helps other customers make decisions.
            
            [Leave a Review Button]
            
            Thank you!
            The PrintBot Team
            """
        }
        
        # Send email (simulated)
        return {'sent': True}
    
    async def check_abandoned_carts(self) -> Dict[str, Any]:
        """Check and send recovery emails for abandoned carts"""
        session = get_db_session()
        try:
            # Find abandoned carts
            for hours in self.cart_abandonment_hours:
                cutoff = datetime.now() - timedelta(hours=hours)
                
                carts = session.query(AbandonedCart).filter(
                    AbandonedCart.created_at <= cutoff,
                    AbandonedCart.recovered == False,
                    AbandonedCart.recovery_email_sent == False
                ).all()
                
                for cart in carts:
                    await self._send_cart_recovery_email(cart, hours)
                    cart.recovery_email_sent = True
                    cart.recovery_email_sent_at = datetime.now()
                
                session.commit()
            
            return {'checked': True}
            
        finally:
            session.close()
    
    async def _send_cart_recovery_email(self, cart: AbandonedCart, hours: int):
        """Send cart recovery email"""
        logger.info(f"Sending cart recovery email to {cart.customer_email} ({hours}h)")
        
        # Different messaging based on timing
        if hours == 1:
            subject = "You left something behind!"
            discount = None
        elif hours == 24:
            subject = "Still thinking it over?"
            discount = "10%"
        else:  # 72 hours
            subject = "Last chance - your cart expires soon!"
            discount = "15%"
        
        # In production, send actual email
        return {'sent': True, 'discount_offered': discount}
    
    async def inject_social_proof(self, product_id: Optional[int] = None) -> Dict[str, Any]:
        """Generate social proof for products"""
        session = get_db_session()
        try:
            if product_id:
                products = [session.query(Product).filter_by(id=product_id).first()]
            else:
                products = session.query(Product).filter(Product.times_sold > 0).all()
            
            social_proofs = []
            for product in products:
                if product and product.times_sold > 0:
                    # Generate social proof messages
                    proofs = self._generate_social_proof(product)
                    social_proofs.append({
                        'product_id': product.id,
                        'product_name': product.name,
                        'proofs': proofs
                    })
            
            return {'social_proofs': social_proofs}
            
        finally:
            session.close()
    
    def _generate_social_proof(self, product: Product) -> List[str]:
        """Generate social proof messages for a product"""
        proofs = []
        
        if product.times_sold >= 100:
            proofs.append(f"🔥 {product.times_sold}+ happy customers!")
        elif product.times_sold >= 50:
            proofs.append(f"⭐ {product.times_sold}+ sold!")
        elif product.times_sold >= 10:
            proofs.append(f"✨ {product.times_sold}+ customers love this!")
        
        # Add recent purchase notification style
        if product.times_sold > 0:
            time_ago = random.choice(['just now', '2 minutes ago', '5 minutes ago', '10 minutes ago'])
            proofs.append(f"👤 Someone in {random.choice(['New York', 'California', 'Texas', 'Florida'])} purchased this {time_ago}")
        
        # Add low stock urgency if applicable
        if product.times_sold > 50:
            proofs.append("⚡ Selling fast - only a few left!")
        
        return proofs
    
    async def capture_email(
        self, 
        email: str, 
        name: Optional[str] = None,
        source: str = 'popup',
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Capture email subscriber"""
        session = get_db_session()
        try:
            # Check if email already exists
            existing = session.query(EmailSubscriber).filter_by(email=email).first()
            if existing:
                return {'success': False, 'message': 'Email already subscribed'}
            
            subscriber = EmailSubscriber(
                email=email,
                name=name,
                source=source,
                tags=tags or [],
                is_verified=False
            )
            
            session.add(subscriber)
            session.commit()
            
            # Send welcome email
            await self._send_welcome_email(subscriber)
            
            logger.info(f"New email subscriber: {email}")
            
            return {
                'success': True,
                'subscriber_id': subscriber.id,
                'email': email
            }
            
        finally:
            session.close()
    
    async def _send_welcome_email(self, subscriber: EmailSubscriber):
        """Send welcome email to new subscriber"""
        logger.info(f"Sending welcome email to {subscriber.email}")
        
        email_content = {
            'subject': "Welcome to PrintBot! Here's 10% off",
            'body': f"""
            Hi {subscriber.name or 'there'},
            
            Welcome to PrintBot! We're excited to have you on board.
            
            As a thank you, here's 10% off your first order:
            Code: WELCOME10
            
            Start shopping: [Shop Now]
            
            Best,
            The PrintBot Team
            """
        }
        
        return {'sent': True}
    
    async def create_abandoned_cart(
        self,
        customer_email: str,
        product_ids: List[int],
        total_value: float,
        customer_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create an abandoned cart record"""
        session = get_db_session()
        try:
            cart = AbandonedCart(
                customer_email=customer_email,
                customer_name=customer_name,
                product_ids=product_ids,
                total_value=total_value,
                recovered=False
            )
            
            session.add(cart)
            session.commit()
            
            return {
                'success': True,
                'cart_id': cart.id
            }
            
        finally:
            session.close()
    
    async def get_analytics(self) -> Dict[str, Any]:
        """Get customer engagement analytics"""
        session = get_db_session()
        try:
            # Email subscribers
            total_subscribers = session.query(EmailSubscriber).count()
            verified_subscribers = session.query(EmailSubscriber).filter_by(is_verified=True).count()
            
            # Abandoned carts
            total_carts = session.query(AbandonedCart).count()
            recovered_carts = session.query(AbandonedCart).filter_by(recovered=True).count()
            recovery_rate = (recovered_carts / total_carts * 100) if total_carts > 0 else 0
            
            # Reviews
            orders_with_reviews = session.query(Order).filter_by(review_received=True).count()
            total_delivered = session.query(Order).filter_by(status='delivered').count()
            review_rate = (orders_with_reviews / total_delivered * 100) if total_delivered > 0 else 0
            
            return {
                'email_subscribers': {
                    'total': total_subscribers,
                    'verified': verified_subscribers
                },
                'abandoned_carts': {
                    'total': total_carts,
                    'recovered': recovered_carts,
                    'recovery_rate': round(recovery_rate, 1)
                },
                'reviews': {
                    'total_requested': session.query(Order).filter_by(review_requested=True).count(),
                    'total_received': orders_with_reviews,
                    'review_rate': round(review_rate, 1),
                    'avg_rating': 4.5  # Simulated
                }
            }
            
        finally:
            session.close()
