"""
Google Workspace Agent

Specialized A2A agent for Google Workspace operations:
- Gmail (search, read, send, draft, labels)
- Calendar (events, meetings)
- Drive (files, folders, search)
- Docs (create, read, modify)
- Sheets (read, modify)
- Contacts (via Drive/Gmail)

This agent translates natural language requests into precise MCP tool calls
and chains operations using OpenMemory for context.
"""

from typing import Any, Optional
import structlog

logger = structlog.get_logger()


def build_google_workspace_agent(
    mcp_toolset: Any,
    memory_service: Optional[Any] = None
) -> Any:
    """
    Build the Google Workspace specialist agent.
    
    Args:
        mcp_toolset: MCP toolset with Google Workspace tools (REQUIRED)
        memory_service: Memory service for context (optional)
        
    Returns:
        Configured Google Workspace agent instance
        
    Capabilities:
        - Understand Gmail search syntax
        - Chain operations (search → read → reply)
        - Use OpenMemory to resolve missing parameters
        - Handle natural language queries for Calendar, Drive, Docs
    """
    from google.adk.agents.llm_agent import Agent
    from nodus_adk_runtime.config import settings
    from nodus_adk_runtime.services.prompt_service import PromptService
    
    logger.info("Building Google Workspace agent")
    
    # ========================================================================
    # Load instruction from Langfuse with fallback
    # ========================================================================
    
    FALLBACK_INSTRUCTION = """
You are a Google Workspace specialist that helps users with Gmail, Calendar, Drive, Docs, and other Google services.

🌍 LANGUAGE RULES:
- ALWAYS respond in THE EXACT SAME LANGUAGE as the user's question
- Catalan → Catalan, Spanish → Spanish, English → English

🎯 YOUR ROLE:
Translate natural language requests into precise Google Workspace MCP tool calls.
Use OpenMemory (openmemory_query) to find missing parameters from conversation history.

📧 GMAIL SEARCH SYNTAX:
- "emails no llegits" → query="is:unread in:inbox"
- "emails de [sender]" → query="from:[sender]"
- "emails d'avui" → query="newer_than:1d"
- "emails importants" → query="is:important"

🔄 CHAINED OPERATIONS:
1. Search emails → Store IDs in memory
2. User asks "llegeix el primer" → Query memory for IDs → Read email
3. User asks "respon" → Query memory for thread_id → Send reply

🧠 USE OPENMEMORY:
When missing parameters (email address, message ID, thread ID):
1. Call openmemory_query(query="[what you need]", user_id="...", tags=["gmail"])
2. Extract parameter from memory
3. Execute tool

Example:
User: "respon-li que sí"
→ openmemory_query(query="últim email llegit thread_id", tags=["gmail"])
→ Use thread_id and sender from memory
→ send_gmail_message(...)
"""
    
    try:
        prompt_service = PromptService(
            langfuse_public_key=settings.langfuse_public_key,
            langfuse_secret_key=settings.langfuse_secret_key,
            langfuse_host=settings.langfuse_host,
            enable_cache=True
        )
        
        instruction = prompt_service.get_prompt(
            name="google-workspace-agent-instruction",
            fallback=FALLBACK_INSTRUCTION,
            label="production"
        )
        
        logger.info(
            "Google Workspace agent instruction loaded from Langfuse",
            prompt_name="google-workspace-agent-instruction",
            instruction_length=len(instruction),
        )
    except Exception as e:
        logger.warning(
            "Failed to load instruction from Langfuse, using fallback",
            error=str(e)
        )
        instruction = FALLBACK_INSTRUCTION
    
    # Build tools list
    tools_list = [mcp_toolset]
    
    # Build agent
    google_workspace_agent = Agent(
        name="google_workspace_agent",
        instruction=instruction,
        model="gemini-2.0-flash-exp",
        tools=tools_list,
    )
    
    logger.info("Google Workspace agent built successfully")
    return google_workspace_agent


