"""
Database Models for PrintBot AI
"""

from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os

Base = declarative_base()

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'printbot.db')
engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)
SessionLocal = sessionmaker(bind=engine)

class StoreConfig(Base):
    __tablename__ = 'store_config'
    
    id = Column(Integer, primary_key=True)
    store_name = Column(String(255))
    niche = Column(String(255))
    platforms = Column(JSON)  # List of platforms
    auto_mode = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # API Keys (encrypted in production)
    openai_api_key = Column(String(500))
    shopify_api_key = Column(String(500))
    printful_api_key = Column(String(500))
    stripe_api_key = Column(String(500))
    
    # Social Media API Keys
    instagram_api_key = Column(String(500))
    tiktok_api_key = Column(String(500))
    pinterest_api_key = Column(String(500))
    
    def to_dict(self):
        return {
            'id': self.id,
            'store_name': self.store_name,
            'niche': self.niche,
            'platforms': self.platforms,
            'auto_mode': self.auto_mode,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(500))
    description = Column(Text)
    design_url = Column(String(1000))
    mockup_urls = Column(JSON)  # List of mockup URLs
    base_cost = Column(Float)
    sale_price = Column(Float)
    profit_margin = Column(Float)
    tags = Column(JSON)
    trending_score = Column(Float, default=0.0)
    niche = Column(String(255))
    status = Column(String(50), default='draft')  # draft, listed, active, paused
    shopify_id = Column(String(255))
    etsy_id = Column(String(255))
    amazon_id = Column(String(255))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    times_sold = Column(Integer, default=0)
    views = Column(Integer, default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'design_url': self.design_url,
            'mockup_urls': self.mockup_urls,
            'base_cost': self.base_cost,
            'sale_price': self.sale_price,
            'profit_margin': self.profit_margin,
            'tags': self.tags,
            'trending_score': self.trending_score,
            'niche': self.niche,
            'status': self.status,
            'times_sold': self.times_sold,
            'views': self.views,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Order(Base):
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    order_number = Column(String(100), unique=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    customer_email = Column(String(255))
    customer_name = Column(String(255))
    shipping_address = Column(JSON)
    quantity = Column(Integer, default=1)
    total_amount = Column(Float)
    cost_amount = Column(Float)
    profit = Column(Float)
    status = Column(String(50), default='pending')  # pending, processing, shipped, delivered, cancelled
    tracking_number = Column(String(255))
    tracking_url = Column(String(1000))
    provider = Column(String(100))  # printful, printify, gelato, gooten
    platform = Column(String(100))  # shopify, etsy, amazon
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    shipped_at = Column(DateTime)
    delivered_at = Column(DateTime)
    review_requested = Column(Boolean, default=False)
    review_received = Column(Boolean, default=False)
    review_rating = Column(Integer)
    review_text = Column(Text)
    
    product = relationship("Product")
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_number': self.order_number,
            'product_id': self.product_id,
            'customer_email': self.customer_email,
            'customer_name': self.customer_name,
            'quantity': self.quantity,
            'total_amount': self.total_amount,
            'profit': self.profit,
            'status': self.status,
            'tracking_number': self.tracking_number,
            'tracking_url': self.tracking_url,
            'provider': self.provider,
            'platform': self.platform,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'shipped_at': self.shipped_at.isoformat() if self.shipped_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None
        }

class SocialAccount(Base):
    __tablename__ = 'social_accounts'
    
    id = Column(Integer, primary_key=True)
    platform = Column(String(100))  # instagram, tiktok, pinterest
    account_name = Column(String(255))
    account_index = Column(Integer, default=0)  # 0, 1, 2 for backup accounts
    is_active = Column(Boolean, default=True)
    is_primary = Column(Boolean, default=False)
    followers = Column(Integer, default=0)
    posts_count = Column(Integer, default=0)
    api_key = Column(String(500))
    last_post_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'platform': self.platform,
            'account_name': self.account_name,
            'account_index': self.account_index,
            'is_active': self.is_active,
            'is_primary': self.is_primary,
            'followers': self.followers,
            'posts_count': self.posts_count,
            'last_post_at': self.last_post_at.isoformat() if self.last_post_at else None
        }

