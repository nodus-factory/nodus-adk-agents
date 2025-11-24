"""
Root Agent (Personal Assistant)
"""

from google.adk.agents.llm_agent import Agent

def get_agent():
    """Create and return the root agent."""
    # TODO: Integrate with nodus-adk-runtime services
    # For now, create a simple agent
    agent = Agent(
        name="personal_assistant",
        instruction="""
        You are a helpful personal assistant that:
        - Understands user requests
        - Delegates to specialized agents (email, calendar, CRM, etc.)
        - Manages multi-step workflows
        - Provides clear, actionable responses
        """,
    )
    return agent


