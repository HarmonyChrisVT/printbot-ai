"""
PrintBot AI - Customer Engagement Agent
========================================
Order tracking, review requests, abandoned cart recovery, social proof
Schedule: Every 15 minutes
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

from config.settings import config
from database.models import Order, Product, AgentLog, get_session


class OrderTrackingManager:
    """Manages order tracking updates"""
    
    def __init__(self, db_session):
        self.session = db_session
    
    async def update_tracking_status(self, order_id: str) -> Optional[Dict]:
        """Update order tracking status"""
        order = self.session.query(Order).filter_by(shopify_order_id=order_id).first()
        if not order or not order.printful_order_id:
            return None
        
        # Get tracking from fulfillment provider
        # This would call the provider's API
        
        tracking_stages = [
            'pending', 'confirmed', 'in_production', 'shipped',
            'in_transit', 'out_for_delivery', 'delivered'
        ]
        
        # Simulate tracking update
        current_stage = order.tracking_status or 'pending'
        
        # Check if stage should advance
        stage_index = tracking_stages.index(current_stage)
        
        # Advance stage based on time
        if order.shipped_at:
            hours_since_shipped = (datetime.utcnow() - order.shipped_at).total_seconds() / 3600
            
            if hours_since_shipped > 48 and current_stage == 'shipped':
                order.tracking_status = 'in_transit'
            elif hours_since_shipped > 72 and current_stage == 'in_transit':
                order.tracking_status = 'out_for_delivery'
            elif hours_since_shipped > 96 and current_stage == 'out_for_delivery':
                order.tracking_status = 'delivered'
                order.delivered_at = datetime.utcnow()
        
        self.session.commit()
        
        # Send tracking update email if status changed
        if order.tracking_status != current_stage:
            await self._send_tracking_update_email(order)
        
        return {
            'order_id': order_id,
            'status': order.tracking_status,
            'tracking_number': order.tracking_number,
            'tracking_url': order.tracking_url
        }
    
    async def _send_tracking_update_email(self, order: Order):
        """Send tracking status update email"""
        status_messages = {
            'confirmed': 'Your order has been confirmed!',
            'in_production': 'Your items are being printed!',
            'shipped': 'Your order has shipped!',
            'in_transit': 'Your order is on the way!',
            'out_for_delivery': 'Your order is out for delivery!',
            'delivered': 'Your order has been delivered!'
        }
        
        message = status_messages.get(order.tracking_status, 'Order update')
        
        print(f"📧 Tracking update for order #{order.order_number}: {message}")
        # Would send actual email here
    
    async def get_tracking_page_data(self, order_id: str) -> Optional[Dict]:
        """Get data for customer tracking page"""
        order = self.session.query(Order).filter_by(shopify_order_id=order_id).first()
        if not order:
            return None
        
        tracking_stages = [
            {'name': 'Order Placed', 'completed': True, 'date': order.created_at},
            {'name': 'Confirmed', 'completed': order.tracking_status in ['confirmed', 'in_production', 'shipped', 'in_transit', 'out_for_delivery', 'delivered']},
            {'name': 'In Production', 'completed': order.tracking_status in ['in_production', 'shipped', 'in_transit', 'out_for_delivery', 'delivered']},
            {'name': 'Shipped', 'completed': order.tracking_status in ['shipped', 'in_transit', 'out_for_delivery', 'delivered']},
            {'name': 'In Transit', 'completed': order.tracking_status in ['in_transit', 'out_for_delivery', 'delivered']},
            {'name': 'Out for Delivery', 'completed': order.tracking_status in ['out_for_delivery', 'delivered']},
            {'name': 'Delivered', 'completed': order.tracking_status == 'delivered'}
        ]
        
        return {
            'order_number': order.order_number,
            'tracking_number': order.tracking_number,
            'tracking_url': order.tracking_url,
            'current_status': order.tracking_status,
            'stages': tracking_stages,
            'estimated_delivery': order.estimated_delivery
        }


class ReviewRequestSystem:
    """Manages customer review requests"""
    
    def __init__(self, db_session):
        self.session = db_session
        self.review_delay_days = 7  # Request review 7 days after delivery
        self.incentive_discount = 0.15  # 15% off next order
    
    async def process_review_requests(self):
        """Process pending review requests"""
        # Find delivered orders without review requests
        orders = self.session.query(Order).filter(
            Order.tracking_status == 'delivered',
            Order.delivered_at < datetime.utcnow() - timedelta(days=self.review_delay_days),
            Order.review_requested == False
        ).all()
        
        for order in orders:
            await self._send_review_request(order)
            order.review_requested = True
            self.session.commit()
    
    async def _send_review_request(self, order: Order):
        """Send review request email"""
        discount_code = f"REVIEW{order.id}"
        
        email_content = f"""
