"""FreeCAD (headless): εφαρμόζει τις θέσεις του placements.json σε ΑΝΤΙΓΡΑΦΟ της συναρμολόγησης.

    SPOT_SRC=.../SPOT_assembly_solids.FCStd SPOT_DST=.../SPOT_assembly_auto.FCStd \
    SPOT_PLACEMENTS=.../placements.json SPOT_RENAMES=.../renames.json SPOT_MIRRORS=.../mirrors.json \
    freecad.cmd freecad_apply.py

SPOT_MIRRORS: κομμάτια που γίνονται κατοπτρικά ως προς ένα τοπικό επίπεδο (π.χ. R_arm_joint από το L).

Δεν γράφει ποτέ στο SPOT_SRC (αποθηκεύει με saveAs στο SPOT_DST, που πρέπει να είναι άλλο αρχείο).
"""
import json
import os

import FreeCAD as App

src = os.environ["SPOT_SRC"]
dst = os.environ["SPOT_DST"]
assert os.path.abspath(src) != os.path.abspath(dst), "το SPOT_DST πρέπει να είναι άλλο αρχείο"
pl = json.load(open(os.environ["SPOT_PLACEMENTS"]))
renames = json.load(open(os.environ["SPOT_RENAMES"])) if os.environ.get("SPOT_RENAMES") else {}
mirrors = json.load(open(os.environ["SPOT_MIRRORS"])) if os.environ.get("SPOT_MIRRORS") else {}

doc = App.openDocument(src, hidden=True)
by_label = {o.Label: o for o in doc.Objects}

# κατοπτρικά κομμάτια: καθρέφτης της γεωμετρίας στο τοπικό σύστημα (πριν από τη θέση)
for label, m in mirrors.items():
    o = by_label[label]
    s = o.Shape.copy()
    s.Placement = App.Placement()
    o.Shape = s.mirror(App.Vector(*m["point"]), App.Vector(*m["normal"]))
    assert o.Shape.isValid() and len(o.Shape.Solids) == len(s.Solids), label

done = []
for label, m in pl.items():
    o = by_label[label]
    M = App.Matrix(*m)
    o.Placement = App.Placement(M)
    if hasattr(o, "Visibility"):
        o.Visibility = True
    done.append(label)

# μετονομασίες σε δύο βήματα (για να μη συγκρουστούν προσωρινά ίδια labels)
objs = {lab: by_label[lab] for lab in renames}
for i, (old, new) in enumerate(renames.items()):
    objs[old].Label = f"__tmp_rename_{i}"
for old, new in renames.items():
    objs[old].Label = new

# το SPOT_DST είναι δικό μας παραγόμενο αρχείο: το αντικαθιστούμε χωρίς να αφήνουμε .FCBak δίπλα στα αρχεία της ομάδας
if os.path.exists(dst):
    os.remove(dst)
doc.saveAs(dst)
print(f"[freecad_apply] {len(done)} θέσεις, {len(mirrors)} κατοπτρικά, {len(renames)} μετονομασίες -> {dst}")
for old, new in renames.items():
    print(f"[freecad_apply]   {old} -> {objs[old].Label}")
