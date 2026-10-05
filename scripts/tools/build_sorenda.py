"""Builds Sorenda's base scene: the village layout (homes, doors, the green, the
Hollow's moss gate and cave mouth, exits, spawns, walls), before the forest dressing.

Sorenda is a forest village half hidden among the trees: six homes round a village
green and the Copper Kettle inn by the south road, each a PixelLab building (front-facing, assets/sprites/tiles/sorenda/) that
you can walk into (interiors: build_interiors.py), with a door lamp. North-east, past
the moss gate (a card gate), the Hollow's cave mouth leads down into the cave
(scenes/world/sorenda_hollow.tscn, build_hollow.py).

Pipeline (run in order, the later steps dress this scene):
  python scripts/tools/build_sorenda.py
  python scripts/tools/build_forest.py sorenda     (ground, treeline, groves, residents, readables)
Edit the layout here and the residents/props in build_forest.py LIFE, not the editor.
"""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

os.chdir(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, "scripts/tools")

SCENE = "scenes/world/sorenda.tscn"
ART = "assets/sprites/tiles/sorenda/"
# Must match build_ground.ZONES["sorenda"]["bounds"].
BOUNDS = (-704, -640, 704, 288)
GROUND = "assets/sprites/tiles/thornveil/sorenda_ground.png"

# Homes: (node, sprite, base position (the foot of the front wall), footprint width,
# door x offset, interior scene, spawn name for coming back out).
HOMES = [
    ("HouseLonghouse", "longhouse", (0, -330), 220, 0, "res://scenes/world/interiors/sorenda_longhouse.tscn", "from_houselonghouse"),
    ("HouseScribe", "scribe_house", (-310, -300), 132, 4, "res://scenes/world/interiors/sorenda_scribe_house.tscn", "from_housescribe"),
    ("HouseHerbalist", "herbalist_house", (450, -210), 176, 0, "res://scenes/world/interiors/sorenda_herbalist_house.tscn", "from_househerbalist"),
    ("HouseWoodcutter", "woodcutter_cottage", (-500, 10), 132, 6, "res://scenes/world/interiors/sorenda_woodcutter.tscn", "from_housewoodcutter"),
    ("HouseFamily", "round_cottage", (-420, 190), 128, -4, "res://scenes/world/interiors/sorenda_family_home.tscn", "from_housefamily"),
    ("HouseTree", "tree_house", (240, -10), 150, 0, "res://scenes/world/interiors/sorenda_tree_house.tscn", "from_housetree"),
    # The Copper Kettle, Mate's inn: the first roof you reach coming up the forest road
    # (set back from the south edge, beside the fire glade).
    ("HouseInn", "kettle_inn", (262, 196), 180, 0, "res://scenes/world/interiors/sorenda_inn.tscn", "from_houseinn"),
]
# The Hollow: a pocket in the north-east corner, fenced off, the moss gate its only way in.
POCKET = (500, -600, 704, -430)          # x0, y0, x1, y1 (north and east are the map edge)
GATE = (600, -430)
MOUTH = (604, -520)                       # base of the cave-mouth sprite
TO_HOLLOW = (604, -532)
FROM_HOLLOW = (604, -498)
SPAWNS = {"town": (0, 120), "from_thornveil": (0, 236), "from_hollow": FROM_HOLLOW}
EXIT_SOUTH = (0, 282)
RIVALS = {"runner": (-60, 110), "raider": (120, 130), "hoarder": (10, -200)}
WELL = (-80, 170)
MERCHANT = (-130, 110)
# Lanterns on posts along the paths (each a real light after dark), the campfire on
# the green (animated, always burning), and benches round it.
LANTERNS = [(-170, 100), (-340, 60), (-70, -40), (70, -200), (150, 196), (390, -40), (500, -340), (-180, -270), (100, 230), (-330, 170)]
CAMPFIRE = (40, 150)
BENCHES = [(-20, 196), (100, 196)]
LANTERN_PNG = "assets/sprites/tiles/thornveil/props/trail_lantern.png"
CAMPFIRE_STRIP = "assets/sprites/tiles/thornveil/props/campfire_anim.png"
BENCH_PNG = "assets/sprites/tiles/kalmora/props/bench_wood.png"
NIGHT = ART + "night/"
# A traveller's cache in the south-west woods, for anyone who looks off the paths.
CHESTS = [("old_stump", (-620, 180), 25, "bread", 2)]


