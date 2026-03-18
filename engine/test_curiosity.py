# test_curiosity.py

from curiosity_engine import CuriosityEngine, KnowledgeNode

# Fake starter graph
nodes = [
    KnowledgeNode("time_crystal", "physics", []),
    KnowledgeNode("music_theory", "music", []),
    KnowledgeNode("signal_processing", "engineering", [])
]

engine = CuriosityEngine(nodes)

result = engine.step()

print(result)
