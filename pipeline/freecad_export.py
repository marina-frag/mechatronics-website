# -*- coding: utf-8 -*-
"""
Βήμα 1/2 — FreeCAD → ενδιάμεσα αρχεία για το Blender.

Ανοίγει τη συναρμολόγηση (.FCStd) χωρίς γραφικό περιβάλλον και, για κάθε
εξάρτημα που είναι άμεσο παιδί του Assembly, γράφει:

  build/geometry.bin   τρίγωνα (float32 κορυφές + uint32 δείκτες)
  build/manifest.json  όνομα, label, θέση στη συναρμολόγηση (4x4, mm)

Ίδια κομμάτια (π.χ. τα 4 πέλματα) γράφονται μία φορά και τα μοιράζονται
όλα τα αντίγραφα, ώστε το τελικό .glb να μένει μικρό.

Υποστηρίζει: Mesh::Feature (εισαγμένα STL), Part::Feature (STEP),
PartDesign::Body, App::Part / υπο-συναρμολογήσεις και App::Link.
Κρυμμένα αντικείμενα παραλείπονται (εκτός αν SPOT_INCLUDE_HIDDEN=1).

Εκτέλεση (το build_glb.sh το κάνει αυτόματα):
    SPOT_FCSTD=/path/SPOT_assembly.FCStd SPOT_BUILD_DIR=/path/build \
        freecad.cmd freecad_export.py

Μεταβλητές περιβάλλοντος:
    SPOT_FCSTD           αρχείο συναρμολόγησης (υποχρεωτικό)
    SPOT_BUILD_DIR       φάκελος εξόδου (υποχρεωτικό)
    SPOT_ASSEMBLY        όνομα αντικειμένου Assembly (προεπιλογή: το πρώτο)
    SPOT_DEFLECTION      ακρίβεια τριγωνοποίησης STEP σε mm (προεπιλογή 0.1)
    SPOT_ANGULAR_DEG     γωνιακή ακρίβεια STEP σε μοίρες (προεπιλογή 10 → ~36 πλευρές/κύκλο)
    SPOT_INCLUDE_HIDDEN  1 = εξάγει και τα κρυμμένα
"""
import datetime
import hashlib
import json
import os
import sys
import traceback

import FreeCAD as App
import numpy as np

# Αντικείμενα που δεν είναι γεωμετρία.
SKIP_TYPES = {
    "App::Origin", "App::Line", "App::Plane", "App::Point",
    "Assembly::JointGroup", "Assembly::ViewGroup", "Assembly::BomGroup",
    "Assembly::SimulationGroup",
}
LINK_TYPES = {"App::Link", "App::LinkElement"}


def log(msg):
    print("[freecad_export] " + msg, flush=True)


def placement_matrix(pl):
    m = pl.toMatrix()
    return np.array([
        [m.A11, m.A12, m.A13, m.A14],
        [m.A21, m.A22, m.A23, m.A24],
        [m.A31, m.A32, m.A33, m.A34],
        [0.0, 0.0, 0.0, 1.0],
    ])


def own_placement(obj):
    pl = getattr(obj, "Placement", None)
    return placement_matrix(pl) if pl is not None else np.eye(4)


def transform(points, M):
    return points @ M[:3, :3].T + M[:3, 3]


def is_visible(obj, include_hidden):
    return include_hidden or getattr(obj, "Visibility", True)


def local_mesh(obj):
    """Κορυφές/τρίγωνα του Mesh στις δικές του συντεταγμένες (χωρίς Placement)."""
    mesh = obj.Mesh.copy()
    mesh.Placement = App.Placement()
    pts, facets = mesh.Topology
    return (np.array([(p.x, p.y, p.z) for p in pts], dtype=np.float64),
            np.array(facets, dtype=np.uint32).reshape(-1, 3),
            placement_matrix(obj.Mesh.Placement))


def local_shape(obj, deflection):
    """Τριγωνοποίηση ενός solid (STEP/Part/Body) στις δικές του συντεταγμένες.
    deflection = (γραμμική σε mm, γωνιακή σε rad)."""
    import MeshPart
    shape = obj.Shape.copy()
    if shape.isNull() or not shape.Faces:
        return None
    shape.Placement = App.Placement()
    linear, angular = deflection
    mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=linear,
                                  AngularDeflection=angular, Relative=False)
    pts, tris = mesh.Topology
    if not tris:
        return None
    return (np.array([(p.x, p.y, p.z) for p in pts], dtype=np.float64),
            np.array(tris, dtype=np.uint32).reshape(-1, 3),
            placement_matrix(obj.Shape.Placement))


