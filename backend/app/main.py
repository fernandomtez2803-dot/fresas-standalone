"""
Fresas Standalone - FastAPI Application
=======================================
Minimal FastAPI app for milling cutter control with barcode scanning.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import fresas

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting Fresas Standalone...")
    logger.info(f"Excel path: {settings.EXCEL_PATH}")
    
    # Pre-load catalog on startup
    from app.data_provider import get_data_provider
    provider = get_data_provider()
    count = provider.get_fresa_count()
    logger.info(f"Loaded {count} fresas from catalog")
    
    yield
    
    logger.info("Shutting down Fresas Standalone...")


# Create app
app = FastAPI(
    title="Fresas Standalone",
    description="Control de fresas con escaneo de código de barras",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(fresas.router, prefix="/api", tags=["Fresas"])


@app.get("/")
async def root():
    """Root endpoint - redirect info."""
    return {
        "app": "Fresas Standalone",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
