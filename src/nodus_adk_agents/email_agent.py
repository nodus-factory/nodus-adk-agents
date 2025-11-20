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


def build_email_agent(mcp_toolset: Any, memory_service: Any) -> Any:
    """
    Build the email domain agent.

    Args:
        mcp_toolset: MCP tools (email server tools)
        memory_service: Memory service for context

    Returns:
        Configured email agent instance

    Capabilities:
        - list_emails: Search and list emails by criteria
        - read_email: Read full email content
        - draft_reply: Compose a draft reply
        - send_email: Send email (requires HITL confirmation)
        - manage_labels: Add/remove labels
    """
    logger.info("Building email agent")

    # TODO: Implement actual ADK agent initialization
    # from google.adk import Agent
    # 
    # email_agent = Agent(
    #     name="email_agent",
    #     instruction="""
    #     You are an email management specialist that helps users:
    #     - Find and read emails efficiently
    #     - Compose professional replies
    #     - Manage email organization
    #     
    #     Always ask for confirmation before sending emails.
    #     Use memory service to remember email context and preferences.
    #     """,
    #     tools=[mcp_toolset.filter_by_server("email"), memory_service],
    # )

    return {
        "type": "domain_agent",
        "name": "email_agent",
        "status": "stub",
        "capabilities": ["list", "read", "draft", "send", "labels"],
    }

