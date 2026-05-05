#!/usr/bin/env python3
"""CLI: provision or update an ElevenAgents scenario agent and print ``agent_id``."""

from __future__ import annotations

import argparse
from importlib import import_module


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Provision (idempotent upsert) a vertical demo agent and print its agent_id "
            "(paste into DEMO_AGENT_ID_* in .env for scripts/agent_simulate.py)."
        ),
    )
    parser.add_argument(
        "scenario",
        choices=("telecom", "banking", "healthcare"),
        help="Scenario package under eleven_demo.scenarios.",
    )
    args = parser.parse_args()

    module = import_module(f"eleven_demo.scenarios.{args.scenario}")
    agent_id = module.provision()
    print(agent_id)


if __name__ == "__main__":
    main()
