"""
PrintBot AI - Fulfillment Agent
================================
Processes orders, syncs with Printful, sends tracking.
Schedule: Every 5 minutes
"""
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ..config.settings import config
from ..database.models import Order, OrderItem, Product, Sale, AgentLog, get_session


class PrintfulAPI:
    """Printful API wrapper with backup provider support"""
    
    def __init__(self):
        self.api_key = config.printful.api_key
        self.store_id = config.printful.store_id
        self.base_url = config.printful.api_base
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        self.current_provider = 'printful'
        self.backup_providers = config.printful.backup_providers
    
    async def _request(self, method: str, endpoint: str, data: Dict = None) -> Optional[Dict]:
        """Make API request with retry logic"""
        url = f"{self.base_url}{endpoint}"
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                if method == 'GET':
                    async with session.get(url, timeout=30) as response:
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 429:  # Rate limited
                            print("⚠️ Printful rate limited, backing off...")
                            await asyncio.sleep(60)
                            return None
                        else:
                            print(f"❌ Printful API error: {response.status}")
                            return None
                
                elif method == 'POST':
                    async with session.post(url, json=data, timeout=30) as response:
                        if response.status in [200, 201]:
                            return await response.json()
                        else:
                            print(f"❌ Printful API error: {response.status}")
                            return None
                            
            except Exception as e:
                print(f"❌ Printful request error: {e}")
                return None
    
    async def get_orders(self, status: str = None) -> List[Dict]:
        """Get orders from Printful"""
        endpoint = '/orders'
        if status:
            endpoint += f'?status={status}'
        
        response = await self._request('GET', endpoint)
        return response.get('result', []) if response else []
    
    async def create_order(self, order_data: Dict) -> Optional[Dict]:
        """Create a new order in Printful"""
        endpoint = '/orders'
        
        # Format order for Printful
        printful_order = {
            'external_id': order_data.get('shopify_order_id'),
            'shipping': order_data.get('shipping_address'),
            'recipient': {
                'name': order_data.get('customer_name'),
                'email': order_data.get('customer_email'),
                **order_data.get('shipping_address', {})
            },
            'items': [
                {
                    'variant_id': item.get('printful_variant_id'),
                    'quantity': item.get('quantity'),
                    'files': [{
                        'url': item.get('design_url')
                    }]
                }
                for item in order_data.get('items', [])
            ]
        }
        
        response = await self._request('POST', endpoint, printful_order)
        return response
    
    async def get_order_status(self, printful_order_id: str) -> Optional[Dict]:
        """Get order status from Printful"""
        endpoint = f'/orders/{printful_order_id}'
        response = await self._request('GET', endpoint)
        return response.get('result') if response else None
    
    async def cancel_order(self, printful_order_id: str) -> bool:
        """Cancel an order in Printful"""
        endpoint = f'/orders/{printful_order_id}'
        response = await self._request('DELETE', endpoint)
        return response is not None
    
    def switch_to_backup(self) -> bool:
        """Switch to a backup fulfillment provider"""
        for provider in self.backup_providers:
            if provider.get('enabled'):
                print(f"🔄 Switching to backup provider: {provider['name']}")
                self.current_provider = provider['name']
                # Would update API credentials here
                return True
        
        print("❌ No backup providers available")
        return False