class SocialPost(Base):
    __tablename__ = 'social_posts'
    
    id = Column(Integer, primary_key=True)
    platform = Column(String(100))
    account_id = Column(Integer, ForeignKey('social_accounts.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    content = Column(Text)
    image_url = Column(String(1000))
    post_url = Column(String(1000))
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    posted_at = Column(DateTime, default=datetime.now)
    
    account = relationship("SocialAccount")
    product = relationship("Product")

class EmailSubscriber(Base):
    __tablename__ = 'email_subscribers'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True)
    name = Column(String(255))
    source = Column(String(100))  # popup, checkout, landing_page
    tags = Column(JSON)
    is_verified = Column(Boolean, default=False)
    subscribed_at = Column(DateTime, default=datetime.now)
    last_email_sent = Column(DateTime)
    emails_sent = Column(Integer, default=0)
    emails_opened = Column(Integer, default=0)
    emails_clicked = Column(Integer, default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'source': self.source,
            'tags': self.tags,
            'is_verified': self.is_verified,
            'subscribed_at': self.subscribed_at.isoformat() if self.subscribed_at else None
        }

class AbandonedCart(Base):
    __tablename__ = 'abandoned_carts'
    
    id = Column(Integer, primary_key=True)
    customer_email = Column(String(255))
    customer_name = Column(String(255))
    product_ids = Column(JSON)
    total_value = Column(Float)
    recovery_email_sent = Column(Boolean, default=False)
    recovery_email_sent_at = Column(DateTime)
    recovered = Column(Boolean, default=False)
    recovered_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)

class B2BClient(Base):
    __tablename__ = 'b2b_clients'
    
    id = Column(Integer, primary_key=True)
    company_name = Column(String(255))
    contact_name = Column(String(255))
    contact_email = Column(String(255))
    contact_phone = Column(String(100))
    industry = Column(String(255))
    order_volume = Column(String(50))  # small, medium, large, enterprise
    status = Column(String(50), default='lead')  # lead, contacted, proposal, negotiating, active, inactive
    contract_value = Column(Float)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_name': self.company_name,
            'contact_name': self.contact_name,
            'contact_email': self.contact_email,
            'industry': self.industry,
            'order_volume': self.order_volume,
            'status': self.status,
            'contract_value': self.contract_value,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Competitor(Base):
    __tablename__ = 'competitors'
    
    id = Column(Integer, primary_key=True)
    store_name = Column(String(255))
    store_url = Column(String(1000))
    niche = Column(String(255))
    products_count = Column(Integer, default=0)
    avg_price = Column(Float)
    social_followers = Column(JSON)
    last_scraped = Column(DateTime)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

class Affiliate(Base):
    __tablename__ = 'affiliates'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    email = Column(String(255))
    referral_code = Column(String(100), unique=True)
    commission_rate = Column(Float, default=0.10)  # 10% default
    total_referrals = Column(Integer, default=0)
    total_sales = Column(Float, default=0.0)
    total_commission = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'referral_code': self.referral_code,
            'commission_rate': self.commission_rate,
            'total_referrals': self.total_referrals,
            'total_sales': self.total_sales,
            'total_commission': self.total_commission,
            'is_active': self.is_active
        }

class ChatLog(Base):
    __tablename__ = 'chat_logs'
    
    id = Column(Integer, primary_key=True)
    customer_email = Column(String(255))
    message = Column(Text)
    response = Column(Text)
    intent = Column(String(100))
    satisfied = Column(Boolean)
    created_at = Column(DateTime, default=datetime.now)

def init_db():
    """Initialize the database"""
    Base.metadata.create_all(engine)

def get_db_session():
    """Get a database session"""
    return SessionLocal()
