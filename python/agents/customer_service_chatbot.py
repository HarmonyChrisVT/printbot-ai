"""
PrintBot AI - Customer Service Chatbot Agent
=============================================
Handles customer inquiries 24/7
Answers common questions, processes returns/refunds
Integrates with help desk systems
"""
import asyncio
import openai
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
import re

from ..config.settings import config
from ..database.models import Order, Product, AgentLog, get_session


@dataclass
class ChatMessage:
    """Chat message"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    intent: str = None  # Detected intent


@dataclass
class ChatSession:
    """Customer chat session"""
    session_id: str
    customer_email: str
    messages: List[ChatMessage]
    order_id: str = None
    context: Dict = None
    escalated: bool = False


class IntentClassifier:
    """Classify customer message intents"""
    
    def __init__(self):
        self.intent_patterns = {
            'order_status': [
                r'where is my order',
                r'order status',
                r'tracking',
                r'when will.*arrive',
                r'has my order shipped'
            ],
            'shipping_info': [
                r'shipping time',
                r'how long.*shipping',
                r'delivery time',
                r'shipping cost'
            ],
            'return_refund': [
                r'return',
                r'refund',
                r'exchange',
                r'wrong size',
                r'defective',
                r'not what.*expected'
            ],
            'product_question': [
                r'size',
                r'fit',
                r'material',
                r'quality',
                r'color',
                r'design'
            ],
            'discount_promo': [
                r'discount',
                r'coupon',
                r'promo code',
                r'sale',
                r'offer'
            ],
            'cancel_order': [
                r'cancel',
                r'stop order',
                r'don\'t want'
            ],
            'contact_human': [
                r'talk to human',
                r'speak to someone',
                r'customer service',
                r'representative',
                r'agent'
            ]
        }
    
    def classify(self, message: str) -> Tuple[str, float]:
        """Classify message intent"""
        message_lower = message.lower()
        
        scores = {}
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    score += 1
            scores[intent] = score
        
        # Get best match
        best_intent = max(scores, key=scores.get)
        best_score = scores[best_intent]
        
        # Calculate confidence
        total = sum(scores.values())
        confidence = best_score / total if total > 0 else 0
        
        return best_intent, confidence


class ResponseGenerator:
    """Generate chatbot responses"""
    
    def __init__(self, db_session):
        self.session = db_session
        self.client = openai.OpenAI(api_key=config.openai.api_key)
        
        # Template responses
        self.templates = {
            'order_status': """I'd be happy to check on your order! Could you please provide your order number? It should look like #1234.""",
            
            'shipping_info': """Our shipping times are:
• Standard: 5-10 business days
• Express: 3-5 business days

Shipping costs are calculated at checkout based on your location.""",
            
            'return_refund': """I can help with returns! Our policy:
• Returns accepted within 30 days
• Items must be unworn with tags
• Refunds processed within 5-7 days

Would you like to start a return?""",
            
            'product_question': """I'd be happy to help with product questions! Could you tell me which specific product you're asking about?""",
            
            'discount_promo': """Current offers:
• New customers: 10% off with code WELCOME10
• Free shipping on orders over $50

Check our homepage for current sales!""",
            
            'cancel_order': """I can help cancel your order if it hasn't shipped yet. Please provide your order number and I'll check the status.""",
            
            'contact_human': """I'll connect you with a human agent right away. Please hold on while I transfer you...""",
            
            'greeting': """Hello! 👋 Welcome to our store! I'm here to help with:
• Order tracking
• Product questions
• Returns & refunds
• General inquiries

What can I help you with today?""",
            
            'fallback': """I'm not sure I understand. Could you rephrase that? Or I can connect you with a human agent if you'd prefer."""
        }
    
    def get_template_response(self, intent: str) -> str:
        """Get template response for intent"""
        return self.templates.get(intent, self.templates['fallback'])
    
    async def generate_ai_response(
        self,
        session: ChatSession,
        message: str
    ) -> str:
        """Generate AI-powered response"""
        
        # Build conversation context
        conversation = ""
        for msg in session.messages[-5:]:  # Last 5 messages
            role = "Customer" if msg.role == 'user' else "Assistant"
            conversation += f"{role}: {msg.content}\n"
        
        system_prompt = """You are a helpful customer service chatbot for a print-on-demand store.
Be friendly, concise, and helpful. Keep responses under 150 words.
If you don't know something, offer to connect to a human agent."""
        
        user_prompt = f"""Conversation history:
{conversation}

Customer's latest message: "{message}"

Respond naturally as a helpful customer service agent."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # Use cheaper model for chat
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ AI response error: {e}")
            return self.templates['fallback']
    
    async def get_order_status_response(self, order_number: str) -> str:
        """Get order status for customer"""
        order = self.session.query(Order).filter(
            Order.order_number.ilike(f"%{order_number}%")
        ).first()
        
        if not order:
            return "I couldn't find an order with that number. Please double-check and try again."
        
        status_messages = {
            'pending': f"Order {order.order_number} is being processed. We'll send tracking info soon!",
            'confirmed': f"Order {order.order_number} is confirmed and being prepared for printing.",
            'in_production': f"Order {order.order_number} is currently being printed!",
            'shipped': f"Order {order.order_number} has shipped! Tracking: {order.tracking_number}",
            'delivered': f"Order {order.order_number} was delivered. Hope you love it!"
        }
        
        return status_messages.get(
            order.tracking_status,
            f"Order {order.order_number} status: {order.tracking_status}"
        )


class CustomerServiceChatbot:
    """
    Customer Service Chatbot Agent
    Handles customer inquiries 24/7
    """
    
    def __init__(self, db_session):
        self.session = db_session
        self.intent_classifier = IntentClassifier()
        self.response_generator = ResponseGenerator(db_session)
        self.active_sessions: Dict[str, ChatSession] = {}
        self.running = False
    
    async def run(self):
        """Main agent loop - monitors for new messages"""
        self.running = True
        print("💬 Customer Service Chatbot started")
        
        while self.running:
            try:
                # Check for new messages (would integrate with chat platform)
                await self._check_new_messages()
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                self._log_error(f"Chatbot error: {e}")
                await asyncio.sleep(30)
    
    async def _check_new_messages(self):
        """Check for new customer messages"""
        # Would integrate with actual chat platform (Intercom, Zendesk, etc.)
        pass
    
    async def handle_message(
        self,
        session_id: str,
        customer_email: str,
        message: str
    ) -> str:
        """Handle incoming customer message"""
        
        # Get or create session
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = ChatSession(
                session_id=session_id,
                customer_email=customer_email,
                messages=[]
            )
        
        session = self.active_sessions[session_id]
        
        # Classify intent
        intent, confidence = self.intent_classifier.classify(message)
        
        # Store message
        chat_msg = ChatMessage(
            role='user',
            content=message,
            timestamp=datetime.utcnow(),
            intent=intent
        )
        session.messages.append(chat_msg)
        
        # Generate response
        response = await self._generate_response(session, message, intent, confidence)
        
        # Store response
        session.messages.append(ChatMessage(
            role='assistant',
            content=response,
            timestamp=datetime.utcnow()
        ))
        
        # Check for escalation
        if intent == 'contact_human' or confidence < 0.3:
            session.escalated = True
            response += "\n\n[Transferring to human agent...]"
        
        return response
    
    async def _generate_response(
        self,
        session: ChatSession,
        message: str,
        intent: str,
        confidence: float
    ) -> str:
        """Generate appropriate response"""
        
        # Use template for common intents
        if confidence > 0.7 and intent in self.response_generator.templates:
            return self.response_generator.get_template_response(intent)
        
        # Check for order number in message
        order_match = re.search(r'#?(\d{4,})', message)
        if order_match and intent == 'order_status':
            return await self.response_generator.get_order_status_response(order_match.group(1))
        
        # Use AI for complex queries
        return await self.response_generator.generate_ai_response(session, message)
    
    def get_session_summary(self, session_id: str) -> Dict:
        """Get summary of chat session"""
        session = self.active_sessions.get(session_id)
        if not session:
            return None
        
        return {
            'session_id': session_id,
            'customer_email': session.customer_email,
            'message_count': len(session.messages),
            'escalated': session.escalated,
            'duration_minutes': (
                (datetime.utcnow() - session.messages[0].timestamp).total_seconds() / 60
                if session.messages else 0
            )
        }
    
    def _log_action(self, action: str, status: str, details: Dict):
        """Log agent action"""
        log = AgentLog(
            agent_name='customer_service_chatbot',
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
        print("🛑 Customer Service Chatbot stopped")


# Standalone run
async def run_chatbot_agent():
    """Run chatbot agent standalone"""
    from ..database.models import init_database
    from ..config.settings import config
    
    engine = init_database(config.database_path)
    session = get_session(engine)
    
    agent = CustomerServiceChatbot(session)
    
    # Test conversation
    session_id = "test_session"
    
    responses = []
    responses.append(await agent.handle_message(session_id, "test@example.com", "Hi there!"))
    responses.append(await agent.handle_message(session_id, "test@example.com", "Where is my order #1234?"))
    responses.append(await agent.handle_message(session_id, "test@example.com", "I want to return something"))
    
    for r in responses:
        print(f"Bot: {r}\n")
    
    await agent.run()


if __name__ == "__main__":
    asyncio.run(run_chatbot_agent())
