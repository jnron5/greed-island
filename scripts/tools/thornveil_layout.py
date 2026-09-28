"""Thornveil Forest's layout, traced from the concept docs/reference/thornveil_concept.webp.

Everything here is in the concept's pixel coordinates (1448x1086); build_thornveil.py maps
it to the world. Terrace heights come from the concept's stairs: the north gate strip is
highest, stepping down through the north terrace and the camp to the great-tree plaza,
then down again to the southern lowland. Streams and the lake sit lowest, in rock
channels (their cliff faces are the channel walls). Water and path shapes are read from
the concept's own colours (classify()); terraces are the polygons below.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

CONCEPT = "docs/reference/thornveil_concept.webp"
CW, CH = 1448, 1086
WATER, LOW, MID, HIGH, TERRACE, TOP = 0, 1, 2, 3, 4, 5

# Terraces, painted in this order over the lowland (LOW). Each polygon's edge is the top
# of the cliff face below it (the face itself belongs to the lower ground).
TERRACES = [
    # Each terrace's own shape is generous toward the lower ground; the higher terraces
    # painted after it cut it back to their cliff line, so neighbours never leave a gap.
    (MID, [(380, 300), (1448, 300), (1448, 790), (1300, 796), (1200, 800), (1150, 778), (1100, 770), (1000, 760),
           (900, 758), (860, 720), (840, 712), (760, 716), (700, 708), (650, 668), (600, 640), (540, 622),
           (500, 606), (440, 604), (400, 590), (380, 540), (392, 470), (408, 420)]),
    (HIGH, [(1000, 300), (1448, 300), (1448, 532), (1240, 532), (1240, 480), (1000, 478)]),
    (TERRACE, [(0, 0), (1448, 0), (1448, 318), (1180, 318), (1150, 322), (1080, 328), (1000, 334), (880, 332),
               (800, 312), (760, 344), (700, 348), (640, 342), (560, 330), (452, 318), (420, 280), (380, 238),
               (300, 236), (230, 228), (120, 236), (0, 240)]),
    (TOP, [(344, 0), (1160, 0), (1160, 76), (1020, 76), (1000, 96), (960, 130), (880, 150), (800, 152), (700, 150),
           (600, 150), (500, 142), (430, 132), (380, 120), (344, 110)]),
    (TOP, [(1160, 0), (1448, 0), (1448, 222), (1160, 222)]),
    *[(MID, poly) for poly in ()],
]
# Land standing in the lake, painted after it.
ISLANDS = [
    (MID, [(36, 432), (120, 420), (200, 424), (262, 462), (272, 560), (262, 602), (200, 616), (60, 612),
           (30, 560)]),                                                   # the lake island
    (MID, [(0, 676), (140, 672), (158, 700), (156, 780), (0, 784)]),     # the rock by the west falls
]

# The lake: the one body of water deep enough to sit below every terrace (rock cliffs
# drop into it). Streams elsewhere are painted over the ground (stream_mask()).
LAKE = [(0, 226), (372, 232), (418, 320), (418, 420), (386, 470), (376, 560), (330, 620), (262, 662),
        (200, 700), (160, 690), (0, 684)]

# Ground that stays dry however wide the streams are drawn (painted after the water):
# roads the concept runs right beside a stream.
DRY = [
    (MID, [(1236, 580), (1448, 580), (1448, 650), (1236, 650)]),          # the east road under the shrine
]

# Stairs: (concept x of the flight's centre, concept y of the upper edge, (lower, upper)).
STAIRS = [
    (722, 150, (TERRACE, TOP)),            # down from the north gate
    (724, 344, (MID, TERRACE)),            # north terrace down to the plaza
    (744, 716, (LOW, MID)),                # plaza down to the south road
    (258, 232, (WATER, TERRACE)),          # the camp straight down onto the dock
    (1214, 222, (TERRACE, TOP)),           # north-east hill down to the ridge
    (1214, 320, (HIGH, TERRACE)),          # ridge down to the east rise
    (1026, 478, (MID, HIGH)),              # east rise down to the east road
    (1352, 532, (MID, HIGH)),              # east road up to the Heartwood shrine
    (1126, 776, (LOW, MID)),               # east meadow down to the south-east clearing
]

# Walkable decks over water (concept px rects): the dock and the plank bridges.
# The dock: a narrow zigzag boardwalk (concept px polylines, half-width) from the foot of
# the camp stairs to the plaza road, with a jetty for the rowboat.
DOCKS = [([(258, 290), (258, 388), (320, 388), (320, 440), (368, 440), (368, 494), (412, 494)], 18),
         ([(386, 494), (386, 560)], 16)]
BRIDGES = [  # (x0, y0, x1, y1): a deck across a stream or out to the island
    (360, 176, 440, 200),                  # camp to the north terrace
    (196, 538, 384, 562),                  # the island out to the jetty
    (620, 790, 690, 814),                  # the south-west meadow over the stream
    (1176, 596, 1240, 620),                # east road over the falls
]
# Falls are found where streams cross cliff faces (build_thornveil.find_falls).


def classify():
    """Masks at concept resolution read from the concept's colours: water, path."""
    im = np.asarray(Image.open(CONCEPT).convert("RGB").filter(ImageFilter.MedianFilter(5))).astype(int)
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    water = (b > 140) & (b > r + 60) & (b > g + 10)
    path = (r > 170) & (g > 130) & (b < 110) & (r > g)
    return water, path


