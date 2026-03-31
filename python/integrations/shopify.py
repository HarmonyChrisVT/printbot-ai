"""
PrintBot AI - Shopify Integration
==================================
Handles all Shopify API interactions.

Auth: supports two modes
  1. Legacy permanent token  — set SHOPIFY_ACCESS_TOKEN (shpca_...)
  2. Dev Dashboard OAuth     — set SHOPIFY_API_KEY + SHOPIFY_API_SECRET (shpss_...)
     Tokens are fetched via client credentials grant and cached for 23 hours.
"""
import aiohttp
import traceback
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from config.settings import config

# Module-level token cache — shared across all ShopifyAPI instances so we
# don't hammer the OAuth endpoint on every API call.
_cached_token: Optional[str] = None
_token_fetched_at: Optional[datetime] = None
_TOKEN_TTL = timedelta(hours=23)


class ShopifyAPI:
    """Shopify API wrapper"""

    def __init__(self):
        self.shop_url = config.shopify.shop_url
        self.api_key = config.shopify.api_key
        self.api_secret = config.shopify.api_secret
        self.api_version = config.shopify.api_version
        self.base_url = f"https://{self.shop_url}/admin/api/{self.api_version}"

        # Static token (legacy shpca_...) — used directly if set
        self._static_token = config.shopify.access_token

        print(
            f"🔧 ShopifyAPI init — shop_url={repr(self.shop_url)} "
            f"| static_token={'yes' if self._static_token else 'no'} "
            f"| oauth={'yes' if (self.api_key and self.api_secret) else 'no'}"
        )

    def _make_headers(self, token: str) -> Dict:
        return {
            'X-Shopify-Access-Token': token,
            'Content-Type': 'application/json',
        }

    async def _fetch_oauth_token(self) -> str:
        """Exchange API key + secret for an access token via client credentials grant."""
        url = f"https://{self.shop_url}/admin/oauth/access_token"
        payload = {
            "client_id": self.api_key,
            "client_secret": self.api_secret,
            "grant_type": "client_credentials",
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=30) as resp:
                body = await resp.json()
                if resp.status == 200 and "access_token" in body:
                    token = body["access_token"]
                    print(f"✅ Shopify OAuth token fetched (prefix: {token[:8]})")
                    return token
                raise Exception(f"OAuth token exchange failed ({resp.status}): {body}")

    async def _get_token(self) -> str:
        """Return a valid access token, refreshing if needed."""
        global _cached_token, _token_fetched_at

        # Use static legacy token if set
        if self._static_token:
            return self._static_token

        # Use cached OAuth token if still fresh
        if (
            _cached_token
            and _token_fetched_at
            and datetime.utcnow() - _token_fetched_at < _TOKEN_TTL
        ):
            return _cached_token

        # Fetch a new OAuth token
        _cached_token = await self._fetch_oauth_token()
        _token_fetched_at = datetime.utcnow()
        return _cached_token
    
    async def _request(self, method: str, endpoint: str, data: Dict = None) -> Optional[Dict]:
        """Make API request"""
        token = await self._get_token()
        url = f"{self.base_url}{endpoint}"

        async with aiohttp.ClientSession(headers=self._make_headers(token)) as session:
            try:
                if method == 'GET':
                    async with session.get(url, timeout=30) as response:
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 403:
                            print(f"⚠️  Shopify 403 on {endpoint} — scope not granted, skipping")
                            return None
                        else:
                            body = await response.text()
                            print(f"❌ Shopify API error {response.status} on {endpoint}: {body[:200]}")
                            return None

                elif method == 'POST':
                    async with session.post(url, json=data, timeout=30) as response:
                        if response.status in [200, 201]:
                            return await response.json()
                        else:
                            body = await response.text()
                            print(f"❌ Shopify API error {response.status} on {endpoint}: {body[:200]}")
                            return None

                elif method == 'PUT':
                    async with session.put(url, json=data, timeout=30) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            body = await response.text()
                            print(f"❌ Shopify API error {response.status} on {endpoint}: {body[:200]}")
                            return None
                
                elif method == 'DELETE':
                    async with session.delete(url, timeout=30) as response:
                        return response.status == 200
                        
            except Exception as e:
                print(f"❌ Shopify request error on {url}: {e}")
                print(traceback.format_exc())
                return None
    
    # Products
    async def get_products(self, limit: int = 50, page_info: str = None) -> List[Dict]:
        """Get products from store"""
        endpoint = f'/products.json?limit={limit}'
        if page_info:
            endpoint += f'&page_info={page_info}'
        
        response = await self._request('GET', endpoint)
        return response.get('products', []) if response else []
    
    async def get_product(self, product_id: str) -> Optional[Dict]:
        """Get a single product"""
        endpoint = f'/products/{product_id}.json'
        response = await self._request('GET', endpoint)
        return response.get('product') if response else None
    
    async def create_product(self, product_data: Dict) -> Optional[Dict]:
        """Create a new product"""
        endpoint = '/products.json'
        
        data = {
            'product': {
                'title': product_data.get('title'),
                'body_html': product_data.get('description'),
                'vendor': product_data.get('vendor', 'PrintBot AI'),
                'product_type': product_data.get('product_type'),
                'tags': product_data.get('tags', []),
                'variants': [
                    {
                        'option1': variant.get('size', 'Default'),
                        'price': str(variant.get('price', 0)),
                        'sku': variant.get('sku'),
                        'inventory_quantity': variant.get('inventory', 100)
                    }
                    for variant in product_data.get('variants', [{}])
                ],
                'options': [
                    {
                        'name': 'Size',
                        'values': list(set(v.get('size', 'Default') for v in product_data.get('variants', [{}])))
                    }
                ],
                'images': [
                    {'src': url}
                    for url in product_data.get('image_urls', [])
                ]
            }
        }
        
        response = await self._request('POST', endpoint, data)
        return response.get('product') if response else None
    
    async def update_product(self, product_id: str, updates: Dict) -> Optional[Dict]:
        """Update an existing product"""
        endpoint = f'/products/{product_id}.json'
        
        data = {'product': updates}
        response = await self._request('PUT', endpoint, data)
        return response.get('product') if response else None
    
    async def update_product_price(self, product_id: str, price: float, compare_at_price: float = None) -> bool:
        """Update product price"""
        # First get the product to find variant ID
        product = await self.get_product(product_id)
        if not product or not product.get('variants'):
            return False
        
        variant_id = product['variants'][0]['id']
        
        # Update variant price
        endpoint = f'/variants/{variant_id}.json'
        data = {
            'variant': {
                'id': variant_id,
                'price': str(price)
            }
        }
        
        if compare_at_price:
            data['variant']['compare_at_price'] = str(compare_at_price)
        
        response = await self._request('PUT', endpoint, data)
        return response is not None
    
    async def delete_product(self, product_id: str) -> bool:
        """Delete a product"""
        endpoint = f'/products/{product_id}.json'
        return await self._request('DELETE', endpoint)
    
    # Orders
    async def get_orders(self, since_id: str = None, status: str = 'any', limit: int = 50) -> List[Dict]:
        """Get orders from store. Returns [] if read_orders scope not granted (403)."""
        endpoint = f'/orders.json?status={status}&limit={limit}'
        if since_id:
            endpoint += f'&since_id={since_id}'
        try:
            response = await self._request('GET', endpoint)
            return response.get('orders', []) if response else []
        except Exception:
            return []
    
    async def get_order(self, order_id: str) -> Optional[Dict]:
        """Get a single order"""
        endpoint = f'/orders/{order_id}.json'
        response = await self._request('GET', endpoint)
        return response.get('order') if response else None
    
    async def fulfill_order(self, order_id: str, tracking_number: str = None, tracking_url: str = None) -> Optional[Dict]:
        """Mark order as fulfilled"""
        endpoint = f'/orders/{order_id}/fulfillments.json'
        
        data = {
            'fulfillment': {
                'location_id': None,  # Use default location
                'tracking_number': tracking_number,
                'tracking_urls': [tracking_url] if tracking_url else [],
                'notify_customer': True
            }
        }
        
        response = await self._request('POST', endpoint, data)
        return response.get('fulfillment') if response else None
    
    # Inventory
    async def get_inventory_levels(self, inventory_item_id: str) -> List[Dict]:
        """Get inventory levels for an item"""
        endpoint = f'/inventory_levels.json?inventory_item_ids={inventory_item_id}'
        response = await self._request('GET', endpoint)
        return response.get('inventory_levels', []) if response else []
    
    async def adjust_inventory(self, inventory_item_id: str, location_id: str, adjustment: int) -> bool:
        """Adjust inventory level"""
        endpoint = '/inventory_levels/adjust.json'
        
        data = {
            'location_id': location_id,
            'inventory_item_id': inventory_item_id,
            'available_adjustment': adjustment
        }
        
        response = await self._request('POST', endpoint, data)
        return response is not None
    
    # Shop info
    async def get_shop_info(self) -> Optional[Dict]:
        """Get shop information"""
        endpoint = '/shop.json'
        response = await self._request('GET', endpoint)
        return response.get('shop') if response else None

    async def test_connection(self) -> Dict:
        """
        Validate Shopify credentials by listing products (avoids read_orders scope).
        Returns dict with 'ok' bool, 'shop_name', and 'message'.
        """
        has_static = bool(self.shop_url and self._static_token)
        has_oauth  = bool(self.shop_url and self.api_key and self.api_secret)
        if not has_static and not has_oauth:
            return {
                'ok': False, 'shop_name': None,
                'message': 'Set SHOPIFY_SHOP_URL + SHOPIFY_API_KEY + SHOPIFY_API_SECRET in Railway'
            }
        try:
            # Use /products.json — does not require read_orders scope
            response = await self._request('GET', '/products.json?limit=1')
            if response is not None:
                return {'ok': True, 'shop_name': self.shop_url, 'message': 'Connected'}
            return {'ok': False, 'shop_name': None, 'message': 'Token rejected — check scopes'}
        except Exception as e:
            return {'ok': False, 'shop_name': None, 'message': str(e)}
    
    # Webhooks
    async def create_webhook(self, topic: str, address: str) -> Optional[Dict]:
        """Create a webhook"""
        endpoint = '/webhooks.json'
        
        data = {
            'webhook': {
                'topic': topic,
                'address': address,
                'format': 'json'
            }
        }
        
        response = await self._request('POST', endpoint, data)
        return response.get('webhook') if response else None
    
    async def get_webhooks(self) -> List[Dict]:
        """Get all webhooks"""
        endpoint = '/webhooks.json'
        response = await self._request('GET', endpoint)
        return response.get('webhooks', []) if response else []
    
    async def delete_webhook(self, webhook_id: str) -> bool:
        """Delete a webhook"""
        endpoint = f'/webhooks/{webhook_id}.json'
        return await self._request('DELETE', endpoint)


