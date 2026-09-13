#!/usr/bin/env python3
"""CLI chat / multi-user simulation for the transport agent."""

from __future__ import annotations

import argparse
import re
import sys
import time

from singapore_transport.agent import TransportAgent

DEFAULT_SIMULATION = [
    "When is the next bus 176 arriving at stop 20251?",
    "Is there any heavy traffic or jams right now?",
    "Tell me about bus service 15.",
    "Is it raining? Should I bring an umbrella?",
    "When is the next bus arriving at stop 83139?",
    "Are there any train disruptions on the NEL line?",
    "What is the frequency of bus 107M during peak hours?",
    "When is the next bus 177 arriving at stop 20251?",
    "Check bus arrival for stop 00000",
    "Hi, I need help with my travel plans.",
]


def format_for_cli(text: str) -> str:
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def run_once(query: str) -> None:
    agent = TransportAgent()
    result = agent.ask(query)
    print("\n" + "=" * 50)
    print(format_for_cli(result.get("final_answer") or "No output"))
    print("=" * 50 + "\n")


def run_simulation(delay: float) -> None:
    agent = TransportAgent()
    print(f"Starting simulation of {len(DEFAULT_SIMULATION)} user requests...\n")
    for i, query in enumerate(DEFAULT_SIMULATION, 1):
        print(f'USER {i}: "{query}"')
        print("-" * 60)
        try:
            result = agent.ask(query)
            print(f"AGENT:\n{result.get('final_answer', 'No response generated.')}")
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR: {exc}")
        print("\n" + "=" * 60 + "\n")
        if i < len(DEFAULT_SIMULATION) and delay > 0:
            print(f"Waiting {delay:.0f}s to respect API rate limits...")
            time.sleep(delay)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Singapore Transport Agent CLI")
    parser.add_argument("query", nargs="?", help="Single query to ask")
    parser.add_argument("--simulate", action="store_true", help="Run the 10-user simulation")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between simulation queries")
    args = parser.parse_args(argv)

    if args.simulate:
        run_simulation(args.delay)
        return 0
    if args.query:
        run_once(args.query)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
