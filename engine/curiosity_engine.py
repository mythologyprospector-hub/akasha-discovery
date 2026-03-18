"""
Curiosity Engine

Detects gaps in knowledge space and applies pressure
to resolve them through proposal generation.
"""

from typing import List, Dict

class KnowledgeNode:
    def __init__(self, id, domain, connections=None, metadata=None):
        self.id = id
        self.domain = domain
        self.connections = connections or []
        self.metadata = metadata or {}

class CuriosityEngine:
    def __init__(self, nodes: List[KnowledgeNode]):
        self.nodes = nodes
        self.gap_threshold = 0.6
        self.history = []

    def evaluate_gap(self, node: KnowledgeNode) -> float:
        """
        Gap score = lack of connections + cross-domain isolation
        """
        connection_count = len(node.connections)

        domain_diversity = len(
            set([c.domain for c in node.connections])
        ) if node.connections else 0

        # Normalize (simple heuristic)
        score = 1.0 - (
            0.5 * min(connection_count / 10, 1.0) +
            0.5 * min(domain_diversity / 5, 1.0)
        )

        return round(score, 3)

    def find_gaps(self) -> List[Dict]:
        gaps = []
        for node in self.nodes:
            score = self.evaluate_gap(node)
            if score >= self.gap_threshold:
                gaps.append({
                    "node": node,
                    "gap_score": score
                })

        return sorted(
            gaps,
            key=lambda x: x["gap_score"],
            reverse=True
        )

    def generate_hypothesis(self, gap: Dict) -> Dict:
        node = gap["node"]

        hypothesis = {
            "target": node.id,
            "gap_score": gap["gap_score"],
            "proposal": f"Explore missing connections for '{node.id}'",
            "suggestions": [
                f"Link '{node.id}' to adjacent domains",
                f"Search for analogous structures in other fields",
                f"Generate tool or model to bridge domain gap"
            ]
        }

        return hypothesis

    def step(self) -> Dict | None:
        gaps = self.find_gaps()

        if not gaps:
            return None

        # Highest pressure gap
        selected = gaps[0]

        hypothesis = self.generate_hypothesis(selected)

        self.history.append(hypothesis)

        return hypothesis
