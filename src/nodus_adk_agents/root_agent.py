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
    knowledge_tool: Optional[Any] = None,
) -> Any:
    """
    Build the root Personal Assistant agent using Google ADK.

    Args:
        mcp_adapter: MCP adapter for external tool integrations
        memory_service: Memory service for RAG (QdrantMemoryService)
        user_context: User context for authentication
        config: Agent configuration (model, etc.)
        domain_agents: Optional list of domain-specific sub-agents
        knowledge_tool: Optional tool to query the knowledge base (documents)

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
    from google.adk.tools.load_memory_tool import load_memory
    from nodus_adk_runtime.adapters.nodus_mcp_toolset import NodusMcpToolset
    
    logger.info("Building root agent", model=config.get("model"))
    
    # Create MCP toolset
    mcp_toolset = NodusMcpToolset(
        mcp_adapter=mcp_adapter,
        user_context=user_context,
    )
    
    # Build tools list
    tools_list = [mcp_toolset, load_memory]
    
    # Add knowledge base tool if provided
    if knowledge_tool:
        tools_list.append(knowledge_tool)
        logger.info("Knowledge base tool added to agent")
    
    instruction = """
You are a helpful personal assistant integrated with Nodus OS.

Your capabilities include:
- Understanding user requests and intent in multiple languages (Catalan, Spanish, English, etc.)
- Accessing external tools via MCP (Model Context Protocol) Gateway
- Using semantic memory (RAG) to recall past conversations by calling the `load_memory` tool
- Searching the organization's knowledge base (uploaded documents) using `query_knowledge_base`
- Providing clear, actionable responses

When the user asks about specific documents, projects, or information:
- ALWAYS use the `query_knowledge_base` tool to search for relevant information
- Examples: "què saps de l'anàlisi funcional de Segalés?", "tell me about the project report"

When you need to use external tools:
- Use the available MCP tools through the gateway
- Tools are organized by server (email, calendar, CRM, etc.)
- Always provide context about what you're doing
- Tools are prefixed with "mcp_" to indicate they come from MCP Gateway

When answering questions:
- Use your memory to recall relevant past conversations by calling the `load_memory` tool
- Use `query_knowledge_base` to search for information in uploaded documents
- Provide accurate, helpful information
- If you don't know something, say so clearly
- Always respond in the same language as the user's question
"""
    
    # Build agent with all tools
    root_agent = Agent(
        name="personal_assistant",
        instruction=instruction,
        model=config.get("model", "gemini-2.0-flash-exp"),
        tools=tools_list,
        # sub_agents=domain_agents if domain_agents else None,
    )
    
    logger.info(
        "Root agent built successfully",
        agent_name=root_agent.name,
        has_mcp_toolset=True,
        has_memory_tool=True,
        has_knowledge_tool=bool(knowledge_tool),
    )
    return root_agent
