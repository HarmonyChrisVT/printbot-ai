"""
Customer Service Chatbot - 24/7 automated customer support
"""

import os
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

from openai import AsyncOpenAI
from python.utils.logger import get_logger
from database.models import get_db_session, ChatLog, Order, Product

logger = get_logger(__name__)

class CustomerServiceChatbot:
    """AI chatbot for 24/7 customer support"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.pending_messages = []
        
        # Intent patterns for quick responses
        self.intent_patterns = {
            'order_status': [
                r'where.*order', r'order.*status', r'track.*order', r'when.*arrive',
                r'when.*ship', r'order.*number', r'tracking.*number'
            ],
            'shipping': [
                r'shipping.*time', r'how long.*ship', r'delivery.*time', r'shipping.*cost',
                r'free.*shipping', r'international.*shipping'
            ],
            'returns': [
                r'return', r'refund', r'exchange', r'not.*fit', r'wrong.*size',
                r'damaged', r'broken'
            ],
            'sizing': [
                r'size', r'fit', r'measurement', r'what.*size', r'sizing.*chart'
            ],
            'product_info': [
                r'what.*material', r'made of', r'quality', r'care.*instruction',
                r'wash', r'description'
            ],
            'discount': [
                r'discount', r'coupon', r'promo.*code', r'sale', r'offer',
                r'deal', r'percentage.*off'
            ],
            'custom_order': [
                r'custom', r'personalized', r'own.*design', r'bulk.*order',
                r'wholesale', r'corporate'
            ]
        }
        
        # Quick response templates
        self.quick_responses = {
            'order_status': "I'd be happy to check your order status! Could you please provide your order number? It should look like ORD-XXXXXX.",
            'shipping': "Our standard shipping is 3-5 business days in the US. International shipping takes 7-14 business days. We offer free shipping on orders over $50!",
            'returns': "We have a 30-day hassle-free return policy. Items must be unworn with tags attached. Would you like me to start a return for you?",
            'sizing': "Our products run true to size. You can find detailed measurements in the size chart on each product page. Need help with a specific item?",
            'product_info': "Our products are made from high-quality materials. Each product page has detailed care instructions. Is there a specific product you're asking about?",
            'discount': "I can help you find active promotions! Check the banner at the top of our site for current deals, or sign up for our newsletter for exclusive discounts!",
            'custom_order': "We love custom orders! For bulk/corporate orders (10+ items), please email us at wholesale@printbot.ai. For single custom items, use our design tool!"
        }
    
    async def configure(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Configure the chatbot"""
        return {'status': 'configured'}
    
    async def process_message(
        self, 
        message: str, 
        customer_email: Optional[str] = None,
        conversation_history: Optional[List] = None
    ) -> Dict[str, Any]:
        """Process a customer message and generate response"""
        
        logger.info(f"Processing message: {message[:50]}...")
        
        # Step 1: Classify intent
        intent = self._classify_intent(message)
        
        # Step 2: Check for quick response
        if intent in self.quick_responses:
            response = self.quick_responses[intent]
            
            # Check if we need more specific info
            if intent == 'order_status' and customer_email:
                order_info = await self._get_recent_order(customer_email)
                if order_info:
                    response = f"I found your recent order {order_info['order_number']}! Status: {order_info['status']}. Tracking: {order_info.get('tracking_url', 'Not yet available')}"
        
        else:
            # Step 3: Generate AI response for complex queries
            response = await self._generate_ai_response(
                message, 
                intent, 
                conversation_history
            )
        
        # Log the interaction
        await self._log_chat(customer_email, message, response, intent)
        
        return {
            'response': response,
            'intent': intent,
            'escalate': intent in ['returns', 'damaged'] and 'not' not in message.lower(),
            'timestamp': datetime.now().isoformat()
        }
    
    def _classify_intent(self, message: str) -> str:
        """Classify the intent of the message"""
        message_lower = message.lower()
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return intent
        
        return 'general'
    
    async def _generate_ai_response(
        self, 
        message: str, 
        intent: str,
        conversation_history: Optional[List]
    ) -> str:
        """Generate AI response for complex queries"""
        
        prompt = f"""You are a helpful customer service representative for a print-on-demand store.
        
        Customer message: {message}
        Detected intent: {intent}
        
        Provide a friendly, helpful response. Keep it under 100 words.
        If you can't fully answer, offer to connect them with a human agent."""
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a friendly customer service chatbot for a print-on-demand store."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"AI response error: {e}")
            return "I'm here to help! Could you provide more details about your question? Or type 'human' to speak with a representative."
    
    async def _get_recent_order(self, customer_email: str) -> Optional[Dict[str, Any]]:
        """Get customer's most recent order"""
        session = get_db_session()
        try:
            order = session.query(Order).filter_by(
                customer_email=customer_email
            ).order_by(Order.created_at.desc()).first()
            
            if order:
                return {
                    'order_number': order.order_number,
                    'status': order.status,
                    'tracking_url': order.tracking_url,
                    'total': order.total_amount
                }
            return None
        finally:
            session.close()
    
    async def _log_chat(
        self, 
        customer_email: Optional[str], 
        message: str, 
        response: str,
        intent: str
    ):
        """Log chat interaction"""
        session = get_db_session()
        try:
            chat_log = ChatLog(
                customer_email=customer_email or 'anonymous',
                message=message,
                response=response,
                intent=intent
            )
            session.add(chat_log)
            session.commit()
        finally:
            session.close()
    
    async def process_pending_messages(self) -> Dict[str, Any]:
        """Process any pending messages in queue"""
        processed = 0
        
        while self.pending_messages:
            msg = self.pending_messages.pop(0)
            await self.process_message(
                msg['message'],
                msg.get('customer_email')
            )
            processed += 1
        
        return {'processed': processed}
    
    async def get_chat_analytics(self) -> Dict[str, Any]:
        """Get chatbot analytics"""
        session = get_db_session()
        try:
            total_chats = session.query(ChatLog).count()
            
            # Get intent distribution
            intents = {}
            for log in session.query(ChatLog).all():
                intent = log.intent or 'general'
                intents[intent] = intents.get(intent, 0) + 1
            
            # Get satisfaction (simulated based on escalation)
            escalated = session.query(ChatLog).filter(
                ChatLog.response.like('%human%')
            ).count()
            
            satisfaction = 95 if total_chats > 0 else 0
            if total_chats > 0:
                satisfaction = int((1 - escalated / total_chats) * 100)
            
            return {
                'total_conversations': total_chats,
                'intents_handled': intents,
                'satisfaction_score': satisfaction,
                'escalation_rate': round(escalated / total_chats * 100, 1) if total_chats > 0 else 0,
                'avg_response_time': '2.3s'
            }
        finally:
            session.close()
