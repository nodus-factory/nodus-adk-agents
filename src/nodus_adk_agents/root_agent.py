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
    enable_a2a: bool = True,
    a2a_tools: Optional[List[Any]] = None,
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
    
    # A2A tools should be loaded before calling this function (to avoid event loop issues)
    # They are passed as a parameter instead of being loaded here
    if a2a_tools is None:
        a2a_tools = []
    
    if a2a_tools:
        logger.info(
            "A2A tools received for root agent",
            count=len(a2a_tools),
            tools=[t.__name__ for t in a2a_tools],
        )
    
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
    
    # Add A2A tools loaded from config
    if a2a_tools:
        tools_list.extend(a2a_tools)
        logger.info("A2A tools added to agent", count=len(a2a_tools))
    
    instruction = """
You are a helpful personal assistant integrated with Nodus OS.

🌍 LANGUAGE RULES (CRITICAL):
- ALWAYS detect the user's language (Catalan, Spanish, English, etc.)
- ALWAYS respond in THE EXACT SAME LANGUAGE as the user's question
- If user writes in Catalan → respond in Catalan
- If user writes in Spanish → respond in Spanish  
- If user writes in English → respond in English
- Maintain language consistency throughout the entire conversation

Your capabilities include:
- Understanding user requests and intent in multiple languages
- Accessing external tools via MCP (Model Context Protocol) Gateway
- Using semantic memory (RAG) to recall past conversations by calling the `load_memory` tool
- Searching the organization's knowledge base (uploaded documents) using `query_knowledge_base`
- Delegating specialized tasks to domain expert agents (A2A - Agent-to-Agent)
- Providing clear, actionable responses

🤝 DELEGATION & A2A (Agent-to-Agent) RULES:
When you have access to sub-agents (domain specialists), you can delegate tasks:
- **email_agent**: For email-related tasks (reading, composing, sending emails)
  Example: "check my unread emails" → delegate to email_agent
- **calendar_agent**: For calendar/scheduling tasks (events, meetings, availability)
  Example: "schedule a meeting tomorrow at 3pm" → delegate to calendar_agent

Delegation strategy:
1. Identify if the task is domain-specific (email, calendar, CRM, etc.)
2. If a specialized agent exists for that domain, delegate the task
3. If the task requires multiple domains, you can delegate to multiple agents in parallel
4. Compose the final response with results from delegated agents

When the user asks about specific documents, projects, or information:
- ALWAYS use the `query_knowledge_base` tool to search for relevant information
- Examples: "què saps de l'anàlisi funcional de Segalés?", "tell me about the project report"
- If `query_knowledge_base` returns "No relevant documents found", clearly inform the user that you don't have information about that topic in the knowledge base

When you need to use external tools:
- Use the available MCP tools through the gateway
- Tools are organized by server (email, calendar, CRM, etc.)
- Always provide context about what you're doing
- Tools are prefixed with "mcp_" to indicate they come from MCP Gateway

🧠 MEMORY & CONTEXT RULES (CRITICAL):
- At the START of EVERY conversation turn, ALWAYS call `load_memory` to recall recent context
- This is ESSENTIAL to understand follow-up questions like "i quin productes fan?" (referring to previous topic)
- After loading memory, you'll know what "they" or "it" or "fan" refers to from previous messages

When answering questions:
1. FIRST: Call `load_memory` to load conversation context (ALWAYS DO THIS)
2. THEN: Decide if you need to delegate to a specialist agent or query knowledge base
3. FINALLY: Provide accurate, helpful information combining memory + knowledge/delegation results
- If you don't know something, say so clearly
"""
    
    # If enable_a2a and no domain_agents provided, create default test agents
    if enable_a2a and not domain_agents:
        from nodus_adk_agents.email_agent import build_email_agent
        from nodus_adk_agents.calendar_agent import build_calendar_agent
        
        logger.info("No domain agents provided, creating default test agents for A2A")
        domain_agents = [
            build_email_agent(),
            build_calendar_agent(),
        ]
        logger.info(f"Created {len(domain_agents)} default domain agents", 
                   agents=[a.name for a in domain_agents])
    
    # Build agent with all tools and sub-agents for A2A
    root_agent = Agent(
        name="personal_assistant",
        instruction=instruction,
        model=config.get("model", "gemini-2.0-flash-exp"),
        tools=tools_list,
        sub_agents=domain_agents if domain_agents else None,
    )
    
    logger.info(
        "Root agent built successfully",
        agent_name=root_agent.name,
        has_mcp_toolset=True,
        has_memory_tool=True,
        has_knowledge_tool=bool(knowledge_tool),
        has_sub_agents=bool(domain_agents),
        sub_agents_count=len(domain_agents) if domain_agents else 0,
    )
    return root_agent
