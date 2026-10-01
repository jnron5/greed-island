"""Builds the Frost Grotto: an ice cave in the east shoulder of the Starfall Range.

Hald's map shows "a second route round the east shoulder of the mountain", rubbed
out again: this is it. The Company's smugglers used it to move the Duskara cargo
north after the pass was brought down; now frost wolves den in it. Four parts: the
mouth (the way back out to the Range), a hall of hanging ice, the wolves' den, and at
the far end a sealed ice wall with daylight behind it (Frisalle, for later) and the
smugglers' abandoned cache with the Frostfang Charm.

Terrain is composed with terrain.compose() from a PixelLab ice cave cliff set
(assets/sprites/tiles/starfall/cliff/ice_cave): level 0 is cave floor, level 1 solid
ice, its faces hanging one row below it. Collision is every cell that isn't floor.
Layout in cells (32 px): chambers are circles, tunnels capsules between cell points.

Run: python scripts/tools/build_grotto.py
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
COLS, ROWS = 42, 30
LEFT, TOP = -COLS * TILE // 2, -ROWS * TILE // 2
ART = "assets/sprites/tiles/starfall/"
GROUND_PNG = ART + "grotto_ground.png"
LEVEL_PNG = ART + "grotto_levels.png"
SCENE = "scenes/world/starfall_grotto.tscn"

CHAMBERS = {
    "mouth": (7, 24, 4.4),
    "hall": (16, 14, 6.2),
    "den": (30, 20, 5.8),
    "cache": (33, 7, 4.6),
}
TUNNELS = [
    ((7, 24), (7, 29.9), 2.2),      # in from the Range: the mouth opens at the bottom edge
    ((7, 24), (12, 18), 2.4),
    ((16, 14), (25, 18), 2.2),
    ((30, 20), (32, 11), 2.0),
]


def cell_px(cx, cy):
    return (LEFT + cx * TILE, TOP + cy * TILE)


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy or 1)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def is_floor(cx, cy):
    wobble = 0.35 * math.sin(cx * 1.3 + cy * 0.7) + 0.25 * math.sin(cx * 0.5 - cy * 1.1)
    for x, y, r in CHAMBERS.values():
        if math.hypot(cx - x, (cy - y) * 1.1) < r + wobble:
            return True
    return any(seg_dist(cx, cy, *a, *b) < w + wobble * 0.5 for a, b, w in TUNNELS)


def build_ground():
    levels = [[0 if is_floor(c, r) and 0 < c < COLS and r > 0 else 1 for c in range(COLS + 1)]
              for r in range(ROWS + 1)]
    ice = CliffSet(ART + "cliff/ice_cave")
    img, stand = compose(levels, {(0, 1): ice}, {0: ((0, 1), "lower"), 1: ((0, 1), "upper")}, TILE)
    a = np.array(img).astype(float)
    rock = np.kron(np.array([[1 if v == 1 else 0 for v in row] for row in stand], np.uint8),
                   np.ones((TILE, TILE), np.uint8)).astype(bool)
    a[rock, :3] *= 0.6
    img = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    img.save(GROUND_PNG)
    lv = Image.new("RGB", (COLS, ROWS))
    for r in range(ROWS):
        for c in range(COLS):
            lv.putpixel((c, r), (0, 0, 0) if stand[r][c] == 0 else (255, 0, 0))
    lv.save(LEVEL_PNG)
    return stand


SPAWN_IN = (7, 27.5)
EXIT_AT = (7, 29.6)
WOLVES = [(29, 19), (31.5, 22)]
CRYSTALS = [(12, 12.5), (20, 13.5), (13, 17.5), (5, 23), (27, 18), (33, 22), (30.5, 8.5), (36, 7)]
CHESTS = [
    # id, cell, gold, card, item, count
    ("hall_crate", (19, 17), 30, "", "healers_tonic", 1),
    ("smugglers_cache", (35, 9), 40, "frostfang_charm", "", 0),
]
READABLES = [
    ("Frozen crates", (16.5, 12.5), [
        "Crates frozen into the floor, their lids split by the cold. Stencilled: 'D.M.C. - NORTH - BY THE SHOULDER'.",
        "Inside: straw, a tin cup, a child's mitten. Whatever was carried in these could walk.",
    ]),
    ("An ice wall", (33, 6), [
        "The tunnel ends in a wall of clear ice, thick as a house. Through it, faint and blue: daylight, and a road going down the far side of the mountain.",
        "Frisalle is that way. Somebody sealed this from the other side.",
    ]),
]


def main():
    stand = build_ground()

    def check(name, cx, cy):
        c, r = int(cx), int(cy)
        if not (0 <= r < ROWS and 0 <= c < COLS) or stand[r][c] != 0:
            raise SystemExit(f"{name} at cell ({cx}, {cy}) is not on the cave floor")

    for name, (cx, cy) in [("spawn", SPAWN_IN)] + [(f"wolf{k}", p) for k, p in enumerate(WOLVES)] \
            + [(f"chest {c[0]}", c[1]) for c in CHESTS] + [(f"readable {t}", p) for t, p, _ in READABLES] \
            + [("crystal", p) for p in CRYSTALS]:
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
        ('PackedScene', "res://scenes/characters/frost_wolf.tscn", "10_wolf"),
        ('Script', "res://scripts/systems/chest.gd", "11_chest"),
        ('Texture2D', "res://assets/sprites/tiles/thornveil/props/chest.png", "12_chest_shut"),
        ('Texture2D', "res://assets/sprites/tiles/thornveil/props/chest_open.png", "13_chest_open"),
        ('Script', "res://scripts/systems/readable.gd", "14_read"),
        ('Script', "res://scripts/systems/lamp_light.gd", "15_lamp"),
        ('Texture2D', "res://" + ART + "ice_crystals.png", "16_ice"),
    ]
    n = [f'''[node name="StarfallGrotto" type="Node2D"]
y_sort_enabled = true
script = ExtResource("1_zone")
display_name = "The Frost Grotto, under the Starfall pass"
underground = true
water_shimmer = false
level_map = ExtResource("9_levels")
level_cell = {TILE}
level_origin = Vector2({LEFT}, {TOP})

[node name="Dark" type="CanvasModulate" parent="."]
color = Color(0.4, 0.48, 0.62, 1)

[node name="GroundTiles" type="Sprite2D" parent="."]
z_index = -10
position = Vector2({LEFT + COLS * TILE / 2}, {TOP + ROWS * TILE / 2})
texture = ExtResource("8_ground")
''']
    solid = [[stand[r][c] != 0 for c in range(COLS)] for r in range(ROWS)]
    walls = merge_rects(solid, LEFT, TOP, TILE)
    ex, ey = cell_px(*EXIT_AT)
    right, bottom = LEFT + COLS * TILE, TOP + ROWS * TILE
    walls += [(LEFT - 40, TOP - 40, right + 40, TOP), (LEFT - 40, TOP, LEFT, bottom), (right, TOP, right + 40, bottom),
              (LEFT - 40, bottom, ex - 40, bottom + 40), (ex + 40, bottom, right + 40, bottom + 40)]
    n.append('[node name="Walls" type="StaticBody2D" parent="."]\n')
    for k, (x0, y0, x1, y1) in enumerate(walls):
        n.append(f'[node name="W{k}" type="CollisionShape2D" parent="Walls"]\nposition = Vector2({(x0 + x1) / 2}, {(y0 + y1) / 2})\n'
                 f'shape = SubResource("{shape(x1 - x0, y1 - y0)}")\n')
    sx, sy = cell_px(*SPAWN_IN)
    n.append(f'''[node name="Spawns" type="Node2D" parent="."]

[node name="from_starfall" type="Marker2D" parent="Spawns"]
position = Vector2({sx}, {sy})

[node name="RivalSpots" type="Node2D" parent="."]

[node name="ToStarfall" parent="." instance=ExtResource("7_exit")]
position = Vector2({ex}, {bottom - 4})
target_scene = "res://scenes/world/starfall_range.tscn"
target_spawn = &"from_grotto"
exit_hint = true
''')
    for rid in ("runner", "raider", "hoarder"):
        n.append(f'[node name="{rid}" type="Marker2D" parent="RivalSpots"]\nposition = Vector2({sx}, {sy - 20})\n')
    for k, (cx, cy) in enumerate(WOLVES):
        x, y = cell_px(cx, cy)
        n.append(f'[node name="FrostWolf{k}" parent="." instance=ExtResource("10_wolf")]\nposition = Vector2({x}, {y})\n')
    for cid, (cx, cy), gold, card, item, count in CHESTS:
        x, y = cell_px(cx, cy)
        n.append(f'[node name="Chest_{cid}" type="StaticBody2D" parent="."]\nposition = Vector2({x}, {y})\n'
                 f'script = ExtResource("11_chest")\nchest_id = &"grotto_{cid}"\ncard_id = &"{card}"\ngold = {gold}\n'
                 + (f'item_id = &"{item}"\nitem_count = {count}\n' if item else "")
                 + f'closed_texture = ExtResource("12_chest_shut")\nopen_texture = ExtResource("13_chest_open")\n\n'
                 f'[node name="Base" type="CollisionShape2D" parent="Chest_{cid}"]\nposition = Vector2(0, -5)\n'
                 f'shape = SubResource("{shape(30, 10)}")\n')
    for k, (title, (cx, cy), lines) in enumerate(READABLES):
        x, y = cell_px(cx, cy)
        quoted = ", ".join('"' + line.replace('"', '\\"') + '"' for line in lines)
        n.append(f'[node name="Read{k}" type="Node2D" parent="."]\nposition = Vector2({x}, {y})\n'
                 f'script = ExtResource("14_read")\ntitle = "{title}"\nlines = PackedStringArray({quoted})\n')
    h = Image.open(ART + "ice_crystals.png").height
    for k, (cx, cy) in enumerate(CRYSTALS):
        x, y = cell_px(cx, cy)
        n.append(f'[node name="Crystal{k}" type="StaticBody2D" parent="."]\nposition = Vector2({x}, {y})\n\n'
                 f'[node name="Sprite" type="Sprite2D" parent="Crystal{k}"]\noffset = Vector2(0, {-h / 2 + 4})\n'
                 f'flip_h = {"true" if k % 2 else "false"}\ntexture = ExtResource("16_ice")\n\n'
                 f'[node name="Base" type="CollisionShape2D" parent="Crystal{k}"]\nposition = Vector2(0, -5)\n'
                 f'shape = SubResource("{shape(28, 10)}")\n\n'
                 f'[node name="CrystalGlow{k}" type="PointLight2D" parent="."]\nposition = Vector2({x}, {y - 20})\n'
                 f'texture_scale = 1.2\nscript = ExtResource("15_lamp")\nalways_on = true\nmax_energy = 0.85\n'
                 f'tint = Color(0.55, 0.85, 1.0, 1)\nflicker = 0.03\n')
    # Daylight through the ice wall at the far end.
    wx, wy = cell_px(32, 4.2)
    n.append(f'[node name="IceDaylight" type="PointLight2D" parent="."]\nposition = Vector2({wx}, {wy})\n'
             f'texture_scale = 2.0\nscript = ExtResource("15_lamp")\nalways_on = true\nmax_energy = 0.7\n'
             f'tint = Color(0.8, 0.92, 1.0, 1)\nflicker = 0.0\n')
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
    print(f"grotto: {COLS}x{ROWS} cells, {len(walls)} wall rects")


if __name__ == "__main__":
    main()
