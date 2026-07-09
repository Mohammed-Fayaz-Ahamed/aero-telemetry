"""
FastAPI application factory for aero-telemetry.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from aero_telemetry.api import health
from aero_telemetry.api import aircraft as aircraft_api
from aero_telemetry.api import test_session as test_session_api
from aero_telemetry.api import telemetry as telemetry_api
from aero_telemetry.storage.sqlite import SQLiteAircraftStorage
from aero_telemetry.storage.test_session import SQLiteTestSessionStorage
from aero_telemetry.storage.telemetry import SQLiteTelemetryStorage


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.
    Runs on startup (before yield) and shutdown (after yield).
    """
    # Startup
    print("Starting aero-telemetry server...")
    # Initialize all databases
    aircraft_storage = SQLiteAircraftStorage()
    await aircraft_storage.init_db()
    
    session_storage = SQLiteTestSessionStorage()
    await session_storage.init_db()
    
    telemetry_storage = SQLiteTelemetryStorage()
    await telemetry_storage.init_db()
    
    yield
    
    print("Shutting down aero-telemetry server...")
    await aircraft_storage.close()
    await session_storage.close()
    await telemetry_storage.close()
    yield
    # Shutdown
    print("Shutting down aero-telemetry server...")


def create_app() -> FastAPI:
    app = FastAPI(
        title="aero-telemetry",
        description="Lightweight telemetry ingestion for AAM prototyping",
        version="0.1.0",
        lifespan=lifespan,
    )
    
    # Register routers
    app.include_router(health.router, tags=["health"])
    app.include_router(aircraft_api.router, prefix="/aircraft", tags=["aircraft"])
    app.include_router(test_session_api.router, prefix="/test-sessions", tags=["test-sessions"])
    app.include_router(telemetry_api.router, prefix="/telemetry", tags=["telemetry"])
    return app


# Global app instance for uvicorn
app = create_app()