"""
PrintBot AI - Configuration Settings
=====================================
Central configuration for all agents and integrations.
"""
import os
from dataclasses import dataclass, field
from typing import List, Dict
from datetime import timedelta


@dataclass
class ShopifyConfig:
    """Shopify API Configuration"""
    shop_url: str = ""  # your-store.myshopify.com
    api_key: str = ""   # Admin API key
    api_secret: str = ""
    access_token: str = ""
    api_version: str = "2024-01"
    
    @property
    def is_configured(self) -> bool:
        return all([self.shop_url, self.access_token])


@dataclass
class PrintfulConfig:
    """Printful API Configuration"""
    api_key: str = ""
    api_base: str = "https://api.printful.com"
    store_id: str = ""
    
    # Backup providers
    backup_providers: List[Dict] = field(default_factory=lambda: [
        {"name": "printify", "enabled": False},
        {"name": "gelato", "enabled": False},
        {"name": "gooten", "enabled": False}
    ])
    
    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)


@dataclass
class OpenAIConfig:
    """OpenAI API Configuration"""
    api_key: str = ""
    model: str = "gpt-4"
    image_model: str = "dall-e-3"
    max_tokens: int = 2000
    temperature: float = 0.7
    
    # Backup AI providers
    backup_providers: List[Dict] = field(default_factory=lambda: [
        {"name": "claude", "api_key": "", "enabled": False},
        {"name": "gemini", "api_key": "", "enabled": False},
        {"name": "stablediffusion", "enabled": False}
    ])
    
    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)


@dataclass
class SocialMediaConfig:
    """Social Media API Configuration"""
    # Instagram
    instagram_accounts: List[Dict] = field(default_factory=lambda: [
        {"username": "", "password": "", "api_key": "", "is_primary": True, "is_active": True},
        {"username": "", "password": "", "api_key": "", "is_primary": False, "is_active": False},
        {"username": "", "password": "", "api_key": "", "is_primary": False, "is_active": False}
    ])
    
    # TikTok
    tiktok_accounts: List[Dict] = field(default_factory=lambda: [
        {"username": "", "password": "", "api_key": "", "is_primary": True, "is_active": True},
        {"username": "", "password": "", "api_key": "", "is_primary": False, "is_active": False},
        {"username": "", "password": "", "api_key": "", "is_primary": False, "is_active": False}
    ])
    
    # Engagement settings
    auto_like: bool = True
    auto_comment: bool = True
    auto_follow: bool = True
    auto_dm: bool = True
    human_delay_min: int = 2
    human_delay_max: int = 8
    max_daily_actions: int = 100


@dataclass
class PricingConfig:
    """Dynamic Pricing Configuration"""
    anchor_margin: float = 0.40  # 40% above cost
    floor_margin: float = 0.25   # Never below 25% margin
    competitor_check_interval: int = 7200  # 2 hours in seconds
    
    # Psychological pricing
    use_charm_pricing: bool = True  # $27.99 instead of $28.00
    charm_ending: str = ".99"
    
    # Bundle pricing
    bundle_enabled: bool = True
    bundle_discount: float = 0.15  # 15% off for 2+ items
    bundle_threshold: int = 2
    
    # Competitor scraping
    competitor_urls: List[str] = field(default_factory=list)
    price_adjustment_threshold: float = 0.05  # 5% difference triggers update


@dataclass
class DesignConfig:
    """Design Agent Configuration"""
    trend_sources: List[str] = field(default_factory=lambda: [
        "https://trends.google.com/trends/trendingsearches/daily",
        "https://www.pinterest.com/today",
        "https://www.etsy.com/search?q=trending",
        "https://www.redbubble.com/shop/?query=trending"
    ])
    
    # Design generation settings
    max_daily_designs: int = 3
    design_interval: int = 1800  # 30 minutes in seconds
    
    # Image generation
    image_size: str = "1024x1024"
    image_quality: str = "standard"
    
    # Approval workflow
    auto_approve: bool = False  # Set to True for full automation
    approval_threshold: float = 0.8  # AI confidence threshold
    
    # Product templates
    product_types: List[str] = field(default_factory=lambda: [
        "t-shirt", "hoodie", "mug", "poster", "phone_case", "tote_bag"
    ])


