# Singapore Transport Agent

Modular **LangGraph** assistant for Singapore public transport. Replaces the original notebook with a package, FastAPI gateway, CLI, caching, and conditional tool routing.

**Author:** Parth Manekar

## Features

- Intent extraction via Groq (structured JSON)
- Selective context enrichment (time/peak, holidays, weather, traffic, MRT alerts)
- Conditional LangGraph routing to dedicated tool handlers
- Bus stop name/code resolution (`BusStops`)
- Cached LTA DataMall + Data.gov.sg calls
- Asia/Singapore timezone and 2025–2026 holiday calendars
- Humanized crowding labels and next 3 arrivals
- FastAPI `POST /chat` + CLI simulation

## Project layout

```text
singapore_transport/
  agent.py          # TransportAgent.ask()
  api.py            # FastAPI app
  config.py         # env-based settings
  graph.py          # StateGraph + conditional edges
  state.py          # TransportState
  llm/              # Groq client
  nodes/            # intent, context, handlers, response
  tools/            # LTA + weather tools
  utils/            # time, holidays, crowding, cache
scripts/simulate.py
tests/
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# set GROQ_API_KEY and LTA_API_KEY
```

## Run

CLI single query:

```bash
python -m scripts.simulate "When is bus 176 arriving at stop 20251?"
```

10-user simulation (lower delay thanks to caching):

```bash
python -m scripts.simulate --simulate --delay 2
```

API server:

```bash
uvicorn singapore_transport.api:app --reload --port 8000
# POST http://localhost:8000/chat  {"query": "Is it raining?"}
```

Tests (no live keys required):

```bash
pytest -q
```

## Architecture

```text
START → intent → context (selective) → conditional route
   ├─ bus_arrival
   ├─ bus_info / bus_frequency
   ├─ traffic_area
   ├─ weather_only
   ├─ train_disruption
   ├─ nearest_stop
   ├─ general_help / fallback
   └─→ answer → END
```

Deterministic Python tools handle APIs; the LLM is used for intent/entity extraction only.

## Design notes

- All clocks use `Asia/Singapore` (`zoneinfo`).
- Static catalogues (`BusServices`, `BusStops`) are cached ~24h; live arrivals ~60s.
- Train alerts parse nested LTA `value[0].Status` correctly (1=normal, 2=disrupted).
- Weather sets `severity` (`Low` / `Moderate` / `High`) for advisories.



## New capabilities (v0.3)

- **Bus route tool** — "Does bus 36 stop at Orchard?" / route previews via LTA `BusRoutes`
- **Carpark tool** — "Parking near HarbourFront?" via LTA `CarParkAvailability`
- **Stop labels** — bus info shows human stop names, not just Origin/Destination codes
- **Tool registry** — `GET /tools` lists registered tools and intents
- **Session memory** — pass `session_id` to `POST /chat` so follow-ups reuse bus/stop/location entities
- **Legacy notebook** — moved to `legacy/travel_agent.ipynb` (reference only)

### Example session follow-up

```bash
curl -s localhost:8000/chat -H 'content-type: application/json' \
  -d '{"query":"When is bus 176 at 20251?","session_id":"u1"}'
curl -s localhost:8000/chat -H 'content-type: application/json' \
  -d '{"query":"What is its frequency?","session_id":"u1"}'
```

## Extending with more tools

1. Add a fetcher under `singapore_transport/tools/` (e.g. `carpark.py`).
2. Register intent in `state.VALID_INTENTS` + prompt in `nodes/intent.py`.
3. Declare context needs in `nodes/context.INTENT_CONTEXT_NEEDS`.
4. Add a handler in `nodes/handlers.py` and wire it in `graph.py`.
5. Format output in `nodes/response.py`.

Good next tools: `BusRoutes`, carpark availability, ERP rates, OneMap geocoding, journey planning.

## Legacy notebook

`travel_agent .ipynb` is kept for reference. Prefer the package above for all new work.
