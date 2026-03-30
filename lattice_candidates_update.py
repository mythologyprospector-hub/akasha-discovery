#!/usr/bin/env python3

import yaml
from pathlib import Path

SCAN_OUTPUT = Path("~/akasha-world/candidates/lattice_candidates.yaml").expanduser()

def load_candidates():
    if not SCAN_OUTPUT.exists():
        return {"candidates": {}}
    return yaml.safe_load(open(SCAN_OUTPUT)) or {"candidates": {}}

def save_candidates(data):
    yaml.safe_dump(data, open(SCAN_OUTPUT, "w"), sort_keys=False)

def main():

    data = load_candidates()
    candidates = data.setdefault("candidates", {})

    # placeholder — future auto discovery would add here

    print("Candidates registry loaded.")
    print(f"{len(candidates)} known candidate concepts.")

if __name__ == "__main__":
    main()
