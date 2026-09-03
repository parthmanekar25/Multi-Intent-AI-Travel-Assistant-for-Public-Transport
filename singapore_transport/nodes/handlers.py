"""Intent-specific handler nodes."""

from __future__ import annotations

from typing import Any

from singapore_transport.state import TransportState
from singapore_transport.tools.bus_arrival import fetch_bus_arrival, summarize_services
from singapore_transport.tools.traffic import filter_incidents_by_location
from singapore_transport.tools.train_alerts import filter_by_line


def handle_bus_arrival(state: TransportState) -> dict[str, Any]:
    entities = state.get("entities") or {}
    resolved = state.get("resolved_stop") or {}
    matched = resolved.get("matched") or []

    stop_code = entities.get("bus_stop_code")
    if not stop_code and matched:
        stop_code = matched[0].get("BusStopCode")

    if not stop_code:
        return {
            "api_response": {
                "error": "No bus stop code provided.",
                "hint": "Give a 5-digit stop code or a stop/place name.",
                "candidates": matched[:5],
            }
        }

    bus_no = entities.get("bus_number")
    data = fetch_bus_arrival(str(stop_code), bus_no)
    if "error" in data:
        return {"api_response": data}

    data = dict(data)
    data["summaries"] = summarize_services(data)
    if matched:
        data["stop_description"] = matched[0].get("Description")
        data["road_name"] = matched[0].get("RoadName")
    return {"api_response": data}


def handle_bus_info(state: TransportState) -> dict[str, Any]:
    service = state.get("bus_service_info")
    entities = state.get("entities") or {}
    return {
        "api_response": {
            "type": "bus_info",
            "service": service,
            "requested": entities.get("bus_number"),
        }
    }


def handle_traffic(state: TransportState) -> dict[str, Any]:
    entities = state.get("entities") or {}
    traffic = state.get("traffic_context") or {}
    payload = filter_incidents_by_location(traffic, entities.get("location"))
    return {"api_response": payload}


def handle_weather(state: TransportState) -> dict[str, Any]:
    return {"api_response": {"type": "weather_only"}}


def handle_train(state: TransportState) -> dict[str, Any]:
    entities = state.get("entities") or {}
    disruption = state.get("disruption_context") or {}
    filtered = filter_by_line(disruption, entities.get("mrt_line"))
    return {
        "api_response": {
            "type": "train_disruption",
            "disruption": filtered,
        }
    }


def handle_nearest_stop(state: TransportState) -> dict[str, Any]:
    resolved = state.get("resolved_stop") or {}
    return {
        "api_response": {
            "type": "nearest_stop",
            "resolved": resolved,
        }
    }


def handle_help(_state: TransportState) -> dict[str, Any]:
    return {"api_response": {"type": "general_help"}}


def handle_fallback(_state: TransportState) -> dict[str, Any]:
    return {"api_response": {"type": "fallback"}}
