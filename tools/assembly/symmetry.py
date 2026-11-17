import numpy as np
from scipy.spatial import cKDTree


def sample_surface(V, F, n=40000, seed=0):
    rng = np.random.default_rng(seed)
    a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    area = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)
    idx = rng.choice(len(F), n, p=area / area.sum())
    u, v = rng.random(n), rng.random(n)
    m = u + v > 1
    u[m], v[m] = 1 - u[m], 1 - v[m]
    return a[idx] + u[:, None] * (b[idx] - a[idx]) + v[:, None] * (c[idx] - a[idx])


def mirror_error(V, F, axis, center=None, n=40000):
    """Απόκλιση (mm, διάμεσος/95%) αν καθρεφτίσουμε το κομμάτι ως προς το επίπεδο x[axis]=center."""
    S = sample_surface(V, F, n)
    c = (V[:, axis].min() + V[:, axis].max()) / 2 if center is None else center
    M = S.copy()
    M[:, axis] = 2 * c - M[:, axis]
    d, _ = cKDTree(S).query(M)
    return np.median(d), np.percentile(d, 95), c


def best_mirror_center(V, F, axis, n=20000):
    """Βρίσκει το κέντρο συμμετρίας που ελαχιστοποιεί την απόκλιση (γύρω από το κέντρο του bbox)."""
    S = sample_surface(V, F, n)
    T = cKDTree(S)
    c0 = (V[:, axis].min() + V[:, axis].max()) / 2
    best = None
    for c in np.arange(c0 - 3, c0 + 3.01, 0.1):
        M = S.copy()
        M[:, axis] = 2 * c - M[:, axis]
        d, _ = T.query(M)
        e = np.percentile(d, 90)
        if best is None or e < best[0]:
            best = (e, c, np.median(d))
    return best
