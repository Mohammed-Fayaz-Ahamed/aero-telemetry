"""
SQLite storage for TelemetryPoint entities.
"""

import json
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, String, DateTime, JSON, Float, Integer
from sqlalchemy import select, delete as sql_delete

from aero_telemetry.models.telemetry import (
    TelemetryPoint,
    GeoPoint,
    Attitude,
    BatteryState,
    MotorState,
    IMUState,
    GPSState,
)
from aero_telemetry.storage.sqlite import Base


class TelemetryPointORM(Base):
    __tablename__ = "telemetry_points"
    
    point_id = Column(String(64), primary_key=True)
    session_id = Column(String(64), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    received_at = Column(DateTime, nullable=False, default=datetime.now)
    
    # Nested models stored as JSON
    position = Column(JSON, nullable=True)
    attitude = Column(JSON, nullable=True)
    battery = Column(JSON, nullable=True)
    motors = Column(JSON, nullable=True)
    imu = Column(JSON, nullable=True)
    gps = Column(JSON, nullable=True)
    
    def to_model(self) -> TelemetryPoint:
        """Reconstruct Pydantic model from ORM."""
        return TelemetryPoint(
            point_id=self.point_id,
            session_id=self.session_id,
            timestamp=self.timestamp,
            position=GeoPoint(**self.position) if self.position else None,
            attitude=Attitude(**self.attitude) if self.attitude else None,
            battery=BatteryState(**self.battery) if self.battery else None,
            motors=[MotorState(**m) for m in self.motors] if self.motors else None,
            imu=IMUState(**self.imu) if self.imu else None,
            gps=GPSState(**self.gps) if self.gps else None,
        )
    
    @classmethod
    def from_model(cls, point: TelemetryPoint) -> "TelemetryPointORM":
        """Convert Pydantic model to ORM."""
        return cls(
            point_id=point.point_id or f"tp-{datetime.now().isoformat()}",
            session_id=point.session_id,
            timestamp=point.timestamp,
            position=point.position.model_dump() if point.position else None,
            attitude=point.attitude.model_dump() if point.attitude else None,
            battery=point.battery.model_dump() if point.battery else None,
            motors=[m.model_dump() for m in point.motors] if point.motors else None,
            imu=point.imu.model_dump() if point.imu else None,
            gps=point.gps.model_dump() if point.gps else None,
        )


class SQLiteTelemetryStorage:
    """SQLite storage for TelemetryPoint."""
    
    def __init__(self, database_url: str = "sqlite+aiosqlite:///./aero_telemetry.db"):
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        self.engine = create_async_engine(database_url, echo=False)
        self.async_session = async_sessionmaker(self.engine, expire_on_commit=False)
    
    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def create(self, point: TelemetryPoint) -> TelemetryPoint:
        async with self.async_session() as db:
            orm = TelemetryPointORM.from_model(point)
            db.add(orm)
            await db.commit()
            return orm.to_model()
    
    async def get(self, point_id: str) -> Optional[TelemetryPoint]:
        async with self.async_session() as db:
            result = await db.execute(
                select(TelemetryPointORM).where(TelemetryPointORM.point_id == point_id)
            )
            orm = result.scalar_one_or_none()
            return orm.to_model() if orm else None
    
    async def list(
        self,
        session_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[TelemetryPoint]:
        async with self.async_session() as db:
            query = select(TelemetryPointORM)
            
            if session_id:
                query = query.where(TelemetryPointORM.session_id == session_id)
            if start_time:
                query = query.where(TelemetryPointORM.timestamp >= start_time)
            if end_time:
                query = query.where(TelemetryPointORM.timestamp <= end_time)
            
            query = query.order_by(TelemetryPointORM.timestamp).offset(skip).limit(limit)
            
            result = await db.execute(query)
            return [orm.to_model() for orm in result.scalars().all()]
    
    async def delete(self, point_id: str) -> bool:
        async with self.async_session() as db:
            result = await db.execute(
                select(TelemetryPointORM).where(TelemetryPointORM.point_id == point_id)
            )
            existing = result.scalar_one_or_none()
            if existing is None:
                return False
            
            await db.delete(existing)
            await db.commit()
            return True
    
    async def close(self):
        await self.engine.dispose()