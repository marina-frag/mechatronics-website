"""Αναφορά ευθυγράμμισης τρυπών μεταξύ κομματιών (στην τρέχουσα θέση τους)."""
import itertools
import numpy as np
from spotgeo import load
from features import part_cylinders, world_cyl


def world_feats(P, labels, W=None):
    out = {}
    for k in labels:
        M = (W or {}).get(k, P[k].M)
        out[k] = [(c, *world_cyl(c, M)) for c in part_cylinders(P[k]) if c["len"] >= 0.9]
    return out


def pair_report(F, a, b, maxd=3.0, show=True):
    rows = []
    for (ca, p0a, p1a, ua, ra) in F[a]:
        for (cb, p0b, p1b, ub, rb) in F[b]:
            if abs(abs(ua @ ub) - 1) > 1e-3:
                continue
            # απόσταση αξόνων
            w = p0b - p0a
            perp = w - (w @ ua) * ua
            d = np.linalg.norm(perp)
            if d > maxd:
                continue
            # επικάλυψη κατά μήκος ή κοντινή απόσταση
            ta = sorted([0, (p1a - p0a) @ ua])
            tb = sorted([(p0b - p0a) @ ua, (p1b - p0a) @ ua])
            gap = max(tb[0] - ta[1], ta[0] - tb[1], 0)
            if gap > 12:
                continue
            rows.append((d, ca["r"], cb["r"], gap, perp, p0a, ua))
    rows.sort(key=lambda r: r[0])
    if show:
        for d, ra, rb, gap, perp, p0a, ua in rows:
            print(f"   {a[:22]:22s} r{ra:5.2f} ~ {b[:22]:22s} r{rb:5.2f}  off={d:5.2f} vec={np.round(perp,2)} gap={gap:4.1f} axis={np.round(ua,2)} at {np.round(p0a,1)}")
    return rows


if __name__ == "__main__":
    import sys
    P = load()
    labels = sys.argv[1:]
    F = world_feats(P, labels)
    for a, b in itertools.combinations(labels, 2):
        pair_report(F, a, b)
