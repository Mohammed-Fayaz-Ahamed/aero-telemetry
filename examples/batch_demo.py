"""
Batch telemetry demo.
Shows battery degradation over a simulated flight.
"""

import httpx
import json
import time


BASE_URL = "http://localhost:8000"


def setup():
    """Create aircraft and session for demo."""
    # Aircraft
    aircraft = {
        "aircraft_id": "batch-demo-ac",
        "name": "Batch Demo Aircraft",
        "aircraft_type": "multicopter",
        "propulsion_type": "battery",
        "mass_kg": 850.0,
        "max_takeoff_mass_kg": 1200.0,
    }
    r = httpx.post(f"{BASE_URL}/aircraft", json=aircraft)
    print(f"Create aircraft: {r.status_code}")
    
    # Session
    session = {
        "session_id": "batch-demo-ses",
        "aircraft_id": "batch-demo-ac",
        "test_type": "endurance",
        "test_objective": "Battery degradation over 5-minute hover",
    }
    r = httpx.post(f"{BASE_URL}/test-sessions", json=session)
    print(f"Create session: {r.status_code}")


def ingest_batch():
    """Ingest 5 telemetry points showing battery degradation."""
    points = [
        {
            "session_id": "batch-demo-ses",
            "battery": {"voltage_v": 540.0, "current_a": 45.0, "soc_percent": 90.0, "temperature_c": 30.0},
        },
        {
            "session_id": "batch-demo-ses",
            "battery": {"voltage_v": 535.0, "current_a": 46.0, "soc_percent": 85.0, "temperature_c": 32.0},
        },
        {
            "session_id": "batch-demo-ses",
            "battery": {"voltage_v": 530.0, "current_a": 47.0, "soc_percent": 80.0, "temperature_c": 34.0},
        },
        {
            "session_id": "batch-demo-ses",
            "battery": {"voltage_v": 525.0, "current_a": 48.0, "soc_percent": 75.0, "temperature_c": 36.0},
        },
        {
            "session_id": "batch-demo-ses",
            "battery": {"voltage_v": 520.0, "current_a": 50.0, "soc_percent": 70.0, "temperature_c": 38.0},
        },
    ]
    
    r = httpx.post(f"{BASE_URL}/telemetry/batch", json=points)
    print(f"Batch ingest: {r.status_code}")
    data = r.json()
    print(f"Ingested {len(data)} points")
    return data


def query_and_analyze():
    """Query telemetry and show battery trend."""
    r = httpx.get(f"{BASE_URL}/telemetry?session_id=batch-demo-ses")
    print(f"\nQuery: {r.status_code}")
    points = r.json()
    
    print(f"\nTotal points: {len(points)}")
    print("\nBattery degradation trend:")
    print("-" * 40)
    print(f"{'Point':<10} {'Voltage':<10} {'SOC %':<10} {'Temp C':<10}")
    print("-" * 40)
    
    for i, p in enumerate(points):
        b = p["battery"]
        print(f"{i+1:<10} {b['voltage_v']:<10.1f} {b['soc_percent']:<10.1f} {b['temperature_c']:<10.1f}")
    
    # Calculate stats
    voltages = [p["battery"]["voltage_v"] for p in points]
    socs = [p["battery"]["soc_percent"] for p in points]
    
    print("-" * 40)
    print(f"Voltage drop: {voltages[0] - voltages[-1]:.1f}V")
    print(f"SOC drop: {socs[0] - socs[-1]:.1f}%")


if __name__ == "__main__":
    print("=== Batch Telemetry Demo ===\n")
    
    # Check server
    try:
        httpx.get(f"{BASE_URL}/health")
    except httpx.ConnectError:
        print("ERROR: Server not running")
        exit(1)
    
    setup()
    ingest_batch()
    query_and_analyze()
    
    print("\n=== Demo complete ===")