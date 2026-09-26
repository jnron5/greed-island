"""Keep a palm's trunk still in a PixelLab sway animation, so only the fronds move.

PixelLab's animate_image bends the whole palm even when asked not to. This takes the
animation's frames, keeps frame 0's trunk, coconuts and base in every frame, and lays
each frame's fronds over it, lined up on the coconuts (so the crown stays on the trunk
and only the fronds' own flutter remains).

Usage: python scripts/tools/lock_palm_trunk.py <out strip.png> <frame0.png> <frame1.png> ...
"""
import sys

import numpy as np
from PIL import Image

BASE_ROW = 118          # below this row: the trunk's foot and its grass, never animated
CROWN_ROW = 92          # frame 0's fronds are cut out above this row (the new ones replace them)


def hsv(a):
    rgb = a[..., :3] / 255.0
    mx, mn = rgb.max(-1), rgb.min(-1)
    d = mx - mn + 1e-9
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) / 6
    s = np.where(mx > 0, d / (mx + 1e-9), 0)
    return h, s, mx


def parts(a):
    """Fronds (green), coconuts (bright red) and trunk (brown) masks."""
    h, s, v = hsv(a.astype(float))
    opaque = a[..., 3] > 128
    fronds = opaque & (h > 0.18) & (h < 0.5)
    coconuts = opaque & ((h < 0.03) | (h > 0.95)) & (s > 0.6) & (v > 0.45)
    trunk = opaque & (h > 0.03) & (h < 0.16) & (s > 0.35)
    trunk[:np.nonzero(coconuts)[0].max() + 3] = False       # the trunk starts under the coconuts
    return fronds, coconuts, trunk


def grow(mask, dy, dx):
    out = mask.copy()
    for oy in range(-dy, dy + 1):
        for ox in range(-dx, dx + 1):
            out |= np.roll(mask, (oy, ox), (0, 1))
    return out


def lock(frames):
    first = frames[0]
    fronds0, nuts0, trunk0 = parts(first)
    anchor = np.array(np.nonzero(nuts0)).mean(1)
    keep = grow(trunk0, 1, 2)                                # frame 0's trunk, rings and outline
    base = first.copy()
    cut = (fronds0 | nuts0) & ~keep
    cut[CROWN_ROW:] = False
    base[cut] = 0
    out = []
    for a in frames:
        fronds, nuts, trunk = parts(a)
        dy, dx = np.round(np.array(np.nonzero(nuts)).mean(1) - anchor).astype(int)
        crown = fronds | nuts
        dark = (a[..., 3] > 128) & (a[..., :3].max(-1) < 60)
        crown |= dark & grow(crown, 1, 1)                     # the fronds' dark outline
        crown &= ~grow(trunk, 2, 3)                          # nothing from this frame's own leaning trunk
        crown[BASE_ROW:] = False
        layer = np.roll(np.where(crown[..., None], a, 0), (-dy, -dx), (0, 1))
        layer[keep] = 0
        f = base.copy()
        on = layer[..., 3] > 0
        f[on] = layer[on]
        out.append(f)
    return out


if __name__ == "__main__":
    frames = [np.asarray(Image.open(p).convert("RGBA")) for p in sys.argv[2:]]
    h, w = frames[0].shape[:2]
    strip = Image.new("RGBA", (w * len(frames), h))
    for i, f in enumerate(lock(frames)):
        strip.paste(Image.fromarray(f), (i * w, 0))
    strip.save(sys.argv[1])
    print(f"{sys.argv[1]}: {len(frames)} frames")
