"""Build Kalmora, Port of Beginnings: a lush, multilevel harbor town.

Usage: python scripts/tools/build_kalmora.py
Writes the ground image, the level map, and scenes/world/kalmora.tscn (the
whole scene is generated: edit the layout here, not in the editor).

The target look is the concept art in docs/reference/kalmora_concept_*.webp
(layout from concept B, with A's canal and beach cove): a dense town ringed
around a fountain square, water on three sides, plank docks with a moored
ship, a beach cove, a lighthouse on a rocky headland, forest to the north.

Levels (tile-corner heightmap, see terrain.py):
  0 sea         water, plus dry sea-level ground painted over it: the plank
                docks, the beach cove (and the canal bridge)
  1 harbor      the quay strip, the market district (a step down from the
                square), the beach's north shore, the lighthouse headland,
                and a grassy ledge under the west cliffs
  2 town        the fountain square and the shops around it, west to the
                windmill and the Verdana road
  3 upper       the north-east residential hill and the forest band with the
                north gate
Harbor walls are one row tall (docks sit just below the quay); the town's
terrace walls are three rows. Stairs are cut through the walls.
"""
import os

import numpy as np
from PIL import Image

os.chdir(os.path.join(os.path.dirname(__file__), "..", ".."))

from terrain import CliffSet, CornerSet, compose, merge_rects, overlay  # noqa: E402

TILE = 32
LEFT, TOP, RIGHT, BOTTOM = -1536, -1312, 1536, 736
COLS, ROWS = (RIGHT - LEFT) // TILE, (BOTTOM - TOP) // TILE
SEA, HARBOR, TOWN, UPPER = 0, 1, 2, 3
WALL_EXTRA = {SEA: 0, HARBOR: 1, TOWN: 1}   # extra wall rows per (k, k+1) cliff

ART = "assets/sprites/tiles/kalmora2/"
GROUND_PNG = ART + "kalmora_ground.png"
LEVEL_PNG = ART + "kalmora_levels.png"
SCENE = "scenes/world/kalmora.tscn"
GATE_Y = TOP + 104                             # the north gate; only way out of town


def level_at(x: float, y: float) -> int:
    if y <= -928:
        return UPPER                                  # forest band with the north gate
    if x >= 480 and y <= -640:
        return UPPER                                  # north-east residential hill
    if x < -960:                                      # west: fields over a grassy sea ledge
        return TOWN if y <= -288 else HARBOR if y <= -96 else SEA
    if x > 992:                                       # east: slope, beach cove, headland
        if y <= -416:
            return TOWN
        if x >= 1248:
            return HARBOR if y <= 512 else SEA        # the lighthouse headland
        return HARBOR if y <= -160 else SEA           # the beach's north shore; the cove is sea level
    if 256 <= x and y > -416:
        return HARBOR if y <= 64 else SEA             # market district, a step down from the square
    if y <= -160:
        return TOWN
    if 160 <= x <= 224 and y > -128:
        return SEA                                    # canal inlet
    return HARBOR if y <= 64 else SEA


def rocky(r, c):
    """Harbor walls are dressed stone along the quay; the rest of the coast is rock."""
    x = LEFT + c * TILE
    return -960 <= x < 1000


# Dry ground painted over sea level.
def sand(x, y):
    return 1024 <= x <= 1216 and -160 <= y <= 288 or ((x - 1120) / 128) ** 2 + ((y - 280) / 96) ** 2 <= 1


def planks(x, y):
    return (-896 <= x <= 384 and 96 <= y <= 224              # the main boardwalk along the quay
            or -640 <= x <= -544 and 224 <= y <= 480          # west pier, where the ship ties up
            or -160 <= x <= -64 and 224 <= y <= 512           # long middle pier
            or 224 <= x <= 320 and 224 <= y <= 448)           # east pier


# The stone bridge over the canal inlet: cells walkable at harbor level.
BRIDGE = (160, -96, 224, -32)                                 # x0, y0, x1, y1


