"""Build Lake Veyra: the ground image (from the PixelLab lake/forest Wang tileset)
and the zone scene, with water collision derived from the same terrain grid.

Usage: python scripts/tools/build_lake_veyra.py
Writes assets/sprites/tiles/thornveil/lake_veyra_ground.png and
scenes/world/lake_veyra.tscn. Re-running overwrites the scene, so change the
layout here rather than in the editor.

Layout (local coords, zone spans x -512..512, y -400..400):
- Enter from Thornveil at the east edge; the Bramble Arch (2 Thorn Sprigs) stands
  across the entry passage.
- The lake fills the middle. The Moss Bridge (1 Moss Lantern) crosses from the
  south shore to an island holding a Veyra Pearl.
- The Shore Path (2 Veyra Reeds) is the only way onto the north shore, where the
  Elder Grove Seal (1 Veyra Pearl) guards a pearl shrine.
"""
import json
import math
import os
import random

from PIL import Image

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
os.chdir(ROOT)

TILE = 32
COLS, ROWS = 32, 25
LEFT, TOP = -512, -400
LAKE_C = (0.0, -60.0)
LAKE_R = (330.0, 190.0)
ISLAND_R = 72.0
BRIDGE_X = 12  # half-width of the walkable plank deck
BRIDGE_Y = (4, 132)  # island edge -> south shore


def is_water(x: float, y: float) -> bool:
    in_lake = ((x - LAKE_C[0]) / LAKE_R[0]) ** 2 + ((y - LAKE_C[1]) / LAKE_R[1]) ** 2 < 1.0
    on_island = math.hypot(x - LAKE_C[0], y - LAKE_C[1]) < ISLAND_R
    return in_lake and not on_island


# ------------------------------------------------------------ ground image
meta = json.load(open("assets/sprites/tiles/thornveil/wang/lake_forest_metadata.json"))
sheet = Image.open("assets/sprites/tiles/thornveil/wang/lake_forest_image.png").convert("RGBA")
tiles = {}
for t in meta["tileset_data"]["tiles"]:
    c = t["corners"]
    idx = (c["NW"] == "upper") * 8 + (c["NE"] == "upper") * 4 + (c["SW"] == "upper") * 2 + (c["SE"] == "upper")
    b = t["bounding_box"]
    tiles[idx] = sheet.crop((b["x"], b["y"], b["x"] + b["width"], b["y"] + b["height"]))

land = [[not is_water(LEFT + i * TILE, TOP + j * TILE) for i in range(COLS + 1)] for j in range(ROWS + 1)]
ground = Image.new("RGBA", (COLS * TILE, ROWS * TILE))
blocked = [[False] * COLS for _ in range(ROWS)]
for j in range(ROWS):
    for i in range(COLS):
        nw, ne, sw, se = land[j][i], land[j][i + 1], land[j + 1][i], land[j + 1][i + 1]
        ground.paste(tiles[nw * 8 + ne * 4 + sw * 2 + se], (i * TILE, j * TILE))
        blocked[j][i] = (4 - (nw + ne + sw + se)) >= 3  # mostly water
ground.save("assets/sprites/tiles/thornveil/lake_veyra_ground.png")

# ------------------------------------------------------------ water collision (row runs, bridge cut out)
water_rects = []  # (x0, y0, x1, y1) in local coords
for j in range(ROWS):
    i = 0
    while i < COLS:
        if not blocked[j][i]:
            i += 1
            continue
        start = i
        while i < COLS and blocked[j][i]:
            i += 1
        x0, x1 = LEFT + start * TILE, LEFT + i * TILE
        y0, y1 = TOP + j * TILE, TOP + (j + 1) * TILE
        if y1 > BRIDGE_Y[0] and y0 < BRIDGE_Y[1] and x0 < -BRIDGE_X and x1 > BRIDGE_X:
            water_rects += [(x0, y0, -BRIDGE_X, y1), (BRIDGE_X, y0, x1, y1)]
        else:
            water_rects.append((x0, y0, x1, y1))

# ------------------------------------------------------------ scene
subs, shapes = {}, []
def rect_shape(w, h):
    key = f"R{w}x{h}"
    if key not in subs:
        subs[key] = f'[sub_resource type="RectangleShape2D" id="{key}"]\nsize = Vector2({w}, {h})\n'
    return key

