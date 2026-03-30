#!/usr/bin/env python3

import yaml
from itertools import product
from pathlib import Path

LATTICE = Path("~/akasha-world/schema/akasha_lattice.yaml").expanduser()

def load_lattice(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def generate_space(axes):
    keys = list(axes.keys())
    values = [axes[k] for k in keys]
    for combo in product(*values):
        yield dict(zip(keys, combo))

def matches_rule(coord, rule):
    return all(coord.get(k) == v for k, v in rule.items())

def is_valid(coord, lattice):
    invalid_rules = lattice.get("rules", {}).get("invalid", [])
    for rule in invalid_rules:
        if matches_rule(coord, rule):
            return False
    return True

def coord_tuple(coord, axes):
    return tuple(coord[k] for k in axes.keys())

def distance(a, b):
    return sum(1 for k in a if a[k] != b[k])

def score_coord(coord, known_nodes):
    nearest = min(distance(coord, node) for node in known_nodes.values())
    score = 10 - nearest

    if coord.get("stability") == "unstable":
        score += 2
    if coord.get("process") in ("transform", "converge"):
        score += 2
    if coord.get("constraint") in ("strong", "maximal"):
        score += 1

    return score, nearest

def suggest_name(coord):
    phase = coord["phase"]
    stability = coord["stability"]
    constraint = coord["constraint"]
    process = coord["process"]

    if stability == "unstable" and process == "transform" and constraint in ("strong", "maximal"):
        return "critical_transition"
    if stability == "unstable" and process == "converge":
        return "recovery_boundary"
    if stability == "stable" and constraint == "maximal":
        return "locked_equilibrium"
    if phase == "transition" and stability == "unstable":
        return "volatile_transition"
    if constraint in ("strong", "maximal") and process == "none":
        return "constraint_barrier"

    return f"{stability}_{process}_{constraint}_{phase}"

def scan_missing(lattice):
    axes = lattice.get("axes", {})
    nodes = lattice.get("nodes", {})

    known = set()
    for _, coord in nodes.items():
        known.add(coord_tuple(coord, axes))

    missing = []
    for coord in generate_space(axes):
        if not is_valid(coord, lattice):
            continue
        tup = coord_tuple(coord, axes)
        if tup not in known:
            score, nearest = score_coord(coord, nodes)
            missing.append({
                "coord": coord,
                "score": score,
                "nearest_distance": nearest,
                "name": suggest_name(coord),
            })

    missing.sort(key=lambda x: (-x["score"], x["nearest_distance"], x["name"]))
    return missing

def main():
    lattice = load_lattice(LATTICE)
    missing = scan_missing(lattice)

    print("==================================")
    print(" AKASHA LATTICE SCAN (NAMED)")
    print("==================================")
    print()
    print(f"Known nodes: {len(lattice.get('nodes', {}))}")
    print(f"Missing valid coordinates: {len(missing)}")
    print()

    for item in missing[:12]:
        print(f"{item['name']:<22} score={item['score']} nearest={item['nearest_distance']}")
        print(f"  {item['coord']}")

if __name__ == "__main__":
    main()
