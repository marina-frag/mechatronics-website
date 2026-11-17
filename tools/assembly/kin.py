"""Μετασχηματισμοί και τα «σημεία σύνδεσης» (mounts) των κομματιών του Spot.

Όλες οι τιμές είναι σε τοπικές συντεταγμένες κάθε κομματιού (mm), όπως βγήκαν από την ανίχνευση τρυπών
(features.py) και τα αρχεία της ομάδας (ST3020 versions/*.FCStd).
"""
import numpy as np

# --- Servo ST3020 (πλαίσιο του motor STL = SCS15_ASM_87 στα αρχεία της ομάδας) ---
SHAFT = np.array([-3.1, 10.13])   # άξονας εξόδου (x, y), κατά +z
Z_BOSS_TIP = 13.6                 # άκρη του κάτω πείρου (r=3, z 13.6..17.5)
Z_BOSS_BASE = 17.5
Z_CASE_BOT = 19.5                 # κάτω πλευρά κελύφους
Z_CASE_TOP = 59.5                 # πάνω πλευρά κελύφους
Z_HUB = (61.5, 63.5)              # πλήμνη κόρνας (r=4.5)
Z_HORN = (63.5, 66.0)             # δίσκος κόρνας (r=10)
CORNER_CENTER = np.array([-3.1, 0.13])  # κέντρο των 4 γωνιακών οπών


def T(R=None, t=None):
    M = np.eye(4)
    if R is not None:
        M[:3, :3] = R
    if t is not None:
        M[:3, 3] = t
    return M


def inv(M):
    R = M[:3, :3]
    return T(R.T, -R.T @ M[:3, 3])


def apply(M, p):
    return M[:3, :3] @ np.asarray(p, float) + M[:3, 3]


def rot_cols(x, y, z):
    R = np.column_stack([x, y, z]).astype(float)
    assert abs(np.linalg.det(R) - 1) < 1e-6, R
    return R


def motor_frame(q, d, u, z_m):
    """Θέση servo σε πλαίσιο κομματιού: το σημείο του άξονα με z=z_m πάει στο q, ο άξονας (σώμα→κόρνα) στο d,
    η διεύθυνση +y του servo (από το κέντρο των οπών προς τον άξονα) στο u."""
    d = np.asarray(d, float)
    u = np.asarray(u, float)
    x = np.cross(u, d)
    R = rot_cols(x, u, d)
    t = np.asarray(q, float) - R @ np.array([SHAFT[0], SHAFT[1], z_m])
    return T(R, t)


def rot_about(axis_point, axis_dir, angle_deg):
    """Στροφή γύρω από ευθεία (σημείο, διεύθυνση)."""
    a = np.asarray(axis_dir, float)
    a = a / np.linalg.norm(a)
    th = np.radians(angle_deg)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    R = np.eye(3) + np.sin(th) * K + (1 - np.cos(th)) * K @ K
    p = np.asarray(axis_point, float)
    return T(R, p - R @ p)


def mirror_plane(point, normal):
    n = np.asarray(normal, float)
    n = n / np.linalg.norm(n)
    S = np.eye(4)
    S[:3, :3] = np.eye(3) - 2 * np.outer(n, n)
    S[:3, 3] = 2 * (np.asarray(point, float) @ n) * n
    return S


def snap_rotation(M, tol=1e-3):
    R = M[:3, :3]
    Rs = np.round(R)
    if np.abs(R - Rs).max() < tol:
        M = M.copy()
        M[:3, :3] = Rs
    return M


# --- Mounts ανά κομμάτι (τοπικά) ---
MOUNTS = {
    # arm_joint: θήκη servo ώμου στο τοίχωμα -Y (y 4.9..7.4), οπή άξονα r=7 στο (9.9, 18.1)
    "aj_servo": dict(q=[9.9, 7.4, 18.1], d=[0, -1, 0], u=[0, 0, -1], z_m=Z_CASE_TOP),
    # arm_joint: διεπαφή κόρνας ισχίου στην όψη +X (πλάκα x 35.4..37.4, εσοχή προς -X)
    "aj_hip": dict(axis_p=[35.4, 25.75, 28.25], d=[-1, 0, 0]),
    # O_shoulder: διεπαφές κόρνας (πλάκα y 0..2, κόρνα προς +Y)
    "os_iface": [dict(axis_p=[16.0, 1.93, 26.0], d=[0, 1, 0]), dict(axis_p=[94.0, 1.93, 26.0], d=[0, 1, 0])],
    # I_shoulder: έδρες ρουλεμάν r=9.6, y -0.1..4.9
    "is_seat": [dict(axis_p=[16.0, -0.1, 26.0], n_in=[0, 1, 0]), dict(axis_p=[94.0, -0.1, 26.0], n_in=[0, 1, 0])],
    # κάλυμμα μηρού (L): servo ισχίου (θέση από το αρχείο της ομάδας, επαληθευμένη με τις 4 γωνιακές οπές)
    "cover_hip": dict(q=[26.32, 29.9, 22.72], d=[0, -1, 0], u=[0, 0, -1], z_m=Z_CASE_BOT),
    # κάλυμμα μηρού (L): έδρα ρουλεμάν γονάτου r=9.63 στο (12.5, ·, 131), y 39.9..44.9
    "cover_knee_seat": dict(axis_p=[12.5, 44.9, 131.0], n_in=[0, -1, 0]),
    # arm (L): διεπαφή κόρνας γονάτου (εσοχή r=10.25 στην όψη -Y, πλάκα y -8.6..-6.1)
    "arm_knee": dict(axis_p=[-3.8, -8.6, 116.9], d=[0, -1, 0]),
    # wrist (L): θήκη servo γονάτου, τοίχωμα -Y (y -42.6..-40.1), γωνιακές οπές x{2.9,37.9} z{2.6,17.4}
    "wrist_servo": dict(q=[10.4, -40.1, 10.0], d=[0, -1, 0], u=[-1, 0, 0], z_m=Z_CASE_TOP),
}

# θέση arm ως προς κάλυμμα (ίδιος προσανατολισμός)· από τη συναρμολόγηση της ομάδας, με το γόνατο ομοαξονικό
ARM_IN_COVER = np.array([16.3, 0.0, 14.1])
# πέλμα ως προς wrist (L): μέσος όρος των τριών ποδιών της ομάδας, κατά Y στο άνοιγμα της οπής
FOOT_IN_WRIST_R = np.array([[0, 0, -1], [0, 1, 0], [1, 0, 0]], float)
FOOT_IN_WRIST_T = np.array([127.82, -30.1, 11.07])
# ενίσχυση ώμου (L): γραμμές (σημείο, διεύθυνση) για ομοαξονικότητα
REINF_LINES = {
    "ring": ([14.1, 71.65, 23.4], [0, 1, 0]),
    "zhole": ([37.9, 5.4, 2.0], [0, 0, 1]),
    "xhole": ([43.0, 5.3, 32.4], [1, 0, 0]),
}
AJ_LINES = {
    "zhole": ([22.75, 16.75, 3.0], [0, 0, 1]),
    "yhole": ([22.8, 39.0, 4.5], [0, 1, 0]),
}
REINF_RING_Y = (68.9, 74.4)
