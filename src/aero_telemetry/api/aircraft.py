"""
Aircraft API routes.
CRUD operations for aircraft configurations.
"""

from fastapi import APIRouter, HTTPException, status

from aero_telemetry.models.aircraft import Aircraft
from aero_telemetry.storage.sqlite import SQLiteAircraftStorage


router = APIRouter()

# Storage instance — in production, use dependency injection
_storage: SQLiteAircraftStorage | None = None


def get_storage() -> SQLiteAircraftStorage:
    """Lazy initialization of storage."""
    global _storage
    if _storage is None:
        _storage = SQLiteAircraftStorage()
    return _storage


@router.on_event("startup")
async def init_storage():
    """Initialize database on startup."""
    storage = get_storage()
    await storage.init_db()


@router.post(
    "",
    response_model=Aircraft,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new aircraft configuration",
)
async def create_aircraft(aircraft: Aircraft):
    """Create a new aircraft configuration."""
    storage = get_storage()
    existing = await storage.get(aircraft.aircraft_id)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Aircraft with id '{aircraft.aircraft_id}' already exists",
        )
    return await storage.create(aircraft)


@router.get(
    "/{aircraft_id}",
    response_model=Aircraft,
    summary="Get aircraft by ID",
)
async def get_aircraft(aircraft_id: str):
    """Retrieve an aircraft configuration by its ID."""
    storage = get_storage()
    aircraft = await storage.get(aircraft_id)
    if aircraft is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aircraft '{aircraft_id}' not found",
        )
    return aircraft


@router.get(
    "",
    response_model=list[Aircraft],
    summary="List all aircraft configurations",
)
async def list_aircraft(skip: int = 0, limit: int = 100):
    """List aircraft configurations with pagination."""
    storage = get_storage()
    return await storage.list(skip=skip, limit=limit)


@router.put(
    "/{aircraft_id}",
    response_model=Aircraft,
    summary="Update aircraft configuration",
)
async def update_aircraft(aircraft_id: str, aircraft: Aircraft):
    """Update an existing aircraft configuration."""
    storage = get_storage()
    updated = await storage.update(aircraft_id, aircraft)
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aircraft '{aircraft_id}' not found",
        )
    return updated


@router.delete(
    "/{aircraft_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete aircraft configuration",
)
async def delete_aircraft(aircraft_id: str):
    """Delete an aircraft configuration."""
    storage = get_storage()
    deleted = await storage.delete(aircraft_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aircraft '{aircraft_id}' not found",
        )
    return None