class Exporter:
    def __init__(self, deflection, include_hidden):
        self.deflection = deflection
        self.include_hidden = include_hidden
        self.warnings = []

    def warn(self, msg):
        self.warnings.append(msg)
        log("ΠΡΟΣΟΧΗ: " + msg)

    def collect(self, obj, M, leaves, check_visibility=True):
        """
        Μαζεύει τα φύλλα-γεωμετρίες κάτω από το obj.
        M: πίνακας από το πλαίσιο του γονέα του obj → πλαίσιο του εξαρτήματος.
        """
        if obj is None or obj.TypeId in SKIP_TYPES:
            return
        if check_visibility and not is_visible(obj, self.include_hidden):
            return
        t = obj.TypeId

        if t in LINK_TYPES:
            if getattr(obj, "ElementCount", 0):
                self.warn(f"{obj.Label}: τα Link arrays δεν υποστηρίζονται, παραλείπεται")
                return
            target = obj.LinkedObject
            if isinstance(target, tuple):
                if len(target) > 1 and target[1]:
                    self.warn(f"{obj.Label}: link σε υπο-στοιχείο '{target[1]}', εξάγεται όλο το αντικείμενο")
                target = target[0]
            if target is None:
                self.warn(f"{obj.Label}: κενό link, παραλείπεται")
                return
            Mn = M @ own_placement(obj)
            if not getattr(obj, "LinkTransform", False):
                # Η θέση του link αντικαθιστά τη θέση του αρχικού αντικειμένου.
                Mn = Mn @ np.linalg.inv(own_placement(target))
            self.collect(target, Mn, leaves, check_visibility=False)
            return

        if obj.isDerivedFrom("Mesh::Feature"):
            v, f, P = local_mesh(obj)
            if len(f):
                leaves.append((obj, transform(v, M @ P), f))
            return

        if t == "PartDesign::Body":
            res = local_shape(obj, self.deflection)
            if res:
                v, f, P = res
                leaves.append((obj, transform(v, M @ P), f))
            return

        if hasattr(obj, "Group"):
            # App::Part / Assembly έχουν Placement, οι απλοί φάκελοι όχι.
            Mn = M @ own_placement(obj) if hasattr(obj, "Placement") else M
            for child in obj.Group:
                self.collect(child, Mn, leaves)
            return

        if hasattr(obj, "Shape"):
            res = local_shape(obj, self.deflection)
            if res:
                v, f, P = res
                leaves.append((obj, transform(v, M @ P), f))
            return
        # Οτιδήποτε άλλο (joints, scripts, κτλ.) δεν είναι γεωμετρία.


def find_assembly(doc, name):
    if name:
        obj = doc.getObject(name) or next((o for o in doc.Objects if o.Label == name), None)
        if obj is None:
            raise RuntimeError(f"Δεν βρέθηκε αντικείμενο '{name}' στο αρχείο")
        return obj
    for o in doc.Objects:
        if o.TypeId == "Assembly::AssemblyObject" and not o.getParentGeoFeatureGroup():
            return o
    raise RuntimeError("Δεν βρέθηκε Assembly. Ορίστε SPOT_ASSEMBLY=<όνομα>")


def geometry_hash(submeshes):
    h = hashlib.sha1()
    for v, f in submeshes:
        h.update(np.round(v, 3).astype("<f4").tobytes())
        h.update(f.astype("<u4").tobytes())
    return h.hexdigest()


