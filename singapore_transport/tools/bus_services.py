"""Bus services static catalogue tool."""

from __future__ import annotations

from typing import Any

from singapore_transport.config import get_settings
from singapore_transport.tools.lta_client import get_lta_client


def _all_services() -> list[dict[str, Any]]:
    settings = get_settings()
    client = get_lta_client()
    return client.get_paginated(
        "BusServices",
        cache_name="bus_services_all",
        ttl=settings.bus_services_cache_ttl_seconds,
    )


def find_bus_service(service_no: str | None) -> dict[str, Any] | str | None:
    if not service_no or str(service_no).lower() in {"none", "null"}:
        return None
    target = str(service_no).strip().upper()
    try:
        services = _all_services()
    except Exception:  # noqa: BLE001
        return "API Error"

    for svc in services:
        if str(svc.get("ServiceNo", "")).upper() == target:
            return svc
    return "Not Found"
