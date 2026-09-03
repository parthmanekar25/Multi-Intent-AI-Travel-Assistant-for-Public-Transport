"""Bus arrival tool."""

from __future__ import annotations

from typing import Any

from singapore_transport.tools.lta_client import get_lta_client
from singapore_transport.utils.crowding import humanize_load
from singapore_transport.utils.time_context import format_arrival_clock, minutes_until


def fetch_bus_arrival(
    bus_stop_code: str,
    service_no: str | None = None,
) -> dict[str, Any]:
    client = get_lta_client()
    params: dict[str, Any] = {"BusStopCode": str(bus_stop_code)}
    if service_no:
        params["ServiceNo"] = str(service_no)

    data = client.get(
        "v3/BusArrival",
        params=params,
        cache_name="bus_arrival",
        cache_key=(str(bus_stop_code), str(service_no or "")),
        ttl=60,
    )
    return data


def summarize_services(api_data: dict[str, Any], limit_services: int = 5) -> list[dict[str, Any]]:
    """Normalize NextBus / NextBus2 / NextBus3 into a readable list."""
    services = api_data.get("Services") or []
    summaries: list[dict[str, Any]] = []

    for svc in services[:limit_services]:
        arrivals = []
        for key in ("NextBus", "NextBus2", "NextBus3"):
            bus = svc.get(key) or {}
            eta = bus.get("EstimatedArrival")
            if not eta:
                continue
            arrivals.append(
                {
                    "minutes": minutes_until(eta),
                    "time": format_arrival_clock(eta),
                    "load": humanize_load(bus.get("Load")),
                    "load_code": bus.get("Load"),
                    "feature": bus.get("Feature"),
                    "type": bus.get("Type"),
                }
            )
        summaries.append(
            {
                "service": svc.get("ServiceNo"),
                "operator": svc.get("Operator"),
                "arrivals": arrivals,
            }
        )
    return summaries
