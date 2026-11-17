"""Αυτόματη συναρμολόγηση του Spot από τις συνδέσεις των servo (βλ. kin.MOUNTS).

Σύμβαση (όπως στο αρχείο της ομάδας): μπροστά = -X (F_cover, O_shoulder_F), πάνω = +Z,
αριστερά πόδια (L) στην πλευρά +Y. Στάση: γόνατα λυγισμένα προς τα πίσω (όπως στο Spot), πέλμα κάτω από το ισχίο.

Έξοδος: placements.json  {label: 4x4 (row-major, mm)}  για όλα τα 59 κομμάτια,
        renames.json     {παλιό label: νέο},
        mirrors.json     {label: επίπεδο}: κομμάτια που στο auto αρχείο γίνονται κατοπτρικά (R_arm_joint).
"""
import json
import os
import sys

import numpy as np

from kin import (AJ_LINES, ARM_IN_COVER, FOOT_IN_WRIST_R, FOOT_IN_WRIST_T, MOUNTS, REINF_LINES, REINF_RING_Y, SHAFT,
                 Z_HORN, T, apply, inv, mirror_plane, motor_frame, rot_about, rot_cols)
from spotgeo import load

HERE = os.path.dirname(os.path.abspath(__file__))
R_ARM_INWARD = 1.0
KNEE_WRIST_GAP = 0.7   # μισό από την επικάλυψη 1.4 mm: μοιράζεται ανάμεσα σε arm και servo
# Στάση ποδιών (μοίρες, γύρω από +Y). Το γόνατο λυγίζει προς τα πίσω έως ~65° πριν η κνήμη χτυπήσει
# στον μηρό· 60° με ισχίο -27.5° φέρνει το πέλμα ακριβώς κάτω από τον άξονα του ισχίου.
KNEE_DEG = 60.0
HIP_DEG = -27.5

LEG_PARTS = {
    # ρόλος: (μοτίβο label για L πόδι, για R πόδι)
    "arm": ("L_arm_st_Leg{}", "R_arm_st_Leg{}"),
    "cover": ("L_arm_cover_for_shoulder_reinforcement_st_Leg{}", "R_arm_cover_for_shoulder_reinforcement_st_Leg{}"),
    "wrist": ("L_wrist_st_Leg{}", "R_wrist_st_Leg{}"),
    "reinf": ("L_shoulder_reinforcement_st_Leg{}", "R_shoulder_reinforcement_Leg{}"),  # βλ. REINF_SIDE
    "aj": ("arm_joint_for_shoulder_reinforcement_st_Leg{}",) * 2,
    "foot": ("foot_Leg{}",) * 2,
}


