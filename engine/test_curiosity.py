from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from curiosity_engine import CuriosityEngine, KnowledgeNode

nodes = [
    KnowledgeNode("time_crystal", "physics", []),
    KnowledgeNode("music_theory", "music", []),
    KnowledgeNode("signal_processing", "engineering", []),
]

engine = CuriosityEngine(nodes)
result = engine.step()
print(result)
