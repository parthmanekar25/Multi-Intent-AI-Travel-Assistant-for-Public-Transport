"""Singapore timezone and peak-hour helpers."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from singapore_transport.config import get_settings


def sg_now() -> datetime:
    """Current time in Asia/Singapore."""
    tz = ZoneInfo(get_settings().timezone)
    return datetime.now(tz)


def peak_period(now: datetime | None = None) -> dict:
    """
    Classify Singapore bus peak windows.
    Morning peak: 06:30–08:59
    Evening peak: 17:00–19:59
    """
    now = now or sg_now()
    hour, minute = now.hour, now.minute

    if (hour == 6 and minute >= 30) or (7 <= hour <= 8):
        period = "morning_peak"
    elif 17 <= hour <= 19:
        period = "evening_peak"
    else:
        period = "off_peak"

    return {
        "hour": hour,
        "minute": minute,
        "period": period,
        "is_peak": period != "off_peak",
        "iso": now.isoformat(),
        "timezone": str(now.tzinfo),
    }


def minutes_until(iso_arrival: str, now: datetime | None = None) -> int | None:
    """Minutes until an LTA EstimatedArrival timestamp."""
    if not iso_arrival:
        return None
    now = now or sg_now()
    raw = iso_arrival.replace("Z", "+00:00")
    try:
        eta = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if eta.tzinfo is None:
        eta = eta.replace(tzinfo=ZoneInfo(get_settings().timezone))
    delta = eta - now.astimezone(eta.tzinfo)
    return max(0, int(delta.total_seconds() / 60))


def format_arrival_clock(iso_arrival: str) -> str:
    if not iso_arrival:
        return "Unknown"
    raw = iso_arrival.replace("Z", "+00:00")
    try:
        eta = datetime.fromisoformat(raw)
    except ValueError:
        return "Unknown"
    if eta.tzinfo is None:
        eta = eta.replace(tzinfo=ZoneInfo(get_settings().timezone))
    local = eta.astimezone(ZoneInfo(get_settings().timezone))
    return local.strftime("%I:%M %p").lstrip("0")
