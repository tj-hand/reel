"""Reel dependencies - FastAPI dependency injection"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from .services.reel_service import ReelService, get_reel_service


async def get_reel(db: AsyncSession = Depends(get_db)) -> ReelService:
    """Get ReelService instance for dependency injection"""
    return get_reel_service(db)


# Type alias for FastAPI dependencies
ReelServiceDep = Annotated[ReelService, Depends(get_reel)]