def paved(x, y):
    """Cobbles vs. grass, per corner. Streets and squares are paved; everything
    else is lawn, garden or wild grass."""
    lv = level_at(x, y)
    if lv == HARBOR:
        if -960 <= x <= 992:
            return True                                       # quay and market paving
        return 1368 <= x <= 1432 and y <= 96                  # the lighthouse path; shores stay grassy
    if lv == TOWN:
        return bool(
            x * x + (y + 300) ** 2 <= 224 ** 2                # the fountain square
            or abs(x) <= 64 and y <= -300                     # north avenue up to the gate stairs
            or -448 <= y <= -384 and x <= 0                   # west road to Verdana
            or -512 <= y <= -448 and 0 <= x <= 1056           # east street to the market stairs
            or 928 <= x <= 1056 and y <= -448                 # up to the hill stairs
            or 544 <= x <= 608 and y >= -512                  # down to the market stairs
            or -1024 <= x <= -960 and -448 <= y               # down to the west ledge stairs
            or -656 <= x <= -464 and -224 >= y >= -300        # the blacksmith's forecourt
        )
    if lv == UPPER:
        return bool(
            abs(x) <= 64                                      # the gate road
            or x >= 480 and -736 <= y <= -672                 # the hill lane in front of the houses
            or 0 <= x <= 640 and -992 <= y <= -960            # path from the gate road to the hill
            or 576 <= x <= 640 and -992 <= y <= -736
            or 960 <= x <= 1024 and y >= -736                 # the hill stairs
        )
    return True


# Stairs: (left x, plateau edge y, lower level). They cover the wall rows around the edge.
STAIRS = [
    (-64, -160, HARBOR), (0, -160, HARBOR),       # grand stairs: square down to the harbor
    (544, -416, HARBOR),                          # town down to the market
    (-32, -928, TOWN),                            # gate band down to the avenue
    (960, -640, TOWN),                            # the hill down to the east street
    (-1024, -288, HARBOR),                        # town down to the west ledge
    (-576, 64, SEA), (32, 64, SEA),               # quay down to the docks
    (1088, -160, SEA),                            # north shore down to the beach
]


def stair_rows(pair):
    return 2 + WALL_EXTRA[pair]


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


