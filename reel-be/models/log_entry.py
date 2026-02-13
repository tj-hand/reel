"""LogEntry model - Audit log entries for all modules"""

import enum
from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

# Use Matrix infrastructure (Layer 0)
from src.database import Base


class LogSeverity(str, enum.Enum):
    """Log severity levels"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogEntry(Base):
    """LogEntry model - stores audit trail for all module actions"""

    __tablename__ = "reel_log_entries"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )

    # Actor info (denormalized for query performance)
    actor_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="User who performed the action (nullable for system actions)",
    )
    actor_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Actor email at time of action (denormalized)",
    )
    actor_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Actor display name at time of action (denormalized)",
    )

    # Context
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="Tenant (account) context for the action",
    )
    client_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Client (local scope) context if applicable",
    )

    # Action info
    module: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Source module (guardian, mentor, aurora, etc.)",
    )
    action: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Action identifier (users.login, permissions.grant, etc.)",
    )
    severity: Mapped[LogSeverity] = mapped_column(
        Enum(LogSeverity),
        nullable=False,
        default=LogSeverity.INFO,
        index=True,
        comment="Log severity level",
    )

    # Resource (optional, for resource-specific actions)
    resource_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Type of resource affected (user, permission, tenant, etc.)",
    )
    resource_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="ID of the affected resource",
    )

    # Payload (flexible JSON data)
    data: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Action-specific data payload",
    )

    # Request metadata
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        comment="Client IP address (IPv4 or IPv6)",
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Client user agent string",
    )
    request_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Request correlation ID for tracing",
    )

    # Timestamps (no updated_at - logs are immutable)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Table indexes for common query patterns
    __table_args__ = (
        # Tenant log queries (most common)
        Index(
            "idx_reel_tenant_created",
            "tenant_id",
            "created_at",
            postgresql_ops={"created_at": "DESC"},
        ),
        # Client log queries
        Index(
            "idx_reel_tenant_client_created",
            "tenant_id",
            "client_id",
            "created_at",
            postgresql_ops={"created_at": "DESC"},
        ),
        # Action filtering
        Index(
            "idx_reel_tenant_module_action",
            "tenant_id",
            "module",
            "action",
        ),
        # User activity lookup
        Index(
            "idx_reel_tenant_actor",
            "tenant_id",
            "actor_id",
        ),
        # Severity filtering
        Index(
            "idx_reel_tenant_severity",
            "tenant_id",
            "severity",
            "created_at",
            postgresql_ops={"created_at": "DESC"},
        ),
    )

    def __repr__(self) -> str:
        return f"<LogEntry(id={self.id}, module={self.module}, action={self.action})>"
