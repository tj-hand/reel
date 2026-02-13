#!/bin/bash
# deploy.sh - Deploy Reel module to Infinity and Matrix
#
# This script deploys Reel to both frontend (Infinity) and backend (Matrix):
# - reel-fe/* → Infinity/src/reel/
# - reel-be/* → Matrix/src/modules/reel/
# - reel-be/alembic/versions/* → Matrix/alembic/versions/
#
# Usage:
#   ./deploy.sh                           # Deploy to ../infinity and ../matrix
#   ./deploy.sh --fe-target ~/infinity    # Custom frontend target
#   ./deploy.sh --be-target ~/matrix      # Custom backend target
#   ./deploy.sh --migrate                 # Run migrations after deploy

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse arguments
FE_TARGET="${DEPLOY_FE_TARGET:-../infinity}"
BE_TARGET="${DEPLOY_BE_TARGET:-../matrix}"
RUN_MIGRATE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --fe-target)
            FE_TARGET="$2"
            shift 2
            ;;
        --be-target)
            BE_TARGET="$2"
            shift 2
            ;;
        --migrate)
            RUN_MIGRATE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--fe-target PATH] [--be-target PATH] [--migrate]"
            exit 1
            ;;
    esac
done

echo "Deploying Reel module..."
echo "  Frontend target: $FE_TARGET"
echo "  Backend target:  $BE_TARGET"
echo ""

# ============================================================================
# FRONTEND DEPLOYMENT (Infinity)
# ============================================================================
if [ -d "$SCRIPT_DIR/reel-fe" ]; then
    echo "Deploying Reel FE to Infinity..."

    FE_SLOT="$FE_TARGET/src/reel"
    mkdir -p "$FE_SLOT"

    # Copy all frontend files
    cp -r "$SCRIPT_DIR/reel-fe/"* "$FE_SLOT/"

    echo "  ✓ Frontend deployed to $FE_SLOT"
else
    echo "  ⚠ No reel-fe directory found, skipping frontend"
fi

# ============================================================================
# BACKEND DEPLOYMENT (Matrix)
# ============================================================================
if [ -d "$SCRIPT_DIR/reel-be" ]; then
    echo "Deploying Reel BE to Matrix..."

    BE_SLOT="$BE_TARGET/src/modules/reel"
    mkdir -p "$BE_SLOT"

    cd "$SCRIPT_DIR/reel-be"

    # Deploy __init__.py
    if [ -f "__init__.py" ]; then
        cp __init__.py "$BE_SLOT/__init__.py"
        echo "  ✓ Module init deployed"
    fi

    # Deploy router.py
    if [ -f "router.py" ]; then
        cp router.py "$BE_SLOT/router.py"
        echo "  ✓ Router deployed"
    fi

    # Deploy config.py
    if [ -f "config.py" ]; then
        cp config.py "$BE_SLOT/config.py"
        echo "  ✓ Config deployed"
    fi

    # Deploy dependencies.py
    if [ -f "dependencies.py" ]; then
        cp dependencies.py "$BE_SLOT/dependencies.py"
        echo "  ✓ Dependencies deployed"
    fi

    # Deploy actions.py
    if [ -f "actions.py" ]; then
        cp actions.py "$BE_SLOT/actions.py"
        echo "  ✓ Actions deployed"
    fi

    # Deploy routers directory
    if [ -d "routers" ]; then
        mkdir -p "$BE_SLOT/routers"
        cp -r routers/* "$BE_SLOT/routers/"
        echo "  ✓ Sub-routers deployed"
    fi

    # Deploy models
    if [ -d "models" ]; then
        mkdir -p "$BE_SLOT/models"
        cp -r models/* "$BE_SLOT/models/"
        echo "  ✓ Models deployed"
    fi

    # Deploy schemas
    if [ -d "schemas" ]; then
        mkdir -p "$BE_SLOT/schemas"
        cp -r schemas/* "$BE_SLOT/schemas/"
        echo "  ✓ Schemas deployed"
    fi

    # Deploy services
    if [ -d "services" ]; then
        mkdir -p "$BE_SLOT/services"
        cp -r services/* "$BE_SLOT/services/"
        echo "  ✓ Services deployed"
    fi

    # Deploy alembic migrations
    if [ -d "alembic/versions" ]; then
        mkdir -p "$BE_TARGET/alembic/versions"
        find alembic/versions -name '*.py' -exec cp {} "$BE_TARGET/alembic/versions/" \; 2>/dev/null || true
        MIGRATION_COUNT=$(find alembic/versions -name '*.py' 2>/dev/null | wc -l)
        if [ "$MIGRATION_COUNT" -gt 0 ]; then
            echo "  ✓ Migrations deployed ($MIGRATION_COUNT files)"
        fi
    fi

    echo "  ✓ Backend deployed to $BE_SLOT"
fi

echo ""
echo "Done! Reel module deployed."
echo ""
echo "Layer architecture:"
echo "  Reel (Layer 4) → Mentor (Layer 3) → Guardian (Layer 2) → Matrix (Layer 0)"
echo ""
echo "Dependencies:"
echo "  - Database: uses src.database (Matrix)"
echo "  - Auth: uses Guardian via Mentor dependencies"
echo "  - Permissions: uses Mentor permission system"
echo "  - Translations: uses Echoes"

# Run migrations if requested
if [ "$RUN_MIGRATE" = true ]; then
    echo ""
    echo "Running migrations..."

    if command -v docker &> /dev/null; then
        if docker ps --format '{{.Names}}' 2>/dev/null | grep -q 'spark-matrix'; then
            docker exec spark-matrix alembic upgrade head && echo "  ✓ Migrations complete" || echo "  ⚠ Migration failed"
        else
            echo "  ⚠ spark-matrix container not running"
            echo "  Run manually: docker exec -it spark-matrix alembic upgrade head"
        fi
    else
        if command -v alembic &> /dev/null; then
            cd "$BE_TARGET"
            alembic upgrade head && echo "  ✓ Migrations complete" || echo "  ⚠ Migration failed"
        else
            echo "  ⚠ alembic not available"
            echo "  Run manually: docker exec -it spark-matrix alembic upgrade head"
        fi
    fi
fi

echo ""
echo "Reel API endpoints:"
echo "  GET  /api/v1/reel/logs           - List logs (paginated, filtered)"
echo "  GET  /api/v1/reel/logs/{id}      - Get single log entry"
echo "  GET  /api/v1/reel/logs/stats     - Log statistics"
echo "  POST /api/v1/reel/logs/export    - Export logs to file"
echo "  POST /api/v1/reel/logs           - Create log (internal)"
