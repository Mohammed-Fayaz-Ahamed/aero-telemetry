"""
Abstract storage interface.
All storage implementations (SQLite, PostgreSQL, etc.) must satisfy this contract.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar


T = TypeVar("T")


class Storage(ABC, Generic[T]):
    """
    Abstract base for storing and retrieving entities.
    
    Design note: Methods are async because real databases are async.
    SQLite with aiosqlite is async. PostgreSQL with asyncpg is async.
    Even if the underlying DB is sync, we wrap it to keep the interface consistent.
    """
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        """Store a new entity. Return the stored entity (may have server-generated fields)."""
        pass
    
    @abstractmethod
    async def get(self, id: str) -> T | None:
        """Retrieve entity by ID. Return None if not found."""
        pass
    
    @abstractmethod
    async def list(self, skip: int = 0, limit: int = 100) -> list[T]:
        """List entities with pagination."""
        pass
    
    @abstractmethod
    async def update(self, id: str, entity: T) -> T | None:
        """Replace entity by ID. Return updated entity or None if not found."""
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Delete entity by ID. Return True if deleted, False if not found."""
        pass