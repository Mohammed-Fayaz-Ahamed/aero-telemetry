"""
SQLite storage implementation.
Uses SQLAlchemy 2.0 with aiosqlite for async support.
"""

from datetime import datetime
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Float,
    DateTime,
    JSON,
    select,
    delete as sql_delete,
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from typing import Type

from aero_telemetry.models.aircraft import Aircraft
from aero_telemetry.models.test_session import TestSession
from aero_telemetry.models.telemetry import TelemetryPoint
from aero_telemetry.storage.base import Storage


Base = declarative_base()


class AircraftORM(Base):
    __tablename__ = "aircraft"
    
    aircraft_id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False)
    aircraft_type = Column(String(32), nullable=False)
    propulsion_type = Column(String(32), nullable=False)
    mass_kg = Column(Float, nullable=False)
    max_takeoff_mass_kg = Column(Float, nullable=False)
    
    def to_model(self) -> Aircraft:
        return Aircraft(
            aircraft_id=self.aircraft_id,
            name=self.name,
            aircraft_type=self.aircraft_type,
            propulsion_type=self.propulsion_type,
            mass_kg=self.mass_kg,
            max_takeoff_mass_kg=self.max_takeoff_mass_kg,
        )
    
    @classmethod
    def from_model(cls, aircraft: Aircraft) -> "AircraftORM":
        return cls(
            aircraft_id=aircraft.aircraft_id,
            name=aircraft.name,
            aircraft_type=aircraft.aircraft_type,
            propulsion_type=aircraft.propulsion_type,
            mass_kg=aircraft.mass_kg,
            max_takeoff_mass_kg=aircraft.max_takeoff_mass_kg,
        )


class SQLiteAircraftStorage(Storage[Aircraft]):
    """
    SQLite storage for Aircraft entities.
    
    Usage:
        storage = SQLiteAircraftStorage("sqlite+aiosqlite:///./aero_telemetry.db")
        await storage.create(aircraft)
    """
    
    def __init__(self, database_url: str = "sqlite+aiosqlite:///./aero_telemetry.db"):
        self.engine = create_async_engine(database_url, echo=False)
        self.async_session = async_sessionmaker(self.engine, expire_on_commit=False)
    
    async def init_db(self):
        """Create tables. Call once at startup."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def create(self, aircraft: Aircraft) -> Aircraft:
        async with self.async_session() as session:
            orm = AircraftORM.from_model(aircraft)
            session.add(orm)
            await session.commit()
            return aircraft  # No server-generated fields, so return as-is
    
    async def get(self, aircraft_id: str) -> Aircraft | None:
        async with self.async_session() as session:
            result = await session.execute(
                select(AircraftORM).where(AircraftORM.aircraft_id == aircraft_id)
            )
            orm = result.scalar_one_or_none()
            return orm.to_model() if orm else None
    
    async def list(self, skip: int = 0, limit: int = 100) -> list[Aircraft]:
        async with self.async_session() as session:
            result = await session.execute(
                select(AircraftORM).offset(skip).limit(limit)
            )
            return [orm.to_model() for orm in result.scalars().all()]
    
    async def update(self, aircraft_id: str, aircraft: Aircraft) -> Aircraft | None:
        async with self.async_session() as session:
            result = await session.execute(
                select(AircraftORM).where(AircraftORM.aircraft_id == aircraft_id)
            )
            existing = result.scalar_one_or_none()
            if existing is None:
                return None
            
            existing.name = aircraft.name
            existing.aircraft_type = aircraft.aircraft_type
            existing.propulsion_type = aircraft.propulsion_type
            existing.mass_kg = aircraft.mass_kg
            existing.max_takeoff_mass_kg = aircraft.max_takeoff_mass_kg
            
            await session.commit()
            return aircraft
    
    async def delete(self, aircraft_id: str) -> bool:
        async with self.async_session() as session:
            result = await session.execute(
                select(AircraftORM).where(AircraftORM.aircraft_id == aircraft_id)
            )
            existing = result.scalar_one_or_none()
            if existing is None:
                return False
            
            await session.delete(existing)
            await session.commit()
            return True
    
    async def close(self):
        await self.engine.dispose()


# --- Test it ---
if __name__ == "__main__":
    import asyncio
    
    async def test():
        storage = SQLiteAircraftStorage("sqlite+aiosqlite:///./test_aircraft.db")
        await storage.init_db()
        
        # Create
        ac = Aircraft(
            aircraft_id="bluj-test-001",
            name="Test Aircraft",
            aircraft_type="multicopter",
            propulsion_type="battery",
            mass_kg=900.0,
            max_takeoff_mass_kg=1300.0,
        )
        created = await storage.create(ac)
        print(f"Created: {created.aircraft_id}")
        
        # Get
        retrieved = await storage.get("bluj-test-001")
        print(f"Retrieved: {retrieved.name if retrieved else 'NOT FOUND'}")
        
        # List
        all_ac = await storage.list()
        print(f"Listed: {len(all_ac)} aircraft")
        
        # Update
        ac.name = "Updated Name"
        updated = await storage.update("bluj-test-001", ac)
        print(f"Updated: {updated.name if updated else 'FAILED'}")
        
        # Delete
        deleted = await storage.delete("bluj-test-001")
        print(f"Deleted: {deleted}")
        
        # Verify deletion
        gone = await storage.get("bluj-test-001")
        print(f"After delete: {'FOUND' if gone else 'NOT FOUND'}")
        
        await storage.close()
    
    asyncio.run(test())