def body_corrections(P, W):
    """Συμμετρία σώματος: όλα τα συμμετρικά κομμάτια κεντραρισμένα στο μέσο επίπεδο Y_c,
    ομοαξονικοί ώμοι (O_shoulder ↔ I_shoulder), O_shoulder σε επαφή με το I_shoulder, κοινό ύψος αξόνων."""
    log = []
    # μέσο επίπεδο από τις πλαϊνές πλάκες (τοπικό x=0 της καθεμιάς)
    yL = apply(W["non-mega_L_side_plate"], [0, 0, 0])[1]
    yR = apply(W["non_mega_R_side_plate"], [0, 0, 0])[1]
    yc = (yL + yR) / 2
    log.append(f"μέσο επίπεδο σώματος Y_c = {yc:.3f}")

    def shift(label, d):
        if np.linalg.norm(d) > 1e-6:
            W[label] = W[label].copy()
            W[label][:3, 3] += d
            log.append(f"  {label}: μετακίνηση {np.round(d, 2).tolist()} mm")

    # τοπικά σημεία που πρέπει να είναι στο Y_c
    centers = {
        "plate": [55.0, 3.5, 42.4],
        "non-mega_T_cover": [120.0, 106.75, 57.0],
        "non-mega_B_cover": [120.0, 21.25, 57.0],
        "F_cover_st": [33.0, 57.0, 5.1],
        "B_cover_st": [33.0, 57.0, 5.1],
    }
    for k, c in centers.items():
        y = apply(W[k], c)[1]
        shift(k, np.array([0, yc - y, 0]))
    # πλαϊνές πλάκες: συμμετρικά ως προς Y_c (ήδη ορίζουν το Y_c), ίδιο ύψος
    zL = apply(W["non-mega_L_side_plate"], [0, 0, 9.5])[2]
    zR = apply(W["non_mega_R_side_plate"], [0, 0, 90.5])[2]
    zs = (zL + zR) / 2
    shift("non-mega_L_side_plate", np.array([0, 0, zs - zL]))
    shift("non_mega_R_side_plate", np.array([0, 0, zs - zR]))

    # ώμοι: άξονες στα Y_c ± 39, κοινό Z
    pairs = [("O_shoulder_st_F", "I_shoulder_st_B"), ("O_shoulder_st_B", "I_shoulder_st_F")]
    zs_axis = []
    for o, i in pairs:
        zs_axis += [apply(W[o], [55, 0, 26])[2], apply(W[i], [55, 0, 26])[2]]
    z_axis = float(np.mean(zs_axis))
    log.append(f"κοινό ύψος αξόνων ώμου Z = {z_axis:.3f}")
    for o, i in pairs:
        # I_shoulder: κέντρο έδρας στο (·, Y_c, z_axis)
        ci = apply(W[i], [55, 0, 26])
        shift(i, np.array([0, yc - ci[1], z_axis - ci[2]]))
        co = apply(W[o], [55, 0, 26])
        d = np.array([0, yc - co[1], z_axis - co[2]])
        # επαφή: εσωτερική όψη O (τοπ. y=0) πάνω στην εξωτερική όψη I (τοπ. y=52.5)
        xo = apply(W[o], [55, 0, 26])[0]
        xi = apply(W[i], [55, 52.5, 26])[0]
        d[0] = xi - xo
        shift(o, d)
    return yc, z_axis, log


