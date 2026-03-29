"""
PrintBot AI - Database Models
==============================
SQLAlchemy models for all data entities.
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import json

Base = declarative_base()


class Product(Base):
    """Store products synced with Shopify"""
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    shopify_id = Column(String(50), unique=True, index=True)
    title = Column(String(255))
    description = Column(Text)
    product_type = Column(String(50))
    tags = Column(JSON)
    
    # Pricing
    cost_price = Column(Float)
    selling_price = Column(Float)
    compare_at_price = Column(Float)
    margin_percent = Column(Float)
    
    # Design
    design_id = Column(Integer, ForeignKey('designs.id'))
    design_url = Column(String(500))
    mockup_urls = Column(JSON)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_approved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_synced = Column(DateTime)
    
    # Relationships
    design = relationship("Design", back_populates="products")
    variants = relationship("ProductVariant", back_populates="product")
    sales = relationship("Sale", back_populates="product")


class ProductVariant(Base):
    """Product variants (size, color)"""
    __tablename__ = 'product_variants'
    
    id = Column(Integer, primary_key=True)
    shopify_variant_id = Column(String(50), unique=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    
    size = Column(String(20))
    color = Column(String(50))
    sku = Column(String(100))
    
    cost_price = Column(Float)
    selling_price = Column(Float)
    inventory_quantity = Column(Integer, default=0)
    
    product = relationship("Product", back_populates="variants")


class Design(Base):
    """AI-generated designs"""
    __tablename__ = 'designs'
    
    id = Column(Integer, primary_key=True)
    
    # Design info
    prompt = Column(Text)
    negative_prompt = Column(Text)
    image_url = Column(String(500))
    local_path = Column(String(500))
    
    # Trend data
    trend_source = Column(String(100))
    trend_keywords = Column(JSON)
    trend_score = Column(Float)
    
    # AI generation
    ai_model = Column(String(50))
    generation_params = Column(JSON)
    
    # Approval workflow
    status = Column(String(20), default="pending")  # pending, approved, rejected
    ai_confidence = Column(Float)
    rejection_reason = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime)
    approved_by = Column(String(50))  # 'ai' or 'human'
    
    # Relationships
    products = relationship("Product", back_populates="design")


class Order(Base):
    """Customer orders"""
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    shopify_order_id = Column(String(50), unique=True)
    order_number = Column(String(50))
    
    # Customer
    customer_email = Column(String(255))
    customer_name = Column(String(255))
    shipping_address = Column(JSON)
    
    # Order details
    total_price = Column(Float)
    subtotal_price = Column(Float)
    tax_price = Column(Float)
    shipping_price = Column(Float)
    discount_price = Column(Float)
    
    # Status
    financial_status = Column(String(20))  # pending, paid, refunded
    fulfillment_status = Column(String(20))  # unfulfilled, partial, fulfilled
    
    # Printful integration
    printful_order_id = Column(String(50))
    printful_status = Column(String(50))
    tracking_number = Column(String(100))
    tracking_url = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    shipped_at = Column(DateTime)
    delivered_at = Column(DateTime)
    
    # Relationships
    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    """Individual items in an order"""
    __tablename__ = 'order_items'
    
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    variant_id = Column(Integer, ForeignKey('product_variants.id'))
    
    quantity = Column(Integer)
    price = Column(Float)
    
    order = relationship("Order", back_populates="items")


class Sale(Base):
    """Sales tracking for analytics"""
    __tablename__ = 'sales'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    order_id = Column(Integer, ForeignKey('orders.id'))
    
    quantity = Column(Integer)
    revenue = Column(Float)
    cost = Column(Float)
    profit = Column(Float)
    margin_percent = Column(Float)
    
    sale_date = Column(DateTime, default=datetime.utcnow)
    
    product = relationship("Product", back_populates="sales")


class SocialPost(Base):
    """Social media posts"""
    __tablename__ = 'social_posts'
    
    id = Column(Integer, primary_key=True)
    
    # Platform
    platform = Column(String(20))  # instagram, tiktok
    account_username = Column(String(100))
    
    # Content
    content_type = Column(String(20))  # image, video, carousel
    caption = Column(Text)
    hashtags = Column(JSON)
    media_urls = Column(JSON)
    
    # Product link
    product_id = Column(Integer, ForeignKey('products.id'))
    product_url = Column(String(500))
    
    # Engagement
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    views = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    
    # Status
    status = Column(String(20), default="scheduled")  # scheduled, posted, failed
    scheduled_at = Column(DateTime)
    posted_at = Column(DateTime)
    
    # External IDs
    external_post_id = Column(String(100))
    external_url = Column(String(500))


class CompetitorPrice(Base):
    """Competitor price tracking"""
    __tablename__ = 'competitor_prices'
    
    id = Column(Integer, primary_key=True)
    
    competitor_name = Column(String(100))
    competitor_url = Column(String(500))
    product_name = Column(String(255))
    
    price = Column(Float)
    currency = Column(String(3), default="USD")
    
    scraped_at = Column(DateTime, default=datetime.utcnow)


class TrendData(Base):
    """Trending keywords and topics"""
    __tablename__ = 'trend_data'
    
    id = Column(Integer, primary_key=True)
    
    keyword = Column(String(255))
    source = Column(String(100))
    category = Column(String(50))
    
    trend_score = Column(Float)
    search_volume = Column(Integer)
    growth_rate = Column(Float)
    
    collected_at = Column(DateTime, default=datetime.utcnow)
    
    # Whether we've created a design for this trend
    design_created = Column(Boolean, default=False)
    design_id = Column(Integer, ForeignKey('designs.id'))


class AgentLog(Base):
    """Agent activity logs"""
    __tablename__ = 'agent_logs'
    
    id = Column(Integer, primary_key=True)
    
    agent_name = Column(String(50))  # design, pricing, social, fulfillment
    action = Column(String(100))
    status = Column(String(20))  # success, error, warning
    
    details = Column(JSON)
    error_message = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class SystemEvent(Base):
    """System-wide events"""
    __tablename__ = 'system_events'
    
    id = Column(Integer, primary_key=True)
    
    event_type = Column(String(50))  # backup, error, config_change, etc.
    severity = Column(String(20))  # info, warning, error, critical
    
    message = Column(Text)
    details = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class AnalyticsDaily(Base):
    """Daily analytics summary"""
    __tablename__ = 'analytics_daily'
    
    id = Column(Integer, primary_key=True)
    date = Column(DateTime, unique=True)
    
    # Sales
    total_orders = Column(Integer, default=0)
    total_revenue = Column(Float, default=0)
    total_cost = Column(Float, default=0)
    total_profit = Column(Float, default=0)
    
    # Products
    products_created = Column(Integer, default=0)
    products_sold = Column(Integer, default=0)
    
    # Social
    posts_created = Column(Integer, default=0)
    total_likes = Column(Integer, default=0)
    total_comments = Column(Integer, default=0)
    total_clicks = Column(Integer, default=0)
    
    # Engagement rate
    engagement_rate = Column(Float, default=0)


# Database initialization
def init_database(db_path: str):
    """Initialize the database with all tables"""
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)
    return engine


def get_session(engine):
    """Get a database session"""
    Session = sessionmaker(bind=engine)
    return Session()
