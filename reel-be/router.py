"""Reel module main router

Aggregates all sub-routers under /v1/reel prefix.
"""

from fastapi import APIRouter

from .routers.logs import router as logs_router

router = APIRouter(prefix="/v1/reel", tags=["reel"])

# Mount sub-routers
router.include_router(logs_router, prefix="/logs", tags=["logs"])
