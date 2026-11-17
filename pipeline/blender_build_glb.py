# -*- coding: utf-8 -*-
"""
Βήμα 2/2 — Blender: build/manifest.json + geometry.bin → spot.glb

Τι κάνει:
  * ενώνει διπλές κορυφές και μειώνει τρίγωνα (decimate) ώστε όλο το
    μοντέλο να χωράει στο triangle_budget του spot_parts.json
  * ίδια κομμάτια μοιράζονται ένα mesh (instancing στο .glb)
  * υλικά ανά υποσύστημα (σκελετός / κινητήρες / ηλεκτρονικά)
  * mm → m, origin στο κέντρο κάθε κομματιού
  * κάθε κόμβος του .glb έχει extras (στο three.js: object.userData):
      label, freecadName, subsystem, subsystemLabel, leg, geometry, triangles
  * γράφει spot.glb, spot.blend (για έλεγχο στο Blender) και spot_report.json

Εκτέλεση (το build_glb.sh το κάνει αυτόματα):
    blender -b --factory-startup -P blender_build_glb.py -- \
        --build build --config spot_parts.json --out out/spot.glb
"""
import argparse
import json
import math
import os
import re
import sys
import time
from collections import Counter, OrderedDict

import bmesh
import bpy
import numpy as np
from mathutils import Matrix


def log(msg):
    print("[blender_build] " + msg, flush=True)


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser(prog="blender_build_glb.py")
    p.add_argument("--build", required=True, help="φάκελος με manifest.json + geometry.bin")
    p.add_argument("--config", required=True, help="spot_parts.json")
    p.add_argument("--out", required=True, help="τελικό .glb")
    p.add_argument("--budget", type=int, help="αντικαθιστά το triangle_budget")
    p.add_argument("--no-draco", action="store_true", help="χωρίς συμπίεση Draco")
    p.add_argument("--no-blend", action="store_true", help="να μη γραφτεί .blend")
    p.add_argument("--cover", help="αποδίδει και μια εικόνα PNG του μοντέλου (για την κάρτα του project)")
    return p.parse_args(argv)


def render_cover(path, root):
    """Εικόνα 1200x800 με διάφανο φόντο: Cycles στον επεξεργαστή, ~10 δευτερόλεπτα."""
    from mathutils import Vector
    scene = bpy.context.scene
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in root.children_recursive if o.type == "MESH" for c in o.bound_box]
    if not pts:
        return
    mn = Vector([min(p[i] for p in pts) for i in range(3)])
    mx = Vector([max(p[i] for p in pts) for i in range(3)])
    center, size = (mn + mx) / 2, (mx - mn).length

    cam = bpy.data.objects.new("_cover_cam", bpy.data.cameras.new("_cover_cam"))
    scene.collection.objects.link(cam)
    cam.data.lens = 50
    d = Vector((1.0, -1.25, 0.8)).normalized()
    cam.location = center + d * size * 1.15
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    cam.data.clip_start, cam.data.clip_end = size * 0.01, size * 20
    scene.camera = cam

    sun = bpy.data.objects.new("_cover_sun", bpy.data.lights.new("_cover_sun", "SUN"))
    sun.data.energy, sun.rotation_euler = 3.0, (0.75, 0.15, 0.7)
    scene.collection.objects.link(sun)
    world = bpy.data.worlds.new("_cover_world")
    world.color = (0.8, 0.8, 0.8)
    scene.world = world

    scene.render.engine = "CYCLES"
    scene.cycles.device, scene.cycles.samples = "CPU", 48
    scene.cycles.use_denoising = True
    scene.render.film_transparent = True
    scene.render.resolution_x, scene.render.resolution_y = 1200, 800
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.filepath = os.path.abspath(path)
    os.makedirs(os.path.dirname(scene.render.filepath), exist_ok=True)
    bpy.ops.render.render(write_still=True)
    for ob in (cam, sun):
        bpy.data.objects.remove(ob)
    scene.world = None
    log(f"Εικόνα -> {path}")


