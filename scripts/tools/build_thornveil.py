"""Build Thornveil Forest (scenes/world/thornveil.tscn) from Jordan's concept.

Usage: python scripts/tools/build_thornveil.py

The layout is traced from docs/reference/thornveil_concept.webp (thornveil_layout.py:
terrace polygons, stairs, docks, bridges, all in the concept's pixels) and mapped
to the world at SCALE. Like Kalmora it is multilevel: the terraces are composed from
PixelLab cliff tilesets (terrain.py) -- grey-brown rock columns between terraces, rock
over the lake and down into the stream channels -- joined by stone stairs. On top:
Kalmora's meadow grass, dirt paths read straight from the concept's path colour, darker
forest floor where the concept is canopy, plank boardwalks and footbridges with real depth
(paint_boardwalk: a front beam, pilings, a shadow on the water, rails), streams that
end in pools at a drop instead of falling down the cliffs, and all the water
rolling with Kalmora's animated wave tile. Trees are the PixelLab-animated firs and oaks
(build_forest.py's scenes), planted densely where the concept shows forest and sparsely
in its lawns, never on a path, stairs or anything that matters.

Things to do: three chests (the stone circle, the lake island, the south-east clearing),
a trapper's camp by the lake with a resident who trades, the Heartwood shrine whose
spring heals, the great tree at the crossroads, readables that carry the story, briar
hounds in the wilder corners and the zone's four set cards.

Edit the layout here and in thornveil_layout.py, not in the editor.
"""
import math
import os
import random
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

