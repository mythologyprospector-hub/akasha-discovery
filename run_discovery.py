#!/usr/bin/env python3
"""
run_discovery.py

First heartbeat of the Akasha pipeline.

Loads nodes from graph source defined in config.yaml
→ scores gaps
→ emits one hypothesis
→ hands it to ForgeStub
→ saves a build artifact
→ prints the result
"""

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent

# Keep environment/path logic in the runner, not the engine
sys.path.insert(0, str(ROOT / "engine"))
sys.path.insert(0, str(ROOT.parent / "akasha-forge" / "engine"))

from curiosity_engine import CuriosityEngine, KnowledgeNode
from forge_stub import ForgeStub


def load_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_graph(schema_path: str):
    with open(schema_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    node_defs = data.get("nodes", {})
    edge_defs = data.get("edges", {})

    # Create node objects
    nodes = {
        name: KnowledgeNode(id=name, domain="phase_systems")
        for name in node_defs.keys()
    }

    # Attach metadata/description if present
    for name, attrs in node_defs.items():
        if isinstance(attrs, dict):
            nodes[name].metadata = attrs
        else:
            nodes[name].metadata = {"value": attrs}

    # Build graph connections
    for edge_name, spec in edge_defs.items():
        if not isinstance(spec, dict):
            continue

        src = spec.get("from")
        dst = spec.get("to")

        if src in nodes and dst in nodes:
            nodes[src].connections.append(nodes[dst])

    # Compute incoming/outgoing counts for classifier compatibility
    incoming_counts = {name: 0 for name in nodes.keys()}

    for node in nodes.values():
        node.outgoing = len(node.connections)
        for conn in node.connections:
            incoming_counts[conn.id] += 1

    for name, node in nodes.items():
        node.incoming = incoming_counts[name]

    return list(nodes.values())


def run():
    print("=" * 50)
    print("AKASHA — Discovery Run")
    print("=" * 50)
    print()

    config = load_config(str(ROOT / "config.yaml"))
    graph_source = config.get("graph_source", "graph_schema.yaml")
    schema_path = (ROOT / graph_source).resolve()

    nodes = load_graph(str(schema_path))

    print(f"Loaded {len(nodes)} nodes from {schema_path.name}")
    for node in nodes:
        print(f"  {node.id} ({len(node.connections)} connections)")
    print()

    engine = CuriosityEngine(nodes)
    hypothesis = engine.step()

    if not hypothesis:
        print("No hypothesis generated.")
        return

    print("Hypothesis generated:")
    print(json.dumps(hypothesis, indent=2))
    print()

    forge = ForgeStub()
    build_plan = forge.build_proposal(hypothesis)
    output_path = forge.save_build_plan(build_plan)

    print(f"Build plan saved to: {output_path}")
    print()
    print("Build plan:")
    print(json.dumps(build_plan, indent=2))
    print()
    print("=" * 50)
    print("Pipeline complete. First heartbeat.")
    print("=" * 50)


if __name__ == "__main__":
    run()
