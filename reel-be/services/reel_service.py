"""ReelService - Core logging service for audit trail"""

import csv
import io
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import func, select, and_, or_, case
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import reel_config
from ..models.log_entry import LogEntry, LogSeverity
from ..schemas.log import (
    LogEntryCreate,
    LogEntryRead,
    LogEntryList,
    LogFilter,
    LogStats,
    LogExportRequest,
    LogExportResponse,
)


class ReelService:
    """Service for managing audit log entries"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        *,
        module: str,
        action: str,
        tenant_id: UUID,
        actor_id: Optional[UUID] = None,
        actor_email: Optional[str] = None,
        actor_name: Optional[str] = None,
        client_id: Optional[UUID] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[UUID] = None,
        data: Optional[dict[str, Any]] = None,
        severity: LogSeverity = LogSeverity.INFO,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[UUID] = None,
    ) -> LogEntry:
        """
        Create a new log entry.

        This is the primary method other modules use to log actions.
        """
        entry = LogEntry(
            module=module,
            action=action,
            tenant_id=tenant_id,
            actor_id=actor_id,
            actor_email=actor_email,
            actor_name=actor_name,
            client_id=client_id,
            resource_type=resource_type,
            resource_id=resource_id,
            data=data,
            severity=severity,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
        )

        self.db.add(entry)
        await self.db.commit()
        await self.db.refresh(entry)

        return entry

    async def log_from_schema(self, entry_data: LogEntryCreate) -> LogEntry:
        """Create a log entry from a Pydantic schema"""
        return await self.log(
            module=entry_data.module,
            action=entry_data.action,
            tenant_id=entry_data.tenant_id,
            actor_id=entry_data.actor_id,
            actor_email=entry_data.actor_email,
            actor_name=entry_data.actor_name,
            client_id=entry_data.client_id,
            resource_type=entry_data.resource_type,
            resource_id=entry_data.resource_id,
            data=entry_data.data,
            severity=entry_data.severity,
            ip_address=entry_data.ip_address,
            user_agent=entry_data.user_agent,
            request_id=entry_data.request_id,
        )

    async def get(self, log_id: UUID, tenant_id: UUID) -> Optional[LogEntry]:
        """Get a single log entry by ID (scoped to tenant)"""
        result = await self.db.execute(
            select(LogEntry).where(
                and_(LogEntry.id == log_id, LogEntry.tenant_id == tenant_id)
            )
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        tenant_id: UUID,
        filter: Optional[LogFilter] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> LogEntryList:
        """
        List log entries with filtering and pagination.

        All queries are scoped to the tenant for security.
        """
        # Validate pagination
        page_size = min(page_size, reel_config.max_page_size)
        page = max(page, 1)

        # Base query
        query = select(LogEntry).where(LogEntry.tenant_id == tenant_id)

        # Apply filters
        if filter:
            query = self._apply_filters(query, filter)

        # Order by created_at DESC (newest first)
        query = query.order_by(LogEntry.created_at.desc())

        # Get total count
        count_query = select(func.count()).select_from(
            query.subquery()
        )
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        # Execute query
        result = await self.db.execute(query)
        entries = result.scalars().all()

        # Calculate pages
        pages = (total + page_size - 1) // page_size if total > 0 else 0

        return LogEntryList(
            items=[LogEntryRead.model_validate(e) for e in entries],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    def _apply_filters(self, query, filter: LogFilter):
        """Apply filter conditions to query"""
        conditions = []

        # Time range
        if filter.start_date:
            conditions.append(LogEntry.created_at >= filter.start_date)
        if filter.end_date:
            conditions.append(LogEntry.created_at <= filter.end_date)

        # Actor
        if filter.actor_id:
            conditions.append(LogEntry.actor_id == filter.actor_id)

        # Module/action
        if filter.module:
            conditions.append(LogEntry.module == filter.module)
        if filter.action:
            # Support partial matching for action hierarchy
            if filter.action.endswith(".*"):
                prefix = filter.action[:-1]  # Remove *
                conditions.append(LogEntry.action.like(f"{prefix}%"))
            else:
                conditions.append(LogEntry.action == filter.action)

        # Severity
        if filter.severity:
            conditions.append(LogEntry.severity == filter.severity)
        if filter.min_severity:
            severity_order = {
                LogSeverity.DEBUG: 0,
                LogSeverity.INFO: 1,
                LogSeverity.WARNING: 2,
                LogSeverity.ERROR: 3,
                LogSeverity.CRITICAL: 4,
            }
            min_level = severity_order.get(filter.min_severity, 0)
            severity_conditions = [
                LogEntry.severity == sev
                for sev, level in severity_order.items()
                if level >= min_level
            ]
            if severity_conditions:
                conditions.append(or_(*severity_conditions))

        # Resource
        if filter.resource_type:
            conditions.append(LogEntry.resource_type == filter.resource_type)
        if filter.resource_id:
            conditions.append(LogEntry.resource_id == filter.resource_id)

        # Client
        if filter.client_id:
            conditions.append(LogEntry.client_id == filter.client_id)

        # Search in data payload (PostgreSQL JSONB contains)
        if filter.search:
            # Search in data as text
            conditions.append(
                LogEntry.data.astext.ilike(f"%{filter.search}%")
            )

        if conditions:
            query = query.where(and_(*conditions))

        return query

    async def get_stats(self, tenant_id: UUID) -> LogStats:
        """Get log statistics for a tenant"""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=now.weekday())

        # Total entries
        total_result = await self.db.execute(
            select(func.count()).where(LogEntry.tenant_id == tenant_id)
        )
        total_entries = total_result.scalar() or 0

        # Entries by severity
        severity_result = await self.db.execute(
            select(LogEntry.severity, func.count())
            .where(LogEntry.tenant_id == tenant_id)
            .group_by(LogEntry.severity)
        )
        entries_by_severity = {
            str(row[0].value): row[1] for row in severity_result.all()
        }

        # Entries by module
        module_result = await self.db.execute(
            select(LogEntry.module, func.count())
            .where(LogEntry.tenant_id == tenant_id)
            .group_by(LogEntry.module)
        )
        entries_by_module = {row[0]: row[1] for row in module_result.all()}

        # Entries today
        today_result = await self.db.execute(
            select(func.count()).where(
                and_(
                    LogEntry.tenant_id == tenant_id,
                    LogEntry.created_at >= today_start,
                )
            )
        )
        entries_today = today_result.scalar() or 0

        # Entries this week
        week_result = await self.db.execute(
            select(func.count()).where(
                and_(
                    LogEntry.tenant_id == tenant_id,
                    LogEntry.created_at >= week_start,
                )
            )
        )
        entries_this_week = week_result.scalar() or 0

        return LogStats(
            total_entries=total_entries,
            entries_by_severity=entries_by_severity,
            entries_by_module=entries_by_module,
            entries_today=entries_today,
            entries_this_week=entries_this_week,
        )

    async def export(
        self,
        tenant_id: UUID,
        request: LogExportRequest,
    ) -> tuple[str, str, int]:
        """
        Export logs to CSV or JSON format.

        Returns: (content, filename, record_count)
        """
        # Get all matching logs (up to export limit)
        query = select(LogEntry).where(LogEntry.tenant_id == tenant_id)

        if request.filter:
            query = self._apply_filters(query, request.filter)

        query = query.order_by(LogEntry.created_at.desc()).limit(
            reel_config.max_export_records
        )

        result = await self.db.execute(query)
        entries = result.scalars().all()

        # Generate filename
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"logs_{timestamp}.{request.format}"

        # Generate content
        if request.format == "json":
            content = self._export_json(entries, request.include_data)
        else:
            content = self._export_csv(entries, request.include_data)

        return content, filename, len(entries)

    def _export_csv(self, entries: list[LogEntry], include_data: bool) -> str:
        """Export entries to CSV format"""
        output = io.StringIO()

        fieldnames = [
            "id",
            "created_at",
            "module",
            "action",
            "severity",
            "actor_id",
            "actor_email",
            "actor_name",
            "tenant_id",
            "client_id",
            "resource_type",
            "resource_id",
            "ip_address",
        ]
        if include_data:
            fieldnames.append("data")

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for entry in entries:
            row = {
                "id": str(entry.id),
                "created_at": entry.created_at.isoformat(),
                "module": entry.module,
                "action": entry.action,
                "severity": entry.severity.value,
                "actor_id": str(entry.actor_id) if entry.actor_id else "",
                "actor_email": entry.actor_email or "",
                "actor_name": entry.actor_name or "",
                "tenant_id": str(entry.tenant_id),
                "client_id": str(entry.client_id) if entry.client_id else "",
                "resource_type": entry.resource_type or "",
                "resource_id": str(entry.resource_id) if entry.resource_id else "",
                "ip_address": entry.ip_address or "",
            }
            if include_data:
                row["data"] = json.dumps(entry.data) if entry.data else ""
            writer.writerow(row)

        return output.getvalue()

    def _export_json(self, entries: list[LogEntry], include_data: bool) -> str:
        """Export entries to JSON format"""
        items = []
        for entry in entries:
            item = {
                "id": str(entry.id),
                "created_at": entry.created_at.isoformat(),
                "module": entry.module,
                "action": entry.action,
                "severity": entry.severity.value,
                "actor_id": str(entry.actor_id) if entry.actor_id else None,
                "actor_email": entry.actor_email,
                "actor_name": entry.actor_name,
                "tenant_id": str(entry.tenant_id),
                "client_id": str(entry.client_id) if entry.client_id else None,
                "resource_type": entry.resource_type,
                "resource_id": str(entry.resource_id) if entry.resource_id else None,
                "ip_address": entry.ip_address,
            }
            if include_data:
                item["data"] = entry.data
            items.append(item)

        return json.dumps({"logs": items, "count": len(items)}, indent=2)

    async def cleanup_old_entries(self) -> int:
        """
        Delete log entries older than retention period.

        Returns number of deleted entries.
        """
        if reel_config.retention_days <= 0:
            return 0  # Retention disabled

        cutoff = datetime.now(timezone.utc) - timedelta(
            days=reel_config.retention_days
        )

        # Count entries to delete
        count_result = await self.db.execute(
            select(func.count()).where(LogEntry.created_at < cutoff)
        )
        count = count_result.scalar() or 0

        if count > 0:
            # Delete in batches to avoid long locks
            from sqlalchemy import delete

            await self.db.execute(
                delete(LogEntry).where(LogEntry.created_at < cutoff)
            )
            await self.db.commit()

        return count


def get_reel_service(db: AsyncSession) -> ReelService:
    """Factory function for ReelService (FastAPI dependency)"""
    return ReelService(db)
