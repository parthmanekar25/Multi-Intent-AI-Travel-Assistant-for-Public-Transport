# Multi-Intent-AI-Travel-Assistant-for-Public-Transport
#  Singapore Transport Agent
**Author:** Parth Manekar  


##  Project Overview
This notebook implements an agentic workflow using **LangGraph** to answer user queries regarding Singapore's public transport. The agent is designed to be **context-aware**, factoring in real-time variables such as weather, traffic incidents, and peak-hour logic before generating a response.

##  Workflow Architecture
The solution uses a state-based graph architecture (`StateGraph`) to orchestrate the flow of data.
1.  **Intent Extraction:** A generic LLM (via Groq) analyzes the user's natural language query to classify intent (e.g., `bus_arrival`, `weather`, `traffic_area`) and extract entities (e.g., Bus Stop Codes).
2.  **Context Enrichment:** Before hitting the transport API, the state is enriched with environmental constraints:
    * **Time Context:** Determines if it is currently Peak/Off-Peak.
    * **Weather (Data.gov.sg):** Checks for rain to add travel advisories.
    * **Traffic (LTA):** Checks for congestion or accidents.
    * **Disruptions:** Checks MRT status.
3.  **Dynamic Routing:** Based on the intent, the agent routes to specific handlers (e.g., querying LTA DataMall for bus timings or filtering traffic incidents by location).
4.  **Response Generation:** A final node synthesizes the API data, environmental context, and user query into a natural language response.

##  Design Decisions & Assumptions
* **LangGraph over Chains:** Chosen for its cyclic and stateful nature, allowing for easier debugging and future expansion (e.g., adding a "correction" node if an API fails).
* **Deterministic Intent:** To reduce latency and token costs, I used the LLM *only* for intent extraction and final formatting. The core logic (Time/API fetching) is handled by deterministic Python functions.
* **Assumption:** The agent assumes the user is currently in Singapore (GMT+8) for time calculations.
* **Assumption:** "Next Bus" queries imply the immediate next arrival; however, the API returns up to 3 upcoming buses, which are processed to find the nearest one.

##  Deployment Strategy (Production)
To move this from a notebook to a production environment:
1.  **API Gateway (FastAPI):** Expose the `graph.invoke` method via a RESTful endpoint (e.g., `POST /chat`).
2.  **Caching (Redis):** LTA DataMall APIs have rate limits. I would implement a Redis cache (TTL: 1 min for Bus Arrival, 15 mins for Traffic) to serve frequent requests for the same bus stop without hitting the LTA origin server.
3.  **Async/Queues:** For high concurrency, API calls should be asynchronous (`aiohttp`). Long-running queries could be offloaded to a task queue (Celery/RabbitMQ).
4.  **Containerization:** Dockerize the application to ensure consistency across dev and prod environments.