def main():
    fcstd = os.environ.get("SPOT_FCSTD")
    build_dir = os.environ.get("SPOT_BUILD_DIR")
    if not fcstd or not build_dir:
        raise RuntimeError("Λείπουν οι μεταβλητές SPOT_FCSTD και/ή SPOT_BUILD_DIR")
    deflection = float(os.environ.get("SPOT_DEFLECTION", "0.1"))
    angular_deg = float(os.environ.get("SPOT_ANGULAR_DEG", "10"))
    include_hidden = os.environ.get("SPOT_INCLUDE_HIDDEN") == "1"
    os.makedirs(build_dir, exist_ok=True)

    log(f"Άνοιγμα {fcstd}")
    # Χωρίς recompute: παίρνουμε τις θέσεις όπως αποθηκεύτηκαν (ό,τι βλέπεις στο FreeCAD).
    doc = App.openDocument(fcstd)
    asm = find_assembly(doc, os.environ.get("SPOT_ASSEMBLY"))
    log(f"Assembly: {asm.Label} ({asm.TypeId})")
    G_root = placement_matrix(asm.getGlobalPlacement()) if hasattr(asm, "getGlobalPlacement") else own_placement(asm)

    import math
    ex = Exporter((deflection, math.radians(angular_deg)), include_hidden)
    geometries = {}      # hash -> {"id", "submeshes": [(label, name, v, f)]}
    components = []
    skipped = []

    for comp in asm.Group:
        has_geometry = (comp.TypeId in LINK_TYPES or hasattr(comp, "Mesh")
                        or hasattr(comp, "Shape") or hasattr(comp, "Group"))
        if comp.TypeId in SKIP_TYPES or not has_geometry:
            continue  # joints, origin κτλ.
        if not is_visible(comp, include_hidden):
            skipped.append({"name": comp.Name, "label": comp.Label, "reason": "κρυμμένο"})
            continue
        F = own_placement(comp)
        leaves = []
        try:
            ex.collect(comp, np.linalg.inv(F), leaves, check_visibility=False)
        except Exception as e:  # ένα χαλασμένο κομμάτι δεν σταματά όλη την εξαγωγή
            ex.warn(f"{comp.Label}: αποτυχία ({e})")
            continue
        if not leaves:
            skipped.append({"name": comp.Name, "label": comp.Label, "reason": f"χωρίς γεωμετρία ({comp.TypeId})"})
            continue

        key = geometry_hash([(v, f) for _, v, f in leaves])
        if key not in geometries:
            geometries[key] = {
                "id": "g%02d_%s" % (len(geometries), key[:8]),
                "submeshes": [(o.Label, o.Name, v, f) for o, v, f in leaves],
            }
        G = G_root @ F
        components.append({
            "name": comp.Name,
            "label": comp.Label,
            "type": comp.TypeId,
            "geometry": geometries[key]["id"],
            "matrix": [float(x) for x in G.ravel()],   # row-major 4x4, mm
            "leaves": len(leaves),
        })
        tris = sum(len(f) for _, _, f in leaves)
        log(f"  {comp.Label:55s} {len(leaves):3d} κομμάτια {tris:8d} τρίγωνα -> {geometries[key]['id']}")

    # Εγγραφή γεωμετριών σε ένα δυαδικό αρχείο.
    bin_path = os.path.join(build_dir, "geometry.bin")
    geo_out = {}
    with open(bin_path, "wb") as fh:
        for g in geometries.values():
            subs = []
            for label, name, v, f in g["submeshes"]:
                v_off = fh.tell(); fh.write(v.astype("<f4").tobytes())
                i_off = fh.tell(); fh.write(f.astype("<u4").tobytes())
                subs.append({"label": label, "name": name,
                             "v_off": v_off, "v_count": int(len(v)),
                             "i_off": i_off, "t_count": int(len(f))})
            geo_out[g["id"]] = {"submeshes": subs,
                                "triangles": int(sum(s["t_count"] for s in subs))}

    manifest = {
        "source": os.path.abspath(fcstd),
        "assembly": {"name": asm.Name, "label": asm.Label},
        "exported_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "freecad": ".".join(App.Version()[:3]),
        "units": "mm",
        "up_axis": "Z",
        "deflection_mm": deflection,
        "angular_deflection_deg": angular_deg,
        "geometries": geo_out,
        "components": components,
        "skipped": skipped,
        "warnings": ex.warnings,
    }
    man_path = os.path.join(build_dir, "manifest.json")
    with open(man_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1)

    total = sum(geo_out[c["geometry"]]["triangles"] for c in components)
    log(f"Εξαρτήματα: {len(components)}, μοναδικές γεωμετρίες: {len(geo_out)}, "
        f"τρίγωνα (με αντίγραφα): {total:,}")
    for s in skipped:
        log(f"  παραλείφθηκε: {s['label']} — {s['reason']}")
    log(f"OK -> {man_path}")


try:
    main()
except Exception:
    traceback.print_exc()
    err = os.path.join(os.environ.get("SPOT_BUILD_DIR", "."), "export_error.txt")
    with open(err, "w", encoding="utf-8") as fh:
        fh.write(traceback.format_exc())
    log(f"ΑΠΟΤΥΧΙΑ — δες {err}")
