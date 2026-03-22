#!/usr/bin/env python3

import yaml
from pathlib import Path

def load_table(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def load_graph(path):
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    nodes = {}

    for name, attrs in data.get("nodes", {}).items():
        nodes[name] = {
            "id": name,
            "meta": attrs or {},
            "incoming_relations": [],
            "outgoing_relations": [],
            "connections": []
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

def schema_gaps(nodes, table):
    gaps = []

    node_types = table.get("node_types", {})

    for n in nodes:
        node_type = infer_type(n["id"])
        rule = node_types.get(node_type, {})

        expects_in = set(rule.get("expects_incoming", []))
        expects_out = set(rule.get("expects_outgoing", []))
        allows_out = rule.get("allows_outgoing", None)

        actual_in = set(n["incoming_relations"])
        actual_out = set(n["outgoing_relations"])

        if expects_in and not (expects_in & actual_in):
            gaps.append(("missing_required_incoming", n["id"], sorted(expects_in), sorted(actual_in)))

        if expects_out and not (expects_out & actual_out):
            gaps.append(("missing_required_outgoing", n["id"], sorted(expects_out), sorted(actual_out)))

        if allows_out == [] and actual_out:
            gaps.append(("illegal_outgoing_for_terminal", n["id"], [], sorted(actual_out)))

    return gaps

def run():
    print("==================================================")
    print("AKASHA — Discovery Run")
    print("==================================================")
    print()

    graph_path = Path("~/akasha-graph-phases/graph_schema.yaml").expanduser()
    table_path = Path("~/akasha-world/schema/akasha_table.yaml").expanduser()

    nodes = load_graph(graph_path)
    table = load_table(table_path)

    print(f"Loaded {len(nodes)} nodes from graph_schema.yaml")
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
    run()