class ShopifyProductSync:
    """Syncs products between local database and Shopify"""
    
    def __init__(self, db_session):
        self.session = db_session
        self.api = ShopifyAPI()
    
    async def sync_all_products(self):
        """Sync all products to Shopify"""
        from database.models import Product
        
        products = self.session.query(Product).filter(
            Product.is_active == True
        ).all()
        
        for product in products:
            if product.shopify_id:
                # Update existing
                await self._update_shopify_product(product)
            else:
                # Create new
                await self._create_shopify_product(product)
    
    async def _create_shopify_product(self, product):
        """Create product in Shopify"""
        product_data = {
            'title': product.title,
            'description': product.description,
            'product_type': product.product_type,
            'tags': product.tags or [],
            'image_urls': product.mockup_urls or [product.design_url],
            'variants': [
                {
                    'size': variant.size,
                    'price': variant.selling_price,
                    'sku': variant.sku,
                    'inventory': variant.inventory_quantity
                }
                for variant in product.variants
            ]
        }
        
        result = await self.api.create_product(product_data)
        
        if result:
            product.shopify_id = str(result.get('id'))
            product.last_synced = datetime.utcnow()
            self.session.commit()
            
            print(f"✅ Product '{product.title}' created in Shopify")
    
    async def _update_shopify_product(self, product):
        """Update product in Shopify"""
        updates = {
            'title': product.title,
            'body_html': product.description,
            'tags': product.tags or []
        }
        
        await self.api.update_product(product.shopify_id, updates)
        
        # Update prices
        for variant in product.variants:
            await self.api.update_product_price(
                product.shopify_id,
                variant.selling_price
            )
        
        product.last_synced = datetime.utcnow()
        self.session.commit()
        
        print(f"✅ Product '{product.title}' updated in Shopify")
