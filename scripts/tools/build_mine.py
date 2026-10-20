"""Builds the North Shaft: the Duskara Mining Company's mine under Duskara.

The shaft on the Company's terrace drops to the lift landing, where old Gideon keeps
the night watch and the tally gate counts every head in (a card gate: a Brass Tally
Tag). Past it, the sorting floor, where small hands sort card-stone at long tables;
east, the King's Seam, the oldest working, glowing with veins of card-stone, carts on
their rails; west, the dormitory of little bunks; north, the foreman's lower office
with the ledger of names ("The Foreman's Names"); south-west, the old flooded
workings over the lake the town floats on, and behind them the escape line's crawl,
which comes up in the Siroth Dunes' Bone Hollow (one way: it's nailed shut from the
dune side). "Beneath the Dunes" (Rafi) brings you here for Ada.

Terrain is composed with terrain.compose() from a PixelLab mine cliff set
(assets/sprites/tiles/duskara/mine/cliff/mine): level 0 is floor, level 1 rock, its
faces hanging one row below it (timber props, teal veins). Collision is every cell
that isn't floor, plus the lake. Layout in cells (32 px): chambers are circles,
tunnels capsules between cell points.

Run: python scripts/tools/build_mine.py
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

os.chdir(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, "scripts/tools")
from terrain import CliffSet, compose, merge_rects  # noqa: E402

TILE = 32
COLS, ROWS = 50, 36
LEFT, TOP = -COLS * TILE // 2, -ROWS * TILE // 2
ART = "assets/sprites/tiles/duskara/mine/"
GROUND_PNG = ART + "mine_ground.png"
LEVEL_PNG = ART + "mine_levels.png"
SCENE = "scenes/world/duskara_mine.tscn"

CHAMBERS = {
    "landing": (25, 30.5, 4.6),
    "sorting": (25, 17, 8.0),
    "office": (25, 5.4, 3.9),
    "seam": (40, 12, 6.8),
    "dorm": (9, 11.5, 5.2),
    "flooded": (10, 26, 6.2),
}
TUNNELS = [
    ((25, 30.5), (25, 35.9), 1.6),     # up the lift to Duskara (the bottom edge)
    ((25, 30.5), (25, 22), 1.35),      # through the tally gate
    ((25, 17), (25, 6), 1.2),          # to the foreman's lower office
    ((30, 15.5), (36, 13), 1.7),       # east to the King's Seam
    ((19, 15.5), (12.5, 12.5), 1.4),   # west to the dormitory
    ((9, 15), (9.5, 21.5), 1.3),       # down to the flooded workings
    ((6.5, 29), (4, 35.9), 1.0),       # the escape line's crawl, out to the dunes
]
LAKE = (12.5, 27.5, 3.0, 1.9)          # cx, cy, rx, ry (cells): the water under the town
GATE_CELL = (25, 25.2)
RAILS = [[(28, 17.5), (33, 15), (37, 13.4), (42, 12.6), (44.5, 9)],
         [(38, 14.5), (41, 16.4), (44, 15.5)]]


def cell_px(cx, cy):
    return (LEFT + cx * TILE, TOP + cy * TILE)


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy or 1)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def in_lake(cx, cy):
    lx, ly, rx, ry = LAKE
    return ((cx - lx) / rx) ** 2 + ((cy - ly) / ry) ** 2 < 1.0


def is_floor(cx, cy):
    wobble = 0.35 * math.sin(cx * 1.3 + cy * 0.7) + 0.25 * math.sin(cx * 0.5 - cy * 1.1)
    for x, y, r in CHAMBERS.values():
        if math.hypot(cx - x, (cy - y) * 1.15) < r + wobble:
            return True
    return any(seg_dist(cx, cy, *a, *b) < w + wobble * 0.4 for a, b, w in TUNNELS)


def noise(rng, H, W, scale):
    small = rng.random((H // scale + 2, W // scale + 2)).astype(np.float32)
    return np.asarray(Image.fromarray((small * 255).astype(np.uint8)).resize(
        ((W // scale + 2) * scale, (H // scale + 2) * scale), Image.BICUBIC))[:H, :W].astype(np.float32) / 255.0


def build_ground():
    levels = [[0 if is_floor(c, r) and 0 < c < COLS and r > 0 else 1 for c in range(COLS + 1)] for r in range(ROWS + 1)]
    # The two ways out reach the bottom edge.
    for r in range(ROWS - 3, ROWS + 1):
        for c in (24, 25, 26, 3, 4, 5):
            if is_floor(c, r - 1):
                levels[r][c] = 0
    rock = CliffSet(ART + "cliff/mine")
    img, stand = compose(levels, {(0, 1): rock}, {0: ((0, 1), "lower"), 1: ((0, 1), "upper")}, TILE)
    a = np.array(img).astype(float)
    H, W = a.shape[:2]
    solid = np.kron(np.array([[1 if v == 1 else 0 for v in row] for row in stand], np.uint8),
                    np.ones((TILE, TILE), np.uint8)).astype(bool)[:H, :W]
    a[solid, :3] *= 0.55
    rng = np.random.default_rng(11)
    # Open floor repainted as trodden dust and grit (the set's floor repeats its
    # pebbles), feathered into the drawn wall feet.
    open_cells = [[stand[r][c] == 0 for c in range(COLS)] for r in range(ROWS)]
    inner = np.kron(np.array(open_cells, np.uint8), np.ones((TILE, TILE), np.uint8)).astype(np.float32)
    inner = np.pad(inner, ((0, H - inner.shape[0]), (0, W - inner.shape[1])))
    feather = np.asarray(Image.fromarray((inner * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))).astype(np.float32) / 255.0
    dust = np.clip(noise(rng, H, W, 40) * 0.6 + noise(rng, H, W, 12) * 0.4, 0, 1)
    floor = (np.array([108, 82, 62], np.float32) * (1 - dust[..., None]) + np.array([148, 116, 86], np.float32) * dust[..., None])
    floor *= (0.95 + 0.08 * noise(rng, H, W, 3))[..., None]
    grit = rng.random((H, W)) > 0.996
    floor[grit] = (176, 150, 118)
    shard = rng.random((H, W)) > 0.9993
    floor[shard] = (110, 220, 210)                       # a fleck of card-stone dropped on the way
    a[..., :3] = a[..., :3] * (1 - feather[..., None]) + floor * feather[..., None]
    # The lake under the town: still black water, a lighter rim, a few ripples.
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    lx, ly, rx, ry = LAKE
    ex = ((xx - lx * TILE) / (rx * TILE)) ** 2 + ((yy - ly * TILE) / (ry * TILE)) ** 2 + (noise(rng, H, W, 10) - 0.5) * 0.08
    water = ex < 1.0
    depth = np.clip(1.0 - ex, 0, 1)[..., None]
    col = np.array([34, 58, 66], np.float32) * (1 - depth * 0.5) + np.array([10, 22, 30], np.float32) * depth * 0.5
    ripple = (np.abs(np.sin(np.sqrt(np.clip(ex, 0, None)) * 26.0)) < 0.06) & water
    a[..., :3] = np.where(water[..., None], col, a[..., :3])
    a[ripple, :3] = (70, 110, 118)
    rim = water & ~(np.asarray(Image.fromarray(water.astype(np.uint8) * 255).filter(ImageFilter.MinFilter(5))) > 0)
    a[rim, :3] = (92, 84, 70)
    # Rails: wooden sleepers and two iron rails along the cart runs.
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    for run in RAILS:
        pts = [(x * TILE, y * TILE) for x, y in run]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            length = math.hypot(x1 - x0, y1 - y0)
            ux, uy = (x1 - x0) / length, (y1 - y0) / length
            nx, ny = -uy, ux
            for t in range(0, int(length), 10):
                cx, cy = x0 + ux * t, y0 + uy * t
                d.line([(cx - nx * 9, cy - ny * 9), (cx + nx * 9, cy + ny * 9)], fill=(84, 58, 38), width=3)
        for off in (-6, 6):
            d.line([(x + off * 0.0, y + off) for x, y in pts], fill=(70, 70, 76), width=2)
            d.line([(x, y + off - 1) for x, y in pts], fill=(150, 150, 160), width=1)
    im.save(GROUND_PNG)
    lv = Image.new("RGB", (COLS, ROWS))
    for r in range(ROWS):
        for c in range(COLS):
            lv.putpixel((c, r), (0, 0, 0) if stand[r][c] == 0 else (255, 0, 0))
    lv.save(LEVEL_PNG)
    return stand, water


SPAWN_DUSKARA = (25, 33)
EXIT_DUSKARA = (25, 35.7)
EXIT_DUNES = (4, 35.7)
# Props: (sprite, cell, footprint w, h, light) -- the light a (tint, energy, scale) or None.
TEAL = ((0.45, 0.95, 0.9, 1), 0.85, 1.1)
WARM = ((1.0, 0.75, 0.42, 1), 0.95, 1.4)
PROPS = [
    ("lift.png", (25, 29.6), 56, 18, None),
    ("lamp_post.png", (22.2, 31.5), 8, 6, WARM), ("lamp_post.png", (27.8, 31.5), 8, 6, WARM),
    ("support_lamp.png", (25, 23.4), 36, 8, WARM),
    # The sorting floor: three long tables, baskets and sacks, lamps.
    ("sorting_table.png", (21, 15.4), 66, 18, WARM), ("sorting_table.png", (29, 15.4), 66, 18, WARM),
    ("sorting_table.png", (25, 19.6), 66, 18, WARM),
    ("baskets.png", (19, 19.5), 30, 12, None), ("sacks.png", (30.9, 20.0), 34, 12, None),
    ("cart_empty.png", (29.5, 14.3), 28, 12, None),
    # The King's Seam: card-stone growing out of the walls, carts full of it.
    ("crystal_cluster.png", (38.7, 9.1), 26, 12, TEAL), ("crystal_tall.png", (43.7, 10.1), 24, 12, TEAL),
    ("crystal_small.png", (35.8, 15.9), 20, 10, TEAL), ("crystal_cluster.png", (44.6, 14.8), 26, 12, TEAL),
    ("crystal_tall.png", (40.2, 17.2), 24, 12, TEAL),
    ("cart_teal.png", (41.6, 12.2), 28, 12, None), ("cart_gold.png", (36.8, 13.4), 28, 12, None),
    ("support.png", (34, 11.2), 30, 8, None), ("support_lamp.png", (45.6, 13.3), 30, 8, WARM),
    # The dormitory.
    ("bunks_a.png", (7, 9.3), 66, 18, None), ("bunks_b.png", (11.8, 10.2), 66, 18, None),
    ("lamp_post.png", (13.4, 13.6), 8, 6, WARM),
    # The foreman's lower office.
    ("workbench.png", (24.0, 4.3), 34, 12, WARM), ("sacks.png", (26.7, 5.5), 34, 12, None),
    # The flooded workings.
    ("support.png", (8.1, 23.5), 30, 8, None), ("crystal_small.png", (15.0, 25.1), 20, 10, TEAL),
    ("cart_empty.png", (6.4, 26.4), 28, 12, None),
]
NPCS = [
    # id, name, cell, lines, extra props
    ("gideon", "Gideon", (22.1, 31.2), [
        "Halt there. ...Ah, you're not a runner. Nobody's checked who's coming down this shaft in years. I'm the night watch. I watch the dark.",
        "The tally gate counts you in. Show it a tag and it opens, and the book says one more head. The book's never wrong. The book's never right, either.",
        "Forty years I've watched this landing. I've seen them come down small and come up taller, and I've seen them not come up.",
        "If anyone asks, I was asleep. I'm old. I sleep a great deal. Especially when the right sort of visitor comes by.",
    ], ""),
    ("sorter_pup", "Tag 212", (22.5, 17.4), [
        "Can't talk. Count's at dawn. Teal ones in the left basket, gold in the right, cracked ones in the sack. Don't touch, they cut.",
        "My name? It's on the tag. Two-one-two. I had another one before. I'll remember it when I'm out.",
        "The foreman's fair. She says so. She counts us every night so nobody gets lost.",
    ], ""),
    ("sorter_kit", "Tag 167", (28.2, 17.4), [
        "You're not from here. You've got sun on you. What's it like up there today?",
        "I sort the King's Seam stone. It's the best. It goes to the racers, Gideon says. Maybe one of yours came through my hands.",
        "Ada's sick. She's in the bunks. Nobody's allowed to say she's sick or they'll move her to the infirmary, and nobody comes back from the infirmary.",
    ], ""),
    ("sorter_pup", "Tag 98", (23.6, 21.2), [
        "Shh. The overseer's looking.",
        "There's a light out in the dunes some nights. Green. Gideon says it's marsh-fire. There's no marsh in the dunes.",
    ], "Npc_sorter_pup2"),
    ("company_man", "Overseer", (39, 15), [
        "Visitor? No visitors in the Seam. Back up to the sorting floor.",
    ], ""),
    ("ada", "Ada", (9.4, 12.6), [
        "...Is it morning? It always feels like morning down here. Or it never does.",
    ], ""),
]
READABLES = [
    ("The tally gate", (25.9, 26.6), [
        "A turnstile of iron bars across the tunnel, a brass slot beside it for a tag, and a counter that clicks each time it turns. Painted over it: 'EVERY HEAD COUNTED. COUNT TRUE.'",
    ]),
    ("The sorting floor", (19.2, 17.6), [
        "Long tables, low enough for small arms. Trays of card-stone in teal and gold, sorted by size, by colour, by whether it will take a picture. Slates with tallies chalked on them. The chairs are crates.",
        "There's a song chalked under one table, a counting song. It counts down, not up.",
    ]),
    ("The King's Seam", (42, 11.2), [
        "The oldest working: a vein of card-stone running through the rock like a river of glass, teal and gold, lit from inside. The walls are scored with tool marks centuries deep.",
        "A plaque bolted to the rock: 'THE KING'S SEAM. Opened by the first king. Worked without interruption ever since.' Without interruption.",
    ]),
    ("The bunks", (10.0, 10.2), [
        "Bunks in rows, too short for anyone grown. A tin cup on each. A rag doll on a pillow, its face sewn on twice.",
        "Scratched into the wood of the top bunk, in many hands: names. Then a line through each, and beside some of them, a little green sun.",
    ]),
    ("The ledger of names", (25.4, 6.2), [
        "The foreman's own ledger, under a lamp in the lower office: names, ages, where from, the date down, the date up. Columns and columns. Most of the 'up' column is empty.",
        "'Corin, 14, Verdana. Sheepdog. Red scarf. Down: harvest, two years past. Up: --. Transferred: North Workings.' Further on, a page of numbers with no names at all.",
    ]),
    ("The lake under the town", (12.5, 24.4), [
        "Black water, perfectly still, stretching away under the rock. Hesper was right: Duskara floats on a lake. A bucket on a rope hangs from the ceiling far above; the Cistern's well comes down here.",
    ]),
    ("A crawl behind the old workings", (5.8, 30.6), [
        "A gap behind a fallen prop, just wide enough to crawl. The dust is swept. Someone has scratched a green sun on the timber, and an arrow: out.",
    ]),
]
CHESTS = [
    # id, cell, gold, card, item, count
    ("dorm_box", (6.3, 13.2), 10, "brass_tally_tag", "", 0),
    ("seam_cache", (44.9, 11.4), 45, "", "healers_tonic", 1),
]


def main():
    stand, water = build_ground()

    def open_at(cx, cy):
        c, r = int(cx), int(cy)
        return 0 < r < ROWS and 0 < c < COLS and stand[r][c] == 0 and stand[r - 1][c] == 0 and not in_lake(cx, cy)

    def snap(name, cell):
        """The nearest spot on open floor (it should already be there; warn when not)."""
        cx, cy = cell
        if open_at(cx, cy):
            return cell
        for rad in [k * 0.5 for k in range(1, 9)]:
            for a in range(16):
                px, py = cx + math.cos(a * math.pi / 8) * rad, cy + math.sin(a * math.pi / 8) * rad
                if open_at(px, py):
                    print(f"  nudged {name} from {cell} to ({px:.1f}, {py:.1f})")
                    return (round(px, 1), round(py, 1))
        raise SystemExit(f"{name} at cell {cell} is nowhere near the mine floor")

    for k, c in enumerate(CHESTS):
        CHESTS[k] = (c[0], snap("chest " + c[0], c[1])) + c[2:]
    for k, t in enumerate(READABLES):
        READABLES[k] = (t[0], snap("readable " + t[0], t[1]), t[2])
    for k, p in enumerate(PROPS):
        PROPS[k] = (p[0], snap("prop " + p[0], p[1])) + p[2:]
    for k, c in enumerate(NPCS):
        NPCS[k] = c[:2] + (snap("npc " + c[1], c[2]),) + c[3:]
    snap("spawn", SPAWN_DUSKARA)

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
        ('PackedScene', "res://scenes/ui/shop_panel.tscn", "5_shop"),
        ('PackedScene', "res://scenes/ui/dialogue_box.tscn", "6_dialogue"),
        ('PackedScene', "res://scenes/systems/zone_exit.tscn", "7_exit"),
        ('Texture2D', "res://" + GROUND_PNG, "8_ground"),
        ('Texture2D', "res://" + LEVEL_PNG, "9_levels"),
        ('PackedScene', "res://scenes/systems/card_gate.tscn", "10_gate"),
        ('Script', "res://scripts/systems/chest.gd", "11_chest"),
        ('Texture2D', "res://assets/sprites/tiles/thornveil/props/chest.png", "12_chest_shut"),
        ('Texture2D', "res://assets/sprites/tiles/thornveil/props/chest_open.png", "13_chest_open"),
        ('Script', "res://scripts/systems/readable.gd", "14_read"),
        ('Script', "res://scripts/systems/lamp_light.gd", "15_lamp"),
        ('PackedScene', "res://scenes/characters/npc.tscn", "17_npc"),
    ]
    tex = {}

    def texture(path):
        if path not in tex:
            tex[path] = f"t{len(tex)}"
            ext.append(('Texture2D', "res://" + path, tex[path]))
        return tex[path]

    n = [f'''[node name="DuskaraMine" type="Node2D"]
y_sort_enabled = true
script = ExtResource("1_zone")
display_name = "The North Shaft, under Duskara"
underground = true
water_shimmer = false
level_map = ExtResource("9_levels")
level_cell = {TILE}
level_origin = Vector2({LEFT}, {TOP})

[node name="Dark" type="CanvasModulate" parent="."]
color = Color(0.42, 0.36, 0.34, 1)

[node name="GroundTiles" type="Sprite2D" parent="."]
z_index = -10
position = Vector2({LEFT + COLS * TILE / 2}, {TOP + ROWS * TILE / 2})
texture = ExtResource("8_ground")
''']
    solid = [[stand[r][c] != 0 for c in range(COLS)] for r in range(ROWS)]
    walls = merge_rects(solid, LEFT, TOP, TILE)
    # The lake blocks like a wall, in 8 px strips that follow its edge.
    H, W = water.shape
    step = 8
    lake_cells = [[bool(water[min(H - 1, r * step + step // 2), min(W - 1, c * step + step // 2)]) for c in range(W // step)]
                  for r in range(H // step)]
    walls += merge_rects(lake_cells, LEFT, TOP, step)
    dx, dy = cell_px(*EXIT_DUSKARA)
    ux, uy = cell_px(*EXIT_DUNES)
    right, bottom = LEFT + COLS * TILE, TOP + ROWS * TILE
    walls += [(LEFT - 40, TOP - 40, right + 40, TOP), (LEFT - 40, TOP, LEFT, bottom), (right, TOP, right + 40, bottom),
              (LEFT - 40, bottom, ux - 30, bottom + 40), (ux + 30, bottom, dx - 50, bottom + 40), (dx + 50, bottom, right + 40, bottom + 40)]
    n.append('[node name="Walls" type="StaticBody2D" parent="."]\n')
    for k, (x0, y0, x1, y1) in enumerate(walls):
        n.append(f'[node name="W{k}" type="CollisionShape2D" parent="Walls"]\nposition = Vector2({(x0 + x1) / 2}, {(y0 + y1) / 2})\n'
                 f'shape = SubResource("{shape(x1 - x0, y1 - y0)}")\n')
    sx, sy = cell_px(*SPAWN_DUSKARA)
    n.append(f'''[node name="Spawns" type="Node2D" parent="."]

[node name="from_duskara" type="Marker2D" parent="Spawns"]
position = Vector2({sx}, {sy})

[node name="RivalSpots" type="Node2D" parent="."]

[node name="ToDuskara" parent="." instance=ExtResource("7_exit")]
position = Vector2({dx}, {bottom - 4})
target_scene = "res://scenes/world/duskara.tscn"
target_spawn = &"from_mine"
exit_hint = true

[node name="ToDunes" parent="." instance=ExtResource("7_exit")]
position = Vector2({ux}, {bottom - 4})
target_scene = "res://scenes/world/siroth_dunes.tscn"
target_spawn = &"from_mine"
exit_hint = true
''')
    for rid in ("runner", "raider", "hoarder"):
        n.append(f'[node name="{rid}" type="Marker2D" parent="RivalSpots"]\nposition = Vector2({sx}, {sy - 20})\n')
    gx, gy = cell_px(*GATE_CELL)
    n.append(f'[node name="Gate_duskara_tally_gate" parent="." instance=ExtResource("10_gate")]\nposition = Vector2({gx}, {gy})\n'
             f'gate_id = &"duskara_tally_gate"\nwidth = 96.0\nlook = &"bars"\n')
    for k, (sprite, (cx, cy), fw, fh, light) in enumerate(PROPS):
        x, y = cell_px(cx, cy)
        path = ART + sprite
        h = Image.open(path).height
        n.append(f'[node name="Prop{k}" type="StaticBody2D" parent="."]\nposition = Vector2({x}, {y})\n\n'
                 f'[node name="Sprite" type="Sprite2D" parent="Prop{k}"]\noffset = Vector2(0, {-h / 2 + 2})\n'
                 f'texture = ExtResource("{texture(path)}")\n\n'
                 f'[node name="Base" type="CollisionShape2D" parent="Prop{k}"]\nposition = Vector2(0, {-fh / 2})\n'
                 f'shape = SubResource("{shape(fw, fh)}")\n')
        if light:
            tint, energy, scale = light
            n.append(f'[node name="PropLight{k}" type="PointLight2D" parent="."]\nposition = Vector2({x}, {y - h * 0.6})\n'
                     f'texture_scale = {scale}\nscript = ExtResource("15_lamp")\nalways_on = true\nmax_energy = {energy}\n'
                     f'tint = Color{tint}\nflicker = {0.1 if tint[0] > 0.9 else 0.03}\n')
    for cid, (cx, cy), gold, card, item, count in CHESTS:
        x, y = cell_px(cx, cy)
        n.append(f'[node name="Chest_{cid}" type="StaticBody2D" parent="."]\nposition = Vector2({x}, {y})\n'
                 f'script = ExtResource("11_chest")\nchest_id = &"mine_{cid}"\ncard_id = &"{card}"\ngold = {gold}\n'
                 + (f'item_id = &"{item}"\nitem_count = {count}\n' if item else "")
                 + f'closed_texture = ExtResource("12_chest_shut")\nopen_texture = ExtResource("13_chest_open")\n\n'
                 f'[node name="Base" type="CollisionShape2D" parent="Chest_{cid}"]\nposition = Vector2(0, -5)\n'
                 f'shape = SubResource("{shape(30, 10)}")\n')
    for k, (title, (cx, cy), lines) in enumerate(READABLES):
        x, y = cell_px(cx, cy)
        quoted = ", ".join('"' + line.replace('"', '\\"') + '"' for line in lines)
        n.append(f'[node name="Read{k}" type="Node2D" parent="."]\nposition = Vector2({x}, {y})\n'
                 f'script = ExtResource("14_read")\ntitle = "{title}"\nlines = PackedStringArray({quoted})\n')
    for npc_id, display, (cx, cy), lines, node in NPCS:
        x, y = cell_px(cx, cy)
        key = f"n_{npc_id}"
        if all(e[2] != key for e in ext):
            ext.append(('SpriteFrames', f"res://assets/sprites/npcs/{npc_id}/{npc_id}_frames.tres", key))
        quoted = ", ".join('"' + line.replace('"', '\\"') + '"' for line in lines)
        n.append(f'[node name="{node or "Npc_" + npc_id}" parent="." instance=ExtResource("17_npc")]\nposition = Vector2({x}, {y})\n'
                 f'npc_id = &"{npc_id}"\ndisplay_name = "{display}"\nsprite_frames = ExtResource("{key}")\n'
                 f'lines = PackedStringArray({quoted})\n'
                 + ('sprite_offset_y = -22.0\n' if npc_id in ("ada", "sorter_pup", "sorter_kit") else ""))
    n.append(f'''[node name="Player" parent="." instance=ExtResource("2_player")]
position = Vector2({sx}, {sy})

[node name="HUD" parent="." instance=ExtResource("3_hud")]

[node name="Binder" parent="." instance=ExtResource("4_binder")]

[node name="ShopPanel" parent="." instance=ExtResource("5_shop")]

[node name="DialogueBox" parent="." instance=ExtResource("6_dialogue")]
''')
    head = f'[gd_scene load_steps={len(ext) + len(subs) + 1} format=3]\n\n'
    head += "".join(f'[ext_resource type="{t}" path="{p}" id="{i}"]\n' for t, p, i in ext) + "\n"
    head += "\n".join(subs.values()) + "\n"
    open(SCENE, "w", encoding="utf-8", newline="\n").write(head + "\n".join(n))
    print(f"mine: {COLS}x{ROWS} cells, {len(walls)} wall rects")


if __name__ == "__main__":
    main()
