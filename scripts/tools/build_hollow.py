"""Builds the Hollow: the cave under Sorenda's roots, past the moss gate.

"What the Trees Remember" ends here. A winding cave in five parts, each a little
further from the light: the mouth (the way back up to Sorenda), a grotto of glowing
mushrooms with a traveller's chest, a narrow crawl, the great chamber where the hollow
bear has made its den, and at the far end the dry alcove where a runaway child hid:
the satchel (Readable "A satchel in the moss", which moves the quest on) and a chest.

Terrain is composed with terrain.compose() from a PixelLab cave cliff set
(assets/sprites/tiles/hollow/cliff/cave): level 0 is cave floor, level 1 solid rock,
and the rock's faces hang one row below it. Collision is every cell that isn't floor
(visible rock, never an invisible wall). The layout below is in cells (32 px):
chambers are circles, tunnels are capsules between cell points.

Run: python scripts/tools/build_hollow.py
"""
import math
import os
import sys

import numpy as np
from PIL import Image

os.chdir(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, "scripts/tools")
from terrain import CliffSet, compose, merge_rects  # noqa: E402

TILE = 32
COLS, ROWS = 46, 34
LEFT, TOP = -COLS * TILE // 2, -ROWS * TILE // 2
ART = "assets/sprites/tiles/hollow/"
GROUND_PNG = ART + "hollow_ground.png"
LEVEL_PNG = ART + "hollow_levels.png"
SCENE = "scenes/world/sorenda_hollow.tscn"

# (cell x, cell y, radius in cells)
CHAMBERS = {
    "mouth": (8, 28, 4.6),
    "grotto": (11, 15, 5.6),
    "den": (31, 20, 7.6),
    "pool": (39, 28, 4.0),
    "alcove": (39, 9, 4.6),
}
# (from cell, to cell, half-width in cells)
TUNNELS = [
    ((8, 28), (8, 33.9), 2.2),       # up from Sorenda: the mouth opens at the map's bottom edge
    ((8, 28), (10, 19), 2.6),
    ((11, 15), (21, 11), 2.3),
    ((21, 11), (25, 14), 2.0),       # the crawl
    ((25, 14), (27, 18), 2.1),
    ((31, 20), (39, 28), 2.1),
    ((31, 20), (37, 13), 2.3),
    ((37, 13), (39, 9), 2.2),
]


def cell_px(cx, cy):
    """World position of a cell point (cell units, fractional)."""
    return (LEFT + cx * TILE, TOP + cy * TILE)


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy or 1)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def is_floor(cx, cy):
    """Is the corner at (cx, cy) (cell units) open cave floor? A little noise keeps the
    walls from looking compass-drawn."""
    wobble = 0.35 * math.sin(cx * 1.7 + cy * 0.9) + 0.25 * math.sin(cx * 0.6 - cy * 1.3)
    for x, y, r in CHAMBERS.values():
        if math.hypot(cx - x, (cy - y) * 1.1) < r + wobble:
            return True
    return any(seg_dist(cx, cy, *a, *b) < w + wobble * 0.5 for a, b, w in TUNNELS)


def build_ground():
    levels = [[0 if is_floor(c, r) and 0 < c < COLS and r > 0 else 1 for c in range(COLS + 1)]
              for r in range(ROWS + 1)]
    cave = CliffSet(ART + "cliff/cave")
    img, stand = compose(levels, {(0, 1): cave}, {0: ((0, 1), "lower"), 1: ((0, 1), "upper")}, TILE)
    # Darken the rock tops so the floor reads as the lit part of the cave.
    a = np.array(img).astype(float)
    rock = np.kron(np.array([[1 if v == 1 else 0 for v in row] for row in stand], np.uint8),
                   np.ones((TILE, TILE), np.uint8)).astype(bool)
    a[rock, :3] *= 0.55
    img = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    os.makedirs(ART, exist_ok=True)
    img.save(GROUND_PNG)
    lv = Image.new("RGB", (COLS, ROWS))
    for r in range(ROWS):
        for c in range(COLS):
            lv.putpixel((c, r), (0, 0, 0) if stand[r][c] == 0 else (255, 0, 0))
    lv.save(LEVEL_PNG)
    return stand