Hi there!

We hope you're loving your recent purchase! 

Would you mind taking a moment to leave a review? Your feedback helps other customers and helps us improve.

As a thank you, here's 15% off your next order:

🎁 Code: {discount_code}

[Leave a Review]

Thanks for your support!
"""
        
        print(f"📧 Review request sent for order #{order.order_number}")
        # Would send actual email
    
    async def process_review_submission(self, order_id: str, rating: int, review: str, photos: List[str] = None):
        """Process a submitted review"""
        from database.models import ProductReview
        
        order = self.session.query(Order).filter_by(shopify_order_id=order_id).first()
        if not order:
            return False
        
        # Create review
        for item in order.items:
            if item.product_id:
                product_review = ProductReview(
                    product_id=item.product_id,
                    order_id=order.id,
                    customer_name=order.customer_name,
                    rating=rating,
                    review_text=review,
                    photos=json.dumps(photos) if photos else None,
                    verified_purchase=True,
                    created_at=datetime.utcnow()
                )
                self.session.add(product_review)
        
        self.session.commit()
        
        # Send thank you email with discount
        await self._send_review_thank_you(order, rating)
        
        return True
    
    async def _send_review_thank_you(self, order: Order, rating: int):
        """Send thank you email for review"""
        print(f"📧 Thank you email sent for order #{order.order_number} (Rating: {rating})")


class AbandonedCartRecovery:
    """Abandoned cart recovery system"""
    
    def __init__(self, db_session):
        self.session = db_session
        self.recovery_sequence = [
            {'delay_hours': 1, 'discount': 0, 'subject': 'You left something behind!'},
            {'delay_hours': 24, 'discount': 0.10, 'subject': 'Still thinking it over? 10% off inside'},
            {'delay_hours': 72, 'discount': 0.15, 'subject': 'Last chance: 15% off your cart'}
        ]
    
    async def process_abandoned_carts(self):
        """Process abandoned carts"""
        from database.models import AbandonedCart
        
        # Find abandoned carts
        carts = self.session.query(AbandonedCart).filter(
            AbandonedCart.recovered == False,
            AbandonedCart.emails_sent < len(self.recovery_sequence)
        ).all()
        
        for cart in carts:
            await self._process_cart_recovery(cart)
    
    async def _process_cart_recovery(self, cart):
        """Process recovery for a single cart"""
        emails_sent = cart.emails_sent
        
        if emails_sent >= len(self.recovery_sequence):
            return
        
        next_email = self.recovery_sequence[emails_sent]
        scheduled_time = cart.abandoned_at + timedelta(hours=next_email['delay_hours'])
        
        if datetime.utcnow() >= scheduled_time:
            await self._send_recovery_email(cart, next_email)
            cart.emails_sent += 1
            self.session.commit()
    
    async def _send_recovery_email(self, cart, email_config):
        """Send recovery email"""
        discount_code = f"COMEBACK{cart.id}" if email_config['discount'] > 0 else None
        
        items_html = ""
        for item in cart.items:
            items_html += f"<li>{item['name']} - ${item['price']}</li>"
        
        email_content = f"""
Hi there!

We noticed you left some items in your cart:

<ul>
{items_html}
</ul>

{"🎁 Use code " + discount_code + " for " + str(int(email_config['discount']*100)) + "% off!" if discount_code else ""}

[Complete Your Purchase]

