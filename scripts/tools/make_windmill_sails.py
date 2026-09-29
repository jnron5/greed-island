"""Kalmora's windmill sails as a turning animation (frames drawn, not a rotated bitmap).

The windmill sprite (kalmora2/objects/windmill2.png) came with its sails painted on;
they were cut out of it (the tower behind them repainted by PixelLab inpaint) and are
drawn here fresh for every frame: four lattice sails on spars round the hub, in the
old sails' wood colours, with a dark outline, so each frame is clean pixel art at
its angle. The sails are four-fold symmetric, so a quarter turn loops.

Writes kalmora2/anim/windmill_sails.png, a horizontal strip of FRAMES frames of
SIZE x SIZE with the hub at the centre.
Run: python scripts/tools/make_windmill_sails.py
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw

os.chdir(os.path.join(os.path.dirname(__file__), "..", ".."))

OUT = "assets/sprites/tiles/kalmora2/anim/windmill_sails.png"
FRAMES = 12
SIZE = 150
HUB = SIZE // 2
REACH = 66           # spar length from the hub
BLADE = (15, 64)     # lattice from this far out to this far
WIDTH = 11           # lattice width, on the trailing side of the spar
# Wood from the old painted sails, dark to light.
OUTLINE = (52, 30, 22, 255)
DARK = (104, 62, 38, 255)
MID = (152, 96, 54, 255)
LIGHT = (196, 138, 78, 255)
CANVAS = (236, 222, 196, 255)
TILT = math.radians(-8)   # the sails lean a touch, like the original


def draw_frame(angle):
    img = Image.new("RGBA", (SIZE, SIZE))
    d = ImageDraw.Draw(img)
    for arm in range(4):
        a = angle + TILT + arm * math.pi / 2
        ux, uy = math.cos(a), math.sin(a)
        px, py = -uy, ux                          # trailing side
        at = lambda r, s: (HUB + ux * r + px * s, HUB + uy * r + py * s)
        # A little sailcloth furled along the inner half of the lattice.
        d.polygon([at(BLADE[0], 2), at(BLADE[0] + 22, 2), at(BLADE[0] + 22, WIDTH - 2), at(BLADE[0], WIDTH - 2)],
                  fill=CANVAS)
        # Lattice frame, cross slats and one long rail.
        d.line([at(BLADE[0], WIDTH), at(BLADE[1], WIDTH)], fill=MID, width=1)
        d.line([at(BLADE[0], WIDTH / 2), at(BLADE[1], WIDTH / 2)], fill=DARK, width=1)
        for r in range(BLADE[0], BLADE[1] + 1, 7):
            d.line([at(r, 0), at(r, WIDTH)], fill=MID, width=1)
        d.line([at(BLADE[1], 0), at(BLADE[1], WIDTH)], fill=MID, width=1)
        # The spar, two pixels thick with a lit edge.
        d.line([at(0, 0), at(REACH, 0)], fill=DARK, width=2)
        d.line([at(2, -0.6), at(REACH - 1, -0.6)], fill=LIGHT, width=1)
    # Dark outline round everything, as the game's sprites have.
    a = np.array(img)
    solid = a[..., 3] > 0
    grown = solid.copy()
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        grown |= np.roll(np.roll(solid, dy, 0), dx, 1)
    ring = grown & ~solid
    a[ring] = OUTLINE
    out = Image.fromarray(a)
    d = ImageDraw.Draw(out)
    d.ellipse([HUB - 5, HUB - 5, HUB + 5, HUB + 5], fill=OUTLINE)
    d.ellipse([HUB - 4, HUB - 4, HUB + 4, HUB + 4], fill=DARK)
    d.ellipse([HUB - 2, HUB - 2, HUB + 1, HUB + 1], fill=LIGHT)
    return out


def main():
    strip = Image.new("RGBA", (SIZE * FRAMES, SIZE))
    for k in range(FRAMES):
        strip.paste(draw_frame(k * (math.pi / 2) / FRAMES), (k * SIZE, 0))
    strip.save(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
