"""
Calendar Agent

Domain agent specialized in calendar operations:
- Viewing calendar events
- Creating events (with HITL confirmation)
- Finding free slots
- Managing attendees
"""

from typing import Any
import structlog

logger = structlog.get_logger()


def build_calendar_agent(mcp_toolset: Any = None, memory_service: Any = None) -> Any:
    """
    Build the calendar domain agent.

    Args:
        mcp_toolset: MCP tools (calendar server tools) - optional for testing
        memory_service: Memory service for context - optional for testing

    Returns:
        Configured calendar agent instance

    Capabilities:
        - list_events: View calendar events
        - find_free_slots: Find available time slots
        - create_event: Create new event (requires HITL)
        - update_event: Modify existing event (requires HITL)
        - delete_event: Delete event (requires HITL)
    """
    from google.adk.agents.llm_agent import Agent
    
    logger.info("Building calendar agent")

    # Build calendar agent with ADK
    # For testing: simplified agent without actual MCP tools
    instruction = """
You are a calendar management specialist that helps users with calendar-related tasks.

Your capabilities:
- Viewing and searching calendar events
- Finding available time slots for meetings
- Creating new events
- Updating existing events
- Managing event attendees

IMPORTANT:
- Always ask for confirmation before creating or modifying events
- Consider user's time zone and working hours
- Suggest optimal meeting times based on availability

For testing purposes, you can simulate calendar operations.
Example responses:
- "Your next meeting is tomorrow at 10:00 AM"
- "You have 3 free slots available this week: Monday 2-3pm, Wednesday 11am-12pm, Friday 4-5pm"
- "I've scheduled a meeting for next Tuesday at 3pm"
"""
    
    # Build tools list (empty for testing, MCP tools would go here)
    tools_list = []
    if mcp_toolset:
        tools_list.append(mcp_toolset)
    
    calendar_agent = Agent(
        name="calendar_agent",
        instruction=instruction,
        model="gemini-2.0-flash-exp",
        tools=tools_list,
    )
    
    logger.info("Calendar agent built successfully")
    return calendar_agent


