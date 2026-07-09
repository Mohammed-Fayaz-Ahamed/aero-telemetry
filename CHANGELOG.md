# Changelog

## [0.1.0] - 2026-07-09

### Added
- Aircraft model with validation (mass, propulsion type, MTOM)
- TestSession model with validation (test types, time ranges, status logic)
- TelemetryPoint model with nested sensor data (GPS, IMU, battery, motors, attitude)
- SQLite storage with async SQLAlchemy 2.0
- FastAPI CRUD endpoints for Aircraft, TestSession, Telemetry
- Batch telemetry ingestion endpoint
- Time-range and session-based telemetry queries
- Pydantic validation for aerospace-specific rules
- 26 pytest tests covering CRUD, validation, edge cases
- Example client scripts and sample payloads
- OpenAPI schema export

### Tech Stack
- Python 3.10+
- FastAPI
- Pydantic v2
- SQLAlchemy 2.0 + aiosqlite
- pytest + httpx
