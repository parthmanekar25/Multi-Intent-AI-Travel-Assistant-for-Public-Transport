"""High-level agent API with optional session memory."""

from __future__ import annotations

from typing import Any

from singapore_transport.graph import get_compiled_graph
from singapore_transport.state import TransportState

# In-memory last-entities store keyed by session_id (process-local).
_SESSION_ENTITIES: dict[str, dict[str, Any]] = {}


class TransportAgent:
    """Thin wrapper around the compiled LangGraph app."""

    def __init__(self):
        self._app = get_compiled_graph()

    def ask(self, query: str, *, session_id: str | None = None) -> dict[str, Any]:
        prior = _SESSION_ENTITIES.get(session_id or "", {})
        initial: TransportState = {
            "user_query": query,
            "entities": dict(prior),
            "errors": [],
            "session_id": session_id,
        }
        result = self._app.invoke(initial)
        if session_id:
            merged = {**(prior or {}), **(result.get("entities") or {})}
            # Drop empty values
            _SESSION_ENTITIES[session_id] = {
                k: v for k, v in merged.items() if v not in (None, "", [], {})
            }
        return result

    def answer_text(self, query: str, *, session_id: str | None = None) -> str:
        result = self.ask(query, session_id=session_id)
        return result.get("final_answer") or "No response generated."

    def clear_session(self, session_id: str) -> None:
        _SESSION_ENTITIES.pop(session_id, None)


def ask(query: str, *, session_id: str | None = None) -> str:
    """Convenience one-liner used by CLI / scripts."""
    return TransportAgent().answer_text(query, session_id=session_id)


def clear_session(session_id: str) -> None:
    _SESSION_ENTITIES.pop(session_id, None)
