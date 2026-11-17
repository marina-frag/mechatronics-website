"""Βοηθός: αποδίδει κομμάτια σε πολλές όψεις και τις ενώνει σε μία εικόνα με τίτλους."""
import json
import os
import subprocess
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SCRATCH = os.environ.get("SPOT_SCRATCH", os.path.join(HERE, "cache", "tmp"))
os.makedirs(SCRATCH, exist_ok=True)

VIEWS = {
    "+X": [1, 0, 0], "-X": [-1, 0, 0], "+Y": [0, 1, 0], "-Y": [0, -1, 0], "+Z": [0, 0, 1], "-Z": [0, 0, -1],
    "iso": [1, -1.2, 0.9], "iso2": [-1, 1.2, 0.9], "iso3": [-1, -1.2, 0.9], "iso4": [1, 1.2, -0.9],
}

PALETTE = [
    (0.85, 0.33, 0.25), (0.25, 0.55, 0.85), (0.35, 0.7, 0.35), (0.9, 0.7, 0.2), (0.6, 0.4, 0.8),
    (0.2, 0.75, 0.75), (0.9, 0.5, 0.7), (0.55, 0.55, 0.55), (0.6, 0.45, 0.25), (0.15, 0.3, 0.5),
]


def render(items, views=("iso", "+X", "+Y", "+Z"), out="view.png", size=(700, 560), focus=None, build=None,
           title=None):
    """items: [(part, M or None, color or None)]"""
    from spotgeo import BUILD
    build = build or BUILD
    parts = []
    for i, it in enumerate(items):
        p, M, c = (it + (None, None))[:3] if isinstance(it, tuple) else (it, None, None)
        M = p.M if M is None else M
        parts.append({"label": p.label, "geom": p.geom, "matrix": [float(x) for x in np.asarray(M).ravel()],
                      "color": list(c or PALETTE[i % len(PALETTE)])})
    vs = [{"dir": VIEWS[v] if isinstance(v, str) else list(v), "name": str(v)} for v in views]
    tmp = tempfile.mkdtemp(dir=SCRATCH)
    spec = {"build": build, "parts": parts, "views": vs, "size": list(size), "out_prefix": os.path.join(tmp, "v"),
            "focus": focus}
    sp = os.path.join(tmp, "spec.json")
    json.dump(spec, open(sp, "w"))
    r = subprocess.run(["blender", "-b", "--factory-startup", "-P", os.path.join(HERE, "blender_views.py"), "--", sp],
                       capture_output=True, text=True)
    imgs = []
    for i in range(len(vs)):
        f = os.path.join(tmp, f"v_{i}.png")
        if not os.path.exists(f):
            raise RuntimeError(r.stdout[-3000:] + r.stderr[-3000:])
        imgs.append(Image.open(f).convert("RGB"))
    cols = 2 if len(imgs) > 1 else 1
    rows = (len(imgs) + cols - 1) // cols
    W, H = size
    head = 30 if title else 0
    sheet = Image.new("RGB", (W * cols, H * rows + head), "white")
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except Exception:
        font = ImageFont.load_default()
    if title:
        d.text((8, 6), title, fill="black", font=font)
    for i, im in enumerate(imgs):
        x, y = (i % cols) * W, (i // cols) * H + head
        sheet.paste(im, (x, y))
        d.rectangle([x, y, x + W - 1, y + H - 1], outline=(200, 200, 200))
        d.text((x + 6, y + 4), f"view {vs[i]['name']}", fill=(90, 90, 90), font=font)
    if not os.path.isabs(out):
        out = os.path.join(SCRATCH, out)
    sheet.save(out)
    return out
