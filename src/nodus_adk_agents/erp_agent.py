"""
ERP Agent (Stub)

Domain agent for ERP operations.
To be implemented when ERP integration is ready.
"""

from typing import Any
import structlog

logger = structlog.get_logger()


def build_erp_agent(mcp_toolset: Any, memory_service: Any) -> Any:
    """Build the ERP domain agent (stub)."""
    logger.info("Building ERP agent (stub)")
    return {
        "type": "domain_agent",
        "name": "erp_agent",
        "status": "stub",
        "capabilities": ["view_orders", "check_inventory", "create_invoice"],
    }

