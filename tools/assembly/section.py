"""Τομή συναρμολόγησης με επίπεδο (κόσμου) και σχέδιο με PIL."""
import json, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from spotgeo import load
from features import slice_loops
from show import SCRATCH, PALETTE

def section(P, W, labels, axis, h, out, scale=4.0, pad=10):
    loops = []
    for i, k in enumerate(labels):
        p = P[k]; M = W[k]
        Vw = p.V @ M[:3,:3].T + M[:3,3]
        if not (Vw[:,axis].min() <= h <= Vw[:,axis].max()): continue
        N = np.cross(Vw[p.F[:,1]]-Vw[p.F[:,0]], Vw[p.F[:,2]]-Vw[p.F[:,0]])
        for lp in slice_loops(Vw, p.F, axis, h, N):
            loops.append((k, i, lp))
    allp = np.vstack([l for _,_,l in loops])
    lo, hi = allp.min(0)-pad, allp.max(0)+pad
    Wd, Hd = int((hi[0]-lo[0])*scale), int((hi[1]-lo[1])*scale)
    im = Image.new('RGB', (Wd, Hd+20*len(labels)), 'white'); d = ImageDraw.Draw(im)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
    used = {}
    for k, i, lp in loops:
        c = tuple(int(255*x) for x in PALETTE[i % len(PALETTE)])
        pts = [((x-lo[0])*scale, Hd-(y-lo[1])*scale) for x,y in lp]
        d.polygon(pts, outline=c)
        used[k] = c
    # grid every 10 mm
    for gx in np.arange(np.ceil(lo[0]/10)*10, hi[0], 10):
        X = (gx-lo[0])*scale; d.line([(X,0),(X,4)], fill=(150,150,150)); d.text((X+1,5), f"{gx:.0f}", fill=(150,150,150), font=font) if int(gx)%50==0 else None
    for gy in np.arange(np.ceil(lo[1]/10)*10, hi[1], 10):
        Y = Hd-(gy-lo[1])*scale; d.line([(0,Y),(4,Y)], fill=(150,150,150)); d.text((6,Y-7), f"{gy:.0f}", fill=(150,150,150), font=font) if int(gy)%50==0 else None
    for j,(k,c) in enumerate(used.items()):
        d.text((5, Hd+3+20*j), k, fill=c, font=font)
    im.save(out); return out

if __name__ == "__main__":
    P = load()
    src = sys.argv[1]
    W = {k: p.M.copy() for k,p in P.items()} if src == 'user' else {k: np.array(v).reshape(4,4) for k,v in json.load(open('placements.json')).items()}
    axis = 'xyz'.index(sys.argv[2]); h = float(sys.argv[3]); labels = sys.argv[4].split(',')
    print(section(P, W, labels, axis, h, f"{SCRATCH}/sec_{src}_{sys.argv[2]}{h:g}.png"))
