"""PROJECT WARROOM FastAPI Application"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from .routes.projects import router as projects_router
from .routes.analysis import router as analysis_router
from .routes.simulation import router as simulation_router
from .routes.reports import router as reports_router
from .routes.competitive import router as competitive_router
from .routes.health import router as health_router

app = FastAPI(
    title="PROJECT WARROOM API",
    description="AI-Powered Project Defense Platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Routers
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
