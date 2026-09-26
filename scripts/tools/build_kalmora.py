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
SURFACE_PNG = ART + "kalmora_surface.png"      # green = sand (takes footprints); red marks grass
SURFACE = ART + "surface/"
GRASS = os.environ.get("KALMORA_GRASS", "grass_meadow")   # which wang/<name> grass set the lawns use
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
    if 1264 <= cx and cy <= 336:     # (a strip of town ground along the canal lands the bridges)
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
    if cx >= 1104 and 596 < cy <= 704:
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
    return (440 <= cy <= 596 and ((cx - 1300) / 176) ** 2 + ((cy - 520) / 150) ** 2 <= 1  # the beach, a crescent cove
            and not ((cx - 1330) / 120) ** 2 + ((cy - 700) / 70) ** 2 <= 1)


def planks_c(cx, cy):
    return (368 <= cx <= 840 and 560 <= cy <= 772                              # the long deck under the square
            or 760 <= cx <= 968 and 760 <= cy <= 836                           # deck below the market wall's foot
            or 600 <= cx <= 672 and 772 <= cy <= 872                           # pier by the ship
            or 900 <= cx <= 968 and 836 <= cy <= 980)                          # the long pier


def sand(x, y):
    return sand_c(*C(x, y))


def planks(x, y):
    return planks_c(*C(x, y))


# Canal bridges (concept px): walkable at town level, decked with planks.
BRIDGES = [(1088, 270, 1184, 280), (1088, 418, 1184, 428)]

