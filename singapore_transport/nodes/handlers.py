"""Intent-specific handler nodes."""

from __future__ import annotations

from typing import Any

from singapore_transport.state import TransportState
from singapore_transport.tools.bus_arrival import fetch_bus_arrival, summarize_services
from singapore_transport.tools.bus_routes import service_serves_stop
from singapore_transport.tools.bus_stops import get_all_stops, lookup_stop_label
from singapore_transport.tools.carpark import fetch_carparks
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
    enriched = service
    if isinstance(service, dict):
        enriched = dict(service)
        origin = service.get("OriginCode")
        dest = service.get("DestinationCode")
        enriched["origin_label"] = lookup_stop_label(str(origin) if origin else None)
        enriched["destination_label"] = lookup_stop_label(str(dest) if dest else None)
    return {
        "api_response": {
            "type": "bus_info",
            "service": enriched,
            "requested": entities.get("bus_number"),
        }
    }


def handle_bus_route(state: TransportState) -> dict[str, Any]:
    entities = state.get("entities") or {}
    resolved = state.get("resolved_stop") or {}
    matched = resolved.get("matched") or []
    bus_no = entities.get("bus_number")
    stop_code = entities.get("bus_stop_code")
    if not stop_code and matched:
        stop_code = matched[0].get("BusStopCode")

    catalogue = None
    # Only load catalogue when matching by location name (not by exact code)
    if entities.get("location") and not stop_code:
        try:
            catalogue = get_all_stops()
        except Exception:  # noqa: BLE001
            catalogue = None

    result = service_serves_stop(
        bus_no,
        bus_stop_code=str(stop_code) if stop_code else None,
        location=entities.get("location"),
        stop_catalogue=catalogue,
    )
    return {"api_response": {"type": "bus_route", **result}}


def handle_carpark(state: TransportState) -> dict[str, Any]:
    entities = state.get("entities") or {}
    result = fetch_carparks(entities.get("location"))
    return {"api_response": {"type": "carpark", **result}}


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
