"""
TestSession API routes.
"""

from fastapi import APIRouter, HTTPException, status

from aero_telemetry.models.test_session import TestSession
from aero_telemetry.storage.test_session import SQLiteTestSessionStorage


router = APIRouter()

_storage: SQLiteTestSessionStorage | None = None


def get_storage() -> SQLiteTestSessionStorage:
    global _storage
    if _storage is None:
        _storage = SQLiteTestSessionStorage()
    return _storage


@router.on_event("startup")
async def init_storage():
    storage = get_storage()
    await storage.init_db()


@router.post(
    "",
    response_model=TestSession,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new test session",
)
async def create_session(session: TestSession):
    storage = get_storage()
    existing = await storage.get(session.session_id)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Session '{session.session_id}' already exists",
        )
    return await storage.create(session)


@router.get(
    "/{session_id}",
    response_model=TestSession,
    summary="Get test session by ID",
)
async def get_session(session_id: str):
    storage = get_storage()
    session = await storage.get(session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found",
        )
    return session


@router.get(
    "",
    response_model=list[TestSession],
    summary="List test sessions",
)
async def list_sessions(skip: int = 0, limit: int = 100):
    storage = get_storage()
    return await storage.list(skip=skip, limit=limit)


@router.get(
    "/aircraft/{aircraft_id}",
    response_model=list[TestSession],
    summary="List sessions for an aircraft",
)
async def list_sessions_by_aircraft(aircraft_id: str, skip: int = 0, limit: int = 100):
    storage = get_storage()
    return await storage.list_by_aircraft(aircraft_id, skip=skip, limit=limit)


@router.put(
    "/{session_id}",
    response_model=TestSession,
    summary="Update test session",
)
async def update_session(session_id: str, session: TestSession):
    storage = get_storage()
    updated = await storage.update(session_id, session)
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found",
        )
    return updated


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete test session",
)
async def delete_session(session_id: str):
    storage = get_storage()
    deleted = await storage.delete(session_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found",
        )
    return None