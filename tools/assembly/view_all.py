import sys, json
import numpy as np
from spotgeo import load
from show import render
P = load()
W = {k: np.array(v).reshape(4,4) for k, v in json.load(open('placements.json')).items()}
def color(k):
    if k.startswith('motor'): return (0.22,0.22,0.27)
    if k.startswith('Bearing'): return (0.85,0.85,0.9)
    if 'arm_cover' in k: return (0.92,0.75,0.25)
    if 'arm_st' in k: return (0.85,0.38,0.27)
    if 'wrist' in k: return (0.27,0.55,0.85)
    if 'foot' in k: return (0.3,0.62,0.3)
    if 'reinforcement' in k: return (0.6,0.42,0.8)
    if 'arm_joint' in k: return (0.85,0.6,0.3)
    return (0.75,0.75,0.75)
skip = set(sys.argv[3].split(',')) if len(sys.argv) > 3 else set()
items = [(P[k], W[k], color(k)) for k in P if not any(s in k for s in skip)]
views = sys.argv[1].split(',') if len(sys.argv) > 1 else ["iso","-X","+Y","+Z"]
name = sys.argv[2] if len(sys.argv) > 2 else "all"
print(render(items, views=views, out=f"ALL_{name}.png", size=(640,560), title=f"auto assembly ({name})"))
