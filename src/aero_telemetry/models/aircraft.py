"""
Aircraft configuration model.
Static data: what the aircraft is, not what it's doing.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Literal


class Aircraft(BaseModel):
    """
    Represents a single aircraft configuration.
    
    Example:
        >>> aircraft = Aircraft(
        ...     aircraft_id="comp-proto-001",
        ...     name="comp Hop Battery Variant",
        ...     aircraft_type="multicopter",
        ...     propulsion_type="battery",
        ...     mass_kg=850.0,
        ...     max_takeoff_mass_kg=1200.0,
        ... )
    """
    
    aircraft_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Unique identifier for this aircraft configuration",
        examples=["comp-proto-001"],
    )
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Human-readable name",
        examples=["comp Hop Battery Variant"],
    )
    
    aircraft_type: Literal["multicopter", "fixed_wing", "tiltrotor", "lift_cruise"] = Field(
        ...,
        description="Airframe configuration",
    )
    
    propulsion_type: Literal["battery", "hydrogen", "hybrid", "turboshaft"] = Field(
        ...,
        description="Primary energy source",
    )
    
    mass_kg: float = Field(
        ...,
        gt=0,
        le=10000,
        description="Empty mass in kilograms",
    )
    
    max_takeoff_mass_kg: float = Field(
        ...,
        gt=0,
        le=20000,
        description="Maximum takeoff mass in kilograms",
    )
    
    @field_validator("max_takeoff_mass_kg")
    @classmethod
    def max_mass_greater_than_empty(cls, v: float, info) -> float:
        """MTOM must be greater than or equal to empty mass."""
        empty_mass = info.data.get("mass_kg")
        if empty_mass is not None and v < empty_mass:
            raise ValueError(
                f"max_takeoff_mass_kg ({v}) must be >= mass_kg ({empty_mass})"
            )
        return v
    
    def payload_capacity_kg(self) -> float:
        """Maximum payload = MTOM - empty mass."""
        return self.max_takeoff_mass_kg - self.mass_kg


# --- Test it right here ---
if __name__ == "__main__":
    # Valid aircraft
    ac = Aircraft(
        aircraft_id="comp-proto-001",
        name="comp Hop Battery Variant",
        aircraft_type="multicopter",
        propulsion_type="battery",
        mass_kg=850.0,
        max_takeoff_mass_kg=1200.0,
    )
    print(f"Created: {ac.name}")
    print(f"Payload capacity: {ac.payload_capacity_kg()} kg")
    print(f"JSON export:\n{ac.model_dump_json(indent=2)}")
    
    # Invalid: MTOM < empty mass
    print("\n--- Testing validation ---")
    try:
        bad = Aircraft(
            aircraft_id="bad-001",
            name="Bad Config",
            aircraft_type="multicopter",
            propulsion_type="battery",
            mass_kg=1000.0,
            max_takeoff_mass_kg=500.0,
        )
    except ValueError as e:
        print(f"Caught expected error: {e}")
    
    # Invalid: negative mass
    print("\n--- Testing negative mass ---")
    try:
        bad2 = Aircraft(
            aircraft_id="bad-002",
            name="Negative Mass",
            aircraft_type="multicopter",
            propulsion_type="battery",
            mass_kg=-100.0,
            max_takeoff_mass_kg=500.0,
        )
    except ValueError as e:
        print(f"Caught expected error: {e}")