def leg_FL(P, W, corner="FL"):
    """Χτίζει το μπροστινό αριστερό πόδι από τις συνδέσεις. Επιστρέφει {ρόλος: 4x4}."""
    L = {}
    Os, Is = W["O_shoulder_st_F"], W["I_shoulder_st_B"]
    # η διεπαφή του FL είναι αυτή με το μεγαλύτερο Y (αριστερά = +Y)
    ifs = MOUNTS["os_iface"]
    k = int(np.argmax([apply(Os, m["axis_p"])[1] for m in ifs]))
    iface = ifs[k]
    q_w = apply(Os, iface["axis_p"])
    d_w = Os[:3, :3] @ np.array(iface["d"], float)  # κόρνα προς τα έξω (μπροστά)

    # arm_joint: τοπ. +Y → -d_w (προς τα μέσα), τοπ. +X → έξω (+Y), τοπ. Z = X × Y
    ax_y = -d_w
    ax_x = np.array([0, 1.0, 0])
    R_aj = rot_cols(ax_x, ax_y, np.cross(ax_x, ax_y))
    T_aj_m1 = motor_frame(**MOUNTS["aj_servo"])
    R_m1 = R_aj @ T_aj_m1[:3, :3]
    W_m1 = T(R_m1, q_w - R_m1 @ np.array([SHAFT[0], SHAFT[1], Z_HORN[0]]))
    L["m_top"] = W_m1
    L["aj"] = W_m1 @ inv(T_aj_m1)

    # ρουλεμάν ώμου στην έδρα του I_shoulder (ομοαξονικό με τον servo)
    seat = MOUNTS["is_seat"][k]
    p_seat = apply(Is, seat["axis_p"])
    n_in = Is[:3, :3] @ np.array(seat["n_in"], float)
    L["b_top"] = bearing_pose(p_seat, n_in)

    # servo ισχίου στη διεπαφή του arm_joint· μηρός κάθετος (κάλυμμα με Ry(180) όπως στο αρχείο)
    hip = MOUNTS["aj_hip"]
    q2 = apply(L["aj"], hip["axis_p"])
    R_cov = np.diag([-1.0, 1.0, -1.0])
    T_cov_m2 = motor_frame(**MOUNTS["cover_hip"])
    p_horn_in_cov = apply(T_cov_m2, [SHAFT[0], SHAFT[1], Z_HORN[0]])
    W_cov = T(R_cov, q2 - R_cov @ p_horn_in_cov)
    L["cover"] = W_cov
    L["m_mid"] = W_cov @ T_cov_m2

    # arm: ίδιος προσανατολισμός με το κάλυμμα, γόνατο ομοαξονικό με το δαχτυλίδι του καλύμματος
    L["arm"] = W_cov @ T(None, ARM_IN_COVER)

    # servo γονάτου: κόρνα στην εσοχή του arm, σώμα μέσα στο wrist· κνήμη κάθετη (wrist με Ry(90) όπως στο αρχείο)
    kn = MOUNTS["arm_knee"]
    q3 = apply(L["arm"], kn["axis_p"])
    R_wr = np.array([[0, 0, 1.0], [0, 1, 0], [-1, 0, 0]])
    T_wr_m3 = motor_frame(**MOUNTS["wrist_servo"])
    p_horn_in_wr = apply(T_wr_m3, [SHAFT[0], SHAFT[1], Z_HORN[0]])
    W_wr = T(R_wr, q3 - R_wr @ p_horn_in_wr)
    L["m_bot"] = W_wr @ T_wr_m3
    # η στοίβα (πλάκα arm 2.5 mm + τοίχωμα wrist) είναι ~1.3 mm μακρύτερη από την πλήμνη της κόρνας:
    # το wrist απομακρύνεται κατά τον άξονα (ο servo μένει με την κόρνα στην εσοχή του arm)
    W_wr = W_wr.copy()
    W_wr[:3, 3] += KNEE_WRIST_GAP * (W_cov[:3, :3] @ np.array([0, 1.0, 0]))
    L["wrist"] = W_wr

    # ρουλεμάν γονάτου στο δαχτυλίδι του καλύμματος
    ks = MOUNTS["cover_knee_seat"]
    L["b_bot"] = bearing_pose(apply(W_cov, ks["axis_p"]), W_cov[:3, :3] @ np.array(ks["n_in"], float))

    # πέλμα
    L["foot"] = L["wrist"] @ T(FOOT_IN_WRIST_R, FOOT_IN_WRIST_T)

    # ενίσχυση ώμου: ομοαξονική με τον άξονα ισχίου και τις δύο βίδες M3 του arm_joint
    targets = [
        (REINF_LINES["ring"], (q2, L["aj"][:3, :3] @ np.array(hip["d"], float))),
        (REINF_LINES["zhole"], (apply(L["aj"], AJ_LINES["yhole"][0]), L["aj"][:3, :3] @ np.array(AJ_LINES["yhole"][1], float))),
        (REINF_LINES["xhole"], (apply(L["aj"], AJ_LINES["zhole"][0]), L["aj"][:3, :3] @ np.array(AJ_LINES["zhole"][1], float))),
    ]
    L["reinf"], res = fit_lines(targets)
    L["_reinf_residual"] = res

    # ρουλεμάν ισχίου μέσα στο δαχτυλίδι της ενίσχυσης, στην πλευρά του μηρού (εκεί που φτάνει ο πείρος του servo)
    d2 = L["m_mid"][:3, :3] @ np.array([0, 0, 1.0])     # σώμα → κόρνα (προς arm_joint)
    p_a = apply(L["reinf"], [14.1, REINF_RING_Y[0], 23.4])
    p_b = apply(L["reinf"], [14.1, REINF_RING_Y[1], 23.4])
    # εξωτερική όψη = αυτή που απέχει περισσότερο από την κόρνα· το ρουλεμάν πρόσωπο με αυτήν, προς τα μέσα
    inner, outer = (p_a, p_b) if (p_a - p_b) @ d2 > 0 else (p_b, p_a)
    L["b_mid"] = bearing_pose(outer, inner - outer)

    # άξονες αρθρώσεων (στην ίσια στάση), για τη στάση του ποδιού
    L["_hip"] = (q2, L["aj"][:3, :3] @ np.array(hip["d"], float))
    L["_knee"] = (q3, L["arm"][:3, :3] @ np.array(kn["d"], float))
    return L, k