class EmailNotifier:
    """Sends email notifications for order updates"""
    
    def __init__(self):
        self.smtp_host = config.fulfillment.smtp_host
        self.smtp_port = config.fulfillment.smtp_port
        self.smtp_user = config.fulfillment.smtp_user
        self.smtp_password = config.fulfillment.smtp_password
        self.from_email = config.fulfillment.smtp_user
    
    def _create_tracking_email(self, order: Order) -> MIMEMultipart:
        """Create tracking notification email"""
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Your order #{order.order_number} has shipped! 🚚"
        msg['From'] = self.from_email
        msg['To'] = order.customer_email
        
        # Plain text version
        text_body = f"""
Hi there!

Great news! Your order #{order.order_number} has been shipped.

Tracking Number: {order.tracking_number}
Track your package: {order.tracking_url}

Items shipped:
"""
        for item in order.items:
            text_body += f"- {item.quantity}x {item.product.title if item.product else 'Product'}\n"
        
        text_body += """
Thanks for shopping with us!

Questions? Just reply to this email.
"""
        
        # HTML version
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #4CAF50; color: white; padding: 20px; text-align: center; }}
        .content {{ background: #f9f9f9; padding: 20px; margin: 20px 0; }}
        .tracking {{ background: #e3f2fd; padding: 15px; margin: 15px 0; border-left: 4px solid #2196F3; }}
        .button {{ display: inline-block; background: #2196F3; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; }}
        .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚚 Your Order Has Shipped!</h1>
        </div>
        
        <div class="content">
            <p>Hi there!</p>
            <p>Great news! Your order <strong>#{order.order_number}</strong> has been shipped and is on its way to you.</p>
            
            <div class="tracking">
                <h3>Tracking Information</h3>
                <p><strong>Tracking Number:</strong> {order.tracking_number}</p>
                <p><a href="{order.tracking_url}" class="button">Track Your Package</a></p>
            </div>
            
            <h3>Items in this shipment:</h3>
            <ul>
"""
        for item in order.items:
            product_title = item.product.title if item.product else 'Product'
            html_body += f"<li>{item.quantity}x {product_title}</li>\n"
        
        html_body += """
            </ul>
        </div>
        
        <div class="footer">
            <p>Thanks for shopping with us!</p>
            <p>Questions? Just reply to this email.</p>
        </div>
    </div>
</body>
</html>
"""
        
        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))
        
        return msg
    
    async def send_tracking_email(self, order: Order) -> bool:
        """Send tracking notification email"""
        if not all([self.smtp_host, self.smtp_user, self.smtp_password]):
            print("⚠️ Email not configured, skipping notification")
            return False
        
        try:
            msg = self._create_tracking_email(order)
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            print(f"✅ Tracking email sent to {order.customer_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False


class FulfillmentAgent:
    """
    Main Fulfillment Agent
    Polls orders, syncs with Printful, sends notifications
    """
    
    def __init__(self, db_session):
        self.session = db_session
        self.printful = PrintfulAPI()
        self.email = EmailNotifier()
        self.running = False
    
    async def run(self):
        """Main agent loop"""
        self.running = True
        print("📦 Fulfillment Agent started")
        
        while self.running:
            try:
                await self._process_cycle()
                
                # Wait for next poll
                await asyncio.sleep(config.fulfillment.order_poll_interval)
                
            except Exception as e:
                self._log_error(f"Fulfillment agent error: {e}")
                await asyncio.sleep(60)  # Wait 1 min on error
    
    async def _process_cycle(self):
        """Process one fulfillment cycle"""
        # 1. Poll for new orders from Shopify
        await self._poll_new_orders()
        
        # 2. Sync pending orders with Printful
        await self._sync_printful_orders()
        
        # 3. Check for shipped orders and send notifications
        await self._process_shipped_orders()
        
        # 4. Update analytics
        await self._update_analytics()
    
    async def _poll_new_orders(self):
        """Poll Shopify for new orders"""
        try:
            from ..integrations.shopify import ShopifyAPI
            shopify = ShopifyAPI()
            
            # Get orders created since last check
            last_check = datetime.utcnow() - timedelta(minutes=10)
            orders = await shopify.get_orders(since_id=None, status='any')
            
            for shopify_order in orders:
                # Check if already in database
                existing = self.session.query(Order).filter_by(
                    shopify_order_id=str(shopify_order.get('id'))
                ).first()
                
                if existing:
                    continue
                
                # Create new order
                order = Order(
                    shopify_order_id=str(shopify_order.get('id')),
                    order_number=shopify_order.get('name'),
                    customer_email=shopify_order.get('email'),
                    customer_name=self._get_customer_name(shopify_order),
                    shipping_address=shopify_order.get('shipping_address', {}),
                    total_price=float(shopify_order.get('total_price', 0)),
                    subtotal_price=float(shopify_order.get('subtotal_price', 0)),
                    tax_price=float(shopify_order.get('total_tax', 0)),
                    shipping_price=float(shopify_order.get('shipping_lines', [{}])[0].get('price', 0)),
                    discount_price=float(shopify_order.get('total_discounts', 0)),
                    financial_status=shopify_order.get('financial_status'),
                    fulfillment_status=shopify_order.get('fulfillment_status') or 'unfulfilled',
                    created_at=datetime.fromisoformat(shopify_order.get('created_at').replace('Z', '+00:00')),
                    processed_at=datetime.utcnow()
                )
                
                self.session.add(order)
                self.session.flush()  # Get order ID
                
                # Add order items
                for item_data in shopify_order.get('line_items', []):
                    # Find product in database
                    product = self.session.query(Product).filter_by(
                        shopify_id=str(item_data.get('product_id'))
                    ).first()
                    
                    order_item = OrderItem(
                        order_id=order.id,
                        product_id=product.id if product else None,
                        quantity=item_data.get('quantity'),
                        price=float(item_data.get('price', 0))
                    )
                    self.session.add(order_item)
                
                self.session.commit()
                
                print(f"✅ New order received: #{order.order_number}")
                
                # Log
                self._log_action("order_received", "success", {
                    "order_id": order.id,
                    "order_number": order.order_number,
                    "total": order.total_price
                })
                
        except Exception as e:
            print(f"❌ Error polling orders: {e}")
    
    async def _sync_printful_orders(self):
        """Sync pending orders with Printful"""
        # Get unfulfilled orders
        pending_orders = self.session.query(Order).filter(
            Order.fulfillment_status == 'unfulfilled',
            Order.printful_order_id == None
        ).all()
        
        for order in pending_orders:
            try:
                # Prepare order data for Printful
                order_data = {
                    'shopify_order_id': order.shopify_order_id,
                    'customer_name': order.customer_name,
                    'customer_email': order.customer_email,
                    'shipping_address': order.shipping_address,
                    'items': []
                }
                
                for item in order.items:
                    if item.product:
                        order_data['items'].append({
                            'printful_variant_id': item.product.variants[0].sku if item.product.variants else None,
                            'quantity': item.quantity,
                            'design_url': item.product.design_url
                        })
                
                # Create order in Printful
                result = await self.printful.create_order(order_data)
                
                if result:
                    order.printful_order_id = result.get('result', {}).get('id')
                    self.session.commit()
                    
                    print(f"✅ Order #{order.order_number} sent to Printful")
                    
                    self._log_action("printful_order_created", "success", {
                        "order_id": order.id,
                        "printful_order_id": order.printful_order_id
                    })
                
            except Exception as e:
                print(f"❌ Error syncing order {order.id}: {e}")
    
    async def _process_shipped_orders(self):
        """Check for shipped orders and send notifications"""
        # Get orders with Printful IDs but no tracking
        shipped_orders = self.session.query(Order).filter(
            Order.printful_order_id != None,
            Order.tracking_number == None
        ).all()
        
        for order in shipped_orders:
            try:
                # Get status from Printful
                status = await self.printful.get_order_status(order.printful_order_id)
                
                if status:
                    printful_status = status.get('status')
                    
                    # Update order status
                    order.printful_status = printful_status
                    
                    # Check if shipped
                    if printful_status in ['shipped', 'delivered']:
                        # Get tracking info
                        shipments = status.get('shipments', [])
                        if shipments:
                            order.tracking_number = shipments[0].get('tracking_number')
                            order.tracking_url = shipments[0].get('tracking_url')
                            order.shipped_at = datetime.utcnow()
                            order.fulfillment_status = 'fulfilled'
                        
                        self.session.commit()
                        
                        print(f"✅ Order #{order.order_number} shipped!")
                        
                        # Send tracking email
                        if config.fulfillment.auto_send_tracking:
                            await self.email.send_tracking_email(order)
                        
                        self._log_action("order_shipped", "success", {
                            "order_id": order.id,
                            "tracking_number": order.tracking_number
                        })
                    
                    elif printful_status == 'delivered':
                        order.delivered_at = datetime.utcnow()
                        self.session.commit()
                
            except Exception as e:
                print(f"❌ Error processing shipped order {order.id}: {e}")
    
    async def _update_analytics(self):
        """Update daily analytics"""
        try:
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Get or create today's analytics
            from ..database.models import AnalyticsDaily
            analytics = self.session.query(AnalyticsDaily).filter_by(date=today).first()
            
            if not analytics:
                analytics = AnalyticsDaily(date=today)
                self.session.add(analytics)
            
            # Calculate today's stats
            today_orders = self.session.query(Order).filter(
                Order.created_at >= today
            ).all()
            
            analytics.total_orders = len(today_orders)
            analytics.total_revenue = sum(o.total_price for o in today_orders)
            analytics.total_cost = sum(
                sum(i.product.cost_price * i.quantity for i in o.items if i.product)
                for o in today_orders
            )
            analytics.total_profit = analytics.total_revenue - analytics.total_cost
            
            self.session.commit()
            
        except Exception as e:
            print(f"❌ Error updating analytics: {e}")
    
    def _get_customer_name(self, order: Dict) -> str:
        """Extract customer name from order"""
        customer = order.get('customer', {})
        first_name = customer.get('first_name', '')
        last_name = customer.get('last_name', '')
        return f"{first_name} {last_name}".strip() or order.get('email', 'Customer')
    
    def _log_action(self, action: str, status: str, details: Dict):
        """Log agent action"""
        log = AgentLog(
            agent_name='fulfillment',
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
        print("🛑 Fulfillment Agent stopped")


# Standalone run function
async def run_fulfillment_agent():
    """Run fulfillment agent standalone"""
    from ..database.models import init_database
    
    engine = init_database(config.database_path)
    session = get_session(engine)
    
    agent = FulfillmentAgent(session)
    await agent.run()


if __name__ == "__main__":
    asyncio.run(run_fulfillment_agent())
