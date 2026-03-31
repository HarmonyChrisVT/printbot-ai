"""
PrintBot AI - Multi-Provider Fulfillment Chain
===============================================
Failover chain: Printful → Printify → Gelato → Gooten
"""
import asyncio
import aiohttp
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

from config.settings import config
from database.models import Order, AgentLog


@dataclass
class ProviderStatus:
    """Status of a fulfillment provider"""
    name: str
    healthy: bool
    last_check: datetime
    failure_count: int
    avg_response_time: float
    orders_processed: int


class BaseFulfillmentProvider:
    """Base class for fulfillment providers"""
    
    def __init__(self, api_key: str, store_id: str = None):
        self.api_key = api_key
        self.store_id = store_id
        self.name = "base"
        self.healthy = True
        self.failure_count = 0
        self.max_failures = 3
        self.last_check = datetime.utcnow()
        self.orders_processed = 0
    
    async def health_check(self) -> bool:
        """Check if provider is healthy"""
        raise NotImplementedError
    
    async def create_order(self, order_data: Dict) -> Optional[Dict]:
        """Create an order"""
        raise NotImplementedError
    
    async def get_order_status(self, order_id: str) -> Optional[Dict]:
        """Get order status"""
        raise NotImplementedError
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        raise NotImplementedError
    
    async def get_shipping_rates(self, address: Dict, items: List) -> List[Dict]:
        """Get shipping rates"""
        raise NotImplementedError
    
    def mark_failure(self):
        """Mark a failure"""
        self.failure_count += 1
        if self.failure_count >= self.max_failures:
            self.healthy = False
            print(f"⚠️ {self.name} marked as unhealthy after {self.failure_count} failures")
    
    def mark_success(self):
        """Mark a success"""
        self.failure_count = max(0, self.failure_count - 1)
        self.healthy = True
        self.orders_processed += 1


class PrintfulProvider(BaseFulfillmentProvider):
    """Printful API integration"""
    
    def __init__(self, api_key: str, store_id: str = None):
        super().__init__(api_key, store_id)
        self.name = "printful"
        self.base_url = "https://api.printful.com"
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    async def _request(self, method: str, endpoint: str, data: Dict = None) -> Optional[Dict]:
        """Make API request"""
        url = f"{self.base_url}{endpoint}"
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                if method == 'GET':
                    async with session.get(url, timeout=30) as response:
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 429:
                            await asyncio.sleep(60)
                            return None
                        else:
                            body = await response.text()
                            print(f"❌ Printful {response.status} on {endpoint}: {body[:300]}")
                            self.mark_failure()
                            return None
                
                elif method == 'POST':
                    async with session.post(url, json=data, timeout=30) as response:
                        if response.status in [200, 201]:
                            self.mark_success()
                            return await response.json()
                        else:
                            self.mark_failure()
                            return None
                            
            except Exception as e:
                print(f"❌ {self.name} request error: {e}")
                self.mark_failure()
                return None
    
    async def health_check(self) -> bool:
        """Check Printful health"""
        print(f"🔍 Printful health check — api_key={'set (' + self.api_key[:8] + '...)' if self.api_key else 'NOT SET'}")
        print(f"   URL: {self.base_url}/catalog/products")
        print(f"   Auth header: Bearer {self.api_key[:8]}..." if self.api_key else "   Auth header: MISSING")
        result = await self._request('GET', '/catalog/products?limit=1')
        self.last_check = datetime.utcnow()
        healthy = result is not None
        print(f"   Printful health: {'✅ healthy' if healthy else '❌ unhealthy'}")
        return healthy
    
    async def create_order(self, order_data: Dict) -> Optional[Dict]:
        """Create Printful order"""
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
                    'files': [{'url': item.get('design_url')}]
                }
                for item in order_data.get('items', [])
            ]
        }
        
        return await self._request('POST', '/orders', printful_order)
    
    async def get_order_status(self, order_id: str) -> Optional[Dict]:
        """Get Printful order status"""
        result = await self._request('GET', f'/orders/{order_id}')
        return result.get('result') if result else None
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel Printful order"""
        result = await self._request('DELETE', f'/orders/{order_id}')
        return result is not None
    
    async def get_shipping_rates(self, address: Dict, items: List) -> List[Dict]:
        """Get Printful shipping rates"""
        data = {
            'recipient': address,
            'items': items
        }
        result = await self._request('POST', '/shipping/rates', data)
        return result.get('result', []) if result else []


class PrintifyProvider(BaseFulfillmentProvider):
    """Printify API integration"""
    
    def __init__(self, api_key: str, shop_id: str = None):
        super().__init__(api_key, shop_id)
        self.name = "printify"
        self.base_url = "https://api.printify.com/v1"
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        self.shop_id = shop_id
    
    async def _request(self, method: str, endpoint: str, data: Dict = None) -> Optional[Dict]:
        """Make API request"""
        url = f"{self.base_url}{endpoint}"
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                if method == 'GET':
                    async with session.get(url, timeout=30) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            self.mark_failure()
                            return None
                
                elif method == 'POST':
                    async with session.post(url, json=data, timeout=30) as response:
                        if response.status in [200, 201]:
                            self.mark_success()
                            return await response.json()
                        else:
                            self.mark_failure()
                            return None
                            
            except Exception as e:
                print(f"❌ {self.name} request error: {e}")
                self.mark_failure()
                return None
    
    async def health_check(self) -> bool:
        """Check Printify health"""
        result = await self._request('GET', '/shops.json')
        self.last_check = datetime.utcnow()
        return result is not None
    
    async def create_order(self, order_data: Dict) -> Optional[Dict]:
        """Create Printify order"""
        if not self.shop_id:
            print("❌ Printify shop_id not configured")
            return None
        
        printify_order = {
            'external_id': order_data.get('shopify_order_id'),
            'label': order_data.get('order_number'),
            'line_items': [
                {
                    'product_id': item.get('printify_product_id'),
                    'variant_id': item.get('printify_variant_id'),
                    'quantity': item.get('quantity')
                }
                for item in order_data.get('items', [])
            ],
            'shipping_address': {
                'first_name': order_data.get('customer_name', '').split()[0],
                'last_name': ' '.join(order_data.get('customer_name', '').split()[1:]),
                'email': order_data.get('customer_email'),
                **order_data.get('shipping_address', {})
            }
        }
        
        return await self._request('POST', f'/shops/{self.shop_id}/orders.json', printify_order)
    
    async def get_order_status(self, order_id: str) -> Optional[Dict]:
        """Get Printify order status"""
        if not self.shop_id:
            return None
        return await self._request('GET', f'/shops/{self.shop_id}/orders/{order_id}.json')
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel Printify order"""
        if not self.shop_id:
            return False
        result = await self._request('POST', f'/shops/{self.shop_id}/orders/{order_id}/cancel.json')
        return result is not None
    
    async def get_shipping_rates(self, address: Dict, items: List) -> List[Dict]:
        """Get Printify shipping rates"""
        # Printify calculates shipping at checkout
        return []


