"""Blender (headless): έλεγχος συγκρούσεων με BVH.

blender -b --factory-startup -P blender_collide.py -- spec.json out.json
spec: {"build": dir, "parts": {label: {"geom", "matrix"[16]}}, "pairs": [[a, b], ...] ή "all"}
Για κάθε ζεύγος: πόσα τρίγωνα τέμνονται και το bbox της περιοχής τομής (mm).
Μετρά επίσης το βάθος: πόσο πρέπει να μετακινηθεί το b κατά ±X/±Y/±Z ώστε να μη τέμνεται (έως 6 mm).
"""
import json
import os
import sys

import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index("--") + 1:]
spec = json.load(open(argv[0]))
build = spec["build"]
man = json.load(open(os.path.join(build, "manifest.json")))
blob = np.fromfile(os.path.join(build, "geometry.bin"), dtype=np.uint8)
geo = {}


def get_geo(gid):
    if gid not in geo:
        g = man["geometries"][gid]
        Vs, Fs, off = [], [], 0
        for s in g["submeshes"]:
            v = np.frombuffer(blob, "<f4", s["v_count"] * 3, s["v_off"]).reshape(-1, 3).astype(np.float64)
            f = np.frombuffer(blob, "<u4", s["t_count"] * 3, s["i_off"]).reshape(-1, 3).astype(np.int64)
            Vs.append(v)
            Fs.append(f + off)
            off += len(v)
        geo[gid] = (np.vstack(Vs), np.vstack(Fs))
    return geo[gid]


def world(label, offset=None):
    p = spec["parts"][label]
    V, F = get_geo(p["geom"])
    M = np.array(p["matrix"]).reshape(4, 4)
    W = V @ M[:3, :3].T + M[:3, 3]
    if offset is not None:
        W = W + offset
    return W, F


trees = {}


def tree(label, offset=None):
    if offset is None and label in trees:
        return trees[label]
    W, F = world(label, offset)
    t = BVHTree.FromPolygons([tuple(v) for v in W], [tuple(f) for f in F], all_triangles=True, epsilon=0.0)
    if offset is None:
        trees[label] = (t, W, F)
        return trees[label]
    return (t, W, F)


labels = list(spec["parts"].keys())
pairs = spec["pairs"]
if pairs == "all":
    # μόνο ζεύγη με επικαλυπτόμενα bbox
    bbs = {}
    for k in labels:
        W, F = world(k)
        bbs[k] = (W.min(0), W.max(0))
    pairs = []
    for i, a in enumerate(labels):
        for b in labels[i + 1:]:
            (a0, a1), (b0, b1) = bbs[a], bbs[b]
            if np.all(a0 <= b1 + 0.5) and np.all(b0 <= a1 + 0.5):
                pairs.append([a, b])

out = []
dirs = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
for a, b in pairs:
    ta, Wa, Fa = tree(a)
    tb, Wb, Fb = tree(b)
    hits = ta.overlap(tb)
    rec = {"a": a, "b": b, "n": len(hits)}
    if hits:
        ia = np.array([h[0] for h in hits])
        P = Wa[Fa[ia]].reshape(-1, 3)
        rec["bbox"] = [P.min(0).round(2).tolist(), P.max(0).round(2).tolist()]
        # βάθος διείσδυσης: κορυφές του ενός μέσα στο άλλο (ισοτιμία ακτίνων) και απόσταση από την επιφάνεια
        def inside_depths(tA, WB):
            dirv = Vector((0.5773, 0.5774, 0.5775))
            deps = []
            for v in WB:
                o = Vector(v)
                cnt, cur = 0, o
                for _ in range(64):
                    hit = tA.ray_cast(cur, dirv)
                    if hit[0] is None:
                        break
                    cnt += 1
                    cur = hit[0] + dirv * 1e-4
                if cnt % 2 == 1:
                    nn = tA.find_nearest(o)
                    deps.append(nn[3])
            return deps
        # μόνο κορυφές κοντά στην περιοχή τομής
        lo = np.array(rec["bbox"][0]) - 1
        hi = np.array(rec["bbox"][1]) + 1
        sb = Wb[np.all((Wb >= lo) & (Wb <= hi), axis=1)]
        sa = Wa[np.all((Wa >= lo) & (Wa <= hi), axis=1)]
        dB = inside_depths(ta, sb[:4000])
        dA = inside_depths(tb, sa[:4000])
        dd = dB + dA
        rec["depth_max"] = round(max(dd), 2) if dd else 0.0
        rec["depth_p90"] = round(float(np.percentile(dd, 90)), 2) if dd else 0.0
        rec["n_inside"] = len(dd)
        if spec.get("depth"):
            dep = {}
            for d in dirs:
                lo, hi = 0.0, 6.0
                tb2 = tree(b, np.array(d) * hi)[0]
                if ta.overlap(tb2):
                    dep[str(d)] = ">6"
                    continue
                for _ in range(10):
                    mid = (lo + hi) / 2
                    if ta.overlap(tree(b, np.array(d) * mid)[0]):
                        lo = mid
                    else:
                        hi = mid
                dep[str(d)] = round(hi, 2)
            rec["free_shift_b"] = dep
    out.append(rec)
json.dump(out, open(argv[1], "w"), indent=1)
print("[collide] pairs", len(pairs), "colliding", sum(1 for r in out if r["n"]))
