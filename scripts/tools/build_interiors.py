"""Build enterable interiors: one detailed PixelLab room image per interior,
plus collision for its walls and furniture, a resident, and the way back out.

Usage: python scripts/tools/build_interiors.py
Writes scenes/world/interiors/<id>.tscn. Room images live in
assets/sprites/tiles/kalmora/interiors/. Coordinates are room-image pixels
(top-left 0,0). Interiors are safe zones with warm fixed light (Zone.interior).
"""
import os

os.chdir(os.path.join(os.path.dirname(__file__), "..", ".."))

SHOP_STOCK = '[&"pickpockets_whisper", &"lockbox_seal", &"second_wind"]'

INTERIORS = {
    "kalmora_tavern": {
        "name": "The Salted Lantern",
        "image": "assets/sprites/tiles/kalmora/interiors/tavern_room.png",
        "size": (384, 288),
        "exit": (188, 282), "back_to": "from_tavern", "spawn": (188, 244),
        "blocks": [  # (x0, y0, x1, y1) walls and furniture
            (0, 0, 384, 104), (0, 0, 70, 288), (314, 0, 384, 288),       # back wall + counter line, sides
            (0, 224, 168, 288), (208, 224, 384, 288),                     # front wall around the door
            (72, 144, 110, 180), (72, 188, 110, 222),                     # left tables
            (166, 144, 218, 188),                                         # cellar hatch
            (276, 140, 314, 178), (248, 186, 314, 222),                   # right table, long table
        ],
        "npcs": [("otto", "Otto", "otto", (112, 122), [
            "Welcome to the Salted Lantern. Sit anywhere that isn't sticky.",
            "Racers, eh? Last one through here swore the prize was a crown. Laughed all the way to the north gate.",
            "The Hoarder's family? Old money. Shipping money. Don't ask them what they ship.",
        ], [])],
    },
    "kalmora_card_shop": {
        "name": "Sable's Card Emporium",
        "image": "assets/sprites/tiles/kalmora/interiors/card_shop_room.png",
        "size": (320, 256),
        "exit": (155, 262), "back_to": "from_cardshop", "spawn": (155, 226),
        "blocks": [
            (0, 0, 130, 106), (186, 0, 320, 106), (130, 0, 186, 90),     # back shelves, hallway
            (0, 0, 40, 256), (280, 0, 320, 256),                           # side shelves, plants
            (40, 204, 122, 256), (190, 240, 320, 256), (0, 240, 120, 256),  # front counter, front wall
        ],
        "npcs": [("sable", "Sable", "sable", (158, 118), [
            "Welcome, welcome. Spells, charms, a little luck in card form. Have a look.",
        ], SHOP_STOCK)],
    },
    "kalmora_nonna_house": {
        "name": "Nonna Vess's House",
        "image": "assets/sprites/tiles/kalmora/interiors/nonna_room.png",
        "size": (288, 224),
        "exit": (150, 232), "back_to": "from_nonnahouse", "spawn": (150, 200),
        "blocks": [
            (0, 0, 288, 104), (0, 0, 40, 224), (270, 0, 288, 224),       # back wall, kitchen side, right wall
            (40, 60, 116, 106), (180, 54, 220, 112), (218, 30, 274, 104),  # cabinets, rocking chair, shelves
            (240, 114, 282, 206),                                          # table
            (0, 216, 110, 224), (190, 216, 288, 224),                      # front wall around the door
        ],
        "npcs": [("nonna", "Nonna Vess", "nonna", (120, 140), [
            "Sit, sit. You look like you've been running. They all do, the racers.",
            "Every generation the King calls a race. Funny thing: the winners never talk about the prize after.",
            "My grandmother used to say the cards grow in the dark, under the dunes. Grandmothers say a lot of things.",
        ], [])],
    },
}


