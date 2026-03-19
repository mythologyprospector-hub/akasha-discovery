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

    nodes = {
        name: KnowledgeNode(id=name, domain="phase_systems")
        for name in node_defs.keys()
    }

    for name, attrs in node_defs.items():
        if isinstance(attrs, dict):
            nodes[name].metadata = attrs
        else:
            nodes[name].metadata = {"value": attrs}

    for edge_name, spec in edge_defs.items():
        if not isinstance(spec, dict):
            continue

        src = spec.get("from")
        dst = spec.get("to")

        if src in nodes and dst in nodes:
            nodes[src].connections.append(nodes[dst])

    incoming_counts = {name: 0 for name in nodes.keys()}

    for node in nodes.values():
        node.outgoing = len(node.connections)
        for conn in node.connections:
            incoming_counts[conn.id] += 1

    for name, node in nodes.items():
        node.incoming = incoming_counts[name]

    return list(nodes.values())


def scan_repo_manifests():
    home = Path.home()
    manifests = []

    for repo_dir in sorted(home.glob("akasha-*")):
        manifest_path = repo_dir / "repo-manifest.yaml"
        if not manifest_path.exists():
            continue

        try:
            data = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
        except Exception:
            data = {"name": repo_dir.name, "status": {"maturity": "unknown"}}

        manifests.append({
            "repo": repo_dir.name,
            "path": str(repo_dir),
            "manifest": data,
        })

    return manifests


def summarize_ecosystem(manifests):
    total = len(manifests)
    experimental = 0
    exploratory = 0

    for item in manifests:
        manifest = item["manifest"]

        role = (
            manifest.get("role")
            or manifest.get("identity", {}).get("role")
            or ""
        )
        maturity = (
            manifest.get("status", {}).get("maturity")
            if isinstance(manifest.get("status"), dict)
            else manifest.get("status", "")
        )

        if role == "exploratory_module":
            exploratory += 1
        if maturity == "experimental":
            experimental += 1

    return {
        "total_repos": total,
        "experimental_repos": experimental,
        "exploratory_modules": exploratory,
    }


def run():
    print("=" * 50)
    print("AKASHA — Discovery Run")
    print("=" * 50)
    print()

    config = load_config(str(ROOT / "config.yaml"))
    graph_source = config.get("graph_source", "graph_schema.yaml")
    schema_path = (ROOT / graph_source).resolve()

    manifests = scan_repo_manifests()
    ecosystem = summarize_ecosystem(manifests)

    print("Ecosystem awareness:")
    print(f"  Repos discovered:       {ecosystem['total_repos']}")
    print(f"  Experimental repos:    {ecosystem['experimental_repos']}")
    print(f"  Exploratory modules:   {ecosystem['exploratory_modules']}")
    print()

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

    # Ecosystem awareness: warn if repo already exists
    repo_candidate = build_plan.get("repo_candidate")
    if repo_candidate and (Path.home() / repo_candidate).exists():
        build_plan["recommended_action"] = f"Review existing module '{repo_candidate}' before materializing"
        build_plan["action"] = "flag_for_review"
        build_plan["repo_candidate"] = repo_candidate
        build_plan["files_to_create"] = []
        print(f"[Awareness] Repo already exists: ~/{repo_candidate}")
        print("[Awareness] Switching action to flag_for_review")
        print()
    else:
        forge.materialize(build_plan)

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
