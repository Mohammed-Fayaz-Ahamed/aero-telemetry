"""
Telemetry API routes.
Ingest and query telemetry points.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status, Query

from aero_telemetry.models.telemetry import TelemetryPoint
from aero_telemetry.storage.telemetry import SQLiteTelemetryStorage


router = APIRouter()

_storage: Optional[SQLiteTelemetryStorage] = None


def get_storage() -> SQLiteTelemetryStorage:
    global _storage
    if _storage is None:
        _storage = SQLiteTelemetryStorage()
    return _storage

@router.post(
    "",
    response_model=TelemetryPoint,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a single telemetry point",
)
async def ingest_telemetry(point: TelemetryPoint):
    """Ingest a single telemetry point."""
    storage = get_storage()
    return await storage.create(point)


@router.post(
    "/batch",
    response_model=List[TelemetryPoint],
    status_code=status.HTTP_201_CREATED,
    summary="Ingest multiple telemetry points",
)
async def ingest_telemetry_batch(points: List[TelemetryPoint]):
    """Ingest multiple telemetry points in one request."""
    storage = get_storage()
    results = []
    for point in points:
        created = await storage.create(point)
        results.append(created)
    return results


@router.get(
    "",
    response_model=List[TelemetryPoint],
    summary="Query telemetry points",
)
async def query_telemetry(
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    start_time: Optional[datetime] = Query(None, description="Start of time range (ISO 8601)"),
    end_time: Optional[datetime] = Query(None, description="End of time range (ISO 8601)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Query telemetry points with optional filters.
    
    Examples:
        - All points: GET /telemetry
        - By session: GET /telemetry?session_id=ts-001
        - Time range: GET /telemetry?start_time=2026-07-07T00:00:00&end_time=2026-07-08T00:00:00
    """
    storage = get_storage()
    return await storage.list(
        session_id=session_id,
        start_time=start_time,
        end_time=end_time,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{point_id}",
    response_model=TelemetryPoint,
    summary="Get telemetry point by ID",
)
async def get_telemetry_point(point_id: str):
    """Retrieve a specific telemetry point by its ID."""
    storage = get_storage()
    point = await storage.get(point_id)
    if point is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Telemetry point '{point_id}' not found",
        )
    return point


@router.delete(
    "/{point_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete telemetry point",
)
async def delete_telemetry_point(point_id: str):
    """Delete a telemetry point."""
    storage = get_storage()
    deleted = await storage.delete(point_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Telemetry point '{point_id}' not found",
        )
    return None