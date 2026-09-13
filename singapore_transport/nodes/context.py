"""Context enrichment — selective by intent to reduce API fan-out."""

from __future__ import annotations

import logging
from typing import Any

from singapore_transport.state import TransportState
from singapore_transport.tools.bus_services import find_bus_service
from singapore_transport.tools.bus_stops import resolve_bus_stop
from singapore_transport.tools.traffic import fetch_traffic_context
from singapore_transport.tools.train_alerts import fetch_disruption_context
from singapore_transport.tools.weather import fetch_weather_context
from singapore_transport.utils.holidays import holiday_context
from singapore_transport.utils.time_context import peak_period

logger = logging.getLogger(__name__)

# Which context slices each intent needs
INTENT_CONTEXT_NEEDS: dict[str, set[str]] = {
    "bus_arrival": {"time", "holiday", "weather", "traffic", "bus_service", "stop"},
    "bus_info": {"time", "holiday", "bus_service"},
    "bus_frequency": {"time", "holiday", "bus_service"},
    "bus_route": {"stop"},
    "carpark": set(),
    "traffic_area": {"time", "weather", "traffic"},
    "weather_only": {"weather"},
    "train_disruption": {"weather", "traffic", "disruption"},
    "nearest_stop": {"stop"},
    "general_help": {"time"},
    "fallback": {"time"},
}


def enrich_context(state: TransportState) -> dict[str, Any]:
    intent = state.get("intent") or "fallback"
    entities = state.get("entities") or {}
    needs = INTENT_CONTEXT_NEEDS.get(intent, {"time", "weather"})

    updates: dict[str, Any] = {}
    errors: list[str] = list(state.get("errors") or [])

    if "time" in needs:
        updates["time_context"] = peak_period()
    if "holiday" in needs:
        updates["holiday_context"] = holiday_context()

    if "weather" in needs:
        try:
            updates["weather_context"] = fetch_weather_context(entities.get("location"))
        except Exception as exc:  # noqa: BLE001
            logger.warning("weather context failed: %s", exc)
            updates["weather_context"] = {
                "condition": "Unknown",
                "severity": "Unknown",
                "impact": "N/A",
            }
            errors.append(f"weather: {exc}")

    if "traffic" in needs:
        try:
            updates["traffic_context"] = fetch_traffic_context()
        except Exception as exc:  # noqa: BLE001
            logger.warning("traffic context failed: %s", exc)
            updates["traffic_context"] = {
                "status": "Unknown",
                "incident_count": 0,
                "major_incidents": [],
                "all_incidents": [],
            }
            errors.append(f"traffic: {exc}")

    if "disruption" in needs:
        try:
            updates["disruption_context"] = fetch_disruption_context()
        except Exception as exc:  # noqa: BLE001
            logger.warning("disruption context failed: %s", exc)
            updates["disruption_context"] = {
                "status_label": "Unavailable",
                "available": False,
                "is_disrupted": False,
                "affected_segments": [],
            }
            errors.append(f"disruption: {exc}")

    if "bus_service" in needs:
        try:
            updates["bus_service_info"] = find_bus_service(entities.get("bus_number"))
        except Exception as exc:  # noqa: BLE001
            logger.warning("bus service lookup failed: %s", exc)
            updates["bus_service_info"] = "API Error"
            errors.append(f"bus_service: {exc}")

    if "stop" in needs:
        try:
            updates["resolved_stop"] = resolve_bus_stop(
                bus_stop_code=entities.get("bus_stop_code"),
                location=entities.get("location"),
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("stop resolution failed: %s", exc)
            updates["resolved_stop"] = {"matched": [], "query": None, "exact": False}
            errors.append(f"stop: {exc}")

    if errors:
        updates["errors"] = errors
    return updates
