"""
REEL Action Registration

Registers REEL's permission actions with the MENTOR Action Registry.
This module is called at application startup to register all REEL actions.

REEL manages audit logging and provides log viewing, filtering, and export capabilities.
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# REEL action definitions
# Each action follows the format: module.resource.operation
# Translation keys follow ECHOES convention: {module}.actions.{resource}.{operation}.name/description

REEL_ACTIONS: List[Dict[str, Any]] = [
    # Log viewing - view audit log entries
    # NOTE: This permission also grants filtering capability (filters are part of list endpoint)
    {
        "resource": "logs",
        "operation": "view",
        "valid_scopes": ["ACCOUNT", "CLIENT"],
        "is_system": True,
    },
    # Log export - export logs to file
    {
        "resource": "logs",
        "operation": "export",
        "valid_scopes": ["CLIENT"],  # Export requires client scope for security
        "is_system": True,
    },
    # Log filter - advanced log filtering
    # NOTE: Reserved for future use. Currently filtering is implicit with view permission.
    # This action can be used to gate advanced filtering features (saved filters, complex queries).
    {
        "resource": "logs",
        "operation": "filter",
        "valid_scopes": ["ACCOUNT", "CLIENT"],
        "is_system": True,
    },
]


def register_reel_actions():
    """
    Register all REEL actions with the MENTOR Action Registry.

    This function should be called at application startup. It safely imports
    from MENTOR to avoid circular dependencies.

    Returns:
        List of registered actions, or empty list if registration failed
    """
    try:
        # Import from MENTOR to access the action registry
        # This import is done here to avoid circular dependencies
        from src.modules.mentor import (
            get_action_registry,
            ActionScope,
        )

        registry = get_action_registry()

        # Convert scope strings to ActionScope enums
        actions_with_scopes = []
        for action in REEL_ACTIONS:
            action_copy = action.copy()
            action_copy["valid_scopes"] = [
                ActionScope(s) for s in action["valid_scopes"]
            ]
            actions_with_scopes.append(action_copy)

        registered = registry.register_module_actions(
            module="reel",
            actions=actions_with_scopes,
            default_category="reel",
        )

        logger.info(f"Registered {len(registered)} REEL actions with MENTOR")
        return registered

    except ImportError as e:
        logger.warning(
            f"Could not import MENTOR action registry: {e}. "
            "REEL actions will not be registered."
        )
        return []
    except Exception as e:
        logger.error(f"Failed to register REEL actions: {e}")
        return []


def get_reel_action_codes() -> List[str]:
    """
    Get list of all REEL action codes.

    Useful for validation or testing.

    Returns:
        List of action codes (e.g., ['reel.logs.view', 'reel.logs.export'])
    """
    return [
        f"reel.{action['resource']}.{action['operation']}"
        for action in REEL_ACTIONS
    ]
