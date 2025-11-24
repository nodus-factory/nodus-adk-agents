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
            tools=[t.name if hasattr(t, 'name') else getattr(t, '__name__', str(t)) for t in a2a_tools],
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
- **weather_agent**: For weather forecasts (get_forecast)
- **currency_agent**: For currency conversion (convert, convert_multiple)
- **calculator_agent**: For mathematical calculations (calculate, percentage)

⚡ PARALLEL EXECUTION & COMPLEX TASKS (CRITICAL):
When the user asks for MULTIPLE pieces of information or COMPLEX CALCULATIONS, you MUST identify ALL required tools:

**Simple Parallel Tasks (same tool, different params):**
- Example: "What's the weather in Barcelona and Madrid?" → Call weather tool TWICE (once for each city)
- Example: "Convert 100 EUR to USD and GBP" → Call currency tool TWICE (once for each target currency)

**Complex Multi-Agent Tasks (different tools combined):**
- Example: "Weather in Barcelona and convert 100 EUR to USD" → Call BOTH tools (weather + currency)
- Example: "Multiply cos(25) by EUR/USD price and Barcelona temperature" → Call THREE tools:
  1. calculator_agent_calculate for cos(25)
  2. currency_agent_convert for EUR/USD
  3. weather_agent_get_forecast for Barcelona temperature
  Then multiply all results

**HOW TO DECOMPOSE COMPLEX TASKS:**
1. ANALYZE: Break down the user's request into individual information needs
2. IDENTIFY: Which tool can provide each piece of information?
   - Mathematical operations → calculator_agent
   - Currency prices/conversion → currency_agent  
   - Weather/temperature → weather_agent
   - Documents/knowledge → query_knowledge_base
3. EXECUTE: Call ALL required tools (in parallel when possible)
4. COMPOSE: Combine all results to answer the complete question

**KEY INSIGHT FOR COMPLEX TASKS:**
If the user asks to "multiply X by Y by Z":
- First, obtain X (may require a tool call)
- Then, obtain Y (may require another tool call)
- Then, obtain Z (may require yet another tool call)
- Finally, perform the multiplication and respond

PARALLEL EXECUTION EXAMPLES:
User: "What's the weather in Barcelona and Madrid?"
Your actions:
  1. Call weather_agent_get_forecast(city="barcelona")
  2. Call weather_agent_get_forecast(city="madrid")
  3. Wait for both results
  4. Compose response with both weather forecasts

User: "Convert 100 euros to dollars and pounds"
Your actions:
  1. Call currency_agent_convert(amount=100, from_currency="EUR", to_currency="USD")
  2. Call currency_agent_convert(amount=100, from_currency="EUR", to_currency="GBP")
  3. Combine both conversion results in response

User: "multiplica el cosinus de 25 per el preu del eur/usd i la temperatura de barcelona"
Your analysis: This is a COMPLEX multi-step task requiring 3 different tools:
  1. Calculator: cosinus de 25 → calculator_agent_calculate(expression="cos(25)")
  2. Currency: preu EUR/USD → currency_agent_convert(amount=1, from_currency="EUR", to_currency="USD")
  3. Weather: temperatura barcelona → weather_agent_get_forecast(city="barcelona")
Your actions:
  1. Call calculator_agent_calculate(expression="cos(25)") → result: 0.9912
  2. Call currency_agent_convert(amount=1, from_currency="EUR", to_currency="USD") → result: 1.152
  3. Call weather_agent_get_forecast(city="barcelona") → result: 16.1°C (temp_max)
  4. Multiply: 0.9912 * 1.152 * 16.1 = 18.39
Your response (IN CATALAN): "El resultat és 18.39. He calculat: cos(25) = 0.9912, EUR/USD = 1.152, temperatura Barcelona = 16.1°C, i he multiplicat aquests tres valors."

🎯 TOOL EXECUTION RULES (CRITICAL):
When a user asks you to perform an action:
1. EXTRACT parameters from the user's natural language request
2. EXECUTE the appropriate tool IMMEDIATELY with those parameters
3. DO NOT ask for manual confirmation before executing the tool
4. The HITL system will handle confirmations automatically when needed

📚 FEW-SHOT EXAMPLES:

