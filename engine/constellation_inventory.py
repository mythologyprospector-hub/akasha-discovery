import os
import yaml


class ConstellationInventory:

    def __init__(self, root_path="."):
        self.root = root_path

    def scan(self):
        inventory = []

        for item in os.listdir(self.root):

            path = os.path.join(self.root, item)

            if not os.path.isdir(path):
                continue

            manifest = os.path.join(path, "repo-manifest.yaml")

            if not os.path.exists(manifest):
                continue

            try:
                with open(manifest, "r") as f:
                    data = yaml.safe_load(f)
            except Exception:
                continue

            entry = {
                "repo": item,
                "family": data.get("engine", {}).get("family"),
                "class": data.get("engine", {}).get("class"),
                "role": data.get("engine", {}).get("role"),
                "layer": data.get("identity", {}).get("layer"),
                "depends_on": data.get("topology", {}).get("depends_on", [])
            }

            inventory.append(entry)

        return inventory
