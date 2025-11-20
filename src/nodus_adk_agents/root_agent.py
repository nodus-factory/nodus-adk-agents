"""
Root Agent (Personal Assistant)

The main orchestrator agent that:
- Understands user intent
- Plans and delegates to domain agents
- Manages A2A (Agent-to-Agent) communication
- Composes final responses
"""

from typing import Any, Dict, List, Optional
import structlog

logger = structlog.get_logger()


def build_root_agent(
    mcp_adapter: Any,
    memory_service: Any,
    user_context: Any,
    config: Dict[str, Any],
    domain_agents: Optional[List[Any]] = None,
) -> Any:
    """
    Build the root Personal Assistant agent using Google ADK.

    Args:
        mcp_adapter: MCP adapter for external tool integrations
        memory_service: Memory service for RAG (QdrantMemoryService)
        user_context: User context for authentication
        config: Agent configuration (model, etc.)
        domain_agents: Optional list of domain-specific sub-agents

    Returns:
        Configured ADK Agent instance

    Example:
        >>> from nodus_adk_runtime.adapters.mcp_adapter import MCPAdapter
        >>> from nodus_adk_runtime.adapters.qdrant_memory_service import QdrantMemoryService
        >>> from nodus_adk_runtime.middleware.auth import UserContext
        >>> 
        >>> mcp = MCPAdapter(gateway_url="http://mcp-gateway:7443")
        >>> memory = QdrantMemoryService(qdrant_url="http://qdrant:6333")
        >>> user_ctx = UserContext(...)
        >>> 
        >>> root = build_root_agent(
        ...     mcp_adapter=mcp,
        ...     memory_service=memory,
        ...     user_context=user_ctx,
        ...     config={"model": "gemini-2.0-flash-exp"}
        ... )
    """
    from google.adk.agents.llm_agent import Agent
    from nodus_adk_runtime.adapters.nodus_mcp_toolset import NodusMcpToolset
    
    logger.info("Building root agent", model=config.get("model"))
    
    # Create MCP toolset
    mcp_toolset = NodusMcpToolset(
        mcp_adapter=mcp_adapter,
        user_context=user_context,
    )
    
    instruction = """
You are a helpful personal assistant integrated with Nodus OS.

Your capabilities include:
- Understanding user requests and intent
- Accessing external tools via MCP (Model Context Protocol) Gateway
- Using semantic memory (RAG) to recall past conversations
- Providing clear, actionable responses

When you need to use external tools:
- Use the available MCP tools through the gateway
- Tools are organized by server (email, calendar, CRM, etc.)
- Always provide context about what you're doing
- Tools are prefixed with "mcp_" to indicate they come from MCP Gateway

When answering questions:
- Use your memory to recall relevant past conversations
- Provide accurate, helpful information
- If you don't know something, say so clearly
"""
    
        # Build agent with MCP toolset
    # Note: memory_service is configured in the Runner, not in the Agent
    root_agent = Agent(
        name="personal_assistant",
        instruction=instruction,
        model=config.get("model", "gemini-2.0-flash-exp"),
        tools=[mcp_toolset],
        # sub_agents=domain_agents if domain_agents else None,
    )
    
    logger.info(
        "Root agent built successfully",
        agent_name=root_agent.name,
        has_mcp_toolset=True,
    )
    return root_agent