# ---------------------------------------------------------------- κανόνες

def first_match(rules, text):
    for r in rules:
        if re.search(r["match"], text, re.IGNORECASE):
            return r
    return None


def classify(label, cfg):
    rule = first_match(cfg["component_rules"], label) or {}
    sub = rule.get("subsystem", cfg["default_subsystem"])
    material = rule.get("material") or cfg["subsystems"][sub]["material"]
    return sub, material


def detect_leg(label, cfg):
    m = re.search(cfg["legs"], label)
    return next((g for g in m.groups() if g), "") if m else ""


# ---------------------------------------------------------------- υλικά

def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def make_material(name, spec):
    h = spec["color"].lstrip("#")
    rgb = [srgb_to_linear(int(h[i:i + 2], 16) / 255.0) for i in (0, 2, 4)]
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*rgb, 1.0)
    bsdf = next(n for n in mat.node_tree.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
    bsdf.inputs["Metallic"].default_value = spec.get("metallic", 0.0)
    bsdf.inputs["Roughness"].default_value = spec.get("roughness", 0.5)
    return mat


# ---------------------------------------------------------------- meshes

def new_mesh(name, verts, tris):
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(verts))
    me.vertices.foreach_set("co", verts.astype(np.float32).ravel())
    me.loops.add(len(tris) * 3)
    me.loops.foreach_set("vertex_index", tris.astype(np.int32).ravel())
    me.polygons.add(len(tris))
    me.polygons.foreach_set("loop_start", np.arange(0, len(tris) * 3, 3, dtype=np.int32))
    me.update(calc_edges=True)
    me.validate(clean_customdata=False)   # πετάει εκφυλισμένα τρίγωνα των STL
    return me


def mesh_arrays(me):
    me.calc_loop_triangles()
    v = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", v)
    t = np.empty(len(me.loop_triangles) * 3, np.int32)
    me.loop_triangles.foreach_get("vertices", t)
    return v.reshape(-1, 3), t.reshape(-1, 3)


def weld(me, dist):
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bm.to_mesh(me)
    bm.free()


def _evaluate(me, scratch, setup):
    """Εφαρμόζει modifiers σε ένα προσωρινό αντικείμενο και επιστρέφει νέο mesh."""
    ob = bpy.data.objects.new("_decimate", me)
    scratch.objects.link(ob)
    setup(ob)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    out = bpy.data.meshes.new_from_object(ob.evaluated_get(depsgraph))
    bpy.data.objects.remove(ob)
    bpy.data.meshes.remove(me)
    return out


def triangle_count(me):
    me.calc_loop_triangles()
    return len(me.loop_triangles)


def planar_simplify(me, scratch, angle_deg):
    """Ενώνει τα τρίγωνα των απόλυτα επίπεδων επιφανειών των CAD. Το σχήμα δεν
    αλλάζει καθόλου, αλλά φεύγουν χιλιάδες περιττά τρίγωνα από τα επίπεδα."""
    if angle_deg <= 0:
        return me

    def setup(ob):
        d = ob.modifiers.new("planar", "DECIMATE")
        d.decimate_type = "DISSOLVE"
        d.angle_limit = math.radians(angle_deg)
        d.delimit = {"NORMAL"}
        tri = ob.modifiers.new("tri", "TRIANGULATE")
        tri.quad_method = "BEAUTY"
        tri.ngon_method = "BEAUTY"
    return _evaluate(me, scratch, setup)


def collapse_to(me, target, scratch):
    """Collapse decimation μέχρι τον στόχο τριγώνων."""
    n = triangle_count(me)
    if target >= n:
        return me

    def setup(ob):
        d = ob.modifiers.new("collapse", "DECIMATE")
        d.decimate_type = "COLLAPSE"
        d.ratio = max(target / n, 1e-4)
        d.use_collapse_triangulate = True
    return _evaluate(me, scratch, setup)


