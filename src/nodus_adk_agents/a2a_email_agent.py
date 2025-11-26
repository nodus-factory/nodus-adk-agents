"""
A2A Email Agent with HITL confirmation
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import structlog
from datetime import datetime
import os

logger = structlog.get_logger()

app = FastAPI(
    title="A2A Email Agent with HITL",
    description="Send emails with mandatory human confirmation",
    version="0.1.0"
)


# --- A2A Protocol Models ---
class A2ARequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: dict
    id: int


class A2AResponse(BaseModel):
    jsonrpc: str = "2.0"
    result: dict = {}
    error: Optional[dict] = None
    id: int


class AgentCard(BaseModel):
    name: str
    description: str
    capabilities: dict
    endpoint: str


# --- Agent Card ---
EMAIL_AGENT_CARD = AgentCard(
    name="email_agent",
    description="Send emails with HITL confirmation (requires human approval)",
    capabilities={
        "send_email": {
            "description": "Send an email (requires human confirmation before sending)",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "Recipient email address"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject line"
                    },
                    "body": {
                        "type": "string",
                        "description": "Email body content"
                    },
                    "cc": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "CC recipients (optional)"
                    },
                    "bcc": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "BCC recipients (optional)"
                    }
                },
                "required": ["to", "subject", "body"]
            }
        },
        "check_inbox": {
            "description": "Check inbox for new emails (no confirmation required)",
            "parameters": {
                "type": "object",
                "properties": {
                    "unread_only": {
                        "type": "boolean",
                        "description": "Only show unread emails",
                        "default": True
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of emails to return",
                        "default": 10
                    }
                }
            }
        }
    },
    endpoint="http://localhost:8004/a2a"
)


# --- Helper Functions ---
def simulate_email_send(to: str, subject: str, body: str, cc: List[str] = None, bcc: List[str] = None) -> dict:
    """Simulate sending an email (HITL approved action)"""
    logger.info(
        "Email sent (simulated)",
        to=to,
        subject=subject,
        cc=cc or [],
        bcc=bcc or []
    )
    return {
        "status": "sent",
        "message_id": f"msg_{datetime.now().timestamp()}",
        "to": to,
        "subject": subject,
        "sent_at": datetime.now().isoformat(),
        "note": "Email sent successfully (simulated)"
    }


def simulate_check_inbox(unread_only: bool = True, limit: int = 10) -> dict:
    """Simulate checking inbox"""
    # Simulated emails
    emails = [
        {
            "id": "email_001",
            "from": "john@example.com",
            "subject": "Project X Update",
            "preview": "Hi, here's the latest update on Project X...",
            "date": "2025-11-23T10:30:00Z",
            "unread": True
        },
        {
            "id": "email_002",
            "from": "sarah@example.com",
            "subject": "Meeting Schedule",
            "preview": "Can we reschedule our meeting for next week?",
            "date": "2025-11-23T09:15:00Z",
            "unread": True
        },
        {
            "id": "email_003",
            "from": "notifications@system.com",
            "subject": "System Alert",
            "preview": "Your account has been updated...",
            "date": "2025-11-22T16:45:00Z",
            "unread": False
        }
    ]
    
    if unread_only:
        emails = [e for e in emails if e["unread"]]
    
    return {
        "emails": emails[:limit],
        "total_count": len(emails),
        "unread_count": sum(1 for e in emails if e["unread"])
    }


# --- A2A Endpoints ---
@app.get("/")
async def get_agent_card():
    """Return agent card for discovery"""
    return EMAIL_AGENT_CARD


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "agent": EMAIL_AGENT_CARD.name}


@app.post("/a2a")
async def handle_a2a_request(request: A2ARequest):
    """Handle A2A requests with HITL support"""
    logger.info("Email agent request", method=request.method, params=request.params)
    
    try:
        if request.method == "send_email":
            to = request.params.get("to")
            subject = request.params.get("subject")
            body = request.params.get("body")
            cc = request.params.get("cc", [])
            bcc = request.params.get("bcc", [])
            
            if not to or not subject or not body:
                return A2AResponse(
                    id=request.id,
                    error={"code": -32602, "message": "Missing required parameters: to, subject, body"}
                )
            
            # Return HITL required status
            # The Root Agent will detect this and create a HITL confirmation
            response_data = {
                "status": "hitl_required",
                "action_type": "send_email",
                "action_description": f"Send email to {to}",
                "action_data": {
                    "to": to,
                    "subject": subject,
                    "body": body,
                    "cc": cc,
                    "bcc": bcc
                },
                "question": f"Do you want to send an email to {to} with subject '{subject}'?",
                "preview": {
                    "to": to,
                    "subject": subject,
                    "body_preview": body[:100] + "..." if len(body) > 100 else body,
                    "cc": cc,
                    "bcc": bcc
                }
            }
            
            logger.info("Email agent requires HITL", to=to, subject=subject)
            return A2AResponse(id=request.id, result=response_data)
        
        elif request.method == "check_inbox":
            unread_only = request.params.get("unread_only", True)
            limit = request.params.get("limit", 10)
            
            # Check inbox does NOT require HITL (read-only operation)
            inbox_data = simulate_check_inbox(unread_only, limit)
            
            logger.info(
                "Email inbox checked",
                unread_only=unread_only,
                limit=limit,
                found=len(inbox_data["emails"])
            )
            
            return A2AResponse(id=request.id, result=inbox_data)
        
        else:
            return A2AResponse(
                id=request.id,
                error={"code": -32601, "message": f"Method not found: {request.method}"}
            )
    
    except Exception as e:
        logger.error("Error handling A2A request", method=request.method, error=str(e))
        return A2AResponse(
            id=request.id,
            error={"code": -32000, "message": f"Internal error: {str(e)}"}
        )


# --- Execute Approved Action ---
@app.post("/a2a/execute")
async def execute_approved_action(request: dict):
    """
    Execute an action that has been approved via HITL
    
    This endpoint is called AFTER the user approves the action.
    The Root Agent will call this with the original action_data.
    """
    try:
        action_type = request.get("action_type")
        action_data = request.get("action_data", {})
        
        if action_type == "send_email":
            result = simulate_email_send(
                to=action_data["to"],
                subject=action_data["subject"],
                body=action_data["body"],
                cc=action_data.get("cc", []),
                bcc=action_data.get("bcc", [])
            )
            return {"status": "success", "result": result}
        
        return {"status": "error", "message": f"Unknown action type: {action_type}"}
    
    except Exception as e:
        logger.error("Error executing approved action", error=str(e))
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting A2A Email Agent with HITL", endpoint=EMAIL_AGENT_CARD.endpoint)
    uvicorn.run(app, host="0.0.0.0", port=8004)


