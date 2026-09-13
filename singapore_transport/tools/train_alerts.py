"""Train / MRT service alerts tool."""

from __future__ import annotations

from typing import Any

from singapore_transport.tools.lta_client import get_lta_client


def fetch_disruption_context() -> dict[str, Any]:
    client = get_lta_client()
    data = client.get("TrainServiceAlerts", cache_name="train_alerts", ttl=120)
    if "error" in data:
        return {
            "status_code": None,
            "status_label": "Unavailable",
            "message": data["error"],
            "affected_segments": [],
            "raw": data,
            "available": False,
        }
    return normalize_train_alerts(data)


def normalize_train_alerts(data: dict[str, Any]) -> dict[str, Any]:
    """
    LTA typically returns:
      { "value": [ { "Status": 1|2, "Message": "...", "AffectedSegments": [...] } ] }
    Status 1 = Normal, 2 = Disrupted.
    """
    value = data.get("value")
    record: dict[str, Any]
    if isinstance(value, list) and value:
        record = value[0] if isinstance(value[0], dict) else {}
    elif isinstance(value, dict):
        record = value
    else:
        # Some payloads put Status at top level
        record = data if "Status" in data else {}

    status = record.get("Status")
    try:
        status_int = int(status) if status is not None else None
    except (TypeError, ValueError):
        status_int = None

    if status_int == 1:
        label = "Normal Service"
    elif status_int == 2:
        label = "Service Disruption"
    elif status_int is None and not record:
        label = "Unknown"
    else:
        label = f"Status {status_int}"

    segments = record.get("AffectedSegments") or []
    message = record.get("Message") or ""
    return {
        "status_code": status_int,
        "status_label": label,
        "message": message,
        "affected_segments": segments,
        "alternative_services": record.get("AlternativeServices") or [],
        "raw": data,
        "available": True,
        "is_disrupted": status_int == 2,
    }


def filter_by_line(context: dict[str, Any], mrt_line: str | None) -> dict[str, Any]:
    if not mrt_line:
        return context
    line = mrt_line.upper().strip()
    segments = context.get("affected_segments") or []
    matched = [
        s
        for s in segments
        if line in str(s.get("Line", "")).upper()
        or line in str(s.get("Direction", "")).upper()
        or line in str(s).upper()
    ]
    enriched = dict(context)
    enriched["line_filter"] = line
    enriched["line_segments"] = matched
    if matched:
        enriched["line_status"] = "Affected"
    elif context.get("is_disrupted"):
        enriched["line_status"] = "Network disrupted (line not listed in segments)"
    else:
        enriched["line_status"] = "No alerts for this line"
    return enriched
