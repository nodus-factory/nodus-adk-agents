"""
Google Workspace A2A Server

Exposes Google Workspace agent as an A2A service.
Handles Gmail, Calendar, Drive, Docs, Sheets operations.
"""

from typing import Any, Dict, Optional
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import structlog

logger = structlog.get_logger()

app = FastAPI()

# Agent Card - Describes capabilities to Root Agent
GOOGLE_WORKSPACE_CARD = {
    "name": "google_workspace_agent",
    "description": "Specialist in Google Workspace (Gmail, Calendar, Drive, Docs, Sheets). Understands Gmail search syntax and chains operations using memory.",
    "version": "1.0.0",
    "capabilities": {
        "search_emails": {
            "description": "Search emails with natural language queries. Understands: 'emails no llegits', 'emails de [sender]', 'emails d'avui', etc.",
            "parameters": {
                "query": {
                    "type": "string",
                    "description": "Natural language query (e.g., 'emails no llegits de John', 'emails importants d'avui')",
                    "required": True
                },
                "max_results": {
                    "type": "integer",
                    "description": "Number of results to return (default: 10)",
                    "required": False
                }
            },
            "returns": "List of emails with IDs, subjects, senders, snippets"
        },
        "read_email": {
            "description": "Read full email content. Can use message_id from previous search or query memory.",
            "parameters": {
                "message_id": {
                    "type": "string",
                    "description": "Gmail message ID (optional if context available)",
                    "required": False
                },
                "reference": {
                    "type": "string",
                    "description": "Reference like 'el primer', 'l'últim', 'el segon' (uses memory)",
                    "required": False
                }
            },
            "returns": "Full email content (subject, from, to, body)"
        },
        "send_email": {
            "description": "Send email or reply. Can resolve recipient from memory.",
            "parameters": {
                "to": {
                    "type": "string",
                    "description": "Recipient email (optional if replying or context available)",
                    "required": False
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject",
                    "required": True
                },
                "body": {
                    "type": "string",
                    "description": "Email body",
                    "required": True
                },
                "is_reply": {
                    "type": "boolean",
                    "description": "True if replying to previous email (uses memory for thread_id)",
                    "required": False
                }
            },
            "returns": "Confirmation of sent email"
        },
        "list_calendar": {
            "description": "List calendar events. Understands: 'avui', 'demà', 'aquesta setmana', etc.",
            "parameters": {
                "time_range": {
                    "type": "string",
                    "description": "Natural language time range (e.g., 'avui', 'aquesta setmana', 'demà')",
                    "required": False
                }
            },
            "returns": "List of calendar events with time, title, location, attendees"
        },
        "search_drive": {
            "description": "Search files in Google Drive",
            "parameters": {
                "query": {
                    "type": "string",
                    "description": "Search query (file name, content, etc.)",
                    "required": True
                }
            },
            "returns": "List of files with IDs, names, types"
        },
        "read_document": {
            "description": "Read content from Google Doc or Drive file",
            "parameters": {
                "file_id": {
                    "type": "string",
                    "description": "File ID from previous search (optional if context available)",
                    "required": False
                },
                "reference": {
                    "type": "string",
                    "description": "Reference like 'el primer document' (uses memory)",
                    "required": False
                }
            },
            "returns": "File content"
        }
    }
}


@app.get("/")
async def get_card():
    """Return Agent Card for discovery"""
    return GOOGLE_WORKSPACE_CARD


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "agent": GOOGLE_WORKSPACE_CARD["name"]}