THIGH = ("cover", "m_mid", "arm", "b_bot", "m_bot", "wrist", "foot")   # γυρίζουν στο ισχίο
SHIN = ("m_bot", "wrist", "foot")                                       # γυρίζουν στο γόνατο


def pose_leg(L, hip_deg, knee_deg):
    """Στρέφει την κνήμη γύρω από το γόνατο και μετά όλο τον μηρό γύρω από το ισχίο (μοίρες, δεξιόστροφα ως προς +Y)."""
    L = dict(L)
    (qh, dh), (qk, dk) = L["_hip"], L["_knee"]
    # γωνίες ως προς τον άξονα +Y του κόσμου (ίδια φορά σε όλα τα πόδια)
    dh = dh * np.sign(dh[1])
    dk = dk * np.sign(dk[1])
    K = rot_about(qk, dk, knee_deg)
    H = rot_about(qh, dh, hip_deg)
    for r in SHIN:
        L[r] = K @ L[r]
    for r in THIGH:
        L[r] = H @ L[r]
    return L


def fit_lines(pairs):
    """Βρίσκει θέση (μία από τις 24 στροφές αξόνων + μετατόπιση) ώστε τοπικές ευθείες να γίνουν ομοαξονικές
    με ευθείες-στόχους. pairs: [((p_local, a_local), (q_world, b_world))]. Επιστρέφει (4x4, rms mm)."""
    from spotgeo import rot_matrices_24
    best = None
    for R in rot_matrices_24():
        if any(abs(abs((R @ np.array(a, float)) @ (b / np.linalg.norm(b))) - 1) > 1e-6 for (p, a), (q, b) in pairs):
            continue
        A, rhs = [], []
        for (p, a), (q, b) in pairs:
            b = b / np.linalg.norm(b)
            Pp = np.eye(3) - np.outer(b, b)
            A.append(Pp)
            rhs.append(Pp @ (np.asarray(q, float) - R @ np.asarray(p, float)))
        A = np.vstack(A)
        rhs = np.concatenate(rhs)
        t, *_ = np.linalg.lstsq(A, rhs, rcond=None)
        res = np.sqrt(np.mean((A @ t - rhs) ** 2))
        if best is None or res < best[1]:
            best = (T(R, t), res)
    return best


def bearing_pose(p_face, n_in):
    """Ρουλεμάν (τοπ. άξονας X, 0..6) με την εξωτερική όψη στο p_face και άξονα προς n_in."""
    n = np.asarray(n_in, float)
    n /= np.linalg.norm(n)
    a = np.array([0, 0, 1.0]) if abs(n[2]) < 0.9 else np.array([1.0, 0, 0])
    y = np.cross(a, n)
    y /= np.linalg.norm(y)
    z = np.cross(n, y)
    return T(rot_cols(n, y, z), p_face)


