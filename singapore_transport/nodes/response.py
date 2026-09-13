"""Final natural-language response synthesizer."""

from __future__ import annotations

from typing import Any

from singapore_transport.state import TransportState
from singapore_transport.utils.crowding import humanize_load


def _weather_alert(weather: dict[str, Any] | None) -> str:
    weather = weather or {}
    if weather.get("condition") == "Rain" or weather.get("severity") in {"Moderate", "High"}:
        return (
            "\n\n---\n"
            "### Weather Update\n"
            f"**Condition:** {weather.get('condition', 'Unknown')}\n"
            f"**Advisory:** {weather.get('impact', 'Please carry an umbrella.')}"
        )
    return ""


def _peak_note(time_ctx: dict[str, Any] | None, holiday: dict[str, Any] | None) -> str:
    time_ctx = time_ctx or {}
    holiday = holiday or {}
    bits = []
    if holiday.get("is_holiday"):
        bits.append("Today is a public holiday — expect Sunday/PH frequencies.")
    elif time_ctx.get("is_peak"):
        bits.append(f"It is currently {time_ctx.get('period', 'peak').replace('_', ' ')}.")
    return ("\n" + " ".join(bits)) if bits else ""


def final_response_node(state: TransportState) -> dict[str, Any]:
    intent = state.get("intent")
    service = state.get("bus_service_info")
    api_response = state.get("api_response") or {}
    weather = state.get("weather_context") or {}
    traffic = state.get("traffic_context") or {}
    disruption = state.get("disruption_context") or {}
    time_ctx = state.get("time_context") or {}
    holiday = state.get("holiday_context") or {}
    entities = state.get("entities") or {}

    weather_alert = _weather_alert(weather)
    peak_note = _peak_note(time_ctx, holiday)

    # Prefer enriched service payload from handlers when present
    if isinstance(api_response.get("service"), dict):
        service = api_response["service"]

    if intent == "bus_arrival":
        response_text = _format_bus_arrival(api_response, weather_alert, peak_note)
    elif intent in {"bus_info", "bus_frequency"}:
        response_text = _format_bus_info(service, entities, time_ctx, holiday) + peak_note
    elif intent == "bus_route":
        response_text = _format_bus_route(api_response, entities)
    elif intent == "carpark":
        response_text = _format_carpark(api_response, entities)
    elif intent == "traffic_area":
        response_text = _format_traffic(api_response, traffic, entities) + weather_alert
    elif intent == "weather_only":
        response_text = _format_weather(weather)
    elif intent == "train_disruption":
        response_text = _format_train(api_response, disruption, traffic, weather, entities)
    elif intent == "nearest_stop":
        response_text = _format_nearest_stop(api_response)
    elif intent == "general_help":
        response_text = (
            "Hi! I'm your Singapore Transport Assistant.\n\n"
            "I can help with:\n"
            '- **Bus Arrivals:** "When is bus 176 arriving at 20251?"\n'
            '- **Stop lookup:** "Bus stops near Orchard Road"\n'
            '- **Bus Info:** "Frequency of bus 107M?"\n'
            '- **Bus Route:** "Does bus 36 stop at Orchard?"\n'
            '- **Carpark:** "Parking near HarbourFront?"\n'
            '- **Traffic:** "Any jams at Orchard?"\n'
            '- **Weather:** "Is it raining?"\n'
            '- **MRT:** "Any disruptions on the NEL?"'
        )
    else:
        response_text = (
            "Sorry, I didn't quite catch that. "
            "Try asking about a bus, stop code/name, carpark, traffic area, weather, or MRT line."
        )

    return {"final_answer": response_text}


