"""
FastAPI application factory for aero-telemetry.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from aero_telemetry.api import health
from aero_telemetry.api import aircraft as aircraft_api


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.
    Runs on startup (before yield) and shutdown (after yield).
    """
    # Startup
    print("Starting aero-telemetry server...")
    yield
    # Shutdown
    print("Shutting down aero-telemetry server...")


def create_app() -> FastAPI:
    """
    Factory function to create the FastAPI application.
    Allows test clients to create isolated app instances.
    """
    app = FastAPI(
        title="aero-telemetry",
        description="Lightweight telemetry ingestion for AAM prototyping",
        version="0.1.0",
        lifespan=lifespan,
    )
    
    # Register routers
    app.include_router(health.router, tags=["health"])
    app.include_router(aircraft_api.router, prefix="/aircraft", tags=["aircraft"])
    
    return app


# Global app instance for uvicorn
app = create_app()