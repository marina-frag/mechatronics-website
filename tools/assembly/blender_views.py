"""Blender (headless): αποδίδει κομμάτια από το geometry.bin σε ορθογραφικές όψεις.

blender -b --factory-startup -P blender_views.py -- spec.json
spec: {"build": dir, "parts": [{"label", "geom", "matrix"[16], "color"[3], "alpha"}],
       "views": [{"dir": [x,y,z], "up": [x,y,z], "name": str}], "size": [w,h], "out_prefix": path,
       "focus": [xmin,ymin,zmin,xmax,ymax,zmax] (προαιρετικό)}
"""
import json
import os
import sys

import bpy
import numpy as np
from mathutils import Matrix, Vector

spec = json.load(open(sys.argv[sys.argv.index("--") + 1]))
build = spec["build"]
man = json.load(open(os.path.join(build, "manifest.json")))
blob = np.fromfile(os.path.join(build, "geometry.bin"), dtype=np.uint8)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
sh = scene.display.shading
sh.light = "STUDIO"
sh.color_type = "OBJECT"
sh.show_cavity = True
sh.cavity_type = "BOTH"
sh.show_object_outline = True
sh.object_outline_color = (0.05, 0.05, 0.05)
sh.show_specular_highlight = False
scene.display.render_aa = "8"
scene.render.film_transparent = False
world = bpy.data.worlds.new("w")
scene.world = world
sh.background_type = "VIEWPORT"
sh.background_color = (1, 1, 1)
w, h = spec.get("size", [900, 700])
scene.render.resolution_x, scene.render.resolution_y = w, h
scene.render.resolution_percentage = 100

meshes = {}


def get_mesh(gid):
    if gid in meshes:
        return meshes[gid]
    g = man["geometries"][gid]
    Vs, Fs, off = [], [], 0
    for s in g["submeshes"]:
        v = np.frombuffer(blob, "<f4", s["v_count"] * 3, s["v_off"]).reshape(-1, 3)
        f = np.frombuffer(blob, "<u4", s["t_count"] * 3, s["i_off"]).reshape(-1, 3)
        Vs.append(v)
        Fs.append(f + off)
        off += len(v)
    V = np.vstack(Vs)
    F = np.vstack(Fs).astype(np.int32)
    me = bpy.data.meshes.new(gid)
    me.vertices.add(len(V))
    me.vertices.foreach_set("co", V.astype(np.float32).ravel())
    me.loops.add(F.size)
    me.loops.foreach_set("vertex_index", F.ravel())
    me.polygons.add(len(F))
    me.polygons.foreach_set("loop_start", np.arange(0, F.size, 3, dtype=np.int32))
    me.update()
    meshes[gid] = me
    return me


allpts = []
for p in spec["parts"]:
    ob = bpy.data.objects.new(p["label"], get_mesh(p["geom"]))
    M = Matrix([p["matrix"][i * 4:(i + 1) * 4] for i in range(4)])
    ob.matrix_world = M
    c = p.get("color", [0.8, 0.8, 0.8])
    ob.color = (c[0], c[1], c[2], p.get("alpha", 1.0))
    scene.collection.objects.link(ob)
    bb = [M @ Vector(v) for v in ob.bound_box]
    allpts += [tuple(v) for v in bb]

P = np.array(allpts)
if spec.get("focus"):
    f = spec["focus"]
    P = np.array([[f[0], f[1], f[2]], [f[3], f[4], f[5]]])
    P = np.array([[x, y, z] for x in P[:, 0] for y in P[:, 1] for z in P[:, 2]])
center = (P.min(0) + P.max(0)) / 2
radius = np.linalg.norm(P.max(0) - P.min(0)) / 2 + 1

cam_data = bpy.data.cameras.new("cam")
cam_data.type = "ORTHO"
cam = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
cam_data.clip_start = 0.1
cam_data.clip_end = radius * 10

for i, v in enumerate(spec["views"]):
    d = Vector(v["dir"]).normalized()
    up = Vector(v.get("up", [0, 0, 1]))
    if abs(d.dot(up.normalized())) > 0.99:
        up = Vector((0, 1, 0)) if abs(d.y) < 0.9 else Vector((1, 0, 0))
    pos = Vector(center) + d * radius * 3
    z = d
    x = up.cross(z).normalized()
    y = z.cross(x)
    R = Matrix((x, y, z)).transposed()
    cam.matrix_world = Matrix.Translation(pos) @ R.to_4x4()
    # ορθογραφικό πλάτος ώστε να χωράει η προβολή
    Pc = (P - center)
    u = Pc @ np.array(x)
    vv = Pc @ np.array(y)
    span = max((u.max() - u.min()), (vv.max() - vv.min()) * w / h) * 1.08
    cam_data.ortho_scale = span
    cam.matrix_world = Matrix.Translation(pos + x * float((u.max() + u.min()) / 2) + y * float((vv.max() + vv.min()) / 2)) @ R.to_4x4()
    scene.render.filepath = f"{spec['out_prefix']}_{i}.png"
    bpy.ops.render.render(write_still=True)
    print("[views] wrote", scene.render.filepath, "scale", span)
