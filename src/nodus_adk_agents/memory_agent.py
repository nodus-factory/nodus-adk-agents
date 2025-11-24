"""
Memory Agent (Stub)

Domain agent for memory operations.
To be implemented when advanced memory features are ready.
"""

from typing import Any
import structlog

logger = structlog.get_logger()


def build_memory_agent(memory_service: Any) -> Any:
    """Build the memory domain agent (stub)."""
    logger.info("Building memory agent (stub)")
    return {
        "type": "domain_agent",
        "name": "memory_agent",
        "status": "stub",
        "capabilities": ["store_fact", "recall_fact", "search_timeline"],
    }


