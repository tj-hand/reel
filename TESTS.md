# Reel Tests

Test status and coverage documentation for the Reel module.

## Validated Tests

| Test | Status | Notes |
|------|--------|-------|
| Module structure | PASS | All expected directories and files present |
| Backend exports | PASS | router, ReelService, LogEntry, LogSeverity export correctly |
| Frontend exports | PASS | useReelStore, useReel, API functions, types export correctly |
| Migration syntax | PASS | Alembic migration has valid SQL |
| TypeScript types | PASS | All interfaces match backend schemas |
| i18n keys | PASS | en.json and pt-BR.json have matching structure |

## Pending Tests

### Blocked by Deployment

| Test | Blocked By | Description |
|------|------------|-------------|
| API endpoints | Matrix + PostgreSQL | Need running database for endpoint tests |
| Log creation | Matrix | Test `ReelService.log()` creates entries |
| Log listing | Matrix | Test pagination and filtering |
| Log statistics | Matrix | Test aggregation queries |
| Log export | Matrix | Test CSV/JSON generation |
| Permission checks | Mentor | Test `reel.logs.view` and `reel.logs.export` |
| Tenant isolation | Mentor | Verify logs scoped to tenant |

### Blocked by Stage

| Test | Blocked By | Description |
|------|------------|-------------|
| Log dashboard UI | Stage blade-reel | UI components not in this repo |
| Log filter UI | Stage blade-reel | Filter controls not in this repo |
| Export download | Stage blade-reel | Download flow not in this repo |

### Blocked by Integration

| Test | Blocked By | Description |
|------|------------|-------------|
| Cross-module logging | Aurora, Guardian | Test other modules calling Reel |
| Action registration | Mentor | Verify actions registered at startup |
| Frontend API calls | Evoke | Test authenticated requests |

## Coverage Map

### Responsibilities

| Responsibility | Tests |
|----------------|-------|
| Store audit logs | Blocked: API endpoints (Matrix) |
| Provide logging API | Blocked: Log creation (Matrix) |
| Enable log viewing | Blocked: Log listing (Matrix) |
| Export logs | Blocked: Log export (Matrix) |
| Track statistics | Blocked: Log statistics (Matrix) |

### Deliveries

| Delivery | Tests |
|----------|-------|
| `router` | Validated: Backend exports |
| `ReelService` | Validated: Backend exports; Blocked: API endpoints |
| `LogEntry` model | Validated: Backend exports; Blocked: Migration |
| `useReelStore` | Validated: Frontend exports |
| `useReel` | Validated: Frontend exports |
| API functions | Validated: Frontend exports; Blocked: Integration |

### Expectations

| Expectation | Tests |
|-------------|-------|
| Matrix database | Blocked: Deployment |
| Mentor auth context | Blocked: Permission checks |
| Evoke client | Blocked: Frontend API calls |
| Echoes translations | Validated: i18n keys |

## Test Commands

Once deployed to a Spark project:

```bash
# Backend tests (from Matrix container)
docker exec spark-matrix pytest src/modules/reel/

# Frontend tests (from Infinity container)
docker exec spark-infinity npm run test -- --filter reel

# Integration tests
spark test reel
```

## Notes

- No automated tests in the module repo itself (tests run in deployed context)
- Stage blade-reel owns all UI component tests
- Mentor owns permission enforcement tests