class GelatoProvider(BaseFulfillmentProvider):
    """Gelato API integration"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.name = "gelato"
        self.base_url = "https://api.gelato.com/v2"
        self.headers = {
            'X-API-KEY': api_key,
            'Content-Type': 'application/json'
        }
    
    async def _request(self, method: str, endpoint: str, data: Dict = None) -> Optional[Dict]:
        """Make API request"""
        url = f"{self.base_url}{endpoint}"
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                if method == 'GET':
                    async with session.get(url, timeout=30) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            self.mark_failure()
                            return None
                
                elif method == 'POST':
                    async with session.post(url, json=data, timeout=30) as response:
                        if response.status in [200, 201]:
                            self.mark_success()
                            return await response.json()
                        else:
                            self.mark_failure()
                            return None
                            
            except Exception as e:
                print(f"❌ {self.name} request error: {e}")
                self.mark_failure()
                return None
    
    async def health_check(self) -> bool:
        """Check Gelato health"""
        result = await self._request('GET', '/products')
        self.last_check = datetime.utcnow()
        return result is not None
    
    async def create_order(self, order_data: Dict) -> Optional[Dict]:
        """Create Gelato order"""
        gelato_order = {
            'orderReferenceId': order_data.get('shopify_order_id'),
            'customer': {
                'firstName': order_data.get('customer_name', '').split()[0],
                'lastName': ' '.join(order_data.get('customer_name', '').split()[1:]),
                'email': order_data.get('customer_email')
            },
            'shippingAddress': order_data.get('shipping_address'),
            'items': [
                {
                    'itemReferenceId': item.get('id'),
                    'productUid': item.get('gelato_product_id'),
                    'files': [{'url': item.get('design_url')}],
                    'quantity': item.get('quantity')
                }
                for item in order_data.get('items', [])
            ]
        }
        
        return await self._request('POST', '/orders', gelato_order)
    
    async def get_order_status(self, order_id: str) -> Optional[Dict]:
        """Get Gelato order status"""
        return await self._request('GET', f'/orders/{order_id}')
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel Gelato order"""
        result = await self._request('POST', f'/orders/{order_id}/cancel')
        return result is not None
    
    async def get_shipping_rates(self, address: Dict, items: List) -> List[Dict]:
        """Get Gelato shipping rates"""
        return []


