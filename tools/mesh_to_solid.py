"""Convert every Mesh::Feature in a FreeCAD assembly to a solid, in place.

For each mesh: (optional) decimate -> Create shape from mesh (sewed) ->
Convert to solid -> new Part::Feature with same Label/Placement, put in the
same Assembly group, old mesh removed. The GroundedJoint is re-pointed.
The original file is never overwritten; result goes to OUT.

Run headless:
  freecad.cmd tools/mesh_to_solid.py  (paths via env vars below)
Env:
  SRC        input .FCStd
  OUT        output .FCStd
  MAX_TRIS   decimate meshes above this triangle count (0 = no decimation)
  ONLY       comma-separated object names to process (for testing)
"""
import os
import time

import FreeCAD as App
import Mesh
import Part

SRC = os.environ["SRC"]
OUT = os.environ["OUT"]
MAX_TRIS = int(os.environ.get("MAX_TRIS", "15000"))
ONLY = [s for s in os.environ.get("ONLY", "").split(",") if s]
TOL = 0.1


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


doc = App.openDocument(SRC)
meshes = [o for o in doc.Objects if o.TypeId == "Mesh::Feature"]
if ONLY:
    meshes = [o for o in meshes if o.Name in ONLY]
log(f"{len(meshes)} meshes to convert, MAX_TRIS={MAX_TRIS}")

grounds = {}
for j in doc.Objects:
    tgt = getattr(j, "ObjectToGround", None)
    if tgt is not None:
        grounds.setdefault(tgt.Name, []).append(j)

t_all = time.time()
for i, m in enumerate(meshes, 1):
    t0 = time.time()
    name, label, placement = m.Name, m.Label, m.Placement
    parents = [p for p in m.InList if hasattr(p, "Group") and m in p.Group]
    mesh = m.Mesh.copy()
    mesh.Placement = App.Placement()  # work in local coords
    n0 = mesh.CountFacets
    if MAX_TRIS and n0 > MAX_TRIS:
        mesh.decimate(1.0, 1.0 - MAX_TRIS / n0)
    n1 = mesh.CountFacets

    shape = Part.Shape()
    shape.makeShapeFromMesh(mesh.Topology, TOL, True)  # True = sew
    shell = Part.Shell(shape.Faces) if shape.ShapeType != "Shell" else shape
    try:
        solid = Part.Solid(shell)
        kind = "solid"
    except Exception as e:  # open mesh: keep shell, still usable for joints
        solid = shell
        kind = f"SHELL (not closed: {e})"

    doc.removeObject(name)
    new = doc.addObject("Part::Feature", name)
    new.Label = label
    new.Shape = solid
    new.Placement = placement
    for p in parents:
        p.addObject(new)
    for j in grounds.get(name, []):
        j.ObjectToGround = new
    log(f"[{i}/{len(meshes)}] {label}: {n0}->{n1} tris, {kind}, {time.time()-t0:.0f}s")
    if i % 5 == 0:
        doc.saveAs(OUT)  # checkpoint

doc.recompute()
doc.saveAs(OUT)
log(f"DONE in {(time.time()-t_all)/60:.1f} min -> {OUT}")