def bottom_offset(path):
    im = Image.open(path)
    return im.height / 2 - im.getbbox()[3]


def window_glow(sprite):
    """The lit-window overlay for a home: the warm window panes and lanterns already
    painted on the sprite (bright cream-yellow, in small compact blobs, so thatch
    highlights don't count), brightened; WindowGlow fades it in at night."""
    a = np.array(Image.open(ART + sprite + ".png").convert("RGBA")).astype(int)
    r, g, b, al = (a[..., i] for i in range(4))
    lit = (al > 200) & (r > 185) & (g > 145) & (b < 170) & (r - b > 45) & (r - g < 75)
    lab, _ = ndimage.label(ndimage.binary_dilation(lit, iterations=1))
    keep = np.zeros_like(lit)
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        blob = (lab[sl] == i) & lit[sl]
        if 3 <= blob.sum() <= 220 and h <= 26 and w <= 26 and blob.sum() >= 0.22 * h * w:
            keep[sl] |= blob
    out = np.zeros_like(a)
    out[keep] = (255, 214, 130, 240)
    os.makedirs(NIGHT, exist_ok=True)
    path = NIGHT + sprite + "_windows.png"
    Image.fromarray(out.astype(np.uint8)).save(path)
    return path


def depth(path):
    b = Image.open(path).getbbox()
    return int(min(90, max(30, (b[3] - b[1]) * 0.42)))