def canopy():
    """Where the concept is dense forest (dark, busy greens) rather than open lawn."""
    im = Image.open(CONCEPT).convert("RGB")
    a = np.asarray(im.filter(ImageFilter.GaussianBlur(10))).astype(float)
    lum = a[..., 0] * 0.3 + a[..., 1] * 0.59 + a[..., 2] * 0.11
    return lum < 88


def drop_specks(mask, min_px):
    """The mask without its small separate blobs (the gates' blue banners, glints)."""
    step = 4
    small = mask[::step, ::step].copy()
    h, w = small.shape
    seen = np.zeros_like(small)
    for y0 in range(h):
        for x0 in range(w):
            if small[y0, x0] and not seen[y0, x0]:
                seen[y0, x0] = True
                blob, stack = [(y0, x0)], [(y0, x0)]
                while stack:
                    y, x = stack.pop()
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < h and 0 <= nx < w and small[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            blob.append((ny, nx))
                            stack.append((ny, nx))
                if len(blob) * step * step < min_px:
                    for y, x in blob:
                        mask[y * step:(y + 1) * step, x * step:(x + 1) * step] = False
    return mask


def _poly_mask(poly):
    m = Image.new("L", (CW, CH), 0)
    ImageDraw.Draw(m).polygon(poly, fill=1)
    return np.asarray(m).astype(bool)


def wet_mask():
    """Every water pixel of the concept, cleaned of specks, streams opened up a little."""
    water, _ = classify()
    m = Image.fromarray(water.astype(np.uint8) * 255)
    m = m.filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.MinFilter(5)).filter(ImageFilter.MaxFilter(5))
    return drop_specks(np.asarray(m) > 0, 1800)


def stream_mask():
    """Streams: water outside the lake, painted over whatever terrace they cross."""
    wet = wet_mask()
    lake = _poly_mask(LAKE)
    for level, poly in DRY:
        wet &= ~_poly_mask(poly)
    return wet & ~lake


def level_image():
    """The terrace heights at concept resolution (one byte per pixel)."""
    img = Image.new("L", (CW, CH), LOW)
    d = ImageDraw.Draw(img)
    for level, poly in TERRACES:
        d.polygon(poly, fill=level)
    lv = np.asarray(img).copy()
    lake = _poly_mask(LAKE) | (wet_mask() & _poly_mask([(0, 240), (430, 240), (430, 700), (0, 700)]))
    lv[lake] = WATER
    for level, poly in DRY:
        lv[_poly_mask(poly)] = level
    for level, poly in ISLANDS:
        lv[_poly_mask(poly)] = level
    return lv
