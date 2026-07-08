"""
Tests for Aircraft API endpoints.
"""

import pytest
import httpx
from aero_telemetry.main import create_app


@pytest.fixture
async def client():
    """Async HTTP client for testing."""
    app = create_app()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_check(client):
    """Test health endpoint returns OK."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "aero-telemetry"


@pytest.mark.asyncio
async def test_create_aircraft(client):
    """Test creating an aircraft."""
    payload = {
        "aircraft_id": "test-001",
        "name": "Test Aircraft",
        "aircraft_type": "multicopter",
        "propulsion_type": "battery",
        "mass_kg": 850.0,
        "max_takeoff_mass_kg": 1200.0,
    }
    response = await client.post("/aircraft", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["aircraft_id"] == "test-001"
    assert data["name"] == "Test Aircraft"


@pytest.mark.asyncio
async def test_create_aircraft_duplicate(client):
    """Test creating duplicate aircraft returns 409."""
    payload = {
        "aircraft_id": "dup-001",
        "name": "Duplicate",
        "aircraft_type": "multicopter",
        "propulsion_type": "battery",
        "mass_kg": 900.0,
        "max_takeoff_mass_kg": 1300.0,
    }
    # First creation
    response = await client.post("/aircraft", json=payload)
    assert response.status_code == 201
    
    # Duplicate
    response = await client.post("/aircraft", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_aircraft(client):
    """Test retrieving an aircraft."""
    # Create first
    payload = {
        "aircraft_id": "get-001",
        "name": "Get Test",
        "aircraft_type": "multicopter",
        "propulsion_type": "battery",
        "mass_kg": 800.0,
        "max_takeoff_mass_kg": 1100.0,
    }
    await client.post("/aircraft", json=payload)
    
    # Get
    response = await client.get("/aircraft/get-001")
    assert response.status_code == 200
    data = response.json()
    assert data["aircraft_id"] == "get-001"


@pytest.mark.asyncio
async def test_get_aircraft_not_found(client):
    """Test 404 for non-existent aircraft."""
    response = await client.get("/aircraft/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_aircraft(client):
    """Test listing aircraft."""
    response = await client.get("/aircraft?skip=0&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_update_aircraft(client):
    """Test updating an aircraft."""
    # Create
    payload = {
        "aircraft_id": "upd-001",
        "name": "Original",
        "aircraft_type": "multicopter",
        "propulsion_type": "battery",
        "mass_kg": 850.0,
        "max_takeoff_mass_kg": 1200.0,
    }
    await client.post("/aircraft", json=payload)
    
    # Update
    payload["name"] = "Updated"
    response = await client.put("/aircraft/upd-001", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated"


@pytest.mark.asyncio
async def test_delete_aircraft(client):
    """Test deleting an aircraft."""
    # Create
    payload = {
        "aircraft_id": "del-001",
        "name": "To Delete",
        "aircraft_type": "multicopter",
        "propulsion_type": "battery",
        "mass_kg": 850.0,
        "max_takeoff_mass_kg": 1200.0,
    }
    await client.post("/aircraft", json=payload)
    
    # Delete
    response = await client.delete("/aircraft/del-001")
    assert response.status_code == 204
    
    # Verify gone
    response = await client.get("/aircraft/del-001")
    assert response.status_code == 404