"""Weather tool — Data.gov.sg 2-hour forecast."""

from __future__ import annotations

import logging
from typing import Any

import requests

from singapore_transport.config import get_settings
from singapore_transport.utils import cached_call

logger = logging.getLogger(__name__)

RAIN_KEYWORDS = ("Rain", "Showers", "Thundery", "Thunder")


def _severity_from_forecasts(forecasts: list[dict[str, Any]]) -> tuple[str, str, str]:
    """Return (condition, severity, impact)."""
    texts = [f.get("forecast", "") for f in forecasts]
    raining = any(any(k in t for k in RAIN_KEYWORDS) for t in texts)
    heavy = any("Heavy" in t or "Thundery" in t for t in texts)

    if raining and heavy:
        return (
            "Heavy Rain / Thunder",
            "High",
            "Expect delays; slippery roads and slower traffic likely.",
        )
    if raining:
        return (
            "Rain",
            "Moderate",
            "Slippery roads and slower traffic expected. Carry an umbrella.",
        )
    return ("Cloudy/Clear", "Low", "Good travel conditions.")


def fetch_weather_context(area: str | None = None) -> dict[str, Any]:
    settings = get_settings()

    def _fetch() -> dict[str, Any]:
        try:
            response = requests.get(settings.weather_url, timeout=settings.request_timeout_seconds)
            data = response.json()
            if response.status_code != 200 or "items" not in data:
                return {"condition": "Unknown", "severity": "Unknown", "impact": "N/A"}

            forecasts = data.get("items", [{}])[0].get("forecasts", [])
            if area:
                area_l = area.lower()
                local = [f for f in forecasts if area_l in str(f.get("area", "")).lower()]
                if local:
                    forecasts = local

            condition, severity, impact = _severity_from_forecasts(forecasts)
            return {
                "condition": condition,
                "severity": severity,
                "impact": impact,
                "area_filter": area,
                "sample_areas": [
                    {"area": f.get("area"), "forecast": f.get("forecast")}
                    for f in forecasts[:5]
                ],
            }
        except requests.RequestException as exc:
            logger.warning("Weather API failed: %s", exc)
            return {"condition": "Unknown", "severity": "Unknown", "impact": "N/A", "error": str(exc)}
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            logger.warning("Weather parse failed: %s", exc)
            return {"condition": "Unknown", "severity": "Unknown", "impact": "N/A", "error": str(exc)}

    return cached_call("weather", area or "all", _fetch, ttl=900)
