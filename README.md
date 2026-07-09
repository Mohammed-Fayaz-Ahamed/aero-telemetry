# aero-telemetry

Lightweight telemetry ingestion and query API for aerospace prototyping.

Built for eVTOL, drone, and AAM developers who need a fast, zero-config way to capture flight test data.

## Features

- Ingest telemetry via HTTP - single points or batches
- Query by session, time range, or aircraft - filter what you need
- Pydantic validation - catch bad data before it hits your database
- SQLite by default - zero infrastructure, runs on a laptop
- FastAPI + async - modern Python, production-ready architecture

## Quick Start

### Clone and install

```bash
git clone https://github.com/Mohammed-Fayaz-Ahamed/aero-telemetry.git
cd aero-telemetry
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Run server

```bash
uvicorn aero_telemetry.main:app --reload
```

### Test health

```bash
curl http://localhost:8000/health
```

## Example Usage

### Create aircraft

```bash
curl -X POST http://localhost:8000/aircraft \
  -H "Content-Type: application/json" \
  -d '{"aircraft_id": "proto-001", "name": "Test eVTOL", "aircraft_type": "multicopter", "propulsion_type": "battery", "mass_kg": 850, "max_takeoff_mass_kg": 1200}'
```

### Create test session

```bash
curl -X POST http://localhost:8000/test-sessions \
  -H "Content-Type: application/json" \
  -d '{"session_id": "ts-001", "aircraft_id": "proto-001", "test_type": "hover", "test_objective": "Battery discharge test"}'
```

### Ingest telemetry

```bash
curl -X POST http://localhost:8000/telemetry \
  -H "Content-Type: application/json" \
  -d '{"session_id": "ts-001", "battery": {"voltage_v": 540.0, "current_a": 45.2, "soc_percent": 87.5, "temperature_c": 35.0}}'
```

### Query telemetry

```bash
curl "http://localhost:8000/telemetry?session_id=ts-001"
```

See `examples/client_example.py` for a full Python client.

## API Endpoints

### Health

- `GET /health` - Health check

### Aircraft

- `POST /aircraft` - Create aircraft
- `GET /aircraft/{id}` - Get aircraft
- `GET /aircraft` - List aircraft
- `PUT /aircraft/{id}` - Update aircraft
- `DELETE /aircraft/{id}` - Delete aircraft

### Test Sessions

- `POST /test-sessions` - Create session
- `GET /test-sessions/{id}` - Get session
- `GET /test-sessions` - List sessions
- `GET /test-sessions/aircraft/{id}` - List by aircraft
- `PUT /test-sessions/{id}` - Update session
- `DELETE /test-sessions/{id}` - Delete session

### Telemetry

- `POST /telemetry` - Ingest single point
- `POST /telemetry/batch` - Ingest batch
- `GET /telemetry` - Query telemetry
- `GET /telemetry/{id}` - Get point by ID
- `DELETE /telemetry/{id}` - Delete point

## Data Model

### Aircraft

Static configuration: mass, propulsion type, MTOM.

### TestSession

A single test event: hover, transition, endurance, etc. Linked to aircraft.

### TelemetryPoint

A sensor snapshot at a moment in time. Contains optional nested data:

- position - GPS (lat, lon, altitude)
- attitude - roll, pitch, yaw
- battery - voltage, current, SOC, temperature
- motors - array of motor states
- imu - accelerometer + gyroscope
- gps - fix quality, satellites, HDOP

## Validation

- Battery voltage > 10V (eVTOL pack detection)
- Motor count <= 12 (typical eVTOL limit)
- Coordinates in valid ranges
- MTOM >= empty mass
- End time > start time
- Completed status requires end time

## Running Tests

```bash
pytest -v
```

26 tests covering CRUD, validation, and query filters.

## Tech Stack

- Python 3.10+
- FastAPI
- Pydantic v2
- SQLAlchemy 2.0 + aiosqlite
- pytest + httpx

## License

Apache-2.0

## Author

Mohammed Fayaz Ahamed - Data Engineer