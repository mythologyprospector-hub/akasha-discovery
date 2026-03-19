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

    # Detect structural sinks
    structural_sinks = [
        n for n in nodes if n.incoming > 0 and n.outgoing == 0
    ]

    # If only intentional terminal remains, do nothing
    if not weak and len(structural_sinks) == 1 and structural_sinks[0].id == "attractor":
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