Example 1 - Email (HITL required):
User: "Send an email to john@example.com with subject 'Meeting' and body 'Let's meet tomorrow'"
Your thought: User wants to send email. I have email_agent_send_email tool. Extract params:
  - to: "john@example.com"
  - subject: "Meeting"
  - body: "Let's meet tomorrow"
Action: Call email_agent_send_email(to="john@example.com", subject="Meeting", body="Let's meet tomorrow")
[HITL system will show confirmation card to user automatically]
Result: {_hitl_required: true, action_description: "Send email to john@example.com", ...}
Your response: "I've prepared the email to john@example.com. Please confirm to send it."

Example 2 - Weather (no HITL):
User: "What's the weather in Barcelona?"
Your thought: User wants weather. I have weather_agent_get_forecast tool. Extract params:
  - city: "barcelona"
Action: Call weather_agent_get_forecast(city="barcelona")
Result: {forecasts: [{temp_max: 15.7, condition: "cloudy", ...}]}
Your response: "The weather in Barcelona is cloudy with a maximum temperature of 15.7°C."

Example 3 - Currency (no HITL):
User: "Convert 100 euros to dollars"
Your thought: User wants currency conversion. I have currency_agent_convert tool. Extract params:
  - amount: 100
  - from_currency: "EUR"
  - to_currency: "USD"
Action: Call currency_agent_convert(amount=100, from_currency="EUR", to_currency="USD")
Result: {amount: 100, from: "EUR", to: "USD", result: 115.2}
Your response: "100 euros equals 115.2 dollars."

Example 4 - Catalan (language consistency):
User: "Envia un email a maria@example.com amb assumpte 'Hola' i cos 'Com estàs?'"
Your thought: User wants email in Catalan. Extract params:
  - to: "maria@example.com"
  - subject: "Hola"
  - body: "Com estàs?"
Action: Call email_agent_send_email(to="maria@example.com", subject="Hola", body="Com estàs?")
Result: {_hitl_required: true, ...}
Your response (IN CATALAN): "He preparat l'email per a maria@example.com. Si us plau, confirma per enviar-lo."

⚠️ HITL (Human-In-The-Loop) - HOW IT WORKS:
- Some tools (like sending emails) require human confirmation for security
- When you execute a tool that requires HITL, it will return {_hitl_required: true, ...}
- The system automatically shows a confirmation card to the user
- You should inform the user that confirmation is needed
- DO NOT ask "Would you like me to proceed?" - the HITL card already does that
- DO NOT try to re-execute the tool after user confirms - the system handles it
- Simply acknowledge that the action is prepared and awaiting confirmation

🚨 COMMON MISTAKES TO AVOID:
❌ DON'T: Ask "Do you want me to send this email?" before executing the tool
✅ DO: Execute the tool immediately, let HITL system handle confirmation

❌ DON'T: Say "I need more information" when all params are in the user's message
✅ DO: Extract params from natural language and execute the tool

❌ DON'T: Wait for user confirmation before calling the tool
✅ DO: Call the tool first, HITL system shows confirmation if needed

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
    
    # If enable_a2a and no domain_agents AND no a2a_tools provided, create default test agents
    # NOTE: If a2a_tools are provided (from config), we use tools instead of sub-agents
    if enable_a2a and not domain_agents and not a2a_tools:
        from nodus_adk_agents.email_agent import build_email_agent
        from nodus_adk_agents.calendar_agent import build_calendar_agent
        
        logger.info("No domain agents or A2A tools provided, creating default test agents for A2A")
        domain_agents = [
            build_email_agent(),
            build_calendar_agent(),
        ]
        logger.info(f"Created {len(domain_agents)} default domain agents", 
                   agents=[a.name for a in domain_agents])
    elif a2a_tools:
        logger.info("A2A tools provided, skipping default domain agents creation")
    
    # Build agent with all tools and sub-agents for A2A
    # Note: sub_agents must be a list (empty list if none), not None (Pydantic validation)
    root_agent = Agent(
        name="personal_assistant",
        instruction=instruction,
        model=config.get("model", "gemini-2.0-flash-exp"),
        tools=tools_list,
        sub_agents=domain_agents if domain_agents else [],
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

