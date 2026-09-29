"""Builds Sorenda's base scene: the village layout (homes, doors, the green, the
Hollow's moss gate and cave mouth, exits, spawns, walls), before the forest dressing.

Sorenda is a forest village half hidden among the trees: six homes round a village
green, each a PixelLab building (front-facing, assets/sprites/tiles/sorenda/) that
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

from PIL import Image

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
    ("HouseLonghouse", "longhouse", (0, -250), 220, 0, "res://scenes/world/interiors/sorenda_longhouse.tscn", "from_houselonghouse"),
    ("HouseScribe", "scribe_house", (-340, -214), 132, 4, "res://scenes/world/interiors/sorenda_scribe_house.tscn", "from_housescribe"),
    ("HouseHerbalist", "herbalist_house", (350, -186), 176, 0, "res://scenes/world/interiors/sorenda_herbalist_house.tscn", "from_househerbalist"),
    ("HouseWoodcutter", "woodcutter_cottage", (-450, 24), 132, 6, "res://scenes/world/interiors/sorenda_woodcutter.tscn", "from_housewoodcutter"),
    ("HouseFamily", "round_cottage", (-240, 176), 128, -4, "res://scenes/world/interiors/sorenda_family_home.tscn", "from_housefamily"),
    ("HouseTree", "tree_house", (380, 120), 120, 0, "res://scenes/world/interiors/sorenda_tree_house.tscn", "from_housetree"),
]
# The Hollow: a pocket in the north-east corner, fenced off, the moss gate its only way in.
POCKET = (500, -600, 704, -430)          # x0, y0, x1, y1 (north and east are the map edge)
GATE = (600, -430)
MOUTH = (604, -520)                       # base of the cave-mouth sprite
TO_HOLLOW = (604, -532)
FROM_HOLLOW = (604, -498)
SPAWNS = {"town": (0, -40), "from_thornveil": (0, 236), "from_hollow": FROM_HOLLOW}
EXIT_SOUTH = (0, 282)
RIVALS = {"runner": (-120, 70), "raider": (200, 40), "hoarder": (-40, -120)}
WELL = (96, -20)
MERCHANT = (-110, 40)
# A traveller's cache in the south-west woods, for anyone who looks off the paths.
CHESTS = [("old_stump", (-620, 180), 25, "bread", 2)]


def bottom_offset(path):
    im = Image.open(path)
    return im.height / 2 - im.getbbox()[3]


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
                 f'texture_scale = 0.9\nscript = ExtResource("20_lamp")\nmax_energy = 0.9\n')
    # The tree house's sprite stops at the trunk: a whole oak stands behind it, so the
    # tree carries on up into a crown.
    tx, ty = next(pos for node, _, pos, *_ in HOMES if node == "HouseTree")
    ext.append(('PackedScene', "res://scenes/world/props/forest_oak.tscn", "23_oak"))
    n.append(f'[node name="TreeHouseCrown" parent="." instance=ExtResource("23_oak")]\nposition = Vector2({tx}, {ty - 160})\n'
             f'scale = Vector2(2, 2)\n')
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
