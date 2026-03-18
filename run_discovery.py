"""
run_discovery.py

First heartbeat of the Akasha pipeline.

Loads nodes from graph_schema.yaml
→ scores gaps (crudely, intentionally)
→ emits one hypothesis
→ hands it to ForgeStub
→ saves a build artifact
→ prints the result

Scoring is dumb on purpose.
Motion before meaning.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "engine"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../akasha-forge/engine"))

import json
import yaml
from pathlib import Path

from curiosity_engine import CuriosityEngine, KnowledgeNode
from forge_stub import ForgeStub


def load_graph(schema_path: str) -> list:
    """
    Load nodes from graph_schema.yaml.
    Edges become connections between nodes.
    Crude but sufficient for first run.
    """
    with open(schema_path, "r") as f:
        schema = yaml.safe_load(f)

    node_defs = schema.get("nodes", {})
    edge_defs = schema.get("edges", {})

    # Build node objects
    nodes = {
        name: KnowledgeNode(id=name, domain="phase_systems")
        for name in node_defs
    }

    # Wire connections from edges
    for edge_name, edge in edge_defs.items():
        src = edge.get("from")
        tgt = edge.get("to")
        if src in nodes and tgt in nodes:
            nodes[src].connections.append(nodes[tgt])

    return list(nodes.values())


def run():
    print("=" * 50)
    print("AKASHA — Discovery Run")
    print("=" * 50)

    # 1. Load nodes from the phase systems graph
    schema_path = Path(__file__).parent / "graph_schema.yaml"
    nodes = load_graph(str(schema_path))
    print(f"\nLoaded {len(nodes)} nodes from graph_schema.yaml")
    for n in nodes:
        print(f"  {n.id} ({len(n.connections)} connections)")

    # 2. Run curiosity engine — one step
    engine = CuriosityEngine(nodes)
    hypothesis = engine.step()

    if not hypothesis:
        print("\nNo gaps detected above threshold.")
        return

    print(f"\nHypothesis generated:")
    print(json.dumps(hypothesis, indent=2, default=str))

    # 3. Hand to forge
    forge = ForgeStub(output_dir="build_outputs")
    plan = forge.build_proposal(hypothesis)
    path = forge.save_build_plan(plan)

    print(f"\nBuild plan saved to: {path}")
    print("\nBuild plan:")
    print(json.dumps(plan, indent=2))

    print("\n" + "=" * 50)
    print("Pipeline complete. First heartbeat.")
    print("=" * 50)


if __name__ == "__main__":
    run()
