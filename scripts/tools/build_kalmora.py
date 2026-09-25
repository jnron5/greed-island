"""Build Kalmora, Port of Beginnings: a lush, multilevel harbor town.

Usage: python scripts/tools/build_kalmora.py
Writes the ground image, the level map, and scenes/world/kalmora.tscn (the
whole scene is generated: edit the layout here, not in the editor).

The layout is traced from the concept art in docs/reference/kalmora_concept_c.webp:
everything below is written in the concept's own pixel coordinates (1536x1024)
and mapped to the world at 1.4x (W()), so positions can be read straight off it.

Levels (tile-corner heightmap, see terrain.py):
  0 sea         water, plus dry sea-level ground painted over it: the plank
                docks, the beach, the sandy islet (and the canal bridges)
  1 harbor      the quay under the square, where the docks tie up
  2 town        the fountain square, shops, market, the west meadow with the
                windmill, the lighthouse headland, the band under the hill houses
  3 upper       the forest band with the north gate, the north-east hill houses
Tall cliffs drop straight from town to sea (rock on the coasts, dressed stone
under the market); a canal runs from under the hill down to the beach.
"""
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

os.chdir(os.path.join(os.path.dirname(__file__), "..", ".."))

from terrain import CliffSet, CornerSet, compose, merge_rects, overlay  # noqa: E402

TILE = 32
SCALE = 1.4                                    # world px per concept px
LEFT, TOP, RIGHT, BOTTOM = -1088, -736, 1088, 704
COLS, ROWS = (RIGHT - LEFT) // TILE, (BOTTOM - TOP) // TILE
SEA, HARBOR, TOWN, UPPER = 0, 1, 2, 3

ART = "assets/sprites/tiles/kalmora2/"
OBJ = ART + "objects/"
GROUND_PNG = ART + "kalmora_ground.png"
LEVEL_PNG = ART + "kalmora_levels.png"
SCENE = "scenes/world/kalmora.tscn"
GATE_Y = TOP + 104                             # the north gate; only way out of town

# Cliff heights: extra wall rows per pair of levels that meet.
WALL_EXTRA = {(0, 1): 0, (0, 2): 0, (0, 3): 0, (1, 2): 1, (1, 3): 2, (2, 3): 1}   # grow up, into the plateau
WALL_DOWN = {(0, 2): 2, (0, 3): 3}                                            # grow down, over the sea


def W(cx, cy):
    """Concept pixel -> world position."""
    return (round(LEFT + cx * SCALE), round(TOP + cy * SCALE))


def C(x, y):
    """World position -> concept pixel."""
    return ((x - LEFT) / SCALE, (y - TOP) / SCALE)


# ------------------------------------------------------------------ terrain (concept px)
def wob(v, amp, period, phase=0.0):
    """A gentle, irregular wave for natural coastlines (built walls stay straight)."""
    return amp * (0.6 * math.sin(v / period + phase) + 0.4 * math.sin(v / (period * 0.37) + 2 * phase))


def level_c(cx, cy):
    if 1104 <= cx <= 1168 and 224 <= cy <= 480:
        return SEA                                        # the canal
    if cy <= 176 and cx >= 336:
        return UPPER                                      # forest band with the north gate
    if 1200 <= cx <= 1440 + wob(cy, 14, 30) and cy <= 336:
        return UPPER                                      # north-east hill houses
    if cx < 336:
        if cy <= 512 + wob(cx, 16, 45, 1):
            return TOWN                                   # west meadow over tall sea cliffs
        if ((cx - 136) / 128) ** 2 + ((cy - 830) / 96) ** 2 <= 1 + 0.18 * math.sin(cx / 19) * math.cos(cy / 23):
            return HARBOR                                 # forested rock islet
        return SEA
    if cx <= 1104 and cy <= (560 if cx >= 384 else 544):
        return TOWN                                       # the town around the square
    if 832 <= cx <= 1104 and cy <= 704:
        return TOWN                                       # market, over the harbor wall
    east = 1456 + wob(cy, 16, 38, 2)                      # the rocky east coast
    if cx >= 1104 and 640 < cy <= 704:
        return TOWN if cx <= east else SEA                # neck of the lighthouse headland
    if cx >= 1152 + wob(cy, 10, 30) and 704 < cy <= 832 + wob(cx, 14, 36, 3):
        return TOWN if cx <= east else SEA                # the lighthouse headland
    if cx > 1104 and cy <= 440 + wob(cx, 8, 30, 4):
        return TOWN if cx <= east else SEA                # canal's east bank, band under the hill
    return SEA


def level_at(x, y):
    return level_c(*C(x, y))


def harbor_wall(r, c):
    """Dressed stone walls along the harbor and under the market; rock elsewhere."""
    cx, cy = C(LEFT + c * TILE, TOP + r * TILE)
    return 368 <= cx <= 1112 and 520 <= cy <= 760


# Dry ground painted over sea level (concept px).
def sand_c(cx, cy):
    return (cy >= 440 and ((cx - 1300) / 176) ** 2 + ((cy - 520) / 150) ** 2 <= 1  # the beach, a crescent cove
            and not ((cx - 1330) / 120) ** 2 + ((cy - 700) / 70) ** 2 <= 1)


def planks_c(cx, cy):
    return (368 <= cx <= 840 and 560 <= cy <= 772                              # the long deck under the square
            or 840 <= cx <= 968 and 712 <= cy <= 772                           # deck under the market wall
            or 600 <= cx <= 672 and 772 <= cy <= 872                           # pier by the ship
            or 900 <= cx <= 968 and 772 <= cy <= 980)                          # the long pier


def sand(x, y):
    return sand_c(*C(x, y))


def planks(x, y):
    return planks_c(*C(x, y))


# Canal bridges (concept px): walkable at town level, decked with planks.
BRIDGES = [(1088, 272, 1184, 280), (1088, 344, 1184, 352)]

# Garden beds inside the paved town (concept px): lawns with bushes and palms.
BEDS = [(640, 384, 704, 432), (832, 384, 896, 432), (624, 496, 688, 528), (848, 496, 912, 528),
        (512, 192, 624, 240), (672, 192, 736, 240), (816, 192, 896, 240), (1040, 192, 1088, 336),
        (1040, 400, 1088, 448), (352, 256, 400, 496), (352, 192, 448, 224)]


def in_rect(cx, cy, r):
    return r[0] <= cx <= r[2] and r[1] <= cy <= r[3]