# --- όλα τα πόδια ---------------------------------------------------------------------------------
# τοπικές συμμετρίες: για τα R κομμάτια ο καθρέφτης R→L (από τα αρχεία nonSTL της ομάδας),
# για τα συμμετρικά κομμάτια το δικό τους επίπεδο συμμετρίας
AJ_MIRROR = ([0, 0, 28.05], [0, 0, 1])   # επίπεδο συμμετρίας του arm_joint (εκτός από τη θήκη του servo)
S_LOCAL = {
    "arm": mirror_plane([0, 50, 0], [0, 1, 0]),
    "cover": mirror_plane([0, 50, 0], [0, 1, 0]),
    "wrist": mirror_plane([0, 0, 0], [0, 1, 0]),
    "reinf": mirror_plane([50, 0, 0], [1, 0, 0]),
    "motor": mirror_plane([-3.1, 0, 0], [1, 0, 0]),
    "bearing": mirror_plane([0, 0, 0], [0, 1, 0]),
    "foot": mirror_plane([0, 0, 0], [1, 0, 0]),
    "aj": mirror_plane(*AJ_MIRROR),
}
ROLE_SYM = {"arm": "arm", "cover": "cover", "wrist": "wrist", "reinf": "reinf", "foot": "foot", "aj": "aj",
            "m_top": "motor", "m_mid": "motor", "m_bot": "motor", "b_top": "bearing", "b_mid": "bearing", "b_bot": "bearing"}
AJ_GROUP = {"aj", "m_top", "b_top", "reinf", "b_mid"}   # δεμένα στο arm_joint: μπρος/πίσω κατοπτρικά
ROLE_LABEL = {
    "arm": ("L_arm_st_Leg{}", "R_arm_st_Leg{}"),
    "cover": ("L_arm_cover_for_shoulder_reinforcement_st_Leg{}", "R_arm_cover_for_shoulder_reinforcement_st_Leg{}"),
    "wrist": ("L_wrist_st_Leg{}", "R_wrist_st_Leg{}"),
    "reinf": ("L_shoulder_reinforcement_st_Leg{}", "R_shoulder_reinforcement_Leg{}"),  # βλ. REINF_SIDE
    "aj": ("arm_joint_for_shoulder_reinforcement_st_Leg{}",) * 2,
    "foot": ("foot_Leg{}",) * 2,
    "m_top": ("motor_Leg{}_top",) * 2, "m_mid": ("motor_Leg{}_middle",) * 2, "m_bot": ("motor_Leg{}_bottom",) * 2,
    "b_top": ("Bearing_Leg{}_top",) * 2, "b_mid": ("Bearing_Leg{}_middle",) * 2, "b_bot": ("Bearing_Leg{}_bottom",) * 2,
}
GREEK = str.maketrans({"Ρ": "R", "Β": "B", "Ε": "E", "Τ": "T", "Υ": "Y", "Ι": "I", "Ο": "O", "Α": "A", "Η": "H", "Κ": "K",
                       "Μ": "M", "Ν": "N", "Χ": "X", "Ζ": "Z"})


def latin(s):
    return s.translate(GREEK)


def mirrored(W, role, S_world):
    M = S_world @ W @ S_LOCAL[ROLE_SYM[role]]
    assert abs(np.linalg.det(M[:3, :3]) - 1) < 1e-6
    return M


def all_legs(P, W, yc):
    FL, k = leg_FL(P, W)
    FL = pose_leg(FL, HIP_DEG, KNEE_DEG)
    FL = {r: M for r, M in FL.items() if not r.startswith("_")}
    # επίπεδο μπρος/πίσω: ανάμεσα στις εσωτερικές όψεις των δύο O_shoulder
    xf = apply(W["O_shoulder_st_F"], [55, 0, 26])[0]
    xb = apply(W["O_shoulder_st_B"], [55, 0, 26])[0]
    xm = (xf + xb) / 2
    SX = mirror_plane([xm, 0, 0], [1, 0, 0])
    SY = mirror_plane([0, yc, 0], [0, 1, 0])
    x_hip = apply(FL["m_mid"], [SHAFT[0], SHAFT[1], 0])[0]
    dx = 2 * (xm - x_hip)
    BL = {}
    for r, M in FL.items():
        if r in AJ_GROUP:
            BL[r] = mirrored(M, r, SX)
        else:
            BL[r] = T(None, [dx, 0, 0]) @ M
    FR = {r: mirrored(M, r, SY) for r, M in FL.items()}
    BR = {r: mirrored(M, r, SY) for r, M in BL.items()}
    # τα R καλύμματα βγήκαν από παλαιότερη έκδοση του L καλύμματος: το R arm κάθεται ~1 mm πιο μέσα
    for legd in (FR, BR):
        inward = np.sign(yc - legd["arm"][1, 3])
        legd["arm"] = T(None, [0, inward * R_ARM_INWARD, 0]) @ legd["arm"]
    return {"FL": FL, "FR": FR, "BL": BL, "BR": BR}, dict(xm=xm, yc=yc, dx=dx)


