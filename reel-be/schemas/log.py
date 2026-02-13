"""Log schemas - Pydantic models for log API endpoints"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ..models.log_entry import LogSeverity


class LogEntryBase(BaseModel):
    """Base schema for log entries"""

    module: str = Field(..., min_length=1, max_length=100, description="Source module")
    action: str = Field(..., min_length=1, max_length=255, description="Action identifier")
    severity: LogSeverity = Field(default=LogSeverity.INFO, description="Log severity")

    # Resource (optional)
    resource_type: Optional[str] = Field(None, max_length=100)
    resource_id: Optional[UUID] = None

    # Payload
    data: Optional[dict[str, Any]] = None


class LogEntryCreate(LogEntryBase):
    """Schema for creating a log entry (internal use)"""

    # Actor info
    actor_id: Optional[UUID] = None
    actor_email: Optional[str] = Field(None, max_length=255)
    actor_name: Optional[str] = Field(None, max_length=255)

    # Context
    tenant_id: UUID
    client_id: Optional[UUID] = None

    # Request metadata
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = None
    request_id: Optional[UUID] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "module": "guardian",
                "action": "users.login",
                "severity": "INFO",
                "actor_id": "123e4567-e89b-12d3-a456-426614174000",
                "actor_email": "user@example.com",
                "tenant_id": "123e4567-e89b-12d3-a456-426614174001",
                "data": {"login_method": "email_token"},
            }
        }
    )


class LogEntryRead(LogEntryBase):
    """Schema for reading a log entry"""

    id: UUID
    actor_id: Optional[UUID]
    actor_email: Optional[str]
    actor_name: Optional[str]
    tenant_id: UUID
    client_id: Optional[UUID]
    ip_address: Optional[str]
    user_agent: Optional[str]
    request_id: Optional[UUID]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LogEntryList(BaseModel):
    """Paginated list of log entries"""

    items: list[LogEntryRead]
    total: int
    page: int
    page_size: int
    pages: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [],
                "total": 100,
                "page": 1,
                "page_size": 50,
                "pages": 2,
            }
        }
    )


class LogFilter(BaseModel):
    """Filter parameters for log queries"""

    # Time range
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    # Actor filter
    actor_id: Optional[UUID] = None

    # Module/action filter
    module: Optional[str] = None
    action: Optional[str] = None

    # Severity filter
    severity: Optional[LogSeverity] = None
    min_severity: Optional[LogSeverity] = None

    # Resource filter
    resource_type: Optional[str] = None
    resource_id: Optional[UUID] = None

    # Client filter (within tenant)
    client_id: Optional[UUID] = None

    # Search in data payload
    search: Optional[str] = Field(None, max_length=255)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "module": "guardian",
                "severity": "WARNING",
                "start_date": "2024-01-01T00:00:00Z",
            }
        }
    )


class LogStats(BaseModel):
    """Log statistics for a tenant"""

    total_entries: int
    entries_by_severity: dict[str, int]
    entries_by_module: dict[str, int]
    entries_today: int
    entries_this_week: int

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_entries": 1500,
                "entries_by_severity": {
                    "INFO": 1200,
                    "WARNING": 250,
                    "ERROR": 50,
                },
                "entries_by_module": {
                    "guardian": 500,
                    "mentor": 800,
                    "aurora": 200,
                },
                "entries_today": 45,
                "entries_this_week": 320,
            }
        }
    )


class LogExportRequest(BaseModel):
    """Request for log export"""

    filter: Optional[LogFilter] = None
    format: str = Field(default="csv", pattern="^(csv|json)$")
    include_data: bool = Field(default=False, description="Include data payload in export")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "filter": {"module": "guardian", "severity": "ERROR"},
                "format": "csv",
                "include_data": True,
            }
        }
    )


class LogExportResponse(BaseModel):
    """Response for log export request"""

    download_url: str
    filename: str
    record_count: int
    expires_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "download_url": "/api/v1/reel/exports/abc123.csv",
                "filename": "logs_2024-01-15_export.csv",
                "record_count": 500,
                "expires_at": "2024-01-15T12:00:00Z",
            }
        }
    )
