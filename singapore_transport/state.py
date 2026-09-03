"""Shared LangGraph state for the transport agent."""

from typing import Any, Dict, List, Optional, TypedDict


class TransportState(TypedDict, total=False):
    user_query: str
    intent: Optional[str]
    entities: Dict[str, Any]

    time_context: Optional[Dict[str, Any]]
    holiday_context: Optional[Dict[str, Any]]
    weather_context: Optional[Dict[str, Any]]
    traffic_context: Optional[Dict[str, Any]]
    disruption_context: Optional[Dict[str, Any]]
    bus_service_info: Optional[Dict[str, Any] | str]

    resolved_stop: Optional[Dict[str, Any]]
    api_response: Optional[Dict[str, Any]]
    errors: List[str]
    final_answer: Optional[str]


VALID_INTENTS = frozenset(
    {
        "bus_arrival",
        "bus_info",
        "bus_frequency",
        "traffic_area",
        "weather_only",
        "train_disruption",
        "nearest_stop",
        "general_help",
        "fallback",
    }
)
