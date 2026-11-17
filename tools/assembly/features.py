"""Ανίχνευση κυλινδρικών τρυπών/πείρων σε τριγωνικά πλέγματα με τομές κάθετες στους τοπικούς άξονες.

Για κάθε άξονα (X, Y, Z του κομματιού) κόβουμε το πλέγμα σε επίπεδα ανά `step` mm, ενώνουμε τα
τμήματα σε κλειστούς βρόχους και κρατάμε όσους είναι κύκλοι. Κύκλοι με ίδιο κέντρο/ακτίνα σε
διαδοχικά ύψη γίνονται ένας κύλινδρος [h0, h1].
Τύπος: 'hole' (το υλικό είναι έξω από τον κύκλο) ή 'boss' (το υλικό είναι μέσα).
"""
import json
import os

import numpy as np

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")


def slice_loops(V, F, axis, h, N=None):
    """Βρόχοι τομής του πλέγματος με το επίπεδο x[axis] = h, με φορά ώστε το υλικό να είναι αριστερά
    (εξωτερικοί βρόχοι CCW όταν κοιτάμε από +axis). Επιστρέφει λίστα πινάκων 2D."""
    d = V[:, axis] - h
    s = d[F] > 0
    cnt = s.sum(1)
    tri = np.where((cnt == 1) | (cnt == 2))[0]
    if len(tri) == 0:
        return []
    o = [i for i in range(3) if i != axis]
    T = F[tri]
    S = s[tri]
    e = np.zeros(3)
    e[axis] = 1
    if N is None:
        N = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    tdir = np.cross(e, N[tri])
    # οι δύο ακμές που τέμνονται σε κάθε τρίγωνο
    E = np.stack([T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]], 1)  # (k,3,2)
    SE = np.stack([S[:, 0] != S[:, 1], S[:, 1] != S[:, 2], S[:, 2] != S[:, 0]], 1)
    idx = np.argsort(~SE, axis=1, kind="stable")[:, :2]
    kk = np.arange(len(tri))[:, None]
    EE = E[kk, idx]  # (k,2,2)
    ia, ib = EE[..., 0], EE[..., 1]
    w = d[ia] / (d[ia] - d[ib])
    Pt = V[ia] + w[..., None] * (V[ib] - V[ia])  # (k,2,3)
    flip = np.einsum("ij,ij->i", Pt[:, 1] - Pt[:, 0], tdir) < 0
    lo = np.minimum(ia, ib)
    hi = np.maximum(ia, ib)
    keys = lo.astype(np.int64) * 10_000_000 + hi
    a_key = np.where(flip, keys[:, 1], keys[:, 0])
    b_key = np.where(flip, keys[:, 0], keys[:, 1])
    a_pt = np.where(flip[:, None], Pt[:, 1], Pt[:, 0])
    segs = dict(zip(a_key.tolist(), b_key.tolist()))
    pts = dict(zip(a_key.tolist(), a_pt[:, o].tolist()))
    loops = []
    seen = set()
    for k0 in segs:
        if k0 in seen:
            continue
        loop = []
        k = k0
        while k is not None and k not in seen:
            seen.add(k)
            loop.append(k)
            k = segs.get(k)
        if k == k0 and len(loop) >= 5:
            loops.append(np.array([pts[x] for x in loop]))
    return loops


def fit_circle(p):
    A = np.c_[2 * p, np.ones(len(p))]
    b = (p ** 2).sum(1)
    sol, *_ = np.linalg.lstsq(A, b, rcond=None)
    c = sol[:2]
    r = np.sqrt(max(sol[2] + c @ c, 0))
    res = np.abs(np.linalg.norm(p - c, axis=1) - r)
    # κάλυψη γωνίας
    ang = np.sort(np.arctan2(p[:, 1] - c[1], p[:, 0] - c[0]))
    gap = np.max(np.diff(np.r_[ang, ang[0] + 2 * np.pi]))
    return c, r, res.max(), gap


def signed_area(p):
    x, y = p[:, 0], p[:, 1]
    return 0.5 * np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)


def cylinders(V, F, step=0.5, rmin=0.9, rmax=16.0, tol=0.12):
    out = []
    N = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    for axis in range(3):
        lo, hi = V[:, axis].min(), V[:, axis].max()
        hs = np.arange(lo + step * 0.37, hi, step)
        circ = []  # (h, cx, cy, r, kind)
        for h in hs:
            for p in slice_loops(V, F, axis, h, N):
                c, r, err, gap = fit_circle(p)
                if not (rmin <= r <= rmax) or err > max(tol * r, 0.08) or gap > 1.4:
                    continue
                A = signed_area(p)
                # κύκλος: με εξωτερικές κάθετες ο εξωτ. βρόχος είναι CCW (A>0) → boss, CW → hole
                # ο άξονας των 2D συντεταγμένων (o0,o1) για axis=1 είναι (x,z): αντιστροφή φοράς
                sign = -1 if axis == 1 else 1
                kind = "boss" if A * sign > 0 else "hole"
                circ.append((h, c[0], c[1], r, kind))
        # ομαδοποίηση σε κυλίνδρους
        circ.sort()
        groups = []
        for h, cx, cy, r, kind in circ:
            for g in groups:
                if g["kind"] == kind and abs(g["r"] - r) < 0.35 and np.hypot(g["c"][0] - cx, g["c"][1] - cy) < 0.4 \
                        and h - g["h1"] <= step * 1.6:
                    n = g["n"]
                    g["c"] = [(g["c"][0] * n + cx) / (n + 1), (g["c"][1] * n + cy) / (n + 1)]
                    g["r"] = (g["r"] * n + r) / (n + 1)
                    g["h1"] = h
                    g["n"] = n + 1
                    break
            else:
                groups.append({"axis": axis, "c": [cx, cy], "r": r, "h0": h, "h1": h, "n": 1, "kind": kind})
        for g in groups:
            o = [i for i in range(3) if i != axis]
            p0 = np.zeros(3)
            p0[o[0]], p0[o[1]] = g["c"]
            p0[axis] = g["h0"] - step / 2
            p1 = p0.copy()
            p1[axis] = g["h1"] + step / 2
            out.append({"axis": axis, "p0": p0.tolist(), "p1": p1.tolist(), "r": round(g["r"], 3), "kind": g["kind"],
                        "len": round(p1[axis] - p0[axis], 2)})
    return out


def part_cylinders(part, step=0.5):
    os.makedirs(CACHE, exist_ok=True)
    f = os.path.join(CACHE, f"cyl_{part.geom}_{step}.json")
    if os.path.exists(f):
        return json.load(open(f))
    cyl = cylinders(part.V, part.F, step=step)
    json.dump(cyl, open(f, "w"))
    return cyl


def world_cyl(c, M):
    """Κύλινδρος σε συντεταγμένες κόσμου: (p0, p1, άξονας μοναδιαίος, r)."""
    p0 = M[:3, :3] @ np.array(c["p0"]) + M[:3, 3]
    p1 = M[:3, :3] @ np.array(c["p1"]) + M[:3, 3]
    a = p1 - p0
    a /= np.linalg.norm(a)
    return p0, p1, a, c["r"]
