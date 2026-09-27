"""Build the card front and back from Jordan's chosen PixelLab frame (frame A).

Usage: python scripts/tools/build_card_frame.py
Writes assets/cards/frames/card_front.png and card_back.png (112x180).

Front: frame A with its picture window trimmed a little (the plain middle rows are
cut) and a gold-rimmed parchment panel added under the name banner for the card's
description. Back: the same frame with one tall parchment panel for the card's name
and lore. The panels are drawn in frame A's own colours. The rects printed at the
end are the ones scripts/ui/card_view.gd uses.
"""
import os

import numpy as np
from PIL import Image

os.chdir(os.path.join(os.path.dirname(__file__), "..", ".."))

SRC = "assets/cards/frames/frame_a.png"
OUT = "assets/cards/frames/"
CUT = (56, 76)          # window rows removed (all plain side border there)
BAND_AT = 122           # rows from here on (the bottom ornament) move down under the new panel
BAND = 40               # height of the description band
BAND_SOURCE = 50        # the band copies rows from here (beside the window, plain side border)
PLAIN_ROW = 97          # a full-width row of plain teal between the side borders

OUTLINE = (29, 17, 12, 255)
GOLD_LIGHT = (242, 196, 102, 255)
GOLD_DARK = (178, 112, 46, 255)
PARCHMENT = (234, 205, 150, 255)
PARCHMENT_EDGE = (214, 176, 118, 255)


def panel(img, x0, y0, x1, y1):
    """A rimmed parchment panel covering x0..x1, y0..y1 inclusive (1px outline, a
    two-tone gold rim, a slightly darker parchment edge), corners cut by one pixel."""
    a = img
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            d = min(x - x0, x1 - x, y - y0, y1 - y)
            corner = (x in (x0, x1)) and (y in (y0, y1))
            if corner:
                continue
            if d == 0:
                c = OUTLINE
            elif d == 1:
                c = GOLD_LIGHT if (y - y0) < (y1 - y) else GOLD_DARK
            elif d == 2:
                c = GOLD_DARK if (y - y0) < (y1 - y) else GOLD_LIGHT
            elif d == 3:
                c = OUTLINE
            elif d == 4:
                c = PARCHMENT_EDGE
            else:
                c = PARCHMENT
            a[y, x] = c


def main():
    src = np.asarray(Image.open(SRC).convert("RGBA"))
    top = src[:CUT[0]]
    middle = src[CUT[1]:BAND_AT]
    # The band's sides are real frame rows (the plain stretch beside the window), so the
    # border and teal keep their texture; the new panel covers the window part of them.
    band = src[BAND_SOURCE:BAND_SOURCE + BAND]
    bottom = src[BAND_AT:]
    front = np.concatenate([top, middle, band, bottom]).copy()
    band_y = CUT[0] + (BAND_AT - CUT[1])
    # the window's see-through part above and below the new panel becomes plain teal
    rows = front[band_y:band_y + BAND]
    hole = rows[..., 3] == 0
    hole[:, :11] = False
    hole[:, 101:] = False
    rows[hole] = np.broadcast_to(src[PLAIN_ROW], rows.shape)[hole]
    for r in (0, 1, BAND - 2, BAND - 1):                   # no stubs of the old window rim
        rows[r, 17:91] = src[PLAIN_ROW, 17:91]
    text_panel = (17, band_y + 2, 90, band_y + BAND - 3)
    panel(front, *text_panel)
    Image.fromarray(front).save(OUT + "card_front.png")

    back = front.copy()
    window_top = 23
    lore_panel = (17, window_top, 90, text_panel[3])
    # clear the window's transparency and the banner, then one panel over them
    panel(back, *lore_panel)
    Image.fromarray(back).save(OUT + "card_back.png")

    h = front.shape[0]
    win_h = (92 - 26 + 1) - (CUT[1] - CUT[0])
    print(f"size 112x{h}")
    print(f"window Rect2i(21, 26, 66, {win_h})")
    print(f"name_y {110 - (CUT[1] - CUT[0])}")
    print(f"text panel inner Rect2i({text_panel[0] + 5}, {text_panel[1] + 5}, "
          f"{text_panel[2] - text_panel[0] - 9}, {text_panel[3] - text_panel[1] - 9})")
    print(f"lore panel inner Rect2i({lore_panel[0] + 5}, {lore_panel[1] + 5}, "
          f"{lore_panel[2] - lore_panel[0] - 9}, {lore_panel[3] - lore_panel[1] - 9})")


if __name__ == "__main__":
    main()