# Things in the cave (cell positions).
SPAWN_IN = (7.5, 31)                    # arriving from Sorenda
EXIT_AT = (7.5, 33.6)
BEAR = (31, 19)
GLOW_MUSHROOMS = [(6.5, 13.5), (15, 12.5), (7, 17.5), (12, 16), (5, 27.5), (10.5, 29), (26, 16), (36, 17),
                  (25.5, 22), (36.5, 23), (40.5, 28.5), (37, 8), (41.5, 10)]
CRYSTAL_ROCKS = [(13.5, 14.5), (26.5, 19.5), (35, 21), (35.5, 11.5)]
FIREFLIES = [(11, 15), (39, 9)]
CHESTS = [
    # id, cell, gold, card, item, count
    ("grotto_cache", (14, 13.5), 30, "", "healers_tonic", 1),
    ("pool_ledge", (40, 29), 0, "", "sea_salt_elixir", 1),
    ("childs_hiding", (40, 9.5), 20, "sorenda_star_map", "", 0),
]
READABLES = [
    ("Scratches on the wall", (8, 24.5), [
        "Tally marks, scratched low on the rock with a stone. Seven of them. Then the scratches stop being tallies and start being a small, careful drawing of a door.",
    ]),
    ("A torn sleeve", (21, 12.5), [
        "A strip of rough cloth caught on the rock where the passage narrows. It's stamped, like a sack: 'D.M. - issue'.",
        "Someone small squeezed through here. Something much bigger has been rubbing the rock smooth trying to follow.",
    ]),
    ("A satchel in the moss", (38.5, 8.5), [
        "A canvas satchel, stiff with old rain, tucked into the driest corner of the cave. Inside: a heel of bread gone to stone, a little carved wooden bird, and a tin work tag stamped 'D.M. - No. 117'.",
        "Scratched into the rock above it, low down, where a small hand could reach: 'I ran. Tell mama I ran.'",
    ]),
]


