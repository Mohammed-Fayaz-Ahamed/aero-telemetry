"""
Tests for Telemetry API endpoints.
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


@pytest.fixture
async def aircraft_and_session(client):
    """Create aircraft and test session for telemetry tests."""
    aircraft = {
        "aircraft_id": "tel-ac-001",
        "name": "Telemetry Test Aircraft",
        "aircraft_type": "multicopter",
        "propulsion_type": "battery",
        "mass_kg": 850.0,
        "max_takeoff_mass_kg": 1200.0,
    }
    await client.post("/aircraft", json=aircraft)
    
    session = {
        "session_id": "tel-ses-001",
        "aircraft_id": "tel-ac-001",
        "test_type": "hover",
        "test_objective": "Telemetry validation test",
    }
    await client.post("/test-sessions", json=session)
    
    return {"aircraft_id": "tel-ac-001", "session_id": "tel-ses-001"}


@pytest.mark.asyncio
async def test_ingest_telemetry_battery_only(client, aircraft_and_session):
    """Test ingesting battery-only telemetry."""
    payload = {
        "session_id": aircraft_and_session["session_id"],
        "battery": {
            "voltage_v": 540.0,
            "current_a": 45.2,
            "soc_percent": 87.5,
            "temperature_c": 35.0,
        },
    }
    response = await client.post("/telemetry", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["session_id"] == aircraft_and_session["session_id"]
    assert data["battery"]["voltage_v"] == 540.0
    assert data["point_id"] is not None


@pytest.mark.asyncio
async def test_ingest_telemetry_full(client, aircraft_and_session):
    """Test ingesting full telemetry with all fields."""
    payload = {
        "session_id": aircraft_and_session["session_id"],
        "position": {"latitude": 17.4065, "longitude": 78.4772, "altitude_msl_m": 542.0},
        "attitude": {"roll": 2.5, "pitch": -1.0, "yaw": 95.0},
        "battery": {"voltage_v": 538.5, "current_a": 120.0, "soc_percent": 72.0, "temperature_c": 42.0},
        "motors": [
            {"motor_id": "M1", "rpm": 1850, "current_a": 28.5, "temperature_c": 55.0},
            {"motor_id": "M2", "rpm": 1860, "current_a": 29.0, "temperature_c": 56.0},
        ],
        "imu": {"accel_x_ms2": 0.2, "accel_y_ms2": -0.1, "accel_z_ms2": 9.8, "gyro_x_dps": 0.5, "gyro_y_dps": -0.3, "gyro_z_dps": 0.1},
        "gps": {"fix_type": "3d", "satellites": 12, "hdop": 1.2},
    }
    response = await client.post("/telemetry", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["position"]["latitude"] == 17.4065
    assert len(data["motors"]) == 2


@pytest.mark.asyncio
async def test_ingest_telemetry_batch(client, aircraft_and_session):
    """Test batch telemetry ingestion."""
    payload = [
        {
            "session_id": aircraft_and_session["session_id"],
            "battery": {"voltage_v": 520.0, "current_a": 50.0, "soc_percent": 80.0, "temperature_c": 36.0},
        },
        {
            "session_id": aircraft_and_session["session_id"],
            "battery": {"voltage_v": 510.0, "current_a": 55.0, "soc_percent": 75.0, "temperature_c": 37.0},
        },
    ]
    response = await client.post("/telemetry/batch", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_query_telemetry_by_session(client, aircraft_and_session):
    """Test querying telemetry by session ID."""
    # Ingest first
    payload = {
        "session_id": aircraft_and_session["session_id"],
        "battery": {"voltage_v": 500.0, "current_a": 60.0, "soc_percent": 70.0, "temperature_c": 40.0},
    }
    await client.post("/telemetry", json=payload)
    
    # Query
    response = await client.get(f"/telemetry?session_id={aircraft_and_session['session_id']}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["session_id"] == aircraft_and_session["session_id"]


@pytest.mark.asyncio
async def test_query_telemetry_time_range(client, aircraft_and_session):
    """Test querying telemetry by time range."""
    # Ingest
    payload = {
        "session_id": aircraft_and_session["session_id"],
        "battery": {"voltage_v": 490.0, "current_a": 65.0, "soc_percent": 65.0, "temperature_c": 41.0},
    }
    await client.post("/telemetry", json=payload)
    
    # Query with broad time range
    response = await client.get("/telemetry?start_time=2026-01-01T00:00:00&end_time=2026-12-31T23:59:59")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_ingest_telemetry_validation_battery_low(client, aircraft_and_session):
    """Test that low battery voltage is rejected."""
    payload = {
        "session_id": aircraft_and_session["session_id"],
        "battery": {"voltage_v": 3.7, "current_a": 0, "soc_percent": 50, "temperature_c": 25},
    }
    response = await client.post("/telemetry", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_ingest_telemetry_validation_too_many_motors(client, aircraft_and_session):
    """Test that too many motors are rejected."""
    motors = [{"motor_id": f"M{i}", "rpm": 1000, "current_a": 10, "temperature_c": 30} for i in range(20)]
    payload = {
        "session_id": aircraft_and_session["session_id"],
        "motors": motors,
    }
    response = await client.post("/telemetry", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_telemetry_point_not_found(client):
    """Test 404 for non-existent telemetry point."""
    response = await client.get("/telemetry/nonexistent-id")
    assert response.status_code == 404