"""Traffic incidents tool."""

from __future__ import annotations

from typing import Any

from singapore_transport.tools.lta_client import get_lta_client

# Common area aliases for substring matching against LTA messages
LOCATION_ALIASES: dict[str, list[str]] = {
    "orchard": ["orchard"],
    "cbd": ["cbd", "raffles", "shenton", "cecil", "fullerton"],
    "jurong": ["jurong"],
    "tampines": ["tampines"],
    "woodlands": ["woodlands"],
    "changi": ["changi"],
    "pi e": ["pie"],
    "pie": ["pie"],
    "cte": ["cte"],
    "aye": ["aye"],
    "ecp": ["ecp"],
}


def fetch_traffic_context() -> dict[str, Any]:
    client = get_lta_client()
    data = client.get("TrafficIncidents", cache_name="traffic_incidents", ttl=120)
    if "error" in data:
        return {
            "status": "Unknown",
            "incident_count": 0,
            "major_incidents": [],
            "all_incidents": [],
            "error": data["error"],
        }

    incidents = data.get("value") or []
    count = len(incidents)
    if count > 5:
        status = "High Congestion"
    elif count > 2:
        status = "Moderate Traffic"
    else:
        status = "Normal"

    messages = [i.get("Message", "") for i in incidents if i.get("Message")]
    return {
        "status": status,
        "incident_count": count,
        "major_incidents": messages[:5],
        "all_incidents": messages,
    }


def filter_incidents_by_location(
    traffic_context: dict[str, Any],
    location: str | None,
) -> dict[str, Any]:
    location = (location or "").strip()
    all_msgs = traffic_context.get("all_incidents") or traffic_context.get("major_incidents") or []

    if not location:
        return {
            "type": "traffic_area",
            "messages": all_msgs[:8] or ["No traffic incidents reported right now."],
            "status_title": "General Traffic Update",
            "matched_location": None,
        }

    loc_l = location.lower()
    aliases = LOCATION_ALIASES.get(loc_l, [loc_l])
    # also include raw tokens
    tokens = [t for t in loc_l.replace("-", " ").split() if len(t) > 2]
    needles = set(aliases + tokens + [loc_l])

    relevant = [
        msg
        for msg in all_msgs
        if any(n in msg.lower() for n in needles)
    ]

    return {
        "type": "traffic_area",
        "messages": relevant
        if relevant
        else ["No specific incidents reported in this area."],
        "status_title": f"Traffic near {location.title()}",
        "matched_location": location,
        "used_fallback": not bool(relevant),
    }
