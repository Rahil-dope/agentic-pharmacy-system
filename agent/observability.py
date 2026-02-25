from __future__ import annotations

"""
Langfuse observability helpers for the Agentic AI Pharmacy Assistant System.

This module centralizes all interaction with Langfuse so that the rest of the
agent code only needs to call simple helper functions. If Langfuse is not
configured or fails, all functions in this module degrade gracefully and do
not raise errors.
"""

from contextlib import nullcontext
from datetime import datetime
from typing import Any, ContextManager, Dict, Optional

from langfuse import get_client

from config import LANGFUSE_HOST


try:
    # The client picks up credentials and base URL from environment variables.
    _langfuse = get_client()
except Exception:  # noqa: BLE001
    _langfuse = None


def _is_enabled() -> bool:
    return _langfuse is not None


def create_trace(customer_id: int, user_input: str) -> ContextManager[Any]:
    """
    Create a root observation for an agent run.

    Returns a context manager that yields the underlying Langfuse span object.
    If Langfuse is not configured, a no-op context manager is returned.
    """
    if not _is_enabled():
        return nullcontext()

    metadata = {
        "customer_id": customer_id,
        "timestamp": datetime.utcnow().isoformat(),
    }
    return _langfuse.start_as_current_observation(
        as_type="span",
        name="pharmacy-agent-run",
        input={"customer_id": customer_id, "user_input": user_input},
        metadata=metadata,
    )


def create_span(trace: Any, name: str, as_type: str = "span", **kwargs: Any) -> ContextManager[Any]:
    """
    Create a child span or generation under the current trace.

    The `trace` argument is accepted for API symmetry but is not required when
    using Langfuse's context propagation. A no-op context manager is returned
    if Langfuse is disabled.
    """
    if not _is_enabled():
        return nullcontext()

    return _langfuse.start_as_current_observation(
        as_type=as_type,
        name=name,
        **kwargs,
    )


def log_generation(observation: Any, messages: Any, response: Any, model: str) -> None:
    """
    Log an LLM generation, including input messages and raw response payload.
    """
    if not _is_enabled() or observation is None:
        return

    try:
        observation.update(
            input={"messages": messages},
            output=response,
            metadata={"type": "llm-generation", "model": model},
        )
    except Exception:  # noqa: BLE001
        # Never let observability failures impact the agent.
        return


def log_tool_call(trace: Any, tool_name: str, arguments: Dict[str, Any], result: Any) -> None:
    """
    Log a backend tool call as its own span.
    """
    if not _is_enabled():
        return

    try:
        with _langfuse.start_as_current_observation(
            as_type="span",
            name=f"tool:{tool_name}",
        ) as span:
            span.update(
                input={"tool_name": tool_name, "arguments": arguments},
                output=result,
                metadata={"type": "tool-call"},
            )
    except Exception:  # noqa: BLE001
        return


def end_trace(trace: Any, output: Dict[str, Any], error: Optional[BaseException] = None) -> Dict[str, Optional[str]]:
    """
    Mark the trace as complete and attach the final output and optional error.

    Returns a dictionary containing the Langfuse trace id and a best-effort
    trace URL (if available).
    """
    trace_id: Optional[str] = None
    try:
        if trace is not None:
            update_payload: Dict[str, Any] = {"output": output}
            if error is not None:
                update_payload.setdefault("metadata", {})["error"] = str(error)
            trace.update(**update_payload)

            trace_id = getattr(trace, "trace_id", None)
    except Exception:  # noqa: BLE001
        # Ignore failures; we still return whatever trace information we have.
        pass

    base_url = (LANGFUSE_HOST or "https://cloud.langfuse.com").rstrip("/")
    trace_url: Optional[str] = None
    if trace_id:
        # Langfuse supports direct trace URLs of the form /trace/{trace_id}.
        trace_url = f"{base_url}/trace/{trace_id}"

    return {"trace_id": trace_id, "trace_url": trace_url}


def flush_traces() -> None:
    """
    Flush pending Langfuse events, useful in short-lived CLI processes.
    """
    if not _is_enabled():
        return
    try:
        _langfuse.flush()
    except Exception:  # noqa: BLE001
        return

