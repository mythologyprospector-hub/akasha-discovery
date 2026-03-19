#!/usr/bin/env python3
"""
run_discovery.py

Akasha Discovery runner.

Loads graph from config-defined source
→ scans ecosystem manifests
→ summarizes ecosystem state
→ identifies weak modules
→ runs graph-based discovery
→ hands result to Forge
→ prevents duplicate materialization
→ saves build artifact
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
        data = yaml.safe_load(f) or {}

    node_defs = data.get("nodes", {})
    edge_defs = data.get("edges", {})

    nodes = {
        name: KnowledgeNode(id=name, domain="phase_systems")
        for name in node_defs.keys()
    }

    # attach node metadata
    for name, attrs in node_defs.items():
        if isinstance(attrs, dict):
            nodes[name].metadata = attrs
        else:
            nodes[name].metadata = {"value": attrs}

    # build graph edges
    for _, spec in edge_defs.items():
        if not isinstance(spec, dict):
            continue

        src = spec.get("from")
        dst = spec.get("to")

        if src in nodes and dst in nodes:
            nodes[src].connections.append(nodes[dst])

    # compute incoming/outgoing counts
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
        if not repo_dir.is_dir():
            continue

        manifest_path = repo_dir / "repo-manifest.yaml"
        if not manifest_path.exists():
            continue

        try:
            manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
        except Exception:
            manifest = {}

        manifests.append(
            {
                "repo": repo_dir.name,
                "path": str(repo_dir),
                "manifest": manifest,
            }
        )

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

        status = manifest.get("status", {})
        if isinstance(status, dict):
            maturity = status.get("maturity", "")
        else:
            maturity = status

        if role == "exploratory_module":
            exploratory += 1

        if maturity == "experimental":
            experimental += 1

    return {
        "total_repos": total,
        "experimental_repos": experimental,
        "exploratory_modules": exploratory,
    }


def detect_weak_modules(manifests):
    weak = []

    for item in manifests:
        repo = item["repo"]
        manifest = item["manifest"]

        function = manifest.get("function", {})
        relationships = manifest.get("relationships", {})
        status = manifest.get("status", {})

        outputs = function.get("outputs", [])
        downstream = relationships.get("downstream", [])
        terminal = function.get("terminal", False)

        if not isinstance(outputs, list):
            outputs = []
        if not isinstance(downstream, list):
            downstream = []

        maturity = ""
        if isinstance(status, dict):
            maturity = status.get("maturity", "")
        elif isinstance(status, str):
            maturity = status

        reasons = []

        # Terminal modules are allowed to have no outputs/downstream
        if "function" in manifest and not terminal:
            if not outputs:
                reasons.append("no outputs defined")

        if "relationships" in manifest and not terminal:
            if not downstream:
                reasons.append("no downstream usage declared")

        if maturity == "experimental" and not terminal and not outputs and not downstream:
            reasons.append("experimental module has no defined propagation")

        if reasons:
            weak.append(
                {
                    "repo": repo,
                    "reasons": reasons,
                }
            )

    return weak


def print_ecosystem_awareness(manifests):
    ecosystem = summarize_ecosystem(manifests)
    weak = detect_weak_modules(manifests)

    print("Ecosystem awareness:")
    print(f"  Repos discovered:       {ecosystem['total_repos']}")
    print(f"  Experimental repos:    {ecosystem['experimental_repos']}")
    print(f"  Exploratory modules:   {ecosystem['exploratory_modules']}")
    print(f"  Weak modules:          {len(weak)}")
    print()

    if weak:
        print("Ecosystem judgment:")
        for item in weak:
            print(f"  [Judgment] {item['repo']}: {', '.join(item['reasons'])}")
        print()

    return weak


def run():
    print("=" * 50)
    print("AKASHA — Discovery Run")
    print("=" * 50)
    print()

    config = load_config(str(ROOT / "config.yaml"))
    graph_source = config.get("graph_source", "graph_schema.yaml")
    schema_path = (ROOT / graph_source).resolve()

    manifests = scan_repo_manifests()
    weak = print_ecosystem_awareness(manifests)

    nodes = load_graph(str(schema_path))

    print(f"Loaded {len(nodes)} nodes from {schema_path.name}")
    for node in nodes:
        print(f"  {node.id} ({len(node.connections)} connections)")
    print()

    # Stability gate:
    # If there are no weak modules and the only remaining sink is attractor,
    # the system is considered stable and no action is required.
    structural_sinks = [n for n in nodes if n.incoming > 0 and n.outgoing == 0]
    only_attractor_terminal = (
        len(structural_sinks) == 1 and structural_sinks[0].id == "attractor"
    )

    if not weak and only_attractor_terminal:
        print("No active structural gaps detected.")
        print("System is in stable configuration.")
        print()
        print("=" * 50)
        print("Pipeline complete. No action required.")
        print("=" * 50)
        return

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

    repo_candidate = build_plan.get("repo_candidate")
    if repo_candidate and (Path.home() / repo_candidate).exists():
        build_plan["recommended_action"] = (
            f"Review existing module '{repo_candidate}' before materializing"
        )
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
