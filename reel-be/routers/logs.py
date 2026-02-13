"""Log management API endpoints"""

from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

# Use Matrix infrastructure (Layer 0)
from src.database import get_db

# Use Mentor dependencies (Layer 3) for auth and permissions
from src.modules.mentor.dependencies.auth import CurrentUser
from src.modules.mentor.dependencies.tenant import TenantContext
from src.modules.mentor.dependencies.permissions import require_permission
from src.modules.mentor.models.policy_assignment import ScopeType

from ..config import reel_config
from ..models.log_entry import LogSeverity
from ..schemas.log import (
    LogEntryCreate,
    LogEntryRead,
    LogEntryList,
    LogFilter,
    LogStats,
    LogExportRequest,
    LogExportResponse,
)
from ..services.reel_service import ReelService

router = APIRouter()


@router.get(
    "",
    response_model=LogEntryList,
    summary="List log entries",
    description="List log entries with filtering and pagination. Requires reel.logs.view permission.",
)
async def list_logs(
    current_user: CurrentUser,
    tenant: TenantContext,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: None = Depends(require_permission("reel.logs.view")),
    # Pagination
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    # Filters
    module: Optional[str] = Query(None, description="Filter by module"),
    action: Optional[str] = Query(None, description="Filter by action (supports wildcard: 'users.*')"),
    severity: Optional[LogSeverity] = Query(None, description="Filter by severity"),
    actor_id: Optional[UUID] = Query(None, description="Filter by actor"),
    client_id: Optional[UUID] = Query(None, description="Filter by client"),
    start_date: Optional[datetime] = Query(None, description="Filter logs after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter logs before this date"),
    search: Optional[str] = Query(None, max_length=255, description="Search in data payload"),
) -> LogEntryList:
    """List log entries with filtering and pagination"""
    reel_service = ReelService(db)

    # Build filter
    log_filter = LogFilter(
        module=module,
        action=action,
        severity=severity,
        actor_id=actor_id,
        client_id=client_id,
        start_date=start_date,
        end_date=end_date,
        search=search,
    )

    return await reel_service.list(
        tenant_id=tenant.tenant_id,
        filter=log_filter,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/stats",
    response_model=LogStats,
    summary="Get log statistics",
    description="Get log statistics for the current tenant. Requires reel.logs.view permission.",
)
async def get_stats(
    current_user: CurrentUser,
    tenant: TenantContext,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: None = Depends(require_permission("reel.logs.view")),
) -> LogStats:
    """Get log statistics for the tenant"""
    reel_service = ReelService(db)
    return await reel_service.get_stats(tenant.tenant_id)


@router.get(
    "/{log_id}",
    response_model=LogEntryRead,
    summary="Get a single log entry",
    description="Get a single log entry by ID. Requires reel.logs.view permission.",
)
async def get_log(
    log_id: UUID,
    current_user: CurrentUser,
    tenant: TenantContext,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: None = Depends(require_permission("reel.logs.view")),
) -> LogEntryRead:
    """Get a single log entry by ID"""
    reel_service = ReelService(db)

    entry = await reel_service.get(log_id, tenant.tenant_id)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log entry not found",
        )

    return LogEntryRead.model_validate(entry)


@router.post(
    "/export",
    response_model=LogExportResponse,
    summary="Export logs",
    description="Export logs to CSV or JSON format. Requires reel.logs.export permission.",
)
async def export_logs(
    request: LogExportRequest,
    current_user: CurrentUser,
    tenant: TenantContext,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: None = Depends(require_permission("reel.logs.export", scope_type=ScopeType.LOCAL)),
) -> LogExportResponse:
    """Export logs to file format"""
    reel_service = ReelService(db)

    content, filename, count = await reel_service.export(
        tenant_id=tenant.tenant_id,
        request=request,
    )

    # NOTE: Export file storage is intentionally not implemented here.
    # The actual file storage (S3, local, etc.) should be configured per-deployment.
    # This returns metadata; the frontend can use content from a streaming endpoint.
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    return LogExportResponse(
        download_url=f"/api/v1/reel/exports/{filename}",
        filename=filename,
        record_count=count,
        expires_at=expires_at,
    )


@router.post(
    "",
    response_model=LogEntryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create log entry (internal)",
    description="Create a log entry. This endpoint is for internal module use only.",
    include_in_schema=False,  # Hide from OpenAPI docs
)
async def create_log(
    entry_data: LogEntryCreate,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    # No permission check - internal only
    # In production, validate internal API key or service token
) -> LogEntryRead:
    """
    Create a log entry (internal use only).

    This endpoint is called by other modules to log actions.
    It should be protected by internal service authentication.
    """
    reel_service = ReelService(db)

    # Add request metadata if not provided
    if not entry_data.ip_address:
        entry_data.ip_address = request.client.host if request.client else None
    if not entry_data.user_agent:
        entry_data.user_agent = request.headers.get("user-agent")

    entry = await reel_service.log_from_schema(entry_data)
    return LogEntryRead.model_validate(entry)