"""
        
        print(f"📧 Recovery email sent to {cart.email} (Discount: {email_config['discount']*100}%)")
    
    async def mark_cart_recovered(self, cart_id: int):
        """Mark cart as recovered"""
        from database.models import AbandonedCart
        
        cart = self.session.query(AbandonedCart).get(cart_id)
        if cart:
            cart.recovered = True
            cart.recovered_at = datetime.utcnow()
            self.session.commit()
            
            print(f"✅ Cart {cart_id} recovered!")


class SocialProofInjector:
    """Injects social proof into customer journey"""
    
    def __init__(self, db_session):
        self.session = db_session
    
    def get_product_social_proof(self, product_id: int) -> Dict:
        """Get social proof for a product"""
        from database.models import ProductReview, Sale
        
        # Get recent sales
        recent_sales = self.session.query(Sale).filter(
            Sale.product_id == product_id,
            Sale.sale_date > datetime.utcnow() - timedelta(days=7)
        ).count()
        
        # Get reviews
        reviews = self.session.query(ProductReview).filter(
            ProductReview.product_id == product_id,
            ProductReview.verified_purchase == True
        ).all()
        
        avg_rating = sum(r.rating for r in reviews) / len(reviews) if reviews else 0
        
        # Get recent review for notification
        recent_review = None
        if reviews:
            latest = max(reviews, key=lambda r: r.created_at)
            recent_review = {
                'name': latest.customer_name.split()[0] + ' from ' + self._get_random_location(),
                'rating': latest.rating,
                'text': latest.review_text[:100] + '...' if len(latest.review_text) > 100 else latest.review_text,
                'time_ago': self._format_time_ago(latest.created_at)
            }
        
        return {
            'recent_sales': recent_sales,
            'total_reviews': len(reviews),
            'avg_rating': round(avg_rating, 1),
            'recent_purchase_notification': recent_sales > 0,
            'recent_review': recent_review,
            'stock_urgency': recent_sales > 5  # Show low stock message if selling fast
        }
    
    def get_cart_social_proof(self, cart_items: List[Dict]) -> Dict:
        """Get social proof for cart page"""
        total_sold = 0
        recent_buyers = []
        
        for item in cart_items:
            from database.models import Sale
            sales = self.session.query(Sale).filter(
                Sale.product_id == item['product_id'],
                Sale.sale_date > datetime.utcnow() - timedelta(hours=24)
            ).count()
            total_sold += sales
        
        return {
            'total_sold_today': total_sold,
            'cart_urgency': total_sold > 10,
            'recent_buyer_notification': total_sold > 0
        }
    
    def _get_random_location(self) -> str:
        """Get random location for social proof"""
        locations = [
            'New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix',
            'London', 'Toronto', 'Sydney', 'Melbourne', 'Vancouver',
            'Miami', 'Seattle', 'Denver', 'Austin', 'Boston'
        ]
        import random
        return random.choice(locations)
    
    def _format_time_ago(self, timestamp: datetime) -> str:
        """Format time ago for social proof"""
        diff = datetime.utcnow() - timestamp
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        else:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"


class CustomerEngagementAgent:
    """
    Main Customer Engagement Agent
    Handles tracking, reviews, cart recovery, social proof
    """
    
    def __init__(self, db_session):
        self.session = db_session
        self.tracking = OrderTrackingManager(db_session)
        self.reviews = ReviewRequestSystem(db_session)
        self.cart_recovery = AbandonedCartRecovery(db_session)
        self.social_proof = SocialProofInjector(db_session)
        self.running = False
    
    async def run(self):
        """Main agent loop"""
        self.running = True
        print("💬 Customer Engagement Agent started")
        
        while self.running:
            try:
                await self._process_cycle()
                await asyncio.sleep(900)  # Every 15 minutes
                
            except Exception as e:
                self._log_error(f"Engagement agent error: {e}")
                await asyncio.sleep(300)
    
    async def _process_cycle(self):
        """Process one engagement cycle"""
        print("💬 Running customer engagement cycle...")
        
        # 1. Update order tracking
        await self._update_order_tracking()
        
        # 2. Process review requests
        await self.reviews.process_review_requests()
        
        # 3. Process abandoned carts
        await self.cart_recovery.process_abandoned_carts()
        
        print("💬 Engagement cycle complete")
    
    async def _update_order_tracking(self):
        """Update tracking for all pending orders"""
        orders = self.session.query(Order).filter(
            Order.tracking_status.in_(['confirmed', 'in_production', 'shipped', 'in_transit', 'out_for_delivery'])
        ).all()
        
        for order in orders:
            await self.tracking.update_tracking_status(order.shopify_order_id)
    
    # Public API methods
    async def get_tracking_info(self, order_id: str) -> Optional[Dict]:
        """Get tracking info for customer"""
        return await self.tracking.get_tracking_page_data(order_id)
    
    def get_product_social_proof(self, product_id: int) -> Dict:
        """Get social proof for product page"""
        return self.social_proof.get_product_social_proof(product_id)
    
    def get_cart_social_proof(self, cart_items: List[Dict]) -> Dict:
        """Get social proof for cart page"""
        return self.social_proof.get_cart_social_proof(cart_items)
    
    async def submit_review(self, order_id: str, rating: int, review: str, photos: List[str] = None):
        """Submit a customer review"""
        return await self.reviews.process_review_submission(order_id, rating, review, photos)
    
    def _log_error(self, message: str):
        """Log error"""
        log = AgentLog(
            agent_name='customer_engagement',
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
        print("🛑 Customer Engagement Agent stopped")


# Standalone run
async def run_customer_engagement_agent():
    """Run engagement agent standalone"""
    from database.models import init_database
    from config.settings import config
    
    engine = init_database(config.database_path)
    session = get_session(engine)
    
    agent = CustomerEngagementAgent(session)
    await agent.run()


if __name__ == "__main__":
    asyncio.run(run_customer_engagement_agent())
