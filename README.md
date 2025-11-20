# Nodus ADK Agents

Agent definitions and domain logic for Nodus OS powered by Google ADK.

## Overview

This package contains all agent implementations for the Nodus OS ADK-based assistant system:

- **Root Agent**: Personal Assistant orchestrator (A2A coordinator)
- **Domain Agents**: Specialized agents for different capabilities
  - Email Agent
  - Calendar Agent
  - CRM Agent (stub)
  - ERP Agent (stub)
  - RAG Agent (stub)
  - Memory Agent (stub)

## Architecture

```
┌─────────────────┐
│   Root Agent    │  (Personal Assistant)
│   (A2A Router)  │
└────────┬────────┘
         │
         ├──► Email Agent ──► MCP (email tools)
         │
         ├──► Calendar Agent ──► MCP (calendar tools)
         │
         ├──► CRM Agent ──► MCP (CRM tools)
         │
         ├──► ERP Agent ──► MCP (ERP tools)
         │
         ├──► RAG Agent ──► Memory Layer
         │
         └──► Memory Agent ──► Memory Layer
```

## Agent Capabilities

### Root Agent (Personal Assistant)
- Intent understanding and classification
- Multi-agent orchestration (A2A)
- Context management
- Response composition
- HITL (Human-In-The-Loop) workflow

### Email Agent
- Search and list emails
- Read email content
- Draft replies
- Send emails (with HITL confirmation)
- Manage labels and organization

### Calendar Agent
- View calendar events
- Find free time slots
- Create events (with HITL confirmation)
- Update/delete events (with HITL confirmation)
- Manage attendees

### Domain Agents (Stubs)
CRM, ERP, RAG, and Memory agents are provided as stubs for future implementation.

## Usage

### Installation

```bash
pip install -e .
```

### Building Agents

```python
from nodus_adk_agents import (
    build_root_agent,
    build_email_agent,
    build_calendar_agent,
)

# Initialize services
mcp_toolset = ...  # From nodus-adk-runtime
memory_service = ...  # From nodus-adk-runtime

# Build domain agents
email_agent = build_email_agent(mcp_toolset, memory_service)
calendar_agent = build_calendar_agent(mcp_toolset, memory_service)

# Build root agent with domain agents
root_agent = build_root_agent(
    domain_agents=[email_agent, calendar_agent],
    mcp_toolset=mcp_toolset,
    memory_service=memory_service,
    config={"model": "gemini-2.0-flash-exp"},
)
```

## Agent Instructions

Each agent has carefully crafted instructions that define:
- Its role and capabilities
- How it interacts with tools (MCP)
- When to ask for confirmation (HITL)
- How to use memory and context

See individual agent files for detailed instructions.

## Development

### Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"
```

### Testing

```bash
pytest
```

### Code Quality

```bash
# Format
black src/

# Lint
ruff check src/

# Type check
mypy src/
```

## Package Structure

```
nodus-adk-agents/
├── src/
│   └── nodus_adk_agents/
│       ├── __init__.py
│       ├── root_agent.py        # PA orchestrator
│       ├── email_agent.py       # Email domain
│       ├── calendar_agent.py    # Calendar domain
│       ├── crm_agent.py         # CRM domain (stub)
│       ├── erp_agent.py         # ERP domain (stub)
│       ├── rag_agent.py         # RAG domain (stub)
│       └── memory_agent.py      # Memory domain (stub)
├── tests/
│   └── __init__.py
├── pyproject.toml
└── README.md
```

## Deployment

This package is installed as a dependency in `nodus-adk-runtime`:

```toml
[project.dependencies]
nodus-adk-agents = { git = "https://github.com/nodus-factory/nodus-adk-agents.git", tag = "v0.1.0" }
```

Or for development:
```toml
nodus-adk-agents = { git = "https://github.com/nodus-factory/nodus-adk-agents.git", branch = "main" }
```

## Adding New Agents

1. Create `new_agent.py` in `src/nodus_adk_agents/`
2. Implement `build_new_agent(mcp_toolset, memory_service)` function
3. Add to `__init__.py` exports
4. Document capabilities and instructions
5. Add tests in `tests/`

## HITL (Human-In-The-Loop)

Agents should request confirmation for:
- ✅ Sending emails
- ✅ Creating/modifying calendar events
- ✅ Creating/updating CRM records
- ✅ Financial transactions
- ❌ Reading/searching (no confirmation needed)

## Integration with MCP Gateway

Agents use MCP tools through the gateway:
- Tools are discovered at runtime
- Each tool has risk level and scope requirements
- Gateway handles auth, rate limits, and audit logs

## License

Copyright © 2024 Nodus Factory

## Links

- [Nodus ADK Runtime](../nodus-adk-runtime)
- [Nodus ADK Infra](../nodus-adk-infra)
- [ADK Python Fork](../adk-python)

