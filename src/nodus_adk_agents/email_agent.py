"""
Email Agent

Domain agent specialized in email operations:
- Reading and searching emails
- Composing draft replies
- Sending emails (with HITL confirmation)
- Managing threads and labels
"""

from typing import Any
import structlog

logger = structlog.get_logger()


def build_email_agent(mcp_toolset: Any = None, memory_service: Any = None) -> Any:
    """
    Build the email domain agent.

    Args:
        mcp_toolset: MCP tools (email server tools) - optional for testing
        memory_service: Memory service for context - optional for testing

    Returns:
        Configured email agent instance

    Capabilities:
        - list_emails: Search and list emails by criteria
        - read_email: Read full email content
        - draft_reply: Compose a draft reply
        - send_email: Send email (requires HITL confirmation)
        - manage_labels: Add/remove labels
    """
    from google.adk.agents.llm_agent import Agent
    
    logger.info("Building email agent")

    # Build email agent with ADK
    # For testing: simplified agent without actual MCP tools
    instruction = """
You are an email management specialist that helps users with email-related tasks.

Your capabilities:
- Listing and searching emails by criteria (sender, subject, date range)
- Reading full email content
- Composing professional replies
- Managing email organization (labels, folders)

IMPORTANT: 
- Always ask for confirmation before sending emails
- Provide clear, concise summaries of email content
- Respect user privacy and confidentiality

For testing purposes, you can simulate email operations.
Example responses:
- "I found 3 emails from john@example.com in the last week"
- "The email from Sarah says: [simulated content]"
- "I've drafted a reply: [simulated draft]"
"""
    
    # Build tools list (empty for testing, MCP tools would go here)
    tools_list = []
    if mcp_toolset:
        tools_list.append(mcp_toolset)
    
    email_agent = Agent(
        name="email_agent",
        instruction=instruction,
        model="gemini-2.0-flash-exp",
        tools=tools_list,
    )
    
    logger.info("Email agent built successfully")
    return email_agent

