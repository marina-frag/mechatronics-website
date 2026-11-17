import json, os, subprocess, tempfile
import numpy as np
from show import SCRATCH, HERE
from spotgeo import BUILD


def check(P, W, labels, pairs="all", depth=True):
    parts = {k: {"geom": P[k].geom, "matrix": [float(x) for x in np.asarray(W[k]).ravel()]} for k in labels}
    tmp = tempfile.mkdtemp(dir=SCRATCH)
    sp, op = os.path.join(tmp, "spec.json"), os.path.join(tmp, "out.json")
    json.dump({"build": BUILD, "parts": parts, "pairs": pairs, "depth": depth}, open(sp, "w"))
    r = subprocess.run(["blender", "-b", "--factory-startup", "-P", os.path.join(HERE, "blender_collide.py"), "--", sp, op],
                       capture_output=True, text=True)
    if not os.path.exists(op):
        raise RuntimeError(r.stdout[-3000:] + r.stderr[-3000:])
    return json.load(open(op))


def report(res, only_hits=True):
    for r in res:
        if r["n"] or not only_hits:
            fs = r.get("free_shift_b", {})
            best = min(((v, k) for k, v in fs.items() if v != ">6"), default=None)
            print(f"  {r['a'][:30]:30s} x {r['b'][:30]:30s} tris={r['n']:5d} inside={r.get('n_inside',0):4d} depth max={r.get('depth_max',0):5.2f} p90={r.get('depth_p90',0):5.2f} free(b)={best}")
