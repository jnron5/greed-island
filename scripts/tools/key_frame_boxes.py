"""python scripts/tools/key_frame_boxes.py <sheet.png> <cell_w> <cell_h>: in each frame cell, a flat opaque
background box (PixelLab sometimes returns one) is flood-filled away from the
box's border."""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

path, cw, ch = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
a = np.array(Image.open(path).convert("RGBA")).astype(int)
H, W = a.shape[:2]
fixed = 0
for y0 in range(0, H, ch):
    for x0 in range(0, W, cw):
        c = a[y0:y0 + ch, x0:x0 + cw]
        op = c[..., 3] > 0
        if not op.any():
            continue
        ys, xs = np.where(op)
        by0, by1, bx0, bx1 = ys.min(), ys.max(), xs.min(), xs.max()
        border = np.concatenate([c[by0, bx0:bx1 + 1], c[by1, bx0:bx1 + 1], c[by0:by1 + 1, bx0], c[by0:by1 + 1, bx1]])
        if (border[:, 3] > 0).mean() < 0.8:
            continue                     # a sprite's own outline, not a box
        border = border[border[:, 3] > 0]
        ref = np.median(border[:, :3], axis=0)
        share = (np.abs(border[:, :3] - ref).max(axis=1) < 14).mean()
        if share < 0.6 or ref.mean() < 90:
            continue
        near = (np.abs(c[..., :3] - ref).max(axis=2) < 16) & op
        lab, _ = ndimage.label(near)
        edge = set(np.unique(np.concatenate([lab[by0, :], lab[by1, :], lab[:, bx0], lab[:, bx1]]))) - {0}
        kill = np.isin(lab, list(edge))
        c[kill, 3] = 0
        fixed += 1
Image.fromarray(a.astype(np.uint8)).save(path)
print(path, "cells fixed:", fixed)