def grade_ground(img, stand, wet):
    """Match the concept's palette: warm, light paving on flat ground (walls keep their
    grey stone); calmer water with turquoise shallows along the shore."""
    from PIL import ImageFilter
    a = np.asarray(img).astype(np.float32)
    cells = np.array([[1 if v >= HARBOR else 0 for v in row] for row in stand], np.uint8)
    water = np.array([[1 if wet(r, c) else 0 for c, v in enumerate(row)]
                      for r, row in enumerate(stand)], np.uint8)
    land_px = np.kron(cells, np.ones((TILE, TILE), np.uint8)).astype(bool)
    water_px = np.kron(water, np.ones((TILE, TILE), np.uint8)).astype(bool)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    grey = (np.abs(r - g) < 28) & (np.abs(g - b) < 34) & ~((g > r + 18) & (g > b + 18))
    pave = land_px & grey
    for i, (mul, add) in enumerate(((1.14, 12), (1.13, 10), (1.12, 8))):
        a[..., i] = np.where(pave, a[..., i] * mul + add, a[..., i])
    # Water: soften the tile's repeating white flecks (the shader adds moving sparkles).
    lum = 0.3 * r + 0.59 * g + 0.11 * b
    fleck = water_px & (lum > 120)
    deep = np.array([34, 88, 168], np.float32)
    for i in range(3):
        a[..., i] = np.where(fleck, a[..., i] * 0.3 + deep[i] * 0.7, a[..., i])
    # Shallows: fade toward turquoise near anything that isn't open water.
    near = Image.fromarray(((1 - water_px) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(28))
    w = np.asarray(near).astype(np.float32) / 255.0 * 1.6
    w = np.clip(w, 0, 0.75) * water_px
    shallow = np.array([46, 158, 186], np.float32)
    for i in range(3):
        a[..., i] = a[..., i] * (1 - w) + shallow[i] * w
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def build_terrain():
    levels = [[level_at(LEFT + c * TILE, TOP + r * TILE) for c in range(COLS + 1)] for r in range(ROWS + 1)]
    quay, rock = CliffSet(ART + "cliff/sea_quay"), CliffSet(ART + "cliff/sea_rock")
    sets = {SEA: lambda r, c: quay if rocky(r, c) else rock,
            HARBOR: CliffSet(ART + "cliff/quay_town"), TOWN: CliffSet(ART + "cliff/town_upper")}
    img, stand = compose(levels, sets, TILE, extra_wall_rows=WALL_EXTRA)

    # Surfaces: grass vs. cobbles on every land level (each level's own base terrain
    # is left alone), sand and planks over the sea.
    grass = CornerSet(ART + "wang/grass")
    lawn = lambda x, y: not paved(x, y)
    overlay(img, stand, HARBOR, grass, lawn, LEFT, TOP, TILE)
    overlay(img, stand, TOWN, grass, lawn, LEFT, TOP, TILE, base_is_upper=True)
    overlay(img, stand, UPPER, grass, lawn, LEFT, TOP, TILE)
    overlay(img, stand, SEA, CornerSet(ART + "wang/sand"), sand, LEFT, TOP, TILE)
    boards = CornerSet(ART + "wang/planks")
    overlay(img, stand, SEA, boards, planks, LEFT, TOP, TILE)
    # The canal footbridge: plank decking across the inlet, like the docks.
    for x in range(BRIDGE[0], BRIDGE[2], TILE):
        for y in range(BRIDGE[1], BRIDGE[3], TILE):
            img.paste(boards.tiles[15], (x - LEFT, y - TOP))
    img = deepen_greens(img)

    stair_cells = set()
    for x, edge, pair in STAIRS:
        c0, r0 = (x - LEFT) // TILE, (edge - TOP) // TILE - WALL_EXTRA[pair]
        for dr in range(stair_rows(pair)):
            for dc in (0, 1):
                stair_cells.add((r0 + dr, c0 + dc))
    bridge_cells = {((y - TOP) // TILE, (x - LEFT) // TILE)
                    for x in range(BRIDGE[0], BRIDGE[2], TILE) for y in range(BRIDGE[1], BRIDGE[3], TILE)}

    def dry(r, c):
        """Sea-level cells you can stand on: fully sand or fully planks."""
        x, y = LEFT + c * TILE, TOP + r * TILE
        corners = [(x, y), (x + TILE, y), (x, y + TILE), (x + TILE, y + TILE)]
        return all(sand(*p) for p in corners) or all(planks(*p) for p in corners)

    def wet(r, c):
        """Open water: sea-level cells with no sand or planks at any corner."""
        x, y = LEFT + c * TILE, TOP + r * TILE
        corners = [(x, y), (x + TILE, y), (x, y + TILE), (x + TILE, y + TILE)]
        return stand[r][c] == SEA and (r, c) not in bridge_cells and not any(sand(*p) or planks(*p) for p in corners)

    img = grade_ground(img, stand, wet)
    walkable = [[(stand[r][c] > SEA or stand[r][c] == SEA and dry(r, c) or (r, c) in stair_cells or (r, c) in bridge_cells)
                 for c in range(COLS)] for r in range(ROWS)]
    blocked = [[not walkable[r][c] for c in range(COLS)] for r in range(ROWS)]

    # Level map: red = level * 40 (255 = cliff/stairs, any level); green = dry sea-level
    # ground, so the water shimmer skips beaches and docks.
    lm = Image.new("RGB", (COLS, ROWS))
    for r in range(ROWS):
        for c in range(COLS):
            v = stand[r][c]
            if (r, c) in stair_cells or v < 0:
                lm.putpixel((c, r), (255, 0, 0))
            elif (r, c) in bridge_cells:
                lm.putpixel((c, r), (HARBOR * 40, 255, 0))
            else:
                lm.putpixel((c, r), (v * 40, 255 if v == SEA and walkable[r][c] else 0, 0))
    img.save(GROUND_PNG)
    lm.save(LEVEL_PNG)
    return stand, blocked, stair_cells


def build_stairs():
    """Stretch the grey stone stairs sprite to 2- and 3-row flights by repeating its
    middle steps, so the treads keep their pixel size."""
    src = Image.open(ART + "objects/stairs.png").convert("RGBA")
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
        out.paste(flight.resize((2 * TILE, target), Image.NEAREST) if w > 2 * TILE else flight, ((2 * TILE - min(w, 2 * TILE)) // 2, 0))
        paths[rows] = f"{ART}stairs_{rows}.png"
        out.save(paths[rows])
    return paths


# ------------------------------------------------------------------ content
OBJ = ART + "objects/"
# (node, sprite, position = footprint bottom-centre, footprint width)
BUILDINGS = [
    # Around the fountain square.
    ("Tavern", "inn", (330, -560), 190),
    ("GeneralStore", "general_store", (-340, -560), 170),
    ("RedHouse", "townhouse_red", (-620, -600), 120),
    ("Blacksmith", "blacksmith", (-560, -232), 160),
    ("CardShop", "item_shop", (820, -490), 160),
    # The harbor.
    ("Harbormaster", "harbormaster2", (-700, 36), 140),
    ("Warehouse", "warehouse", (-420, 40), 170),
    # Along the west road.
    ("BlueTownhouse", "townhouse_blue", (-820, -480), 100),
    ("TealTownhouse", "townhouse_teal", (-1000, -480), 96),
    ("Bakery", "bakery2", (-1440, -470), 120),
    # The fisherman's hut on the west ledge.
    ("FisherHut", "fisher_hut2", (-1460, -100), 110),
    # The north-east hill.
    ("BlueCottage", "cottage_blue", (560, -770), 140),
    ("BlueHouse", "house_blue", (820, -770), 170),
    ("HillHouse", "townhouse_red", (1110, -770), 120),
    ("NonnaHouse", "cottage_red", (1340, -770), 130),
    # West fields.
    ("Windmill", "windmill", (-1250, -620), 110),
]
# Enterable buildings: node -> (door x offset from the building, interior scene).
DOORS = {
    "Tavern": (0, "res://scenes/world/interiors/kalmora_tavern.tscn"),
    "CardShop": (0, "res://scenes/world/interiors/kalmora_card_shop.tscn"),
    "NonnaHouse": (0, "res://scenes/world/interiors/kalmora_nonna_house.tscn"),
}
# Residents (dogs and cats). (id, name, sprite id, position, wander radius, lines)
NPCS = [
    ("bram", "Bram", "bram", (-160, -30), 0, ["Tide's good today. Good for ships, anyway."]),
    ("mirela", "Harbormaster Mirela", "mirela", (-630, 52), 0, [
        "Manifests, manifests. Everything that lands in Kalmora gets a stamp. Everything.",
        "The race? The whole island's talking. Somebody's walking into Vetrassa with a full set, mark my words.",
    ]),
    ("pip", "Pip", "pip", (460, -100), 40, [
        "Fresh fish! Well. Fresh-ish.",
        "My cousin went to work out in Duskara last spring. Good pay, they said. He hasn't written.",
    ]),
    ("sailor", "Deckhand Luca", "sailor", (-300, 160), 60, [
        "Sailed round the whole isle once. Vetrassa's got the tallest spires you ever saw.",
        "You racers bind your cards in town, right? Thieves love a loose card on the road.",
    ]),
    ("baker", "Baker Rosa", "baker", (-1400, -440), 40, [
        "Warm bread! Two coins a loaf, one if you tell me a good rumor.",
        "The Runner came through at dawn, all scarf and no manners. Didn't even stop for bread.",
    ]),
    ("tomas", "Keeper Tomas", "tomas", (1320, 40), 0, [
        "Lost my lighthouse wick somewhere up on the hill houses. Can't light the lamp without it.",
        "That lens up there's worth more than my whole cottage. Door stays locked, wick or no wick.",
    ]),
    ("rook", "Guard Rook", "rook", (80, -1120), 0, [
        "North road's sealed. A Salt Compass opens it. Old rule, nobody remembers why.",
        "Thornveil's no place to wander with loose cards. The hounds don't care, but the Raider does.",
    ]),
]
# The unmarked shipment: three crates piled on the quay, where Bram works.
CLUE_CRATES = [("crate_sand", (-110, 24)), ("crate_glove", (-70, -8)), ("crate_ledger", (-40, 30))]
CARDS = [  # (card, position)
    ("harbor_lantern", (-860, -40)), ("coral_coin", (1110, 110)), ("gull_feather", (1450, 420)),
    ("sea_glass", (-1360, -118)), ("sunken_crown_shard", (-112, 470)),
    ("salt_compass", (-900, -560)), ("tide_bell", (900, -200)), ("terracotta_tile", (-420, -720)),
    ("lighthouse_wick", (1300, -700)), ("fishers_knot", (272, 410)),
]
EXTRA_SALT_COMPASS = (-1180, -420)
DUMMIES = [(-1300, -170), (-1200, -170), (-1100, -170)]
RIVAL_SPOTS = {"runner": (-700, -420), "raider": (680, -710), "hoarder": (-300, -420)}
SPAWNS = {"town": (0, -190), "from_thornveil": (0, -1130)}
LIGHTHOUSE = (1400, 190)      # yard centre; the gate faces north toward the path
MERCHANT = (600, -120)
FOUNTAIN = (0, -236)

# Trees: (sprite, position).
PALM, TREE = "palm", "tree"
TREES = (
    # Forest along the north edge, behind the gate line, and down the band's sides.
    [(TREE, (x, -1236)) for x in range(-1480, 1500, 104) if abs(x) > 120]
    + [(TREE, (x, -1120)) for x in (-1440, -1250, -1060, -860, -660, -470, -280, 280, 470)]
    + [(TREE, (x, -1010)) for x in (-1350, -1150, -950, -750, -550, -350, -200, 200, 360)]
    + [(TREE, (x, -1080)) for x in (760, 960, 1160, 1360)]
    + [(TREE, (x, -1178)) for x in range(-1428, 1500, 104) if abs(x) > 180 and not 230 <= x <= 520]
    # The avenue and the square.
    + [(TREE, (sx * 120, y)) for sx in (-1, 1) for y in (-700, -840)]
    + [(PALM, (sx * 290, -250)) for sx in (-1, 1)] + [(PALM, (sx * 200, -470)) for sx in (-1, 1)]
    # Gardens around the west houses and the windmill fields.
    + [(TREE, (-820, -700)), (TREE, (-480, -760)), (TREE, (-880, -300)), (TREE, (-1460, -760)), (TREE, (-1060, -820))]
    + [(PALM, (-940, -330)), (PALM, (-400, -300))]
    # The market and the harbor.
    + [(PALM, (300, -340)), (PALM, (970, -340)), (PALM, (-930, 0)), (PALM, (100, -64))]
    # The east slope, the beach and the headland.
    + [(PALM, (1060, -520)), (PALM, (1400, -560)), (PALM, (1050, -300)), (PALM, (1200, -330)),
       (PALM, (1036, -40)), (PALM, (1200, 150)), (PALM, (1300, 330)), (PALM, (1500, -250)), (PALM, (1290, -300))]
    # The hill gardens.
    + [(TREE, (690, -880)), (TREE, (960, -900)), (TREE, (1230, -880)), (TREE, (1460, -880))]
)


def row(name, x0, x1, y, step):
    return [(name, x, y) for x in range(x0, x1 + 1, step)]


# Props: (name, x, y). Names resolve to the new pack (props/), then objects/, then
# the old 32px pack (tiles/kalmora/props). Grouped by where a resident would put them.
STALLS = ["stall_fruit", "stall_fish", "stall_pottery", "stall_bread"]
PROPS = (
    # --- The fountain square ---------------------------------------------------
    [("banner", sx * 150, -420) for sx in (-1, 1)] + [("banner", sx * 104, -196) for sx in (-1, 1)]
    + [("flower_bed", sx * 216, y) for sx in (-1, 1) for y in (-360, -210)]
    + [("bench", sx * 118, -300) for sx in (-1, 1)]
    + [("bush_flowers", -190, -540), ("bush_flowers", 250, -520)]
    # Shops around the square.
    + [("parasol_table", 240, -500), ("parasol_table", 420, -500), ("menu_board", 290, -540)]
    + [("apples_crate", -420, -548), ("oranges_basket", -270, -548), ("sack", -440, -520), ("flour_sack", -250, -520)]
    + [("barrel", -660, -228), ("barrels", -690, -228), ("crates", -455, -228), ("boulder", -760, -250)]
    + [("potted_palm", 740, -500), ("potted_palm", 900, -500), ("bush", 1000, -500)]
    + [("bush", -700, -612), ("bush_flowers", -540, -612)]
    # The windmill fields and the closed road to Verdana.
    + [("flower_bed", x, y) for x in (-1100, -1010, -920) for y in (-760, -680)]
    + row("fence", -1136, -880, -630, 32)
    + [("signpost", -1330, -460), ("cart", -1500, -410), ("barrels", -1470, -380), ("wheelbarrow", -1180, -560)]
    # --- The market district ----------------------------------------------------
    + [(STALLS[k % 4], x, -250) for k, x in enumerate((340, 460, 720, 840))]
    + [(STALLS[(k + 2) % 4], x, -120) for k, x in enumerate((340, 460, 720, 840))]
    + [("fish_crates", 400, -40), ("crates", 520, -40), ("barrels", 680, -40), ("amphorae", 780, -40), ("lemons_crate", 880, -40)]
    + [("parasol_table", 940, -200), ("bench", 950, -290)]
    # --- The harbor quay ----------------------------------------------------------
    + [("crates", -880, 0), ("barrels", -850, 30), ("crate", -880, 34), ("net_crate", -820, -60)]
    + [("anchor", -250, -40), ("ship_wheel", -210, -40), ("fish_crates", -300, 20), ("rope", -250, 44)]
    + [("lobster_trap", 100, -40), ("buoy", 300, 40)]
    # --- The docks -----------------------------------------------------------------
    + [("fish_crates", -220, 150), ("barrel", 120, 150), ("barrels", 330, 150), ("crates", -820, 150), ("rope", -600, 200)]
    # --- The beach and the headland ------------------------------------------------
    + [("parasol_table", 1150, 20), ("boulder", 1050, 210), ("bench", 1220, -250)]
    + [("bush", 1500, 100), ("boulder", 1300, 460), ("candle_shrine", 1470, 40)]
    # Hedges around the lighthouse yard (its walls are the yard's collision).
    + [("bush", LIGHTHOUSE[0] + sx * 72, LIGHTHOUSE[1] + dy) for sx in (-1, 1) for dy in (-50, 10, 70)]
    + [("bush", LIGHTHOUSE[0] + dx, LIGHTHOUSE[1] + 96) for dx in (-60, 60)]
    # --- The hill: flowers at the doors, gardens between the houses -------------------
    + [("flower_bed", x, -690) for x in (520, 690, 900, 1230, 1460)]
    + [("bush_flowers", 1000, -800), ("bush", 1220, -800), ("laundry_line", 700, -800)]
    # --- The gate band ------------------------------------------------------------------
    + [("flower_bed", sx * 110, -1000) for sx in (-1, 1)] + [("bush", sx * 170, -1160) for sx in (-1, 1)]
    # --- West ledge: a sparring spot above the sea ------------------------------------------
    + [("fish_crates", -1380, -110)]
)
# Free sprites (y-sorted, no collision): boats and rocks out on the water.
FLOATING = [("ship", -820, 500), ("rowboat", -300, 330), ("rowboat", 60, 420), ("rowboat", 440, 330),
            ("sea_rocks", 1270, 590), ("sea_rocks", 1480, 610), ("sea_rocks", -1300, 40), ("sea_rocks", -1060, 150),
            ("sea_rocks", 1520, -120)]
LAMPS = ([("lamp_post", x, y) for x, y in ((-210, -420), (210, -420), (-180, -240), (180, -240))]
         + [("lamp_post", x, -470) for x in (-600, 60, 640)]
         + [("lamp_post", x, 40) for x in (-900, -570, 120, 400, 900)]
         + [("lamp_post", x, 216) for x in (-660, -130, 250)]
         + [("lamp_post", x, -700) for x in (500, 1060)]
         + [("lamp_post", sx * 96, -1160) for sx in (-1, 1)])
PROP_DIRS = [ART + "props/", OBJ, "assets/sprites/tiles/kalmora/props/"]
FOOTPRINT_FRAC = {"bench": (0.8, 10), "parasol_table": (0.5, 10), "lamp_post": (0.3, 8), "banner": (0.3, 8),
                  "flower_bed": (0.9, 14), "bush": (0.7, 14), "bush_flowers": (0.7, 14), "boulder": (0.8, 16)}


def prop_path(name):
    for d in PROP_DIRS:
        if os.path.exists(f"{d}{name}.png"):
            return f"{d}{name}.png"
    raise SystemExit(f"no sprite for prop {name}")


def cell_of(x, y):
    return int((y - TOP) // TILE), int((x - LEFT) // TILE)


def check_spot(stand, blocked, name, x, y, want=None):
    r, c = cell_of(x, y)
    ok = 0 <= r < ROWS and 0 <= c < COLS and not blocked[r][c] and (want is None or stand[r][c] == want)
    if not ok:
        raise SystemExit(f"{name} at ({x}, {y}) is not on walkable ground (cell level {stand[r][c]})")


def main():
    stand, blocked, stair_cells = build_terrain()
    stair_png = build_stairs()
    for name, _, (x, y), _ in BUILDINGS:
        if name in DOORS:
            SPAWNS[f"from_{name.lower()}"] = (x + DOORS[name][0], y + 26)
    for card, (x, y) in CARDS:
        check_spot(stand, blocked, card, x, y)
    for name, (x, y) in {**SPAWNS, **RIVAL_SPOTS}.items():
        check_spot(stand, blocked, name, x, y)

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

    def bottom_offset(path):
        im = Image.open(path)
        return im.height / 2 - im.getbbox()[3]

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
    for k, (x, edge, pair) in enumerate(STAIRS):
        rows = stair_rows(pair)
        top = edge - WALL_EXTRA[pair] * TILE
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

    # Lighthouse yard on the headland: low walls, the door gate facing the path.
    lx, ly = LIGHTHOUSE
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
    check_spot(stand, blocked, "lighthouse lens", lx, ly - 30, HARBOR)

    gp = OBJ + "gate_pillars.png"
    n.append(f'''[node name="Fountain" parent="." instance=ExtResource("18_fountain")]
position = Vector2{FOUNTAIN}

[node name="Merchant" parent="." instance=ExtResource("8_merchant")]
position = Vector2{MERCHANT}
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
    check_spot(stand, blocked, "north gate", 0, GATE_Y + 24, UPPER)
    for name, (x, y) in SPAWNS.items():
        n.append(f'[node name="{name}" type="Marker2D" parent="Spawns"]\nposition = Vector2({x}, {y})\n')
    n.append('[node name="RivalSpots" type="Node2D" parent="."]\n')
    for name, (x, y) in RIVAL_SPOTS.items():
        n.append(f'[node name="{name}" type="Marker2D" parent="RivalSpots"]\nposition = Vector2({x}, {y})\n')

    taken = [p for _, p in CARDS] + DUMMIES + list(RIVAL_SPOTS.values()) + list(SPAWNS.values()) \
        + [EXTRA_SALT_COMPASS, MERCHANT, FOUNTAIN, (lx, ly - 85), (lx, ly - 30), (0, GATE_Y)]
    for card, (x, y) in CARDS:
        n.append(f'[node name="Card_{card}" parent="." instance=ExtResource("6_pick")]\nposition = Vector2({x}, {y})\ncard_id = &"{card}"\n')
    n.append(f'[node name="Card_salt_compass_2" parent="." instance=ExtResource("6_pick")]\nposition = Vector2{EXTRA_SALT_COMPASS}\ncard_id = &"salt_compass"\n')
    for k, (x, y) in enumerate(DUMMIES):
        check_spot(stand, blocked, "dummy", x, y, HARBOR)
        n.append(f'[node name="TrainingDummy{k + 1}" parent="." instance=ExtResource("7_dummy")]\nposition = Vector2({x}, {y})\n')

    def solid(node, path, x, y, fw, fh):
        return (f'[node name="{node}" type="StaticBody2D" parent="."]\nposition = Vector2({x}, {y})\n\n'
                f'[node name="Sprite" type="Sprite2D" parent="{node}"]\nposition = Vector2(0, {bottom_offset(path)})\n'
                f'texture = ExtResource("{texture(path)}")\n\n'
                f'[node name="Base" type="CollisionShape2D" parent="{node}"]\nposition = Vector2(0, {-fh / 2})\n'
                f'shape = SubResource("{shape(fw, fh)}")\n')

    for name, sprite, (x, y), fw in BUILDINGS:
        check_spot(stand, blocked, name, x, y)
        n.append(solid(name, OBJ + sprite + ".png", x, y, fw, 40))
        taken.append((x, y))
        if name in DOORS:
            dx, interior = DOORS[name]
            n.append(f'[node name="{name}Lamp" type="PointLight2D" parent="."]\nposition = Vector2({x + dx}, {y - 40})\n'
                     f'texture_scale = 0.9\nscript = ExtResource("20_lamp")\nmax_energy = 0.8\n')
            n.append(f'[node name="{name}Door" parent="." instance=ExtResource("11_exit")]\nposition = Vector2({x + dx}, {y + 4})\n'
                     f'scale = Vector2(0.5, 1)\ntarget_scene = "{interior}"\ntarget_spawn = &"door"\n')

    # Residents and the quay's unmarked crates.
    for npc_id, display, sprite_id, (x, y), wander, lines in NPCS:
        check_spot(stand, blocked, npc_id, x, y)
        frames_id = f"n_{sprite_id}"
        ext.append(('SpriteFrames', f"res://assets/sprites/npcs/{sprite_id}/{sprite_id}_frames.tres", frames_id))
        quoted = ", ".join('"' + line.replace('"', '\\"') + '"' for line in lines)
        n.append(f'[node name="Npc_{npc_id}" parent="." instance=ExtResource("19_npc")]\nposition = Vector2({x}, {y})\n'
                 f'npc_id = &"{npc_id}"\ndisplay_name = "{display}"\nsprite_frames = ExtResource("{frames_id}")\n'
                 f'lines = PackedStringArray({quoted})\nwander_radius = {float(wander)}\n')
        taken.append((x, y))
    for clue, (x, y) in CLUE_CRATES:
        check_spot(stand, blocked, clue, x, y, HARBOR)
        n.append(f'[node name="Clue_{clue}" parent="." instance=ExtResource("21_clue")]\nposition = Vector2({x}, {y})\nclue_id = &"{clue}"\n')
        taken.append((x, y))

    # Trees, then props. Everything is placed on purpose (see TREES/PROPS/LAMPS);
    # a spot that lands on a wall, stairs, or something already placed is an error
    # in the layout, so the build stops and says where.
    crowd = lambda x, y, r: next(((a, b) for a, b in taken if (x - a) ** 2 + (y - b) ** 2 < r ** 2), None)

    errors = []

    def place_check(name, x, y, clearance=18):
        r, c = cell_of(x, y)
        if not (0 <= r < ROWS and 0 <= c < COLS) or blocked[r][c] or (r, c) in stair_cells:
            errors.append(f"{name} at ({x}, {y}) is not on open ground (level {stand[r][c] if 0 <= r < ROWS and 0 <= c < COLS else '-'})")
        hit = crowd(x, y, clearance)
        if hit:
            errors.append(f"{name} at ({x}, {y}) crowds something at {hit}")

    for k, (sprite, (x, y)) in enumerate(TREES):
        place_check(sprite, x, y, 24)
        taken.append((x, y))
        n.append(solid(f"{sprite.title()}{k + 1}", OBJ + sprite + ".png", x, y, 16 if sprite == PALM else 30, 10))

    count = [0]
    def prop_node(name, x, y, kind="solid"):
        path = prop_path(name)
        count[0] += 1
        node = f"P{count[0]}_{name}"
        if kind == "free":
            return (f'[node name="{node}" type="Sprite2D" parent="."]\nposition = Vector2({x}, {y})\n'
                    f'offset = Vector2(0, {bottom_offset(path)})\ntexture = ExtResource("{texture(path)}")\n')
        taken.append((x, y))
        im = Image.open(path)
        b = im.getbbox()
        frac, fh = FOOTPRINT_FRAC.get(name, (0.6, 10))
        return solid(node, path, x, y, max(12, int((b[2] - b[0]) * frac)), fh)

    for name, x, y in PROPS:
        place_check(name, x, y)
        n.append(prop_node(name, x, y))
    for name, x, y in LAMPS:
        place_check(name, x, y)
        n.append(prop_node(name, x, y))
        n.append(f'[node name="Light{count[0]}" type="PointLight2D" parent="."]\nposition = Vector2({x + 18}, {y - 47})\n'
                 f'texture_scale = 1.4\nscript = ExtResource("20_lamp")\n')
    for name, x, y in FLOATING:
        n.append(prop_node(name, x, y, "free"))
    if errors:
        raise SystemExit("layout errors:\n  " + "\n  ".join(errors))

    n.append('''[node name="Player" parent="." instance=ExtResource("2_player")]
position = Vector2(0, -190)

[node name="HUD" parent="." instance=ExtResource("3_hud")]

[node name="Binder" parent="." instance=ExtResource("4_binder")]

[node name="ShopPanel" parent="." instance=ExtResource("5_shop")]

[node name="DialogueBox" parent="." instance=ExtResource("22_dialogue")]
''')
    head = f'[gd_scene load_steps={len(ext) + len(subs) + 1} format=3]\n\n' + "".join(
        f'[ext_resource type="{t}" path="{p}" id="{i}"]\n' for t, p, i in ext) + "\n"
    open(SCENE, "w", encoding="utf-8", newline="\n").write(head + "\n".join(subs.values()) + "\n" + "\n".join(n))
    print(f"kalmora: {COLS}x{ROWS} cells, {len(walls)} wall rects, {len(taken)} placed things")


if __name__ == "__main__":
    main()
