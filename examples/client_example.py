"""
Example client for aero-telemetry API.
Demonstrates creating aircraft, sessions, and ingesting telemetry.
"""

import httpx
import json


BASE_URL = "http://localhost:8000"


def create_aircraft():
    """Create a sample aircraft."""
    payload = {
        "aircraft_id": "demo-ac-001",
        "name": "Demo eVTOL",
        "aircraft_type": "multicopter",
        "propulsion_type": "battery",
        "mass_kg": 850.0,
        "max_takeoff_mass_kg": 1200.0,
    }
    response = httpx.post(f"{BASE_URL}/aircraft", json=payload)
    print(f"Create aircraft: {response.status_code}")
    return response.json() if response.status_code == 201 else None


def create_session(aircraft_id: str):
    """Create a test session."""
    payload = {
        "session_id": "demo-ses-001",
        "aircraft_id": aircraft_id,
        "test_type": "hover",
        "test_objective": "Demo flight test",
    }
    response = httpx.post(f"{BASE_URL}/test-sessions", json=payload)
    print(f"Create session: {response.status_code}")
    return response.json() if response.status_code == 201 else None


def ingest_telemetry(session_id: str):
    """Ingest sample telemetry."""
    payload = {
        "session_id": session_id,
        "position": {"latitude": 17.4065, "longitude": 78.4772, "altitude_msl_m": 542.0},
        "attitude": {"roll": 0.0, "pitch": 0.0, "yaw": 0.0},
        "battery": {"voltage_v": 540.0, "current_a": 45.0, "soc_percent": 95.0, "temperature_c": 30.0},
        "motors": [
            {"motor_id": "M1", "rpm": 0, "current_a": 0.5, "temperature_c": 25.0},
            {"motor_id": "M2", "rpm": 0, "current_a": 0.5, "temperature_c": 25.0},
            {"motor_id": "M3", "rpm": 0, "current_a": 0.5, "temperature_c": 25.0},
            {"motor_id": "M4", "rpm": 0, "current_a": 0.5, "temperature_c": 25.0},
        ],
        "imu": {"accel_x_ms2": 0.0, "accel_y_ms2": 0.0, "accel_z_ms2": 9.8, "gyro_x_dps": 0.0, "gyro_y_dps": 0.0, "gyro_z_dps": 0.0},
        "gps": {"fix_type": "3d", "satellites": 8, "hdop": 1.5},
    }
    response = httpx.post(f"{BASE_URL}/telemetry", json=payload)
    print(f"Ingest telemetry: {response.status_code}")
    return response.json() if response.status_code == 201 else None


def query_telemetry(session_id: str):
    """Query telemetry for a session."""
    response = httpx.get(f"{BASE_URL}/telemetry?session_id={session_id}")
    print(f"Query telemetry: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Found {len(data)} points")
        return data
    return None


if __name__ == "__main__":
    print("=== Aero-Telemetry Demo Client ===\n")
    
    # Ensure server is running
    try:
        health = httpx.get(f"{BASE_URL}/health")
        print(f"Server health: {health.json()}\n")
    except httpx.ConnectError:
        print("ERROR: Server not running. Start with: uvicorn aero_telemetry.main:app --reload")
        exit(1)
    
    # Create aircraft
    aircraft = create_aircraft()
    if not aircraft:
        print("Aircraft may already exist, continuing...")
    
    # Create session
    session = create_session("demo-ac-001")
    if not session:
        print("Session may already exist, continuing...")
    
    # Ingest telemetry
    point = ingest_telemetry("demo-ses-001")
    if point:
        print(f"Point ID: {point['point_id']}")
        print(f"Battery SOC: {point['battery']['soc_percent']}%\n")
    
    # Query back
    points = query_telemetry("demo-ses-001")
    if points:
        print("First point battery voltage:", points[0]["battery"]["voltage_v"])
    
    print("\n=== Demo complete ===")