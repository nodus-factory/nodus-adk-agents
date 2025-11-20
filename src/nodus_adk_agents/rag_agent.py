"""
RAG Agent (Stub)

Domain agent for RAG (Retrieval-Augmented Generation) operations.
To be implemented when RAG system is ready.
"""

from typing import Any
import structlog

logger = structlog.get_logger()


def build_rag_agent(mcp_toolset: Any, memory_service: Any) -> Any:
    """Build the RAG domain agent (stub)."""
    logger.info("Building RAG agent (stub)")
    return {
        "type": "domain_agent",
        "name": "rag_agent",
        "status": "stub",
        "capabilities": ["query_documents", "ingest_documents", "search_knowledge"],
    }

