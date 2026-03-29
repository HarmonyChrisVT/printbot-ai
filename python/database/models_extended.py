"""
PrintBot AI - Extended Database Models
=======================================
Additional models for B2B, engagement, and analytics
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


# Email Capture & Leads
class EmailLead(Base):
    """Captured email leads"""
    __tablename__ = 'email_leads'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True)
    source = Column(String(100))  # popup, checkout, b2b_form, etc.
    capture_trigger = Column(String(50))  # exit_intent, scroll, time, etc.
    
    # Metadata
    page_url = Column(String(500))
    referrer = Column(String(500))
    user_agent = Column(String(500))
    ip_address = Column(String(50))
    
    # Engagement tracking
    engagement_score = Column(Integer, default=0)
    emails_sent = Column(Integer, default=0)
    emails_opened = Column(Integer, default=0)
    emails_clicked = Column(Integer, default=0)
    
    # Status
    is_subscribed = Column(Boolean, default=True)
    is_customer = Column(Boolean, default=False)
    
    # Timestamps
    captured_at = Column(DateTime, default=datetime.utcnow)
    last_engagement = Column(DateTime)
    converted_at = Column(DateTime)


# Product Reviews
class ProductReview(Base):
    """Customer product reviews"""
    __tablename__ = 'product_reviews'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    order_id = Column(Integer, ForeignKey('orders.id'))
    
    # Review content
    customer_name = Column(String(255))
    rating = Column(Integer)  # 1-5
    review_text = Column(Text)
    photos = Column(JSON)  # List of photo URLs
    
    # Status
    verified_purchase = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=True)
    helpful_count = Column(Integer, default=0)
    
    # Response
    seller_response = Column(Text)
    responded_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)


# Abandoned Carts
class AbandonedCart(Base):
    """Abandoned shopping carts"""
    __tablename__ = 'abandoned_carts'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), index=True)
    session_id = Column(String(255))
    
    # Cart items
    items = Column(JSON)  # List of {product_id, variant_id, quantity, price, name}
    total_value = Column(Float)
    currency = Column(String(3), default='USD')
    
    # Recovery
    emails_sent = Column(Integer, default=0)
    recovered = Column(Boolean, default=False)
    recovered_at = Column(DateTime)
    recovered_order_id = Column(Integer, ForeignKey('orders.id'))
    
    # Timestamps
    abandoned_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime)


# Corporate Clients (B2B)
class CorporateClient(Base):
    """B2B corporate clients"""
    __tablename__ = 'corporate_clients'
    
    id = Column(Integer, primary_key=True)
    
    # Company info
    company_name = Column(String(255))
    contact_name = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    tax_id = Column(String(50))
    
    # Address
    billing_address = Column(JSON)
    shipping_addresses = Column(JSON)  # Multiple shipping locations
    
    # Account settings
    discount_tier = Column(String(20), default='bronze')  # bronze, silver, gold, platinum
    payment_terms = Column(String(20), default='net30')  # net30, net60, etc.
    credit_limit = Column(Float, default=0)
    current_balance = Column(Float, default=0)
    
    # Status
    is_approved = Column(Boolean, default=False)
    approved_at = Column(DateTime)
    approved_by = Column(String(100))
    
    # Notes
    internal_notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Bulk Quotes (B2B)
class BulkQuote(Base):
    """B2B bulk order quotes"""
    __tablename__ = 'bulk_quotes'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('corporate_clients.id'))
    
    # Quote details
    items = Column(JSON)  # List of {product_id, quantity, unit_price}
    quantity = Column(Integer)
    unit_price = Column(Float)
    discount_percent = Column(Float)
    total_price = Column(Float)
    
    # Status
    status = Column(String(20), default='pending')  # pending, approved, rejected, expired
    
    # Validity
    valid_until = Column(DateTime)
    
    # Response
    rejection_reason = Column(Text)
    approved_by = Column(String(100))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Extended Order Model additions
class OrderExtended:
    """Additional fields for Order model"""
    # These would be added to the existing Order model
    tracking_status = Column(String(50), default='pending')
    estimated_delivery = Column(DateTime)
    review_requested = Column(Boolean, default=False)
    fulfillment_provider = Column(String(50))  # printful, printify, gelato, gooten


# Profit Analytics
class ProfitAnalytics(Base):
    """Detailed profit analytics"""
    __tablename__ = 'profit_analytics'
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, index=True)
    
    # Revenue breakdown
    total_revenue = Column(Float, default=0)
    product_revenue = Column(Float, default=0)
    shipping_revenue = Column(Float, default=0)
    tax_collected = Column(Float, default=0)
    
    # Cost breakdown
    total_cost = Column(Float, default=0)
    product_cost = Column(Float, default=0)
    shipping_cost = Column(Float, default=0)
    payment_fees = Column(Float, default=0)
    platform_fees = Column(Float, default=0)
    
    # Profit
    gross_profit = Column(Float, default=0)
    net_profit = Column(Float, default=0)
    profit_margin = Column(Float, default=0)
    
    # Metrics
    total_orders = Column(Integer, default=0)
    total_units = Column(Integer, default=0)
    avg_order_value = Column(Float, default=0)
    avg_unit_price = Column(Float, default=0)
    
    # Channel breakdown
    direct_traffic_revenue = Column(Float, default=0)
    social_traffic_revenue = Column(Float, default=0)
    organic_traffic_revenue = Column(Float, default=0)
    paid_traffic_revenue = Column(Float, default=0)


# Social Proof Events
class SocialProofEvent(Base):
    """Social proof events for display"""
    __tablename__ = 'social_proof_events'
    
    id = Column(Integer, primary_key=True)
    event_type = Column(String(50))  # purchase, review, cart_add
    product_id = Column(Integer, ForeignKey('products.id'))
    
    # Anonymized data
    location = Column(String(100))
    time_ago = Column(String(50))
    
    # For reviews
    rating = Column(Integer)
    review_snippet = Column(String(200))
    
    # Display settings
    should_display = Column(Boolean, default=True)
    display_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)


# Manual Override Log
class ManualOverride(Base):
    """Log of manual overrides"""
    __tablename__ = 'manual_overrides'
    
    id = Column(Integer, primary_key=True)
    
    # What was overridden
    agent_name = Column(String(50))
    action_type = Column(String(50))  # approve_design, update_price, cancel_order, etc.
    target_id = Column(String(100))  # ID of the item that was overridden
    
    # Override details
    original_value = Column(JSON)
    new_value = Column(JSON)
    reason = Column(Text)
    
    # Who did it
    overridden_by = Column(String(100))
    overridden_at = Column(DateTime, default=datetime.utcnow)
    
    # Was it reverted
    reverted = Column(Boolean, default=False)
    reverted_at = Column(DateTime)
    reverted_by = Column(String(100))


# Fulfillment Provider Status
class FulfillmentProviderStatus(Base):
    """Status tracking for fulfillment providers"""
    __tablename__ = 'fulfillment_provider_status'
    
    id = Column(Integer, primary_key=True)
    provider_name = Column(String(50))  # printful, printify, gelato, gooten
    
    # Health
    is_healthy = Column(Boolean, default=True)
    last_health_check = Column(DateTime)
    failure_count = Column(Integer, default=0)
    
    # Performance
    avg_response_time = Column(Float, default=0)
    total_orders = Column(Integer, default=0)
    successful_orders = Column(Integer, default=0)
    failed_orders = Column(Integer, default=0)
    
    # Current status
    is_active = Column(Boolean, default=True)
    is_primary = Column(Boolean, default=False)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Social Account Status
class SocialAccountStatus(Base):
    """Status tracking for social media accounts"""
    __tablename__ = 'social_account_status'
    
    id = Column(Integer, primary_key=True)
    platform = Column(String(20))  # instagram, tiktok
    username = Column(String(100))
    
    # Status
    is_active = Column(Boolean, default=True)
    is_primary = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)
    
    # Usage
    daily_actions = Column(Integer, default=0)
    total_posts = Column(Integer, default=0)
    total_followers = Column(Integer, default=0)
    
    # Health
    failure_count = Column(Integer, default=0)
    last_post = Column(DateTime)
    last_error = Column(Text)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
