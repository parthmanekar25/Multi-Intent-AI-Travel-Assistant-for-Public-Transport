"""LangGraph assembly with conditional intent routing."""

from __future__ import annotations

from typing import Literal

from langgraph.graph import END, START, StateGraph

from singapore_transport.nodes import (
    enrich_context,
    extract_intent,
    final_response_node,
    handle_bus_arrival,
    handle_bus_info,
    handle_fallback,
    handle_help,
    handle_nearest_stop,
    handle_traffic,
    handle_train,
    handle_weather,
)
from singapore_transport.state import TransportState

IntentRoute = Literal[
    "bus_arrival",
    "bus_info",
    "traffic_area",
    "weather_only",
    "train_disruption",
    "nearest_stop",
    "general_help",
    "fallback",
]


def route_by_intent(state: TransportState) -> IntentRoute:
    intent = state.get("intent") or "fallback"
    if intent in {"bus_info", "bus_frequency"}:
        return "bus_info"
    if intent == "bus_arrival":
        return "bus_arrival"
    if intent == "traffic_area":
        return "traffic_area"
    if intent == "weather_only":
        return "weather_only"
    if intent == "train_disruption":
        return "train_disruption"
    if intent == "nearest_stop":
        return "nearest_stop"
    if intent == "general_help":
        return "general_help"
    return "fallback"


def build_graph():
    graph = StateGraph(TransportState)

    graph.add_node("intent", extract_intent)
    graph.add_node("context", enrich_context)
    graph.add_node("bus_arrival", handle_bus_arrival)
    graph.add_node("bus_info", handle_bus_info)
    graph.add_node("traffic_area", handle_traffic)
    graph.add_node("weather_only", handle_weather)
    graph.add_node("train_disruption", handle_train)
    graph.add_node("nearest_stop", handle_nearest_stop)
    graph.add_node("general_help", handle_help)
    graph.add_node("fallback", handle_fallback)
    graph.add_node("answer", final_response_node)

    graph.add_edge(START, "intent")
    graph.add_edge("intent", "context")
    graph.add_conditional_edges(
        "context",
        route_by_intent,
        {
            "bus_arrival": "bus_arrival",
            "bus_info": "bus_info",
            "traffic_area": "traffic_area",
            "weather_only": "weather_only",
            "train_disruption": "train_disruption",
            "nearest_stop": "nearest_stop",
            "general_help": "general_help",
            "fallback": "fallback",
        },
    )

    for node in (
        "bus_arrival",
        "bus_info",
        "traffic_area",
        "weather_only",
        "train_disruption",
        "nearest_stop",
        "general_help",
        "fallback",
    ):
        graph.add_edge(node, "answer")

    graph.add_edge("answer", END)
    return graph.compile()


_app = None


def get_compiled_graph():
    global _app
    if _app is None:
        _app = build_graph()
    return _app
