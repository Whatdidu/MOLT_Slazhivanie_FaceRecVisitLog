"""
Trace ID utilities for request tracking.
"""
import uuid
from contextvars import ContextVar

# Context variable for storing trace ID per request
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")


def generate_trace_id() -> str:
    """
    Generate a new UUID-based trace ID.

    Returns:
        Trace ID string (UUID4)
    """
    return str(uuid.uuid4())


def get_trace_id() -> str:
    """
    Get current trace ID from context.

    Returns:
        Current trace ID or generates a new one if not set
    """
    trace_id = trace_id_var.get()
    if not trace_id:
        trace_id = generate_trace_id()
        trace_id_var.set(trace_id)
    return trace_id


def set_trace_id(trace_id: str) -> None:
    """
    Set trace ID in context.

    Args:
        trace_id: Trace ID to set
    """
    trace_id_var.set(trace_id)