os.chdir(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from terrain import CliffSet, CornerSet, compose, mask_rects, merge_rects  # noqa: E402
import thornveil_layout as L  # noqa: E402
from build_forest import write_tree_scene  # noqa: E402

TILE = 32
SCALE = 1.5                                         # world px per concept px
LEFT, TOP = -1088, -1504
COLS, ROWS = 68, 51
RIGHT, BOTTOM = LEFT + COLS * TILE, TOP + ROWS * TILE
WATER, LOW, MID, HIGH, TERRACE, TOP_LV = L.WATER, L.LOW, L.MID, L.HIGH, L.TERRACE, L.TOP

ART = "assets/sprites/tiles/thornveil/"
PROPS = ART + "props/"
FOREST = "assets/sprites/tiles/forest/props/"
K2 = "assets/sprites/tiles/kalmora2/"
GROUND_PNG = ART + "thornveil_ground.png"
LEVEL_PNG = ART + "thornveil_levels.png"
WATER_MASK = ART + "thornveil_water_mask.png"
STREAM_MASK = ART + "thornveil_stream_mask.png"
# Water frames (make_forest_water.py): the calm lake and the flowing streams.
WATER_ART = ART + "water/"
SCENE = "scenes/world/thornveil.tscn"


def W(cx, cy):
    """Concept pixel -> world position."""
    return (round(LEFT + cx * SCALE), round(TOP + cy * SCALE))


def C(x, y):
    return ((x - LEFT) / SCALE, (y - TOP) / SCALE)


def wall_down(pair):
    """Rows a cliff face hangs below its terrace's edge, over the lower ground (the
    concept draws every face there): taller between terraces further apart."""
    lo, hi = pair
    return min(2, hi - lo) if lo > WATER else min(2, (hi + 1) // 2)


# ------------------------------------------------------------------ terrain
LV = L.level_image()
WET_C, PATH_C = L.classify()
# The concept's paths, joined up where trees and shading break them and a little
# wider, so they read as the concept's broad golden roads.
from scipy import ndimage as _nd  # noqa: E402
PATH_C = _nd.binary_closing(_nd.binary_dilation(PATH_C, iterations=2), iterations=6) & ~WET_C
CANOPY_C = L.canopy()
STREAM_C = L.stream_mask()
STREAM_PX = None
BEAM_PX = None


def level_c(cx, cy):
    return int(LV[min(L.CH - 1, max(0, int(cy))), min(L.CW - 1, max(0, int(cx)))])


def level_at(x, y):
    return level_c(*C(x, y))


def cells_in(rect, pad=0):
    x0, y0, x1, y1 = rect
    (wx0, wy0), (wx1, wy1) = W(x0, y0), W(x1, y1)
    return {(r, c) for r in range(max(0, (wy0 - TOP) // TILE - pad), min(ROWS, (wy1 - 1 - TOP) // TILE + 1 + pad))
            for c in range(max(0, (wx0 - LEFT) // TILE), min(COLS, (wx1 - 1 - LEFT) // TILE + 1))}


STAIR_SPOTS = []   # (column, first row, rows, (lo, hi))


def resolve_stairs(levels):
    STAIR_SPOTS.clear()
    for cx, cy, (lo, hi) in L.STAIRS:
        x, y = W(cx, cy)
        c0 = int((x - LEFT) // TILE) - 1
        guess = round((y - TOP) / TILE)
        edge = next((r for r in sorted(range(guess - 5, guess + 6), key=lambda r: abs(r - guess))
                     if 0 <= r < ROWS and all(levels[r][c] == hi and levels[r + 1][c] == lo for c in (c0, c0 + 1, c0 + 2))), None)
        if edge is None:
            raise SystemExit(f"stairs at concept ({cx}, {cy}): no {hi}->{lo} edge near there")
        STAIR_SPOTS.append((c0, edge, 2 + wall_down((lo, hi)), (lo, hi)))


def stair_cells():
    return {(r0 + dr, c0 + dc) for c0, r0, rows, _ in STAIR_SPOTS for dr in range(rows) for dc in (0, 1)}


def bridge_span(rect):
    """A bridge's walkable cells: two rows (a comfortable width) centred on its rect,
    across the columns it spans."""
    x0, y0, x1, y1 = rect
    (wx0, wy0), (wx1, wy1) = W(x0, y0), W(x1, y1)
    r0 = round(((wy0 + wy1) / 2 - TOP) / TILE) - 1
    c0, c1 = (wx0 - LEFT) // TILE, (wx1 - 1 - LEFT) // TILE
    return {(r, c) for r in (r0, r0 + 1) for c in range(c0, c1 + 1)}


def soft_mask(fn, size, res=4, blur=5, jitter=0.18, seed=0):
    """A pixel mask of fn(cx, cy) (concept px) with rounded, slightly wandering edges."""
    W_, H_ = size
    gw, gh = W_ // res, H_ // res
    coarse = np.zeros((gh, gw), np.uint8)
    for j in range(gh):
        for i in range(gw):
            coarse[j, i] = 255 if fn(*C(LEFT + i * res + res / 2, TOP + j * res + res / 2)) else 0
    m = Image.fromarray(coarse).resize((W_, H_), Image.BILINEAR).filter(ImageFilter.GaussianBlur(blur))
    rng = np.random.default_rng(seed)
    noise = Image.fromarray((rng.random((H_ // 20 + 1, W_ // 20 + 1)) * 255).astype(np.uint8)).resize((W_, H_), Image.BICUBIC)
    return np.asarray(m) / 255.0 + (np.asarray(noise) / 255.0 - 0.5) * jitter > 0.5


def path_c(cx, cy):
    x, y = int(cx), int(cy)
    if not (0 <= x < L.CW and 0 <= y < L.CH):
        return False
    return bool(PATH_C[max(0, y - 2):y + 3, max(0, x - 2):x + 3].mean() > 0.4) or any(
        seg_dist(cx, cy, *a, *b) <= w for pts, w in EXTRA_PATHS for a, b in zip(pts, pts[1:]))


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy or 1)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


# Path pieces the concept leaves implied: out to the zone's exits.
EXTRA_PATHS = [
    ([(0, 176), (30, 172), (60, 165)], 14),              # west, to Lake Veyra
    ([(1336, 142), (1400, 150), (1448, 152)], 14),        # east, to the Warden's Grove
    ([(724, 0), (724, 40)], 16), ([(744, 1040), (744, 1086)], 16),
]


def build_terrain():
    levels = [[level_at(LEFT + c * TILE, TOP + r * TILE) for c in range(COLS + 1)] for r in range(ROWS + 1)]
    terrace = CliffSet(ART + "cliff/forest_terrace")
    rock = CliffSet(K2 + "cliff/sea_rock")
    # Grey rock columns between terraces, rock over the water. (A PixelLab root-bound
    # earth set was tried for the lower terraces: its side edges came out as loose vine
    # strands on the grass.)
    sets = {(lo, hi): (rock if lo == WATER else terrace) for lo in range(6) for hi in range(lo + 1, 6)}
    flat = {WATER: ((0, 1), "lower"), **{lv: ((1, 2), "upper" if lv > 1 else "lower") for lv in range(1, 6)}}
    down = {pair: wall_down(pair) for pair in sets}
    img, stand = compose(levels, sets, flat, TILE, grow_down=down)
    resolve_stairs(levels)
    stairs = stair_cells()

    decks = set()
    for r in range(ROWS):
        for c in range(COLS):
            px, py = C(LEFT + (c + 0.5) * TILE, TOP + (r + 0.5) * TILE)
            if any(seg_dist(px, py, *a, *b) <= w for pts, w in L.DOCKS for a, b in zip(pts, pts[1:])):
                decks.add((r, c))
    bridges = {}
    for k, rect in enumerate(L.BRIDGES):
        for cell in bridge_span(rect):
            bridges[cell] = k
    # Grass everywhere on land, then the paths, then darker forest floor under canopy.
    grass = CornerSet(K2 + "wang/grass_meadow")
    dirt = CornerSet(K2 + "wang/dirt")
    size = img.size
    tile_img = lambda t: np.tile(np.asarray(t.convert("RGBA")), (size[1] // TILE, size[0] // TILE, 1)).astype(np.float32)
    lawn, soil = tile_img(grass.tiles[15]), tile_img(dirt.tiles[15])
    land = np.kron(np.array([[1 if v >= LOW else 0 for v in row] for row in stand], np.uint8),
                   np.ones((TILE, TILE), np.uint8)).astype(bool)
    a = np.asarray(img).astype(np.float32)
    rng = np.random.default_rng(7)

    def noise(cell):
        n = (rng.random((size[1] // cell + 3, size[0] // cell + 3)) * 255).astype(np.uint8)
        return np.asarray(Image.fromarray(n).resize(((size[0] // cell + 3) * cell, (size[1] // cell + 3) * cell),
                                                    Image.BICUBIC))[:size[1], :size[0]] / 255.0
    # Cliff tiles bring their own grass along the tops; every flat pixel that is grassy
    # takes the meadow instead, so all grass is one grass.
    r_, g_, b_ = a[..., 0], a[..., 1], a[..., 2]
    grassy = (g_ > r_ + 30) & (g_ > b_ + 30)
    a = np.where((land | grassy)[..., None] & grassy[..., None], lawn, a)
    a = np.where(land[..., None], lawn, a)
    dirt_on = soft_mask(path_c, size, seed=2) & land
    # Warm, sunlit dirt, toward the concept's golden paths.
    soil = soil.copy()
    soil[..., :3] = np.clip(soil[..., :3] * np.array([1.1, 1.08, 0.92]) + np.array([14, 12, 6]), 0, 255)
    a = np.where(dirt_on[..., None], soil, a)
    near_grass = np.asarray(Image.fromarray((~dirt_on).astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(5))) > 0
    a[..., :3] = np.where((dirt_on & near_grass)[..., None], a[..., :3] * 0.8, a[..., :3])
    near_path = np.asarray(Image.fromarray(dirt_on.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(7))) > 0
    a[..., :3] = np.where((~dirt_on & near_path & land)[..., None], a[..., :3] * 0.88, a[..., :3])
    # Forest floor: deeper, cooler, dappled where the concept is under canopy.
    floor = soft_mask(lambda cx, cy: bool(CANOPY_C[min(L.CH - 1, int(cy)), min(L.CW - 1, int(cx))]), size, blur=14,
                      jitter=0.3, seed=4) & land & ~dirt_on
    dapple = np.round((noise(60) * 0.6 + noise(22) * 0.4 - 0.5) * 4) / 4
    shade = (0.84 + dapple * 0.14)[..., None] * np.array([0.86, 0.9, 0.84])
    a[..., :3] = np.where(floor[..., None], a[..., :3] * shade, a[..., :3])
    # Open lawns keep the meadow's own light, with a faint dapple too.
    a[..., :3] = np.where((land & ~floor & ~dirt_on)[..., None], a[..., :3] * (0.97 + dapple[..., None] * 0.06), a[..., :3])

    # Streams: ribbons of water painted across the terraces, with a dark wet bank and
    # paler shallows along the edge. They never run down a cliff face (painted falls
    # never looked like water falling): a stream that reaches a drop ends in a round
    # pool at the top, and starts again from a spring pool at the foot.
    streams = soft_mask(lambda cx, cy: bool(STREAM_C[min(L.CH - 1, int(cy)), min(L.CW - 1, int(cx))]), size,
                        res=4, blur=4, jitter=0.25, seed=9)
    near = lambda m, px: np.asarray(Image.fromarray(m.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(px * 2 + 1))) > 0
    wall_px = np.kron(np.array([[1 if (v < 0 and (r, c) not in stairs) else 0 for c, v in enumerate(row)]
                                for r, row in enumerate(stand)], np.uint8), np.ones((TILE, TILE), np.uint8)).astype(bool)
    cut = streams & wall_px
    streams &= ~wall_px
    ends = near(cut, 3) & streams
    blur = np.asarray(Image.fromarray(ends.astype(np.uint8) * 255).filter(ImageFilter.GaussianBlur(9))).astype(float)
    streams |= (blur > 22) & ~near(wall_px, 2)
    # Where a stream meets the lake it is the lake (no paler stream water laid over it).
    lake_cells = np.kron(np.array([[1 if v == WATER else 0 for v in row] for row in stand], np.uint8),
                         np.ones((TILE, TILE), np.uint8)).astype(bool)
    streams &= ~lake_cells
    bank = near(streams, 3) & ~streams & ~lake_cells
    shallow = streams & near(~streams, 3)
    a[..., :3] = np.where(bank[..., None], a[..., :3] * np.array([0.55, 0.52, 0.48]), a[..., :3])
    a[..., :3] = np.where(streams[..., None], np.array([30, 104, 204], np.float32), a[..., :3])
    a[..., :3] = np.where(shallow[..., None], np.array([70, 160, 214], np.float32), a[..., :3])
    a[..., 3] = np.where(streams | bank, 255, a[..., 3])
    out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
    out = grade(out, stand, decks)
    water_px = np.kron(np.array([[1 if v == WATER else 0 for v in row] for row in stand], np.uint8),
                       np.ones((TILE, TILE), np.uint8)).astype(bool) | streams
    bridge_set = set(bridges)
    paint_boardwalk(out, decks | bridge_set, water_px, across=bridge_set)

    cover = streams.reshape(ROWS, TILE, COLS, TILE).mean(axis=(1, 3))
    wet_cells = {(r, c) for r in range(ROWS) for c in range(COLS) if cover[r, c] > 0.35}
    walkable = [[((stand[r][c] >= LOW and (r, c) not in wet_cells) or (r, c) in stairs or (r, c) in decks
                  or (r, c) in bridges) for c in range(COLS)] for r in range(ROWS)]
    blocked = [[not walkable[r][c] for c in range(COLS)] for r in range(ROWS)]
    global STREAM_PX
    # (no stream water animates over a dock or bridge)
    covered = np.zeros(streams.shape, bool)
    for r, c in decks | set(bridges):
        covered[r * TILE:(r + 1) * TILE, c * TILE:(c + 1) * TILE] = True
    STREAM_PX = streams & ~covered
    # Level map: red = level * 40 (255 = cliff/stairs); green marks decks and bridges.
    lm = Image.new("RGB", (COLS, ROWS))
    bridge_level = {k: level_c(*((rect[0] + rect[2]) / 2 - 40, (rect[1] + rect[3]) / 2)) or MID
                    for k, rect in enumerate(L.BRIDGES)}
    for r in range(ROWS):
        for c in range(COLS):
            v = stand[r][c]
            if (r, c) in stairs or (blocked[r][c] and (r, c) not in decks and (r, c) not in bridges):
                lm.putpixel((c, r), (255, 0, 0))
            elif (r, c) in decks:
                lm.putpixel((c, r), (MID * 40, 255, 0))
            elif (r, c) in bridges:
                lm.putpixel((c, r), (bridge_level[bridges[(r, c)]] * 40, 255, 0))
            else:
                lm.putpixel((c, r), (v * 40, 0, 0))
    lm.save(LEVEL_PNG)
    water_cells = {(r, c) for r in range(ROWS) for c in range(COLS)
                   if (stand[r][c] == WATER or (r, c) in wet_cells) and (r, c) not in decks and (r, c) not in bridges}
    return out, stand, blocked, stairs, decks, set(bridges), floor, dirt_on, water_cells


def paint_boardwalk(img, cells, water_px, across=()):
    """Plank boardwalks over the water, with depth: boards (laid across the way you
    walk), a dark outline, a front beam where the deck's south edge stands over the
    water, pilings below it every so often, the deck's shadow on the water, and a rail
    with posts along every edge that faces water. `across`: cells whose boards run
    north-south (bridges you cross east-west)."""
    a = np.asarray(img).astype(np.float32)
    H, W_ = a.shape[:2]
    deck = np.zeros((H, W_), bool)
    vertical = np.zeros((H, W_), bool)
    for r, c in cells:
        deck[r * TILE:(r + 1) * TILE, c * TILE:(c + 1) * TILE] = True
        # boards run across the way you walk: east-west runs get north-south boards
        ew = ((r, c - 1) in cells or (r, c + 1) in cells) and not ((r - 1, c) in cells or (r + 1, c) in cells)
        if ew or (r, c) in across:
            vertical[r * TILE:(r + 1) * TILE, c * TILE:(c + 1) * TILE] = True
    ys, xs = np.mgrid[0:H, 0:W_]
    wood = np.array([150, 104, 62], np.float32)
    # Boards 6px wide, each its own shade, joints staggered.
    along = np.where(vertical, xs, ys)
    other = np.where(vertical, ys, xs)
    board = along // 6
    shade = 0.86 + ((board * 37) % 7) / 7.0 * 0.22
    joint = ((other + (board % 3) * 23) % 64) == 0
    seam = (along % 6) == 0
    col = wood[None, None, :] * shade[..., None]
    col = np.where(seam[..., None], np.array([92, 60, 36], np.float32), col)
    col = np.where(joint[..., None], np.array([104, 68, 40], np.float32), col)
    col = np.where(((along % 6) == 1)[..., None], col * 1.12, col)          # each board's lit edge
    # Water below and around (for the beam, pilings, shadow and rails).
    open_water = water_px & ~deck
    # Shadow on the water: the deck shifted down and right.
    shadow = np.zeros_like(deck)
    shadow[10:, 4:] = deck[:-10, :-4]
    shadow &= open_water
    a[..., :3] = np.where(shadow[..., None], a[..., :3] * 0.62, a[..., :3])
    a[..., :3] = np.where(deck[..., None], col, a[..., :3])
    a[..., 3] = np.where(deck, 255, a[..., 3])
    # Front beam: the 6px under every south edge that hangs over water.
    beam = np.zeros_like(deck)
    for k in range(1, 7):
        step = np.zeros_like(deck)
        step[k:, :] = deck[:-k, :]
        beam |= step
    # (a bridge stands up off its banks: its beam shows over land too)
    bridge_px = np.zeros_like(deck)
    for r, c in across:
        bridge_px[r * TILE:(r + 1) * TILE, c * TILE:(c + 1) * TILE] = True
    below_bridge = np.zeros_like(deck)
    below_bridge[7:, :] = bridge_px[:-7, :]
    beam &= ~deck & (open_water | below_bridge)
    a[..., :3] = np.where(beam[..., None], np.array([84, 54, 32], np.float32), a[..., :3])
    global BEAM_PX
    BEAM_PX = beam & open_water           # the deck's face over water: water to walk on
    edge_low = np.zeros_like(deck)
    edge_low[6:, :] = deck[:-6, :]
    edge_low &= beam
    a[..., :3] = np.where(edge_low[..., None], np.array([52, 32, 18], np.float32), a[..., :3])
    # Pilings: posts down into the water under the beam every 24px.
    bottom = beam & ~np.vstack([beam[1:], np.zeros((1, W_), bool)])
    for y, x in zip(*np.nonzero(bottom)):
        if x % 24 in (2, 3, 4, 5):
            y1 = min(H, y + 10)
            seg = open_water[y:y1, x]
            a[y:y1, x, :3] = np.where(seg[:, None], np.array([70, 44, 26], np.float32) * (0.9 if x % 24 == 2 else 1.0),
                                      a[y:y1, x, :3])
            BEAM_PX[y:y1, x] |= seg
            if y1 < H and open_water[y1 - 1, x]:
                a[y1 - 1, max(0, x - 2):x + 3, :3] = np.minimum(255, a[y1 - 1, max(0, x - 2):x + 3, :3] * 1.35)
    # Outline round the deck.
    grown = np.asarray(Image.fromarray(deck.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(3))) > 0
    rim = grown & ~deck & ~beam
    a[..., :3] = np.where(rim[..., None], np.array([60, 38, 22], np.float32), a[..., :3])
    BEAM_PX |= rim & open_water
    out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
    # Rails along every edge facing water: a rail with a highlight and posts every 16px.
    d = ImageDraw.Draw(out)
    rail, light, post = (96, 60, 34, 255), (184, 134, 82, 255), (64, 38, 20, 255)
    for r, c in cells:
        x, y = c * TILE, r * TILE
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if (nr, nc) in cells:
                continue
            probe = (min(H - 1, max(0, y + TILE // 2 + dr * (TILE // 2 + 3))), min(W_ - 1, max(0, x + TILE // 2 + dc * (TILE // 2 + 3))))
            # a bridge has rails along both long sides; the dock wherever it meets water
            if not water_px[probe] and not ((r, c) in across and dr):
                continue
            if dr:
                ry = y + (2 if dr < 0 else TILE - 4)
                for px in range(x + 2, x + TILE, 16):
                    d.rectangle((px, ry - 6, px + 2, ry + 1), fill=post)
                d.rectangle((x, ry - 6, x + TILE - 1, ry - 5), fill=rail)
                d.line((x, ry - 6, x + TILE - 1, ry - 6), fill=light)
            else:
                rx = x + (2 if dc < 0 else TILE - 4)
                d.rectangle((rx, y, rx + 1, y + TILE - 1), fill=rail)
                d.line((rx, y, rx, y + TILE - 1), fill=light)
                for py in range(y + 6, y + TILE, 16):
                    d.rectangle((rx - 1, py - 4, rx + 2, py + 1), fill=post)
    img.paste(out)


def grade(img, stand, decks):
    """The concept's palette: deep saturated greens, bright blue water."""
    a = np.asarray(img).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    grass = (g > r + 18) & (g > b + 18)
    a[..., 0] = np.where(grass, r * 0.40 + g * 0.26 + 2, r)
    a[..., 1] = np.where(grass, g * 0.80 + 4, g)
    a[..., 2] = np.where(grass, b * 0.24 + g * 0.2 + 2, b)
    water = np.kron(np.array([[1 if (v == WATER and (rr, c) not in decks) else 0 for c, v in enumerate(row)]
                              for rr, row in enumerate(stand)], np.uint8), np.ones((TILE, TILE), np.uint8)).astype(bool)
    deep = np.array([24, 96, 196], np.float32)
    for i in range(3):
        a[..., i] = np.where(water, a[..., i] * 0.35 + deep[i] * 0.65, a[..., i])
    out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
    from PIL import ImageEnhance
    alpha = out.getchannel("A")
    out = ImageEnhance.Contrast(ImageEnhance.Color(out.convert("RGB")).enhance(1.15)).enhance(1.06).convert("RGBA")
    out.putalpha(alpha)
    return out


def build_stairs():
    """Kalmora's grey stone stairs stretched to each flight's height."""
    src = Image.open(K2 + "objects/stairs.png").convert("RGBA")
    src = src.crop(src.getbbox())
    w, h = src.size
    paths = {}
    for rows in {rows for _, _, rows, _ in STAIR_SPOTS}:
        target = rows * TILE
        top, bottom, mid = src.crop((0, 0, w, 14)), src.crop((0, h - 14, w, h)), src.crop((0, 14, w, h - 14))
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
SPAWNS = {"from_kalmora": (744, 1040), "from_sorenda": (724, 60), "from_lake": (40, 176), "from_grove": (1410, 150)}
EXITS = [  # (node, concept point on the map edge, target scene, target spawn, rotated)
    ("ToKalmora", (744, 1086), "res://scenes/world/kalmora.tscn", "from_thornveil", False),
    ("ToSorenda", (724, 0), "res://scenes/world/sorenda.tscn", "from_thornveil", False),
    ("ToLake", (0, 176), "res://scenes/world/lake_veyra.tscn", "from_thornveil", True),
    ("ToGrove", (1448, 152), "res://scenes/world/wardens_grove.tscn", "from_thornveil", True),
]
GATES = [(724, 44), (744, 1010)]                    # the banner towers on the north and south roads
HOUNDS = [(330, 110), (560, 250), (1230, 60), (1100, 430), (1000, 640), (420, 800), (1000, 940), (160, 900)]
BOARS = [(820, 520), (330, 880), (1150, 890)]       # moss boars: tougher, slower, they charge
RIVAL_SPOTS = {"raider": (540, 236), "runner": (1100, 420), "hoarder": (600, 470)}

# The trapper's camp above the lake: Tobin, a badger-striped hound who traps for the
# Sorenda furriers and trades what racers need.
CAMP = {"tent": (140, 224), "fire": (196, 236), "npc": (190, 212)}
# Chests: (id, concept px, gold, hint, card). The zone's set cards are in chests, never
# lying on the ground; whoever opens one first (player or rival) takes it.
CHESTS = [
    ("stone_circle", (962, 248), 60, "The stones hum when you stand among them.", "owl_quill"),
    ("lake_island", (130, 520), 120, "Salt-stiff rope still ties the lid.", "", ("sea_salt_elixir", 1)),
    ("south_clearing", (1283, 942), 70, "A hunter's cache, hidden in the ferns.", "", ("smoked_fish", 3)),
    ("camp_cache", (96, 196), 0, "Tobin's spare kit, the lid wedged shut with a stone.", "fern_sigil"),
    ("heartwood", (1352, 452), 0, "Cradled in the Heartwood's roots, the wood warm to the touch.", "elderwood_heart"),
    ("meadow_stump", (470, 760), 0, "Stuffed into the hollow of an old stump, under the moss.", "bark_rune"),
]
BUTTERFLIES = [(722, 520, 3), (960, 300, 2), (1352, 470, 3), (200, 250, 2), (560, 820, 2), (1280, 930, 2)]
CLEARINGS = [(962, 250, 190), (1352, 450, 200), (160, 215, 150), (722, 560, 210), (1283, 942, 120),
             (130, 520, 80), (724, 60, 140), (744, 1010, 150)]    # (concept x, y, world radius)
SHRINE = {"fountain": (1352, 488), "tree": (1352, 412)}
GREAT_TREE = (722, 560)
RUNE_STONES = [(1292, 452), (1296, 500), (1408, 446), (1414, 500), (1300, 384), (1410, 380)]
RUIN_PILLARS = [(912, 236), (1000, 226), (1020, 262), (1022, 300), (900, 290)]
LANTERNS = [(632, 548), (814, 546), (486, 250), (770, 236), (1046, 282), (1244, 146), (1094, 376),
            (160, 76), (716, 880), (420, 748), (1272, 736), (938, 400)]
FALLEN_LOGS = [(1300, 96), (1340, 900)]
FENCES = ([(x, 62) for x in range(446, 660, 16)] + [(x, 62) for x in range(790, 900, 16)]
          + [(x, 48) for x in range(1000, 1090, 16)]
          + [(x, 1004) for x in range(470, 560, 16)] + [(x, 996) for x in range(596, 660, 16)]
          + [(x, 1004) for x in range(790, 880, 16)] + [(x, 996) for x in range(1190, 1330, 16)]
          + [(x, 108) for x in range(16, 70, 16)] + [(x, 870) for x in range(820, 880, 16)])
BENCHES = [(722, 606)]
READABLES = [
    ("The great tree's stone ring", (722, 600), [
        "A ring of old stones round the great tree, worn smooth by hands. Carved into one: 'Here the roads meet. Here the racers rest. Here we count them going, and fewer coming back.'",
    ]),
    ("A trail marker", (632, 560), [
        "North: Sorenda. South: Kalmora and the sea. West, past the lake: Veyra. East, up the ridge: the Warden's Grove.",
        "Someone has scratched a red sun into the post, and an arrow pointing east.",
    ]),
    ("The Heartwood spring", (1352, 510), [
        "Clear water rises in an old stone basin under the Heartwood. The rune stones around it glow faintly blue. Drink, and the ache goes out of you.",
        "Round the rim, very old letters: 'Given freely, before the Race. Before the counting.'",
    ]),
    ("Standing stones", (960, 290), [
        "Five weathered pillars in a ring. Each carries the same worn carving: a crown, and under it, a line of small figures bent double, carrying something on their backs.",
    ]),
    ("A note pinned to the dock", (260, 300), [
        "'Boat's for hire. Leave a coin in the tin, bring her back. Mind the island - the old chest out there's been waiting for a brave one since my grandad's day. - T.'",
    ]),
]


def main():
    ground, stand, blocked, stairs, decks, bridge_cells, floor, dirt_on, water_cells = build_terrain()
    stair_png = build_stairs()
    errors = []

    def cell_of(x, y):
        return int((y - TOP) // TILE), int((x - LEFT) // TILE)

    def walk_ok(x, y):
        r, c = cell_of(x, y)
        return 0 <= r < ROWS and 0 <= c < COLS and not blocked[r][c]

    def ground_ok(x, y):
        """Walkable earth: not a dock or bridge deck."""
        return walk_ok(x, y) and cell_of(x, y) not in decks and cell_of(x, y) not in bridge_cells

    def check_spot(name, x, y):
        if not walk_ok(x, y):
            errors.append(f"{name} at concept {tuple(round(v) for v in C(x, y))} is not on walkable ground")

    subs = {}

    def shape(w, h):
        key = f"R{w:g}x{h:g}".replace(".", "_")
        subs[key] = f'[sub_resource type="RectangleShape2D" id="{key}"]\nsize = Vector2({w}, {h})\n'
        return key

    ext = [
        ('Script', "res://scripts/world/zone.gd", "1_zone"),
        ('PackedScene', "res://scenes/characters/player.tscn", "2_player"),
        ('PackedScene', "res://scenes/ui/hud.tscn", "3_hud"),
        ('PackedScene', "res://scenes/ui/binder.tscn", "4_binder"),
        ('PackedScene', "res://scenes/characters/briar_hound.tscn", "7_hound"),
        ('SpriteFrames', "res://assets/sprites/monsters/briar_hound/briar_hound_frames.tres", "8_hound_frames"),
        ('PackedScene', "res://scenes/characters/moss_boar.tscn", "7_boar"),
        ('PackedScene', "res://scenes/systems/zone_exit.tscn", "9_exit"),
        ('Texture2D', "res://" + GROUND_PNG, "10_ground"),
        ('Texture2D', "res://" + LEVEL_PNG, "11_levels"),
        ('PackedScene', "res://scenes/characters/npc.tscn", "12_npc"),
        ('Script', "res://scripts/systems/lamp_light.gd", "13_lamp"),
        ('Script', "res://scripts/systems/readable.gd", "14_read"),
        ('PackedScene', "res://scenes/ui/dialogue_box.tscn", "15_dialogue"),
        ('PackedScene', "res://scenes/ui/shop_panel.tscn", "16_shop"),
        ('Texture2D', "res://" + WATER_MASK, "17_watermask"),
        ('Script', "res://scripts/world/tiled_animation.gd", "18_tiled"),
        ('Texture2D', "res://" + WATER_ART + "lake.png", "19_waves"),
        ('Texture2D', "res://" + STREAM_MASK, "17_streammask"),
        ('Texture2D', "res://" + WATER_ART + "stream_flow.png", "19_flow"),
        ('Script', "res://scripts/systems/chest.gd", "20_chest"),
        ('Script', "res://scripts/systems/healing_spring.gd", "21_spring"),
        ('PackedScene', "res://scenes/world/props/great_tree.tscn", "22_great"),
        ('SpriteFrames', "res://assets/sprites/npcs/tobin/tobin_frames.tres", "23_tobin"),
    ]
    for rows, path in stair_png.items():
        ext.append(('Texture2D', "res://" + path, f"st_{rows}"))
    tex = {}

    def texture(path):
        if path not in tex:
            tex[path] = f"t{len(tex)}_{os.path.basename(path)[:-4]}"
            ext.append(('Texture2D', "res://" + path, tex[path]))
        return tex[path]

    scripts = {}

    def script_res(path):
        if path not in scripts:
            scripts[path] = f"s{len(scripts)}_{os.path.basename(path)[:-3]}"
            ext.append(('Script', path, scripts[path]))
        return scripts[path]

    def bottom_offset(path):
        im = Image.open(path)
        return im.height / 2 - im.getbbox()[3]

    shadows = []
    n = []
    cx, cy = (LEFT + RIGHT) / 2, (TOP + BOTTOM) / 2
    n.append(f'''[node name="Thornveil" type="Node2D"]
y_sort_enabled = true
script = ExtResource("1_zone")
display_name = "Thornveil Forest"
level_map = ExtResource("11_levels")
level_cell = {TILE}
level_origin = Vector2({LEFT}, {TOP})

[node name="GroundTiles" type="Sprite2D" parent="."]
z_index = -10
position = Vector2({cx}, {cy})
texture = ExtResource("10_ground")
''')
    for k, (c0, r0, rows, _) in enumerate(STAIR_SPOTS):
        x, top = LEFT + c0 * TILE, TOP + r0 * TILE
        n.append(f'[node name="Stairs{k + 1}" type="Sprite2D" parent="."]\nz_index = -8\n'
                 f'position = Vector2({x + TILE}, {top + rows * TILE / 2})\ntexture = ExtResource("st_{rows}")\n')
    # (Bridges and the dock are painted into the ground by paint_boardwalk.)

    cliff = [[blocked[r][c] and (r, c) not in water_cells for c in range(COLS)] for r in range(ROWS)]
    walls = merge_rects(cliff, LEFT, TOP, TILE)
    # Water blocks exactly where it shows (a few px in from its edge), except under
    # the bridges and the dock.
    open_decks = [(LEFT + c * TILE, TOP + r * TILE, LEFT + (c + 1) * TILE, TOP + (r + 1) * TILE)
                  for r, c in decks | bridge_cells]
    walls += mask_rects(water_pixels(ground, stand, decks) | BEAM_PX, LEFT, TOP, step=8, erode=2, clear=open_decks)
    # The map's edges; exits leave gaps in them.
    walls += [(LEFT - 40, TOP - 40, RIGHT + 40, TOP), (LEFT - 40, BOTTOM, RIGHT + 40, BOTTOM + 40),
              (LEFT - 40, TOP, LEFT, BOTTOM), (RIGHT, TOP, RIGHT + 40, BOTTOM)]
    gaps = []
    for _, pos, *_ in EXITS:
        gaps.append(W(*pos))

    def cut(rect):
        x0, y0, x1, y1 = rect
        for gx, gy in gaps:
            if x0 <= gx <= x1 and y0 - 1 <= gy <= y1 + 1:
                if x1 - x0 > y1 - y0:
                    return cut((x0, y0, gx - 40, y1)) + cut((gx + 40, y0, x1, y1))
                return cut((x0, y0, x1, gy - 40)) + cut((x0, gy + 40, x1, y1))
        return [rect] if x1 > x0 and y1 > y0 else []
    walls = [piece for rect in walls for piece in cut(rect)]
    n.append('[node name="Walls" type="StaticBody2D" parent="."]\n')
    for k, (x0, y0, x1, y1) in enumerate(walls):
        n.append(f'[node name="W{k}" type="CollisionShape2D" parent="Walls"]\nposition = Vector2({(x0 + x1) / 2}, {(y0 + y1) / 2})\n'
                 f'shape = SubResource("{shape(x1 - x0, y1 - y0)}")\n')

    # Exits, spawns, rivals.
    n.append('[node name="Spawns" type="Node2D" parent="."]\n')
    spawns = {k: W(*v) for k, v in SPAWNS.items()}
    for name, (x, y) in spawns.items():
        check_spot(name, x, y)
        n.append(f'[node name="{name}" type="Marker2D" parent="Spawns"]\nposition = Vector2({x}, {y})\n')
    exits = {}
    for name, pos, scene, spawn, rotated in EXITS:
        x, y = W(*pos)
        x = min(max(x, LEFT + 4), RIGHT - 4)
        y = min(max(y, TOP + 4), BOTTOM - 4)
        exits[name] = (x, y)
        n.append(f'[node name="{name}" parent="." instance=ExtResource("9_exit")]\nposition = Vector2({x}, {y})\n'
                 + ("rotation = 1.5708\n" if rotated else "") + f'target_scene = "{scene}"\ntarget_spawn = &"{spawn}"\n')
    n.append('[node name="RivalSpots" type="Node2D" parent="."]\n')
    rivals = {k: W(*v) for k, v in RIVAL_SPOTS.items()}
    for name, (x, y) in rivals.items():
        check_spot(f"rival {name}", x, y)
        n.append(f'[node name="{name}" type="Marker2D" parent="RivalSpots"]\nposition = Vector2({x}, {y})\n')

    taken = list(spawns.values()) + list(rivals.values()) + list(exits.values())
    solids = []

    def solid(node, path, x, y, fw, fh, extra=""):
        solids.append((x - fw / 2, y - fh, x + fw / 2, y))
        return (f'[node name="{node}" type="StaticBody2D" parent="."]\nposition = Vector2({x}, {y})\n{extra}\n'
                f'[node name="Sprite" type="Sprite2D" parent="{node}"]\nposition = Vector2(0, {bottom_offset(path)})\n'
                f'texture = ExtResource("{texture(path)}")\n\n'
                f'[node name="Base" type="CollisionShape2D" parent="{node}"]\nposition = Vector2(0, {-fh / 2})\n'
                f'shape = SubResource("{shape(fw, fh)}")\n')

    def shadow(x, y, rx, ry=None, k=0.45):
        shadows.append((x + 4, y - 2, rx, ry or max(5, rx * 0.3), k))

    # Gates on the north and south roads.
    gp = K2 + "objects/gate_pillars.png"
    for k, pos in enumerate(GATES):
        x, y = W(*pos)
        n.append(f'[node name="GatePillars{k + 1}" type="Sprite2D" parent="."]\nposition = Vector2({x}, {y})\n'
                 f'offset = Vector2(0, {bottom_offset(gp)})\ntexture = ExtResource("{texture(gp)}")\n')
        solids += [(x - 96, y - 20, x - 50, y), (x + 50, y - 20, x + 96, y)]
        n.append(f'[node name="GateBase{k + 1}" type="StaticBody2D" parent="."]\nposition = Vector2({x}, {y})\n\n'
                 f'[node name="West" type="CollisionShape2D" parent="GateBase{k + 1}"]\nposition = Vector2(-73, -10)\n'
                 f'shape = SubResource("{shape(46, 20)}")\n\n'
                 f'[node name="East" type="CollisionShape2D" parent="GateBase{k + 1}"]\nposition = Vector2(73, -10)\n'
                 f'shape = SubResource("{shape(46, 20)}")\n')
        shadow(x, y, 110, 12, 0.4)
        taken.append((x, y))

    # Cards and hounds.
    for k, pos in enumerate(HOUNDS):
        x, y = W(*pos)
        check_spot(f"hound {k + 1}", x, y)
        taken.append((x, y))
        n.append(f'[node name="BriarHound{k + 1}" parent="." instance=ExtResource("7_hound")]\nposition = Vector2({x}, {y})\n'
                 f'sprite_frames = ExtResource("8_hound_frames")\n')

    for k, pos in enumerate(BOARS):
        x, y = W(*pos)
        check_spot(f"boar {k + 1}", x, y)
        taken.append((x, y))
        n.append(f'[node name="MossBoar{k + 1}" parent="." instance=ExtResource("7_boar")]\nposition = Vector2({x}, {y})\n')

    # The trapper's camp.
    tx, ty = W(*CAMP["tent"])
    n.append(solid("Tent", PROPS + "tent.png", tx, ty, 90, 26))
    shadow(tx, ty, 50, 12)
    fx, fy = W(*CAMP["fire"])
    n.append(f'[node name="Campfire" type="AnimatedSprite2D" parent="."]\nposition = Vector2({fx}, {fy})\n'
             f'offset = Vector2(0, {bottom_offset(PROPS + "campfire.png")})\nsprite_frames = SubResource("frames_campfire")\n'
             f'autoplay = "default"\n\n[node name="CampfireLight" type="PointLight2D" parent="."]\n'
             f'position = Vector2({fx}, {fy - 14})\ntexture_scale = 1.2\nscript = ExtResource("13_lamp")\nmax_energy = 0.7\n')
    solids.append((fx - 14, fy - 10, fx + 14, fy))
    n.append(f'[node name="FireBase" type="StaticBody2D" parent="."]\nposition = Vector2({fx}, {fy})\n\n'
             f'[node name="CollisionShape2D" type="CollisionShape2D" parent="FireBase"]\nposition = Vector2(0, -5)\n'
             f'shape = SubResource("{shape(28, 10)}")\n')
    nx, ny = W(*CAMP["npc"])
    check_spot("Tobin", nx, ny)
    n.append(f'''[node name="Npc_tobin" parent="." instance=ExtResource("12_npc")]
position = Vector2({nx}, {ny})
npc_id = &"tobin"
display_name = "Tobin"
sprite_frames = ExtResource("23_tobin")
lines = PackedStringArray("Tobin. I trap for the Sorenda furriers and sell to whoever's passing. Racers pass a lot.", "The chest on the island? My grandad's grandad left it. Take the dock, cross the plank bridge. Nobody's been brave enough to wade the last bit. You won't need to.", "Stones up on the north terrace hum at dusk. Stand in the ring and listen, and you'll find what they're guarding.", "Carts go east on the ridge road at night, no lamps. Red sun on the crates. I don't trap near that road anymore.")
shop_stock = Array[StringName]([&"second_wind", &"lockbox_seal"])
''')
    taken += [(tx, ty), (fx, fy), (nx, ny)]

    # Chests.
    for cid, pos, gold, hint, card, *extra in CHESTS:
        item, item_n = extra[0] if extra else ("", 1)
        x, y = W(*pos)
        check_spot(f"chest {cid}", x, y)
        taken.append((x, y))
        solids.append((x - 16, y - 10, x + 16, y))
        n.append(f'''[node name="Chest_{cid}" type="StaticBody2D" parent="."]
position = Vector2({x}, {y})
script = ExtResource("20_chest")
chest_id = &"thornveil_{cid}"
card_id = &"{card}"
gold = {gold}
item_id = &"{item}"
item_count = {item_n}
hint = "{hint}"
closed_texture = ExtResource("{texture(PROPS + "chest.png")}")
open_texture = ExtResource("{texture(PROPS + "chest_open.png")}")

[node name="Base" type="CollisionShape2D" parent="Chest_{cid}"]
position = Vector2(0, -5)
shape = SubResource("{shape(32, 10)}")
''')
        shadow(x, y, 18, 6, 0.4)

    # The Heartwood shrine: its great tree, the spring, the rune stones.
    sx, sy = W(*SHRINE["tree"])
    n.append(f'[node name="Heartwood" parent="." instance=ExtResource("22_great")]\nposition = Vector2({sx}, {sy})\n')
    shadow(sx, sy, 60, 16, 0.5)
    fx, fy = W(*SHRINE["fountain"])
    n.append(solid("Spring", PROPS + "shrine_fountain.png", fx, fy, 76, 30,
                   extra='script = ExtResource("21_spring")\n'))
    shadow(fx, fy, 44, 10)
    taken += [(sx, sy), (fx, fy)]
    for k, pos in enumerate(RUNE_STONES):
        x, y = W(*pos)
        n.append(solid(f"RuneStone{k + 1}", PROPS + "rune_stone.png", x, y, 26, 12))
        n.append(f'[node name="RuneGlow{k + 1}" type="PointLight2D" parent="."]\nposition = Vector2({x}, {y - 36})\n'
                 f'color = Color(0.45, 0.75, 1, 1)\ntexture_scale = 0.9\nscript = ExtResource("13_lamp")\nalways_on = true\nmax_energy = 0.6\n')
        shadow(x, y, 16, 6)
        taken.append((x, y))
    for k, pos in enumerate(RUIN_PILLARS):
        x, y = W(*pos)
        n.append(solid(f"Pillar{k + 1}", PROPS + "ruin_pillar.png", x, y, 24, 12))
        shadow(x, y, 16, 6)
        taken.append((x, y))
    gx, gy = W(*GREAT_TREE)
    n.append(f'[node name="GreatTree" parent="." instance=ExtResource("22_great")]\nposition = Vector2({gx}, {gy})\n')
    shadow(gx, gy, 64, 18, 0.5)
    taken.append((gx, gy))
    for k, pos in enumerate(BENCHES):
        x, y = W(*pos)
        n.append(solid(f"Bench{k + 1}", "assets/sprites/tiles/kalmora/props/bench_wood.png", x, y, 40, 8))
        taken.append((x, y))
    for k, pos in enumerate(LANTERNS):
        x, y = W(*pos)
        if not walk_ok(x, y):
            continue
        n.append(solid(f"Lantern{k + 1}", PROPS + "trail_lantern.png", x, y, 10, 8))
        n.append(f'[node name="LanternLight{k + 1}" type="PointLight2D" parent="."]\nposition = Vector2({x + 8}, {y - 40})\n'
                 f'texture_scale = 1.3\nscript = ExtResource("13_lamp")\n')
        taken.append((x, y))
    for k, pos in enumerate(FALLEN_LOGS):
        x, y = W(*pos)
        n.append(solid(f"FallenLog{k + 1}", PROPS + "fallen_log.png", x, y, 90, 16))
        shadow(x, y, 50, 10)
        taken.append((x, y))
    fence = "assets/sprites/tiles/kalmora/props/fence.png"
    for k, pos in enumerate(FENCES):
        x, y = W(*pos)
        if walk_ok(x, y) and not any((x - a) ** 2 + (y - b) ** 2 < 50 ** 2 for a, b in exits.values()):
            n.append(solid(f"Fence{k + 1}", fence, x, y, 24, 8))
    bx, by = W(302, 472)
    n.append(f'[node name="Rowboat" type="Sprite2D" parent="."]\nz_index = -7\nposition = Vector2({bx}, {by})\n'
             f'rotation = -0.5\ntexture = ExtResource("{texture(K2 + "props/rowboat.png")}")\n')
    rng = random.Random(11)
    lily = 0
    for _ in range(600):
        pcx, pcy = rng.uniform(0, L.CW), rng.uniform(0, L.CH)
        x, y = W(pcx, pcy)
        r, c = cell_of(x, y)
        if not (0 <= r < ROWS and 0 <= c < COLS) or stand[r][c] != WATER or (r, c) in decks or (r, c) in bridge_cells:
            continue
        if not all(0 <= r + dr < ROWS and 0 <= c + dc < COLS and stand[r + dr][c + dc] == WATER
                   and (r + dr, c + dc) not in decks and (r + dr, c + dc) not in bridge_cells
                   for dr in (-2, -1, 0, 1, 2) for dc in (-2, -1, 0, 1, 2)):
            continue
        if lily < 26 and (pcx < 420 or rng.random() < 0.35):
            lily += 1
            n.append(f'[node name="Lily{lily}" type="Sprite2D" parent="."]\nz_index = -7\nposition = Vector2({x}, {y})\n'
                     f'texture = ExtResource("{texture(PROPS + "lily_pads.png")}")\n' + ("flip_h = true\n" if lily % 2 else ""))

    # Butterflies over the open glades and clearings.
    for k, (bcx, bcy, count) in enumerate(BUTTERFLIES):
        x, y = W(bcx, bcy)
        n.append(f'[node name="Butterflies{k + 1}" type="Node2D" parent="."]\nposition = Vector2({x}, {y})\n'
                 f'script = ExtResource("{script_res("res://scripts/world/butterflies.gd")}")\ncount = {count}\nseed = {k + 5}\n')
        # ...and fireflies over the same glades after dusk.
        n.append(f'[node name="Fireflies{k + 1}" type="Node2D" parent="."]\nposition = Vector2({x}, {y})\n'
                 f'script = ExtResource("{script_res("res://scripts/world/fireflies.gd")}")\ncount = {count * 3}\nseed = {k + 11}\n')

    # Readables.
    for k, (title, pos, lines) in enumerate(READABLES):
        x, y = W(*pos)
        quoted = ", ".join('"' + line.replace('"', '\\"') + '"' for line in lines)
        n.append(f'[node name="Read{k + 1}" type="Node2D" parent="."]\nposition = Vector2({x}, {y})\n'
                 f'script = ExtResource("14_read")\ntitle = "{title}"\nlines = PackedStringArray({quoted})\n')

    # Trees: dense where the concept is forest, a few in its lawns; never on paths,
    # stairs, docks, cliff edges, or near anything that matters.
    fir = "res://" + "scenes/world/props/forest_fir.tscn"
    write_tree_scene("fir"), write_tree_scene("oak")
    ext += [('PackedScene', fir, "30_fir"), ('PackedScene', "res://scenes/world/props/forest_oak.tscn", "30_oak")]
    keep = [(x, y, 54) for x, y in taken] + [(x, y, 84) for x, y in [W(*p) for p in HOUNDS + BOARS]] \
        + [(x, y, 90) for x, y in exits.values()]
    for c0, r0, rows, _ in STAIR_SPOTS:
        keep.append((LEFT + (c0 + 1) * TILE, TOP + (r0 + rows / 2) * TILE, 30 + rows * 16))
    for x0, y0, x1, y1 in L.BRIDGES:
        (a0, b0), (a1, b1) = W(x0, y0), W(x1, y1)
        keep.append(((a0 + a1) / 2, (b0 + b1) / 2, max(a1 - a0, b1 - b0) / 2 + 40))
    for pts, _ in L.DOCKS:
        keep += [(*W(*p), 60) for p in pts]
    # Clearings the concept keeps open: no trees there.
    keep += [(*W(cx, cy), rad) for cx, cy, rad in CLEARINGS]
    floor_px = floor
    dirt_px = np.asarray(Image.fromarray(dirt_on.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(41))) > 0

    def tree_ok(x, y):
        r, c = cell_of(x, y)
        if not all(0 <= r + dr < ROWS and 0 <= c + dc < COLS and not blocked[r + dr][c + dc] and (r + dr, c + dc) not in stairs
                   and (r + dr, c + dc) not in decks and (r + dr, c + dc) not in bridge_cells
                   for dr in (-1, 0, 1) for dc in (-1, 0, 1)):
            return False                              # (-1: open ground behind the trunk, so it never grows up a cliff face)
        px, py = int(x - LEFT), int(y - TOP)
        if dirt_px[py, px]:
            return False
        return not any((x - a) ** 2 + (y - b) ** 2 < rr ** 2 for a, b, rr in keep)

    trees = []
    rng = random.Random(5)
    edge_band = 150                                   # the map's edges are thick forest (its walls)
    for _ in range(24000):
        x, y = rng.uniform(LEFT + 8, RIGHT - 8), rng.uniform(TOP + 40, BOTTOM - 4)
        px, py = int(x - LEFT), int(y - TOP)
        at_edge = min(x - LEFT, RIGHT - x, y - TOP, BOTTOM - y) < edge_band
        dense = floor_px[py, px] or at_edge
        gap = 44 if at_edge else 58 if dense else 84   # inner woods a little airier than the edges
        if not dense and rng.random() > 0.5:
            continue
        if tree_ok(x, y) and all((x - a) ** 2 + (y - b) ** 2 >= gap ** 2 for _, a, b in trees):
            trees.append(("oak" if rng.random() < 0.45 else "fir", round(x), round(y)))
    for k, (kind, x, y) in enumerate(trees):
        n.append(f'[node name="ForestTree{k + 1}" parent="." instance=ExtResource("30_{kind}")]\nposition = Vector2({x}, {y})\n')
        solids.append((x - 8, y - 10, x + 8, y + 4))
        shadow(x, y, 26 if kind == "oak" else 20, 9, 0.5)
    # Undergrowth: at tree feet, along path edges, and flower patches in the lawns.
    under = [("fern", 5), ("grass_clump", 4), ("berry_bush", 2), ("flowers", 4), ("mushrooms", 2), ("clover", 2),
             ("pinecones", 1), ("acorns", 1)]
    names, weights = [u for u, _ in under], [w for _, w in under]
    props = []

    def prop_ok(x, y, gap=18):
        return (ground_ok(x, y) and cell_of(x, y) not in stairs and not dirt_on[int(y - TOP), int(x - LEFT)]
                and not any((x - a) ** 2 + (y - b) ** 2 < (rr * 0.5) ** 2 for a, b, rr in keep)
                and all((x - a) ** 2 + (y - b) ** 2 >= gap ** 2 for _, a, b in props)
                and all((x - a) ** 2 + (y - b) ** 2 >= 14 ** 2 for _, a, b in trees))
    for _, tx0, ty0 in trees:
        if rng.random() < 0.5:
            x, y = tx0 + rng.choice([-1, 1]) * rng.randint(16, 26), ty0 + rng.randint(2, 12)
            if prop_ok(x, y):
                props.append((rng.choices(names, weights)[0], x, y))
    for _ in range(50):
        x, y = rng.uniform(LEFT + 40, RIGHT - 40), rng.uniform(TOP + 60, BOTTOM - 20)
        kind = rng.choice(["flowers", "flowers", "clover", "grass_clump"])
        for _ in range(rng.randint(3, 6)):
            px, py = round(x + rng.gauss(0, 16)), round(y + rng.gauss(0, 10))
            if prop_ok(px, py, 14):
                props.append((kind, px, py))
    # Flowering bushes along the paths and round the clearings, the concept's colour.
    path_near = np.asarray(Image.fromarray(dirt_on.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(81))) > 0
    for _ in range(4000):
        x, y = rng.uniform(LEFT + 40, RIGHT - 40), rng.uniform(TOP + 60, BOTTOM - 20)
        if len([p for p in props if p[0].startswith("bush")]) >= 70:
            break
        clear_of_decks = not any((x - a) ** 2 + (y - b) ** 2 < rr ** 2 for a, b, rr in keep)
        if path_near[int(y - TOP), int(x - LEFT)] and not dirt_px[int(y - TOP), int(x - LEFT)] and clear_of_decks                 and prop_ok(x, y, 40):
            props.append((rng.choice(["bush_flowers_g", "bush_flowers_g", "bush_g"]), round(x), round(y)))
    for k, (name, x, y) in enumerate(props):
        if name.startswith("bush"):
            n.append(solid(f"Bush{k + 1}", K2 + "props/" + name + ".png", x, y, 26, 10))
            continue
        path = FOREST + name + ".png"
        h = Image.open(path).height
        n.append(f'[node name="Under{k + 1}" type="Sprite2D" parent="."]\nposition = Vector2({x}, {y})\n'
                 f'offset = Vector2(0, {-h / 2 + 2})\n' + ("flip_h = true\n" if (x * 7 + y) % 2 else "")
                 + f'texture = ExtResource("{texture(path)}")\n')
    rocks = 0
    for _ in range(400):
        x, y = rng.uniform(LEFT + 60, RIGHT - 60), rng.uniform(TOP + 90, BOTTOM - 40)
        if rocks < 18 and prop_ok(x, y, 90) and all((x - a) ** 2 + (y - b) ** 2 > 60 ** 2 for a, b in taken):
            rocks += 1
            name = rng.choice(["rock", "stump", "rock", "log"])
            props.append((name, x, y))
            x, y = round(x), round(y)
            n.append(solid(f"Landmark{rocks}", FOREST + name + ".png", x, y, 22, 8))

    # Water: the animated wave tile clipped to every water pixel of the ground.
    wet = water_pixels(ground, stand, decks)
    lake_px = wet & ~STREAM_PX
    stream_px = wet & STREAM_PX
    for px, path in ((lake_px, WATER_MASK), (stream_px, STREAM_MASK)):
        mask = np.zeros(wet.shape + (4,), np.uint8)
        mask[px] = 255
        Image.fromarray(mask, "RGBA").save(path)
    w, h = ground.size
    n.append(f'''[node name="Lake" type="Sprite2D" parent="."]
z_index = -9
clip_children = 1
position = Vector2({cx}, {cy})
texture = ExtResource("17_watermask")

[node name="Waves" type="Sprite2D" parent="Lake"]
script = ExtResource("18_tiled")
strip = ExtResource("19_waves")
frame_count = 8
fps = 3.0
region_rect = Rect2(0, 0, {w}, {h})

[node name="Streams" type="Sprite2D" parent="."]
z_index = -9
clip_children = 1
position = Vector2({cx}, {cy})
texture = ExtResource("17_streammask")

[node name="Flow" type="Sprite2D" parent="Streams"]
script = ExtResource("18_tiled")
strip = ExtResource("19_flow")
frame_count = 8
fps = 8.0
region_rect = Rect2(0, 0, {w}, {h})
''')

    # Animated strips (falls, campfire).
    for key, strip, count, fps in (("frames_campfire", PROPS + "campfire_anim.png", 8, 9),):
        im = Image.open(strip)
        fw, fh = im.width // count, im.height
        atlas = texture(strip)
        refs = []
        for k in range(count):
            subs[f"{key}_{k}"] = (f'[sub_resource type="AtlasTexture" id="{key}_{k}"]\natlas = ExtResource("{atlas}")\n'
                                  f'region = Rect2({k * fw}, 0, {fw}, {fh})\n')
            refs.append(f'{{\n"duration": 1.0,\n"texture": SubResource("{key}_{k}")\n}}')
        subs[key] = (f'[sub_resource type="SpriteFrames" id="{key}"]\nanimations = [{{\n"frames": [{", ".join(refs)}],\n'
                     f'"loop": true,\n"name": &"default",\n"speed": {fps}\n}}]\n')

    # Reachability: everything that matters, from the south road.
    errors += reachable_errors(blocked, stairs, solids, spawns["from_kalmora"], {
        **{f"spawn {k}": v for k, v in spawns.items()},
        **{f"chest {c}": W(*p) for c, p, *_ in CHESTS},
        **{f"rival {k}": v for k, v in rivals.items()}, "Tobin": W(*CAMP["npc"]),
        "spring": (W(*SHRINE["fountain"])[0], W(*SHRINE["fountain"])[1] + 30),
        **{f"exit {k}": v for k, v in exits.items()},
    })
    if os.environ.get("THORNVEIL_DEBUG"):
        debug_view(ground, blocked, stairs, os.environ["THORNVEIL_DEBUG"])
    if errors:
        raise SystemExit("layout errors:\n  " + "\n  ".join(errors))

    # Bake contact shadows.
    m = Image.new("L", ground.size, 0)
    d = ImageDraw.Draw(m)
    for x, y, rx, ry, k in shadows:
        px, py = x - LEFT, y - TOP
        d.ellipse((px - rx, py - ry, px + rx, py + ry), fill=int(255 * k))
    m = np.asarray(m.filter(ImageFilter.GaussianBlur(5))).astype(np.float32)[..., None] / 255.0
    g = np.asarray(ground).astype(np.float32)
    g[..., :3] = g[..., :3] * (1 - m * 0.7) + np.array([20, 32, 40]) * m * 0.7 * 0.35
    # The ground's own painted water (under the animated layers, and peeking out at
    # their edges): into the forest water's teal, so no bright sea-blue rims show.
    blue = (g[..., 2] > g[..., 0] + 50) & (g[..., 2] > g[..., 1] + 15)
    lum = g[..., :3].mean(axis=-1) / 255.0
    teal = np.array([(18, 46, 110), (24, 72, 160), (36, 104, 200), (64, 142, 224), (130, 196, 240)], np.float32)
    idx = np.clip((lum * 1.6 * (len(teal) - 1)).round().astype(int), 0, len(teal) - 1)
    g[..., :3] = np.where(blue[..., None], teal[idx], g[..., :3])
    Image.fromarray(np.clip(g, 0, 255).astype(np.uint8), "RGBA").save(GROUND_PNG)

    sx, sy = spawns["from_kalmora"]
    n.append(f'''[node name="Player" parent="." instance=ExtResource("2_player")]
position = Vector2({sx}, {sy})

[node name="HUD" parent="." instance=ExtResource("3_hud")]

[node name="Binder" parent="." instance=ExtResource("4_binder")]

[node name="ShopPanel" parent="." instance=ExtResource("16_shop")]

[node name="DialogueBox" parent="." instance=ExtResource("15_dialogue")]
''')
    head = f'[gd_scene load_steps={len(ext) + len(subs) + 1} format=3]\n\n' + "".join(
        f'[ext_resource type="{t}" path="{p}" id="{i}"]\n' for t, p, i in ext) + "\n"
    open(SCENE, "w", encoding="utf-8", newline="\n").write(head + "\n".join(subs.values()) + "\n" + "\n".join(n))
    print(f"thornveil: {COLS}x{ROWS} cells, {len(walls)} wall rects, {len(trees)} trees, {len(props)} undergrowth, "
          f"{len(STAIR_SPOTS)} stairs")


def water_pixels(ground, stand, decks):
    """Every pixel of open water in the ground: the lake's blue and the streams."""
    a = np.asarray(ground).astype(int)
    lake = np.kron(np.array([[1 if (v == WATER and (r, c) not in decks) else 0 for c, v in enumerate(row)]
                             for r, row in enumerate(stand)], np.uint8), np.ones((TILE, TILE), np.uint8)).astype(bool)
    return (lake & (a[..., 2] > a[..., 0] + 50)) | STREAM_PX


def debug_view(ground, blocked, stairs, out):
    """The ground with blocked cells tinted red and the reachable area dotted green."""
    img = ground.convert("RGBA")
    over = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    for r in range(ROWS):
        for c in range(COLS):
            if blocked[r][c] and (r, c) not in stairs:
                d.rectangle((c * TILE, r * TILE, c * TILE + TILE - 1, r * TILE + TILE - 1), fill=(255, 0, 0, 70))
    seen = np.load(os.path.join(tempfile.gettempdir(), "thornveil_reach.npy"))
    ys, xs = np.nonzero(seen)
    for y, x in zip(ys[::3], xs[::3]):
        d.rectangle((x * 8 + 3, y * 8 + 3, x * 8 + 4, y * 8 + 4), fill=(0, 255, 0, 255))
    Image.alpha_composite(img, over).save(out)


def reachable_errors(blocked, stairs, solids, start, targets, step=8, body=5):
    w, h = (RIGHT - LEFT) // step, (BOTTOM - TOP) // step
    grid = np.zeros((h, w), bool)
    for r in range(ROWS):
        for c in range(COLS):
            if blocked[r][c] and (r, c) not in stairs:
                grid[r * TILE // step:(r + 1) * TILE // step, c * TILE // step:(c + 1) * TILE // step] = True
    for x0, y0, x1, y1 in solids:
        gx0, gy0 = max(0, math.ceil((x0 - body - LEFT) / step - 0.5)), max(0, math.ceil((y0 - body - TOP) / step - 0.5))
        gx1, gy1 = min(w, math.floor((x1 + body - LEFT) / step - 0.5) + 1), min(h, math.floor((y1 + body - TOP) / step - 0.5) + 1)
        if gx1 > gx0 and gy1 > gy0:
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
    np.save(os.path.join(tempfile.gettempdir(), "thornveil_reach.npy"), seen)
    bad = []
    for name, (x, y) in targets.items():
        gx, gy = int((x - LEFT) // step), int((y - TOP) // step)
        if not seen[max(0, gy - 4):gy + 5, max(0, gx - 4):gx + 5].any():
            bad.append(f"{name} at concept {tuple(round(v) for v in C(x, y))} can't be reached on foot")
    return bad


if __name__ == "__main__":
    main()
