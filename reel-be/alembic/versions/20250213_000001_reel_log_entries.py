"""Create reel log entries table

Revision ID: 20250213_000001
Revises: 20241216_000001
Create Date: 2025-02-13

Creates the reel_log_entries table for audit logging across all modules.

Dependencies: Mentor core migration (20241216_000001)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20250213_000001'
down_revision: Union[str, None] = '20241216_000001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ============================================================================
    # LOG SEVERITY ENUM
    # ============================================================================
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE log_severity_enum AS ENUM ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$
    """)

    # ============================================================================
    # REEL LOG ENTRIES: Audit trail for all module actions
    # ============================================================================
    op.execute("""
        CREATE TABLE IF NOT EXISTS reel_log_entries (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

            -- Actor info (denormalized for query performance)
            actor_id UUID,
            actor_email VARCHAR(255),
            actor_name VARCHAR(255),

            -- Context (tenant is required, client is optional)
            tenant_id UUID NOT NULL,
            client_id UUID,

            -- Action info
            module VARCHAR(100) NOT NULL,
            action VARCHAR(255) NOT NULL,
            severity log_severity_enum NOT NULL DEFAULT 'INFO',

            -- Resource (optional, for resource-specific actions)
            resource_type VARCHAR(100),
            resource_id UUID,

            -- Payload (flexible JSON data)
            data JSONB,

            -- Request metadata
            ip_address VARCHAR(45),
            user_agent TEXT,
            request_id UUID,

            -- Timestamp (logs are immutable, no updated_at)
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    # ============================================================================
    # INDEXES: Optimized for common query patterns
    # ============================================================================

    # Tenant log queries (most common)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_reel_tenant_created
        ON reel_log_entries(tenant_id, created_at DESC)
    """)

    # Client log queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_reel_tenant_client_created
        ON reel_log_entries(tenant_id, client_id, created_at DESC)
    """)

    # Action filtering
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_reel_tenant_module_action
        ON reel_log_entries(tenant_id, module, action)
    """)

    # User activity lookup
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_reel_tenant_actor
        ON reel_log_entries(tenant_id, actor_id)
    """)

    # Severity filtering
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_reel_tenant_severity
        ON reel_log_entries(tenant_id, severity, created_at DESC)
    """)

    # Request correlation
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_reel_request_id
        ON reel_log_entries(request_id)
        WHERE request_id IS NOT NULL
    """)

    # Module index for cross-tenant analytics (admin only)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_reel_module
        ON reel_log_entries(module)
    """)

    # ============================================================================
    # COMMENTS: Documentation
    # ============================================================================
    op.execute("COMMENT ON TABLE reel_log_entries IS 'Audit log entries for all module actions'")
    op.execute("COMMENT ON COLUMN reel_log_entries.actor_id IS 'User who performed the action (NULL for system actions)'")
    op.execute("COMMENT ON COLUMN reel_log_entries.actor_email IS 'Denormalized email at time of action'")
    op.execute("COMMENT ON COLUMN reel_log_entries.tenant_id IS 'Tenant context (required for all logs)'")
    op.execute("COMMENT ON COLUMN reel_log_entries.client_id IS 'Client context if applicable'")
    op.execute("COMMENT ON COLUMN reel_log_entries.module IS 'Source module (guardian, mentor, aurora, etc.)'")
    op.execute("COMMENT ON COLUMN reel_log_entries.action IS 'Action identifier (users.login, permissions.grant, etc.)'")
    op.execute("COMMENT ON COLUMN reel_log_entries.severity IS 'Log severity level'")
    op.execute("COMMENT ON COLUMN reel_log_entries.resource_type IS 'Type of affected resource'")
    op.execute("COMMENT ON COLUMN reel_log_entries.resource_id IS 'ID of affected resource'")
    op.execute("COMMENT ON COLUMN reel_log_entries.data IS 'Action-specific payload (JSONB)'")
    op.execute("COMMENT ON COLUMN reel_log_entries.request_id IS 'Request correlation ID for tracing'")


def downgrade() -> None:
    # Drop table
    op.execute("DROP TABLE IF EXISTS reel_log_entries CASCADE")

    # Drop enum type
    op.execute("DROP TYPE IF EXISTS log_severity_enum")
