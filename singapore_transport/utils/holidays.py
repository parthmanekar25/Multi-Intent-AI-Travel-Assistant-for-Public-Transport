"""Public holiday detection for Singapore."""

from __future__ import annotations

from datetime import date

from singapore_transport.utils.time_context import sg_now

# Fallback calendars when the live API is unavailable.
# Keep at least current + previous year.
SINGAPORE_HOLIDAYS: dict[int, set[str]] = {
    2025: {
        "2025-01-01",
        "2025-01-29",
        "2025-01-30",
        "2025-03-31",
        "2025-04-18",
        "2025-05-01",
        "2025-05-12",
        "2025-06-07",
        "2025-08-09",
        "2025-10-20",
        "2025-12-25",
    },
    2026: {
        "2026-01-01",
        "2026-02-17",
        "2026-02-18",
        "2026-03-21",
        "2026-04-03",
        "2026-05-01",
        "2026-05-27",
        "2026-05-31",
        "2026-08-09",
        "2026-08-10",  # observed if NDP falls on Sunday in some years; keep if gazetted
        "2026-11-08",
        "2026-12-25",
    },
}


def is_public_holiday(day: date | None = None) -> bool:
    day = day or sg_now().date()
    key = day.isoformat()
    year_set = SINGAPORE_HOLIDAYS.get(day.year, set())
    return key in year_set


def holiday_context(day: date | None = None) -> dict:
    day = day or sg_now().date()
    return {
        "date": day.isoformat(),
        "is_holiday": is_public_holiday(day),
        "weekday": day.strftime("%A"),
        "is_weekend": day.weekday() >= 5,
    }
