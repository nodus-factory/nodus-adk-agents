"""
Stub for a2a_observability when OpenTelemetry is not available.
Provides no-op functions to avoid import errors.
"""

import structlog

logger = structlog.get_logger()


def setup_observability(service_name: str, **kwargs):
    """No-op observability setup"""
    logger.debug("Observability disabled (OpenTelemetry not installed)", service=service_name)


def trace_async_function(func=None, *, name=None, **kwargs):
    """No-op async function tracer (decorator with optional args)"""
    if func is None:
        # Called with arguments: @trace_async_function(name="foo")
        def wrapper(f):
            return f
        return wrapper
    # Called without arguments: @trace_async_function
    return func


def trace_function(func=None, *, name=None, **kwargs):
    """No-op function tracer (decorator with optional args)"""
    if func is None:
        # Called with arguments: @trace_function(name="foo")
        def wrapper(f):
            return f
        return wrapper
    # Called without arguments: @trace_function
    return func


def add_span_event(name: str, attributes: dict = None):
    """No-op span event"""
    pass


def set_span_attribute(key: str, value):
    """No-op span attribute"""
    pass


def instrument_fastapi_app(app):
    """No-op FastAPI instrumentation"""
    pass

