# Reel

Centralized action logging and audit trail for all modules.

## What It Does

- **Stores audit logs** - Persists all module actions to PostgreSQL with actor, context, and resource info
- **Provides logging API** - Other modules call `ReelService.log()` to record actions
- **Enables log viewing** - Paginated queries with filtering by module, action, severity, actor, date range
- **Exports logs** - CSV/JSON export for compliance and analysis
- **Tracks statistics** - Aggregates by severity, module, and time period

## What It Provides

### Backend Exports

| Export | Description |
|--------|-------------|
| `router` | FastAPI router for `/api/v1/reel/*` |
| `ReelService` | Core logging service |
| `get_reel_service(db)` | FastAPI dependency |
| `LogEntry` | SQLAlchemy model |
| `LogSeverity` | Severity enum (DEBUG, INFO, WARNING, ERROR, CRITICAL) |

### Frontend Exports

| Export | Description |
|--------|-------------|
| `useReelStore()` | Pinia store for log state |
| `useReel()` | Composable for logging and viewing |
| `fetchLogs()`, `fetchLog()` | API functions |
| `fetchLogStats()`, `exportLogs()` | API functions |
| `createLog()` | Client-side logging |

### API Endpoints

| Method | Path | Permission |
|--------|------|------------|
| GET | `/api/v1/reel/logs` | `reel.logs.view` |
| GET | `/api/v1/reel/logs/{id}` | `reel.logs.view` |
| GET | `/api/v1/reel/logs/stats` | `reel.logs.view` |
| POST | `/api/v1/reel/logs/export` | `reel.logs.export` |
| POST | `/api/v1/reel/logs` | Internal only |

### Mentor Actions

| Action | Scopes |
|--------|--------|
| `reel.logs.view` | ACCOUNT, CLIENT |
| `reel.logs.export` | CLIENT |
| `reel.logs.filter` | ACCOUNT, CLIENT (reserved) |

## What It Expects

| Dependency | Purpose |
|------------|---------|
| Matrix | Database infrastructure (`src.database`) |
| Mentor | Auth context (`CurrentUser`, `TenantContext`), permissions |
| Evoke | Frontend HTTP client |
| Echoes | Translation keys |
| Stage | UI via blade-reel |

## What It Never Does

- **No UI components** - UI lives in Stage blade-reel
- **No file storage** - Export generates content; storage is deployment-specific
- **No log rotation** - Use `cleanup_old_entries()` or external tools
- **No cross-tenant queries** - All queries scoped to tenant

## File Structure

```
reel/
├── reel-be/                  # Backend (FastAPI)
│   ├── models/               # LogEntry SQLAlchemy model
│   ├── schemas/              # Pydantic schemas
│   ├── services/             # ReelService
│   ├── routers/              # API endpoints
│   ├── actions.py            # Mentor action registration
│   └── alembic/versions/     # Database migration
├── reel-fe/                  # Frontend (Vue 3)
│   ├── stores/               # Pinia store
│   ├── composables/          # useReel
│   ├── services/             # API client
│   ├── types/                # TypeScript interfaces
│   └── locales/              # i18n (en, pt-BR)
└── deploy.sh                 # Deployment script
```

## Usage

### Backend - Log an action

```python
from src.modules.reel import ReelService, LogSeverity

async def create_user(reel: ReelService, user: User, actor: CurrentUser, tenant: TenantContext):
    await reel.log(
        module="aurora",
        action="users.create",
        actor_id=actor.id,
        actor_email=actor.email,
        tenant_id=tenant.tenant_id,
        resource_type="user",
        resource_id=user.id,
        data={"email": user.email},
        severity=LogSeverity.INFO,
    )
```

### Frontend - Log and view

```typescript
import { useReel } from '@/reel'

// Logging
const { log } = useReel()
await log({ module: 'app', action: 'button.click', data: { buttonId: 'submit' } })

// Viewing
const { logs, loadLogs, filter, setFilter } = useReel({ autoLoad: true })
await setFilter({ module: 'guardian', severity: 'ERROR' })
```

## Stack Spec

See [architecture.md](https://github.com/tj-hand/spark/blob/main/architecture.md) section 4.5 for full specification.
