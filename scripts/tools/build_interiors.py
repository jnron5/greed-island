"""Build enterable interiors: one detailed PixelLab room image per interior,
plus collision for its walls and furniture, a resident, and the way back out.

Usage: python scripts/tools/build_interiors.py
Writes scenes/world/interiors/<id>.tscn. Room images live in
assets/sprites/tiles/kalmora/interiors/. Coordinates are room-image pixels
(top-left 0,0). Interiors are safe zones with warm fixed light (Zone.interior).
The room art is drawn at ROOM_SCALE so furniture and doors match the player's size;
everything below stays in the image's own pixels and is scaled on the way out.
"""
import os

os.chdir(os.path.join(os.path.dirname(__file__), "..", ".."))

ROOM_SCALE = 1

# Greta's shelves: satchel items that heal (data/items/).
PROVISIONS = '[&"smoked_fish", &"bread", &"healers_tonic", &"sea_salt_elixir"]'
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
    # ---- every other house in Kalmora. Each has a detail that ties back to the story:
    # the island's comfort is paid for somewhere out in the dunes, and the town half knows.
    "kalmora_red_house": {
        "name": "The Tamsin Home",
        "image": "assets/sprites/tiles/kalmora/interiors/fisher_room.png",
        "size": (320, 256),
        "exit": (160, 250), "back_to": "from_redhouse", "spawn": (160, 206),
        "blocks": [
            (0, 0, 320, 112), (0, 0, 36, 256), (286, 0, 320, 256),       # back wall, sides
            (36, 60, 92, 190),                                            # bunk bed
            (110, 96, 218, 182),                                          # table and benches
            (242, 90, 280, 138), (238, 194, 264, 206),                    # stove, toy boat
            (0, 218, 132, 256), (188, 218, 320, 256),                     # front wall around the door
        ],
        "npcs": [("wen", "Wen", "wen", (250, 160), [
            "Papa went to work in Duskara. He sends cards now instead of letters. Mama says that means good pay.",
            "I'm building a boat. When it's done I'm going to sail round to the dunes and bring him home.",
            "You're racing? If you get to Duskara, will you look for a fisher called Tamsin? He has a crooked ear.",
        ], [])],
        "readables": [
            ("A letter on the table", (165, 186), [
                "A letter in careful handwriting, never finished:",
                "'Dear Tam, the harbormaster says your cards arrived again. Forty commons. Wen asks when you're coming home. So do I. The last cards smelled of smoke and had sand in the",
                "The letter stops there.",
            ]),
        ],
    },
    "kalmora_general_store": {
        "name": "Greta's Provisions",
        "image": "assets/sprites/tiles/kalmora/interiors/store_room.png",
        "size": (320, 256),
        "exit": (161, 252), "back_to": "from_generalstore", "spawn": (161, 214),
        "blocks": [
            (0, 0, 320, 100), (0, 0, 40, 256), (290, 0, 320, 256),       # shelves, side walls
            (38, 104, 240, 170), (38, 140, 122, 180), (30, 178, 92, 236),  # counter, flour sacks, barrels
            (0, 236, 142, 256), (180, 236, 320, 256),                     # front wall
        ],
        "npcs": [("greta", "Greta", "greta", (262, 140), [
            "Greta's Provisions! Bread, smoked fish, tonics for the road. Racers come in limping and go out running.",
            "The big house up the hill buys more lamps than the lighthouse. Oil, wicks, the lot. Who needs that many lamps?",
            "Every autumn a whole cart of children's boots goes out on the southern barge. Charity, they say. Funny sort of charity.",
        ], PROVISIONS)],
        "readables": [
            ("Greta's ledger", (205, 176), [
                "A fat ledger open on the counter.",
                "'Calloway house: 20 sacks flour, 6 miner's lamps, 3 coils rope. Charged to the Duskara account, as usual.'",
                "In the margin: 'Nobody has paid the Duskara account in person in nine years. It always clears.'",
            ]),
        ],
    },
    "kalmora_forge": {
        "name": "Brannoc's Forge",
        "image": "assets/sprites/tiles/kalmora/interiors/forge_room.png",
        "size": (320, 256),
        "exit": (160, 252), "back_to": "from_blacksmith", "spawn": (160, 222),
        "blocks": [
            (0, 0, 320, 122), (128, 120, 192, 142), (195, 95, 240, 140),  # back wall, hearth, bellows
            (0, 0, 30, 256), (270, 0, 320, 256), (36, 128, 70, 176),      # side walls, workbench
            (142, 156, 182, 192), (208, 160, 258, 222),                   # anvil on its stump, quench barrel
            (30, 196, 112, 230), (246, 205, 300, 235),                    # coal heaps
            (0, 234, 122, 256), (198, 234, 320, 256),                     # front wall
        ],
        "npcs": [("brannoc", "Brannoc", "brannoc", (96, 160), [
            "Mind the anvil. Mind the coals. Mind your fingers, mostly.",
            "Forty pickaxe heads a month, every month, for a hole out east. Must be a very big hole.",
            "They asked me for shackles. Small ones. I told them I don't make those. They found someone who does.",
        ], [])],
        "readables": [
            ("An order nailed to the bench", (80, 184), [
                "'Forty pick heads. Twelve lamp brackets. Deliver to the red-sun crates at the warehouse.'",
                "'Paid in commons, as agreed. D.M.'",
            ]),
        ],
    },
    "kalmora_harbor_office": {
        "name": "Harbormaster's Office",
        "image": "assets/sprites/tiles/kalmora/interiors/harbor_office_room.png",
        "size": (320, 256),
        "exit": (161, 252), "back_to": "from_harbormaster", "spawn": (161, 216),
        "blocks": [
            (0, 0, 320, 140), (0, 0, 24, 256), (298, 0, 320, 256),       # back wall and cabinets, sides
            (22, 140, 60, 222),                                           # telescope
            (108, 118, 218, 176),                                         # desk
            (210, 193, 254, 225), (258, 55, 300, 225),                    # chest, bookcase
            (0, 228, 140, 256), (182, 228, 320, 256),                     # front wall around the door
        ],
        "npcs": [],
        "readables": [
            ("Cargo manifests", (96, 176), [
                "A stack of manifests, all properly stamped.",
                "'Brig Serin. Duskara Mining Co. Machine parts, three tons. Inspected.'",
                "Underneath, in pencil, in a different hand: 'Parts don't cough.'",
            ]),
            ("The sea chart", (234, 150), [
                "A chart of Virelia Isle. Someone has pencilled a line from the Duskara landing to Kalmora's quay, then scratched it out so hard the paper tore.",
            ]),
        ],
    },
    "kalmora_warehouse": {
        "name": "Harbor Warehouse",
        "image": "assets/sprites/tiles/kalmora/interiors/warehouse_room.png",
        "size": (320, 256),
        "exit": (158, 252), "back_to": "from_warehouse", "spawn": (158, 214),
        "blocks": [
            (0, 0, 320, 70), (0, 0, 28, 256), (298, 0, 320, 256),        # back wall, sides
            (28, 40, 80, 232), (98, 48, 146, 110),                        # crate stacks, barrels
            (180, 64, 222, 108), (244, 56, 300, 112),                     # grain pallet, red-sun crates
            (104, 125, 146, 166), (150, 104, 220, 180),                   # sacks, crates and barrels
            (246, 150, 298, 228), (226, 196, 246, 228), (66, 196, 118, 230),  # stacks by the door, rope coils
            (0, 226, 134, 256), (182, 226, 320, 256),                     # front wall
        ],
        "npcs": [],
        "readables": [
            ("Crates with a red sun", (268, 124), [
                "Crates stamped with a red sun and nothing else. No harbor stamp, no manifest tag.",
                "Through the slats: pick handles, lamp glass, and a coil of very small chains.",
            ]),
        ],
    },
    "kalmora_blue_cottage": {
        "name": "Old Fenn's Cottage",
        "image": "assets/sprites/tiles/kalmora/interiors/sailor_room.png",
        "size": (288, 224),
        "exit": (144, 220), "back_to": "from_bluecottage", "spawn": (144, 188),
        "blocks": [
            (0, 0, 288, 110), (0, 0, 30, 224), (258, 0, 288, 224),       # back wall, sides
            (44, 78, 92, 140), (32, 138, 92, 196), (194, 102, 248, 156),  # fireplace, armchair, sea chest
            (0, 200, 120, 224), (168, 200, 288, 224),                     # front wall
        ],
        "npcs": [],
        "readables": [
            ("A ship in a bottle", (180, 116), [
                "The Gull's Mercy, rigged in thread. A note is tied round the cork:",
                "'For my old crew. We carried what we were told and never opened the hold. May the sea forgive the rest.'",
            ]),
            ("Fenn's logbook", (222, 164), [
                "'Fourth run south to the Duskara landing this season. Out: boots, forty pairs, small. Back: sealed crates, heavy, singing a little when the sea was calm.'",
                "'Asked the foreman about the singing. Was told it was the wind in the slats.'",
            ]),
        ],
    },
    "kalmora_calloway_house": {
        "name": "Calloway House",
        "image": "assets/sprites/tiles/kalmora/interiors/manor_room.png",
        "size": (320, 256),
        "exit": (160, 250), "back_to": "from_hillhouse", "spawn": (160, 214),
        "blocks": [
            (0, 0, 320, 112), (68, 84, 138, 150), (232, 110, 290, 190),  # back wall, desk, sofa
            (268, 170, 300, 225), (24, 150, 78, 225),                     # side table, strongbox
            (0, 0, 52, 256), (296, 0, 320, 256),                          # side walls
            (0, 232, 128, 256), (192, 232, 320, 256),                     # front wall
        ],
        "npcs": [("calloway", "Lady Calloway", "calloway", (190, 140), [
            "Another racer. Do wipe your feet. My grandson is racing too, you know. Calloways always race.",
            "The Duskara trade built this island, dear. Everyone eats from that table. Some of us simply set it.",
            "The King's race is older than any of us. Old things have their reasons. I wouldn't go digging for them.",
        ], [])],
        "readables": [
            ("The family portrait", (160, 118), [
                "Four generations of Calloways, painted in gold leaf. Behind them, very small, a window shows red dunes.",
            ]),
            ("A letter on the desk", (104, 158), [
                "'Mother. The Duskara consignment is short again; the foreman blames the heat. Tell him the King's count must be met. Hire younger if he must. - H.'",
            ]),
            ("An iron strongbox", (86, 190), [
                "Locked tight. A brass plate on the lid: 'CALLOWAY & DUNE, SHIPPING. Est. the year of the Third Race.'",
            ]),
        ],
    },
    "kalmora_teal_house": {
        "name": "Ilse's Map House",
        "image": "assets/sprites/tiles/kalmora/interiors/mapmaker_room.png",
        "size": (288, 224),
        "exit": (144, 222), "back_to": "from_tealhouse", "spawn": (144, 186),
        "blocks": [
            (0, 0, 288, 86), (60, 66, 92, 108), (208, 68, 238, 94),       # back wall, globe, scrolls
            (84, 88, 196, 156),                                           # drafting table
            (0, 0, 48, 200), (236, 0, 288, 200),                          # bookshelves on both sides
            (0, 196, 122, 224), (166, 196, 288, 224),                     # front wall
        ],
        "npcs": [("ilse", "Ilse", "ilse", (214, 130), [
            "Ilse Marrow, cartographer. Mind the ink, it never comes out.",
            "Every map of Virelia has a blank spot in the dunes east of Duskara. Every one. Mine too. I was paid to leave it blank.",
            "Heading north? Take the forest road. The coast path is prettier, but the Raider likes it.",
        ], [])],
        "readables": [
            ("Ilse's working chart", (140, 162), [
                "The whole isle in fine ink. The Siroth Dunes are drawn dune by dune, except one patch east of Duskara, left blank.",
                "Across the blank, in red: 'Not to be surveyed. By order of the Crown.'",
            ]),
        ],
    },
    "kalmora_mill": {
        "name": "The Windmill",
        "image": "assets/sprites/tiles/kalmora/interiors/mill_room.png",
        "size": (288, 224),
        "exit": (144, 222), "back_to": "from_windmill", "spawn": (144, 202),
        "blocks": [
            (0, 0, 288, 92), (36, 50, 70, 146), (104, 96, 182, 158),      # back wall, ladder, millstone base
            (18, 110, 58, 156), (26, 166, 92, 205), (76, 186, 106, 205),   # flour sacks
            (206, 98, 268, 138), (204, 154, 264, 196), (176, 184, 206, 208),  # workbench, table, barrel
            (0, 0, 20, 224), (270, 0, 288, 224),                          # walls
            (0, 212, 130, 224), (160, 212, 288, 224),                     # front wall
        ],
        "npcs": [],
        "readables": [
            ("A note on the mill post", (140, 180), [
                "'Gone to Verdana for the harvest. Grind the Calloway order first. They pay double and never ask the price. - Miller Oake'",
            ]),
        ],
    },
}


