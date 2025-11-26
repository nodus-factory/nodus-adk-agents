"""
HITL Math Agent A2A Server
Demonstrates HITL with user input for multiplication
"""

from datetime import datetime
from typing import Any, Dict, Optional

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os

logger = structlog.get_logger()

app = FastAPI(title="HITL Math Agent A2A")


async def multiply_with_confirmation(
    base_number: float,
    factor: float = 2.0,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Multiply a base number by a factor (requires HITL confirmation)
    
    Args:
        base_number: The base number to multiply
        factor: The multiplication factor (default: 2.0)
        user_id: Optional user ID for personalization
        
    Returns:
        HITL request asking user to confirm the multiplication
    """
    logger.info(
        "Multiplication with HITL requested",
        base_number=base_number,
        factor=factor,
        user_id=user_id,
    )
    
    # Return HITL marker - ADK Runtime will intercept this
    return {
        "status": "hitl_required",
        "action_type": "math_multiplication",
        "action_description": f"Multiplicar {base_number} per un número",
        "action_data": {
            "base_number": base_number,
            "factor": factor,  # Default factor if user doesn't provide one
            "operation": "multiplication",
            "input_type": "number",
        },
        "metadata": {
            "tool": "request_user_input",
            "input_type": "number"
        },
        "question": f"Per quin número vols multiplicar {base_number}?",
        "preview": f"Multiplicació de {base_number}",
    }


async def execute_multiplication(
    base_number: float,
    factor: float = 2.0,
) -> Dict[str, Any]:
    """
    Execute the multiplication (called after HITL confirmation)
    
    Args:
        base_number: The base number
        factor: The multiplication factor (default: 2.0)
        
    Returns:
        The multiplication result
    """
    result = base_number * factor
    
    logger.info(
        "Multiplication executed",
        base_number=base_number,
        factor=factor,
        result=result,
    )
    
    return {
        "base_number": base_number,
        "factor": factor,
        "result": result,
        "operation": "multiplication",
        "explanation": f"El resultat de {base_number} × {factor} és {result}",
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/a2a")
async def a2a_handler(request: Request):
    """Handle A2A JSON-RPC requests"""
    try:
        data = await request.json()
        method = data.get("method")
        params = data.get("params", {})
        request_id = data.get("id")
        
        logger.info(
            "A2A request received",
            method=method,
            params=params,
            request_id=request_id,
        )
        
        if method == "multiply_with_confirmation":
            result = await multiply_with_confirmation(**params)
        elif method == "execute_multiplication":
            result = await execute_multiplication(**params)
        else:
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32601,
                        "message": f"Method '{method}' not found",
                    },
                    "id": request_id,
                }
            )
        
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "result": result,
                "error": None,
                "id": request_id,
            }
        )
        
    except Exception as e:
        logger.error("A2A request failed", error=str(e))
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": str(e)},
                "id": request_id if "request_id" in locals() else None,
            }
        )


@app.get("/")
@app.get("/discover")
async def discover():
    """Return agent capabilities card"""
    return {
        "name": "hitl_math_agent",
        "version": "1.0.0",
        "description": "HITL Math Agent for interactive multiplication",
        "capabilities": {
            "multiply_with_confirmation": {
                "description": "Multiply a number by a factor with HITL confirmation (default factor: 2)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "base_number": {
                            "type": "number",
                            "description": "The base number to multiply",
                        },
                        "factor": {
                            "type": "number",
                            "description": "The multiplication factor (default: 2.0)",
                        },
                        "user_id": {
                            "type": "string",
                            "description": "Optional user ID",
                        },
                    },
                    "required": ["base_number"],
                },
                "returns": {
                    "description": "HITL confirmation request for multiplication",
                },
            },
            "execute_multiplication": {
                "description": "Execute multiplication (called after HITL confirmation)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "base_number": {
                            "type": "number",
                            "description": "The base number",
                        },
                        "factor": {
                            "type": "number",
                            "description": "The multiplication factor (default: 2.0)",
                        },
                    },
                    "required": ["base_number"],
                },
                "returns": {
                    "description": "The multiplication result",
                },
            },
        },
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "agent": "hitl_math_agent"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)

