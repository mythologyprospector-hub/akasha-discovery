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

    def classify_gap(self, node: KnowledgeNode, all_nodes: List) -> Dict:
        """
        Distinguish gap types so Forge doesn't blindly materialize everything.

        structural_sink   — node is a target of edges but emits none
        isolated          — no connections at all
        sparse            — some connections but below density threshold
        """
        outgoing = len(node.connections)
        incoming = sum(1 for n in all_nodes if node in n.connections)

        if incoming > 0 and outgoing == 0:
            return {
                "type": "structural_sink",
                "reason": f"node '{node.id}' receives {incoming} incoming edge(s) but emits none — likely missing propagation structure"
            }
        if incoming == 0 and outgoing == 0:
            return {
                "type": "isolated",
                "reason": f"node '{node.id}' has zero incoming and zero outgoing connections in current graph wiring"
            }
        return {
            "type": "sparse",
            "reason": f"node '{node.id}' has {incoming} incoming and {outgoing} outgoing edges — below density threshold, worth watching"
        }

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
                classification = self.classify_gap(node, self.nodes)
                gaps.append({
                    "node": node,
                    "gap_score": score,
                    "gap_type": classification["type"],
                    "reason": classification["reason"]
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
            "gap_type": gap["gap_type"],
            "reason": gap["reason"],
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
