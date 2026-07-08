"""
Tests for TestSession API endpoints.
"""

import pytest
import httpx
from datetime import datetime, timedelta
import uuid
from aero_telemetry.main import create_app


@pytest.fixture
async def client():
    """Async HTTP client for testing."""
    app = create_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def aircraft(client):
    """Create aircraft for session tests."""
    payload = {
        "aircraft_id": "ses-ac-001",
        "name": "Session Test Aircraft",
        "aircraft_type": "multicopter",
        "propulsion_type": "battery",
        "mass_kg": 850.0,
        "max_takeoff_mass_kg": 1200.0,
    }
    await client.post("/aircraft", json=payload)
    return "ses-ac-001"


@pytest.mark.asyncio
async def test_create_session(client, aircraft):
    """Test creating a test session."""
    session_id = f"ses-{uuid.uuid4().hex[:8]}"
    payload = {
        "session_id": session_id,
        "aircraft_id": aircraft,
        "test_type": "hover",
        "test_objective": "Test session creation",
    }
    response = await client.post("/test-sessions", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["session_id"] == session_id
    assert data["status"] == "planned"


@pytest.mark.asyncio
async def test_create_session_duplicate(client, aircraft):
    """Test duplicate session returns 409."""
    payload = {
        "session_id": "ses-dup-001",
        "aircraft_id": aircraft,
        "test_type": "hover",
        "test_objective": "Duplicate test",
    }
    await client.post("/test-sessions", json=payload)
    
    response = await client.post("/test-sessions", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_session(client, aircraft):
    """Test retrieving a session."""
    payload = {
        "session_id": "ses-get-001",
        "aircraft_id": aircraft,
        "test_type": "hover",
        "test_objective": "Get test",
    }
    await client.post("/test-sessions", json=payload)
    
    response = await client.get("/test-sessions/ses-get-001")
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "ses-get-001"


@pytest.mark.asyncio
async def test_get_session_not_found(client):
    """Test 404 for non-existent session."""
    response = await client.get("/test-sessions/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_sessions(client, aircraft):
    """Test listing sessions."""
    response = await client.get("/test-sessions?skip=0&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_list_sessions_by_aircraft(client, aircraft):
    """Test listing sessions for specific aircraft."""
    payload = {
        "session_id": "ses-ac-001",
        "aircraft_id": aircraft,
        "test_type": "hover",
        "test_objective": "Aircraft filter test",
    }
    await client.post("/test-sessions", json=payload)
    
    response = await client.get(f"/test-sessions/aircraft/{aircraft}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["aircraft_id"] == aircraft


@pytest.mark.asyncio
async def test_update_session(client, aircraft):
    """Test updating a session."""
    payload = {
        "session_id": "ses-upd-001",
        "aircraft_id": aircraft,
        "test_type": "hover",
        "test_objective": "Original",
    }
    await client.post("/test-sessions", json=payload)
    
    payload["test_objective"] = "Updated"
    response = await client.put("/test-sessions/ses-upd-001", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["test_objective"] == "Updated"


@pytest.mark.asyncio
async def test_delete_session(client, aircraft):
    """Test deleting a session."""
    payload = {
        "session_id": "ses-del-001",
        "aircraft_id": aircraft,
        "test_type": "hover",
        "test_objective": "To delete",
    }
    await client.post("/test-sessions", json=payload)
    
    response = await client.delete("/test-sessions/ses-del-001")
    assert response.status_code == 204
    
    response = await client.get("/test-sessions/ses-del-001")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_session_end_before_start(client, aircraft):
    """Test validation: end_time before start_time."""
    now = datetime.now()
    payload = {
        "session_id": "ses-bad-001",
        "aircraft_id": aircraft,
        "test_type": "hover",
        "test_objective": "Bad times",
        "start_time": now.isoformat(),
        "end_time": (now - timedelta(hours=1)).isoformat(),
    }
    response = await client.post("/test-sessions", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_session_completed_without_end(client, aircraft):
    """Test validation: completed status without end_time."""
    payload = {
        "session_id": "ses-bad-002",
        "aircraft_id": aircraft,
        "test_type": "hover",
        "test_objective": "Bad status",
        "status": "completed",
    }
    response = await client.post("/test-sessions", json=payload)
    assert response.status_code == 422