def _format_bus_arrival(api_response: dict, weather_alert: str, peak_note: str) -> str:
    if api_response.get("error"):
        candidates = api_response.get("candidates") or []
        hint = api_response.get("hint") or api_response["error"]
        extra = ""
        if candidates:
            lines = [
                f"- {c.get('BusStopCode')} — {c.get('Description')} ({c.get('RoadName')})"
                for c in candidates[:5]
            ]
            extra = "\n\nPossible stops:\n" + "\n".join(lines)
        return f"{hint}{extra}"

    summaries = api_response.get("summaries") or []
    if not summaries:
        return (
            "I checked the bus timings, but no services are available for that query right now."
            + weather_alert
        )

    stop = api_response.get("BusStopCode")
    desc = api_response.get("stop_description")
    stop_label = f"{stop} ({desc})" if desc else str(stop)

    blocks = []
    for summary in summaries[:3]:
        svc = summary.get("service")
        arrivals = summary.get("arrivals") or []
        if not arrivals:
            blocks.append(f"## Bus {svc}\nNo upcoming arrivals reported.")
            continue
        lines = [
            f"- **{a['minutes']} min** ({a['time']}) — {a['load']}"
            for a in arrivals
            if a.get("minutes") is not None
        ]
        blocks.append(
            f"## Bus {svc} – Stop {stop_label}\n\n"
            + ("\n".join(lines) if lines else "No upcoming arrivals reported.")
        )

    return (
        "Your bus is on the way — here are the latest details:\n\n"
        + "\n\n".join(blocks)
        + peak_note
        + weather_alert
    )


def _format_bus_info(service: Any, entities: dict, time_ctx: dict, holiday: dict) -> str:
    if isinstance(service, dict) and service.get("ServiceNo"):
        period = time_ctx.get("period", "off_peak")
        if holiday.get("is_holiday") or period == "off_peak":
            focus = service.get("AM_Offpeak_Freq") or service.get("PM_Offpeak_Freq")
            focus_label = "Off-peak / PH"
        elif period == "morning_peak":
            focus = service.get("AM_Peak_Freq")
            focus_label = "AM Peak"
        else:
            focus = service.get("PM_Peak_Freq")
            focus_label = "PM Peak"

        origin = service.get("origin_label") or service.get("OriginCode")
        destination = service.get("destination_label") or service.get("DestinationCode")

        return (
            f"Here's the info for Bus Service {service.get('ServiceNo')}:\n\n"
            f"## Service {service.get('ServiceNo')} Details\n\n"
            f"**Origin stop:** {origin}\n"
            f"**Destination stop:** {destination}\n"
            f"**Operator:** {service.get('Operator', 'Unknown')}\n"
            f"**Category:** {service.get('Category', 'Unknown')}\n\n"
            f"### Frequency\n"
            f"**AM Peak:** {service.get('AM_Peak_Freq', '-')} mins\n"
            f"**AM Off-Peak:** {service.get('AM_Offpeak_Freq', '-')} mins\n"
            f"**PM Peak:** {service.get('PM_Peak_Freq', '-')} mins\n"
            f"**PM Off-Peak:** {service.get('PM_Offpeak_Freq', '-')} mins\n\n"
            f"**Relevant now ({focus_label}):** {focus or '-'} mins"
        )
    requested = entities.get("bus_number") or "that service"
    return f"I couldn't find specific details for bus {requested}."


def _format_bus_route(api_response: dict, entities: dict) -> str:
    service = api_response.get("service") or entities.get("bus_number") or "that bus"
    query = api_response.get("query")
    matches = api_response.get("matches") or []
    if api_response.get("error"):
        return f"I couldn't look up the route for bus {service}: {api_response['error']}"

    if api_response.get("preview"):
        lines = []
        for row in matches[:12]:
            code = row.get("BusStopCode")
            road = row.get("RoadName") or row.get("Description") or ""
            seq = row.get("StopSequence")
            lines.append(f"- #{seq}: {code} {f'({road})' if road else ''}".rstrip())
        total = api_response.get("total_stops", len(matches))
        return (
            f"## Bus {service} route preview\n\n"
            f"Showing first {len(lines)} of {total} stops:\n"
            + ("\n".join(lines) if lines else "No stops found.")
        )

    if not api_response.get("serves"):
        where = query or entities.get("location") or entities.get("bus_stop_code") or "that stop"
        return f"Bus {service} does not appear to serve {where}."

    lines = []
    for row in matches[:10]:
        code = row.get("BusStopCode")
        desc = row.get("Description") or ""
        road = row.get("RoadName") or ""
        seq = row.get("StopSequence")
        label = " — ".join(p for p in [str(code), desc, road] if p)
        lines.append(f"- Stop #{seq}: {label}")
    where = query or "the requested stop/area"
    return (
        f"## Bus {service} serves {where}\n\n"
        + ("\n".join(lines) if lines else "Matched, but no stop details were returned.")
    )