def resolve_labels(P):
    """{(γωνία, ρόλος): label στο αρχείο} — με ανοχή σε ελληνικά γράμματα στα labels."""
    by_latin = {latin(k): k for k in P}
    out = {}
    for c in ("FL", "FR", "BL", "BR"):
        side = 0 if c[1] == "L" else 1
        for r, pats in ROLE_LABEL.items():
            if r == "reinf":
                # η ενίσχυση βιδώνει στο arm_joint: L στα FL/BR, R στα FR/BL (στο αρχείο τα L/R των πίσω ήταν ανάποδα)
                rs = 0 if c in ("FL", "BR") else 1
                src = {"FL": "FL", "FR": "FR", "BL": "BR", "BR": "BL"}[c]
                out[(c, r)] = by_latin[pats[rs].format(src)]
                continue
            name = pats[side].format(c)
            out[(c, r)] = by_latin[name]
    return out


def build(P):
    W = {k: p.M.copy() for k, p in P.items()}
    yc, z_axis, log = body_corrections(P, W)
    legs, info = all_legs(P, W, yc)
    labels = resolve_labels(P)
    for (c, r), lab in labels.items():
        W[lab] = legs[c][r]
    assert len(set(labels.values())) == len(labels)
    return W, legs, labels, info, log


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "all":
    P = load()
    W, legs, labels, info, log = build(P)
    print("\n".join(log))
    print(info)
    out = {k: [float(x) for x in W[k].ravel()] for k in P}
    json.dump(out, open(os.path.join(HERE, "placements.json"), "w"), indent=1, ensure_ascii=False)
    print("placements.json:", len(out), "κομμάτια")
    # μετονομασίες: label = θέση στο ρομπότ (με λατινικούς χαρακτήρες)
    renames = {}
    for (c, r), lab in labels.items():
        side = 0 if r != "reinf" else (0 if c in ("FL", "BR") else 1)
        if r != "reinf":
            side = 0 if c[1] == "L" else 1
        want = ROLE_LABEL[r][side].format(c)
        if lab != want:
            renames[lab] = want
    for k in P:
        if latin(k) != k and k not in renames:
            renames[k] = latin(k)
    # arm_joint: υπάρχει μόνο L στο αρχείο. Στα FR/BL γίνεται κατοπτρικό (R) ως προς το δικό του επίπεδο
    # συμμετρίας· με τη θέση που ήδη υπολογίστηκε (mirrored) βγαίνει ακριβές είδωλο του L.
    mirrors = {}
    for c in ("FL", "FR", "BL", "BR"):
        lab = labels[(c, "aj")]
        side = "L" if c in ("FL", "BR") else "R"
        renames[lab] = f"{side}_{ROLE_LABEL['aj'][0].format(c)}"
        if side == "R":
            mirrors[lab] = {"point": AJ_MIRROR[0], "normal": AJ_MIRROR[1]}
    json.dump(renames, open(os.path.join(HERE, "renames.json"), "w"), indent=1, ensure_ascii=False)
    json.dump(mirrors, open(os.path.join(HERE, "mirrors.json"), "w"), indent=1, ensure_ascii=False)
    print("renames.json:", renames)
    print("mirrors.json:", list(mirrors))