def scaled(cfg, k=ROOM_SCALE):
    """The config in zone coordinates: every position and rect multiplied by k."""
    pt = lambda p: (p[0] * k, p[1] * k)
    out = dict(cfg)
    out["size"] = pt(cfg["size"])
    out["exit"], out["spawn"] = pt(cfg["exit"]), pt(cfg["spawn"])
    out["blocks"] = [tuple(v * k for v in b) for b in cfg["blocks"]]
    out["npcs"] = [(a, b, c, pt(pos), lines, stock) for a, b, c, pos, lines, stock in cfg["npcs"]]
    out["readables"] = [(t, pt(pos), lines) for t, pos, lines in cfg.get("readables", [])]
    return out


def build(zone_id, cfg):
    cfg = scaled(cfg)
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
        ('Script', "res://scripts/systems/readable.gd", "12_read"),
    ]
    subs = {}
    def shape(sw, sh):
        key = f"R{sw:g}x{sh:g}".replace(".", "_")
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
scale = Vector2({ROOM_SCALE}, {ROOM_SCALE})
texture = ExtResource("10_room")

[node name="Glow" type="PointLight2D" parent="."]
position = Vector2({w / 2}, {h / 2})
texture_scale = {4.0 * ROOM_SCALE}
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
exit_hint = true
''')
    for npc_id, display, sprite_id, (x, y), lines, stock in cfg["npcs"]:
        rid = f"n_{sprite_id}"
        ext.append(('SpriteFrames', f"res://assets/sprites/npcs/{sprite_id}/{sprite_id}_frames.tres", rid))
        quoted = ", ".join('"' + line.replace('"', '\\"') + '"' for line in lines)
        n.append(f'[node name="Npc_{npc_id}" parent="." instance=ExtResource("9_npc")]\nposition = Vector2({x}, {y})\n'
                 f'npc_id = &"{npc_id}"\ndisplay_name = "{display}"\nsprite_frames = ExtResource("{rid}")\n'
                 f'lines = PackedStringArray({quoted})\n' + (f'shop_stock = Array[StringName]({stock})\n' if stock else "")
                 + ('shop_buys_cards = false\nshop_title = "Greta\'s Provisions"\n' if stock == PROVISIONS else ""))
    for k, (title, (x, y), lines) in enumerate(cfg.get("readables", [])):
        quoted = ", ".join('"' + line.replace('"', '\\"') + '"' for line in lines)
        n.append(f'[node name="Read{k + 1}" type="Node2D" parent="."]\nposition = Vector2({x}, {y})\nscript = ExtResource("12_read")\n'
                 f'title = "{title}"\nlines = PackedStringArray({quoted})\n')
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