# Garden beds inside the paved town (concept px): lawns with bushes and palms.
BEDS = [(640, 384, 704, 432), (832, 384, 896, 432), (624, 496, 688, 528), (848, 496, 912, 528),
        (512, 192, 624, 240), (672, 192, 736, 240), (816, 192, 896, 240),
        (352, 256, 400, 496), (352, 192, 448, 224)]


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
        return (1184 <= cx <= 1456 and (144 <= cy <= 176 or 272 <= cy <= 304)   # hill lanes
                or 1280 <= cx <= 1312 and cy >= 144)
    return True


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return ((px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2) ** 0.5


# Dirt paths (concept px polylines, half-width): the north road and the meadow's tracks.
PATHS = [
    ([(768, 0), (768, 176)], 28),
    ([(236, 352), (236, 396), (336, 396), (352, 340)], 14),                  # windmill door to town
    ([(300, 396), (300, 488)], 12),                                          # lane down past the south plot
    ([(318, 0), (318, 120), (360, 150), (416, 168)], 20),                    # up from the west gate
]


def dirt_c(cx, cy):
    return any(seg_dist(cx, cy, *a, *b) <= w for pts, w in PATHS for a, b in zip(pts, pts[1:]))


# Stairs: (concept x of the left edge, concept y of the plateau edge, (lower, upper) levels).
STAIRS = [
    (736, 560, (0, 2)),                           # grand stairs: square down to the deck
    (752, 176, (2, 3)),                           # the gate road down into town
    (416, 176, (2, 3)),                           # the west gate
    (1280, 336, (2, 3)),                          # the hill houses down to the band
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


def soft_surface(img, stand, levels, tile, inside, seed=0, res=4, blur=6, jitter=0.16, rim=0.8, shade_outside=True,
                 texture=None):
    """Paints `tile` (tiled) over the flat cells of `levels` wherever inside(cx, cy) holds
    (concept px), with a pixel-level edge: the coarse mask is blurred, which rounds every
    corner, then thresholded against smooth noise so the edge wanders a little. The
    surface gets a darker rim along its edge, and (shade_outside) the ground just outside
    it a soft shade, like grass lipping over stone. `texture` (a full-size array) replaces
    the tiled `tile`. Returns the new image and the mask of pixels the surface covers."""
    W_, H_ = img.size
    gw, gh = W_ // res, H_ // res
    coarse = np.zeros((gh, gw), np.float32)
    for j in range(gh):
        for i in range(gw):
            coarse[j, i] = 1.0 if inside(*C(LEFT + i * res + res / 2, TOP + j * res + res / 2)) else 0.0
    m = Image.fromarray((coarse * 255).astype(np.uint8)).resize((W_, H_), Image.BILINEAR).filter(ImageFilter.GaussianBlur(blur))
    rng = np.random.default_rng(seed)
    noise = Image.fromarray((rng.random((H_ // 24 + 1, W_ // 24 + 1)) * 255).astype(np.uint8)).resize((W_, H_), Image.BICUBIC)
    level = np.asarray(m).astype(np.float32) / 255.0 + (np.asarray(noise).astype(np.float32) / 255.0 - 0.5) * jitter
    on = level > 0.5
    cells = np.array([[1 if v in levels else 0 for v in row] for row in stand], np.uint8)
    region = np.kron(cells, np.ones((TILE, TILE), np.uint8)).astype(bool)
    on &= region
    if texture is None:
        texture = np.tile(np.asarray(tile.convert("RGBA")), (H_ // TILE, W_ // TILE, 1))
    tex = texture.astype(np.float32)
    a = np.asarray(img).astype(np.float32)
    a = np.where(on[..., None], tex, a)
    # Edges: pixels of the surface within 2px of its outside, and outside pixels within 3px of it.
    near_out = np.asarray(Image.fromarray((~on & region).astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(5))) > 0
    near_in = np.asarray(Image.fromarray(on.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(7))) > 0
    rim_px = on & near_out
    a[..., :3] = np.where(rim_px[..., None], a[..., :3] * rim, a[..., :3])
    if shade_outside:
        shade = ~on & near_in & region
        a[..., :3] = np.where(shade[..., None], a[..., :3] * 0.86, a[..., :3])
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA"), on


def regrass(img, grass_on, field):
    """The cliff tiles and the field sets bring their own (older, brighter) grass along
    cliff tops and field edges. Every patch of that old grass joined to the new meadow
    takes the new grass too; isolated specks (moss on the cliff faces) stay."""
    a = np.asarray(img)
    r, g, b = (a[..., i].astype(int) for i in range(3))
    old_px = (g > r + 40) & (g > b + 40) & ~grass_on                  # bright, grassy greens
    fields = np.zeros(old_px.shape, bool)                               # crop rows stay crops
    for x0, y0, x1, y1 in WHEAT + CROPS:
        (px0, py0), (px1, py1) = W(x0, y0), W(x1, y1)
        fields[max(0, py0 - TOP - TILE):py1 - TOP + TILE, max(0, px0 - LEFT - TILE):px1 - LEFT + TILE] = True
    old_px &= ~fields
    allowed = old_px | grass_on
    reach = grass_on.copy()
    count = reach.sum()
    while True:
        reach = (np.asarray(Image.fromarray(reach.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(3))) > 0) & allowed
        if reach.sum() == count:
            break
        count = reach.sum()
    add = reach & old_px
    out = np.where(add[..., None], field, a)
    return Image.fromarray(out.astype(np.uint8), "RGBA"), grass_on | add


def paint_sand(img, stand):
    """The beach, painted per pixel over the sea: rippled dry sand that darkens to wet sand
    toward the waterline, with a broken line of foam where the water meets it."""
    W_, H_ = img.size
    res = 2
    gw, gh = W_ // res, H_ // res
    coarse = np.zeros((gh, gw), np.uint8)
    for j in range(gh):
        for i in range(gw):
            coarse[j, i] = 255 if sand_c(*C(LEFT + i * res + 1, TOP + j * res + 1)) else 0
    m = np.asarray(Image.fromarray(coarse).resize((W_, H_), Image.BILINEAR).filter(ImageFilter.GaussianBlur(4))) / 255.0
    rng = np.random.default_rng(5)

    def smooth_noise(cell):
        n = (rng.random((H_ // cell + 2, W_ // cell + 2)) * 255).astype(np.uint8)
        return np.asarray(Image.fromarray(n).resize((W_ + 2 * cell, H_ + 2 * cell), Image.BICUBIC))[:H_, :W_] / 255.0

    def near(mask, px):
        return np.asarray(Image.fromarray(mask.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(px * 2 + 1))) > 0

    edge_noise, patch = smooth_noise(14), smooth_noise(90)
    cells = np.array([[1 if v == SEA else 0 for v in row] for row in stand], np.uint8)
    region = np.kron(cells, np.ones((TILE, TILE), np.uint8)).astype(bool)
    on = (m + (edge_noise - 0.5) * 0.25 > 0.5) & region
    tile = np.asarray(Image.open(SURFACE + "sand_ripples.png").convert("RGBA"))
    tex = np.tile(tile, (H_ // tile.shape[0] + 1, W_ // tile.shape[1] + 1, 1))[:H_, :W_].astype(np.float32)
    # Broad, barely-there patches of lighter and darker sand so the ripples don't read as a grid.
    tex[..., :3] *= (1.0 + np.round((patch - 0.5) * 4) * 0.025)[..., None]
    # Wet sand: a dark band right at the waterline and a lighter one behind it, its width wandering.
    water = region & ~on
    wet1 = on & near(water, 3)
    wet2 = on & ~wet1 & (near(water, 9) | near(water, 13) & (edge_noise > 0.5))
    tex[..., :3] = np.where(wet2[..., None], tex[..., :3] * np.array([0.86, 0.84, 0.82]), tex[..., :3])
    tex[..., :3] = np.where(wet1[..., None], tex[..., :3] * np.array([0.72, 0.7, 0.7]), tex[..., :3])
    a = np.asarray(img).astype(np.float32)
    a = np.where(on[..., None], tex, a)
    foam = water & near(on, 2) & (smooth_noise(6) > 0.3)
    a[..., :3] = np.where(foam[..., None], a[..., :3] * 0.25 + np.array([236, 246, 244]) * 0.75, a[..., :3])
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA"), on


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
    grass, dirt = CornerSet(ART + "wang/" + GRASS), CornerSet(ART + "wang/dirt")
    # Grass over paving and dirt over grass are blended per pixel (soft_surface), so
    # their edges round off and wander a little instead of stepping along tile corners.
    land = (HARBOR, TOWN, UPPER)
    img, _ = soft_surface(img, stand, land, grass.tiles[0], lambda cx, cy: True, jitter=0, rim=1.0,
                          shade_outside=False)                     # paving everywhere first
    lawn = grass.tiles[15]
    field = np.tile(np.asarray(lawn.convert("RGBA")), (img.size[1] // TILE, img.size[0] // TILE, 1))
    img, grass_on = soft_surface(img, stand, land, lawn, lambda cx, cy: not paved_c(cx, cy), seed=1)
    wheat, crops = CornerSet(ART + "wang/wheat"), CornerSet(ART + "wang/crops")
    for level in (TOWN, UPPER):
        overlay(img, stand, level, wheat, lambda x, y: in_field(*C(x, y), WHEAT), LEFT, TOP, TILE)
        overlay(img, stand, level, crops, lambda x, y: in_field(*C(x, y), CROPS), LEFT, TOP, TILE)
    img, dirt_on = soft_surface(img, stand, land, dirt.tiles[15], lambda cx, cy: dirt_c(cx, cy) and not paved_c(cx, cy),
                                seed=2, blur=3, rim=0.9, shade_outside=False)
    img, grass_on = regrass(img, grass_on, field)
    img, sand_on = paint_sand(img, stand)
    boards = CornerSet(ART + "wang/planks")
    overlay(img, stand, SEA, boards, planks, LEFT, TOP, TILE)
    bridges = bridge_cells()   # drawn by the stone bridge sprites (build_bridge), walkable here
    img = deepen_greens(img)
    surface = np.zeros((img.size[1], img.size[0], 3), np.uint8)
    surface[..., 0] = (grass_on & ~dirt_on) * 255
    surface[..., 1] = sand_on * 255
    Image.fromarray(surface, "RGB").save(SURFACE_PNG)

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


def build_bridge():
    """The canal footbridge: PixelLab's stone bridge with its end walls cut away so both
    ends are open, lengthened to span bank to bank, and its cobbled deck deepened to a
    comfortable walking width."""
    src = Image.open(OBJ + "canal_bridge.png").convert("RGBA")
    x0, y0, x1, y1 = src.getbbox()
    src = src.crop((x0, y0, x1, y1))
    w, h = src.size
    end = 13                                    # the end walls' width
    body = src.crop((end, 0, w - end, h))       # parapets along top and bottom, deck between
    # Deepen the deck: repeat its middle rows (rows 12..29 of the crop are cobbles).
    top, deck, bottom = body.crop((0, 0, body.width, 12)), body.crop((0, 12, body.width, 30)), body.crop((0, 30, body.width, h))
    tall = Image.new("RGBA", (body.width, 12 + 40 + bottom.height))
    tall.paste(top, (0, 0))
    for y in range(12, 52, deck.height):
        tall.paste(deck.crop((0, 0, body.width, min(deck.height, 52 - y))), (0, y))
    tall.paste(bottom, (0, 52))
    # Lengthen: repeat a plain middle slice until it spans the canal and onto both banks.
    target = round((BRIDGES[0][2] - BRIDGES[0][0]) * SCALE) + 16
    mid = tall.crop((40, 0, 60, tall.height))
    out = Image.new("RGBA", (target, tall.height))
    half = tall.width // 2
    out.paste(tall.crop((0, 0, half, tall.height)), (0, 0))
    for x in range(half, target - half, mid.width):
        out.paste(mid, (x, 0))
    out.paste(tall.crop((tall.width - half, 0, tall.width, tall.height)), (target - half, 0))
    path = ART + "canal_bridge_span.png"
    out.save(path)
    return path, 12 + 20                        # the deck's centre row in the sprite


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
    ("CardShop", "item_shop", (1034, 520), 150),
    ("Harbormaster", "harbormaster2", (440, 700), 140),
    ("Warehouse", "warehouse", (560, 700), 170),
    ("BlueCottage", "cottage_blue", (1150, 136), 140),
    ("NonnaHouse", "cottage_red", (1328, 136), 130),
    ("HillHouse", "townhouse_blue", (1318, 262), 100),
    ("TealHouse", "townhouse_teal", (1400, 262), 96),
    ("Windmill", "windmill2", (230, 344), 90),
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
    ("harbor_lantern", (400, 740)), ("coral_coin", (1330, 540)), ("gull_feather", (1360, 790)),
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

PALM, TREE = "palm_g", "tree3_g"
# Plants that move in the sea breeze: PixelLab-animated frame strips (strip, frames, fps).
ANIMATED = {PALM: (ART + "anim/palm_sway.png", 8, 7), TREE: (ART + "anim/tree_sway.png", 8, 6),
            "tuft": (ART + "anim/tuft_sway.png", 8, 7), "tuft_flowers": (ART + "anim/tuft_flowers_sway.png", 8, 6)}
# Where grass tufts grow around each kind of tree (offsets from its base, world px).
TUFT_RING = {TREE: [(-26, 4), (24, 2), (-12, 16), (14, 18)], PALM: [(-16, 6), (15, 10)]}


def grid(xs, ys):
    return [(x, y) for x in xs for y in ys]


# Trees: palms only (concept px). The broadleaf trees read out of place in this palette.
TREES = (
    [(PALM, p) for p in [(650, 526), (872, 526), (700, 240), (860, 240), (380, 480)]]      # the square and town
    + [(PALM, p) for p in [(1200, 760), (1400, 720), (1430, 620), (1400, 540)]]           # headland and beach
    + [(PALM, p) for p in [(100, 810), (175, 850), (95, 880)]]                             # the islet
    # Sparse round trees in the open grass, as in the cleaned-up picture.
    + [(TREE, p) for p in [(30, 40), (220, 42), (285, 38), (420, 44), (630, 42), (1110, 40), (1470, 50),
                           (70, 118), (600, 116), (960, 116), (1085, 140), (1215, 140), (1420, 150),
                           (300, 230), (380, 300), (385, 440)]]
)


def row(name, x0, x1, y, step):
    return [(name, x, y) for x in range(x0, x1 + 1, step)]


# The windmill farm (concept px rects): golden wheat and vegetable plots, fenced along
# their tops and bottoms; plus a kitchen garden east of the hill houses.
WHEAT = [(5, 180, 130, 228), (5, 346, 125, 386)]
CROPS = [(5, 262, 120, 312), (65, 424, 225, 490), (1466, 200, 1530, 325)]
# One fence line per plot edge (shared edges get a single line): (x0, x1, y), concept px.
FARM_FENCES = [(5, 140, 166), (5, 140, 246), (5, 140, 330), (5, 235, 408)]


def in_field(cx, cy, fields):
    return any(in_rect(cx, cy, f) for f in fields)


def farm_fences():
    """Split-rail fences between the meadow plots, gapped every few rails for gates."""
    return [("fence", x, y) for x0, x1, y in FARM_FENCES for k, x in enumerate(range(x0 + 8, x1, 16)) if k % 5 != 2]


STALLS = ["stall_fruit", "stall_fish", "stall_pottery", "stall_bread"]
# Props: (name, concept x, concept y), grouped by where a resident would put them.
PROPS = (
    # The fountain square: banners on its rim, flower beds, benches.
    [("banner", x, y) for x, y in [(700, 408), (836, 408), (700, 540), (836, 540)]]
    + [("bush_g", x, y) for x, y in [(718, 478), (818, 478)]]
    # Shop fronts.
    + [("parasol_table", 880, 420)]
    + [("barrels", 418, 520)]
    # Market stalls east of the square, in rows.
    # The quay and the deck.
    + [("crates", 400, 660), ("fish_crates", 520, 700)]
    # The west meadow: fenced fields around the windmill.
    + farm_fences()
    + [("signpost", 24, 344)]
    # Beach and headland.
    + [("parasol_table", 1340, 520), ("candle_shrine", 1430, 700)]
    # The hill: flowers at doors, gardens between the houses.

    # Gate band.

)
# Packing: the concept piles goods, flowers and planters into every gap (concept px).
CLUTTER = (
    # Cargo along the deck and out on the piers.
    [("crates", 386, 736), ("barrels", 470, 760), ("barrel", 650, 840)]
    # Goods between the market stalls.
    # Flowers at the doors of the houses.
    # The beach, the meadow, and the gate band.
    # Rocks and greenery along the canal banks and around the hill houses.
)
SMALL = {"crate", "barrel", "sack", "flour_sack", "rope", "buoy", "bucket", "lobster_trap", "apples_crate",
         "oranges_basket", "lemons_crate", "amphora"}
# Bushes packed along walls, beds and building sides (concept px).
BUSHES = [(1430, 450), (1420, 790), (1230, 800), (1350, 800)]

# Walking corridors (concept px polylines, half-width): the routes people actually take.
# No decoration may stand in them, so every district stays easy to cross.
ROUTES = [
    ([(768, 90), (768, 560)], 24),                                        # gate road down through the square
    ([(768, 450), (560, 450), (380, 430), (340, 330), (200, 400)], 20),   # west street out to the meadow
    ([(768, 450), (1000, 450), (1080, 350), (1210, 350), (1296, 330), (1296, 150), (1400, 150)], 20),  # east bank and hill
    ([(1210, 276), (1210, 350)], 16),                                    # along the canal strip
    ([(1080, 350), (1080, 276), (1200, 276)], 16),                        # the upper bridge
    ([(1000, 450), (1080, 423), (1210, 423)], 16),                        # the lower bridge
    ([(1248, 350), (1300, 420), (1310, 520), (1330, 600)], 18),           # down to the beach
    ([(768, 540), (900, 620), (1100, 620), (1225, 680), (1225, 770), (1290, 770)], 20),  # through the market, round to the lighthouse door
    ([(745, 540), (745, 700), (560, 720), (400, 720)], 22),               # grand stairs, the deck
    ([(745, 720), (800, 790), (934, 800)], 18), ([(636, 740), (636, 870)], 14), ([(934, 740), (934, 960)], 14),  # deck east, piers
    ([(930, 400), (930, 450)], 14), ([(1034, 520), (1034, 560)], 14), ([(1328, 136), (1328, 160)], 14),  # doors
    ([(590, 400), (590, 450)], 14), ([(455, 348), (455, 400)], 14), ([(478, 490), (478, 520)], 14),
]


def on_route(cx, cy, pad=0):
    return any(seg_dist(cx, cy, *a, *b) <= w + pad for pts, w in ROUTES for a, b in zip(pts, pts[1:]))
# Free sprites (y-sorted, no collision): boats and rocks out on the water (concept px).
# Harbor detail: boat arches in the foot of the market's harbor wall, pilings along the
# deck and pier edges (drawn only; the water behind them is already blocked).
HARBOR_DETAIL = ([("wall_arch", x, 773) for x in (950, 1050)]
                 + [("pilings", x, 782) for x in (390, 450, 520, 580, 700)] + [("pilings", x, 846) for x in (780, 840)]
                 + [("pilings", x, y) for x, y in [(604, 880), (668, 880), (902, 988), (966, 988), (900, 860), (966, 860)]])
# A split-rail fence marks the gate line (its collision is the invisible wall line in the
# scene), so nobody walks round the north gate and nothing blocks you unseen.
GATE_FENCE = ([("fence", x, 78) for x in range(346, 1190, 16) if abs(x - 768) > 44]
              + [("fence", x, 148) for x in list(range(352, 740, 16)) + list(range(812, 1080, 16))])
ROCKS = [("sea_rocks", x, y) for x, y in [(20, 900), (70, 945), (200, 940), (262, 902), (278, 850),
                                           (1170, 862), (1350, 866), (1440, 810), (1474, 730), (1480, 520)]]
FLOATING = HARBOR_DETAIL + GATE_FENCE + ROCKS + [("ship", 470, 960), ("rowboat", 250, 650), ("rowboat", 1010, 880), ("rowboat", 870, 960),
]
LAMPS = ([(x, y) for x, y in [(690, 380), (846, 380), (690, 560), (846, 560), (768, 200)]]
         + [(x, 606) for x in (400, 720)] + [(x, 716) for x in (500, 760)] + [(1140, 620), (1180, 700)]
         + [(x, 300) for x in (500, 1000)] + [(1230, 180), (1420, 180), (330, 190)])
PROP_DIRS = [ART + "props/", OBJ, "assets/sprites/tiles/kalmora/props/"]
FOOTPRINT_FRAC = {"fence": (1.0, 16), "bench": (0.8, 10), "parasol_table": (0.5, 10), "lamp_post": (0.3, 8), "banner": (0.3, 8),
                  "flower_bed": (0.9, 14), "bush_g": (0.7, 14), "bush_flowers_g": (0.7, 14), "boulder": (0.8, 16)}
# Soft contact shadows baked into the ground: (rx scale, ry scale, x offset, strength) per kind.
SHADOW = {"building": (0.52, 0.10, 6, 0.55), "tree": (0.42, 0.16, 8, 0.5), "prop": (0.5, 0.2, 2, 0.4),
          "float": (0.45, 0.14, 4, 0.35)}


# The bay's water rolls: a PixelLab-animated water tile repeated over the whole bay and
# clipped to its water pixels (BAY_MASK), so it follows the shoreline exactly. The narrow
# channels (by the beach, the canal) and the strip beside the beach stay as painted.
BAY_STRIP, BAY_FRAMES, BAY_FPS = ART + "anim/bay_water.png", 8, 6
BAY_MASK = ART + "kalmora_bay_mask.png"
BAY_SKIP_ROWS = 27            # the east-edge strip north of this row runs beside the beach


def bay_cells():
    """Level-0 open-water cells of the bay: the sea minus channels under three cells wide."""
    lm = np.asarray(Image.open(LEVEL_PNG).convert("RGB")).astype(int)
    wet = (lm[..., 0] == 0) & (lm[..., 1] == 0)

    def spread(m, keep):
        p = np.pad(m, 1, constant_values=keep)
        out = m.copy()
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                nb = p[1 + dy:1 + dy + ROWS, 1 + dx:1 + dx + COLS]
                out = out & nb if keep else out | nb
        return out

    bay = spread(spread(spread(wet, True), False), False) & wet    # open, then grown back to the shore
    bay[:BAY_SKIP_ROWS, COLS - 6:] = False
    return bay


def bay_water(ground):
    """Writes BAY_MASK (opaque where the bay's water shows in the ground) and returns the
    scene nodes: the mask as a clipping sprite, the animated water tiled inside it."""
    cells = bay_cells()
    near = np.kron(cells, np.ones((TILE, TILE), np.uint8)).astype(bool)
    near = np.asarray(Image.fromarray(near.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(2 * TILE + 1))) > 0
    a = np.asarray(ground).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    water = near & (b > r + 50) & (b >= g - 10)                    # blue water, not foam, rock or wood
    mask = np.zeros(a.shape[:2] + (4,), np.uint8)
    mask[water] = 255
    Image.fromarray(mask, "RGBA").save(BAY_MASK)
    w, h = ground.size
    return [f'''[node name="Bay" type="Sprite2D" parent="."]
z_index = -9
clip_children = 1
position = Vector2({(LEFT + RIGHT) / 2}, {(TOP + BOTTOM) / 2})
texture = ExtResource("25_baymask")

[node name="Water" type="Sprite2D" parent="Bay"]
script = ExtResource("26_tiled")
strip = ExtResource("27_baywater")
frame_count = {BAY_FRAMES}
fps = {BAY_FPS}
region_rect = Rect2(0, 0, {w}, {h})
''']


def prop_path(name):
    for d in PROP_DIRS:
        if os.path.exists(f"{d}{name}.png"):
            return f"{d}{name}.png"
    raise SystemExit(f"no sprite for prop {name}")


# Open ground that is meant to be out of reach (concept px rects): the islet across the
# water and the forests' interiors.
MEANT_UNREACHABLE = [(0, 700, 300, 1024), (0, 0, 1200, 150)]


def unreachable(blocked, stairs, solids, start, targets, step=8, body=5, min_pocket=48, allowed=()):
    """Flood-fills an 8px grid from start, treating terrain walls and every solid
    footprint (grown by a walker's radius) as blocked; returns the targets that
    can't be reached (a target counts if any open cell within ~24px is reached)."""
    w, h = (RIGHT - LEFT) // step, (BOTTOM - TOP) // step
    grid = np.zeros((h, w), bool)
    for r in range(ROWS):
        for c in range(COLS):
            if blocked[r][c] and (r, c) not in stairs:
                grid[r * TILE // step:(r + 1) * TILE // step, c * TILE // step:(c + 1) * TILE // step] = True
    for x0, y0, x1, y1 in solids:
        # A cell is blocked when its centre falls inside the rect grown by a walker's radius.
        gx0, gy0 = max(0, math.ceil((x0 - body - LEFT) / step - 0.5)), max(0, math.ceil((y0 - body - TOP) / step - 0.5))
        gx1, gy1 = min(w, math.floor((x1 + body - LEFT) / step - 0.5) + 1), min(h, math.floor((y1 + body - TOP) / step - 0.5) + 1)
        if gx1 > gx0 and gy1 > gy0:      # rects wholly off the map (road walls past the edge) clip to nothing
            grid[gy0:gy1, gx0:gx1] = True
    seen = np.zeros_like(grid)
    sx, sy = int((start[0] - LEFT) // step), int((start[1] - TOP) // step)
    queue = [(sy, sx)]
    seen[sy, sx] = True
    while queue:
        y, x = queue.pop()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and not grid[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True
                queue.append((ny, nx))
    bad = []
    for name, (x, y) in targets.items():
        gx, gy = int((x - LEFT) // step), int((y - TOP) // step)
        if not seen[max(0, gy - 3):gy + 4, max(0, gx - 3):gx + 4].any():
            bad.append(f"{name} at concept {C(x, y)} can't be reached on foot")
    # Open ground nobody can walk to means an invisible wall somewhere: report every
    # sealed pocket bigger than a small nook.
    pocket = ~grid & ~seen
    label = np.zeros_like(grid, dtype=np.int32)
    for y0 in range(h):
        for x0 in range(w):
            if pocket[y0, x0] and not label[y0, x0]:
                label[y0, x0] = 1
                cells, stack = [(y0, x0)], [(y0, x0)]
                while stack:
                    y, x = stack.pop()
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < h and 0 <= nx < w and pocket[ny, nx] and not label[ny, nx]:
                            label[ny, nx] = 1
                            cells.append((ny, nx))
                            stack.append((ny, nx))
                cy = sum(c[0] for c in cells) / len(cells) * step + TOP
                cx = sum(c[1] for c in cells) / len(cells) * step + LEFT
                if len(cells) >= min_pocket and not any(in_rect(*C(cx, cy), r) for r in allowed):
                    bad.append(f"sealed-off open ground ({len(cells) * step * step // 1024} tiles) around concept "
                               f"{tuple(round(v) for v in C(cx, cy))}")
    return bad


def cell_of(x, y):
    return int((y - TOP) // TILE), int((x - LEFT) // TILE)


def main():
    ground, stand, blocked, stairs = build_terrain()
    stair_png = build_stairs()
    bridge_png, bridge_mid = build_bridge()
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
        ('Texture2D', "res://" + SURFACE_PNG, "24_surface"),
        ('Texture2D', "res://" + BAY_MASK, "25_baymask"),
        ('Script', "res://scripts/world/tiled_animation.gd", "26_tiled"),
        ('Texture2D', "res://" + BAY_STRIP, "27_baywater"),
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
surface_map = ExtResource("24_surface")

[node name="GroundTiles" type="Sprite2D" parent="."]
z_index = -10
position = Vector2({cx}, {cy})
texture = ExtResource("12_ground")
''')
    for k, (c0, r0, rows) in enumerate(STAIR_SPOTS):
        x, top = LEFT + c0 * TILE, TOP + r0 * TILE
        n.append(f'[node name="Stairs{k + 1}" type="Sprite2D" parent="."]\nz_index = -8\nposition = Vector2({x + TILE}, {top + rows * TILE / 2})\n'
                 f'texture = ExtResource("st_{rows}")\n')
    # Canal bridges: the deck's centre lines up with the walkable bridge row.
    bw, bh = Image.open(bridge_png).size
    for k, (bx0, by0, bx1, by1) in enumerate(BRIDGES):
        rows = sorted({r for r, c in bridge_cells() if TOP + r * TILE <= W(bx0, by0)[1] + TILE and TOP + (r + 1) * TILE >= W(bx1, by1)[1] - TILE})
        cy = TOP + (rows[0] + rows[-1] + 1) * TILE / 2
        cx = (W(bx0, by0)[0] + W(bx1, by1)[0]) / 2
        n.append(f'[node name="CanalBridge{k + 1}" type="Sprite2D" parent="."]\nz_index = -8\n'
                 f'position = Vector2({cx}, {cy + bh / 2 - bridge_mid})\ntexture = ExtResource("{texture(bridge_png)}")\n')

    # Cliffs, sea and the town's outer walls, merged into rectangles; the gate line
    # closes the forest band so the north gate is the only way out.
    walls = merge_rects(blocked, LEFT, TOP, TILE)
    walls += [(LEFT - 40, TOP - 40, -24, TOP), (24, TOP - 40, RIGHT + 40, TOP),
              (-64, TOP - 80, -24, TOP - 40), (24, TOP - 80, 64, TOP - 40),
              # the gate line spans only the forest band (the meadow's cliff and a seal behind the
              # blue cottage's roof close its ends), so no open ground is walled off by it
              (W(336, 0)[0], GATE_Y - 12, -22, GATE_Y + 4), (22, GATE_Y - 12, W(1196, 0)[0], GATE_Y + 4),
              (W(1196, 0)[0] - 8, TOP, W(1196, 0)[0] + 8, GATE_Y + 4),
              (LEFT - 40, TOP, LEFT, BOTTOM), (RIGHT, TOP, RIGHT + 40, BOTTOM),
              (LEFT - 40, BOTTOM, RIGHT + 40, BOTTOM + 40)]
    n.append('[node name="Walls" type="StaticBody2D" parent="."]\n')
    for k, (x0, y0, x1, y1) in enumerate(walls):
        n.append(f'[node name="W{k}" type="CollisionShape2D" parent="Walls"]\nposition = Vector2({(x0 + x1) / 2}, {(y0 + y1) / 2})\n'
                 f'shape = SubResource("{shape(x1 - x0, y1 - y0)}")\n')

    # The lighthouse on the headland. Its lens sits just inside the door, in a notch in
    # the tower's base; the locked door gate closes the notch's mouth. What blocks you is
    # exactly what you see: the tower and its door.
    lx, ly = W(*LIGHTHOUSE)                                       # the tower's base line
    lh = OBJ + "lighthouse.png"
    n.append(f'''[node name="Lighthouse" type="StaticBody2D" parent="."]
position = Vector2({lx}, {ly})

[node name="Sprite" type="Sprite2D" parent="Lighthouse"]
position = Vector2(0, {bottom_offset(lh)})
texture = ExtResource("{texture(lh)}")

[node name="BaseWest" type="CollisionShape2D" parent="Lighthouse"]
position = Vector2(-24.5, -15)
shape = SubResource("{shape(19, 30)}")

[node name="BaseEast" type="CollisionShape2D" parent="Lighthouse"]
position = Vector2(24.5, -15)
shape = SubResource("{shape(19, 30)}")

[node name="BaseBack" type="CollisionShape2D" parent="Lighthouse"]
position = Vector2(0, -25)
shape = SubResource("{shape(30, 10)}")

[node name="LighthouseLight" type="PointLight2D" parent="."]
position = Vector2({lx}, {ly - 230})
texture_scale = 3.0
script = ExtResource("20_lamp")
max_energy = 1.2

[node name="LighthouseDoor" parent="." instance=ExtResource("10_gate")]
position = Vector2({lx}, {ly + 6})
gate_id = &"kalmora_lighthouse_door"

[node name="Card_lighthouse_lens" parent="." instance=ExtResource("6_pick")]
position = Vector2({lx}, {ly - 10})
card_id = &"lighthouse_lens"
behind_gate = &"kalmora_lighthouse_door"
''')
    shadow("building", lh, lx, ly)
    check_spot("lighthouse lens", lx, ly - 10, TOWN)

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
        + [(ex, ey), (mx, my), (fx, fy), (lx, ly + 6), (lx, ly - 10), (0, GATE_Y)]
    for card, (x, y) in cards:
        n.append(f'[node name="Card_{card}" parent="." instance=ExtResource("6_pick")]\nposition = Vector2({x}, {y})\ncard_id = &"{card}"\n')
    n.append(f'[node name="Card_salt_compass_2" parent="." instance=ExtResource("6_pick")]\nposition = Vector2({ex}, {ey})\ncard_id = &"salt_compass"\n')
    for k, p in enumerate(DUMMIES):
        x, y = W(*p)
        check_spot("dummy", x, y)
        taken.append((x, y))
        n.append(f'[node name="TrainingDummy{k + 1}" parent="." instance=ExtResource("7_dummy")]\nposition = Vector2({x}, {y})\n')

    solids = []   # world rects (x0, y0, x1, y1) of every collision footprint, for the reachability check

    def frames(kind):
        """SpriteFrames for one of the ANIMATED plants, from its horizontal strip; returns
        (sub-resource id, the frames' shared bottom offset, frame count)."""
        strip, count, fps = ANIMATED[kind]
        key = f"frames_{kind}"
        im = Image.open(strip)
        w, h = im.width // count, im.height
        bottom = max(b[3] for b in (im.crop((k * w, 0, (k + 1) * w, h)).getbbox() for k in range(count)) if b)
        if key not in subs:
            atlas = texture(strip)
            refs = []
            for k in range(count):
                subs[f"{key}_{k}"] = (f'[sub_resource type="AtlasTexture" id="{key}_{k}"]\natlas = ExtResource("{atlas}")\n'
                                      f'region = Rect2({k * w}, 0, {w}, {h})\n')
                refs.append(f'{{\n"duration": 1.0,\n"texture": SubResource("{key}_{k}")\n}}')
            subs[key] = (f'[sub_resource type="SpriteFrames" id="{key}"]\nanimations = [{{\n"frames": [{", ".join(refs)}],\n'
                         f'"loop": true,\n"name": &"default",\n"speed": {fps}\n}}]\n')
        return key, h / 2 - bottom, count

    def plant_sprite(parent, kind, k):
        """An animated plant sprite; neighbours start on different frames and play at
        slightly different speeds, so a row of palms doesn't sway in lockstep."""
        key, offset, count = frames(kind)
        speed = 0.85 + (k * 37 % 11) / 30
        return (f'[node name="Sprite" type="AnimatedSprite2D" parent="{parent}"]\nposition = Vector2(0, {offset})\n'
                f'sprite_frames = SubResource("{key}")\nautoplay = "default"\nframe = {k * 3 % count}\n'
                f'speed_scale = {speed:.2f}\n')

    def solid(node, path, x, y, fw, fh, animated=None, k=0):
        solids.append((x - fw / 2, y - fh, x + fw / 2, y))
        sprite = (plant_sprite(node, animated, k) if animated else
                  f'[node name="Sprite" type="Sprite2D" parent="{node}"]\nposition = Vector2(0, {bottom_offset(path)})\n'
                  f'texture = ExtResource("{texture(path)}")\n')
        return (f'[node name="{node}" type="StaticBody2D" parent="."]\nposition = Vector2({x}, {y})\n\n' + sprite +
                f'\n[node name="Base" type="CollisionShape2D" parent="{node}"]\nposition = Vector2(0, {-fh / 2})\n'
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

    yards = [(*W(*pos), fw) for _, _, pos, fw in BUILDINGS]   # front yards stay open

    def fits(x, y, clearance):
        r, c = cell_of(x, y)
        return (0 <= r < ROWS and 0 <= c < COLS and not blocked[r][c] and (r, c) not in stairs
                and not crowd(x, y, clearance) and not on_route(*C(x, y), clearance / SCALE)
                and not any(abs(x - bx) <= fw / 2 + 36 and by - 16 <= y <= by + 90 for bx, by, fw in yards))

    def place_check(name, x, y, clearance=18):
        """Decorations that don't fit (a wall, stairs, something already there) are
        nudged to the nearest open spot within a short reach, else skipped with a
        warning; they never block the build. Returns the spot used, or None."""
        for reach in range(0, 1 if name == "fence" else 49, 8):   # fences stay in line or go
            for dx, dy in ((0, 0),) if reach == 0 else [(reach * math.cos(t), reach * math.sin(t))
                                                         for t in (i * math.pi / 4 for i in range(8))]:
                if fits(x + dx, y + dy, clearance):
                    return (round(x + dx), round(y + dy))
        skipped.append(f"{name} at concept {C(x, y)}")
        return None

    tree_spots = []
    for k, (sprite, pos) in enumerate(TREES):
        path = OBJ + sprite + ".png"
        spot = place_check(sprite, *W(*pos), 26)
        if spot:
            x, y = spot
            taken.append((x, y))
            n.append(solid(f"{sprite.title()}{k + 1}", path, x, y, 16 if sprite == PALM else 28, 10, animated=sprite, k=k))
            shadow("tree", path, x, y)
            tree_spots.append((sprite, x, y))

    # Grass tufts swaying at the foot of the trees (decoration: they don't block). Only
    # on grass, never on a path or on something already placed.
    lawn = np.asarray(Image.open(SURFACE_PNG))[..., 0] > 0
    def on_grass(x, y):
        px, py = int(x - LEFT), int(y - TOP)
        return 0 <= py < lawn.shape[0] and 0 <= px < lawn.shape[1] and lawn[py, px]
    tufts = 0
    for sprite, tx, ty in tree_spots:
        for dx, dy in TUFT_RING[sprite]:
            x, y = tx + dx, ty + dy
            if not on_grass(x, y) or on_route(*C(x, y), 6) or crowd(x, y, 10):
                continue
            kind = ("tuft", "tuft_flowers")[(tufts * 5 + int(tx)) % 3 == 0]
            key, offset, count = frames(kind)
            tufts += 1
            n.append(f'[node name="Tuft{tufts}" type="AnimatedSprite2D" parent="."]\nposition = Vector2({x}, {y})\n'
                     f'offset = Vector2(0, {offset})\nsprite_frames = SubResource("{key}")\nautoplay = "default"\n'
                     f'frame = {tufts * 3 % count}\nspeed_scale = {0.85 + (tufts * 37 % 11) / 30:.2f}\n')

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
    n += bay_water(ground)
    # Everything that matters must be reachable on foot from the town spawn.
    lx, ly = W(*LIGHTHOUSE)
    solids += [(lx - 34, ly - 30, lx - 15, ly), (lx + 15, ly - 30, lx + 34, ly), (lx - 15, ly - 30, lx + 15, ly - 20)]
    solids += [(x - 12, y - 10, x + 12, y) for x, y in [W(*p) for _, p in CLUE_CRATES] + [W(*p) for p in DUMMIES]]
    targets = {**{f"spawn {k}": v for k, v in spawns.items()}, **{f"rival spot {k}": v for k, v in rival_spots.items()},
               **{f"card {k}": v for k, v in cards}, "north gate": (0, GATE_Y + 24), "lighthouse door": (lx, ly + 30),
               **{f"npc {n[0]}": W(*n[3]) for n in NPCS}, **{f"crate {k}": W(*p) for k, p in CLUE_CRATES}}
    for k, (c0, r0, rows) in enumerate(STAIR_SPOTS):
        targets[f"stairs {k + 1} top"] = (LEFT + (c0 + 1) * TILE, TOP + r0 * TILE - 12)
        targets[f"stairs {k + 1} bottom"] = (LEFT + (c0 + 1) * TILE, TOP + (r0 + rows) * TILE + 12)
    errors += unreachable(blocked, stairs, solids + walls, spawns["town"], targets, allowed=MEANT_UNREACHABLE)
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
