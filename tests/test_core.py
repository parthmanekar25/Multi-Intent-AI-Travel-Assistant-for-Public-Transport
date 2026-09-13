"""Unit tests that do not require live API keys."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from singapore_transport.nodes.response import final_response_node
from singapore_transport.state import TransportState
from singapore_transport.tools.train_alerts import normalize_train_alerts
from singapore_transport.utils.crowding import humanize_load
from singapore_transport.utils.holidays import holiday_context, is_public_holiday
from singapore_transport.utils.time_context import format_arrival_clock, minutes_until, peak_period


class TestPeakPeriod:
    def test_morning_peak(self):
        now = datetime(2026, 3, 10, 7, 15, tzinfo=ZoneInfo("Asia/Singapore"))
        ctx = peak_period(now)
        assert ctx["period"] == "morning_peak"
        assert ctx["is_peak"] is True

    def test_before_morning_peak(self):
        now = datetime(2026, 3, 10, 6, 15, tzinfo=ZoneInfo("Asia/Singapore"))
        ctx = peak_period(now)
        assert ctx["period"] == "off_peak"

    def test_evening_peak(self):
        now = datetime(2026, 3, 10, 18, 0, tzinfo=ZoneInfo("Asia/Singapore"))
        ctx = peak_period(now)
        assert ctx["period"] == "evening_peak"

    def test_after_evening_peak(self):
        now = datetime(2026, 3, 10, 20, 0, tzinfo=ZoneInfo("Asia/Singapore"))
        ctx = peak_period(now)
        assert ctx["period"] == "off_peak"


class TestHolidays:
    def test_known_2026_holiday(self):
        assert is_public_holiday(date(2026, 2, 17)) is True

    def test_non_holiday(self):
        assert is_public_holiday(date(2026, 3, 10)) is False

    def test_context_shape(self):
        ctx = holiday_context(date(2026, 1, 1))
        assert ctx["is_holiday"] is True
        assert ctx["date"] == "2026-01-01"


class TestCrowding:
    def test_sea(self):
        assert humanize_load("SEA") == "Seats available"

    def test_unknown(self):
        assert humanize_load(None) == "Unknown"


class TestArrivalMath:
    def test_minutes_until_future(self):
        now = datetime(2026, 3, 10, 12, 0, tzinfo=ZoneInfo("Asia/Singapore"))
        eta = "2026-03-10T12:07:00+08:00"
        assert minutes_until(eta, now=now) == 7

    def test_format_clock(self):
        assert "12:07" in format_arrival_clock("2026-03-10T12:07:00+08:00")


class TestTrainAlerts:
    def test_normal_nested_value(self):
        data = {"value": [{"Status": 1, "Message": "", "AffectedSegments": []}]}
        normalized = normalize_train_alerts(data)
        assert normalized["status_code"] == 1
        assert normalized["is_disrupted"] is False
        assert normalized["status_label"] == "Normal Service"

    def test_disrupted(self):
        data = {
            "value": [
                {
                    "Status": 2,
                    "Message": "NEL delay",
                    "AffectedSegments": [{"Line": "NEL", "Direction": "HarbourFront"}],
                }
            ]
        }
        normalized = normalize_train_alerts(data)
        assert normalized["is_disrupted"] is True
        assert "NEL" in str(normalized["affected_segments"])


class TestFinalResponse:
    def test_help(self):
        state: TransportState = {
            "user_query": "hi",
            "intent": "general_help",
            "entities": {},
            "api_response": {"type": "general_help"},
        }
        out = final_response_node(state)
        assert "Bus Arrivals" in out["final_answer"]

    def test_bus_arrival_with_summaries(self):
        state: TransportState = {
            "user_query": "bus",
            "intent": "bus_arrival",
            "entities": {},
            "weather_context": {"condition": "Cloudy/Clear", "severity": "Low"},
            "time_context": {"period": "off_peak", "is_peak": False},
            "api_response": {
                "BusStopCode": "20251",
                "stop_description": "Opp Blk 123",
                "summaries": [
                    {
                        "service": "176",
                        "arrivals": [
                            {
                                "minutes": 3,
                                "time": "4:20 PM",
                                "load": "Seats available",
                            },
                            {
                                "minutes": 12,
                                "time": "4:29 PM",
                                "load": "Standing available",
                            },
                        ],
                    }
                ],
            },
        }
        out = final_response_node(state)
        text = out["final_answer"]
        assert "176" in text
        assert "3 min" in text
        assert "12 min" in text
        assert "Seats available" in text
        assert "SEA" not in text

    def test_weather_severity_alert(self):
        state: TransportState = {
            "user_query": "rain?",
            "intent": "weather_only",
            "entities": {},
            "weather_context": {
                "condition": "Rain",
                "severity": "Moderate",
                "impact": "Carry umbrella",
            },
            "api_response": {"type": "weather_only"},
        }
        out = final_response_node(state)
        assert "Umbrella recommended" in out["final_answer"]


class TestIntentHeuristics:
    def test_extract_stop_and_bus_without_llm(self, monkeypatch):
        from singapore_transport.nodes import intent as intent_mod

        class DummyLLM:
            def generate_json(self, prompt: str):
                return {"intent": "bus_arrival"}

        monkeypatch.setattr(intent_mod, "get_llm", lambda: DummyLLM())
        result = intent_mod.extract_intent(
            {"user_query": "When is the next bus 176 arriving at stop 20251?"}
        )
        assert result["intent"] == "bus_arrival"
        assert result["entities"]["bus_number"] == "176"
        assert result["entities"]["bus_stop_code"] == "20251"


class TestGraphRouting:
    def test_route_bus_frequency_to_bus_info(self):
        from singapore_transport.graph import route_by_intent

        assert route_by_intent({"intent": "bus_frequency"}) == "bus_info"
        assert route_by_intent({"intent": "weather_only"}) == "weather_only"
