"""
SQLite storage for TestSession entities.
"""

from datetime import datetime
from typing import List
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy import select, delete as sql_delete

from aero_telemetry.models.test_session import TestSession
from aero_telemetry.storage.sqlite import Base, SQLiteAircraftStorage  # Reuse Base


class TestSessionORM(Base):
    __tablename__ = "test_sessions"
    
    session_id = Column(String(64), primary_key=True)
    aircraft_id = Column(String(64), nullable=False, index=True)
    test_type = Column(String(32), nullable=False)
    test_objective = Column(Text, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    status = Column(String(16), nullable=False, default="planned")
    location_name = Column(String(128), nullable=True)
    notes = Column(Text, nullable=True)
    
    def to_model(self) -> TestSession:
        return TestSession(
            session_id=self.session_id,
            aircraft_id=self.aircraft_id,
            test_type=self.test_type,
            test_objective=self.test_objective,
            start_time=self.start_time,
            end_time=self.end_time,
            status=self.status,
            location_name=self.location_name,
            notes=self.notes,
        )
    
    @classmethod
    def from_model(cls, session: TestSession) -> "TestSessionORM":
        return cls(
            session_id=session.session_id,
            aircraft_id=session.aircraft_id,
            test_type=session.test_type,
            test_objective=session.test_objective,
            start_time=session.start_time,
            end_time=session.end_time,
            status=session.status,
            location_name=session.location_name,
            notes=session.notes,
        )


class SQLiteTestSessionStorage:
    """
    SQLite storage for TestSession.
    Uses same engine as Aircraft storage (shared database).
    """
    
    def __init__(self, database_url: str = "sqlite+aiosqlite:///./aero_telemetry.db"):
        # Reuse engine from Aircraft storage or create shared one
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        self.engine = create_async_engine(database_url, echo=False)
        self.async_session = async_sessionmaker(self.engine, expire_on_commit=False)
    
    async def init_db(self):
        """Create tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def create(self, session: TestSession) -> TestSession:
        async with self.async_session() as db:
            orm = TestSessionORM.from_model(session)
            db.add(orm)
            await db.commit()
            return session
    
    async def get(self, session_id: str) -> TestSession | None:
        async with self.async_session() as db:
            result = await db.execute(
                select(TestSessionORM).where(TestSessionORM.session_id == session_id)
            )
            orm = result.scalar_one_or_none()
            return orm.to_model() if orm else None
    
    async def list(self, skip: int = 0, limit: int = 100) -> List[TestSession]:
        async with self.async_session() as db:
            result = await db.execute(
                select(TestSessionORM).offset(skip).limit(limit)
            )
            return [orm.to_model() for orm in result.scalars().all()]
    
    async def update(self, session_id: str, session: TestSession) -> TestSession | None:
        async with self.async_session() as db:
            result = await db.execute(
                select(TestSessionORM).where(TestSessionORM.session_id == session_id)
            )
            existing = result.scalar_one_or_none()
            if existing is None:
                return None
            
            existing.aircraft_id = session.aircraft_id
            existing.test_type = session.test_type
            existing.test_objective = session.test_objective
            existing.start_time = session.start_time
            existing.end_time = session.end_time
            existing.status = session.status
            existing.location_name = session.location_name
            existing.notes = session.notes
            
            await db.commit()
            return session
    
    async def delete(self, session_id: str) -> bool:
        async with self.async_session() as db:
            result = await db.execute(
                select(TestSessionORM).where(TestSessionORM.session_id == session_id)
            )
            existing = result.scalar_one_or_none()
            if existing is None:
                return False
            
            await db.delete(existing)
            await db.commit()
            return True
    
    async def list_by_aircraft(self, aircraft_id: str, skip: int = 0, limit: int = 100) -> List[TestSession]:
        """List sessions for a specific aircraft."""
        async with self.async_session() as db:
            result = await db.execute(
                select(TestSessionORM)
                .where(TestSessionORM.aircraft_id == aircraft_id)
                .offset(skip)
                .limit(limit)
            )
            return [orm.to_model() for orm in result.scalars().all()]
    
    async def close(self):
        await self.engine.dispose()