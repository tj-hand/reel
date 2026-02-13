"""Reel module - Audit logging for all modules

Provides action logging, audit trail, and log visualization.

Exports:
    - router: FastAPI router for /api/v1/reel/*
    - ReelService: Core logging service
    - get_reel_service: FastAPI dependency
    - LogEntry: SQLAlchemy model
    - LogSeverity: Log severity enum
"""

from .router import router
from .models.log_entry import LogEntry, LogSeverity
from .services.reel_service import ReelService, get_reel_service

__all__ = [
    "router",
    "LogEntry",
    "LogSeverity",
    "ReelService",
    "get_reel_service",
]