class GootenProvider(BaseFulfillmentProvider):
    """Gooten API integration"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.name = "gooten"
        self.base_url = "https://api.gooten.com/api/v1"
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    async def _request(self, method: str, endpoint: str, data: Dict = None) -> Optional[Dict]:
        """Make API request"""
        url = f"{self.base_url}{endpoint}"
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                if method == 'GET':
                    async with session.get(url, timeout=30) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            self.mark_failure()
                            return None
                
                elif method == 'POST':
                    async with session.post(url, json=data, timeout=30) as response:
                        if response.status in [200, 201]:
                            self.mark_success()
                            return await response.json()
                        else:
                            self.mark_failure()
                            return None
                            
            except Exception as e:
                print(f"❌ {self.name} request error: {e}")
                self.mark_failure()
                return None
    
    async def health_check(self) -> bool:
        """Check Gooten health"""
        result = await self._request('GET', '/products')
        self.last_check = datetime.utcnow()
        return result is not None
    
    async def create_order(self, order_data: Dict) -> Optional[Dict]:
        """Create Gooten order"""
        gooten_order = {
            'Id': order_data.get('shopify_order_id'),
            'Items': [
                {
                    'ProductId': item.get('gooten_product_id'),
                    'Quantity': item.get('quantity'),
                    'Images': [{'Url': item.get('design_url')}]
                }
                for item in order_data.get('items', [])
            ],
            'ShippingAddress': order_data.get('shipping_address'),
            'Email': order_data.get('customer_email')
        }
        
        return await self._request('POST', '/orders', gooten_order)
    
    async def get_order_status(self, order_id: str) -> Optional[Dict]:
        """Get Gooten order status"""
        return await self._request('GET', f'/orders/{order_id}')
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel Gooten order"""
        result = await self._request('POST', f'/orders/{order_id}/cancel')
        return result is not None
    
    async def get_shipping_rates(self, address: Dict, items: List) -> List[Dict]:
        """Get Gooten shipping rates"""
        return []


class FulfillmentProviderChain:
    """
    Manages the failover chain of fulfillment providers
    Order: Printful → Printify → Gelato → Gooten
    """
    
    def __init__(self, db_session):
        self.session = db_session
        self.providers: List[BaseFulfillmentProvider] = []
        self.current_provider_index = 0
        
        # Initialize providers from config
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all configured providers"""
        # Primary: Printful
        if config.printful.api_key:
            self.providers.append(PrintfulProvider(
                config.printful.api_key,
                config.printful.store_id
            ))
        
        # Backup 1: Printify
        printify_config = next(
            (p for p in config.printful.backup_providers if p['name'] == 'printify'),
            None
        )
        if printify_config and printify_config.get('enabled') and printify_config.get('api_key'):
            self.providers.append(PrintifyProvider(
                printify_config['api_key'],
                printify_config.get('shop_id')
            ))
        
        # Backup 2: Gelato
        gelato_config = next(
            (p for p in config.printful.backup_providers if p['name'] == 'gelato'),
            None
        )
        if gelato_config and gelato_config.get('enabled') and gelato_config.get('api_key'):
            self.providers.append(GelatoProvider(gelato_config['api_key']))
        
        # Backup 3: Gooten
        gooten_config = next(
            (p for p in config.printful.backup_providers if p['name'] == 'gooten'),
            None
        )
        if gooten_config and gooten_config.get('enabled') and gooten_config.get('api_key'):
            self.providers.append(GootenProvider(gooten_config['api_key']))
    
    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all providers"""
        results = {}
        for provider in self.providers:
            healthy = await provider.health_check()
            results[provider.name] = healthy
        return results
    
    async def create_order(self, order_data: Dict) -> Tuple[Optional[Dict], str]:
        """
        Create order with failover
        Returns: (order_result, provider_name_used)
        """
        # Try each provider in order
        for i, provider in enumerate(self.providers):
            if not provider.healthy:
                continue
            
            print(f"🔄 Trying {provider.name}...")
            
            result = await provider.create_order(order_data)
            
            if result:
                print(f"✅ Order created with {provider.name}")
                return result, provider.name
            else:
                print(f"⚠️ {provider.name} failed, trying next...")
        
        # All providers failed
        print("❌ All fulfillment providers failed!")
        return None, "none"
    
    async def get_order_status(self, order_id: str, provider_name: str) -> Optional[Dict]:
        """Get order status from specific provider"""
        provider = self._get_provider_by_name(provider_name)
        if provider:
            return await provider.get_order_status(order_id)
        return None
    
    async def cancel_order(self, order_id: str, provider_name: str) -> bool:
        """Cancel order with specific provider"""
        provider = self._get_provider_by_name(provider_name)
        if provider:
            return await provider.cancel_order(order_id)
        return False
    
    def _get_provider_by_name(self, name: str) -> Optional[BaseFulfillmentProvider]:
        """Get provider by name"""
        for provider in self.providers:
            if provider.name == name:
                return provider
        return None
    
    def get_status(self) -> List[ProviderStatus]:
        """Get status of all providers"""
        return [
            ProviderStatus(
                name=p.name,
                healthy=p.healthy,
                last_check=p.last_check,
                failure_count=p.failure_count,
                avg_response_time=0.0,  # Would track actual times
                orders_processed=p.orders_processed
            )
            for p in self.providers
        ]
