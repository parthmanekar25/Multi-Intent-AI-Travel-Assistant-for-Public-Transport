"""Tool exports."""

from singapore_transport.tools.bus_arrival import fetch_bus_arrival, summarize_services
from singapore_transport.tools.bus_routes import get_route_for_service, service_serves_stop
from singapore_transport.tools.bus_services import find_bus_service
from singapore_transport.tools.bus_stops import lookup_stop_label, resolve_bus_stop
from singapore_transport.tools.carpark import fetch_carparks
from singapore_transport.tools.registry import list_tools, registry_summary, tools_for_intent
from singapore_transport.tools.traffic import fetch_traffic_context, filter_incidents_by_location
from singapore_transport.tools.train_alerts import fetch_disruption_context, filter_by_line
from singapore_transport.tools.weather import fetch_weather_context

# Side-effect imports so ToolSpec registrations run.
from singapore_transport.tools import bus_routes as _bus_routes  # noqa: F401
from singapore_transport.tools import carpark as _carpark  # noqa: F401

__all__ = [
    "fetch_bus_arrival",
    "summarize_services",
    "find_bus_service",
    "resolve_bus_stop",
    "lookup_stop_label",
    "get_route_for_service",
    "service_serves_stop",
    "fetch_carparks",
    "fetch_traffic_context",
    "filter_incidents_by_location",
    "fetch_disruption_context",
    "filter_by_line",
    "fetch_weather_context",
    "list_tools",
    "registry_summary",
    "tools_for_intent",
]
