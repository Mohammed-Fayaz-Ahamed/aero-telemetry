"""
Test session model.
A test session is a single ground test or flight test event.
All telemetry points belong to a test session.
"""

from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from typing import Literal


class TestSession(BaseModel):
    """
    Represents a single test session (ground test or flight test).
    
    Example:
        >>> session = TestSession(
        ...     session_id="ts-20240706-001",
        ...     aircraft_id="comp-proto-001",
        ...     test_type="hover",
        ...     test_objective="Validate battery discharge profile at 80% load",
        ...     start_time=datetime.now(),
        ... )
    """
    
    session_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Unique identifier for this test session",
        examples=["ts-20240706-001"],
    )
    
    aircraft_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Reference to Aircraft.aircraft_id",
        examples=["comp-proto-001"],
    )
    
    test_type: Literal[
        "ground_spin",
        "tethered_hover",
        "hover",
        "transition",
        "cruise",
        "landing",
        "endurance",
        "payload",
        "emergency",
    ] = Field(
        ...,
        description="Category of test being performed",
    )
    
    test_objective: str = Field(
        ...,
        min_length=1,
        max_length=512,
        description="What this test aims to validate or measure",
        examples=["Validate battery discharge profile at 80% load"],
    )
    
    start_time: datetime = Field(
        default_factory=datetime.now,
        description="When the test session started",
    )
    
    end_time: datetime | None = Field(
        default=None,
        description="When the test session ended. Null until completed.",
    )
    
    status: Literal["planned", "active", "completed", "aborted"] = Field(
        default="planned",
        description="Current state of the test session",
    )
    
    location_name: str | None = Field(
        default=None,
        max_length=128,
        description="Human-readable location (e.g., 'Hyderabad Test Facility')",
    )
    
    notes: str | None = Field(
        default=None,
        max_length=2048,
        description="Free-form notes from test engineers",
    )
    
    @field_validator("end_time")
    @classmethod
    def end_after_start(cls, v: datetime | None, info) -> datetime | None:
        """End time must be after start time, if provided."""
        if v is None:
            return v
        start = info.data.get("start_time")
        if start is not None and v <= start:
            raise ValueError(f"end_time ({v}) must be after start_time ({start})")
        return v
    
    @field_validator("status")
    @classmethod
    def status_logic(cls, v: str, info) -> str:
        """Completed/aborted status requires end_time."""
        if v in ("completed", "aborted"):
            end = info.data.get("end_time")
            if end is None:
                raise ValueError(f"status '{v}' requires end_time to be set")
        return v
    
    def duration_seconds(self) -> float | None:
        """Calculate duration if session has ended."""
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time).total_seconds()


# --- Test it ---
if __name__ == "__main__":
    from datetime import timedelta
    
    # Valid: planned session
    s1 = TestSession(
        session_id="ts-001",
        aircraft_id="comp-proto-001",
        test_type="hover",
        test_objective="Battery discharge at 80% load",
    )
    print(f"Created session: {s1.session_id}, status={s1.status}")
    print(f"Duration: {s1.duration_seconds()} (not ended yet)")
    print(f"JSON:\n{s1.model_dump_json(indent=2)}")
    
    # Valid: completed session
    now = datetime.now()
    s2 = TestSession(
        session_id="ts-002",
        aircraft_id="comp-proto-001",
        test_type="transition",
        test_objective="Tilt mechanism validation",
        start_time=now,
        end_time=now + timedelta(minutes=15),
        status="completed",
        location_name="Hyderabad Test Facility",
    )
    print(f"\nCompleted session: {s2.session_id}")
    print(f"Duration: {s2.duration_seconds()} seconds")
    
    # Invalid: end before start
    print("\n--- Testing end before start ---")
    try:
        bad = TestSession(
            session_id="ts-bad",
            aircraft_id="comp-proto-001",
            test_type="hover",
            test_objective="Bad test",
            start_time=now,
            end_time=now - timedelta(hours=1),
        )
    except ValueError as e:
        print(f"Caught: {e}")
    
    # Invalid: completed without end_time
    print("\n--- Testing completed without end_time ---")
    try:
        bad2 = TestSession(
            session_id="ts-bad2",
            aircraft_id="comp-proto-001",
            test_type="hover",
            test_objective="Bad test",
            status="completed",
        )
    except ValueError as e:
        print(f"Caught: {e}")