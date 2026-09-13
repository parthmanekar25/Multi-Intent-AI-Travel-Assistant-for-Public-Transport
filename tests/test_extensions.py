"""Tests for new tools, routing, formatting, and session memory."""

from __future__ import annotations

from singapore_transport.agent import TransportAgent, clear_session
from singapore_transport.graph import route_by_intent
from singapore_transport.nodes.intent import extract_intent
from singapore_transport.nodes.response import final_response_node
from singapore_transport.tools.registry import registry_summary, tools_for_intent


class TestNewRouting:
    def test_bus_route_and_carpark_routes(self):
        assert route_by_intent({"intent": "bus_route"}) == "bus_route"
        assert route_by_intent({"intent": "carpark"}) == "carpark"
        assert route_by_intent({"intent": "bus_frequency"}) == "bus_info"


class TestIntentHeuristicsExtended:
    def test_carpark_heuristic(self, monkeypatch):
        from singapore_transport.nodes import intent as intent_mod

        class DummyLLM:
            def generate_json(self, prompt: str):
                return {}

        monkeypatch.setattr(intent_mod, "get_llm", lambda: DummyLLM())
        result = extract_intent({"user_query": "Any parking near HarbourFront?"})
        assert result["intent"] == "carpark"

    def test_bus_route_heuristic(self, monkeypatch):
        from singapore_transport.nodes import intent as intent_mod

        class DummyLLM:
            def generate_json(self, prompt: str):
                return {}

        monkeypatch.setattr(intent_mod, "get_llm", lambda: DummyLLM())
        result = extract_intent({"user_query": "Does bus 36 stop at Orchard?"})
        assert result["intent"] == "bus_route"
        assert result["entities"]["bus_number"] == "36"


class TestResponseFormatters:
    def test_bus_route_serves(self):
        out = final_response_node(
            {
                "intent": "bus_route",
                "entities": {"bus_number": "36"},
                "api_response": {
                    "type": "bus_route",
                    "service": "36",
                    "serves": True,
                    "query": "orchard",
                    "matches": [
                        {
                            "BusStopCode": "09047",
                            "Description": "Orchard Stn",
                            "RoadName": "Orchard Rd",
                            "StopSequence": 12,
                        }
                    ],
                },
            }
        )
        text = out["final_answer"]
        assert "36" in text
        assert "09047" in text
        assert "Orchard" in text

    def test_carpark_format(self):
        out = final_response_node(
            {
                "intent": "carpark",
                "entities": {"location": "HarbourFront"},
                "api_response": {
                    "type": "carpark",
                    "query": "HarbourFront",
                    "total_matched": 1,
                    "carparks": [
                        {
                            "Development": "VivoCity",
                            "Area": "HarbourFront",
                            "AvailableLots": 120,
                            "LotType": "C",
                        }
                    ],
                },
            }
        )
        text = out["final_answer"]
        assert "VivoCity" in text
        assert "120" in text

    def test_bus_info_uses_stop_labels(self):
        out = final_response_node(
            {
                "intent": "bus_info",
                "entities": {"bus_number": "15"},
                "time_context": {"period": "off_peak", "is_peak": False},
                "holiday_context": {"is_holiday": False},
                "api_response": {
                    "type": "bus_info",
                    "service": {
                        "ServiceNo": "15",
                        "OriginCode": "77009",
                        "DestinationCode": "77009",
                        "origin_label": "77009 — Tampines Int (Tampines Ave 4)",
                        "destination_label": "77009 — Tampines Int (Tampines Ave 4)",
                        "Operator": "GAS",
                        "Category": "TRUNK",
                        "AM_Peak_Freq": "04-09",
                        "AM_Offpeak_Freq": "04-13",
                        "PM_Peak_Freq": "07-15",
                        "PM_Offpeak_Freq": "08-15",
                    },
                },
            }
        )
        text = out["final_answer"]
        assert "Tampines Int" in text
        assert "15" in text


class TestRegistry:
    def test_registered_tools(self):
        names = {t["name"] for t in registry_summary()}
        assert "bus_routes" in names
        assert "carpark_availability" in names
        assert tools_for_intent("carpark")


class TestSessionMemory:
    def test_entities_carry_forward(self, monkeypatch):
        from singapore_transport.nodes import intent as intent_mod
        from singapore_transport import agent as agent_mod

        class DummyLLM:
            def generate_json(self, prompt: str):
                return {"intent": "bus_info"}

        monkeypatch.setattr(intent_mod, "get_llm", lambda: DummyLLM())
        agent_mod._SESSION_ENTITIES["test-session"] = {
            "bus_number": "176",
            "bus_stop_code": "20251",
        }
        agent = TransportAgent()
        result = agent.ask("Tell me about that bus", session_id="test-session")
        assert result["entities"].get("bus_number") == "176"
        assert result["entities"].get("bus_stop_code") == "20251"
        clear_session("test-session")
