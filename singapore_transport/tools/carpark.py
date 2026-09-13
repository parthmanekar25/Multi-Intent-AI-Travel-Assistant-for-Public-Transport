"""Car park availability tool (LTA CarParkAvailability)."""

from __future__ import annotations

from typing import Any

from singapore_transport.tools.lta_client import get_lta_client
from singapore_transport.tools.registry import ToolSpec, register_tool


def fetch_carparks(location: str | None = None, *, limit: int = 8) -> dict[str, Any]:
    client = get_lta_client()
    data = client.get("CarParkAvailability", cache_name="carpark", ttl=120)
    if "error" in data:
        return {
            "carparks": [],
            "query": location,
            "error": data["error"],
        }

    rows = data.get("value") or []
    location_l = (location or "").strip().lower()

    scored: list[tuple[int, dict[str, Any]]] = []
    for row in rows:
        development = str(row.get("Development") or "")
        area = str(row.get("Area") or "")
        hay = f"{development} {area}".lower()
        if location_l:
            if location_l == development.lower():
                score = 100
            elif location_l in hay:
                score = 80
            elif any(tok in hay for tok in location_l.split() if len(tok) > 2):
                score = 50
            else:
                continue
        else:
            # No filter: prefer lots with availability
            try:
                avail = int(row.get("AvailableLots") or 0)
            except (TypeError, ValueError):
                avail = 0
            score = avail
        scored.append((score, row))

    scored.sort(key=lambda x: (-x[0], str(x[1].get("Development") or "")))
    top = [r for _, r in scored[:limit]]
    return {
        "carparks": top,
        "query": location,
        "total_matched": len(scored),
    }


register_tool(
    ToolSpec(
        name="carpark_availability",
        description="Find car park lot availability near an area or development.",
        intents=("carpark",),
        runner=fetch_carparks,
        required_entities=(),
        notes="Uses LTA CarParkAvailability (live, cached ~2 min).",
    )
)
