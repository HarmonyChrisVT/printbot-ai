"""
PrintBot AI - Protection System
================================
Advanced protection, monitoring, and contingency systems
"""
import asyncio
import json
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp

from config.settings import config
from database.models import SystemEvent, AgentLog, get_session


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskEvent:
    """Risk event data"""
    timestamp: datetime
    level: RiskLevel
    category: str
    message: str
    details: Dict
    auto_resolved: bool = False


class RateLimiter:
    """Rate limiter with exponential backoff"""
    
    def __init__(self):
        self.limits = {}
        self.backoff_delays = {}
    
    async def check_limit(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """Check if request is within rate limit"""
        now = datetime.utcnow()
        
        if key not in self.limits:
            self.limits[key] = []
        
        # Clean old entries
        self.limits[key] = [
            ts for ts in self.limits[key]
            if (now - ts).total_seconds() < window_seconds
        ]
        
        # Check if under limit
        if len(self.limits[key]) < max_requests:
            self.limits[key].append(now)
            return True
        
        return False
    
    async def get_backoff_delay(self, key: str, attempt: int) -> int:
        """Get exponential backoff delay"""
        base_delay = config.system.base_delay
        max_delay = 3600  # Max 1 hour
        
        if config.system.rate_limit_backoff == "exponential":
            delay = min(base_delay * (2 ** attempt), max_delay)
        else:
            delay = min(base_delay * attempt, max_delay)
        
        self.backoff_delays[key] = delay
        return delay


class FraudDetector:
    """Detect suspicious activities and potential fraud"""
    
    def __init__(self, db_session):
        self.session = db_session
        self.suspicious_patterns = {
            'rapid_orders': {'threshold': 5, 'window_minutes': 10},
            'high_value_orders': {'threshold': 500, 'currency': 'USD'},
            'multiple_addresses': {'threshold': 3, 'window_hours': 24},
            'failed_payments': {'threshold': 3, 'window_hours': 1}
        }
    
    def analyze_order(self, order_data: Dict) -> Optional[RiskEvent]:
        """Analyze order for fraud indicators"""
        risks = []
        
        # Check order value
        if order_data.get('total_price', 0) > self.suspicious_patterns['high_value_orders']['threshold']:
            risks.append(f"High value order: ${order_data.get('total_price')}")
        
        # Check for rapid ordering (would need customer history)
        # Check for multiple shipping addresses
        
        if risks:
            return RiskEvent(
                timestamp=datetime.utcnow(),
                level=RiskLevel.MEDIUM,
                category='fraud',
                message='Suspicious order detected',
                details={'risks': risks, 'order': order_data}
            )
        
        return None
    
    def flag_review(self, risk_event: RiskEvent) -> bool:
        """Flag order for manual review"""
        # Log the event
        event = SystemEvent(
            event_type='fraud_alert',
            severity='warning',
            message=risk_event.message,
            details=asdict(risk_event)
        )
        self.session.add(event)
        self.session.commit()
        
        # Would send notification
        return True


class APIMonitor:
    """Monitor API health and switch to backups"""
    
    def __init__(self):
        self.api_health = {
            'openai': {'healthy': True, 'last_check': None, 'failures': 0},
            'shopify': {'healthy': True, 'last_check': None, 'failures': 0},
            'printful': {'healthy': True, 'last_check': None, 'failures': 0},
            'instagram': {'healthy': True, 'last_check': None, 'failures': 0},
        }
        self.max_failures = 3
    
    async def check_api_health(self, api_name: str, check_func: Callable) -> bool:
        """Check if an API is healthy"""
        try:
            is_healthy = await check_func()
            
            self.api_health[api_name]['last_check'] = datetime.utcnow()
            
            if is_healthy:
                self.api_health[api_name]['healthy'] = True
                self.api_health[api_name]['failures'] = 0
            else:
                self.api_health[api_name]['failures'] += 1
                
                if self.api_health[api_name]['failures'] >= self.max_failures:
                    self.api_health[api_name]['healthy'] = False
                    await self._handle_api_failure(api_name)
            
            return is_healthy
            
        except Exception as e:
            self.api_health[api_name]['failures'] += 1
            
            if self.api_health[api_name]['failures'] >= self.max_failures:
                self.api_health[api_name]['healthy'] = False
                await self._handle_api_failure(api_name)
            
            return False
    
    async def _handle_api_failure(self, api_name: str):
        """Handle API failure - switch to backup"""
        print(f"⚠️ API failure detected: {api_name}")
        
        if api_name == 'openai':
            # Switch to backup AI provider
            print("🔄 Switching to backup AI provider...")
            # Would implement provider switching logic
        
        elif api_name == 'printful':
            # Switch to backup fulfillment provider
            print("🔄 Switching to backup fulfillment provider...")
            # Would implement provider switching logic


class ContentModerator:
    """Moderate AI-generated content for policy compliance"""
    
    def __init__(self):
        self.blocked_keywords = [
            # Add inappropriate terms to block
        ]
        self.sensitive_topics = [
            'political', 'religious', 'controversial'
        ]
    
    def check_design_prompt(self, prompt: str) -> Dict:
        """Check if design prompt is appropriate"""
        prompt_lower = prompt.lower()
        
        # Check blocked keywords
        for keyword in self.blocked_keywords:
            if keyword in prompt_lower:
                return {
                    'approved': False,
                    'reason': f'Blocked keyword detected: {keyword}'
                }
        
        # Check for sensitive topics
        sensitive_found = []
        for topic in self.sensitive_topics:
            if topic in prompt_lower:
                sensitive_found.append(topic)
        
        if sensitive_found:
            return {
                'approved': True,
                'flagged': True,
                'reason': f'Sensitive topics detected: {", ".join(sensitive_found)}',
                'requires_review': True
            }
        
        return {
            'approved': True,
            'flagged': False
        }
    
    def check_social_post(self, content: str) -> Dict:
        """Check if social media post is appropriate"""
        # Similar checks for social content
        return self.check_design_prompt(content)


class ComplianceMonitor:
    """Monitor for legal and platform compliance"""
    
    def __init__(self, db_session):
        self.session = db_session
        self.platform_rules = {
            'instagram': {
                'max_daily_actions': 200,
                'max_hourly_actions': 60,
                'min_delay_seconds': 30
            },
            'tiktok': {
                'max_daily_actions': 150,
                'max_hourly_actions': 50,
                'min_delay_seconds': 45
            }
        }
    
    def check_action_limits(self, platform: str, action_count: int, time_window: str) -> bool:
        """Check if action is within platform limits"""
        rules = self.platform_rules.get(platform, {})
        
        if time_window == 'daily':
            return action_count < rules.get('max_daily_actions', 100)
        elif time_window == 'hourly':
            return action_count < rules.get('max_hourly_actions', 30)
        
        return True
    
    def log_compliance_check(self, platform: str, action: str, passed: bool):
        """Log compliance check"""
        event = SystemEvent(
            event_type='compliance_check',
            severity='info' if passed else 'warning',
            message=f'{platform} {action} compliance: {"passed" if passed else "failed"}',
            details={'platform': platform, 'action': action, 'passed': passed}
        )
        self.session.add(event)
        self.session.commit()


class ProtectionSystem:
    """
    Main Protection System
    Coordinates all protection features
    """
    
    def __init__(self, db_session):
        self.session = db_session
        self.rate_limiter = RateLimiter()
        self.fraud_detector = FraudDetector(db_session)
        self.api_monitor = APIMonitor()
        self.content_moderator = ContentModerator()
        self.compliance_monitor = ComplianceMonitor(db_session)
        
        self.risk_events: List[RiskEvent] = []
        self.protection_active = True
    
    async def initialize(self):
        """Initialize protection systems"""
        print("🛡️  Protection System initialized")
        
        # Start monitoring loops
        asyncio.create_task(self._monitoring_loop())
    
    async def _monitoring_loop(self):
        """Continuous monitoring loop"""
        while self.protection_active:
            try:
                # Check API health
                await self._check_all_apis()
                
                # Clean old risk events
                self._clean_old_events()
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                print(f"❌ Protection monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _check_all_apis(self):
        """Check health of all APIs"""
        # Would implement actual health checks
        pass
    
    def _clean_old_events(self):
        """Clean risk events older than 24 hours"""
        cutoff = datetime.utcnow() - timedelta(hours=24)
        self.risk_events = [
            e for e in self.risk_events
            if e.timestamp > cutoff
        ]
    
    # Public API methods
    async def check_rate_limit(self, key: str, max_requests: int, window: int) -> bool:
        """Check rate limit"""
        return await self.rate_limiter.check_limit(key, max_requests, window)
    
    def moderate_content(self, content: str, content_type: str = 'design') -> Dict:
        """Moderate content"""
        if content_type == 'design':
            return self.content_moderator.check_design_prompt(content)
        else:
            return self.content_moderator.check_social_post(content)
    
    def check_fraud(self, order_data: Dict) -> Optional[RiskEvent]:
        """Check for fraud"""
        return self.fraud_detector.analyze_order(order_data)
    
    def get_risk_summary(self) -> Dict:
        """Get summary of current risks"""
        by_level = {
            RiskLevel.LOW: 0,
            RiskLevel.MEDIUM: 0,
            RiskLevel.HIGH: 0,
            RiskLevel.CRITICAL: 0
        }
        
        for event in self.risk_events:
            by_level[event.level] += 1
        
        return {
            'total_events': len(self.risk_events),
            'by_level': {k.value: v for k, v in by_level.items()},
            'recent_events': [
                {
                    'timestamp': e.timestamp.isoformat(),
                    'level': e.level.value,
                    'category': e.category,
                    'message': e.message
                }
                for e in sorted(self.risk_events, key=lambda x: x.timestamp, reverse=True)[:5]
            ]
        }
    
    def get_protection_status(self) -> Dict:
        """Get overall protection status"""
        return {
            'active': self.protection_active,
            'api_health': self.api_monitor.api_health,
            'rate_limits': len(self.rate_limiter.limits),
            'risk_summary': self.get_risk_summary()
        }
