"""Intent + entity extraction via Groq."""

from __future__ import annotations

import logging
import re
from typing import Any

from singapore_transport.llm import get_llm
from singapore_transport.state import VALID_INTENTS, TransportState

logger = logging.getLogger(__name__)

_STOP_IN_QUERY = re.compile(r"\b(?:stop|bus\s*stop)\s*#?\s*(\d{5})\b", re.I)
_BARE_STOP = re.compile(r"\b(\d{5})\b")
_BUS_NO = re.compile(r"\bbus\s+(\d{1,3}[A-Za-z]?)\b", re.I)


def _heuristic_entities(query: str) -> dict[str, Any]:
    stop = None
    m = _STOP_IN_QUERY.search(query) or _BARE_STOP.search(query)
    if m:
        stop = m.group(1)
    bus = None
    bm = _BUS_NO.search(query)
    if bm:
        bus = bm.group(1).upper()
    return {
        "bus_stop_code": stop,
        "bus_number": bus,
        "location": None,
        "mrt_line": None,
    }


def extract_intent(state: TransportState) -> dict[str, Any]:
    query = state.get("user_query") or ""
    prompt = f"""
You are a Singapore transport assistant.

Analyze the user query:
"{query}"

Classify intent STRICTLY into ONE of the following:
- bus_arrival → next bus / arrival time
- bus_info → route, operator, service details
- bus_frequency → peak or off-peak frequency
- traffic_area → traffic or jams in a specific area/road
- weather_only → rain, weather, umbrella
- train_disruption → MRT/LRT disruptions or line status
- nearest_stop → find bus stop near a place/name
- general_help → vague help or travel planning
- fallback → unclear query

Extract entities if present:
- bus_stop_code (5 digits)
- bus_number
- location (e.g., Orchard Road, Jurong, Tampines)
- mrt_line (e.g., NEL, NSL)

Respond ONLY in valid JSON:
{{
  "intent": "...",
  "bus_stop_code": null,
  "bus_number": null,
  "location": null,
  "mrt_line": null
}}
"""
    data: dict[str, Any] = {}
    try:
        data = get_llm().generate_json(prompt)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Intent LLM failed, using heuristics: %s", exc)

    heuristics = _heuristic_entities(query)
    intent = str(data.get("intent") or "fallback").strip().lower()
    if intent not in VALID_INTENTS:
        intent = "fallback"

    entities = {
        "bus_stop_code": data.get("bus_stop_code") or heuristics.get("bus_stop_code"),
        "bus_number": data.get("bus_number") or heuristics.get("bus_number"),
        "location": data.get("location") or heuristics.get("location"),
        "mrt_line": data.get("mrt_line") or heuristics.get("mrt_line"),
    }

    # Normalize bus number
    if entities["bus_number"] is not None:
        entities["bus_number"] = str(entities["bus_number"]).strip().upper()
        if entities["bus_number"].lower() in {"none", "null", ""}:
            entities["bus_number"] = None

    if entities["bus_stop_code"] is not None:
        code = str(entities["bus_stop_code"]).strip()
        entities["bus_stop_code"] = code if re.fullmatch(r"\d{5}", code) else None

    return {"intent": intent, "entities": entities}
