"""BusRoutes tool — stop sequence / does-this-bus-serve-X."""

from __future__ import annotations

from typing import Any

from singapore_transport.config import get_settings
from singapore_transport.tools.lta_client import get_lta_client
from singapore_transport.tools.registry import ToolSpec, register_tool


def _all_routes() -> list[dict[str, Any]]:
    settings = get_settings()
    client = get_lta_client()
    return client.get_paginated(
        "BusRoutes",
        cache_name="bus_routes_all",
        ttl=settings.bus_services_cache_ttl_seconds,
        max_pages=80,
    )


def get_route_for_service(service_no: str | None) -> list[dict[str, Any]]:
    if not service_no:
        return []
    target = str(service_no).strip().upper()
    routes = _all_routes()
    matched = [r for r in routes if str(r.get("ServiceNo", "")).upper() == target]
    matched.sort(key=lambda r: (int(r.get("Direction") or 1), int(r.get("StopSequence") or 0)))
    return matched


def service_serves_stop(
    service_no: str | None,
    *,
    bus_stop_code: str | None = None,
    location: str | None = None,
    stop_catalogue: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Check whether a service calls a stop code or a location-matched stop.
    """
    route = get_route_for_service(service_no)
    if not route:
        return {
            "service": service_no,
            "serves": False,
            "matches": [],
            "error": "Service not found" if service_no else "No service provided",
        }

    code = (bus_stop_code or "").strip()
    if code:
        hits = [r for r in route if str(r.get("BusStopCode")) == code]
        return {
            "service": service_no,
            "serves": bool(hits),
            "matches": hits,
            "query": code,
        }

    location = (location or "").strip().lower()
    if not location:
        # Return a compact route preview when no stop filter is given
        preview = route[:12]
        return {
            "service": service_no,
            "serves": True,
            "matches": preview,
            "total_stops": len(route),
            "query": None,
            "preview": True,
        }

    # Match against stop descriptions if catalogue provided; else match RoadName in route rows
    hits: list[dict[str, Any]] = []
    code_to_meta = {}
    if stop_catalogue:
        for s in stop_catalogue:
            code_to_meta[str(s.get("BusStopCode"))] = s

    for row in route:
        stop_code = str(row.get("BusStopCode") or "")
        meta = code_to_meta.get(stop_code, {})
        hay = " ".join(
            [
                str(row.get("RoadName") or ""),
                str(meta.get("Description") or ""),
                str(meta.get("RoadName") or ""),
            ]
        ).lower()
        if location in hay or all(tok in hay for tok in location.split() if len(tok) > 2):
            enriched = dict(row)
            if meta:
                enriched["Description"] = meta.get("Description")
                enriched["RoadName"] = meta.get("RoadName") or enriched.get("RoadName")
            hits.append(enriched)

    return {
        "service": service_no,
        "serves": bool(hits),
        "matches": hits[:15],
        "query": location,
        "total_stops": len(route),
    }


register_tool(
    ToolSpec(
        name="bus_routes",
        description="Look up bus route stop sequences and whether a service serves a stop/area.",
        intents=("bus_route",),
        runner=service_serves_stop,
        required_entities=("bus_number",),
        notes="Uses LTA BusRoutes (static, cached ~24h).",
    )
)
