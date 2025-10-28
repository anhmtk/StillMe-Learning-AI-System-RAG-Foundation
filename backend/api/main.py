"""
FastAPI Main Application for StillMe V2
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..database.schema import init_database
from .routes import chat_router, learning_router, proposals_router
from ..services.scheduler import learning_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    logger.info("Starting StillMe V2 API...")
    
    os.makedirs("data", exist_ok=True)
    
    engine, session_local = init_database("sqlite:///data/stillme_v2.db")
    app.state.db_engine = engine
    app.state.db_session_local = session_local
    
    logger.info("Database initialized")
    
    # Start learning scheduler
    await learning_scheduler.start_scheduler()
    logger.info("Learning scheduler started")
    
    logger.info("StillMe V2 API ready")
    
    yield
    
    # Stop learning scheduler
    await learning_scheduler.stop_scheduler()
    logger.info("Shutting down StillMe V2 API...")


app = FastAPI(
    title="StillMe V2 API",
    description="Self-Evolving AI that learns from the internet daily",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router)
app.include_router(learning_router)
app.include_router(proposals_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "StillMe V2",
        "version": "2.0.0",
        "description": "Self-Evolving AI API",
        "status": "running",
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/stats")
async def stats():
    """API statistics"""
    return {
        "endpoints": len(app.routes),
        "database": "sqlite",
        "version": "2.0.0",
    }


@app.get("/scheduler/status")
async def scheduler_status():
    """Get learning scheduler status"""
    return learning_scheduler.get_scheduler_status()


@app.post("/scheduler/start")
async def start_scheduler():
    """Start learning scheduler"""
    await learning_scheduler.start_scheduler()
    return {"message": "Learning scheduler started", "status": "success"}


@app.post("/scheduler/stop")
async def stop_scheduler():
    """Stop learning scheduler"""
    await learning_scheduler.stop_scheduler()
    return {"message": "Learning scheduler stopped", "status": "success"}

