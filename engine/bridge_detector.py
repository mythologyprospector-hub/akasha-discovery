class BridgeDetector:

    def detect(self, inventory):

        repos = {repo["repo"]: repo for repo in inventory}

        roles = {repo["role"]: repo["repo"] for repo in inventory if repo["role"]}

        bridges = []

        # Example bridge rules

        bridge_rules = [
            ("gap_detection", "artifact_and_structure_forging", "discovery-forge-bridge"),
            ("source_harvesting", "gap_detection", "harvest-discovery-bridge"),
            ("artifact_and_structure_forging", "structure_and_output_rendering", "forge-herald-bridge")
        ]

        for source_role, target_role, name in bridge_rules:

            if source_role in roles and target_role in roles:

                bridge_repo = f"akasha-{name}"

                if bridge_repo not in repos:

                    bridges.append({
                        "gap_type": "weak_bridge",
                        "family": "governance",
                        "role": f"{source_role}_to_{target_role}_bridge",
                        "reason": f"No bridge detected between {source_role} and {target_role}",
                        "recommended_repo": bridge_repo
                    })

        return bridges