def build(zone_id, cfg):
    w, h = cfg["size"]
    ext = [
        ('Script', "res://scripts/world/zone.gd", "1_zone"),
        ('PackedScene', "res://scenes/characters/player.tscn", "2_player"),
        ('PackedScene', "res://scenes/ui/hud.tscn", "3_hud"),
        ('PackedScene', "res://scenes/ui/binder.tscn", "4_binder"),
        ('PackedScene', "res://scenes/ui/shop_panel.tscn", "5_shop"),
        ('PackedScene', "res://scenes/ui/dialogue_box.tscn", "6_dialogue"),
        ('PackedScene', "res://scenes/systems/zone_exit.tscn", "7_exit"),
        ('Script', "res://scripts/systems/safe_zone.gd", "8_safe"),
        ('PackedScene', "res://scenes/characters/npc.tscn", "9_npc"),
        ('Texture2D', "res://" + cfg["image"], "10_room"),
        ('Script', "res://scripts/systems/lamp_light.gd", "11_lamp"),
    ]
    subs = {}
    def shape(sw, sh):
        key = f"R{sw}x{sh}"
        subs[key] = f'[sub_resource type="RectangleShape2D" id="{key}"]\nsize = Vector2({sw}, {sh})\n'
        return key
    ex, ey = cfg["exit"]
    n = [f'''[node name="{zone_id}" type="Node2D"]
y_sort_enabled = true
script = ExtResource("1_zone")
display_name = "{cfg["name"]}"
interior = true

[node name="Ground" type="Sprite2D" parent="."]
z_index = -10
position = Vector2({w / 2}, {h / 2})
texture = ExtResource("10_room")

[node name="Glow" type="PointLight2D" parent="."]
position = Vector2({w / 2}, {h / 2})
texture_scale = 4.0
script = ExtResource("11_lamp")
always_on = true
max_energy = 0.35

[node name="Walls" type="StaticBody2D" parent="."]
''']
    for k, (x0, y0, x1, y1) in enumerate(cfg["blocks"] + [(-40, -40, w + 40, 0), (-40, 0, 0, h + 60), (w, 0, w + 40, h + 60),
                                                          (-40, h + 20, w + 40, h + 60)]):
        n.append(f'[node name="W{k}" type="CollisionShape2D" parent="Walls"]\nposition = Vector2({(x0 + x1) / 2}, {(y0 + y1) / 2})\n'
                 f'shape = SubResource("{shape(x1 - x0, y1 - y0)}")\n')
    n.append(f'''[node name="SafeZone" type="Area2D" parent="."]
collision_layer = 0
collision_mask = 6
monitorable = false
script = ExtResource("8_safe")

[node name="CollisionShape2D" type="CollisionShape2D" parent="SafeZone"]
position = Vector2({w / 2}, {h / 2})
shape = SubResource("{shape(w, h + 20)}")

[node name="Spawns" type="Node2D" parent="."]

[node name="door" type="Marker2D" parent="Spawns"]
position = Vector2{cfg["spawn"]}

[node name="Out" parent="." instance=ExtResource("7_exit")]
position = Vector2({ex}, {ey})
target_scene = "res://scenes/world/kalmora.tscn"
target_spawn = &"{cfg["back_to"]}"
''')
    for npc_id, display, sprite_id, (x, y), lines, stock in cfg["npcs"]:
        rid = f"n_{sprite_id}"
        ext.append(('SpriteFrames', f"res://assets/sprites/npcs/{sprite_id}/{sprite_id}_frames.tres", rid))
        quoted = ", ".join('"' + line.replace('"', '\\"') + '"' for line in lines)
        n.append(f'[node name="Npc_{npc_id}" parent="." instance=ExtResource("9_npc")]\nposition = Vector2({x}, {y})\n'
                 f'npc_id = &"{npc_id}"\ndisplay_name = "{display}"\nsprite_frames = ExtResource("{rid}")\n'
                 f'lines = PackedStringArray({quoted})\n' + (f'shop_stock = Array[StringName]({stock})\n' if stock else ""))
    sx, sy = cfg["spawn"]
    n.append(f'''[node name="Player" parent="." instance=ExtResource("2_player")]
position = Vector2({sx}, {sy})

[node name="HUD" parent="." instance=ExtResource("3_hud")]

[node name="Binder" parent="." instance=ExtResource("4_binder")]

[node name="ShopPanel" parent="." instance=ExtResource("5_shop")]

[node name="DialogueBox" parent="." instance=ExtResource("6_dialogue")]
''')
    head = f'[gd_scene load_steps={len(ext) + len(subs) + 1} format=3]\n\n' + "".join(
        f'[ext_resource type="{t}" path="{p}" id="{i}"]\n' for t, p, i in ext) + "\n"
    os.makedirs("scenes/world/interiors", exist_ok=True)
    open(f"scenes/world/interiors/{zone_id}.tscn", "w", encoding="utf-8", newline="\n").write(
        head + "\n".join(subs.values()) + "\n" + "\n".join(n))
    print(f"{zone_id}: {len(cfg['blocks'])} blocks")


if __name__ == "__main__":
    for zone_id, cfg in INTERIORS.items():
        build(zone_id, cfg)
