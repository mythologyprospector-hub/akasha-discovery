import json


class Organogenesis:
    """
    Converts detected architectural gaps into structured Akasha repo proposals.
    """

    def generate(self, gaps):

        proposals = []

        for gap in gaps:

            if gap["gap_type"] == "missing_organ":
                proposals.append(self._generate_missing_organ(gap))

            elif gap["gap_type"] == "weak_bridge":
                proposals.append(self._generate_bridge(gap))

        return proposals


    def _generate_missing_organ(self, gap):

        repo_candidate = f"akasha-{gap['role'].replace('_','-')}"

        return {
            "proposal_type": "missing_organ",
            "repo_candidate": repo_candidate,
            "title": f"{gap['role'].replace('_',' ').title()} Engine",
            "reason": gap["reason"],
            "family": gap["family"],
            "class": "organ_engine",
            "role": gap["role"],
            "layer": "unknown",
            "description": f"Akasha organ responsible for role '{gap['role']}'.",
            "depends_on": [],
            "starter_files": [
                "README.md",
                "repo-manifest.yaml",
                "engine/__init__.py"
            ],
            "confidence": "medium",
            "review_status": "candidate"
        }


    def _generate_bridge(self, gap):

        # Canonical bridge naming rules
        name_map = {
            "gap_detection_to_artifact_and_structure_forging_bridge":
                "akasha-discovery-forge-bridge",

            "artifact_and_structure_forging_to_structure_and_output_rendering_bridge":
                "akasha-forge-visualize-bridge",

            "source_harvesting_to_gap_detection_bridge":
                "akasha-harvest-discovery-bridge"
        }

        role = gap["role"]

        repo_candidate = name_map.get(
            role,
            f"akasha-{role.replace('_','-')}"
        )

        return {
            "proposal_type": "weak_bridge",
            "repo_candidate": repo_candidate,
            "title": "Akasha System Bridge",
            "reason": gap["reason"],
            "family": "governance",
            "class": "bridge_engine",
            "role": role,
            "layer": "coordination",
            "description": "Coordinates signal flow between Akasha system organs.",
            "depends_on": [],
            "starter_files": [
                "README.md",
                "repo-manifest.yaml",
                "bridge/router.py"
            ],
            "confidence": "medium",
            "review_status": "candidate"
        }


    def write(self, proposals, output_path):

        with open(output_path, "w") as f:
            json.dump(proposals, f, indent=2)
