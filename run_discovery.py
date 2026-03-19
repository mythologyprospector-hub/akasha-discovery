#!/usr/bin/env python3

import json
import sys
from pathlib import Path
from datetime import datetime, UTC

import yaml

ROOT = Path(__file__).resolve().parent
STATE_DIR = ROOT / "state"
STATE_FILE = STATE_DIR / "system_state.json"

sys.path.insert(0, str(ROOT / "engine"))
sys.path.insert(0, str(ROOT.parent / "akasha-forge" / "engine"))

from curiosity_engine import CuriosityEngine, KnowledgeNode
from forge_stub import ForgeStub


def now():
    return datetime.now(UTC).isoformat()


def load_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_state():
    if not STATE_FILE.exists():
        return {}
    try:
        raw = STATE_FILE.read_text(encoding="utf-8").strip()
        if not raw:
            return {}
        return json.loads(raw)
    except Exception:
        return {}


def save_state(state):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def load_graph(schema_path: str):
    with open(schema_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    nodes = {
        name: KnowledgeNode(id=name, domain="phase_systems")
        for name in data.get("nodes", {})
    }

    for name, attrs in data.get("nodes", {}).items():
        nodes[name].metadata = attrs if isinstance(attrs, dict) else {"value": attrs}

    for spec in data.get("edges", {}).values():
        if not isinstance(spec, dict):
            continue
        src, dst = spec.get("from"), spec.get("to")
        if src in nodes and dst in nodes:
            nodes[src].connections.append(nodes[dst])

    incoming = {n: 0 for n in nodes}
    for node in nodes.values():
        node.outgoing = len(node.connections)
        for c in node.connections:
            incoming[c.id] += 1

    for name, node in nodes.items():
        node.incoming = incoming[name]

    return list(nodes.values())


def scan_repo_manifests():
    home = Path.home()
    manifests = []

    for repo_dir in home.glob("akasha-*"):
        if not repo_dir.is_dir():
            continue

        mpath = repo_dir / "repo-manifest.yaml"
        if not mpath.exists():
            continue

        try:
            manifest = yaml.safe_load(mpath.read_text(encoding="utf-8")) or {}
        except Exception:
            manifest = {}

        manifests.append({"repo": repo_dir.name, "manifest": manifest})

    return manifests


def get_status_maturity(manifest: dict) -> str:
    status = manifest.get("status", {})
    if isinstance(status, dict):
        return status.get("maturity", "")
    if isinstance(status, str):
        return status
    return ""


def get_role(manifest: dict) -> str:
    return (
        manifest.get("role")
        or manifest.get("identity", {}).get("role")
        or ""
    )


def summarize_ecosystem(manifests):
    experimental = 0
    exploratory = 0

    for m in manifests:
        manifest = m["manifest"]

        role = get_role(manifest)
        maturity = get_status_maturity(manifest)

        if role == "exploratory_module":
            exploratory += 1

        if maturity == "experimental":
            experimental += 1

    return {
        "total": len(manifests),
        "experimental": experimental,
        "exploratory": exploratory,
    }


def detect_weak(manifests):
    weak = []

    for m in manifests:
        man = m["manifest"]

        func = man.get("function", {})
        rel = man.get("relationships", {})
        maturity = get_status_maturity(man)

        terminal = func.get("terminal", False)
        outputs = func.get("outputs", [])
        downstream = rel.get("downstream", [])

        if not isinstance(outputs, list):
            outputs = []
        if not isinstance(downstream, list):
            downstream = []

        reasons = []

        if "function" in man and not terminal and not outputs:
            reasons.append("no outputs")

        if "relationships" in man and not terminal and not downstream:
            reasons.append("no downstream")

        if maturity == "experimental" and not terminal and not outputs and not downstream:
            reasons.append("no propagation")

        if reasons:
            weak.append({"repo": m["repo"], "reasons": reasons})

    return weak


def run():
    print("=" * 50)
    print("AKASHA — Discovery Run")
    print("=" * 50)
    print()

    cfg = load_config(str(ROOT / "config.yaml"))
    schema = (ROOT / cfg.get("graph_source", "graph_schema.yaml")).resolve()

    manifests = scan_repo_manifests()
    eco = summarize_ecosystem(manifests)
    weak = detect_weak(manifests)

    print("Ecosystem awareness:")
    print(f"  Repos discovered:       {eco['total']}")
    print(f"  Experimental repos:    {eco['experimental']}")
    print(f"  Exploratory modules:   {eco['exploratory']}")
    print(f"  Weak modules:          {len(weak)}")
    print()

    if weak:
        print("Ecosystem judgment:")
        for item in weak:
            print(f"  [Judgment] {item['repo']}: {', '.join(item['reasons'])}")
        print()

    nodes = load_graph(str(schema))

    print(f"Loaded {len(nodes)} nodes from {schema.name}")
    for n in nodes:
        print(f"  {n.id} ({len(n.connections)} connections)")
    print()

    sinks = [n for n in nodes if n.incoming > 0 and n.outgoing == 0]
    stable = (len(sinks) == 1 and sinks[0].id == "attractor" and not weak)

    state = load_state()

    if stable:
        if state.get("status") != "stable":
            last_event = state.get("last_event", {})
            if last_event:
                last_event["resolved_at"] = now()

            state = {
                "status": "stable",
                "since": now(),
                "last_event": last_event or None,
            }
            save_state(state)

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

    state = {
        "status": "unstable",
        "since": now(),
        "last_event": {
            "type": hypothesis.get("gap_type"),
            "target": hypothesis.get("target"),
            "timestamp": now(),
        },
    }
    save_state(state)

    print("Hypothesis generated:")
    print(json.dumps(hypothesis, indent=2))
    print()

    forge = ForgeStub()
    plan = forge.build_proposal(hypothesis)

    if plan.get("repo_candidate") and (Path.home() / plan["repo_candidate"]).exists():
        plan["action"] = "flag_for_review"
        plan["files_to_create"] = []
        print("[Awareness] Existing repo detected — review instead")
        print()
    else:
        forge.materialize(plan)

    out = forge.save_build_plan(plan)

    print(f"Build plan saved to: {out}")
    print("=" * 50)
    print("Pipeline complete. First heartbeat.")
    print("=" * 50)


if __name__ == "__main__":
    run()
