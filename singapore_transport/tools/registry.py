"""Lightweight tool registry for documenting and discovering agent tools."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    intents: tuple[str, ...]
    runner: Callable[..., Any]
    required_entities: tuple[str, ...] = ()
    notes: str = ""


_REGISTRY: dict[str, ToolSpec] = {}


def register_tool(spec: ToolSpec) -> ToolSpec:
    _REGISTRY[spec.name] = spec
    return spec


def get_tool(name: str) -> ToolSpec | None:
    return _REGISTRY.get(name)


def list_tools() -> list[ToolSpec]:
    return list(_REGISTRY.values())


def tools_for_intent(intent: str) -> list[ToolSpec]:
    return [t for t in _REGISTRY.values() if intent in t.intents]


def registry_summary() -> list[dict[str, Any]]:
    return [
        {
            "name": t.name,
            "description": t.description,
            "intents": list(t.intents),
            "required_entities": list(t.required_entities),
            "notes": t.notes,
        }
        for t in list_tools()
    ]