@app.post("/a2a")
async def handle_a2a_request(request: Request):
    """
    Handle A2A requests for Google Workspace operations.
    
    This endpoint receives high-level requests from Root Agent and
    translates them into specific MCP tool calls by building and running
    the Google Workspace agent.
    """
    body = await request.json()
    method = body.get("method")
    params = body.get("params", {})
    request_id = body.get("id", "1")
    
    logger.info(
        "Google Workspace agent A2A request",
        method=method,
        params=params,
        request_id=request_id
    )
    
    try:
        # Import necessary modules
        from nodus_adk_agents.google_workspace_agent import build_google_workspace_agent
        from nodus_adk_runtime.adapters.nodus_mcp_toolset import NodusMcpToolset
        from nodus_adk_runtime.adapters.mcp_adapter import MCPAdapter
        from nodus_adk_runtime.middleware.auth import UserContext
        from nodus_adk_runtime.config import settings
        from google.adk.runners import Runner
        from google.genai import types as genai_types
        
        # Extract user context from request headers (if available)
        # For now, use a default context
        user_context = UserContext(
            sub="default_user",
            tenant_id="t_default",
            scopes=["mcp:*", "google:*"],
            raw_token="",
            email="default@mynodus.com"
        )
        
        # Build MCP adapter
        mcp_adapter = MCPAdapter(gateway_url=settings.mcp_gateway_url)
        
        # Build Google Workspace MCP toolset
        google_toolset = NodusMcpToolset(
            mcp_adapter=mcp_adapter,
            user_context=user_context,
            server_id="google-workspace",
            tool_filter=None,  # All Google tools
            tool_name_prefix="google_",
        )
        
        # Build Google Workspace agent
        agent = build_google_workspace_agent(
            mcp_toolset=google_toolset,
            memory_service=None  # TODO: Add memory service if needed
        )
        
        # Create a synthetic user message based on the method
        user_message = _create_user_message_from_method(method, params)
        
        logger.info(
            "Running Google Workspace agent",
            method=method,
            user_message=user_message[:100]
        )
        
        # Run the agent
        runner = Runner(
            app_name="google_workspace_assistant",
            agent=agent,
        )
        
        # Collect agent response
        response_text = ""
        async for event in runner.run_async(
            user_content=genai_types.Content(
                role="user",
                parts=[genai_types.Part.from_text(text=user_message)],
            )
        ):
            if hasattr(event, 'text') and event.text:
                response_text += event.text
        
        logger.info(
            "Google Workspace agent response",
            method=method,
            response_length=len(response_text)
        )
        
        # Return the agent's response
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "status": "success",
                "response": response_text,
                "method": method
            }
        })
    
    except Exception as e:
        logger.error(
            "Google Workspace agent error",
            method=method,
            error=str(e),
            error_type=type(e).__name__
        )
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        })


def _create_user_message_from_method(method: str, params: Dict[str, Any]) -> str:
    """
    Create a natural language user message from A2A method and params.
    This allows the Google Workspace agent to process the request naturally.
    """
    if method == "search_emails":
        query = params.get("query", "")
        max_results = params.get("max_results", 10)
        if query:
            return f"Busca emails amb la query: {query}. Màxim {max_results} resultats."
        else:
            return f"Quins emails tinc? Mostra els últims {max_results}."
    
    elif method == "read_email":
        message_id = params.get("message_id")
        if message_id:
            return f"Llegeix l'email amb ID: {message_id}"
        else:
            return "Llegeix l'últim email"
    
    elif method == "send_email":
        to = params.get("to")
        subject = params.get("subject", "")
        body = params.get("body", "")
        return f"Envia un email a {to} amb assumpte '{subject}' i cos: {body}"
    
    elif method == "list_calendar":
        time_range = params.get("time_range", "avui")
        return f"Què tinc a l'agenda {time_range}?"
    
    elif method == "search_drive":
        query = params.get("query", "")
        return f"Busca fitxers a Drive: {query}"
    
    elif method == "read_document":
        file_id = params.get("file_id")
        if file_id:
            return f"Llegeix el document amb ID: {file_id}"
        else:
            return "Llegeix l'últim document"
    
    else:
        return f"Executa l'operació: {method} amb paràmetres: {params}"


# For testing
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