def main():
    x0, y0, x1, y1 = BOUNDS
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
        ('PackedScene', "res://scenes/systems/zone_exit.tscn", "8_exit"),
        ('PackedScene', "res://scenes/systems/merchant.tscn", "9_merchant"),
        ('Script', "res://scripts/systems/safe_zone.gd", "10_safe"),
        ('PackedScene', "res://scenes/systems/card_gate.tscn", "11_gate"),
        ('PackedScene', "res://scenes/world/props/sorenda_well.tscn", "14_well"),
        ('Texture2D', "res://" + GROUND, "90_ground"),
        ('Texture2D', "res://assets/sprites/tiles/kalmora/market_stall.png", "83_stall"),
        ('Script', "res://scripts/systems/lamp_light.gd", "20_lamp"),
        ('Texture2D', "res://assets/sprites/tiles/kalmora/props/fence.png", "21_fence"),
        ('Script', "res://scripts/systems/chest.gd", "70_chest"),
        ('Texture2D', "res://assets/sprites/tiles/thornveil/props/chest.png", "70_chest_shut"),
        ('Texture2D', "res://assets/sprites/tiles/thornveil/props/chest_open.png", "70_chest_open"),
        ('PackedScene', "res://scenes/ui/dialogue_box.tscn", "22_dialogue"),
        ('Script', "res://scripts/world/window_glow.gd", "24_windows"),
    ]
    tex = {}

    def texture(path):
        if path not in tex:
            tex[path] = f"t{len(tex)}_{os.path.basename(path)[:-4]}"
            ext.append(('Texture2D', "res://" + path, tex[path]))
        return tex[path]

    n = [f'''[node name="Sorenda" type="Node2D"]
y_sort_enabled = true
script = ExtResource("1_zone")
display_name = "Sorenda, Village of the Old Roads"

[node name="GroundTiles" type="Sprite2D" parent="."]
z_index = -10
position = Vector2({(x0 + x1) / 2}, {(y0 + y1) / 2})
texture = ExtResource("90_ground")
''']
    # The map's edges (the treeline stands along them), open at the south road.
    walls = [(x0 - 40, y0 - 40, x1 + 40, y0), (x0 - 40, y0, x0, y1), (x1, y0, x1 + 40, y1),
             (x0 - 40, y1, EXIT_SOUTH[0] - 40, y1 + 40), (EXIT_SOUTH[0] + 40, y1, x1 + 40, y1 + 40)]
    # The Hollow's pocket: fenced along its west and south sides, the gate in the south fence.
    px0, py0, px1, py1 = POCKET
    walls += [(px0 - 5, py0, px0 + 5, py1), (px0, py1 - 5, GATE[0] - 28, py1 + 5), (GATE[0] + 28, py1 - 5, px1, py1 + 5)]
    n.append('[node name="Walls" type="StaticBody2D" parent="."]\n')
    for k, (a, b, c, d) in enumerate(walls):
        n.append(f'[node name="W{k}" type="CollisionShape2D" parent="Walls"]\nposition = Vector2({(a + c) / 2}, {(b + d) / 2})\n'
                 f'shape = SubResource("{shape(c - a, d - b)}")\n')
    # The fence you see along those pocket walls.
    fences = [(px0, y) for y in range(py0 + 40, py1 + 1, 16)] + \
             [(x, py1) for x in range(px0 + 8, px1, 16) if abs(x - GATE[0]) > 30]
    for k, (x, y) in enumerate(fences):
        n.append(f'[node name="PocketFence{k}" type="Sprite2D" parent="."]\nposition = Vector2({x}, {y + 4})\n'
                 f'offset = Vector2(0, -8)\ntexture = ExtResource("21_fence")\n')

    n.append(f'''[node name="SafeZone" type="Area2D" parent="."]
position = Vector2(-20, -40)
collision_layer = 0
collision_mask = 6
monitorable = false
script = ExtResource("10_safe")

[node name="CollisionShape2D" type="CollisionShape2D" parent="SafeZone"]
shape = SubResource("{shape(1120, 620)}")

[node name="Spawns" type="Node2D" parent="."]
''')
    spawns = dict(SPAWNS)
    for node, sprite, (x, y), fw, dx, interior, back in HOMES:
        spawns[back] = (x + dx, y + 26)
    for name, (x, y) in spawns.items():
        n.append(f'[node name="{name}" type="Marker2D" parent="Spawns"]\nposition = Vector2({x}, {y})\n')
    n.append('[node name="RivalSpots" type="Node2D" parent="."]\n')
    for name, (x, y) in RIVALS.items():
        n.append(f'[node name="{name}" type="Marker2D" parent="RivalSpots"]\nposition = Vector2({x}, {y})\n')

    n.append(f'''[node name="ToThornveil" parent="." instance=ExtResource("8_exit")]
position = Vector2({EXIT_SOUTH[0]}, {EXIT_SOUTH[1]})
target_scene = "res://scenes/world/thornveil.tscn"
target_spawn = &"from_sorenda"

[node name="HollowGate" parent="." instance=ExtResource("11_gate")]
position = Vector2({GATE[0]}, {GATE[1]})
gate_id = &"sorenda_hollow"

[node name="CaveMouth" type="StaticBody2D" parent="."]
position = Vector2({MOUTH[0]}, {MOUTH[1]})

[node name="Sprite" type="Sprite2D" parent="CaveMouth"]
position = Vector2(0, {bottom_offset(ART + "cave_mouth.png")})
texture = ExtResource("{texture(ART + "cave_mouth.png")}")

[node name="RootWest" type="CollisionShape2D" parent="CaveMouth"]
position = Vector2(-52, -14)
shape = SubResource("{shape(44, 28)}")

[node name="RootEast" type="CollisionShape2D" parent="CaveMouth"]
position = Vector2(52, -14)
shape = SubResource("{shape(44, 28)}")

[node name="ToHollow" parent="." instance=ExtResource("8_exit")]
position = Vector2({TO_HOLLOW[0]}, {TO_HOLLOW[1]})
target_scene = "res://scenes/world/sorenda_hollow.tscn"
target_spawn = &"from_sorenda"

[node name="MouthGlow" type="PointLight2D" parent="."]
position = Vector2({MOUTH[0]}, {MOUTH[1] - 30})
texture_scale = 1.2
script = ExtResource("20_lamp")
always_on = true
max_energy = 0.5
tint = Color(0.45, 0.95, 0.85, 1)

[node name="Merchant" parent="." instance=ExtResource("9_merchant")]
stall_texture = ExtResource("83_stall")
position = Vector2({MERCHANT[0]}, {MERCHANT[1]})

[node name="Well" parent="." instance=ExtResource("14_well")]
position = Vector2({WELL[0]}, {WELL[1]})
''')
    for node, sprite, (x, y), fw, dx, interior, back in HOMES:
        path = ART + sprite + ".png"
        fd = depth(path)
        n.append(f'[node name="{node}" type="StaticBody2D" parent="."]\nposition = Vector2({x}, {y})\n\n'
                 f'[node name="Sprite" type="Sprite2D" parent="{node}"]\nposition = Vector2(0, {bottom_offset(path)})\n'
                 f'texture = ExtResource("{texture(path)}")\n\n'
                 f'[node name="Base" type="CollisionShape2D" parent="{node}"]\nposition = Vector2(0, {-fd / 2})\n'
                 f'shape = SubResource("{shape(fw, fd)}")\n\n'
                 f'[node name="{node}Door" parent="." instance=ExtResource("8_exit")]\nposition = Vector2({x + dx}, {y + 4})\n'
                 f'target_scene = "{interior}"\ntarget_spawn = &"door"\nneeds_interact = true\n\n'
                 f'[node name="{node}Lamp" type="PointLight2D" parent="."]\nposition = Vector2({x + dx}, {y - 30})\n'
                 f'texture_scale = 0.9\nscript = ExtResource("20_lamp")\nmax_energy = 0.9\n\n'
                 f'[node name="Windows" type="Sprite2D" parent="{node}"]\nposition = Vector2(0, {bottom_offset(path)})\n'
                 f'texture = ExtResource("{texture(window_glow(sprite))}")\nscript = ExtResource("24_windows")\n'
                 f'lights_out = {1.0 + (len(node) % 5) * 0.6:.1f}\n')
    # Lanterns along the paths, each with its light.
    for k, (x, y) in enumerate(LANTERNS):
        n.append(f'[node name="PathLantern{k}" type="StaticBody2D" parent="."]\nposition = Vector2({x}, {y})\n\n'
                 f'[node name="Sprite" type="Sprite2D" parent="PathLantern{k}"]\nposition = Vector2(0, {bottom_offset(LANTERN_PNG)})\n'
                 f'texture = ExtResource("{texture(LANTERN_PNG)}")\n\n'
                 f'[node name="Base" type="CollisionShape2D" parent="PathLantern{k}"]\nposition = Vector2(0, -4)\n'
                 f'shape = SubResource("{shape(10, 8)}")\n\n'
                 f'[node name="PathLight{k}" type="PointLight2D" parent="."]\nposition = Vector2({x + 6}, {y - 44})\n'
                 f'texture_scale = 1.2\nscript = ExtResource("20_lamp")\n')
    # The campfire on the green: always burning, lighting the benches round it.
    frames = Image.open(CAMPFIRE_STRIP)
    fw, fh = frames.width // 8, frames.height
    strip = texture(CAMPFIRE_STRIP)
    refs = []
    for f in range(8):
        subs[f"fire_{f}"] = (f'[sub_resource type="AtlasTexture" id="fire_{f}"]\natlas = ExtResource("{strip}")\n'
                             f'region = Rect2({f * fw}, 0, {fw}, {fh})\n')
        refs.append(f'{{\n"duration": 1.0,\n"texture": SubResource("fire_{f}")\n}}')
    subs["fire_frames"] = (f'[sub_resource type="SpriteFrames" id="fire_frames"]\nanimations = [{{\n"frames": [{", ".join(refs)}],\n'
                           f'"loop": true,\n"name": &"default",\n"speed": 9\n}}]\n')
    cx, cy = CAMPFIRE
    n.append(f'[node name="Campfire" type="StaticBody2D" parent="."]\nposition = Vector2({cx}, {cy})\n\n'
             f'[node name="Fire" type="AnimatedSprite2D" parent="Campfire"]\nscale = Vector2(2, 2)\nposition = Vector2(0, -{fh - 4})\n'
             f'sprite_frames = SubResource("fire_frames")\nautoplay = "default"\n\n'
             f'[node name="Base" type="CollisionShape2D" parent="Campfire"]\nposition = Vector2(0, -16)\n'
             f'shape = SubResource("{shape(64, 30)}")\n\n'
             f'[node name="CampfireLight" type="PointLight2D" parent="."]\nposition = Vector2({cx}, {cy - 30})\n'
             f'texture_scale = 2.2\nscript = ExtResource("20_lamp")\nalways_on = true\nmax_energy = 0.9\nflicker = 0.18\n')
    for k, (x, y) in enumerate(BENCHES):
        n.append(f'[node name="Bench{k}" type="StaticBody2D" parent="."]\nposition = Vector2({x}, {y})\n\n'
                 f'[node name="Sprite" type="Sprite2D" parent="Bench{k}"]\nposition = Vector2(0, {bottom_offset(BENCH_PNG)})\n'
                 f'texture = ExtResource("{texture(BENCH_PNG)}")\n\n'
                 f'[node name="Base" type="CollisionShape2D" parent="Bench{k}"]\nposition = Vector2(0, -5)\n'
                 f'shape = SubResource("{shape(36, 10)}")\n')
    for cid, (x, y), gold, item, count in CHESTS:
        n.append(f'[node name="Chest_{cid}" type="StaticBody2D" parent="."]\nposition = Vector2({x}, {y})\n'
                 f'script = ExtResource("70_chest")\nchest_id = &"sorenda_{cid}"\ncard_id = &""\ngold = {gold}\n'
                 f'item_id = &"{item}"\nitem_count = {count}\n'
                 f'closed_texture = ExtResource("70_chest_shut")\nopen_texture = ExtResource("70_chest_open")\n\n'
                 f'[node name="Base" type="CollisionShape2D" parent="Chest_{cid}"]\nposition = Vector2(0, -5)\n'
                 f'shape = SubResource("{shape(30, 10)}")\n')

    n.append(f'''[node name="Player" parent="." instance=ExtResource("2_player")]
position = Vector2({SPAWNS["from_thornveil"][0]}, {SPAWNS["from_thornveil"][1]})

[node name="HUD" parent="." instance=ExtResource("3_hud")]

[node name="Binder" parent="." instance=ExtResource("4_binder")]

[node name="ShopPanel" parent="." instance=ExtResource("5_shop")]

[node name="DialogueBox" parent="." instance=ExtResource("22_dialogue")]
''')
    head = f'[gd_scene load_steps={len(ext) + len(subs) + 1} format=3]\n\n'
    head += "".join(f'[ext_resource type="{t}" path="{p}" id="{i}"]\n' for t, p, i in ext) + "\n"
    head += "\n".join(subs.values()) + "\n"
    open(SCENE, "w", encoding="utf-8", newline="\n").write(head + "\n".join(n))
    print(f"sorenda base: {len(HOMES)} homes, {len(walls)} walls")


if __name__ == "__main__":
    main()