def body(name, rects):
    lines = [f'[node name="{name}" type="StaticBody2D" parent="."]\n']
    for k, (x0, y0, x1, y1) in enumerate(rects):
        key = rect_shape(x1 - x0, y1 - y0)
        lines.append(f'[node name="S{k}" type="CollisionShape2D" parent="{name}"]\n'
                     f'position = Vector2({(x0 + x1) / 2}, {(y0 + y1) / 2})\nshape = SubResource("{key}")\n')
    return lines

walls = [
    (-552, -440, 552, -400), (-552, 400, 552, 440),          # north, south
    (-552, -400, -512, 400),                                  # west
    (512, -400, 552, 226), (512, 274, 552, 400), (552, 226, 580, 274),  # east with entry gap
    (426, -400, 434, 228), (426, 272, 434, 400),              # Bramble Arch line
    (-512, -65, -374, -55), (-335, -65, -300, -55),           # Shore Path line (west)
    (300, -65, 426, -55),                                     # east side: no way north
    (-385, -400, -375, -280),                                 # Elder Grove east side
    (-512, -285, -468, -275), (-424, -285, -380, -275),       # Elder Grove south, seal gap
]

random.seed(31)
trees = []
keep_clear = [(470, 250, 70), (0, 160, 60), (-352, -60, 60), (-446, -250, 50), (-446, -340, 70)]
while len(trees) < 26:
    x, y = random.randint(-495, 410), random.randint(-390, 390)
    near_water = ((x - LAKE_C[0]) / (LAKE_R[0] + 50)) ** 2 + ((y - LAKE_C[1]) / (LAKE_R[1] + 50)) ** 2 < 1.0
    if near_water or any((x - a) ** 2 + (y - b) ** 2 < r ** 2 for a, b, r in keep_clear):
        continue
    if -512 < x < -375 and -400 < y < -275:
        continue  # inside the Elder Grove
    if abs(y + 60) < 30:
        continue  # the Shore Path / barrier line
    if any((x - a) ** 2 + (y - b) ** 2 < 60 ** 2 for a, b in trees):
        continue
    trees.append((x, y))

drops = '[&"veyra_reed", &"moss_lantern", &"thorn_sprig"]'
hounds = [(-250, 260), (100, 270), (260, 190), (60, -330)]
pickups = [
    ("veyra_pearl", (0, -75), "thornveil_moss_bridge", "IslandPearl"),
    ("veyra_pearl", (-446, -325), "elder_grove_seal", "ShrinePearl"),
    ("veyra_reed", (150, -320), "veyra_shore_path", "NorthReed"),
    ("canopy_seed", (-160, -330), "veyra_shore_path", "NorthSeed"),
]
gates = [
    ("BrambleArch", (430, 250), "thornveil_bramble_arch", True),
    ("MossBridgeGate", (0, 146), "thornveil_moss_bridge", False),
    ("ShorePathGate", (-352, -60), "veyra_shore_path", False),
    ("ElderGroveSeal", (-446, -280), "elder_grove_seal", False),
]

nodes = ['''[node name="LakeVeyra" type="Node2D"]
y_sort_enabled = true
script = ExtResource("1_zone")
display_name = "Lake Veyra"

[node name="Ground" type="Sprite2D" parent="."]
z_index = -10
texture = ExtResource("10_ground")

[node name="EntryPath" type="ColorRect" parent="."]
z_index = -9
offset_left = 500.0
offset_top = 226.0
offset_right = 580.0
offset_bottom = 274.0
mouse_filter = 2
color = Color(0.5, 0.44, 0.32, 1)

[node name="MossBridge" type="Sprite2D" parent="."]
z_index = -8
position = Vector2(0, 67)
texture = ExtResource("11_bridge")

[node name="ElderShrine" parent="." instance=ExtResource("12_shrine")]
position = Vector2(-446, -350)
''']
nodes += body("Water", water_rects)
nodes += body("Walls", walls)
# Interior walls (everything after the outer boundary) get a visible bramble hedge.
for k, (x0, y0, x1, y1) in enumerate(walls[6:]):
    pad = 3
    nodes.append(f'[node name="Hedge{k}" type="ColorRect" parent="."]\nz_index = -7\n'
                 f'offset_left = {x0 - pad}.0\noffset_top = {y0 - pad}.0\n'
                 f'offset_right = {x1 + pad}.0\noffset_bottom = {y1 + pad}.0\n'
                 f'mouse_filter = 2\ncolor = Color(0.2, 0.3, 0.14, 1)\n')