def main():
    stand = build_ground()

    def check(name, cx, cy):
        c, r = int(cx), int(cy)
        if not (0 <= r < ROWS and 0 <= c < COLS) or stand[r][c] != 0:
            raise SystemExit(f"{name} at cell ({cx}, {cy}) is not on the cave floor")

    for name, (cx, cy) in [("spawn", SPAWN_IN), ("bear", BEAR)] + [(f"chest {c[0]}", c[1]) for c in CHESTS] \
            + [(f"readable {t}", p) for t, p, _ in READABLES] + [("mushroom", p) for p in GLOW_MUSHROOMS] \
            + [("crystal rock", p) for p in CRYSTAL_ROCKS]:
        check(name, cx, cy)

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
        ('PackedScene', "res://scenes/characters/hollow_bear.tscn", "10_bear"),
        ('Script', "res://scripts/systems/chest.gd", "11_chest"),
        ('Texture2D', "res://assets/sprites/tiles/thornveil/props/chest.png", "12_chest_shut"),
        ('Texture2D', "res://assets/sprites/tiles/thornveil/props/chest_open.png", "13_chest_open"),
        ('Script', "res://scripts/systems/readable.gd", "14_read"),
        ('Script', "res://scripts/systems/lamp_light.gd", "15_lamp"),
        ('Texture2D', "res://" + ART + "glow_mushrooms.png", "16_mushroom"),
        ('Texture2D', "res://" + ART + "crystal_rock.png", "17_rock"),
        ('Script', "res://scripts/world/fireflies.gd", "18_fireflies"),
    ]
    n = []
    n.append(f'''[node name="SorendaHollow" type="Node2D"]
y_sort_enabled = true
script = ExtResource("1_zone")
display_name = "The Hollow, under Sorenda"
underground = true
water_shimmer = false
level_map = ExtResource("9_levels")
level_cell = {TILE}
level_origin = Vector2({LEFT}, {TOP})

[node name="Dark" type="CanvasModulate" parent="."]
color = Color(0.34, 0.38, 0.46, 1)

[node name="GroundTiles" type="Sprite2D" parent="."]
z_index = -10
position = Vector2({LEFT + COLS * TILE / 2}, {TOP + ROWS * TILE / 2})
texture = ExtResource("8_ground")
''')
    # Rock blocks exactly where it's drawn; the map's edges too, except the way out.
    solid = [[stand[r][c] != 0 for c in range(COLS)] for r in range(ROWS)]
    walls = merge_rects(solid, LEFT, TOP, TILE)
    ex, ey = cell_px(*EXIT_AT)
    walls += [(LEFT - 40, TOP - 40, RIGHT + 40, TOP) for RIGHT in [LEFT + COLS * TILE]]
    walls += [(LEFT - 40, TOP, LEFT, TOP + ROWS * TILE), (LEFT + COLS * TILE, TOP, LEFT + COLS * TILE + 40, TOP + ROWS * TILE)]
    bottom = TOP + ROWS * TILE
    walls += [(LEFT - 40, bottom, ex - 40, bottom + 40), (ex + 40, bottom, LEFT + COLS * TILE + 40, bottom + 40)]
    n.append('[node name="Walls" type="StaticBody2D" parent="."]\n')
    for k, (x0, y0, x1, y1) in enumerate(walls):
        n.append(f'[node name="W{k}" type="CollisionShape2D" parent="Walls"]\nposition = Vector2({(x0 + x1) / 2}, {(y0 + y1) / 2})\n'
                 f'shape = SubResource("{shape(x1 - x0, y1 - y0)}")\n')

    sx, sy = cell_px(*SPAWN_IN)
    n.append(f'''[node name="Spawns" type="Node2D" parent="."]

[node name="from_sorenda" type="Marker2D" parent="Spawns"]
position = Vector2({sx}, {sy})

[node name="RivalSpots" type="Node2D" parent="."]

[node name="ToSorenda" parent="." instance=ExtResource("7_exit")]
position = Vector2({ex}, {bottom - 4})
target_scene = "res://scenes/world/sorenda.tscn"
target_spawn = &"from_hollow"
exit_hint = true
''')
    for rid in ("runner", "raider", "hoarder"):
        n.append(f'[node name="{rid}" type="Marker2D" parent="RivalSpots"]\nposition = Vector2({sx}, {sy - 20})\n')

    bx, by = cell_px(*BEAR)
    n.append(f'[node name="HollowBear" parent="." instance=ExtResource("10_bear")]\nposition = Vector2({bx}, {by})\n')

    for cid, (cx, cy), gold, card, item, count in CHESTS:
        x, y = cell_px(cx, cy)
        n.append(f'[node name="Chest_{cid}" type="StaticBody2D" parent="."]\nposition = Vector2({x}, {y})\n'
                 f'script = ExtResource("11_chest")\nchest_id = &"hollow_{cid}"\ncard_id = &"{card}"\ngold = {gold}\n'
                 + (f'item_id = &"{item}"\nitem_count = {count}\n' if item else "")
                 + f'closed_texture = ExtResource("12_chest_shut")\nopen_texture = ExtResource("13_chest_open")\n\n'
                 f'[node name="Base" type="CollisionShape2D" parent="Chest_{cid}"]\nposition = Vector2(0, -5)\n'
                 f'shape = SubResource("{shape(30, 10)}")\n')
    for k, (title, (cx, cy), lines) in enumerate(READABLES):
        x, y = cell_px(cx, cy)
        quoted = ", ".join('"' + line.replace('"', '\\"') + '"' for line in lines)
        n.append(f'[node name="Read{k}" type="Node2D" parent="."]\nposition = Vector2({x}, {y})\n'
                 f'script = ExtResource("14_read")\ntitle = "{title}"\nlines = PackedStringArray({quoted})\n')
    # Light: glowing mushrooms (each a soft teal lamp) and crystal rocks, nothing else.
    for k, (cx, cy) in enumerate(GLOW_MUSHROOMS):
        x, y = cell_px(cx, cy)
        n.append(f'[node name="Mushrooms{k}" type="Sprite2D" parent="."]\nposition = Vector2({x}, {y})\n'
                 f'offset = Vector2(0, -18)\ntexture = ExtResource("16_mushroom")\n\n'
                 f'[node name="Glow{k}" type="PointLight2D" parent="."]\nposition = Vector2({x}, {y - 14})\n'
                 f'texture_scale = 1.3\nscript = ExtResource("15_lamp")\nalways_on = true\nmax_energy = 0.9\n'
                 f'tint = Color(0.45, 0.95, 0.85, 1)\nflicker = 0.04\n')
    for k, (cx, cy) in enumerate(CRYSTAL_ROCKS):
        x, y = cell_px(cx, cy)
        n.append(f'[node name="Crystal{k}" type="StaticBody2D" parent="."]\nposition = Vector2({x}, {y})\n\n'
                 f'[node name="Sprite" type="Sprite2D" parent="Crystal{k}"]\noffset = Vector2(0, -22)\n'
                 f'texture = ExtResource("17_rock")\n\n'
                 f'[node name="Base" type="CollisionShape2D" parent="Crystal{k}"]\nposition = Vector2(0, -8)\n'
                 f'shape = SubResource("{shape(44, 16)}")\n\n'
                 f'[node name="CrystalGlow{k}" type="PointLight2D" parent="."]\nposition = Vector2({x}, {y - 20})\n'
                 f'texture_scale = 1.0\nscript = ExtResource("15_lamp")\nalways_on = true\nmax_energy = 0.7\n'
                 f'tint = Color(0.4, 0.85, 1.0, 1)\nflicker = 0.02\n')
    # Cave litter: rocks, pale mushrooms, fallen branches and old roots on the floor,
    # tinted cave-dark, never on the way through (kept off a clear line down every
    # tunnel) and clear of everything placed above.
    import random
    rng = random.Random(4)
    placed = [SPAWN_IN, BEAR, EXIT_AT] + [c[1] for c in CHESTS] + [r[1] for r in READABLES] \
        + GLOW_MUSHROOMS + CRYSTAL_ROCKS
    litter = []
    kinds = [("rock", True), ("pale_mushrooms", False), ("branch", False), ("rock", True), ("log", True), ("stump", True)]
    for _ in range(3000):
        if len(litter) >= 34:
            break
        cx, cy = rng.uniform(1, COLS - 1), rng.uniform(1, ROWS - 1)
        c, r = int(cx), int(cy)
        if not all(0 <= r + dr < ROWS and 0 <= c + dc < COLS and stand[r + dr][c + dc] == 0
                   for dr in (-1, 0, 1) for dc in (-1, 0, 1)):
            continue
        if any(seg_dist(cx, cy, *a, *b) < 0.9 for a, b, _ in TUNNELS):
            continue
        if any(math.hypot(cx - px, cy - py) < 2.2 for px, py in placed + [(x, y) for _, x, y, _ in litter]):
            continue
        name, solid = rng.choice(kinds)
        litter.append((name, cx, cy, solid))
    for k, (name, cx, cy, solid) in enumerate(litter):
        x, y = cell_px(cx, cy)
        tex = f"res://assets/sprites/tiles/forest/props/{name}.png"
        if ("Texture2D", tex, f"19_{name}") not in ext:
            ext.append(("Texture2D", tex, f"19_{name}"))
        h = Image.open(tex.replace("res://", "")).height
        tint = "modulate = Color(0.62, 0.7, 0.8, 1)\n"
        if solid:
            n.append(f'[node name="Litter{k}" type="StaticBody2D" parent="."]\nposition = Vector2({x:.0f}, {y:.0f})\n\n'
                     f'[node name="Sprite" type="Sprite2D" parent="Litter{k}"]\n{tint}offset = Vector2(0, {-h / 2 + 2})\n'
                     f'texture = ExtResource("19_{name}")\n\n'
                     f'[node name="Base" type="CollisionShape2D" parent="Litter{k}"]\nposition = Vector2(0, -3)\n'
                     f'shape = SubResource("{shape(22, 8)}")\n')
        else:
            n.append(f'[node name="Litter{k}" type="Sprite2D" parent="."]\nposition = Vector2({x:.0f}, {y:.0f})\n'
                     f'{tint}offset = Vector2(0, {-h / 2 + 2})\ntexture = ExtResource("19_{name}")\n')
    for k, (cx, cy) in enumerate(FIREFLIES):
        x, y = cell_px(cx, cy)
        n.append(f'[node name="Fireflies{k}" type="Node2D" parent="."]\nposition = Vector2({x}, {y})\n'
                 f'script = ExtResource("18_fireflies")\ncount = 7\nseed = {k + 40}\nradius = 70.0\nalways = true\n')

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
    print(f"hollow: {COLS}x{ROWS} cells, {len(walls)} wall rects")


if __name__ == "__main__":
    main()
