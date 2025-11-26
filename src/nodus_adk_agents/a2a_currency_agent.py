"""
Currency Converter Agent A2A Server
Real exchange rates using ExchangeRate-API.com (free, no API key needed)
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

try:
    from .a2a_observability import (
        setup_observability,
        trace_async_function,
        add_span_event,
        set_span_attribute,
        instrument_fastapi_app,
    )
except ImportError:
    from .a2a_observability_stub import (
        setup_observability,
        trace_async_function,
        add_span_event,
        set_span_attribute,
        instrument_fastapi_app,
    )

logger = structlog.get_logger()

app = FastAPI(title="Currency Converter Agent A2A")

# Setup OpenTelemetry + Langfuse observability
# Read from env vars for flexibility (works in pool or standalone)
import os
setup_observability(
    service_name="currency_agent",
    langfuse_host=os.getenv("LANGFUSE_HOST", "http://localhost:3000"),
    otel_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
)

# ExchangeRate-API endpoint (free, no auth needed, more stable than Frankfurter)
EXCHANGE_API = "https://api.exchangerate-api.com/v4/latest"

# Supported currencies
SUPPORTED_CURRENCIES = [
    "EUR", "USD", "GBP", "JPY", "CHF", "CAD", "AUD", "CNY", "INR", "BRL",
    "MXN", "ZAR", "SEK", "NOK", "DKK", "PLN", "CZK", "HUF", "RON", "BGN",
    "HRK", "ISK", "TRY", "RUB", "KRW", "HKD", "SGD", "NZD", "THB", "MYR",
]


@trace_async_function(
    name="get_exchange_rate",
    attributes={"agent": "currency_agent", "provider": "ExchangeRate-API"}
)
async def get_exchange_rate(
    from_currency: str,
    to_currency: str,
    amount: float = 1.0,
) -> Dict[str, Any]:
    """
    Get real-time exchange rate from ExchangeRate-API
    
    Args:
        from_currency: Source currency code (e.g., "EUR")
        to_currency: Target currency code (e.g., "USD")
        amount: Amount to convert (default: 1.0)
        
    Returns:
        Exchange rate data with converted amount
    """
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()
    
    # Add span event
    add_span_event("exchange_rate_requested", {
        "from": from_currency,
        "to": to_currency,
        "amount": amount
    })
    
    if from_currency not in SUPPORTED_CURRENCIES:
        return {
            "error": f"Currency '{from_currency}' not supported. Available: {', '.join(SUPPORTED_CURRENCIES[:10])}..."
        }
    
    if to_currency not in SUPPORTED_CURRENCIES:
        return {
            "error": f"Currency '{to_currency}' not supported. Available: {', '.join(SUPPORTED_CURRENCIES[:10])}..."
        }
    
    try:
        add_span_event("api_request_start", {"endpoint": EXCHANGE_API})
        
        # ExchangeRate-API request (simpler, more stable)
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            response = await client.get(f"{EXCHANGE_API}/{from_currency}")
            response.raise_for_status()
            data = response.json()
        
        add_span_event("api_request_success", {"status_code": response.status_code})
        
        # Parse response
        if to_currency not in data["rates"]:
            return {"error": f"Currency '{to_currency}' not found in rates"}
        
        rate = data["rates"][to_currency]
        converted_amount = amount * rate
        
        # Log conversion details in span
        set_span_attribute("exchange.rate", rate)
        set_span_attribute("exchange.converted_amount", converted_amount)
        add_span_event("conversion_completed", {"rate": rate, "result": converted_amount})
        
        return {
            "from_currency": from_currency,
            "to_currency": to_currency,
            "amount": amount,
            "rate": rate,
            "converted_amount": converted_amount,
            "date": data.get("date", datetime.now().strftime("%Y-%m-%d")),
            "source": "ExchangeRate-API",
            "timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.error(
            "Failed to fetch exchange rate",
            error=str(e),
            from_currency=from_currency,
            to_currency=to_currency,
        )
        return {"error": f"Failed to fetch exchange rate: {str(e)}"}


@trace_async_function(
    name="convert_multiple",
    attributes={"agent": "currency_agent", "provider": "ExchangeRate-API"}
)
async def convert_multiple(
    from_currency: str,
    to_currencies: List[str],
    amount: float = 1.0,
) -> Dict[str, Any]:
    """
    Convert to multiple currencies at once
    
    Args:
        from_currency: Source currency code
        to_currencies: List of target currency codes
        amount: Amount to convert
        
    Returns:
        Multiple conversion results
    """
    from_currency = from_currency.upper()
    to_currencies = [c.upper() for c in to_currencies]
    
    add_span_event("multiple_conversion_requested", {
        "from": from_currency,
        "to_count": len(to_currencies),
        "amount": amount
    })
    
    try:
        # ExchangeRate-API returns all rates, filter what we need
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            response = await client.get(f"{EXCHANGE_API}/{from_currency}")
            response.raise_for_status()
            data = response.json()
        
        # Parse response and filter requested currencies
        conversions = []
        for currency in to_currencies:
            if currency in data["rates"]:
                rate = data["rates"][currency]
                conversions.append({
                    "to_currency": currency,
                    "rate": rate,
                    "converted_amount": amount * rate,
                })
            else:
                conversions.append({
                    "to_currency": currency,
                    "error": f"Currency '{currency}' not found",
                })
        
        return {
            "from_currency": from_currency,
            "amount": amount,
            "conversions": conversions,
            "date": data.get("date", datetime.now().strftime("%Y-%m-%d")),
            "source": "ExchangeRate-API",
            "timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.error(
            "Failed to convert multiple currencies",
            error=str(e),
            from_currency=from_currency,
        )
        return {"error": f"Failed to convert: {str(e)}"}


@app.get("/")
async def root():
    """Agent Card - A2A Discovery"""
    return {
        "name": "currency_agent",
        "description": "Real-time currency conversion using ExchangeRate-API (stable, free)",
        "version": "1.0.0",
        "capabilities": {
            "convert": {
                "description": "Convert amount from one currency to another",
                "parameters": {
                    "from_currency": {
                        "type": "string",
                        "description": "Source currency code (e.g., EUR, USD)",
                        "enum": SUPPORTED_CURRENCIES,
                    },
                    "to_currency": {
                        "type": "string",
                        "description": "Target currency code",
                        "enum": SUPPORTED_CURRENCIES,
                    },
                    "amount": {
                        "type": "number",
                        "description": "Amount to convert",
                        "default": 1.0,
                        "minimum": 0.01,
                    },
                },
                "returns": {
                    "rate": "Exchange rate",
                    "converted_amount": "Converted amount",
                },
            },
            "convert_multiple": {
                "description": "Convert to multiple currencies at once",
                "parameters": {
                    "from_currency": {
                        "type": "string",
                        "description": "Source currency code",
                        "enum": SUPPORTED_CURRENCIES,
                    },
                    "to_currencies": {
                        "type": "array",
                        "description": "List of target currency codes",
                        "items": {"type": "string", "enum": SUPPORTED_CURRENCIES},
                    },
                    "amount": {
                        "type": "number",
                        "description": "Amount to convert",
                        "default": 1.0,
                    },
                },
                "returns": {
                    "conversions": "Array of conversion results",
                },
            },
            "supported_currencies": {
                "description": "Get list of supported currencies",
                "parameters": {},
                "returns": {
                    "currencies": "Array of currency codes",
                },
            },
        },
        "endpoint": "http://localhost:8002/a2a",
        "protocol": "A2A",
        "transport": "JSON-RPC 2.0 over HTTP",
    }


@app.post("/a2a")
async def handle_a2a_request(request: Request):
    """
    A2A JSON-RPC 2.0 endpoint
    """
    try:
        body = await request.json()
        
        logger.info("A2A request received", method=body.get("method"), id=body.get("id"))
        
        # Validate JSON-RPC 2.0 format
        if body.get("jsonrpc") != "2.0":
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "error": {"code": -32600, "message": "Invalid Request"},
                    "id": body.get("id"),
                },
                status_code=400,
            )
        
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")
        
        # Handle methods
        if method == "convert":
            from_currency = params.get("from_currency", "EUR")
            to_currency = params.get("to_currency", "USD")
            amount = params.get("amount", 1.0)
            
            result = await get_exchange_rate(from_currency, to_currency, amount)
            
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "result": result,
                    "id": request_id,
                }
            )
        
        elif method == "convert_multiple":
            from_currency = params.get("from_currency", "EUR")
            to_currencies = params.get("to_currencies", ["USD", "GBP"])
            amount = params.get("amount", 1.0)
            
            result = await convert_multiple(from_currency, to_currencies, amount)
            
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "result": result,
                    "id": request_id,
                }
            )
        
        elif method == "supported_currencies":
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "result": {
                        "currencies": SUPPORTED_CURRENCIES,
                        "count": len(SUPPORTED_CURRENCIES),
                    },
                    "id": request_id,
                }
            )
        
        else:
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}",
                    },
                    "id": request_id,
                },
                status_code=404,
            )
    
    except Exception as e:
        logger.error("A2A request failed", error=str(e))
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
                "id": body.get("id") if "body" in locals() else None,
            },
            status_code=500,
        )


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "agent": "currency_agent"}


if __name__ == "__main__":
    import uvicorn
    
    # Instrument FastAPI app
    instrument_fastapi_app(app)
    
    logger.info("Starting Currency Converter Agent A2A Server", port=8002)
    uvicorn.run(app, host="0.0.0.0", port=8002)

