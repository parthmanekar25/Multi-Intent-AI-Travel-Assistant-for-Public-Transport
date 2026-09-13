"""Bus stop catalogue + fuzzy name / code resolution."""

from __future__ import annotations

import re
from typing import Any

from singapore_transport.config import get_settings
from singapore_transport.tools.lta_client import get_lta_client

_STOP_CODE_RE = re.compile(r"^\d{5}$")


def get_all_stops() -> list[dict[str, Any]]:
    settings = get_settings()
    client = get_lta_client()
    return client.get_paginated(
        "BusStops",
        cache_name="bus_stops_all",
        ttl=settings.bus_stops_cache_ttl_seconds,
    )


# Back-compat alias used by older call sites
_all_stops = get_all_stops


def lookup_stop_label(bus_stop_code: str | None) -> str:
    """Return 'CODE — Description (Road)' when possible, else the raw code."""
    code = (bus_stop_code or "").strip()
    if not code:
        return "Unknown"
    try:
        resolved = resolve_bus_stop(bus_stop_code=code)
        matched = resolved.get("matched") or []
        if matched:
            stop = matched[0]
            desc = stop.get("Description") or ""
            road = stop.get("RoadName") or ""
            if desc and road:
                return f"{code} — {desc} ({road})"
            if desc:
                return f"{code} — {desc}"
    except Exception:  # noqa: BLE001
        pass
    return code


def resolve_bus_stop(
    *,
    bus_stop_code: str | None = None,
    location: str | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    """
    Resolve a stop code or free-text location to bus stop records.
    Returns {"matched": [...], "query": ..., "exact": bool}.
    """
    code = (bus_stop_code or "").strip()
    if code and _STOP_CODE_RE.match(code):
        try:
            stops = _all_stops()
            exact = next((s for s in stops if str(s.get("BusStopCode")) == code), None)
            if exact:
                return {"matched": [exact], "query": code, "exact": True}
        except Exception:  # noqa: BLE001
            # Even without catalogue, a valid code can still query arrivals.
            return {
                "matched": [{"BusStopCode": code, "Description": code}],
                "query": code,
                "exact": True,
            }
        return {
            "matched": [{"BusStopCode": code, "Description": code}],
            "query": code,
            "exact": True,
        }

    query = (location or "").strip()
    if not query:
        return {"matched": [], "query": query, "exact": False}

    query_l = query.lower()
    try:
        stops = _all_stops()
    except Exception as exc:  # noqa: BLE001
        return {"matched": [], "query": query, "exact": False, "error": str(exc)}

    scored: list[tuple[int, dict[str, Any]]] = []
    for stop in stops:
        desc = str(stop.get("Description") or "")
        road = str(stop.get("RoadName") or "")
        hay = f"{desc} {road}".lower()
        if query_l == desc.lower():
            score = 100
        elif query_l in hay:
            score = 80 if query_l in desc.lower() else 60
        else:
            tokens = [t for t in re.split(r"\W+", query_l) if t]
            if tokens and all(t in hay for t in tokens):
                score = 50
            else:
                continue
        scored.append((score, stop))

    scored.sort(key=lambda x: (-x[0], str(x[1].get("Description") or "")))
    matched = [s for _, s in scored[:limit]]
    return {
        "matched": matched,
        "query": query,
        "exact": bool(matched) and scored[0][0] >= 100,
    }
