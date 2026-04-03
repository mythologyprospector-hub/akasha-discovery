import yaml


class ArchitecturalGapDetector:

    def __init__(self, anatomy_file):

        with open(anatomy_file, "r") as f:
            self.anatomy = yaml.safe_load(f)

    def detect(self, inventory):

        gaps = []

        roles_present = set()

        for repo in inventory:
            role = repo.get("role")
            if role:
                roles_present.add(role)

        for family, data in self.anatomy["organ_families"].items():

            for role in data["expected_roles"]:

                if role not in roles_present:

                    gaps.append({
                        "gap_type": "missing_organ",
                        "family": family,
                        "role": role,
                        "reason": f"No repository currently fulfills role '{role}'"
                    })

        return gaps
