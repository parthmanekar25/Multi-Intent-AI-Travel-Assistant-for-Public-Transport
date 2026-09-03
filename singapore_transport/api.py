"""FastAPI gateway for the Singapore Transport Agent."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from singapore_transport.agent import TransportAgent

app = FastAPI(
    title="Singapore Transport Agent",
    description="Multi-intent AI assistant for Singapore public transport.",
    version="0.2.0",
)

_agent: TransportAgent | None = None


def get_agent() -> TransportAgent:
    global _agent
    if _agent is None:
        _agent = TransportAgent()
    return _agent


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, examples=["When is bus 176 arriving at stop 20251?"])


class ChatResponse(BaseModel):
    query: str
    intent: Optional[str] = None
    entities: dict[str, Any] = Field(default_factory=dict)
    answer: str
    context: dict[str, Any] = Field(default_factory=dict)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest) -> ChatResponse:
    try:
        result = get_agent().ask(body.query)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Agent error: {exc}") from exc

    return ChatResponse(
        query=body.query,
        intent=result.get("intent"),
        entities=result.get("entities") or {},
        answer=result.get("final_answer") or "",
        context={
            "time": result.get("time_context"),
            "weather": result.get("weather_context"),
            "traffic": result.get("traffic_context"),
            "holiday": result.get("holiday_context"),
        },
    )
