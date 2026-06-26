"""PROJECT WARROOM FastAPI Application"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle"""
    from database.config import db_config
    try:
        await db_config.initialize()
        logger.info("Database initialized")
    except Exception as e:
        logger.warning(f"Database init skipped: {e}")
    yield
    try:
        await db_config.close()
        logger.info("Database connections closed")
    except Exception as e:
        logger.warning(f"Database close skipped: {e}")


app = FastAPI(
    title="PROJECT WARROOM API",
    description="AI-Powered Project Defense Platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Middleware — allow all origins, no credentials (avoids CORS spec violation)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Routers
from .routes.health import router as health_router
from .routes.projects import router as projects_router
from .routes.analysis import router as analysis_router
from .routes.simulation import router as simulation_router
from .routes.reports import router as reports_router
from .routes.competitive import router as competitive_router

app.include_router(health_router, tags=["Health"])
app.include_router(projects_router, prefix="/api/v1/projects", tags=["Projects"])
app.include_router(analysis_router, prefix="/api/v1/analysis", tags=["Analysis"])
app.include_router(simulation_router, prefix="/api/v1/simulation", tags=["Simulation"])
app.include_router(reports_router, prefix="/api/v1/reports", tags=["Reports"])
app.include_router(competitive_router, prefix="/api/v1/competitive", tags=["Competitive"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "PROJECT WARROOM",
        "version": "0.1.0",
        "status": "operational",
        "docs": "/docs",
    }
