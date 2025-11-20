"""
CRM Agent (Stub)

Domain agent for CRM operations.
To be implemented when CRM integration is ready.
"""

from typing import Any
import structlog

logger = structlog.get_logger()


def build_crm_agent(mcp_toolset: Any, memory_service: Any) -> Any:
    """Build the CRM domain agent (stub)."""
    logger.info("Building CRM agent (stub)")
    return {
        "type": "domain_agent",
        "name": "crm_agent",
        "status": "stub",
        "capabilities": ["search_contacts", "view_deals", "log_activity"],
    }

