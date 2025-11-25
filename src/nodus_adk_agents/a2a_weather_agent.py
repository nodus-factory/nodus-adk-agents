"""
Weather Agent A2A Server
Real weather data using Open-Meteo API (free, no API key needed)
"""

import asyncio
from datetime import datetime
from typing import Any, Dict

import httpx
import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .a2a_observability import (
    setup_observability,
    trace_async_function,
    add_span_event,
    set_span_attribute,
    instrument_fastapi_app,
)

logger = structlog.get_logger()

app = FastAPI(title="Weather Agent A2A")

# Setup OpenTelemetry + Langfuse observability
setup_observability(service_name="weather_agent")

# Open-Meteo API endpoint (free, no auth needed)
OPEN_METEO_API = "https://api.open-meteo.com/v1/forecast"

# City coordinates (can be extended)
CITY_COORDS = {
    "barcelona": {"lat": 41.3879, "lon": 2.1699},
    "madrid": {"lat": 40.4168, "lon": -3.7038},
    "valencia": {"lat": 39.4699, "lon": -0.3763},
    "sevilla": {"lat": 37.3891, "lon": -5.9845},
    "bilbao": {"lat": 43.2627, "lon": -2.9253},
}


@trace_async_function(
    name="get_weather_forecast",
    attributes={"agent": "weather_agent", "provider": "Open-Meteo"}
)
async def get_weather_forecast(city: str, days: int = 1) -> Dict[str, Any]:
    """
    Get real weather forecast from Open-Meteo API
    
    Args:
        city: City name (lowercase)
        days: Number of forecast days (1-7)
        
    Returns:
        Weather data with temperature, condition, precipitation, wind
    """
    city_lower = city.lower()
    
    # Add span event
    add_span_event("forecast_requested", {"city": city, "days": days})
    
    if city_lower not in CITY_COORDS:
        add_span_event("city_not_found", {"city": city})
        return {
            "error": f"City '{city}' not found. Available: {', '.join(CITY_COORDS.keys())}"
        }
    
    coords = CITY_COORDS[city_lower]
    
    # Log coordinates in span
    set_span_attribute("geo.latitude", coords["lat"])
    set_span_attribute("geo.longitude", coords["lon"])
    
    # Open-Meteo API parameters
    params = {
        "latitude": coords["lat"],
        "longitude": coords["lon"],
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_probability_max",
            "wind_speed_10m_max",
            "weather_code",
        ],
        "forecast_days": days,
        "timezone": "Europe/Madrid",
    }
    
    try:
        add_span_event("api_request_start", {"endpoint": OPEN_METEO_API})
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(OPEN_METEO_API, params=params)
            response.raise_for_status()
            data = response.json()
        
        add_span_event("api_request_success", {"status_code": response.status_code})
        
        # Parse response
        daily = data["daily"]
        
        # Weather code to description mapping (WMO codes)
        weather_descriptions = {
            0: "clar",
            1: "principalment clar",
            2: "parcialment ennuvolat",
            3: "ennuvolat",
            45: "boira",
            48: "boira amb gelada",
            51: "plugim lleuger",
            53: "plugim moderat",
            55: "plugim dens",
            61: "pluja lleuger",
            63: "pluja moderada",
            65: "pluja forta",
            71: "neu lleugera",
            73: "neu moderada",
            75: "neu forta",
            80: "xàfecs lleugers",
            81: "xàfecs moderats",
            82: "xàfecs forts",
            95: "tempesta",
        }
        
        forecasts = []
        for i in range(days):
            weather_code = daily["weather_code"][i]
            condition = weather_descriptions.get(weather_code, "desconegut")
            
            forecast = {
                "date": daily["time"][i],
                "temp_max": daily["temperature_2m_max"][i],
                "temp_min": daily["temperature_2m_min"][i],
                "condition": condition,
                "precipitation_prob": daily["precipitation_probability_max"][i],
                "wind_speed": daily["wind_speed_10m_max"][i],
            }
            forecasts.append(forecast)
        
        # Log forecast count in span
        set_span_attribute("forecast.count", len(forecasts))
        set_span_attribute("forecast.city", city)
        
        add_span_event("forecast_parsed", {"forecast_count": len(forecasts)})
        
        return {
            "city": city,
            "forecasts": forecasts,
            "source": "Open-Meteo API",
            "timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.error("Failed to fetch weather data", error=str(e), city=city)
        add_span_event("api_request_failed", {"error": str(e)})
        return {"error": f"Failed to fetch weather: {str(e)}"}


@app.get("/")
async def root():
    """Agent Card - A2A Discovery"""
    return {
        "name": "weather_agent",
        "description": "Real-time weather forecasts for Spanish cities using Open-Meteo API",
        "version": "1.0.0",
        "capabilities": {
            "get_forecast": {
                "description": "Get weather forecast for a city",
                "parameters": {
                    "city": {
                        "type": "string",
                        "description": "City name",
                        "enum": list(CITY_COORDS.keys()),
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of forecast days (1-7)",
                        "default": 1,
                        "minimum": 1,
                        "maximum": 7,
                    },
                },
                "returns": {
                    "forecasts": "Array of daily forecasts with temp, condition, precipitation",
                },
            }
        },
        "endpoint": "http://localhost:8001/a2a",
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
        
        # Handle method
        if method == "get_forecast":
            city = params.get("city", "barcelona")
            days = params.get("days", 1)
            
            result = await get_weather_forecast(city, days)
            
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "result": result,
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
    return {"status": "healthy", "agent": "weather_agent"}


if __name__ == "__main__":
    import uvicorn
    
    # Instrument FastAPI app
    instrument_fastapi_app(app)
    
    logger.info("Starting Weather Agent A2A Server", port=8001)
    uvicorn.run(app, host="0.0.0.0", port=8001)


