#!/usr/bin/env python3

import argparse
import yaml
from pathlib import Path


def load_table(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_graph(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    nodes = {}

    for name, attrs in data.get("nodes", {}).items():
        nodes[name] = {
            "id": name,
            "meta": attrs or {},
            "incoming_relations": [],
            "outgoing_relations": [],
            "connections": [],
        }

    for rel_name, spec in data.get("edges", {}).items():
        if not isinstance(spec, dict):
            continue

        src = spec.get("from")
        dst = spec.get("to")

        if src in nodes and dst in nodes:
            nodes[src]["connections"].append(dst)
            nodes[src]["outgoing_relations"].append(rel_name)
            nodes[dst]["incoming_relations"].append(rel_name)

    return list(nodes.values())


def infer_type(node_id):
    if node_id == "attractor":
        return "attractor"
    if node_id in ["phase", "equilibrium", "instability"]:
        return "state"
    if node_id == "transition":
        return "process"
    if node_id == "constraint":
        return "constraint"
    return "observer"


def normalize_relation(rel, table):
    aliases = table.get("relation_aliases", {})
    for canonical, alts in aliases.items():
        if rel == canonical or rel in alts:
            return canonical
    return rel


def schema_gaps(nodes, table):
    gaps = []

    node_types = table.get("node_types", {})

    for n in nodes:
        node_type = infer_type(n["id"])
        rule = node_types.get(node_type, {})

        expects_in = set(rule.get("expects_incoming", []))
        expects_out = set(rule.get("expects_outgoing", []))
        allows_out = rule.get("allows_outgoing", None)

        actual_in = {normalize_relation(r, table) for r in n["incoming_relations"]}
        actual_out = {normalize_relation(r, table) for r in n["outgoing_relations"]}

        if expects_in and not (expects_in & actual_in):
            gaps.append(("missing_required_incoming", n["id"], sorted(expects_in), sorted(actual_in)))

        if expects_out and not (expects_out & actual_out):
            gaps.append(("missing_required_outgoing", n["id"], sorted(expects_out), sorted(actual_out)))

        if allows_out == [] and actual_out:
            gaps.append(("illegal_outgoing_for_terminal", n["id"], [], sorted(actual_out)))

    return gaps


def candidate_roots(script_dir: Path) -> list[Path]:
    roots = []
    env_root = Path.home()
    akasha_home = env_root / "akasha"
    if akasha_home.exists():
        roots.append(akasha_home)
    roots.append(env_root)
    roots.append(script_dir.parent)
    roots.append(script_dir)
    return roots


def resolve_path(explicit: str | None, config_value: str | None, script_dir: Path, *fallbacks: str) -> Path:
    candidates = []

    def add_candidate(raw):
        if not raw:
            return
        p = Path(raw).expanduser()
        candidates.append(p)
        if not p.is_absolute():
            candidates.append((script_dir / p).resolve())
            candidates.append((script_dir.parent / p).resolve())
            for root in candidate_roots(script_dir):
                candidates.append((root / p).resolve())

    add_candidate(explicit)
    add_candidate(config_value)
    for item in fallbacks:
        add_candidate(item)

    seen = set()
    for path in candidates:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        if path.exists():
            return path

    searched = "\n  - ".join(str(p) for p in candidates)
    raise FileNotFoundError(f"Could not resolve required file. Searched:\n  - {searched}")


def load_config(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def run(graph_override: str | None = None, table_override: str | None = None):
    print("==================================================")
    print("AKASHA — Discovery Run")
    print("==================================================")
    print()

    script_dir = Path(__file__).resolve().parent
    config = load_config(script_dir / "config.yaml")

    graph_path = resolve_path(
        graph_override,
        config.get("graph_source"),
        script_dir,
        "~/akasha-graph-phases/graph_schema.yaml",
        "graph_schema.yaml",
        "../akasha-graph-phases/graph_schema.yaml",
    )
    table_path = resolve_path(
        table_override,
        config.get("table_source"),
        script_dir,
        "~/akasha-world/schema/akasha_table.yaml",
        "../akasha-world/schema/akasha_table.yaml",
    )

    nodes = load_graph(graph_path)
    table = load_table(table_path)

    print(f"Graph: {graph_path}")
    print(f"Table: {table_path}")
    print()
    print(f"Loaded {len(nodes)} nodes from {graph_path.name}")
    for n in nodes:
        print(f"  {n['id']} ({len(n['connections'])} connections)")
    print()

    gaps = schema_gaps(nodes, table)

    if gaps:
        print("Schema Gaps Detected:")
        for kind, node_id, expected, actual in gaps:
            print(f"  {kind}: {node_id}")
            print(f"    expected: {expected}")
            print(f"    actual:   {actual}")
    else:
        print("No schema gaps detected.")

    print()
    print("==================================================")
    print("Pipeline complete.")
    print("==================================================")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Akasha discovery schema checks.")
    parser.add_argument("--graph", help="Explicit path to graph schema YAML.")
    parser.add_argument("--table", help="Explicit path to akasha table YAML.")
    args = parser.parse_args()
    run(args.graph, args.table)
