"""
PrintBot AI - Shopify Integration
==================================
Handles all Shopify API interactions
"""
import aiohttp
from typing import List, Dict, Optional
from datetime import datetime

from config.settings import config


class ShopifyAPI:
    """Shopify API wrapper"""
    
    def __init__(self):
        self.shop_url = config.shopify.shop_url
        self.access_token = config.shopify.access_token
        self.api_version = config.shopify.api_version
        self.base_url = f"https://{self.shop_url}/admin/api/{self.api_version}"
        
        self.headers = {
            'X-Shopify-Access-Token': self.access_token,
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
                            print(f"❌ Shopify API error: {response.status}")
                            return None
                
                elif method == 'POST':
                    async with session.post(url, json=data, timeout=30) as response:
                        if response.status in [200, 201]:
                            return await response.json()
                        else:
                            print(f"❌ Shopify API error: {response.status}")
                            return None
                
                elif method == 'PUT':
                    async with session.put(url, json=data, timeout=30) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            print(f"❌ Shopify API error: {response.status}")
                            return None
                
                elif method == 'DELETE':
                    async with session.delete(url, timeout=30) as response:
                        return response.status == 200
                        
            except Exception as e:
                print(f"❌ Shopify request error: {e}")
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
        """Get orders from store"""
        endpoint = f'/orders.json?status={status}&limit={limit}'
        if since_id:
            endpoint += f'&since_id={since_id}'
        
        response = await self._request('GET', endpoint)
        return response.get('orders', []) if response else []
    
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
