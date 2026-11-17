import json, sys
import numpy as np
from spotgeo import load
from collide import check, report
# check_all.py [κατώφλι mm] [--as-built]
#   --as-built: θέσεις όπως είναι μέσα στη γεωμετρία που φορτώθηκε (SPOT_GEO_BUILD), όχι από το placements.json
args = [a for a in sys.argv[1:] if not a.startswith('--')]
P = load()
if '--as-built' in sys.argv:
    W = {k: p.M for k, p in P.items()}
else:
    W = {k: np.array(v).reshape(4,4) for k, v in json.load(open('placements.json')).items()}
res = check(P, W, list(P.keys()), "all", depth=False)
json.dump(res, open('collisions.json','w'), indent=1, ensure_ascii=False)
thr = float(args[0]) if args else 0.6
bad = [r for r in res if r['n'] and r.get('depth_p90',0) > thr and 'Bearing' not in r['a']+r['b']]
print(len([r for r in res if r['n']]), 'touching pairs;', len(bad), f'with p90 depth > {thr} mm (bearings excluded):')
for r in sorted(bad, key=lambda r: -r['depth_p90']):
    print(f"  {r['a'][:38]:38s} x {r['b'][:38]:38s} p90={r['depth_p90']:5.2f} max={r['depth_max']:5.2f}")
