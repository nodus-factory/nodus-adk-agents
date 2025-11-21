"""
A2A Calculator Agent
Provides mathematical calculations without external dependencies
"""

import structlog
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import math

logger = structlog.get_logger()

# --- A2A Protocol Models ---
class AgentCard(BaseModel):
    name: str
    description: str
    capabilities: dict
    endpoint: str

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

# --- Calculator Specific Models ---
class CalculationResult(BaseModel):
    expression: str
    result: float
    explanation: str
    timestamp: datetime = Field(default_factory=datetime.now)

# --- FastAPI App ---
app = FastAPI(
    title="A2A Calculator Agent",
    description="Mathematical calculations agent with support for basic and advanced operations",
    version="1.0.0",
)

CALCULATOR_AGENT_CARD = AgentCard(
    name="calculator_agent",
    description="Mathematical calculations (addition, subtraction, multiplication, division, power, square root, percentages)",
    capabilities={
        "calculate": {
            "description": "Evaluate a mathematical expression",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate (e.g., '2 + 2', '15% of 200', 'sqrt(144)')"
                    }
                },
                "required": ["expression"]
            }
        },
        "percentage": {
            "description": "Calculate percentage of a number",
            "parameters": {
                "type": "object",
                "properties": {
                    "percentage": {"type": "number", "description": "Percentage value (e.g., 15 for 15%)"},
                    "of_value": {"type": "number", "description": "Base value"}
                },
                "required": ["percentage", "of_value"]
            }
        }
    },
    endpoint="http://localhost:8003/a2a"
)

# --- Helper Functions ---
def safe_eval_expression(expression: str) -> float:
    """
    Safely evaluate mathematical expressions
    Supports: +, -, *, /, **, sqrt, %, parentheses
    """
    # Replace common mathematical notations
    expression = expression.replace("^", "**")  # Power
    expression = expression.replace("√", "sqrt")
    
    # Handle percentage in expressions like "15% of 200"
    if "%" in expression and " of " in expression:
        parts = expression.split(" of ")
        if len(parts) == 2:
            percentage = float(parts[0].replace("%", "").strip())
            value = float(parts[1].strip())
            return (percentage / 100) * value
    
    # Safe math functions
    safe_dict = {
        'sqrt': math.sqrt,
        'pow': math.pow,
        'abs': abs,
        'round': round,
        'pi': math.pi,
        'e': math.e,
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'log': math.log,
        'log10': math.log10,
    }
    
    # Evaluate safely (no __builtins__ access)
    try:
        result = eval(expression, {"__builtins__": {}}, safe_dict)
        return float(result)
    except Exception as e:
        raise ValueError(f"Invalid expression: {str(e)}")

# --- A2A Endpoints ---
@app.get("/")
async def get_agent_card():
    return CALCULATOR_AGENT_CARD

@app.get("/health")
async def health_check():
    return {"status": "healthy", "agent": CALCULATOR_AGENT_CARD.name}

@app.post("/a2a")
async def handle_a2a_request(request: A2ARequest):
    logger.info("Received A2A request", method=request.method, params=request.params)
    
    try:
        if request.method == "calculate":
            expression = request.params.get("expression")
            if not expression:
                raise ValueError("Expression parameter is required")
            
            result = safe_eval_expression(expression)
            
            response_data = CalculationResult(
                expression=expression,
                result=result,
                explanation=f"The result of {expression} is {result}"
            )
            
            logger.info("Calculation completed", expression=expression, result=result)
            return A2AResponse(id=request.id, result=response_data.model_dump())
        
        elif request.method == "percentage":
            percentage = float(request.params.get("percentage"))
            of_value = float(request.params.get("of_value"))
            
            result = (percentage / 100) * of_value
            expression = f"{percentage}% of {of_value}"
            
            response_data = CalculationResult(
                expression=expression,
                result=result,
                explanation=f"{percentage}% of {of_value} is {result}"
            )
            
            logger.info("Percentage calculated", percentage=percentage, of_value=of_value, result=result)
            return A2AResponse(id=request.id, result=response_data.model_dump())
        
        else:
            raise HTTPException(status_code=404, detail="Method not found")
    
    except ValueError as e:
        logger.error("Calculation error", error=str(e))
        return A2AResponse(id=request.id, error={"code": -32000, "message": str(e)})
    except Exception as e:
        logger.error("Unexpected error", error=str(e))
        return A2AResponse(id=request.id, error={"code": -32002, "message": f"Unexpected error: {str(e)}"})

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting A2A Calculator Agent", endpoint=CALCULATOR_AGENT_CARD.endpoint)
    uvicorn.run(app, host="0.0.0.0", port=8003)