nodes.append('''[node name="Spawns" type="Node2D" parent="."]

[node name="from_thornveil" type="Marker2D" parent="Spawns"]
position = Vector2(470, 250)

[node name="ToThornveil" parent="." instance=ExtResource("7_exit")]
position = Vector2(535, 250)
rotation = 1.5708
target_scene = "res://scenes/world/thornveil.tscn"
target_spawn = &"from_lake"
''')
for name, (x, y), gate_id, vertical in gates:
    nodes.append(f'[node name="{name}" parent="." instance=ExtResource("8_gate")]\nposition = Vector2({x}, {y})\n'
                 f'gate_id = &"{gate_id}"\n' + ("vertical = true\n" if vertical else ""))
for card, (x, y), gate_id, name in pickups:
    nodes.append(f'[node name="Card_{name}" parent="." instance=ExtResource("5_pick")]\nposition = Vector2({x}, {y})\n'
                 f'card_id = &"{card}"\nbehind_gate = &"{gate_id}"\n')
for k, (x, y) in enumerate(hounds):
    nodes.append(f'[node name="BriarHound{k + 1}" parent="." instance=ExtResource("6_hound")]\nposition = Vector2({x}, {y})\n'
                 f'sprite_frames = ExtResource("9_hound_frames")\ndrop_card_ids = Array[StringName]({drops})\n')
for k, (x, y) in enumerate(trees):
    nodes.append(f'[node name="Tree{k + 1}" parent="." instance=ExtResource("13_tree")]\nposition = Vector2({x}, {y})\n'
                 f'radius = {random.choice([16.0, 18.0, 20.0])}\ntint = Color(0.18, 0.36, 0.22, 1)\n')
nodes.append('''[node name="Player" parent="." instance=ExtResource("2_player")]
position = Vector2(470, 250)

[node name="HUD" parent="." instance=ExtResource("3_hud")]

[node name="Binder" parent="." instance=ExtResource("4_binder")]
''')

header = f'''[gd_scene load_steps={14 + len(subs)} format=3]

[ext_resource type="Script" path="res://scripts/world/zone.gd" id="1_zone"]
[ext_resource type="PackedScene" path="res://scenes/characters/player.tscn" id="2_player"]
[ext_resource type="PackedScene" path="res://scenes/ui/hud.tscn" id="3_hud"]
[ext_resource type="PackedScene" path="res://scenes/ui/binder.tscn" id="4_binder"]
[ext_resource type="PackedScene" path="res://scenes/systems/card_pickup.tscn" id="5_pick"]
[ext_resource type="PackedScene" path="res://scenes/characters/briar_hound.tscn" id="6_hound"]
[ext_resource type="PackedScene" path="res://scenes/systems/zone_exit.tscn" id="7_exit"]
[ext_resource type="PackedScene" path="res://scenes/systems/card_gate.tscn" id="8_gate"]
[ext_resource type="SpriteFrames" path="res://assets/sprites/monsters/briar_hound/briar_hound_frames.tres" id="9_hound_frames"]
[ext_resource type="Texture2D" path="res://assets/sprites/tiles/thornveil/lake_veyra_ground.png" id="10_ground"]
[ext_resource type="Texture2D" path="res://assets/sprites/tiles/thornveil/moss_bridge.png" id="11_bridge"]
[ext_resource type="PackedScene" path="res://scenes/world/props/elder_shrine.tscn" id="12_shrine"]
[ext_resource type="PackedScene" path="res://scenes/world/props/tree.tscn" id="13_tree"]

'''
open("scenes/world/lake_veyra.tscn", "w", newline="\n").write(header + "\n".join(subs.values()) + "\n" + "\n".join(nodes))
print(f"lake: {len(water_rects)} water rects, {len(trees)} trees")
