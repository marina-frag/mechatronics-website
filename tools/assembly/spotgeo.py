"""Φόρτωση της γεωμετρίας του Spot από την εξαγωγή του pipeline (manifest.json + geometry.bin).

Κάθε κομμάτι δίνει: τοπικές κορυφές V (mm), τρίγωνα F και τη θέση του M (4x4) στη συναρμολόγηση.
Χρησιμοποιείται από τα εργαλεία ανάλυσης/συναρμολόγησης σε αυτόν τον φάκελο.
"""
import json
import os

import numpy as np

BUILD = os.environ.get("SPOT_GEO_BUILD", "/home/marina-fragkouli/mechatronics_web/pipeline/build/probe")


class Part:
    def __init__(self, label, name, geom, V, F, M):
        self.label, self.name, self.geom = label, name, geom
        self.V, self.F, self.M = V, F, M

    def world(self, M=None):
        M = self.M if M is None else M
        return self.V @ M[:3, :3].T + M[:3, 3]

    def __repr__(self):
        return f"Part({self.label}, {len(self.V)}v)"


def load(build=BUILD):
    m = json.load(open(os.path.join(build, "manifest.json")))
    blob = np.fromfile(os.path.join(build, "geometry.bin"), dtype=np.uint8)
    geo = {}
    for gid, g in m["geometries"].items():
        Vs, Fs, off = [], [], 0
        for s in g["submeshes"]:
            v = np.frombuffer(blob, "<f4", s["v_count"] * 3, s["v_off"]).reshape(-1, 3).astype(np.float64)
            f = np.frombuffer(blob, "<u4", s["t_count"] * 3, s["i_off"]).reshape(-1, 3).astype(np.int64)
            Vs.append(v)
            Fs.append(f + off)
            off += len(v)
        geo[gid] = (np.vstack(Vs), np.vstack(Fs))
    parts = {}
    for c in m["components"]:
        V, F = geo[c["geometry"]]
        M = np.array(c["matrix"], dtype=np.float64).reshape(4, 4)
        parts[c["label"]] = Part(c["label"], c["name"], c["geometry"], V, F, M)
    return parts


def face_normals(V, F):
    n = np.cross(V[F[:, 1]] - V[F[:, 0]], V[F[:, 2]] - V[F[:, 0]])
    a = np.linalg.norm(n, axis=1)
    return n / np.maximum(a, 1e-12)[:, None], a / 2


def rot_matrices_24():
    """Οι 24 στροφές που απεικονίζουν άξονες σε άξονες."""
    out = []
    import itertools
    for perm in itertools.permutations(range(3)):
        for signs in itertools.product((1, -1), repeat=3):
            R = np.zeros((3, 3))
            for i, (p, s) in enumerate(zip(perm, signs)):
                R[i, p] = s
            if np.linalg.det(R) > 0:
                out.append(R)
    return out
