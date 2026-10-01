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
SHOP_STOCK = '[&"pickpockets_whisper", &"lockbox_seal", &"second_wind", &"hollowpoint_charm", &"tidewalker_anklet"]'

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
            "Racers, eh? Last one through here swore the prize would make him richer than the King. Laughed all the way to the north gate.",
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
    # ---- Sorenda's homes (the village: build_sorenda.py). Same rules: 1x, doorway gap
    # at the bottom middle, furniture blocks only its footprint.
    "sorenda_longhouse": {
        "town": "res://scenes/world/sorenda.tscn",
        "name": "The Elder's Longhouse",
        "image": "assets/sprites/tiles/sorenda/interiors/longhouse_room.png",
        "size": (352, 256),
        "exit": (173, 254), "back_to": "from_houselonghouse", "spawn": (173, 206),
        "blocks": [
            (0, 0, 352, 78), (198, 0, 290, 92), (26, 60, 56, 100),         # back wall, carved post and pot shelves, pots
            (26, 100, 44, 214), (62, 84, 154, 194),                         # bench on the west wall, the long table and benches
            (196, 124, 262, 180), (286, 70, 326, 214),                      # fire pit, sleeping furs
            (0, 0, 24, 256), (326, 0, 352, 256),                            # walls
            (0, 214, 150, 256), (196, 214, 352, 256),                       # front wall
        ],
        "npcs": [],
        "readables": [
            ("The notched post", (209, 100), [
                "The longhouse's own post, older than the one outside. Every notch here has a name cut beside it, in a hand that changes every few generations.",
                "The last forty years are all small notches. The last forty years are all children.",
            ]),
        ],
    },
    "sorenda_scribe_house": {
        "town": "res://scenes/world/sorenda.tscn",
        "name": "Wren's House",
        "image": "assets/sprites/tiles/sorenda/interiors/scribe_room.png",
        "size": (288, 224),
        "exit": (142, 222), "back_to": "from_housescribe", "spawn": (142, 188),
        "blocks": [
            (0, 0, 288, 62), (148, 0, 280, 94), (0, 40, 32, 90),           # back wall, bookshelves, hearth
            (50, 58, 122, 98), (66, 82, 100, 126), (120, 76, 138, 102),     # desk, chair, scroll stack
            (180, 100, 205, 128), (208, 106, 225, 128),                     # book stacks
            (232, 108, 278, 196), (14, 146, 95, 196),                       # beds
            (100, 164, 118, 196), (200, 160, 232, 198),                     # more books
            (0, 0, 10, 224), (278, 0, 288, 224),
            (0, 198, 118, 224), (166, 198, 288, 224),
        ],
        "npcs": [],
        "readables": [
            ("Wren's book of names", (86, 96), [
                "A thick book, bound in bark. Every page is a list of names, and beside each, a year and a place.",
                "The places change over the years: Vetrassa, Verdana, the Starfall mines. For the last forty years, they all say Duskara.",
            ]),
        ],
    },
    "sorenda_herbalist_house": {
        "town": "res://scenes/world/sorenda.tscn",
        "name": "Juniper's Cottage",
        "image": "assets/sprites/tiles/sorenda/interiors/herbalist_room.png",
        "size": (288, 224),
        "exit": (142, 222), "back_to": "from_househerbalist", "spawn": (142, 188),
        "blocks": [
            (0, 0, 288, 78), (112, 40, 186, 82), (0, 90, 30, 160),         # back wall and shelves, jars, bottles
            (60, 112, 138, 168), (162, 104, 228, 162),                      # work table, cauldron
            (256, 52, 288, 190), (0, 158, 55, 198), (205, 172, 258, 198),   # bed, potted plants
            (0, 0, 10, 224), (278, 0, 288, 224),
            (0, 198, 118, 224), (166, 198, 288, 224),
        ],
        "npcs": [],
        "readables": [
            ("A remedy list", (100, 170), [
                "'Feverfew for heat. Willow bark for aches. Moss poultice for cuts that won't close.'",
                "At the bottom, underlined twice: 'Send the good salve east with the next children. They come back with their hands cracked from the dust. If they come back.'",
            ]),
        ],
    },
    "sorenda_woodcutter": {
        "town": "res://scenes/world/sorenda.tscn",
        "name": "Harl's Cottage",
        "image": "assets/sprites/tiles/sorenda/interiors/woodcutter_room.png",
        "size": (288, 224),
        "exit": (142, 222), "back_to": "from_housewoodcutter", "spawn": (142, 188),
        "blocks": [
            (0, 0, 288, 62), (168, 0, 250, 112), (0, 62, 16, 190), (272, 62, 288, 190),   # back wall, hearth, curved walls
            (0, 150, 30, 224), (258, 150, 288, 224),
            (50, 82, 82, 116), (14, 96, 52, 140),                           # chopping block, firewood
            (110, 112, 178, 155), (135, 146, 158, 170), (205, 110, 272, 185),  # table, stool, bed
            (0, 196, 118, 224), (166, 196, 288, 224),
        ],
        "npcs": [],
        "readables": [
            ("A timber order", (92, 100), [
                "'Forty lengths of oak, cut and planed, for pens. Small pens, four foot by four. Deliver to the red-sun crates at Kalmora. D.M.'",
                "Harl has written 'NO' across it, so hard the pencil went through.",
            ]),
        ],
    },
    "sorenda_family_home": {
        "town": "res://scenes/world/sorenda.tscn",
        "name": "Pell's Home",
        "image": "assets/sprites/tiles/sorenda/interiors/family_room.png",
        "size": (288, 224),
        "exit": (142, 222), "back_to": "from_housefamily", "spawn": (142, 188),
        "blocks": [
            (0, 0, 288, 50), (10, 44, 82, 95), (10, 80, 30, 100), (92, 44, 130, 86),    # back wall, stove, wood, cupboard
            (238, 56, 278, 128), (250, 128, 275, 158),                      # child's bed, toys
            (50, 122, 108, 172), (28, 128, 48, 170), (110, 128, 130, 170),  # table and chairs
            (70, 100, 90, 126), (70, 165, 90, 196),
            (0, 0, 10, 224), (278, 0, 288, 224),
            (0, 198, 118, 224), (166, 198, 288, 224),
        ],
        "npcs": [],
        "readables": [
            ("A child's drawing", (226, 140), [
                "Crayon on bark paper: two children holding hands under a big tree. One of them is labelled 'me'. The other is labelled 'Tansy'.",
                "On the back, in a grown-up's hand: 'Tansy went east in the spring. Keep it for her.'",
            ]),
        ],
    },
    "sorenda_tree_house": {
        "town": "res://scenes/world/sorenda.tscn",
        "name": "The Old Tree House",
        "image": "assets/sprites/tiles/sorenda/interiors/tree_house_room.png",
        "size": (288, 224),
        "exit": (142, 222), "back_to": "from_housetree", "spawn": (142, 186),
        "blocks": [
            (0, 0, 288, 100), (40, 60, 110, 112), (200, 104, 255, 136),    # the trunk and stair, hammock, tea table
            (96, 112, 190, 176),                                            # ring of stump seats
            (0, 0, 28, 224), (262, 0, 288, 224), (0, 150, 60, 224), (228, 150, 288, 224),   # curved walls
            (0, 190, 116, 224), (166, 190, 288, 224),
        ],
        "npcs": [],
        "readables": [
            ("A stargazer's journal", (206, 150), [
                "'Another star gone from the Wreath tonight. That's nine since the last race. Mother's map shows all of them.'",
                "'The old stories say the stars go out when the island takes more than it gives. I think the old stories were being polite.'",
            ]),
        ],
    },
    # ---- Verdana, Lake Serin, the Starfall Range (outdoor zones: build_region.py) ----
    "verdana_inn": {
        "town": "res://scenes/world/verdana.tscn",
        "name": "The Sheaf & Sickle",
        "image": "assets/sprites/tiles/verdana/interiors/inn_room.png",
        "size": (288, 224),
        "exit": (143, 196), "back_to": "from_houseinn", "spawn": (143, 168),
        "blocks": [
            (39, 24, 249, 56), (39, 24, 80, 112), (96, 24, 144, 90),       # back wall, stair, hearth
            (160, 60, 243, 100), (170, 98, 236, 114),                       # bar counter and its stools
            (60, 122, 102, 170), (136, 116, 182, 150), (192, 136, 234, 172),   # tables with stools
            (39, 24, 48, 194), (240, 24, 249, 194),                          # side walls
            (39, 180, 128, 194), (158, 180, 249, 194),                       # front wall round the door
        ],
        "npcs": [],
        "readables": [
            ("The slate behind the bar", (118, 104), [
                "Chalked prices: cider, bread, a bed. Under them, a column headed 'Company men - on account'. It's very long, and nothing on it has been crossed off.",
            ]),
        ],
    },
    "verdana_farmhouse": {
        "town": "res://scenes/world/verdana.tscn",
        "name": "Marta's Farmhouse",
        "image": "assets/sprites/tiles/verdana/interiors/farmhouse_room.png",
        "size": (288, 224),
        "exit": (145, 200), "back_to": "from_housefarm", "spawn": (145, 166),
        "blocks": [
            (51, 25, 237, 84), (74, 60, 122, 104), (56, 78, 76, 100),        # back wall, stove, kindling
            (134, 76, 200, 100), (204, 70, 232, 112),                        # churn, baskets, rocking chair
            (152, 104, 220, 158), (208, 152, 232, 178),                      # table and benches, bucket
            (51, 25, 60, 184), (229, 25, 237, 184),
            (51, 176, 124, 184), (166, 176, 237, 184),
        ],
        "npcs": [],
        "readables": [
            ("A letter on the table", (130, 130), [
                "'Dear Marta. The Company will take the whole harvest again at the agreed rate. Scrip enclosed. Your son is well and learning a trade. You may write to him care of the Duskara office.'",
                "Every letter from the last two years is in the drawer. None of them has an answer from her son.",
            ]),
        ],
    },
    "verdana_scholar": {
        "town": "res://scenes/world/verdana.tscn",
        "name": "Aldous's House",
        "image": "assets/sprites/tiles/verdana/interiors/scholar_room.png",
        "size": (288, 224),
        "exit": (143, 205), "back_to": "from_housescholar", "spawn": (143, 166),
        "blocks": [
            (26, 21, 262, 104), (32, 88, 108, 170), (32, 156, 62, 178),       # shelves, desk, book piles
            (136, 96, 166, 132), (168, 98, 202, 150), (196, 128, 214, 160),  # candle and books, armchair
            (220, 108, 250, 152), (234, 148, 258, 178),                      # telescope, books
            (26, 21, 34, 180), (254, 21, 262, 180),
            (26, 172, 124, 180), (162, 172, 262, 180),
        ],
        "npcs": [],
        "readables": [
            ("Rubbings of the stones", (120, 116), [
                "Charcoal rubbings of three standing stones, pinned side by side. On each, a crown and a line of figures beneath it. Aldous has numbered the figures in red ink.",
                "The numbers go into the hundreds. Beside the last one he has written, very small: 'still counting'.",
            ]),
        ],
    },
    "verdana_weaver": {
        "town": "res://scenes/world/verdana.tscn",
        "name": "Oda's Cottage",
        "image": "assets/sprites/tiles/verdana/interiors/weaver_room.png",
        "size": (288, 224),
        "exit": (144, 196), "back_to": "from_houseweaver", "spawn": (144, 168),
        "blocks": [
            (34, 20, 253, 92), (112, 74, 160, 130), (164, 90, 184, 110),     # yarn shelves, loom, basket
            (46, 92, 84, 112), (50, 112, 74, 150), (46, 150, 84, 172),       # baskets, hearth, baskets
            (208, 86, 240, 142), (154, 114, 186, 148),                       # bed, spinning wheel
            (34, 20, 44, 196), (243, 20, 253, 196),
            (34, 176, 128, 196), (160, 176, 253, 196),
        ],
        "npcs": [],
        "readables": [
            ("A half-woven tapestry", (104, 150), [
                "On the loom: a long procession of small figures walking west under a golden sky, each one carrying a sack. Oda has woven them in every colour she owns.",
                "The last figures are only outlines, pinned in place and waiting for thread.",
            ]),
        ],
    },
    "verdana_bakery": {
        "town": "res://scenes/world/verdana.tscn",
        "name": "Pim's Bakery",
        "image": "assets/sprites/tiles/verdana/interiors/bakery_room.png",
        "size": (288, 224),
        "exit": (142, 200), "back_to": "from_housebakery", "spawn": (142, 170),
        "blocks": [
            (32, 24, 256, 82), (124, 24, 176, 92), (40, 40, 104, 90),        # back wall, oven, bread racks
            (208, 62, 246, 112), (40, 100, 106, 130), (40, 120, 62, 184),    # flour sacks, pie table, rolls rack
            (110, 98, 206, 134), (162, 146, 216, 184),                       # counter, kneading table
            (32, 24, 40, 200), (248, 24, 256, 200),
            (32, 188, 124, 200), (160, 188, 256, 200),
        ],
        "npcs": [],
        "readables": [
            ("The order book", (100, 146), [
                "Pim's orders, by the week. The Sheaf & Sickle, the Hensley farm, Old Aldous (one small loaf, no crusts). And a standing order, larger than the rest put together: 'D.M.C. - hard bread, keeps a month. Deliver to the dune road cart.'",
                "The last three weeks' crosses are missing. Nobody came to collect.",
            ]),
        ],
    },
    "verdana_barn": {
        "town": "res://scenes/world/verdana.tscn",
        "name": "The Hensley Barn",
        "image": "assets/sprites/tiles/verdana/interiors/barn_room.png",
        "size": (288, 224),
        "exit": (144, 204), "back_to": "from_housebarn", "spawn": (144, 166),
        "blocks": [
            (28, 20, 260, 86), (38, 94, 90, 140), (96, 82, 114, 130),        # loft and hay, cow stall, ladder
            (124, 94, 176, 140), (220, 94, 250, 122), (184, 112, 250, 158),  # goat stall and post, sacks, cart
            (28, 20, 38, 204), (250, 20, 260, 204),
            (28, 180, 112, 204), (176, 180, 260, 204),
        ],
        "npcs": [],
        "readables": [
            ("A child's cot in the loft", (110, 150), [
                "Up the ladder, tucked behind the hay: a little straw bed, a blanket, a tin cup. Somebody small slept here, and not long ago.",
                "Scratched into the beam: a crown, crossed out. Same as on the Starfall stone.",
            ]),
        ],
    },
    "verdana_mill": {
        "town": "res://scenes/world/verdana.tscn",
        "name": "Verdana Mill",
        "image": "assets/sprites/tiles/verdana/interiors/mill_room.png",
        "size": (288, 224),
        "exit": (144, 222), "back_to": "from_housemill", "spawn": (144, 180),
        "blocks": [
            (6, 0, 282, 50), (150, 40, 232, 82), (34, 52, 112, 104),         # wall top, stair, sacks
            (96, 96, 196, 164), (214, 62, 262, 160),                         # millstones, scale and ledger desk
            (40, 160, 72, 196), (186, 164, 246, 196),                        # sacks
            (6, 0, 40, 224), (248, 0, 282, 224), (40, 50, 70, 90), (218, 50, 248, 90),
            (40, 176, 80, 224), (208, 176, 248, 224), (80, 196, 124, 224), (164, 196, 208, 224),
        ],
        "npcs": [],
        "readables": [
            ("The miller's ledger", (176, 176), [
                "'Flour to the Company: 200 sacks, one third market, by agreement.' The same line, month after month, in the same tired hand.",
                "On the last page: 'Asked where it goes. Told it feeds the workers. Asked which workers. Told to mind the stones.'",
            ]),
        ],
    },
    "serin_fisher_hut": {
        "town": "res://scenes/world/lake_serin.tscn",
        "name": "Neri's Hut",
        "image": "assets/sprites/tiles/lake_serin/interiors/fisher_room.png",
        "size": (288, 224),
        "exit": (144, 214), "back_to": "from_houseneri", "spawn": (144, 158),
        "blocks": [
            (24, 8, 264, 72), (48, 64, 82, 112), (86, 76, 106, 98),          # back wall, stove, bucket
            (148, 68, 232, 112), (180, 118, 246, 166), (38, 122, 84, 170),   # bed, table, barrel and buckets
            (24, 8, 44, 216), (244, 8, 264, 216),
            (24, 168, 124, 216), (164, 168, 264, 216),
        ],
        "npcs": [],
        "readables": [
            ("Neri's night tally", (166, 140), [
                "The back of the tally board: 'Barges, north, by night.' Four or five a week, all last year. Beside the last mark: 'Didn't make it across. Heard them. Didn't go out.'",
            ]),
        ],
    },
    "starfall_cabin": {
        "town": "res://scenes/world/starfall_range.tscn",
        "name": "Hald's Cabin",
        "image": "assets/sprites/tiles/starfall/interiors/cabin_room.png",
        "size": (288, 224),
        "exit": (144, 207), "back_to": "from_househald", "spawn": (144, 172),
        "blocks": [
            (20, 25, 268, 92), (114, 25, 174, 104), (74, 78, 116, 104),      # back wall, fireplace, firewood
            (176, 36, 196, 100), (50, 106, 104, 170), (30, 112, 50, 178),    # skis, table, bench
            (200, 88, 258, 190),                                             # bunk
            (20, 25, 30, 200), (258, 25, 268, 200),
            (20, 190, 128, 200), (160, 190, 268, 200),
        ],
        "npcs": [],
        "readables": [
            ("A map of the pass", (118, 140), [
                "Hald's map of the Starfall pass, marked in pencil: the old road north to Frisalle, the slide, and a second route drawn and rubbed out again, round the east shoulder of the mountain.",
                "In the margin: 'Company men came up with powder. Came down without it.'",
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
target_scene = "{cfg.get("town", "res://scenes/world/kalmora.tscn")}"
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
