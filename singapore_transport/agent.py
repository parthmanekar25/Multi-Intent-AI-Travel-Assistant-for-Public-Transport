"""High-level agent API."""

from __future__ import annotations

from typing import Any

from singapore_transport.graph import get_compiled_graph
from singapore_transport.state import TransportState


class TransportAgent:
    """Thin wrapper around the compiled LangGraph app."""

    def __init__(self):
        self._app = get_compiled_graph()

    def ask(self, query: str) -> dict[str, Any]:
        initial: TransportState = {
            "user_query": query,
            "entities": {},
            "errors": [],
        }
        return self._app.invoke(initial)

    def answer_text(self, query: str) -> str:
        result = self.ask(query)
        return result.get("final_answer") or "No response generated."


def ask(query: str) -> str:
    """Convenience one-liner used by CLI / scripts."""
    return TransportAgent().answer_text(query)
