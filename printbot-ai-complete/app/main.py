#!/usr/bin/env python3
"""
PrintBot AI - Main Application
Automated Print-on-Demand Store with 11 AI Agents
"""

import asyncio
import os
import sys
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn

# Add python folder to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python'))

from database.models import init_db, get_db_session, StoreConfig, Product, Order, SocialAccount
from python.agents.orchestrator import AgentOrchestrator
from python.utils.logger import get_logger

logger = get_logger(__name__)

# Global orchestrator instance
orchestrator = None

class StoreSetupRequest(BaseModel):
    store_name: str
    niche: str
    platforms: List[str]
    auto_mode: bool = True

class ProductRequest(BaseModel):
    prompt: Optional[str] = None
    trending: bool = True

class SocialPostRequest(BaseModel):
    platform: str
    content_type: str = "product"

class ManualOverrideRequest(BaseModel):
    action: str
    params: Dict[str, Any]

# Startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    global orchestrator
    logger.info("=" * 50)
    logger.info("PrintBot AI Starting Up...")
    logger.info("=" * 50)
    
    # Initialize database
    init_db()
    
    # Initialize orchestrator
    orchestrator = AgentOrchestrator()
    
    logger.info("PrintBot AI Ready!")
    yield
    
    # Shutdown
    logger.info("Shutting down PrintBot AI...")

app = FastAPI(
    title="PrintBot AI",
    description="Automated Print-on-Demand Store with 11 AI Agents",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
@app.get("/api/status")
async def get_status():
    """Get overall system status"""
    if orchestrator:
        return await orchestrator.get_status()
    return {"status": "initializing", "agents": {}}

@app.post("/api/setup")
async def setup_store(request: StoreSetupRequest):
    """Initial store setup"""
    try:
        result = await orchestrator.setup_store(
            store_name=request.store_name,
            niche=request.niche,
            platforms=request.platforms,
            auto_mode=request.auto_mode
        )
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Setup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/products/generate")
async def generate_product(request: ProductRequest, background_tasks: BackgroundTasks):
    """Generate a new product"""
    try:
        product = await orchestrator.generate_product(
            prompt=request.prompt,
            use_trending=request.trending
        )
        return {"success": True, "product": product}
    except Exception as e:
        logger.error(f"Product generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/products")
async def get_products(limit: int = 50):
    """Get all products"""
    session = get_db_session()
    try:
        products = session.query(Product).order_by(Product.created_at.desc()).limit(limit).all()
        return {"products": [p.to_dict() for p in products]}
    finally:
        session.close()

@app.get("/api/orders")
async def get_orders(status: Optional[str] = None):
    """Get orders with optional filter"""
    session = get_db_session()
    try:
        query = session.query(Order)
        if status:
            query = query.filter(Order.status == status)
        orders = query.order_by(Order.created_at.desc()).all()
        return {"orders": [o.to_dict() for o in orders]}
    finally:
        session.close()

@app.post("/api/social/post")
async def create_social_post(request: SocialPostRequest):
    """Create a social media post"""
    try:
        result = await orchestrator.create_social_post(
            platform=request.platform,
            content_type=request.content_type
        )
        return {"success": True, "post": result}
    except Exception as e:
        logger.error(f"Social post error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/profit")
async def get_profit_analytics():
    """Get profit analytics"""
    try:
        analytics = await orchestrator.get_profit_analytics()
        return {"success": True, "analytics": analytics}
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/override")
async def manual_override(request: ManualOverrideRequest):
    """Manual override for any agent action"""
    try:
        result = await orchestrator.manual_override(
            action=request.action,
            params=request.params
        )
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Override error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config")
async def get_config():
    """Get store configuration"""
    session = get_db_session()
    try:
        config = session.query(StoreConfig).first()
        if config:
            return {"config": config.to_dict()}
        return {"config": None}
    finally:
        session.close()

@app.post("/api/config")
async def update_config(config: Dict[str, Any]):
    """Update store configuration"""
    session = get_db_session()
    try:
        store_config = session.query(StoreConfig).first()
        if not store_config:
            store_config = StoreConfig()
        
        for key, value in config.items():
            if hasattr(store_config, key):
                setattr(store_config, key, value)
        
        session.add(store_config)
        session.commit()
        return {"success": True, "config": store_config.to_dict()}
    finally:
        session.close()

# Serve React frontend
@app.get("/")
async def serve_frontend():
    frontend_path = os.path.join(os.path.dirname(__file__), 'src', 'index.html')
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    return {"message": "PrintBot AI API is running", "docs": "/docs"}

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"Starting PrintBot AI on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")
