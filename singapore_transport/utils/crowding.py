"""Humanize LTA crowding / occupancy codes."""

from __future__ import annotations

LOAD_LABELS = {
    "SEA": "Seats available",
    "SDA": "Standing available",
    "LSD": "Limited standing",
}


def humanize_load(code: str | None) -> str:
    if not code:
        return "Unknown"
    return LOAD_LABELS.get(code.upper(), code)
