import argparse
import os
import json
from datetime import datetime, UTC

from engine.constellation_inventory import ConstellationInventory
from engine.architectural_gap_detector import ArchitecturalGapDetector
from engine.bridge_detector import BridgeDetector
from engine.organogenesis import Organogenesis


def run_constellation():
    print("AKASHA CONSTELLATION DISCOVERY")
    print("--------------------------------")

    # Scan constellation
    inventory_engine = ConstellationInventory("..")
    inventory = inventory_engine.scan()

    print(f"repos scanned: {len(inventory)}")

    # Detect missing organs
    detector = ArchitecturalGapDetector("schema/akasha_anatomy.yaml")
    gaps = detector.detect(inventory)

    # Detect weak or missing bridges between existing organs
    bridge_detector = BridgeDetector()
    bridge_gaps = bridge_detector.detect(inventory)

    gaps.extend(bridge_gaps)

    print(f"gaps detected: {len(gaps)}")

    # Generate proposals
    organ = Organogenesis()
    proposals = organ.generate(gaps)

    # Safe UTC timestamp
    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%SZ")

    outdir = f"build_outputs/runs/{timestamp}"
    os.makedirs(outdir, exist_ok=True)

    proposals_file = f"{outdir}/candidate_proposals.json"

    # Write proposals
    organ.write(proposals, proposals_file)

    # Write summary
    summary = {
        "timestamp": timestamp,
        "repos_scanned": len(inventory),
        "gaps_detected": len(gaps),
        "organ_gaps_detected": len([g for g in gaps if g.get("gap_type") == "missing_organ"]),
        "bridge_gaps_detected": len([g for g in gaps if g.get("gap_type") == "weak_bridge"]),
        "proposals_generated": len(proposals),
    }

    with open(f"{outdir}/summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    # Console summary
    print("")
    print("Discovery summary")
    print("-----------------")
    print(f"organ gaps: {summary['organ_gaps_detected']}")
    print(f"bridge gaps: {summary['bridge_gaps_detected']}")
    print(f"proposals generated: {summary['proposals_generated']}")
    print("")
    print("Output directory:")
    print(outdir)
    print("")
    print("Proposals file:")
    print(proposals_file)

    if proposals:
        print("")
        print("Proposed repos:")
        for proposal in proposals:
            print(f"  - {proposal.get('repo_candidate')} ({proposal.get('proposal_type')})")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--mode",
        default="concept",
        help="concept or constellation"
    )

    args = parser.parse_args()

    if args.mode == "constellation":
        run_constellation()
    else:
        print("Concept discovery mode not implemented yet.")


if __name__ == "__main__":
    main()