def surface_area(v, t):
    a, b, c = v[t[:, 0]], v[t[:, 1]], v[t[:, 2]]
    return float(0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1).sum())


def allocate_triangles(parts, budget):
    """
    Μοιράζει το budget ώστε όλα τα κομμάτια να έχουν την ίδια πυκνότητα
    τριγώνων ανά m² (ρ). Κανένα κομμάτι δεν ξεπερνά τα αρχικά του τρίγωνα
    και κανένα δεν πέφτει κάτω από το floor του. Επιστρέφει τη ρ.
    parts: dicts με t, area, inst, floor, fixed (None ή αριθμός τριγώνων)
    """
    def target(p, rho):
        if p["fixed"] is not None:
            return p["fixed"]
        return min(p["t"], max(p["floor"], rho * p["area"]))

    def total(rho):
        return sum(p["inst"] * target(p, rho) for p in parts)

    hi = max((p["t"] / p["area"] for p in parts if p["area"] > 0), default=0.0)
    if total(hi) > budget:
        lo = 0.0
        for _ in range(200):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if total(mid) <= budget else (lo, mid)
        hi = lo
    for p in parts:
        p["target"] = int(target(p, hi))
    return hi


# ---------------------------------------------------------------- main

def main():
    args = parse_args()
    t0 = time.time()
    cfg = json.load(open(args.config, encoding="utf-8"))
    man = json.load(open(os.path.join(args.build, "manifest.json"), encoding="utf-8"))
    blob = np.fromfile(os.path.join(args.build, "geometry.bin"), dtype=np.uint8)
    scale = 0.001 if man.get("units", "mm") == "mm" else 1.0
    weld_dist = cfg.get("weld_distance_mm", 0.001) * scale
    budget = args.budget or cfg["decimation"]["triangle_budget"]
    min_part = cfg["decimation"].get("min_triangles_per_part", 200)
    planar_deg = cfg["decimation"].get("planar_angle_deg", 0.05)
    exclude = cfg.get("exclude_parts") or ""
    draco = cfg.get("draco", True) and not args.no_draco

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scratch = bpy.data.collections.new("_scratch")
    scene.collection.children.link(scratch)

    comps = man["components"]
    geoms = man["geometries"]
    if not comps:
        raise SystemExit("Το manifest δεν έχει εξαρτήματα")

    # Κατάταξη κάθε εξαρτήματος + βασικό υλικό ανά γεωμετρία.
    for c in comps:
        c["subsystem"], c["material"] = classify(c["label"], cfg)
        c["leg"] = detect_leg(c["label"], cfg)
    geo_users = OrderedDict()
    for c in comps:
        geo_users.setdefault(c["geometry"], []).append(c)

    # Ποια κομμάτια κρατάμε από κάθε γεωμετρία.
    kept = {}
    for gid, users in geo_users.items():
        subs = geoms[gid]["submeshes"]
        if exclude and len(subs) > 1:
            subs = [s for s in subs if not re.search(exclude, s["label"], re.IGNORECASE)]
        kept[gid] = subs

    # 1) Κάθε κομμάτι: ένωση κορυφών + planar dissolve (χωρίς αλλαγή σχήματος).
    inst = Counter(c["geometry"] for c in comps)
    tris = {g: sum(s["t_count"] for s in kept[g]) for g in geo_users}
    part_mesh, budget_parts = {}, {}
    for gid, users in geo_users.items():
        rule = first_match(cfg["decimation"].get("overrides", []), users[0]["label"])
        for i, s in enumerate(kept[gid]):
            v = np.frombuffer(blob, "<f4", s["v_count"] * 3, s["v_off"]).reshape(-1, 3) * scale
            t = np.frombuffer(blob, "<u4", s["t_count"] * 3, s["i_off"]).reshape(-1, 3)
            me = new_mesh("_part", v, t)
            weld(me, weld_dist)
            me = planar_simplify(me, scratch, planar_deg)
            n = triangle_count(me)
            part_mesh[(gid, i)] = me
            fixed = None
            if rule:
                ratio = 1.0 if rule.get("keep") else min(1.0, rule["max_triangles"] / max(tris[gid], 1))
                fixed = max(int(n * ratio), min(n, min_part))
            budget_parts[(gid, i)] = {"t": n, "area": surface_area(v, t), "inst": inst[gid],
                                      "floor": min(n, min_part), "fixed": fixed}
    before = sum(inst[g] * tris[g] for g in tris)
    after_planar = sum(p["inst"] * p["t"] for p in budget_parts.values())

    # 2) Ίδια πυκνότητα τριγώνων παντού: τα μεγάλα ορατά κομμάτια κρατούν
    #    λεπτομέρεια και τα μικρά/κρυμμένα δεν τρώνε budget.
    rho = allocate_triangles(list(budget_parts.values()), budget)
    log(f"Τρίγωνα: αρχικά {before:,} · μετά τα επίπεδα {after_planar:,} · στόχος {budget:,} · "
        f"πυκνότητα {rho / 1e4:.1f} τρίγωνα/cm²")

    # Υλικά.
    materials = {name: make_material(name, spec) for name, spec in cfg["materials"].items()}

    # 3) Collapse στον στόχο και ένωση των κομματιών κάθε γεωμετρίας σε ένα mesh.
    geo_mesh, geo_center, geo_final = {}, {}, {}
    for gid, users in geo_users.items():
        multi = len(geoms[gid]["submeshes"]) > 1
        base_mat = users[0]["material"]
        parts_v, parts_t, parts_m = [], [], []
        offset = 0
        for i, s in enumerate(kept[gid]):
            me = collapse_to(part_mesh.pop((gid, i)), budget_parts[(gid, i)]["target"], scratch)
            pv, pt = mesh_arrays(me)
            bpy.data.meshes.remove(me)
            mat = base_mat
            if multi:
                rule = first_match(cfg.get("part_material_rules", []), s["label"])
                mat = rule["material"] if rule else base_mat
            parts_v.append(pv)
            parts_t.append(pt + offset)
            parts_m.append((mat, len(pt)))
            offset += len(pv)
        if not parts_v or offset == 0:
            log(f"  ΠΡΟΣΟΧΗ: η γεωμετρία {gid} άδειασε, παραλείπεται")
            continue

        V = np.vstack(parts_v)
        T = np.vstack(parts_t)
        center = (V.min(0) + V.max(0)) / 2 if cfg.get("recenter_origins", True) else np.zeros(3)
        me = new_mesh(users[0]["label"], V - center, T)
        slot_names = list(OrderedDict.fromkeys(m for m, _ in parts_m))
        for name in slot_names:
            me.materials.append(materials[name])
        mat_idx = np.concatenate([np.full(k, slot_names.index(m), np.int32) for m, k in parts_m])
        if len(mat_idx) == len(me.polygons):
            me.polygons.foreach_set("material_index", mat_idx)
        me.shade_smooth()
        me.set_sharp_from_angle(angle=math.radians(cfg.get("smooth_angle_deg", 40)))
        geo_mesh[gid], geo_center[gid], geo_final[gid] = me, center, len(me.polygons)
        log(f"  {users[0]['label']:50s} x{inst[gid]}  {tris[gid]:7,d} → {geo_final[gid]:6,d} τρίγωνα")

    bpy.data.collections.remove(scratch)

    # Σκηνή: Spot (empty) → ένα αντικείμενο ανά εξάρτημα.
    spot_coll = bpy.data.collections.new("Spot")
    scene.collection.children.link(spot_coll)
    sub_coll = {}
    for key, sub in cfg["subsystems"].items():
        sub_coll[key] = bpy.data.collections.new(sub["label"])
        spot_coll.children.link(sub_coll[key])
    root = bpy.data.objects.new("Spot", None)
    spot_coll.objects.link(root)

    report, labels = [], Counter(c["label"] for c in comps)
    for c in comps:
        gid = c["geometry"]
        if gid not in geo_mesh:
            continue
        if labels[c["label"]] > 1:
            log(f"  ΠΡΟΣΟΧΗ: διπλό label '{c['label']}' — χρησιμοποίησε userData.freecadName στο site")
        name = c["label"].encode("utf-8")[:63].decode("utf-8", "ignore")
        ob = bpy.data.objects.new(name, geo_mesh[gid])
        M = Matrix([c["matrix"][i * 4:(i + 1) * 4] for i in range(4)])
        M.translation = M.translation * scale
        ob.matrix_basis = M @ Matrix.Translation(geo_center[gid].tolist())
        ob.parent = root
        sub_coll[c["subsystem"]].objects.link(ob)
        extras = {
            "label": c["label"],
            "freecadName": c["name"],
            "subsystem": c["subsystem"],
            "subsystemLabel": cfg["subsystems"][c["subsystem"]]["label"],
            "leg": c["leg"],
            "geometry": gid,
            "triangles": geo_final[gid],
        }
        for k, v in extras.items():
            ob[k] = v
        report.append({**extras, "name": ob.name, "triangles_source": tris[gid],
                       "instances_of_geometry": inst[gid]})

    # Εξαγωγή.
    out = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    gltf_opts = dict(
        filepath=out, export_format="GLB", use_selection=False,
        export_extras=True, export_yup=True, export_apply=False,
        export_texcoords=False, export_normals=True, export_materials="EXPORT",
        export_animations=False, export_cameras=False, export_lights=False,
        export_draco_mesh_compression_enable=draco,
        export_draco_mesh_compression_level=6,
    )
    valid = set(bpy.ops.export_scene.gltf.get_rna_type().properties.keys())
    for k in [k for k in gltf_opts if k not in valid]:
        log(f"  (η επιλογή {k} δεν υπάρχει σε αυτό το Blender, παραλείπεται)")
        gltf_opts.pop(k)
    bpy.ops.export_scene.gltf(**gltf_opts)

    stem = os.path.splitext(out)[0]
    if args.cover:
        render_cover(args.cover, root)
    if not args.no_blend:
        bpy.context.preferences.filepaths.save_version = 0   # χωρίς spot.blend1
        bpy.ops.wm.save_as_mainfile(filepath=stem + ".blend", compress=True)
    final_total = sum(r["triangles"] for r in report)
    with open(stem + "_report.json", "w", encoding="utf-8") as fh:
        json.dump({
            "glb": os.path.basename(out),
            "source": man.get("source"),
            "exported_from_freecad_at": man.get("exported_at"),
            "draco": draco,
            "triangles_before": before,
            "triangles_after": final_total,
            "subsystems": {k: v["label"] for k, v in cfg["subsystems"].items()},
            "parts": report,
            "freecad_warnings": man.get("warnings", []),
            "freecad_skipped": man.get("skipped", []),
        }, fh, ensure_ascii=False, indent=1)

    per_sub = Counter(r["subsystemLabel"] for r in report)
    summary = ", ".join("%s: %d" % (k, n) for k, n in per_sub.items())
    log(f"Εξαρτήματα: {len(report)} ({summary})")
    log(f"Τρίγωνα: {before:,} → {final_total:,}")
    log(f"OK -> {out} ({os.path.getsize(out) / 1e6:.1f} MB, Draco: {'ναι' if draco else 'όχι'}) σε {time.time() - t0:.0f}s")


try:
    main()
except SystemExit:
    raise
except Exception:
    import traceback
    traceback.print_exc()
    sys.exit(1)
