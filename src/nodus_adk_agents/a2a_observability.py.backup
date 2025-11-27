"""
OpenTelemetry Instrumentation for A2A Agents
Provides generous spans and tracing for all agent operations
"""

import functools
import os
from typing import Any, Callable, Dict, Optional

import structlog
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.trace import Status, StatusCode
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

logger = structlog.get_logger()

# Global tracer instance
_tracer: Optional[trace.Tracer] = None
_initialized = False


def setup_observability(
    service_name: str,
    langfuse_host: str = "http://langfuse:3000",
    otel_endpoint: Optional[str] = None,
) -> bool:
    """
    Setup OpenTelemetry + Langfuse for an A2A agent
    
    Args:
        service_name: Name of the agent (e.g., "weather_agent")
        langfuse_host: Langfuse host URL
        otel_endpoint: OTLP endpoint (defaults to Langfuse ingestion)
        
    Returns:
        True if setup successful, False otherwise
    """
    global _tracer, _initialized
    
    if _initialized:
        logger.info("Observability already initialized", service=service_name)
        return True
    
    try:
        # Default OTLP endpoint to Langfuse
        if not otel_endpoint:
            otel_endpoint = f"{langfuse_host}/api/public/ingestion"
        
        logger.info(
            "Setting up observability for A2A agent",
            service=service_name,
            endpoint=otel_endpoint,
        )
        
        # Create resource with service name
        resource = Resource.create({
            "service.name": service_name,
            "service.version": "1.0.0",
            "deployment.environment": os.getenv("ENVIRONMENT", "development"),
        })
        
        # Create tracer provider
        provider = TracerProvider(resource=resource)
        
        # Create OTLP exporter for Langfuse
        otlp_exporter = OTLPSpanExporter(
            endpoint=otel_endpoint,
            headers={"Content-Type": "application/json"},
        )
        
        # Add span processor
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        
        # Set as global tracer provider
        trace.set_tracer_provider(provider)
        
        # Get tracer instance
        _tracer = trace.get_tracer(service_name)
        
        # Instrument HTTP client (for external API calls)
        HTTPXClientInstrumentor().instrument()
        
        _initialized = True
        
        logger.info(
            "✅ Observability setup complete",
            service=service_name,
            endpoint=otel_endpoint,
        )
        
        return True
        
    except Exception as e:
        logger.error(
            "Failed to setup observability",
            service=service_name,
            error=str(e),
        )
        return False


def get_tracer() -> trace.Tracer:
    """Get the global tracer instance"""
    global _tracer
    if not _tracer:
        # Fallback to no-op tracer if not initialized
        _tracer = trace.get_tracer(__name__)
    return _tracer


def trace_async_function(
    name: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
) -> Callable:
    """
    Decorator to trace async functions with generous spans
    
    Args:
        name: Custom span name (defaults to function name)
        attributes: Additional span attributes
        
    Example:
        @trace_async_function(name="fetch_weather", attributes={"provider": "OpenMeteo"})
        async def get_weather(city: str):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            tracer = get_tracer()
            span_name = name or func.__name__
            
            with tracer.start_as_current_span(span_name) as span:
                # Add function metadata
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                # Add custom attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, str(value))
                
                # Add function arguments as span attributes (generous logging)
                for i, arg in enumerate(args):
                    span.set_attribute(f"arg.{i}", str(arg))
                
                for key, value in kwargs.items():
                    # Convert to string for OpenTelemetry compatibility
                    span.set_attribute(f"param.{key}", str(value))
                
                try:
                    # Execute function
                    result = await func(*args, **kwargs)
                    
                    # Log result (generous span data)
                    if isinstance(result, dict):
                        # Add result metadata
                        if "error" in result:
                            span.set_status(Status(StatusCode.ERROR))
                            span.set_attribute("error.message", str(result["error"]))
                        else:
                            span.set_status(Status(StatusCode.OK))
                            # Add result keys as attributes
                            for key in result.keys():
                                span.set_attribute(f"result.{key}", "present")
                    
                    return result
                    
                except Exception as e:
                    # Record exception
                    span.set_status(Status(StatusCode.ERROR))
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    span.record_exception(e)
                    raise
        
        return wrapper
    return decorator


def trace_function(
    name: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
) -> Callable:
    """
    Decorator to trace sync functions with generous spans
    
    Args:
        name: Custom span name (defaults to function name)
        attributes: Additional span attributes
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            span_name = name or func.__name__
            
            with tracer.start_as_current_span(span_name) as span:
                # Add function metadata
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                # Add custom attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, str(value))
                
                # Add function arguments
                for i, arg in enumerate(args):
                    span.set_attribute(f"arg.{i}", str(arg))
                
                for key, value in kwargs.items():
                    span.set_attribute(f"param.{key}", str(value))
                
                try:
                    # Execute function
                    result = func(*args, **kwargs)
                    
                    # Log result
                    if isinstance(result, dict):
                        if "error" in result:
                            span.set_status(Status(StatusCode.ERROR))
                            span.set_attribute("error.message", str(result["error"]))
                        else:
                            span.set_status(Status(StatusCode.OK))
                            for key in result.keys():
                                span.set_attribute(f"result.{key}", "present")
                    
                    return result
                    
                except Exception as e:
                    # Record exception
                    span.set_status(Status(StatusCode.ERROR))
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    span.record_exception(e)
                    raise
        
        return wrapper
    return decorator


def add_span_event(name: str, attributes: Optional[Dict[str, Any]] = None):
    """
    Add an event to the current span
    
    Args:
        name: Event name
        attributes: Event attributes
    """
    current_span = trace.get_current_span()
    if current_span:
        current_span.add_event(name, attributes=attributes or {})


def set_span_attribute(key: str, value: Any):
    """
    Set an attribute on the current span
    
    Args:
        key: Attribute key
        value: Attribute value
    """
    current_span = trace.get_current_span()
    if current_span:
        current_span.set_attribute(key, str(value))


def instrument_fastapi_app(app):
    """
    Instrument a FastAPI app with OpenTelemetry
    
    Args:
        app: FastAPI app instance
    """
    try:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI app instrumented with OpenTelemetry")
    except Exception as e:
        logger.warning("Failed to instrument FastAPI app", error=str(e))