@dataclass
class FulfillmentConfig:
    """Fulfillment Agent Configuration"""
    order_poll_interval: int = 300  # 5 minutes in seconds
    
    # Email notifications
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    notification_email: str = ""
    
    # Tracking
    auto_send_tracking: bool = True
    tracking_email_template: str = ""


@dataclass
class SystemConfig:
    """System-wide Configuration"""
    # Dead man's switch
    dead_mans_switch_enabled: bool = True
    check_in_interval: int = 86400  # 24 hours
    emergency_contact: str = ""
    
    # Backups
    backup_enabled: bool = True
    backup_interval: int = 604800  # Weekly (7 days)
    backup_cloud_provider: str = "google_drive"  # or "dropbox", "s3"
    backup_cloud_token: str = ""
    
    # Rate limiting
    rate_limit_backoff: str = "exponential"
    max_retries: int = 5
    base_delay: int = 60  # seconds
    
    # Logging
    log_level: str = "INFO"
    log_to_file: bool = True
    log_retention_days: int = 30


@dataclass
class AppConfig:
    """Main Application Configuration"""
    shopify: ShopifyConfig = field(default_factory=ShopifyConfig)
    printful: PrintfulConfig = field(default_factory=PrintfulConfig)
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)
    social: SocialMediaConfig = field(default_factory=SocialMediaConfig)
    pricing: PricingConfig = field(default_factory=PricingConfig)
    design: DesignConfig = field(default_factory=DesignConfig)
    fulfillment: FulfillmentConfig = field(default_factory=FulfillmentConfig)
    system: SystemConfig = field(default_factory=SystemConfig)
    
    # Database
    database_path: str = "./data/printbot.db"
    
    # Dashboard
    dashboard_host: str = "0.0.0.0"
    dashboard_port: int = 8080


# Global config instance
config = AppConfig()


def load_config_from_env():
    """Load configuration from environment variables"""
    # Shopify
    config.shopify.shop_url = os.getenv("SHOPIFY_SHOP_URL", "")
    config.shopify.access_token = os.getenv("SHOPIFY_ACCESS_TOKEN", "")
    config.shopify.api_key = os.getenv("SHOPIFY_API_KEY", "")
    config.shopify.api_secret = os.getenv("SHOPIFY_API_SECRET", "")
    
    # Printful
    config.printful.api_key = os.getenv("PRINTFUL_API_KEY", "")
    config.printful.store_id = os.getenv("PRINTFUL_STORE_ID", "")
    
    # OpenAI
    config.openai.api_key = os.getenv("OPENAI_API_KEY", "")
    
    # Social Media
    for i, account in enumerate(config.social.instagram_accounts):
        account["username"] = os.getenv(f"INSTAGRAM_USERNAME_{i}", "")
        account["password"] = os.getenv(f"INSTAGRAM_PASSWORD_{i}", "")
        account["api_key"] = os.getenv(f"INSTAGRAM_API_KEY_{i}", "")
    
    # Email
    config.fulfillment.smtp_host = os.getenv("SMTP_HOST", "")
    config.fulfillment.smtp_user = os.getenv("SMTP_USER", "")
    config.fulfillment.smtp_password = os.getenv("SMTP_PASSWORD", "")
    config.fulfillment.notification_email = os.getenv("NOTIFICATION_EMAIL", "")
    
    # System
    config.system.emergency_contact = os.getenv("EMERGENCY_CONTACT", "")
    config.system.backup_cloud_token = os.getenv("BACKUP_CLOUD_TOKEN", "")


def load_config_from_file(filepath: str):
    """Load configuration from JSON file"""
    import json
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            data = json.load(f)
            # Update config from JSON data
            for key, value in data.items():
                if hasattr(config, key):
                    setattr(config, key, value)


def save_config_to_file(filepath: str):
    """Save configuration to JSON file"""
    import json
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(config.__dict__, f, indent=2, default=str)
