"""Cut the PixelLab UI sources (assets/ui/src/) into the pieces the game theme uses.

Usage: python scripts/tools/build_ui_kit.py
Writes assets/ui/*.png. The kit sheet (ui_kit.png) is a PixelLab UI panel set in
the card frame's colours; its pieces are cut by the rects below. The dialogue
panel and name plate were drawn at twice the game's pixel size, so they are halved.
Then run: godot --headless --path . -s scripts/tools/make_theme.gd
"""
import os

import numpy as np
from PIL import Image, ImageEnhance

os.chdir(os.path.join(os.path.dirname(__file__), "..", ".."))

SRC = "assets/ui/src/"
OUT = "assets/ui/"
KIT = {  # name -> rect in ui_kit.png (x0, y0, x1, y1 inclusive)
    "window": (14, 14, 93, 73),        # teal window, shell corners (its title tab is removed below)
    "panel_inset": (14, 142, 93, 198),  # window with an inner inset panel
    "button": (213, 76, 241, 94),
    "slot": (125, 146, 140, 162),
    "slot_round": (125, 98, 140, 114),
    "portrait": (202, 126, 237, 160),
    "medal_shell": (163, 54, 179, 71),
    "medal_star": (183, 54, 199, 71),
    "bar_heart": (13, 204, 67, 217),
    "bar_long": (127, 203, 239, 217),
    "tab_bar": (125, 14, 241, 50),
}


def cut(sheet, rect):
    x0, y0, x1, y1 = rect
    return sheet.crop((x0, y0, x1 + 1, y1 + 1))


def halve(img):
    """Half size for art drawn at 2x: each 2x2 block becomes its most common colour
    (keeps hard pixel edges, no blur)."""
    a = np.asarray(img.convert("RGBA"))
    h, w = a.shape[0] // 2, a.shape[1] // 2
    out = np.zeros((h, w, 4), np.uint8)
    blocks = a[:h * 2, :w * 2].reshape(h, 2, w, 2, 4).transpose(0, 2, 1, 3, 4).reshape(h, w, 4, 4)
    for y in range(h):
        for x in range(w):
            px = [tuple(p) for p in blocks[y, x]]
            out[y, x] = max(set(px), key=px.count)
    return Image.fromarray(out, "RGBA")


def remove_tab(win):
    """The kit's window has a title tab in the middle of its top edge; copy plain top
    edge over it so the window 9-slices cleanly."""
    a = np.asarray(win).copy()
    edge = a[:, 14:18]                      # a plain stretch of the top border
    for x in range(18, a.shape[1] - 18, 4):
        a[:12, x:x + 4] = edge[:12, :min(4, a.shape[1] - 18 - x)]
    return Image.fromarray(a)


def tint(img, brightness=1.0, saturation=1.0):
    alpha = img.getchannel("A")
    rgb = ImageEnhance.Brightness(ImageEnhance.Color(img.convert("RGB")).enhance(saturation)).enhance(brightness)
    rgb = rgb.convert("RGBA")
    rgb.putalpha(alpha)
    return rgb


# The binder (a PixelLab open ring binder with blank see-through pages): pages get
# parchment, and each page six clear sleeves. scripts/ui/binder.gd uses these rects.
BINDER_PAGES = [(48, 22, 275, 297), (299, 22, 526, 297)]
POCKET = (88, 84)
POCKET_COLS = [58, 158, 316, 416]
POCKET_ROWS = [27, 117, 207]


def build_binder():
    img = Image.open(SRC + "binder.png").convert("RGBA")
    a = np.asarray(img).copy()
    rng = np.random.default_rng(4)
    for x0, y0, x1, y1 in BINDER_PAGES:
        region = a[y0:y1 + 1, x0:x1 + 1]
        hole = region[..., 3] == 0
        h, w = hole.shape
        base = np.array([236, 222, 190], np.float32)
        grain = (rng.random((h, w)) - 0.5) * 10 + np.linspace(-6, 6, w)[None, :] * (1 if x0 < 280 else -1)
        paper = np.clip(base[None, None, :] + grain[..., None] * np.array([1, 0.9, 0.7]), 0, 255)
        region[hole, :3] = paper[hole].astype(np.uint8)
        region[hole, 3] = 255
    for px in POCKET_COLS:
        for py in POCKET_ROWS:
            w, h = POCKET
            sleeve = a[py:py + h, px:px + w].astype(np.float32)
            sleeve[..., :3] = sleeve[..., :3] * 0.92 + np.array([200, 222, 236]) * 0.08   # a faint blue sheen
            sleeve[0, :, :3] = sleeve[-1, :, :3] = (150, 160, 170)                         # sleeve edges
            sleeve[:, 0, :3] = sleeve[:, -1, :3] = (150, 160, 170)
            sleeve[1, 1:-1, :3] = (250, 252, 255)                                          # the open top lip
            sleeve[3:-3, 2, :3] = np.minimum(255, sleeve[3:-3, 2, :3] + 18)                  # glint down one side
            a[py:py + h, px:px + w] = sleeve.astype(np.uint8)
    Image.fromarray(a).save(OUT + "binder.png")


def main():
    sheet = Image.open(SRC + "ui_kit.png").convert("RGBA")
    for name, rect in KIT.items():
        piece = cut(sheet, rect)
        if name == "window":
            piece = remove_tab(piece)
        piece.save(OUT + name + ".png")
    ring = np.asarray(Image.open(OUT + "portrait.png")).copy()
    yy, xx = np.mgrid[0:ring.shape[0], 0:ring.shape[1]]
    inside = (xx - 17.5) ** 2 + (yy - 17) ** 2 <= 14.2 ** 2          # the placeholder face inside the ring
    ring[inside] = 0
    Image.fromarray(ring).save(OUT + "portrait.png")
    button = Image.open(OUT + "button.png")
    tint(button, 1.18, 1.1).save(OUT + "button_hover.png")
    tint(button, 0.8).save(OUT + "button_pressed.png")
    tint(button, 0.75, 0.25).save(OUT + "button_disabled.png")
    for name in ("dialogue_panel", "name_plate"):
        img = Image.open(SRC + name + ".png").convert("RGBA")
        img = img.crop(img.getbbox())
        halve(img).save(OUT + name + ".png")
    build_binder()
    for f in sorted(os.listdir(OUT)):
        if f.endswith(".png"):
            print(f, Image.open(OUT + f).size)


if __name__ == "__main__":
    main()