def _format_carpark(api_response: dict, entities: dict) -> str:
    if api_response.get("error"):
        return f"I couldn't fetch car park data: {api_response['error']}"
    query = api_response.get("query") or entities.get("location") or "Singapore"
    carparks = api_response.get("carparks") or []
    if not carparks:
        return f"No car parks matched '{query}'."
    lines = []
    for cp in carparks[:8]:
        name = cp.get("Development") or cp.get("CarParkID") or "Car park"
        area = cp.get("Area") or ""
        lots = cp.get("AvailableLots")
        lot_type = cp.get("LotType") or ""
        lines.append(
            f"- **{name}**"
            + (f" ({area})" if area else "")
            + f": {lots} lots"
            + (f" [{lot_type}]" if lot_type else "")
        )
    total = api_response.get("total_matched", len(carparks))
    return f"## Car parks near {query}\n\n" + "\n".join(lines) + f"\n\n_{total} matches_"


def _format_traffic(api_response: dict, traffic: dict, entities: dict) -> str:
    location = api_response.get("matched_location") or entities.get("location") or "your area"
    msgs = api_response.get("messages") or []
    if msgs:
        bullets = "\n".join(f"- {msg}" for msg in msgs)
        details = f"**Incidents:**\n{bullets}"
    else:
        details = "No major incidents reported here right now."
    return (
        f"## Traffic Check: {str(location).title()}\n\n"
        f"{details}\n\n"
        f"**General Context:** {traffic.get('status', 'Normal Traffic')} "
        f"({traffic.get('incident_count', 0)} incidents network-wide)"
    )


def _format_weather(weather: dict) -> str:
    is_rain = "Rain" in str(weather.get("condition", "")) or weather.get("severity") in {
        "Moderate",
        "High",
    }
    return (
        "## Weather Update\n\n"
        f"**Current Condition:** {weather.get('condition', 'Unknown')}\n"
        f"**Severity:** {weather.get('severity', 'Unknown')}\n"
        f"**Advisory:** {weather.get('impact', 'No data')}\n\n"
        f"{'Umbrella recommended.' if is_rain else 'No umbrella needed.'}"
    )


def _format_train(
    api_response: dict,
    disruption: dict,
    traffic: dict,
    weather: dict,
    entities: dict,
) -> str:
    info = api_response.get("disruption") or disruption
    line = entities.get("mrt_line")
    status = info.get("status_label") or "Unknown"
    message = info.get("message") or ""
    line_status = info.get("line_status")
    segments = info.get("line_segments") or info.get("affected_segments") or []

    segment_text = ""
    if segments:
        lines = []
        for seg in segments[:5]:
            if isinstance(seg, dict):
                lines.append(
                    f"- {seg.get('Line', '?')}: {seg.get('Direction', '')} "
                    f"({seg.get('Stations', '')})"
                )
            else:
                lines.append(f"- {seg}")
        segment_text = "\n\n**Affected segments:**\n" + "\n".join(lines)

    header = f"## Transport Network Status{f' ({line})' if line else ''}\n\n"
    return (
        header
        + f"**MRT/LRT:** {status}\n"
        + (f"**Message:** {message}\n" if message else "")
        + (f"**Line filter:** {line_status}\n" if line_status else "")
        + segment_text
        + f"\n**Traffic Overall:** {traffic.get('status', 'Normal')}\n"
        + f"**Weather:** {weather.get('condition', 'Unknown')}"
    )


def _format_nearest_stop(api_response: dict) -> str:
    resolved = api_response.get("resolved") or {}
    matched = resolved.get("matched") or []
    query = resolved.get("query") or "your search"
    if not matched:
        return f"I couldn't find bus stops matching '{query}'. Try a clearer landmark or road name."
    lines = [
        f"- **{s.get('BusStopCode')}** — {s.get('Description')} ({s.get('RoadName')})"
        for s in matched[:8]
    ]
    return f"## Bus stops matching '{query}'\n\n" + "\n".join(lines)