def paved_c(cx, cy):
    lv = level_c(cx, cy)
    if lv == HARBOR:
        return cx >= 336                                           # the islet is wild
    if lv == TOWN:
        if cx < 336:
            return False                                           # the meadow
        if cx > 1168 and cy > 336 and 592 >= cy:
            return 1280 <= cx <= 1328                               # path down to the beach stairs
        if cx >= 1152 and cy > 704:
            return 1248 <= cx <= 1296 or cy <= 736                  # the headland: a path to the lighthouse
        return not any(in_rect(cx, cy, b) for b in BEDS)
    if lv == UPPER:
        return (cx >= 1184 and (144 <= cy <= 176 or 272 <= cy <= 304)   # hill lanes
                or 1232 <= cx <= 1264 and cy >= 144)
    return True


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return ((px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2) ** 0.5


# Dirt paths (concept px polylines, half-width): the north road and the meadow's tracks.
PATHS = [
    ([(768, 0), (768, 176)], 28),
    ([(0, 208), (96, 200), (208, 212), (296, 244), (340, 284), (352, 330)], 24),
    ([(0, 336), (128, 346), (240, 370), (330, 396)], 23),
    ([(300, 0), (318, 64), (352, 118), (416, 168)], 24),
]


def dirt_c(cx, cy):
    return any(seg_dist(cx, cy, *a, *b) <= w for pts, w in PATHS for a, b in zip(pts, pts[1:]))


# Stairs: (concept x of the left edge, concept y of the plateau edge, (lower, upper) levels).
STAIRS = [
    (722, 560, (0, 2)), (768, 560, (0, 2)),       # grand stairs: square down to the deck
    (752, 176, (2, 3)),                           # the gate road down into town
    (416, 176, (2, 3)),                           # the west gate
    (1232, 336, (2, 3)),                          # the hill houses down to the band
    (1296, 440, (0, 2)),                          # band down to the beach
]


def stair_rows(pair):
    return 2 + WALL_EXTRA[pair] + WALL_DOWN.get(pair, 0)


STAIR_SPOTS = []   # (column, first row, rows) per stairs, resolved against the level grid


def resolve_stairs(levels):
    """Each stairs is given roughly in concept px; find the actual plateau edge in its
    column (the last vertex row of the upper level above the lower one) and cut the
    flight through the wall rows around it."""
    STAIR_SPOTS.clear()
    for cx, cy, (lo, hi) in STAIRS:
        x, y = W(cx, cy)
        c0 = int((x - LEFT) // TILE)
        guess = round((y - TOP) / TILE)
        edge = next((r for r in sorted(range(guess - 4, guess + 5), key=lambda r: abs(r - guess))
                     if all(levels[r][c] == hi and levels[r + 1][c] == lo for c in (c0, c0 + 1, c0 + 2))), None)
        if edge is None:
            raise SystemExit(f"stairs at concept ({cx}, {cy}): no {hi}->{lo} edge near there")
        STAIR_SPOTS.append((c0, edge - WALL_EXTRA[(lo, hi)], stair_rows((lo, hi))))


def stair_cells():
    return {(r0 + dr, c0 + dc) for c0, r0, rows in STAIR_SPOTS for dr in range(rows) for dc in (0, 1)}


def bridge_cells():
    cells = set()
    for x0, y0, x1, y1 in BRIDGES:
        (wx0, wy0), (wx1, wy1) = W(x0, y0), W(x1, y1)
        for c in range((wx0 - LEFT) // TILE, (wx1 - 1 - LEFT) // TILE + 1):
            for r in range((wy0 - TOP) // TILE, (wy1 - 1 - TOP) // TILE + 1):
                cells.add((r, c))
    return cells


def deepen_greens(img):
    """PixelLab's grass comes out neon; pull it toward the concept's deep, warm greens."""
    a = np.asarray(img).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    grass = (g > r + 18) & (g > b + 18)
    out = a.copy()
    out[..., 0] = np.where(grass, r * 0.35 + g * 0.30 + 2, r)
    out[..., 1] = np.where(grass, g * 0.72 + 2, g)
    out[..., 2] = np.where(grass, b * 0.20 + g * 0.24 + 2, b)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")


def grade_ground(img, stand, wet, natural):
    """Match the concept's palette: warm, light paving on flat ground (walls keep their
    grey stone); calmer water with turquoise shallows along the shore."""
    a = np.asarray(img).astype(np.float32)
    cells = np.array([[1 if v >= HARBOR else 0 for v in row] for row in stand], np.uint8)
    water = np.array([[1 if wet(r, c) else 0 for c in range(len(row))] for r, row in enumerate(stand)], np.uint8)
    land_px = np.kron(cells, np.ones((TILE, TILE), np.uint8)).astype(bool)
    water_px = np.kron(water, np.ones((TILE, TILE), np.uint8)).astype(bool)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    grey = (np.abs(r - g) < 28) & (np.abs(g - b) < 34) & ~((g > r + 18) & (g > b + 18))
    pave = land_px & grey
    # Lighter plaza paving around the fountain, fading out over ~200px.
    fx, fy = W(*FOUNTAIN)
    yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    plaza = np.clip(1.0 - np.hypot(xx - (fx - LEFT), (yy - (fy - 60 - TOP)) * 1.15) / 210.0, 0, 1) * 16
    for i, (mul, add) in enumerate(((1.45, 25), (1.35, 20), (1.2, 19))):
        a[..., i] = np.where(pave, a[..., i] * mul + add + plaza, a[..., i])
    lum = 0.3 * r + 0.59 * g + 0.11 * b
    fleck = water_px & (lum > 120)
    deep = np.array([34, 88, 168], np.float32)
    for i in range(3):
        a[..., i] = np.where(fleck, a[..., i] * 0.3 + deep[i] * 0.7, a[..., i])
    # Shallows only against natural shores (sand, rock), not docks or harbor walls.
    shore = np.array([[1 if natural(r, c) else 0 for c in range(len(row))] for r, row in enumerate(stand)], np.uint8)
    shore_px = np.kron(shore, np.ones((TILE, TILE), np.uint8))
    near = Image.fromarray((shore_px * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(28))
    w = np.clip(np.asarray(near).astype(np.float32) / 255.0 * 1.3, 0, 0.5) * water_px
    shallow = np.array([46, 158, 186], np.float32)
    for i in range(3):
        a[..., i] = a[..., i] * (1 - w) + shallow[i] * w
    # The concept's sea is a calm, bright teal: smooth the tile's busy pattern and shift the hue.
    smooth = np.asarray(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA").filter(ImageFilter.GaussianBlur(3))).astype(np.float32)
    for i in range(3):
        a[..., i] = np.where(water_px, a[..., i] * 0.72 + smooth[..., i] * 0.28, a[..., i])
    for i, (mul, add) in enumerate(((0.95, 0), (1.26, 12), (1.0, 8))):
        a[..., i] = np.where(water_px, a[..., i] * mul + add, a[..., i])
    out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
    # A touch more saturation and contrast overall, like the concept's.
    from PIL import ImageEnhance
    alpha = out.getchannel("A")
    out = ImageEnhance.Contrast(ImageEnhance.Color(out.convert("RGB")).enhance(1.18)).enhance(1.08).convert("RGBA")
    out.putalpha(alpha)
    return out


def build_terrain():
    levels = [[level_at(LEFT + c * TILE, TOP + r * TILE) for c in range(COLS + 1)] for r in range(ROWS + 1)]
    quay, rock = CliffSet(ART + "cliff/sea_quay"), CliffSet(ART + "cliff/sea_rock")
    quay_town, town_upper = CliffSet(ART + "cliff/quay_town"), CliffSet(ART + "cliff/town_upper")
    coast = lambda r, c: quay if harbor_wall(r, c) else rock
    sets = {(0, 1): coast, (0, 2): coast, (0, 3): rock, (1, 2): quay_town, (1, 3): quay_town, (2, 3): town_upper}
    flat = {SEA: ((0, 1), "lower"), HARBOR: ((1, 2), "lower"), TOWN: ((1, 2), "upper"), UPPER: ((2, 3), "upper")}
    img, stand = compose(levels, sets, flat, TILE, extra_wall_rows=WALL_EXTRA, grow_down=WALL_DOWN)
    resolve_stairs(levels)

    # Surfaces: cobbles vs. grass on every land level (each level's own base terrain is
    # left alone), dirt tracks, then sand and planks over the sea.
    grass, dirt = CornerSet(ART + "wang/grass"), CornerSet(ART + "wang/dirt")
    lawn = lambda x, y: not paved_c(*C(x, y))
    overlay(img, stand, HARBOR, grass, lawn, LEFT, TOP, TILE)
    overlay(img, stand, TOWN, grass, lawn, LEFT, TOP, TILE, base_is_upper=True)
    overlay(img, stand, UPPER, grass, lawn, LEFT, TOP, TILE)
    track = lambda x, y: dirt_c(*C(x, y)) and not paved_c(*C(x, y))
    overlay(img, stand, TOWN, dirt, track, LEFT, TOP, TILE)
    overlay(img, stand, UPPER, dirt, track, LEFT, TOP, TILE)
    overlay(img, stand, SEA, CornerSet(ART + "wang/sand"), sand, LEFT, TOP, TILE)
    boards = CornerSet(ART + "wang/planks")
    overlay(img, stand, SEA, boards, planks, LEFT, TOP, TILE)
    bridges = bridge_cells()
    for r, c in bridges:
        img.paste(boards.tiles[15], (c * TILE, r * TILE))
    img = deepen_greens(img)

    stairs = stair_cells()

    def corners(r, c):
        x, y = LEFT + c * TILE, TOP + r * TILE
        return [(x, y), (x + TILE, y), (x, y + TILE), (x + TILE, y + TILE)]

    def dry(r, c):
        """Sea-level cells you can stand on: fully sand or fully planks."""
        pts = corners(r, c)
        return all(sand(*p) for p in pts) or all(planks(*p) for p in pts)

    def wet(r, c):
        """Open water: sea-level cells with no sand or planks at any corner."""
        return stand[r][c] == SEA and (r, c) not in bridges and not any(sand(*p) or planks(*p) for p in corners(r, c))

    def natural(r, c):
        """Shore that isn't built: sand, rock cliffs and land away from the harbor."""
        if wet(r, c) or (r, c) in bridges:
            return False
        if stand[r][c] == SEA:
            return any(sand(*p) for p in corners(r, c))
        return not harbor_wall(r, c)

    img = grade_ground(img, stand, wet, natural)
    walkable = [[(stand[r][c] > SEA or stand[r][c] == SEA and dry(r, c) or (r, c) in stairs or (r, c) in bridges)
                 for c in range(COLS)] for r in range(ROWS)]
    blocked = [[not walkable[r][c] for c in range(COLS)] for r in range(ROWS)]

    # Level map: red = level * 40 (255 = cliff/stairs, any level); green = dry sea-level
    # ground, so the water shimmer skips beaches and docks.
    lm = Image.new("RGB", (COLS, ROWS))
    for r in range(ROWS):
        for c in range(COLS):
            v = stand[r][c]
            if (r, c) in stairs or (v < 0 and (r, c) not in bridges):
                lm.putpixel((c, r), (255, 0, 0))
            elif (r, c) in bridges:
                lm.putpixel((c, r), (TOWN * 40, 255, 0))
            else:
                lm.putpixel((c, r), (v * 40, 255 if v == SEA and walkable[r][c] else 0, 0))
    lm.save(LEVEL_PNG)
    return img, stand, blocked, stairs


def build_stairs():
    """Stretch the grey stone stairs sprite to each flight height by repeating its
    middle steps, so the treads keep their pixel size."""
    src = Image.open(OBJ + "stairs.png").convert("RGBA")
    src = src.crop(src.getbbox())
    w, h = src.size
    paths = {}
    for rows in {stair_rows(p) for _, _, p in STAIRS}:
        target = rows * TILE
        top, bottom = src.crop((0, 0, w, 14)), src.crop((0, h - 14, w, h))
        mid = src.crop((0, 14, w, h - 14))
        body = Image.new("RGBA", (w, target - 28))
        for y in range(0, body.height, mid.height):
            body.paste(mid, (0, y))
        flight = Image.new("RGBA", (w, target))
        flight.paste(top, (0, 0)); flight.paste(body, (0, 14)); flight.paste(bottom, (0, target - 14))
        out = Image.new("RGBA", (2 * TILE, target))
        out.paste(flight, ((2 * TILE - w) // 2, 0))
        paths[rows] = f"{ART}stairs_{rows}.png"
        out.save(paths[rows])
    return paths


# ------------------------------------------------------------------ content (concept px)
# (node, sprite, concept position = footprint bottom-centre, footprint width in world px)
BUILDINGS = [
    ("RedHouse", "townhouse_red", (455, 348), 120),
    ("GeneralStore", "general_store", (590, 400), 170),
    ("Blacksmith", "blacksmith", (478, 490), 160),
    ("Tavern", "inn", (930, 400), 190),
    ("NorthHouse", "house_blue", (990, 252), 170),
    ("CardShop", "item_shop", (1034, 520), 150),
    ("Harbormaster", "harbormaster2", (440, 700), 140),
    ("Warehouse", "warehouse", (560, 700), 170),
    ("BlueCottage", "cottage_blue", (1150, 136), 140),
    ("NonnaHouse", "cottage_red", (1328, 136), 130),
    ("HillHouse", "townhouse_blue", (1318, 262), 100),
    ("TealHouse", "townhouse_teal", (1400, 262), 96),
    ("Windmill", "windmill", (230, 344), 110),
]
# Enterable buildings: node -> (door x offset from the building, interior scene).
DOORS = {
    "Tavern": (0, "res://scenes/world/interiors/kalmora_tavern.tscn"),
    "CardShop": (0, "res://scenes/world/interiors/kalmora_card_shop.tscn"),
    "NonnaHouse": (0, "res://scenes/world/interiors/kalmora_nonna_house.tscn"),
}
# Residents (dogs and cats). (id, name, sprite id, concept position, wander radius, lines)
NPCS = [
    ("bram", "Bram", "bram", (640, 700), 0, ["Tide's good today. Good for ships, anyway."]),
    ("mirela", "Harbormaster Mirela", "mirela", (490, 712), 0, [
        "Manifests, manifests. Everything that lands in Kalmora gets a stamp. Everything.",
        "The race? The whole island's talking. Somebody's walking into Vetrassa with a full set, mark my words.",
    ]),
    ("pip", "Pip", "pip", (880, 640), 30, [
        "Fresh fish! Well. Fresh-ish.",
        "My cousin went to work out in Duskara last spring. Good pay, they said. He hasn't written.",
    ]),
    ("sailor", "Deckhand Luca", "sailor", (780, 740), 40, [
        "Sailed round the whole isle once. Vetrassa's got the tallest spires you ever saw.",
        "You racers bind your cards in town, right? Thieves love a loose card on the road.",
    ]),
    ("baker", "Baker Rosa", "baker", (640, 420), 30, [
        "Warm bread! Two coins a loaf, one if you tell me a good rumor.",
        "The Runner came through at dawn, all scarf and no manners. Didn't even stop for bread.",
    ]),
    ("tomas", "Keeper Tomas", "tomas", (1220, 690), 0, [
        "Lost my lighthouse wick somewhere up on the hill houses. Can't light the lamp without it.",
        "That lens up there's worth more than my whole cottage. Door stays locked, wick or no wick.",
    ]),
    ("rook", "Guard Rook", "rook", (808, 92), 0, [
        "North road's sealed. A Salt Compass opens it. Old rule, nobody remembers why.",
        "Thornveil's no place to wander with loose cards. The hounds don't care, but the Raider does.",
    ]),
]
# The unmarked shipment: three crates piled on the quay, where Bram works.
CLUE_CRATES = [("crate_sand", (680, 700)), ("crate_glove", (700, 690)), ("crate_ledger", (714, 704))]
CARDS = [  # (card, concept position)
    ("harbor_lantern", (400, 740)), ("coral_coin", (1330, 540)), ("gull_feather", (1310, 740)),
    ("sea_glass", (1400, 560)), ("sunken_crown_shard", (934, 935)),
    ("salt_compass", (150, 280)), ("tide_bell", (1000, 600)), ("terracotta_tile", (560, 216)),
    ("lighthouse_wick", (1390, 290)), ("fishers_knot", (636, 850)),
]
EXTRA_SALT_COMPASS = (60, 400)
DUMMIES = [(80, 420), (130, 420), (180, 420)]           # a sparring spot in the meadow
RIVAL_SPOTS = {"runner": (200, 420), "raider": (1300, 160), "hoarder": (950, 560)}
SPAWNS = {"town": (768, 520), "from_thornveil": (768, 91)}
LIGHTHOUSE = (1290, 740)      # yard centre; the gate faces north toward the market
MERCHANT = (880, 600)
FOUNTAIN = (768, 486)

PALM, TREE, PINE = "palm_g", "tree_g", "pine"


def grid(xs, ys):
    return [(x, y) for x in xs for y in ys]


# Trees: (sprite, concept position). The forest band and the meadow's edges are dense.
def forest(x0, y0, x1, y1, spacing, seed, keep_clear=()):
    """A dense, staggered stand of trees whose canopies overlap, like the concept's
    forests; keep_clear rects (concept px) stay open for roads and houses."""
    rng = random.Random(seed)
    out, j, y = [], 0, y0
    while y <= y1:
        x = x0 + (j % 2) * spacing / 2
        while x <= x1:
            px, py = x + rng.uniform(-0.22, 0.22) * spacing, y + rng.uniform(-0.2, 0.2) * spacing
            if not any(in_rect(px, py, r) for r in keep_clear):
                out.append((TREE, (round(px), round(py))))
            x += spacing
        y += spacing * 0.72
        j += 1
    return out


HOUSE_CLEAR = [(1060, 20, 1240, 160), (1240, 20, 1420, 160), (720, 0, 816, 180), (380, 90, 460, 190)]
TREES = (
    forest(350, 18, 1196, 150, 40, 1, HOUSE_CLEAR)                    # the forest band over the town
    + forest(10, 18, 330, 110, 42, 2, [(270, 0, 340, 130)])           # woods above the meadow
    + forest(1180, 8, 1520, 30, 40, 3)                                # trees behind the hill houses
    + forest(20, 740, 250, 900, 44, 4)                                # the forested islet
    + [(TREE, (x, y)) for x, y in [(30, 250), (80, 270), (40, 480), (300, 470), (260, 150), (180, 150),
                                   (20, 150), (300, 420)]]
    + [(PINE, (x, y)) for x, y in [(150, 240), (190, 270), (100, 450), (240, 470), (320, 300), (320, 250)]]
    # The town: palms around the square, trees in the gardens.
    + [(PALM, p) for p in [(660, 426), (880, 426), (650, 526), (872, 526), (700, 240), (860, 240),
                           (1060, 330), (1062, 440), (1180, 230), (1180, 420), (380, 480), (380, 300)]]
    + [(TREE, p) for p in [(540, 236), (600, 236), (832, 236), (390, 220)]]
    # Market, headland and beach.
    + [(PALM, p) for p in [(1150, 690), (1200, 760), (1400, 720), (1430, 620), (1170, 520), (1400, 540),
                           (1190, 810), (1300, 820)]]
    # The hill: trees behind and between the houses, forest on the band's cliff.
    + [(TREE, p) for p in [(1230, 60), (1420, 60), (1240, 230), (1450, 200)]]
    + [(TREE, p) for p in [(1200, 400), (1250, 420), (1360, 400), (1410, 430), (1440, 380)]]
)


def row(name, x0, x1, y, step):
    return [(name, x, y) for x in range(x0, x1 + 1, step)]


def track_fences():
    """Split-rail fences along both sides of the meadow tracks, on their flatter
    stretches (the rail sprite is horizontal), like the concept's fenced fields."""
    out = []
    for pts, w in PATHS[1:]:
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            if abs(by - ay) > 0.4 * abs(bx - ax):
                continue
            steps = max(1, int(abs(bx - ax) // 22))
            for k in range(steps + 1):
                t = k / steps
                x, y = ax + (bx - ax) * t, ay + (by - ay) * t
                if x < 330:
                    out += [("fence", round(x), round(y - w - 6)), ("fence", round(x), round(y + w + 10))]
    return out


STALLS = ["stall_fruit", "stall_fish", "stall_pottery", "stall_bread"]
# Props: (name, concept x, concept y), grouped by where a resident would put them.
PROPS = (
    # The fountain square: banners on its rim, flower beds, benches.
    [("banner", x, y) for x, y in [(700, 408), (836, 408), (700, 540), (836, 540), (712, 330), (824, 330)]]
    + [("flower_bed", x, y) for x, y in [(690, 460), (846, 460)]]
    + [("bench", x, 484) for x in (724, 812)]
    # Shop fronts.
    + [("apples_crate", 552, 410), ("oranges_basket", 628, 410), ("sack", 540, 420)]
    + [("parasol_table", 880, 420), ("parasol_table", 980, 420), ("menu_board", 900, 404)]
    + [("barrel", 430, 512), ("barrels", 418, 520), ("crates", 530, 512)]
    + [("potted_palm", 996, 526), ("potted_palm", 1072, 526)]
    # Market stalls east of the square, in rows.
    + [(STALLS[k % 4], x, y) for k, (x, y) in enumerate([(880, 560), (960, 560), (1040, 590), (900, 660),
                                                          (980, 660), (1060, 670)])]
    + [("fish_crates", 840, 600), ("crates", 1080, 610), ("amphorae", 940, 610), ("lemons_crate", 1010, 620)]
    # The quay and the deck.
    + [("anchor", 740, 590), ("rope", 700, 600), ("crates", 400, 660), ("barrels", 430, 690),
       ("fish_crates", 520, 700), ("barrel", 760, 700), ("crates", 780, 680), ("net_crate", 600, 700)]
    # The west meadow: fenced fields around the windmill.
    + track_fences()
    + [("flower_bed", x, y) for x, y in [(60, 262), (110, 262), (70, 360), (120, 360)]]
    + [("wheelbarrow", 270, 360), ("signpost", 24, 344), ("cart", 16, 300)]
    # Beach and headland.
    + [("parasol_table", 1340, 520), ("boulder", 1250, 560), ("bench", 1370, 660), ("candle_shrine", 1430, 700)]
    # The hill: flowers at doors, gardens between the houses.
    + [("flower_bed", x, y) for x, y in [(1110, 150), (1190, 150), (1290, 150), (1370, 150), (1270, 276), (1440, 276)]]
    + [("laundry_line", 1210, 240), ("bush_flowers_g", 1450, 150)]
    # Gate band.
    + [("flower_bed", x, 160) for x in (720, 820)]
)
# Packing: the concept piles goods, flowers and planters into every gap (concept px).
CLUTTER = (
    # Cargo along the deck and out on the piers.
    [("crates", 386, 736), ("barrel", 404, 752), ("barrels", 470, 760), ("fish_crates", 520, 762),
     ("crates", 600, 758), ("rope", 640, 764), ("barrels", 700, 762), ("crate", 740, 756), ("amphorae", 800, 760),
     ("lobster_trap", 830, 744), ("buoy", 850, 760), ("crates", 616, 856), ("barrel", 650, 840),
     ("barrel", 920, 820), ("crate", 950, 900), ("net_crate", 930, 960)]
    # Goods between the market stalls.
    + [("crates", 860, 690), ("barrels", 1000, 690), ("amphorae", 1090, 650), ("fish_crates", 940, 700),
       ("apples_crate", 1040, 560), ("oranges_basket", 1100, 580), ("sack", 920, 600), ("lemons_crate", 1060, 620)]
    # Flowers at the doors of the houses.
    + [("flower_bed", x, y) for x, y in [(1120, 146), (1180, 146), (1298, 146), (1358, 146), (1290, 272),
                                         (1430, 272), (955, 262), (1025, 262)]]
    + [("bush_flowers_g", x, y) for x, y in [(425, 356), (485, 356), (650, 470), (886, 470)]]
    # The beach, the meadow, and the gate band.
    + [("parasol_table", 1250, 610), ("parasol_table", 1380, 620), ("boulder", 1420, 600)]
    + [("bush_flowers_g", x, y) for x, y in [(40, 232), (200, 222), (90, 332), (250, 342)]]
    + [("crates", 200, 352), ("sack", 212, 364)]
    + [("bush_g", x, 166) for x in (400, 500, 600, 900, 1000)]
    # Rocks and greenery along the canal banks and around the hill houses.
    + [("boulder", x, y) for x, y in [(1086, 250), (1188, 310), (1086, 420), (1190, 400), (1230, 210), (1450, 250),
                                      (1210, 330)]]
    + [("bush_flowers_g", x, y) for x, y in [(1086, 300), (1190, 250), (1088, 470)]]
)
SMALL = {"crate", "barrel", "sack", "flour_sack", "rope", "buoy", "bucket", "lobster_trap", "apples_crate",
         "oranges_basket", "lemons_crate", "amphora"}
# Bushes packed along walls, beds and building sides (concept px).
BUSHES = (
    [(x, 250) for x in (520, 560, 610, 680, 740, 800, 850)]
    + [(x, 380) for x in (600, 640, 900, 940)] + [(x, 536) for x in (600, 680, 860, 920)]
    + [(380, 380), (390, 420), (1060, 260), (1070, 380), (1090, 460), (1180, 300), (1180, 180)]
    + [(1210, 400), (1300, 440), (1430, 450), (1220, 700), (1290, 780), (1420, 790), (1180, 760)]
    + [(170, 480), (60, 170), (230, 190), (300, 380), (10, 420)]
    + [(1110, 60), (1200, 110), (1440, 110), (1180, 250), (1380, 330)]
)
# Free sprites (y-sorted, no collision): boats and rocks out on the water (concept px).
# Bridge railings: split rails along both sides of each canal crossing (drawn only).
RAILS = [("fence", x, y) for x0, y0, x1, y1 in BRIDGES for x in range(x0 + 8, x1, 22) for y in (y0 - 3, y1 + 11)]
FLOATING = RAILS + [("ship", 470, 960), ("rowboat", 250, 650), ("rowboat", 1210, 652), ("rowboat", 1010, 880), ("rowboat", 870, 960),
            ("sea_rocks", 1480, 700), ("sea_rocks", 1470, 860), ("sea_rocks", 1300, 900), ("sea_rocks", 1100, 900),
            ("sea_rocks", 60, 560), ("sea_rocks", 230, 580), ("sea_rocks", 1500, 420), ("sea_rocks", 280, 760)]
LAMPS = ([(x, y) for x, y in [(690, 380), (846, 380), (690, 560), (846, 560), (768, 200)]]
         + [(x, 606) for x in (400, 720)] + [(x, 716) for x in (500, 760)] + [(1140, 620), (1250, 760)]
         + [(x, 300) for x in (500, 1000)] + [(1230, 180), (1420, 180), (330, 190)])
PROP_DIRS = [ART + "props/", OBJ, "assets/sprites/tiles/kalmora/props/"]
FOOTPRINT_FRAC = {"fence": (1.0, 16), "bench": (0.8, 10), "parasol_table": (0.5, 10), "lamp_post": (0.3, 8), "banner": (0.3, 8),
                  "flower_bed": (0.9, 14), "bush_g": (0.7, 14), "bush_flowers_g": (0.7, 14), "boulder": (0.8, 16)}
# Soft contact shadows baked into the ground: (rx scale, ry scale, x offset, strength) per kind.
SHADOW = {"building": (0.52, 0.10, 6, 0.55), "tree": (0.42, 0.16, 8, 0.5), "prop": (0.5, 0.2, 2, 0.4),
          "float": (0.45, 0.14, 4, 0.35)}


def prop_path(name):
    for d in PROP_DIRS:
        if os.path.exists(f"{d}{name}.png"):
            return f"{d}{name}.png"
    raise SystemExit(f"no sprite for prop {name}")


def cell_of(x, y):
    return int((y - TOP) // TILE), int((x - LEFT) // TILE)


def main():
    ground, stand, blocked, stairs = build_terrain()
    stair_png = build_stairs()
    errors = []

    def check_spot(name, x, y, want=None):
        r, c = cell_of(x, y)
        ok = 0 <= r < ROWS and 0 <= c < COLS and not blocked[r][c] and (want is None or stand[r][c] == want)
        if not ok:
            errors.append(f"{name} at concept {C(x, y)} is not on walkable ground")

    spawns = {k: W(*v) for k, v in SPAWNS.items()}
    for name, _, pos, _ in BUILDINGS:
        if name in DOORS:
            x, y = W(*pos)
            spawns[f"from_{name.lower()}"] = (x + DOORS[name][0], y + 26)
    cards = [(card, W(*p)) for card, p in CARDS]
    rival_spots = {k: W(*v) for k, v in RIVAL_SPOTS.items()}
    for card, (x, y) in cards:
        check_spot(card, x, y)
    for name, (x, y) in {**spawns, **rival_spots}.items():
        check_spot(name, x, y)

    subs = {}
    def shape(w, h):
        key = f"R{w}x{h}"
        subs[key] = f'[sub_resource type="RectangleShape2D" id="{key}"]\nsize = Vector2({w}, {h})\n'
        return key

    ext = [
        ('Script', "res://scripts/world/zone.gd", "1_zone"),
        ('PackedScene', "res://scenes/characters/player.tscn", "2_player"),
        ('PackedScene', "res://scenes/ui/hud.tscn", "3_hud"),
        ('PackedScene', "res://scenes/ui/binder.tscn", "4_binder"),
        ('PackedScene', "res://scenes/ui/shop_panel.tscn", "5_shop"),
        ('PackedScene', "res://scenes/systems/card_pickup.tscn", "6_pick"),
        ('PackedScene', "res://scenes/characters/training_dummy.tscn", "7_dummy"),
        ('PackedScene', "res://scenes/systems/merchant.tscn", "8_merchant"),
        ('Script', "res://scripts/systems/safe_zone.gd", "9_safe"),
        ('PackedScene', "res://scenes/systems/card_gate.tscn", "10_gate"),
        ('PackedScene', "res://scenes/systems/zone_exit.tscn", "11_exit"),
        ('Texture2D', "res://" + GROUND_PNG, "12_ground"),
        ('Texture2D', "res://" + LEVEL_PNG, "13_levels"),
        ('PackedScene', "res://scenes/world/props/kalmora_fountain.tscn", "18_fountain"),
        ('PackedScene', "res://scenes/characters/npc.tscn", "19_npc"),
        ('Script', "res://scripts/systems/lamp_light.gd", "20_lamp"),
        ('PackedScene', "res://scenes/systems/clue_crate.tscn", "21_clue"),
        ('PackedScene', "res://scenes/ui/dialogue_box.tscn", "22_dialogue"),
    ]
    for rows, path in stair_png.items():
        ext.append(('Texture2D', "res://" + path, f"st_{rows}"))
    tex = {}
    def texture(path):
        if path not in tex:
            tex[path] = f"t{len(tex)}_{os.path.basename(path)[:-4]}"
            ext.append(('Texture2D', "res://" + path, tex[path]))
        return tex[path]

    sizes = {}
    def bbox(path):
        if path not in sizes:
            im = Image.open(path)
            sizes[path] = (im.size, im.getbbox())
        return sizes[path]

    def bottom_offset(path):
        (w, h), b = bbox(path)
        return h / 2 - b[3]

    shadows = []   # (x, y, rx, ry, strength)
    def shadow(kind, path, x, y):
        (_, _), b = bbox(path)
        w = b[2] - b[0]
        sx, sy, dx, k = SHADOW[kind]
        shadows.append((x + dx, y - 2, w * sx, max(5.0, w * sy), k))

    n = []
    cx, cy = (LEFT + RIGHT) / 2, (TOP + BOTTOM) / 2
    n.append(f'''[node name="Kalmora" type="Node2D"]
y_sort_enabled = true
script = ExtResource("1_zone")
display_name = "Kalmora, Port of Beginnings"
level_map = ExtResource("13_levels")
level_cell = {TILE}
level_origin = Vector2({LEFT}, {TOP})

[node name="GroundTiles" type="Sprite2D" parent="."]
z_index = -10
position = Vector2({cx}, {cy})
texture = ExtResource("12_ground")
''')
    for k, (c0, r0, rows) in enumerate(STAIR_SPOTS):
        x, top = LEFT + c0 * TILE, TOP + r0 * TILE
        n.append(f'[node name="Stairs{k + 1}" type="Sprite2D" parent="."]\nz_index = -8\nposition = Vector2({x + TILE}, {top + rows * TILE / 2})\n'
                 f'texture = ExtResource("st_{rows}")\n')

    # Cliffs, sea and the town's outer walls, merged into rectangles; the gate line
    # closes the forest band so the north gate is the only way out.
    walls = merge_rects(blocked, LEFT, TOP, TILE)
    walls += [(LEFT - 40, TOP - 40, -24, TOP), (24, TOP - 40, RIGHT + 40, TOP),
              (-64, TOP - 80, -24, TOP - 40), (24, TOP - 80, 64, TOP - 40),
              (LEFT, GATE_Y - 12, -22, GATE_Y + 4), (22, GATE_Y - 12, RIGHT, GATE_Y + 4),
              (LEFT - 40, TOP, LEFT, BOTTOM), (RIGHT, TOP, RIGHT + 40, BOTTOM),
              (LEFT - 40, BOTTOM, RIGHT + 40, BOTTOM + 40)]
    n.append('[node name="Walls" type="StaticBody2D" parent="."]\n')
    for k, (x0, y0, x1, y1) in enumerate(walls):
        n.append(f'[node name="W{k}" type="CollisionShape2D" parent="Walls"]\nposition = Vector2({(x0 + x1) / 2}, {(y0 + y1) / 2})\n'
                 f'shape = SubResource("{shape(x1 - x0, y1 - y0)}")\n')

    # Lighthouse yard on the headland: low walls, the door gate facing the market.
    lx, ly = W(*LIGHTHOUSE)
    lh = OBJ + "lighthouse.png"
    n.append(f'''[node name="LighthouseYard" type="StaticBody2D" parent="."]
position = Vector2({lx}, {ly})

[node name="West" type="CollisionShape2D" parent="LighthouseYard"]
position = Vector2(-70, 0)
shape = SubResource("{shape(10, 170)}")

[node name="East" type="CollisionShape2D" parent="LighthouseYard"]
position = Vector2(70, 0)
shape = SubResource("{shape(10, 170)}")

[node name="South" type="CollisionShape2D" parent="LighthouseYard"]
position = Vector2(0, 85)
shape = SubResource("{shape(140, 10)}")

[node name="FrontWest" type="CollisionShape2D" parent="LighthouseYard"]
position = Vector2(-46, -85)
shape = SubResource("{shape(48, 10)}")

[node name="FrontEast" type="CollisionShape2D" parent="LighthouseYard"]
position = Vector2(46, -85)
shape = SubResource("{shape(48, 10)}")

[node name="Lighthouse" type="StaticBody2D" parent="."]
position = Vector2({lx}, {ly + 70})

[node name="Sprite" type="Sprite2D" parent="Lighthouse"]
position = Vector2(0, {bottom_offset(lh)})
texture = ExtResource("{texture(lh)}")

[node name="Base" type="CollisionShape2D" parent="Lighthouse"]
position = Vector2(0, -14)
shape = SubResource("{shape(64, 28)}")

[node name="LighthouseLight" type="PointLight2D" parent="."]
position = Vector2({lx}, {ly + 70 - 230})
texture_scale = 3.0
script = ExtResource("20_lamp")
max_energy = 1.2

[node name="LighthouseDoor" parent="." instance=ExtResource("10_gate")]
position = Vector2({lx}, {ly - 85})
gate_id = &"kalmora_lighthouse_door"

[node name="Card_lighthouse_lens" parent="." instance=ExtResource("6_pick")]
position = Vector2({lx}, {ly - 30})
card_id = &"lighthouse_lens"
behind_gate = &"kalmora_lighthouse_door"
''')
    shadow("building", lh, lx, ly + 70)
    check_spot("lighthouse lens", lx, ly - 30, TOWN)

    gp = OBJ + "gate_pillars.png"
    fx, fy = W(*FOUNTAIN)
    mx, my = W(*MERCHANT)
    n.append(f'''[node name="Fountain" parent="." instance=ExtResource("18_fountain")]
position = Vector2({fx}, {fy})

[node name="Merchant" parent="." instance=ExtResource("8_merchant")]
position = Vector2({mx}, {my})
stall_texture = ExtResource("{texture(ART + "props/stall_fruit.png")}")

[node name="GatePillars" type="Sprite2D" parent="."]
position = Vector2(0, {GATE_Y + 8})
offset = Vector2(0, {bottom_offset(gp)})
texture = ExtResource("{texture(gp)}")

[node name="NorthGate" parent="." instance=ExtResource("10_gate")]
position = Vector2(0, {GATE_Y})
gate_id = &"kalmora_north_gate"

[node name="ToThornveil" parent="." instance=ExtResource("11_exit")]
position = Vector2(0, {TOP - 20})
target_scene = "res://scenes/world/thornveil.tscn"
target_spawn = &"from_kalmora"

[node name="SafeZone" type="Area2D" parent="."]
collision_layer = 0
collision_mask = 6
monitorable = false
script = ExtResource("9_safe")

[node name="CollisionShape2D" type="CollisionShape2D" parent="SafeZone"]
position = Vector2({cx}, {cy})
shape = SubResource("{shape(RIGHT - LEFT, BOTTOM - TOP)}")

[node name="Spawns" type="Node2D" parent="."]
''')
    shadows.append((fx + 4, fy - 6, 60, 16, 0.45))
    shadows.append((0, GATE_Y + 6, 80, 10, 0.4))
    check_spot("north gate", 0, GATE_Y + 24, UPPER)
    for name, (x, y) in spawns.items():
        n.append(f'[node name="{name}" type="Marker2D" parent="Spawns"]\nposition = Vector2({x}, {y})\n')
    n.append('[node name="RivalSpots" type="Node2D" parent="."]\n')
    for name, (x, y) in rival_spots.items():
        n.append(f'[node name="{name}" type="Marker2D" parent="RivalSpots"]\nposition = Vector2({x}, {y})\n')

    ex, ey = W(*EXTRA_SALT_COMPASS)
    taken = [p for _, p in cards] + list(rival_spots.values()) + list(spawns.values()) \
        + [(ex, ey), (mx, my), (fx, fy), (lx, ly - 85), (lx, ly - 30), (0, GATE_Y)]
    for card, (x, y) in cards:
        n.append(f'[node name="Card_{card}" parent="." instance=ExtResource("6_pick")]\nposition = Vector2({x}, {y})\ncard_id = &"{card}"\n')
    n.append(f'[node name="Card_salt_compass_2" parent="." instance=ExtResource("6_pick")]\nposition = Vector2({ex}, {ey})\ncard_id = &"salt_compass"\n')
    for k, p in enumerate(DUMMIES):
        x, y = W(*p)
        check_spot("dummy", x, y)
        taken.append((x, y))
        n.append(f'[node name="TrainingDummy{k + 1}" parent="." instance=ExtResource("7_dummy")]\nposition = Vector2({x}, {y})\n')

    def solid(node, path, x, y, fw, fh):
        return (f'[node name="{node}" type="StaticBody2D" parent="."]\nposition = Vector2({x}, {y})\n\n'
                f'[node name="Sprite" type="Sprite2D" parent="{node}"]\nposition = Vector2(0, {bottom_offset(path)})\n'
                f'texture = ExtResource("{texture(path)}")\n\n'
                f'[node name="Base" type="CollisionShape2D" parent="{node}"]\nposition = Vector2(0, {-fh / 2})\n'
                f'shape = SubResource("{shape(fw, fh)}")\n')

    for name, sprite, pos, fw in BUILDINGS:
        x, y = W(*pos)
        check_spot(name, x, y)
        path = OBJ + sprite + ".png"
        n.append(solid(name, path, x, y, fw, 40))
        shadow("building", path, x, y)
        taken.append((x, y))
        if name in DOORS:
            dx, interior = DOORS[name]
            n.append(f'[node name="{name}Lamp" type="PointLight2D" parent="."]\nposition = Vector2({x + dx}, {y - 40})\n'
                     f'texture_scale = 0.9\nscript = ExtResource("20_lamp")\nmax_energy = 0.8\n')
            n.append(f'[node name="{name}Door" parent="." instance=ExtResource("11_exit")]\nposition = Vector2({x + dx}, {y + 4})\n'
                     f'scale = Vector2(0.5, 1)\ntarget_scene = "{interior}"\ntarget_spawn = &"door"\n')

    # Residents and the quay's unmarked crates.
    for npc_id, display, sprite_id, pos, wander, lines in NPCS:
        x, y = W(*pos)
        check_spot(npc_id, x, y)
        frames_id = f"n_{sprite_id}"
        ext.append(('SpriteFrames', f"res://assets/sprites/npcs/{sprite_id}/{sprite_id}_frames.tres", frames_id))
        quoted = ", ".join('"' + line.replace('"', '\\"') + '"' for line in lines)
        n.append(f'[node name="Npc_{npc_id}" parent="." instance=ExtResource("19_npc")]\nposition = Vector2({x}, {y})\n'
                 f'npc_id = &"{npc_id}"\ndisplay_name = "{display}"\nsprite_frames = ExtResource("{frames_id}")\n'
                 f'lines = PackedStringArray({quoted})\nwander_radius = {float(wander)}\n')
        taken.append((x, y))
    for clue, pos in CLUE_CRATES:
        x, y = W(*pos)
        check_spot(clue, x, y)
        n.append(f'[node name="Clue_{clue}" parent="." instance=ExtResource("21_clue")]\nposition = Vector2({x}, {y})\nclue_id = &"{clue}"\n')
        taken.append((x, y))

    # Trees, then props. Everything is placed on purpose; a spot that lands on a wall,
    # stairs, or something already placed is a layout error, reported all at once.
    crowd = lambda x, y, r: next(((a, b) for a, b in taken if (x - a) ** 2 + (y - b) ** 2 < r ** 2), None)

    skipped = []

    def fits(x, y, clearance):
        r, c = cell_of(x, y)
        return (0 <= r < ROWS and 0 <= c < COLS and not blocked[r][c] and (r, c) not in stairs
                and not crowd(x, y, clearance))

    def place_check(name, x, y, clearance=18):
        """Decorations that don't fit (a wall, stairs, something already there) are
        nudged to the nearest open spot within a short reach, else skipped with a
        warning; they never block the build. Returns the spot used, or None."""
        for reach in range(0, 49, 8):
            for dx, dy in ((0, 0),) if reach == 0 else [(reach * math.cos(t), reach * math.sin(t))
                                                         for t in (i * math.pi / 4 for i in range(8))]:
                if fits(x + dx, y + dy, clearance):
                    return (round(x + dx), round(y + dy))
        skipped.append(f"{name} at concept {C(x, y)}")
        return None

    for k, (sprite, pos) in enumerate(TREES):
        path = OBJ + sprite + ".png" if sprite != PINE else "assets/sprites/tiles/kalmora/cypress.png"
        spot = place_check(sprite, *W(*pos), 26)
        if spot:
            x, y = spot
            taken.append((x, y))
            n.append(solid(f"{sprite.title()}{k + 1}", path, x, y, 16 if sprite != TREE else 30, 10))
            shadow("tree", path, x, y)

    count = [0]
    def prop_node(name, x, y, kind="solid"):
        path = prop_path(name)
        count[0] += 1
        node = f"P{count[0]}_{name}"
        if kind == "free":
            shadow("float", path, x, y)
            scale = 1.5 if name == "ship" else 1.0      # the concept's moored ship dwarfs the piers
            return (f'[node name="{node}" type="Sprite2D" parent="."]\nposition = Vector2({x}, {y})\n'
                    f'scale = Vector2({scale}, {scale})\n'
                    f'offset = Vector2(0, {bottom_offset(path)})\ntexture = ExtResource("{texture(path)}")\n')
        taken.append((x, y))
        (_, _), b = bbox(path)
        frac, fh = FOOTPRINT_FRAC.get(name, (0.6, 10))
        shadow("prop", path, x, y)
        return solid(node, path, x, y, max(12, int((b[2] - b[0]) * frac)), fh)

    for pcx, pcy in LAMPS:
        spot = place_check("lamp_post", *W(pcx, pcy))
        if spot:
            x, y = spot
            n.append(prop_node("lamp_post", x, y))
            n.append(f'[node name="Light{count[0]}" type="PointLight2D" parent="."]\nposition = Vector2({x + 18}, {y - 47})\n'
                     f'texture_scale = 1.4\nscript = ExtResource("20_lamp")\n')
    for name, pcx, pcy in PROPS + CLUTTER:
        spot = place_check(name, *W(pcx, pcy), 16 if name in SMALL else 18)
        if spot:
            n.append(prop_node(name, *spot))
    for k, (pcx, pcy) in enumerate(BUSHES):
        name = ("bush_g", "bush_flowers_g")[k % 3 == 0]
        spot = place_check(name, *W(pcx, pcy), 22)
        if spot:
            n.append(prop_node(name, *spot))
    for name, pcx, pcy in FLOATING:
        n.append(prop_node(name, *W(pcx, pcy), "free"))
    # Boulders in the surf along every rocky cliff foot, like the concept's coasts.
    rng = random.Random(9)
    for r in range(ROWS - 1):
        for c in range(COLS):
            if stand[r][c] == -1 and stand[r + 1][c] == SEA and blocked[r + 1][c] and not harbor_wall(r, c) \
                    and (r, c) not in stairs and rng.random() < 0.45:
                x = LEFT + c * TILE + TILE // 2 + rng.randint(-10, 10)
                y = TOP + (r + 1) * TILE + rng.randint(4, 20)
                n.append(prop_node("sea_rocks", x, y, "free"))
    # Side-facing coasts (the rock set only draws a thin edge there): pile boulders
    # into the water along them.
    for r in range(1, ROWS - 1):
        for c in range(1, COLS - 1):
            if stand[r][c] != SEA or not blocked[r][c] or harbor_wall(r, c):
                continue
            side = next((dc for dc in (-1, 1) if stand[r][c + dc] != SEA and not blocked[r][c + dc] or stand[r][c + dc] == -1), None)
            if side is None or rng.random() > 0.5:
                continue
            x = LEFT + c * TILE + TILE // 2 - side * rng.randint(0, 8)
            y = TOP + r * TILE + rng.randint(14, 30)
            n.append(prop_node("sea_rocks", x, y, "free"))
    if errors:
        raise SystemExit("layout errors:\n  " + "\n  ".join(errors))
    if skipped:
        print(f"skipped {len(skipped)} decorations:\n  " + "\n  ".join(skipped))

    # Bake the soft contact shadows into the ground.
    mask = Image.new("L", ground.size, 0)
    d = ImageDraw.Draw(mask)
    for x, y, rx, ry, k in shadows:
        px, py = x - LEFT, y - TOP
        d.ellipse((px - rx, py - ry, px + rx, py + ry), fill=int(255 * k))
    mask = mask.filter(ImageFilter.GaussianBlur(5))
    a = np.asarray(ground).astype(np.float32)
    m = np.asarray(mask).astype(np.float32)[..., None] / 255.0
    tint = np.array([28, 30, 52], np.float32)                    # shadows lean cool, like the concept's
    a[..., :3] = a[..., :3] * (1 - m * 0.75) + tint * (m * 0.75) * 0.35
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA").save(GROUND_PNG)

    n.append(f'''[node name="Player" parent="." instance=ExtResource("2_player")]
position = Vector2{spawns["town"]}

[node name="HUD" parent="." instance=ExtResource("3_hud")]

[node name="Binder" parent="." instance=ExtResource("4_binder")]

[node name="ShopPanel" parent="." instance=ExtResource("5_shop")]

[node name="DialogueBox" parent="." instance=ExtResource("22_dialogue")]
''')
    head = f'[gd_scene load_steps={len(ext) + len(subs) + 1} format=3]\n\n' + "".join(
        f'[ext_resource type="{t}" path="{p}" id="{i}"]\n' for t, p, i in ext) + "\n"
    open(SCENE, "w", encoding="utf-8", newline="\n").write(head + "\n".join(subs.values()) + "\n" + "\n".join(n))
    print(f"kalmora: {COLS}x{ROWS} cells, {len(walls)} wall rects, {len(taken)} placed things, {len(shadows)} shadows")


if __name__ == "__main__":
    main()
