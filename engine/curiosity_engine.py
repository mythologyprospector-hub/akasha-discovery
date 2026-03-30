from typing import Dict, List, Optional


class KnowledgeNode:
    def __init__(
        self,
        id: str,
        domain: str,
        connections: Optional[List["KnowledgeNode"]] = None,
        metadata: Optional[Dict] = None,
    ):
        self.id = id
        self.domain = domain
        self.connections = connections or []
        self.metadata = metadata or {}

        # Optional compatibility fields used by run_discovery.py
        self.incoming = 0
        self.outgoing = None  # let classifier fall back to len(connections)


INTENTIONAL_TERMINALS = {
    "attractor"
}


class CuriosityEngine:
    def __init__(self, nodes: List[KnowledgeNode]):
        self.nodes = nodes
        self.history = []

    def _incoming_count(self, node: KnowledgeNode) -> int:
        if getattr(node, "incoming", None) not in (None, 0):
            return node.incoming

        # Fallback: count references from other nodes' connections
        count = 0
        for other in self.nodes:
            for conn in getattr(other, "connections", []):
                if getattr(conn, "id", None) == node.id:
                    count += 1
        return count

    def _outgoing_count(self, node: KnowledgeNode) -> int:
        if getattr(node, "outgoing", None) not in (None,):
            # If outgoing was explicitly set, use it
            if node.outgoing is not None:
                return node.outgoing

        # Fallback: derive from actual connections
        return len(getattr(node, "connections", []))

    def classify_gap(self, node: KnowledgeNode) -> Dict:
        incoming = self._incoming_count(node)
        outgoing = self._outgoing_count(node)

        if incoming > 0 and outgoing == 0 and node.id in INTENTIONAL_TERMINALS:
            return {
                "gap_type": "intentional_terminal",
                "reason": f"node '{node.id}' receives {incoming} incoming edge(s) and is allowed to terminate flow by design",
                "gap_score": 0.2,
            }

        if incoming == 0 and outgoing == 0:
            return {
                "gap_type": "isolated",
                "reason": f"node '{node.id}' has zero incoming and zero outgoing connections in current graph wiring",
                "gap_score": 1.0,
            }

        if incoming > 0 and outgoing == 0:
            return {
                "gap_type": "structural_sink",
                "reason": f"node '{node.id}' receives {incoming} incoming edge(s) but emits none — likely missing propagation structure",
                "gap_score": 1.0,
            }

        if incoming == 0 and outgoing > 0:
            return {
                "gap_type": "structural_source",
                "reason": f"node '{node.id}' emits {outgoing} outgoing edge(s) but receives none — may lack grounding",
                "gap_score": 0.6,
            }

        return {
            "gap_type": "balanced",
            "reason": f"node '{node.id}' has both incoming and outgoing connections",
            "gap_score": 0.0,
        }

    def find_gaps(self) -> List[Dict]:
        gaps = []

        for node in self.nodes:
            classification = self.classify_gap(node)

            if classification["gap_score"] > 0:
                gaps.append(
                    {
                        "node": node,
                        "gap_type": classification["gap_type"],
                        "reason": classification["reason"],
                        "gap_score": classification["gap_score"],
                    }
                )

        return sorted(gaps, key=lambda x: x["gap_score"], reverse=True)

    def generate_hypothesis(self, gap: Dict) -> Dict:
        node = gap["node"]

        return {
            "target": node.id,
            "gap_type": gap["gap_type"],
            "reason": gap["reason"],
            "gap_score": gap["gap_score"],
            "proposal": f"Explore missing connections for '{node.id}'",
            "suggestions": [
                f"Link '{node.id}' to adjacent domains",
                "Search for analogous structures in other fields",
                "Generate tool or model to bridge domain gap",
            ],
        }

    def step(self) -> Dict | None:
        gaps = self.find_gaps()

        if not gaps:
            return None

        selected = gaps[0]
        hypothesis = self.generate_hypothesis(selected)
        self.history.append(hypothesis)
        return hypothesis
