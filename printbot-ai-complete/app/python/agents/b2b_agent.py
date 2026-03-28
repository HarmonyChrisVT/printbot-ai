"""
B2B Agent - Corporate client management and bulk orders
"""

import os
import random
from typing import Dict, Any, List, Optional
from datetime import datetime

from openai import AsyncOpenAI
from python.utils.logger import get_logger
from database.models import get_db_session, B2BClient

logger = get_logger(__name__)

class B2BAgent:
    """AI agent that manages B2B corporate clients"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.industries = [
            'tech', 'healthcare', 'education', 'retail', 'hospitality',
            'fitness', 'nonprofit', 'events', 'real_estate', 'finance'
        ]
    
    async def configure(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Configure the B2B agent"""
        return {'status': 'configured', 'industries': self.industries}
    
    async def find_leads(self, industry: Optional[str] = None, location: Optional[str] = None) -> List[Dict[str, Any]]:
        """Find potential B2B leads"""
        logger.info(f"Finding B2B leads for industry: {industry}")
        
        # In production, this would search business databases
        # For now, return simulated leads
        
        target_industry = industry or random.choice(self.industries)
        
        leads = []
        for i in range(random.randint(5, 15)):
            leads.append({
                'company_name': f"{target_industry.title()} Corp {i+1}",
                'industry': target_industry,
                'size': random.choice(['small', 'medium', 'large', 'enterprise']),
                'location': location or random.choice(['USA', 'Canada', 'UK', 'Australia']),
                'potential_order_value': random.randint(1000, 50000),
                'contact_email': f"contact@{target_industry}corp{i+1}.com",
                'source': random.choice(['linkedin', 'trade_show', 'referral', 'website']),
                'score': random.randint(60, 95)
            })
        
        # Sort by score
        leads.sort(key=lambda x: x['score'], reverse=True)
        
        return leads
    
    async def outreach(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """Send personalized outreach to a lead"""
        logger.info(f"Sending outreach to: {lead['company_name']}")
        
        # Generate personalized email
        email = await self._generate_outreach_email(lead)
        
        # In production, this would send actual email
        # For now, simulate sending
        
        return {
            'success': True,
            'company': lead['company_name'],
            'email_subject': email['subject'],
            'email_body': email['body'],
            'sent_at': datetime.now().isoformat()
        }
    
    async def _generate_outreach_email(self, lead: Dict[str, Any]) -> Dict[str, str]:
        """Generate personalized outreach email"""
        prompt = f"""Write a personalized B2B outreach email to:
        
        Company: {lead['company_name']}
        Industry: {lead['industry']}
        Size: {lead['size']}
        
        We offer custom print-on-demand merchandise for businesses.
        
        Write:
        1. A compelling subject line
        2. A personalized email body (150-200 words)
        3. A clear call-to-action
        
        Format as JSON with 'subject' and 'body' keys."""
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a B2B sales expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            import json
            content = response.choices[0].message.content
            try:
                return json.loads(content)
            except:
                return {
                    'subject': f"Custom Merchandise for {lead['company_name']}",
                    'body': f"Hi there,\n\nI noticed {lead['company_name']} is making waves in the {lead['industry']} industry. We'd love to help you create custom merchandise for your team or events.\n\nBest regards"
                }
        except Exception as e:
            logger.error(f"Email generation error: {e}")
            return {
                'subject': f"Custom Merchandise for {lead['company_name']}",
                'body': f"Hi there,\n\nI noticed {lead['company_name']} is making waves in the {lead['industry']} industry. We'd love to help you create custom merchandise for your team or events.\n\nBest regards"
            }
    
    async def create_proposal(self, client_id: int, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Create a custom proposal for a B2B client"""
        session = get_db_session()
        try:
            client = session.query(B2BClient).filter_by(id=client_id).first()
            if not client:
                return {'error': 'Client not found'}
            
            # Generate proposal
            proposal = await self._generate_proposal(client, requirements)
            
            return {
                'success': True,
                'client': client.company_name,
                'proposal': proposal,
                'created_at': datetime.now().isoformat()
            }
        finally:
            session.close()
    
    async def _generate_proposal(self, client: B2BClient, requirements: Dict) -> Dict[str, Any]:
        """Generate proposal content"""
        quantity = requirements.get('quantity', 100)
        product_types = requirements.get('product_types', ['t-shirts'])
        
        # Calculate pricing
        base_price_per_item = 15.00
        volume_discount = self._calculate_volume_discount(quantity)
        final_price = base_price_per_item * (1 - volume_discount)
        total = final_price * quantity
        
        return {
            'title': f"Custom Merchandise Proposal for {client.company_name}",
            'products': product_types,
            'quantity': quantity,
            'price_per_item': round(final_price, 2),
            'volume_discount': f"{int(volume_discount * 100)}%",
            'total_value': round(total, 2),
            'delivery_time': '2-3 weeks',
            'includes': [
                'Custom design work',
                'Sample approval',
                'Bulk production',
                'Free shipping',
                'Dedicated account manager'
            ],
            'valid_until': (datetime.now() + timedelta(days=30)).isoformat()
        }
    
    def _calculate_volume_discount(self, quantity: int) -> float:
        """Calculate volume discount percentage"""
        if quantity >= 1000:
            return 0.35
        elif quantity >= 500:
            return 0.25
        elif quantity >= 250:
            return 0.15
        elif quantity >= 100:
            return 0.10
        else:
            return 0.05
    
    async def add_client(self, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new B2B client"""
        session = get_db_session()
        try:
            client = B2BClient(
                company_name=client_data['company_name'],
                contact_name=client_data.get('contact_name'),
                contact_email=client_data.get('contact_email'),
                contact_phone=client_data.get('contact_phone'),
                industry=client_data.get('industry'),
                order_volume=client_data.get('order_volume', 'small'),
                status='lead',
                notes=client_data.get('notes', '')
            )
            
            session.add(client)
            session.commit()
            
            return {
                'success': True,
                'client_id': client.id,
                'company': client.company_name
            }
        finally:
            session.close()
    
    async def get_clients(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all B2B clients"""
        session = get_db_session()
        try:
            query = session.query(B2BClient)
            if status:
                query = query.filter_by(status=status)
            
            clients = query.order_by(B2BClient.created_at.desc()).all()
            return [c.to_dict() for c in clients]
        finally:
            session.close()
