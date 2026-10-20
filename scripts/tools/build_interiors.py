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
# What inn keepers sell over the counter (food and tonics; they don't trade cards).
INN_STOCK = '[&"bread", &"smoked_fish", &"healers_tonic"]'
SHOP_STOCK = '[&"pickpockets_whisper", &"lockbox_seal", &"second_wind", &"hollowpoint_charm", &"tidewalker_anklet"]'


# Seabright's guest bungalows: blocks traced from each room (the mirrored rooms reuse
# them flipped).
HONEYMOON = [
    (0, 0, 320, 96), (0, 0, 14, 256), (306, 0, 320, 256),            # back wall and open terrace, side walls
    (14, 40, 138, 178), (0, 130, 40, 210),                            # the canopy bed, a palm
    (186, 96, 222, 122), (208, 64, 236, 116), (234, 52, 290, 132),    # cases, a palm, the wardrobe
    (264, 96, 300, 154), (206, 118, 300, 212),                        # a palm, the chairs round the champagne
    (0, 212, 124, 256), (196, 212, 320, 256),                         # the front wall round the door
]
FAMILY = [
    (0, 0, 320, 112), (0, 0, 22, 256), (300, 0, 320, 256),            # back wall, side walls
    (36, 80, 116, 166), (116, 98, 146, 130), (200, 64, 284, 148),     # the bed, the lamp table, the bunks
    (252, 138, 296, 206), (22, 150, 62, 230), (130, 162, 190, 202),   # the desk, a palm, the fruit table
    (216, 186, 256, 232), (262, 168, 300, 230),                       # the beach bag, a palm
    (0, 232, 130, 256), (186, 232, 320, 256),                         # the front wall round the door
]
COMPANY = [
    (0, 0, 320, 104), (0, 0, 38, 256), (296, 0, 320, 256),            # back wall, side walls
    (26, 56, 120, 170), (176, 108, 226, 148), (232, 90, 300, 170),    # the crates, the hatch, the bed
    (6, 172, 126, 232), (196, 172, 312, 232),                         # the ledger desk, the chart table
    (0, 232, 128, 256), (192, 232, 320, 256),                         # the front wall round the door
]


def mirror(rects, w=320):
    return [(w - x1, y0, w - x0, y1) for x0, y0, x1, y1 in rects]

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
        ], []),
                 ("jobelle", "Jobelle", "jobelle", (250, 124), [
            "There you are! Sit, sit. You look like the road chewed you up and spat you out. The tea's on.",
            "My little sister Mate runs the Copper Kettle up in Sorenda. Tell her Jobelle says to be nice to you. She won't be, but tell her anyway.",
            "Tilly's the baby of the three of us. She's out on the Aurewind downs with her sheep, talking to them like they're people. If you pass her, make sure she's eating.",
            "I keep a candle in the window for every racer out after dark. You're one of my candles now, love. Don't make me worry.",
            "Three sisters, three roofs. Mate says I fuss. Tilly says I fuss. They're both right, and I'm not stopping.",
            "Anyone gives you trouble on the docks, you come straight back here. Otto pretends he's tough. He'll walk you home if I ask him.",
            "Mind you eat something that isn't a card. Bread, a bit of fish. Your heart needs more than luck to keep going.",
            "Mate sent me a letter last week. Four lines, and two of them were about Chef. That's how I know she's well.",
            "Our brother Sully hasn't written in a year. He came to us as a boy with a fine coat and nothing else in the world. If you see a black shepherd in a red scarf, tell him Jobelle's keeping his room.",
            "Sully used to sit right where you're sitting and help me fold sheets. Badly. I'd give anything to have him back folding them badly.",
            "When we were small, Mate always took the bigger half of the apple, then gave it to Tilly when she thought I wasn't looking. Don't let her tell you she's all thorns.",
            "Tilly wrote to say a ram knocked her into the pond. She thought it was the funniest thing that ever happened. I didn't sleep for a week.",
            "You've got that look. Somebody you're racing for, back home? Keep them in mind. It helps on the long roads.",
        ], []),
                 # After dark the docks empty into the tavern: Bram and Luca, off work.
                 ("bram", "Bram", "bram", (130, 200), [
            "Long day hauling crates nobody's allowed to ask about. Long night forgetting them.",
            "Otto waters the cider. Don't tell him I know. It's the only thing in this town that's honest about being thin.",
            "Night tide brings the unmarked ones. I'm in here so I don't have to see them come in.",
        ], [], {"out": (5.0, 6.5)}),
                 ("sailor", "Deckhand Luca", "sailor", (232, 204), [
            "Pull up a stool! I'm telling the one about the sea serpent off Halmeer. It gets bigger every time.",
            "A sailor's day ends when the lamps come on. A sailor's night ends when Jobelle throws him out.",
            "You racers never sleep, do you? Bind your cards before you go out there. The night's when the thieves work.",
        ], [], {"out": (5.0, 6.5)})],
        "inn": "jobelle",
        "keeper": {"wake_lines": ["Oh, love. Oh, look at you. Somebody carried you in off the road and I've sat with you all night. Rest a minute before you go anywhere.", "There you are. You gave me such a fright. Drink this, it's only tea. Whatever you lost out there, it isn't worth losing you.", "Welcome back, sweetheart. Otto carried you up the stairs himself. Don't tell him I told you; he likes people to think he's grumpy."],
                   "room_prompt": "Of course, love! Fresh sheets, a warm brick in the bed. Half a day, or a whole one?",
                   "room_broke": "Oh, love, it's %d gold. Come back when you can. And eat something in the meantime."},
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
        ], SHOP_STOCK[:-1] + ', &"kalmora_return"]')],
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
        ], [], {"out": (23.0, 20.0)})],
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
        ], [], {"out": (22.5, 20.0)})],
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
        ], [], {"out": (5.0, 20.0)})],
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
        ], [], {"out": (5.0, 20.0)})],
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
        "npcs": [("wren", "Wren", "wren", (160, 146), [
            "I write by candle when the village is asleep. The names come easier when nobody's watching me write them.",
            "Mind the stacks. That one's the last ten winters. That one's the seven children.",
        ], [], {"out": (19.0, 8.0)})],
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
        "npcs": [("harl", "Harl", "harl", (90, 172), [
            "Axe is sharp, fire's low, door's barred. That's how a woodcutter sleeps easy in Thornveil.",
            "Sit, sit. There's stew in the pot. It's not Mate's. Don't tell her it's better.",
        ], [], {"out": (20.0, 6.0)})],
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
    "sorenda_inn": {
        "town": "res://scenes/world/sorenda.tscn",
        "name": "The Copper Kettle",
        "image": "assets/sprites/tiles/sorenda/interiors/inn_room.png",
        "size": (288, 224),
        "exit": (144, 222), "back_to": "from_houseinn", "spawn": (144, 196),
        "blocks": [
            (0, 0, 288, 96), (56, 60, 120, 120), (30, 86, 56, 112),         # back wall, the kettle hearth, firewood
            (130, 74, 192, 132), (198, 96, 222, 142), (222, 40, 272, 168),  # bar and stools, barrels, the stair
            (30, 144, 92, 190), (84, 180, 102, 198),                        # west table and stools
            (128, 146, 192, 184), (184, 170, 202, 194),                     # east table and stools
            (222, 192, 262, 218), (20, 170, 36, 210),                       # barrels by the door, a broom
            (0, 0, 18, 224), (270, 0, 288, 224),                            # walls
            (0, 216, 128, 224), (160, 216, 288, 224),                       # front wall round the door
        ],
        "npcs": [("mate", "Mate", "mate", (108, 136), [
            'What. You want a bed, or do you want to stand there dripping on my floor?',
            'Chef. CHEF. Some dog in Vetrassa puts a sprig of parsley on a potato and the whole island weeps. My stew would put him out of business in a week.',
            "Yes, one arm. No, I don't need help with the kettle. I've been lifting it longer than you've been racing.",
            "Jobelle's my sister. She'll have told you I'm nice underneath. She lies to be kind. It's her worst habit.",
            "People wait a year for a table at Chef's. Here you wait for nothing and the gravy's better. Think about that.",
            "Tilly's the youngest of us. Anyone's unkind to her out on those downs, they answer to me. With the one arm. It's plenty.",
            "You know what's in Chef's famous broth? Water and reputation. You know what's in mine? Mushrooms I picked, roots I dug, and spite.",
            'Lost the arm in the Thornveil years back. A hound got the better of me. Then I got the better of the hound.',
            "Don't touch the kettle. Don't touch the guest book. And don't say the word 'restaurant' in here.",
            "Some racer last year said my pie reminded him of Chef's. I threw him out. In the rain. Into the brambles.",
            "Sully? Don't say that name in here unless you've news. He's our brother. He's an idiot. I'd give my other arm for him.",
            "Chef's got a brother, you know. A better one. We raised him. Chef got the restaurant; we got the decent one.",
            "Fine. The bread's good. You can tell people that. Tell them in Vetrassa, loudly, outside a certain door.",
        ], [])],
        "inn": "mate",
        "keeper": {"wake_lines": ["You're awake. Good. You were bleeding on my clean floor.", "Somebody dragged you in off the road. Wasn't me. ...Fine, it was me. Don't make a habit of it.", "Back from the dead, are we? Eat something. And no, it's not from Chef's. It's better."],
                   "room_prompt": "Bed's up the stair. How long. Pick.",
                   "room_broke": "%d gold. Not a copper less. This isn't Chef's, I don't do charity for show."},
        "readables": [
            ("The guest book", (210, 150), [
                "A fat guest book, every page a race year. Each year starts with three cloaked names, signed in a hurry.",
                "Most years, two of the names sign again on the way back south. Never the third. Mate has drawn a little kettle beside each one that didn't.",
            ]),
        ],
    },
    # ---- Seabright Quay, the royal resort (outdoors: build_region.py) ----
    "seabright_hotel": {
        "town": "res://scenes/world/seabright_quay.tscn",
        "name": "The Seabright Grand",
        "image": "assets/sprites/tiles/resort/interiors/lobby_room.png",
        "size": (320, 256),
        "exit": (160, 252), "back_to": "from_househotel", "spawn": (160, 214),
        "blocks": [
            (0, 0, 320, 100), (122, 84, 198, 126),                          # back wall, the reception desk
            (0, 0, 28, 256), (292, 0, 320, 256),                            # side walls
            (204, 56, 300, 160), (32, 62, 64, 118),                         # the grand stair, a palm
            (266, 112, 300, 158), (244, 136, 268, 166),                     # palm and lamp table by the stair
            (36, 144, 116, 180), (60, 170, 90, 198),                        # red armchairs round a table
            (30, 176, 58, 206), (60, 190, 88, 222),                         # green armchairs
            (10, 186, 40, 248), (96, 186, 124, 248), (196, 190, 224, 248),  # potted palms by the door
            (218, 170, 290, 200), (240, 196, 272, 220), (220, 206, 292, 232), (282, 186, 312, 248),
            (0, 240, 128, 256), (192, 240, 320, 256),                       # the front wall round the doors
        ],
        "npcs": [("fennick", "Fennick", "fennick", (110, 136), [
            "Welcome to the Seabright Grand. Do mind the rug; it was a gift from the Crown.",
            "We are, I'm afraid, rather full. Racing season. And the Duke has the whole top floor. He always has the whole top floor.",
            "The Seabright belongs to the young ladies Sparkle and Sassy now; His Majesty's gift. Miss Sparkle runs the boats and Miss Sassy runs the guests. I run everything else.",
            "The young ladies keep the last bungalow on the east jetty for themselves. Do knock. Miss Sparkle has a way of answering the door from the sea.",
            "The hotel's accounts are settled by the Duskara Mining Company, through the Duke. The young ladies do not read the accounts. That is, I gather, the arrangement.",
            "The hotel asks guests not to discuss business in the lobby. The hotel is mostly asking the Duke.",
            "Our chef trained under Chef himself, in Vetrassa. Please do not tell the woman who runs the inn at Sorenda; she sent us a very long letter about it.",
            "Should you require anything at all, ring the bell. I shall appear. I always appear.",
        ], [])],
        "inn": "fennick",
        "keeper": {"wake_lines": [
                       "Ah. You're awake. A fisherman found you and brought you up the quay. We have put the room on account. Do try not to faint on the promenade again; it upsets the guests.",
                       "Welcome back to the land of the living. Tea is on its way. The Seabright Grand prides itself on its recoveries.",
                   ],
                   "room_prompt": "Certainly. A sea view, naturally. Half a day, or the full day?",
                   # Seabright has no card shop: the concierge arranges your return.
                   "extra_stock": ["seabright_return"],
                   "room_broke": "I'm afraid a room is %d gold, even for racers. Perhaps the inn at Verdana; I hear the dinner is very punctual."},
        "readables": [
            ("The guest register", (160, 130), [
                "A heavy leather book open on the desk. 'Top floor, all rooms: the Duke. Standing booking. Paid in advance, every season.'",
                "Under it, in the same hand, a list of 'business guests' who all arrived by sea, at night. None of them have names. They have numbers.",
            ]),
        ],
    },
    "seabright_bungalow": {
        "town": "res://scenes/world/seabright_quay.tscn",
        "name": "The Sisters' Bungalow",
        "image": "assets/sprites/tiles/resort/interiors/cousins_bungalow.png",
        "size": (320, 256),
        "exit": (160, 252), "back_to": "from_housebungalow", "spawn": (160, 220),
        "blocks": [
            (0, 0, 320, 98), (0, 0, 22, 256), (300, 0, 320, 256),            # back wall and window, side walls
            (56, 40, 104, 112), (22, 84, 62, 166), (66, 134, 94, 160),      # vanity, dresser, pouf
            (8, 170, 72, 244), (216, 30, 290, 146),                          # the trunk of dresses, the canopy bed
            (288, 126, 310, 232), (264, 204, 290, 230),                      # surfboard, snorkel and fins
            (78, 182, 112, 246), (208, 182, 236, 246),                       # potted palms by the door
            (136, 120, 186, 152),                                            # the low table on the rug
            (0, 244, 124, 256), (196, 244, 320, 256),                        # the front wall round the door
        ],
        "npcs": [],
        "readables": [
            ("A deed on the vanity", (80, 124), [
                "Heavy paper, a royal seal. 'Seabright Quay, its quay, terrace, bungalows and the Grand, to my nieces Sparkle and Sassy, to keep and to enjoy. L.'",
                "Pinned behind it, a smaller note: 'Upkeep, staff and stores met in full by the Duskara Mining Company, in gratitude for the Crown's friendship.' No signature. A stamp of a pick and a crown.",
            ]),
            ("Sparkle's dive log", (266, 178), [
                "Scrawled in waterproof pencil. 'Night dive. The light again, low on the water past the yachts. A barge, no lamps. Third night running.'",
                "'They let something down on a rope at the old reef and pull it up empty. Tomorrow I swim out and see what's on the rope. DON'T tell Sassy. Sassy, if you're reading this, stop it.'",
            ]),
            ("Sassy's seating plan", (160, 160), [
                "A card covered in hearts and crossings-out. 'Dinner, Saturday. Duke on my right (he likes that). His three gentlemen next to him; they said not to write names, just put \'Company\'.'",
                "'Cousin Chef: said he'd come, didn't. Cousin Freya: sent two guards instead. Cousin Sully: never answers. Note to self: ask Uncle why nobody comes to our parties.'",
            ]),
            ("A letter on the trunk", (88, 168), [
                "'Sparkle, Sassy. Pepper is under-salting the stew. Tell her. Do not tell her I said tell her. Duke says the business guests liked the tart. Good. Burn this. C.'",
                "It has not been burned. Somebody has drawn a moustache on the signature.",
            ]),
        ],
    },
    # ---- Seabright's guest bungalows (west jetty 1-3, east jetty 4-5) ----
    "seabright_bungalow1": {
        "town": "res://scenes/world/seabright_quay.tscn",
        "name": "Bungalow 1",
        "image": "assets/sprites/tiles/resort/interiors/honeymoon_bungalow.png",
        "size": (320, 256),
        "exit": (160, 252), "back_to": "from_bungalow1", "spawn": (160, 204),
        "blocks": HONEYMOON,
        "npcs": [],
        "readables": [
            ("A card on the pillow", (90, 186), [
                "Gold-edged, propped on the rose petals. 'Welcome to Seabright, Mr and Mrs Hale. Your stay is with the compliments of the Duskara Mining Company, in thanks for your husband's years of service.'",
                "On the back, in pencil, a different hand: 'Twenty years in the counting room and they give him a week by the sea. He cried. I'm keeping the card.'",
            ]),
            ("A half-written postcard", (198, 178), [
                "'Dear Mother. The water is so clear you can see the fish through the floor. Edmund says the barge that goes past at night is nothing, only the night post. He says it very quickly.'",
            ]),
        ],
    },
    "seabright_bungalow2": {
        "town": "res://scenes/world/seabright_quay.tscn",
        "name": "Bungalow 2",
        "image": "assets/sprites/tiles/resort/interiors/family_bungalow.png",
        "size": (320, 256),
        "exit": (158, 252), "back_to": "from_bungalow2", "spawn": (158, 214),
        "blocks": FAMILY,
        "npcs": [],
        "readables": [
            ("Postcards on the desk", (244, 176), [
                "A stack of postcards of the Saltglass Terrace, all addressed to the same school in Vetrassa. 'We saw a dolphin. We saw Lady Sparkle jump off the pier. Papa said not to tell anyone that.'",
            ]),
            ("A child's drawing", (108, 214), [
                "Crayon on hotel paper: the jetty, the bungalows, a round yellow moon. Out on the water, a long black boat with no windows, and a little light on it, coloured in very hard.",
                "Underneath, carefully: 'THE GOST BOAT. It comes when evryone is asleep. Not me.'",
            ]),
        ],
    },
    "seabright_bungalow3": {
        "town": "res://scenes/world/seabright_quay.tscn",
        "name": "Bungalow 3",
        "image": "assets/sprites/tiles/resort/interiors/company_bungalow.png",
        "size": (320, 256),
        "exit": (160, 252), "back_to": "from_bungalow3", "spawn": (160, 212),
        "blocks": COMPANY,
        "npcs": [],
        "readables": [
            ("A tonnage ledger", (120, 180), [
                "Columns of dates and weights, no names. 'Reef drop, the Gannet, 4 crates. Lamp: 3 short, 1 long. Received by hand, Bungalow 3.' The same line, every week, back two years.",
                "In the margin of the last page: 'Halmeer route cleared through the cape. D. says no more drops off the Quay once the cousins start asking questions.'",
            ]),
            ("A chart with pins", (190, 198), [
                "A sea chart of the south coast. Red pins: the old reef off Seabright, a cove past the southern cape marked HALMEER, and a dotted line from there up the west coast to Vetrassa.",
                "Duskara is not on the chart. Somebody has drawn a small pick in the empty sand where it should be.",
            ]),
            ("A crate stencilled D.M.C.", (128, 130), [
                "Packed in straw: stacks of blank cards, uncut, still in sheets. Gritty with red sand. Each sheet has a stamp in the corner, a pick and a crown, and a number.",
            ]),
            ("A hatch in the floor", (204, 152), [
                "A square hatch over the water with a ladder going down. The rungs are wet and there's rope burn on the frame. Below, black water and the slap of the tide on the pilings.",
            ]),
        ],
    },
    "seabright_bungalow4": {
        "town": "res://scenes/world/seabright_quay.tscn",
        "name": "Bungalow 4",
        "image": "assets/sprites/tiles/resort/interiors/family_bungalow_r.png",
        "size": (320, 256),
        "exit": (162, 252), "back_to": "from_bungalow4", "spawn": (162, 214),
        "blocks": mirror(FAMILY),
        "npcs": [],
        "readables": [
            ("A painter's sketchbook", (74, 176), [
                "Watercolours of the bay: the terrace at noon, the yachts, Lady Sassy asleep on a lounger with a drink balanced on her stomach.",
                "The last page is the bay at night, all dark blue, except one small yellow square low on the water past the yachts. Under it: 'Asked Fennick what it was. He changed the subject to the weather. The weather was fine.'",
            ]),
            ("A guestbook page", (160, 210), [
                "'Lovely stay. Staff charming. The gentlemen in Bungalow 3 might consider sleeping at night like everyone else. Five stars.'",
            ]),
        ],
    },
    "seabright_bungalow5": {
        "town": "res://scenes/world/seabright_quay.tscn",
        "name": "Bungalow 5",
        "image": "assets/sprites/tiles/resort/interiors/honeymoon_bungalow_r.png",
        "size": (320, 256),
        "exit": (160, 252), "back_to": "from_bungalow5", "spawn": (160, 204),
        "blocks": mirror(HONEYMOON),
        "npcs": [],
        "readables": [
            ("A report, half-written", (230, 186), [
                "'Captain. Day nine. The Ladies are well. They know we are here and have taken to waving. Lady Sparkle swam under our bungalow at dawn and knocked on the floor.'",
                "'Nothing to report but this: the Duke's men do not sleep, and a boat with no lamps comes to the reef twice a week. Your mother's friends, I think. Shall I keep watching, or stop? F., I await your orders.'",
            ]),
            ("A guard's tabard, folded", (122, 170), [
                "The black and gold of the King's Guard in Vetrassa, folded small and hidden under a beach towel. Whoever is staying here is not on holiday.",
            ]),
        ],
    },
    # ---- Frisalle (outdoors: build_region.py) ----
    "frisalle_inn": {
        "town": "res://scenes/world/frisalle.tscn",
        "name": "The Hearth & Horn",
        "image": "assets/sprites/tiles/frisalle/interiors/inn_room.png",
        "size": (320, 256),
        "exit": (160, 250), "back_to": "from_houseinn", "spawn": (160, 222),
        "blocks": [
            (0, 0, 320, 112), (124, 90, 196, 124), (0, 0, 34, 256), (34, 40, 74, 126),   # back wall, hearth, stairs
            (216, 100, 262, 186), (262, 0, 320, 256),                                     # the bar, the shelves behind it
            (30, 124, 108, 178), (124, 126, 196, 180), (46, 188, 124, 236),               # tables and benches
            (190, 204, 232, 240), (0, 200, 40, 256), (284, 200, 320, 256),                # coat rack, the corners
            (0, 244, 136, 256), (184, 244, 320, 256),                                     # the front wall round the door
        ],
        "npcs": [("mirren", "Mirren", "mirren", (172, 214), [
            "Oh. Hello. I'm not working. I'm eating. Ottilie makes me eat.",
            "The factors never come in here. That's why I do.",
        ], [], {"out": (19.0, 23.0)}),
                 ("ottilie", "Ottilie", "ottilie", (204, 194), [
            "Come in, come in, shake the snow off! Boots by the fire, coat on the rack, and you'll have something hot before you've said your name.",
            "The toll was my idea. One wolf collar a head. The wolves took every goat on the upper meadow; let the wolves pay to get in, I said.",
            "My Anselm guided folk over the pass for thirty years. They carved his name on the bell tower the winter the slide came down. Last name on it. I mean to keep it the last.",
            "Somebody drilled that mountain, love. Weather doesn't drill. When I find out who, they'll pay a toll they'll remember.",
            "Bodo's buying rounds again. Bodo never bought a round in his life before the slide. A man doesn't get generous; he gets paid.",
            "Little Mirren from the counting house eats here every night and never finishes her plate. Something's eating her first, poor thing.",
            "They say there's a cook down on the south coast making Chef's own stew, the one from Vetrassa. Fancy that. I've never tasted it. Never been further than the pass.",
            "Supper at dusk, bed when you like, and nobody sleeps cold in my house. Those are the rules. There aren't any others.",
        ], [])],
        "inn": "ottilie",
        "keeper": {"wake_lines": [
                       "There you are. Sven carried you down off the snow like a sack of flour. Drink this. All of it. Don't argue with me.",
                       "Welcome back, love. You were blue when they brought you in. You're pink now. Pink's better. Stay pink.",
                   ],
                   "room_prompt": "A bed by the chimney, a hot stone for your feet. Half a day, or the whole day?",
                   "room_broke": "It's %d gold, love, and I've a roof to keep up. Sit by the fire as long as you like, though. That's free."},
        "readables": [
            ("The visitors' book", (150, 196), [
                "Racers, guides, a pedlar or two. Then, since the slide, a page of names in one hand that all signed in after midnight, and all paid in Duskara silver.",
            ]),
        ],
    },
    "frisalle_counting": {
        "town": "res://scenes/world/frisalle.tscn",
        "name": "The Factors' Counting House",
        "image": "assets/sprites/tiles/frisalle/interiors/counting_room.png",
        "size": (320, 256),
        "exit": (157, 228), "back_to": "from_housecounting", "spawn": (157, 204),
        "blocks": [
            (0, 0, 320, 100), (14, 100, 98, 178), (88, 90, 122, 130), (186, 20, 238, 136),   # back wall, clerks' desks, stove, shelves
            (244, 112, 290, 150), (254, 150, 300, 200), (130, 128, 220, 192),                # strongbox, scales, the partners' desk
            (0, 0, 16, 256), (300, 0, 320, 256), (0, 180, 20, 256), (300, 180, 320, 256),    # walls and corners
            (0, 212, 136, 256), (180, 212, 320, 256),                                        # the front wall round the door
        ],
        "npcs": [("mirren", "Mirren", "mirren", (112, 190), [
            "Oh! A customer. Nobody comes in. Well, the factors come in. They don't count as customers. They count everything else.",
            "I'm the clerk. I keep the books. I keep them very carefully. Somebody else keeps the other books.",
            "Please don't touch the strongbox. Please don't look at the strongbox. Thank you.",
            "Before the slide we sealed perhaps a cart a week over the pass. Since the slide, the pass is closed, and somehow I'm busier than ever.",
            "The factors live in Vetrassa. They come up once a year, eat at the Hearth & Horn, and go home. They've a friend who keeps an eye on things. A dachshund. Very charming. Very interested in carts.",
        ], [], {"out": (7.0, 19.0)})],
        "readables": [
            ("The great ledger", (238, 160), [
                "The factors' book, in Mirren's tidy hand. 'Over the pass: nil. Through the town: nil. Sealed and weighed: flour, salt, firewood.'",
                "On the facing page, in a different ink: forty cartloads 'from the south road', weighed at night, sealed with the second seal. Consigned to 'the Company, by way of Vetrassa'.",
            ]),
            ("A portrait", (40, 194), [
                "A stern old factor in a fur collar, a seal on a ribbon round his neck. The brass plate reads 'Founder'. Somebody has stuck a little paper crown on his head and taken it off again.",
            ]),
        ],
    },
    "frisalle_carver": {
        "town": "res://scenes/world/frisalle.tscn",
        "name": "Liesl's Workshop",
        "image": "assets/sprites/tiles/frisalle/interiors/carver_room.png",
        "size": (320, 256),
        "exit": (142, 248), "back_to": "from_housecarver", "spawn": (150, 214),
        "blocks": [
            (0, 0, 320, 64), (0, 0, 14, 256), (300, 0, 320, 256),                    # walls
            (14, 130, 124, 214), (76, 56, 182, 132), (176, 30, 240, 186),              # bed, workbench, the owl and the shelves
            (238, 40, 300, 186), (178, 188, 230, 228),                                 # stove, stacked logs
            (0, 214, 112, 256), (230, 214, 320, 256), (176, 230, 320, 256),            # the floor's lower edges
        ],
        "npcs": [("liesl", "Liesl", "liesl", (150, 172), [
            "Evenings are for the fine work. Eyes, whiskers, the little claws. The frost can't do those.",
            "Sit if you can find a chair that isn't half a bear.",
        ], [], {"out": (20.0, 7.0)})],
        "readables": [
            ("A half-carved figure", (150, 136), [
                "A little wolf, half out of the block. Round its neck Liesl has carved a collar, and on the collar a tiny red sun.",
            ]),
            ("Liesl's order book", (160, 196), [
                "Spoons, a cradle, a sign for the inn. Then: 'Bodo: armchair, walnut. Paid three times the price. Said forget it.' Then: 'Bodo: a box with a false bottom. Said forget that too.'",
            ]),
        ],
    },
    "frisalle_weighmaster": {
        "town": "res://scenes/world/frisalle.tscn",
        "name": "The Weigh Master's House",
        "image": "assets/sprites/tiles/frisalle/interiors/weigh_room.png",
        "size": (320, 256),
        "exit": (157, 236), "back_to": "from_houseweigh", "spawn": (157, 210),
        "blocks": [
            (0, 0, 320, 100), (92, 86, 156, 118), (160, 50, 204, 108), (208, 40, 232, 108),   # back wall, desk, cabinet, clock
            (20, 40, 70, 212), (66, 110, 112, 170), (262, 70, 296, 170), (236, 90, 262, 128),  # stove, armchair, wardrobe, chair
            (220, 166, 296, 212), (0, 0, 20, 256), (300, 0, 320, 256),                        # bed, side walls
            (0, 220, 136, 256), (180, 220, 320, 256),                                         # the front wall round the door
        ],
        "npcs": [("bodo", "Bodo", "bodo", (160, 160), [
            "This is a private house! I mean. Welcome. Wipe your feet. Don't touch the cups.",
            "Lovely chair, isn't it? Walnut. Carved locally. I paid a fair price. A very fair price.",
        ], [], {"out": (21.0, 6.0)})],
        "readables": [
            ("A letter in the desk drawer", (124, 124), [
                "The drawer isn't locked. It's the false bottom of the box inside it that's locked, and Bodo has left the key in it.",
                "'B. Forty loads this winter, through the ice road. Weigh them, seal them, forget them. Your fee is enclosed. The Company thanks you. D.' The seal on it is a dachshund's head over a crossed pick.",
            ]),
            ("A cabinet of silver cups", (182, 120), [
                "Racing cups, christening cups, a punch bowl. None of them engraved with Bodo's name. All of them new.",
            ]),
        ],
    },
    "frisalle_guide": {
        "town": "res://scenes/world/frisalle.tscn",
        "name": "The Guide's Lodge",
        "image": "assets/sprites/tiles/frisalle/interiors/guide_room.png",
        "size": (320, 256),
        "exit": (160, 244), "back_to": "from_houseguide", "spawn": (160, 214),
        "blocks": [
            (0, 0, 320, 112), (24, 10, 64, 180), (76, 108, 122, 128),            # back wall, fireplace, boots drying
            (20, 176, 100, 236), (236, 74, 296, 196), (200, 64, 224, 126),       # table, bunk bed, sled
            (0, 0, 20, 256), (300, 0, 320, 256),                                  # side walls
            (0, 232, 132, 256), (188, 226, 320, 256),                             # the front wall round the door
        ],
        "npcs": [],
        "readables": [
            ("The map of the passes", (160, 122), [
                "Every route over the Starfall Range in Sven's hand, with the guides' huts and the safe snow marked. The main pass is crossed through in red: 'SLIDE. Drill marks.'",
                "A thin dotted line he has added since: from the ice caves east of the pass, under the mountain, coming out behind Frisalle. Beside it: 'ice road? carts? who cut it?'",
            ]),
            ("Sven's logbook", (112, 200), [
                "'Took the Vetrassa factors over in autumn. Took the Duke's man over twice, with a heavy pack he wouldn't let me carry. Then the slide. No more fares.'",
                "'Heard wheels under the mountain last night. Ottilie says I'm drinking. I'm not drinking. Yet.'",
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
        "npcs": [("bruno", "Bruno", "bruno", (158, 164), [
            "Kitchen's closed. Well. It's closed for anyone who asks politely. Here, have the heel of the loaf.",
            "Tally's asleep upstairs, so I can say it: the cider's better after dark. I don't know why either.",
        ], [], {"out": (20.0, 6.0)}),
                 ("tally", "Tally", "tally", (110, 106), [
            'Hello, hello, HELLO! Welcome to the Sheaf & Sickle! Boots off the table, coin on the counter, smile on the face!',
            "Dinner is at five. Not five past. Not 'about five'. FIVE. The bell rings, the plates go down, and the door stays shut until the gravy's gone.",
            "Men! Honestly! Bruno's the only one I let in my kitchen, and that's because he's scared of me. As he should be.",
            "Bruno asked if dinner could be at half five on market days. I said no. He asked why. I said FIVE. He hasn't asked again.",
            "I've been up since four! Swept the yard, chased off a ram, counted the Company's debts twice. Still not paid! Still counting!",
            'Every man who came through that door this harvest tried to tell me how to run my inn. Every one of them ate his dinner at five.',
            "Tilly's my best friend in the whole world! Her sister Jobelle sends me jam every winter. Her other sister Mate sends me complaints. I keep both!",
            "Racers are always in a hurry. I respect that! You'll still sit down at five like everybody else.",
            "The Company man in the corner wanted his supper at seven. Seven! I gave him a crust and a lecture. He's still here. Still hungry.",
            "Oh, I love a busy day! Fifty pints, twelve beds, one dinner, at FIVE, and not a single man telling me anything I didn't already know!",
            # Chef (the royal son, in Vetrassa): the one man she'd let tell her how to cook.
            "Men are useless. All of them. Except... no. All of them. Mostly. Don't look at me like that.",
            "Have you eaten at Chef's place in Vetrassa? No? Me neither. Not yet. I've a dress picked out for when I do. Not that it matters. It's just a dress.",
            "Chef once said my gravy was 'honest'. Honest! In a letter! To Tilly! Who told me! I've read it eleven times. It's on the wall behind the bar. Don't touch it.",
            "If Chef ever came to Verdana, I'd serve him dinner at whatever time he liked. Six, seven, midnight. Don't you DARE tell Bruno I said that.",
            "Mate says Chef's sauces are all show and no supper. Mate is wrong. Mate is jealous. Mate has never seen him fold a pastry. Neither have I. But I've imagined it.",
            "A German Shepherd who cooks. Do you know how rare that is? I don't hate ALL men. I hate the ones who aren't Chef.",
            "I wrote to Chef asking for his stew recipe. Strictly professional. I signed it 'yours'. Strictly professionally yours. I've been sick with it for a month.",
        ], [])],
        "inn": "tally",
        "keeper": {"wake_lines": ["WELCOME BACK! You've been out cold for hours! You missed DINNER!", "Up you get! A shepherd found you face down in the barley. Lucky for you it wasn't five o'clock or I'd never have come out!", 'There she wakes! Or he. Or whatever you are under that hood! Some man tried to carry you in and I did it myself!'],
                   "room_prompt": "A room! Lovely! Half a day or a full one? Dinner's at five either way!",
                   "room_broke": "%d gold, sweetheart! No coin, no bed! You can still come to dinner. At FIVE.",
                   "meal_hour": 17.0,
                   "meal_lines": ["It's five o'clock! Sit! Eat! Everything on the plate, I'm watching!", "There. Full belly, full heart. That's the Sheaf & Sickle way!"],
                   "pre_meal_lines": ["Dinner in under an hour! Wash your paws and don't be late. I lock the door at five past!", "Smell that? That's dinner. At FIVE. Go and do something useful until then.", 'Nearly five! Nearly five! Bruno, the plates! BRUNO!']},
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
        "npcs": [("marta", "Marta", "marta", (110, 140), [
            "Supper's done, boots are off. If you're here about the harvest, it's sold. If you're here about my son, sit down.",
            "I count the Company scrip every night. It never comes to more than it was the night before.",
        ], [], {"out": (20.0, 5.0)})],
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
        "npcs": [("oda", "Oda", "oda", (196, 162), [
            "I weave by lamplight. The figures come out smaller at night. I don't know why.",
            "Sit by the hearth a moment. You've the look of someone who's walked a long way to find someone.",
        ], [], {"out": (20.5, 6.5)})],
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
    # ---- Duskara (outdoors: build_region.py) ----
    "duskara_inn": {
        "town": "res://scenes/world/duskara.tscn",
        "name": "The Cistern",
        "image": "assets/sprites/tiles/duskara/interiors/inn_room.png",
        "size": (320, 256),
        "exit": (158, 250), "back_to": "from_houseinn", "spawn": (158, 222),
        "blocks": [
            (0, 0, 320, 92), (0, 56, 88, 128), (126, 94, 194, 176),                      # back wall, the stair, the well and its table
            (220, 96, 290, 182), (262, 0, 320, 190),                                     # the counter, the shelves behind it
            (40, 140, 108, 172), (8, 138, 40, 190),                                      # cushions round the left table, a palm
            (72, 202, 98, 244), (222, 204, 244, 244), (246, 206, 266, 226),             # palms by the door (their pots), the little table
            (116, 198, 134, 236), (184, 198, 202, 236),                                  # the door's lantern posts
            (0, 186, 56, 256), (268, 186, 320, 256),                                     # the corners
            (0, 246, 134, 256), (182, 246, 320, 256),                                    # the front wall round the door
        ],
        "npcs": [("hesper", "Hesper", "hesper", (236, 192), [
            "Come out of the sun. Sit. The Cistern stays cool all day; the old well under the floor breathes for us.",
            "Water's free in my house. It always was in Duskara, before the meters. I'm old-fashioned.",
            "Racers, Company clerks, caravan folk, the odd lost poet. Everyone ends up at the Cistern. There's nowhere else.",
            "The foreman eats here on the first of the month. Alone, at that table, with her ledger. Nobody sits near her. I always bring her an extra cup.",
            "Listen at the well some nights and you'll hear water moving far below. My grandmother said the whole town floats on a lake underground. The Company says that's their lake now.",
            "Rafi brings me sweet water from the Sunwell. I don't ask how he gets it past the Company tank, and he doesn't ask what I do with the extra beds.",
            "Sleep in the heat of the day, walk in the cool of the night. That's how Duskara has always lived. The shaft doesn't care what hour it is.",
            "My rooms are up the stair, under the dome. Cool as a cellar. Lie still and you can hear the town breathing.",
        ], [])],
        "inn": "hesper",
        "keeper": {"wake_lines": [
                       "Shh, easy. Zahra's people found you face down in the dunes. You're in the Cistern. Drink first, then talk.",
                       "You're awake. Good. The sand nearly had you. Lie still a while; the dome keeps the heat off.",
                       "Welcome back to the living. Nib ran all the way to fetch me. Thank him, he won't ask you to.",
                   ],
                   "room_prompt": "A cool bed under the dome. Half a day, or sleep through the heat to tomorrow?",
                   "room_broke": "That's %d gold, friend. Sit by the well a while instead; that's free, and so is the water."},
        "readables": [
            ("The old cistern", (160, 182), [
                "A round stone well in the middle of the floor, its rim worn smooth by four hundred years of ropes. The water far down is black and cold.",
                "Scratched inside the rim, just below where a hand would rest: little marks in rows, like a tally. And beside them, a sun.",
            ]),
            ("The guest ledger", (210, 146), [
                "Names, dates, rooms. Racers. A caravan. Then, every few nights, the same entry in Hesper's neat hand: 'Two guests. No names. Paid.'",
            ]),
        ],
    },
    "duskara_office": {
        "town": "res://scenes/world/duskara.tscn",
        "name": "The Company Office",
        "image": "assets/sprites/tiles/duskara/interiors/office_room.png",
        "size": (320, 256),
        "exit": (158, 250), "back_to": "from_houseoffice", "spawn": (158, 222),
        "blocks": [
            (0, 0, 320, 100), (0, 0, 56, 192), (40, 120, 82, 176), (62, 84, 110, 118),   # back wall, the tool rack, the bench, crates
            (180, 110, 232, 192), (230, 116, 256, 162), (226, 66, 264, 116),             # the desk, its chair, the safe
            (266, 56, 320, 182),                                                          # the ledger shelves
            (24, 180, 116, 250), (200, 180, 320, 250),                                   # crates by the door
            (132, 192, 141, 256), (176, 192, 185, 256),                                  # the door posts
            (0, 246, 134, 256), (182, 246, 320, 256),                                    # the front wall round the door
        ],
        "npcs": [],
        "readables": [
            ("The tunnel chart", (100, 108), [
                "A chart of the workings under Duskara: the North Shaft, then tunnels branching east under the dunes, further than seems possible, each one marked with a date and a number of heads.",
                "The oldest tunnel is labelled in a different, older hand: 'THE KING'S SEAM.' Someone has written beside it, in the foreman's: 'Still producing.'",
            ]),
            ("The tag board", (184, 108), [
                "Rows of brass tags on hooks, each stamped with a number and a red sun, like the one on the frost wolves' collars. Hundreds of them.",
                "Some hooks are empty, with a chalk cross under them. Some crosses have been rubbed out and redrawn as a circle. Nobody has written what a circle means.",
            ]),
            ("The foreman's desk", (166, 184), [
                "A day ledger, open: 'Down 212. Up 209. Three in the infirmary. Count true.' Signed with an X in black ink, firm.",
                "Under the ledger, a letter on heavy paper: 'Production must rise before the race is run. Your husband's indulgence of the old custom cannot be allowed to cost us the season. D.' The seal is a dachshund's head over a crossed pick.",
            ]),
        ],
    },
    "duskara_glassworks": {
        "town": "res://scenes/world/duskara.tscn",
        "name": "Oren's Glassworks",
        "image": "assets/sprites/tiles/duskara/interiors/glass_room.png",
        "size": (320, 256),
        "exit": (158, 250), "back_to": "from_houseglass", "spawn": (158, 222),
        "blocks": [
            (0, 0, 320, 96), (0, 40, 80, 182), (70, 115, 120, 175),                     # back wall, the workbench, the sand bin
            (222, 20, 300, 128), (226, 140, 282, 178), (290, 60, 320, 190),             # the furnace, the cooling rack, shelves
            (282, 170, 320, 200), (40, 195, 104, 250), (104, 214, 124, 245),            # barrels, the bottle tables, buckets
            (225, 195, 270, 245), (208, 215, 228, 240),
            (134, 192, 141, 256), (177, 192, 184, 256),                                  # the door posts
            (0, 180, 40, 256), (282, 180, 320, 256), (0, 246, 134, 256), (182, 246, 320, 256),
        ],
        "npcs": [("oren", "Oren", "oren", (180, 150), [
            "Mind the furnace. It's been lit for nine years. If it goes out, so do I.",
            "Duskara sand makes the clearest glass on the island. The Company wants it for lamps. Lamps for the shaft. I make them. I don't like making them.",
            "Every bottle on that shelf has a little air trapped in it from the day I blew it. My breath, nine years of it. Sentimental, for a dog who works with fire.",
            "The old temple on the mesa has sun-glass in its sand, where lightning struck it. Green as a lizard's eye. I'd go up and gather it, if I could leave the furnace.",
            "Nib comes in to warm his hands in the cold nights. Don't let the heat fool you; the desert freezes after dark. He sits by the furnace and says nothing at all.",
        ], [])],
        "readables": [
            ("A cooling rack of glass", (254, 188), [
                "Lamps, dozens of them, with heavy bases and wire cages: miner's lamps. Each base is stamped D.M.C. One, at the end, has a tiny sun scratched inside its glass where nobody would see it.",
            ]),
        ],
    },
    "duskara_rafi": {
        "town": "res://scenes/world/duskara.tscn",
        "name": "Rafi's House",
        "image": "assets/sprites/tiles/duskara/interiors/home_room.png",
        "size": (320, 256),
        "exit": (160, 250), "back_to": "from_houserafi", "spawn": (160, 220),
        "blocks": [
            (0, 0, 320, 105), (14, 118, 92, 175), (52, 96, 96, 118), (60, 175, 120, 230),  # back wall, the bed, baskets, the loom
            (8, 168, 40, 196), (38, 196, 60, 222),                                         # baskets
            (230, 88, 290, 145), (270, 130, 310, 190), (284, 148, 312, 192),              # water jars, the urn
            (182, 138, 240, 162), (186, 218, 255, 250),                                    # the tea table, sacks by the door
            (0, 190, 30, 256), (290, 190, 320, 256), (0, 246, 138, 256), (182, 246, 320, 256),
        ],
        "npcs": [("rafi", "Rafi", "rafi", (150, 170), [
            "Ah! A visitor. Sit, sit. Tea? It's mostly sand, but it's hot.",
            "Two bedrolls? My cousin visits. Often. She has a lot of cousins.",
            "If anyone from the terrace asks, I sell water and I go to bed early. Both true. Mostly true.",
        ], [], {"out": (21.0, 6.0)})],
        "readables": [
            ("The roof hatch", (112, 112), [
                "A rope ladder up to a hatch in the roof. On the ledge beside it: a lamp with a green-tinted glass, the wick trimmed, a box of matches. From the roof, a green light would be seen a long way across the dunes.",
            ]),
            ("Bedrolls behind the jars", (250, 150), [
                "Behind the big water jars, rolled tight and tied: four small bedrolls, each about the length of a child. Clean, and recently used.",
            ]),
        ],
    },
    # ---- Vetrassa (outdoors: build_region.py) ----
    "vetrassa_palace": {
        "town": "res://scenes/world/vetrassa.tscn",
        "name": "The Throne Room",
        "image": "assets/sprites/tiles/vetrassa/interiors/throne_room.png",
        "size": (320, 256),
        "exit": (160, 250), "back_to": "from_housepalace", "spawn": (160, 222),
        "blocks": [
            (0, 0, 320, 82), (64, 0, 92, 108), (228, 0, 256, 108),                     # back wall, the inner pillars
            (146, 58, 172, 104), (180, 76, 198, 108),                                   # the throne, the lectern with the set
            (52, 104, 76, 232), (244, 104, 268, 232),                                   # the front pillars
            (97, 92, 113, 112), (209, 92, 225, 112), (80, 152, 97, 180), (225, 152, 242, 180),
            (80, 200, 97, 222), (225, 200, 242, 222),                                   # braziers
            (0, 80, 50, 200), (270, 80, 320, 200),                                      # the side walls: vases, the chest, armour
            (0, 190, 60, 256), (262, 190, 320, 256), (36, 190, 52, 214),
            (138, 214, 145, 256), (175, 214, 182, 256),                                 # the door frame
            (0, 246, 140, 256), (180, 246, 320, 256),
        ],
        "npcs": [("steward", "The Steward of the Set", "steward", (208, 126), [
            "Welcome to the throne room. You have the look of a racer: tired, and certain.",
            "I keep the set. Every race, someone brings it up those steps, and every race I check it card by card. It is the only part of my work I enjoy.",
            "The throne has been empty for some time. His Majesty travels. He always has, in a race year.",
            "What is owed to the winner? Everything that was promised, and nothing that wasn't. I'm afraid that's all I'm permitted to say.",
        ], [])],
        "readables": [
            ("The empty throne", (159, 116), [
                "A high gold throne on a raised step, its blue cushion worn into the shape of whoever sat in it last. There's dust on the arms. Nobody has sat here in a long while.",
            ]),
            ("The Throne Ledger", (189, 118), [
                "A great book on the lectern by the throne, chained to it. The King's own record: every race, every winner, every king. The first page is in a hand older than the island's roads.",
                "'The set is gathered from the land, and the land gives what is taken from it.' Then, every race since: 'Seam worked. Count true.' The last entry is in a familiar hand, signed L.",
            ]),
        ],
    },
    "vetrassa_restaurant": {
        "town": "res://scenes/world/vetrassa.tscn",
        "name": "Chef's",
        "image": "assets/sprites/tiles/vetrassa/interiors/dining_room.png",
        "size": (320, 256),
        "exit": (158, 250), "back_to": "from_houserestaurant", "spawn": (158, 222),
        "blocks": [
            (0, 0, 320, 62), (0, 58, 52, 140), (68, 60, 146, 126),                      # back wall, the stair, the private alcove
            (160, 56, 320, 116), (226, 116, 300, 172), (296, 116, 320, 200),            # the kitchen, the bar, the shelves
            (48, 136, 100, 176), (140, 140, 188, 180), (56, 184, 100, 220), (236, 184, 280, 220),  # tables
            (8, 140, 30, 190), (290, 140, 312, 190), (78, 192, 100, 240), (222, 192, 246, 240),    # bay trees
            (116, 196, 130, 232), (186, 196, 200, 232), (204, 208, 222, 240),           # lanterns, the lectern
            (0, 190, 56, 256), (264, 190, 320, 256), (0, 246, 136, 256), (182, 246, 320, 256),
        ],
        "npcs": [("chef", "Chef", "chef", (204, 130), [
            "Welcome to Chef's. Yes, that's the name. When you're the best, you don't need another one.",
            "My stew? Pepper at Seabright makes it with my recipe and my saffron and somehow it's still not mine. A recipe is a map. Cooking is the walking.",
            "The Duke dines here every night he's in Vetrassa. Him and his 'Company' friends, in the alcove, behind the curtain. They tip extravagantly. I hear everything.",
            "My father taught me to cook. Then he taught me to keep secrets. I'm much better at the first one.",
            "Tally in Verdana keeps sending me letters about gravy. I wrote back once, to be polite. I said her gravy was honest. I meant it.",
            "My little brother hasn't come home in years. My mother says he's ungrateful. I say he's the only one of us who walked out of the kitchen when it got too hot.",
        ], [])],
        "readables": [
            ("The private alcove", (106, 134), [
                "A table for three behind a velvet curtain, laid with the best silver. A card on the cloth: 'Reserved. The Duke and guests. To the Company's account.'",
                "Under the table, a napkin with figures pencilled on it: tonnages, and a route through 'the shoulder', and a name crossed out: Halmeer.",
            ]),
            ("Tonight's menu", (210, 244), [
                "'CHEF'S. Saffron stew of the north. Lemon tart. Roast of the King's own herd.' At the bottom, in Chef's hand: 'No substitutions. No exceptions. No Company tabs after the race.'",
            ]),
        ],
    },
    "vetrassa_inn": {
        "town": "res://scenes/world/vetrassa.tscn",
        "name": "The Crown & Anchor",
        "image": "assets/sprites/tiles/vetrassa/interiors/inn_room.png",
        "size": (320, 256),
        "exit": (158, 250), "back_to": "from_houseinn", "spawn": (158, 222),
        "blocks": [
            (0, 0, 320, 92), (130, 40, 188, 108), (0, 58, 90, 128),                     # back wall, the hearth, the stair
            (126, 132, 196, 166), (48, 136, 104, 172), (8, 140, 30, 190),               # tables, a plant
            (226, 96, 300, 176), (290, 60, 320, 200),                                   # the bar, the shelves
            (28, 192, 112, 250), (204, 200, 270, 250),                                  # barrels and crates, sacks and the tree
            (116, 196, 130, 232), (186, 196, 200, 232),                                 # lanterns by the door
            (0, 190, 30, 256), (290, 190, 320, 256), (0, 246, 136, 256), (182, 246, 320, 256),
        ],
        "npcs": [("brigid", "Brigid", "brigid", (210, 152), [
            "In you come, out of the wind! Vetrassa's wind comes straight off the sea and goes straight through you. Sit by the fire.",
            "Every racer ends up at the Crown & Anchor. The winners for one night, the losers for a week.",
            "The palace? Up the grand stairs. The Steward checks every card. He once sent a racer away for a bent corner.",
            "Freya drinks here when she's off the steps. Quiet as stone. She's waiting for something, that one, and it isn't a racer.",
            "The Duke's men drink here too, on the Company's tab. I charge them double and the Company pays it without blinking. Makes you wonder how rich the ground is.",
            "My rooms are warm and my beds are long. Half a day or a whole one, and you'll walk up those stairs mended.",
        ], [])],
        "inn": "brigid",
        "keeper": {"wake_lines": [
                       "Easy, easy. The guard carried you in off the square. The whole town saw. Don't worry, they've seen worse.",
                       "There you are. You were out cold on the quay. I put you by the fire and told everyone you were resting your eyes.",
                   ],
                   "room_prompt": "A long bed and a warm stone. Half a day, or the whole day?",
                   "room_broke": "It's %d gold, love. Sit by the fire as long as you like, though; that's free."},
        "readables": [
            ("The racers' wall", (212, 106), [
                "Over the bar, names scratched into the stone: racers of past years. Next to some, a little crown. Every crowned name is a different hand. None of them is a name anyone in town remembers.",
            ]),
        ],
    },
    # ---- Halmeer (outdoors: build_region.py) ----
    "halmeer_inn": {
        "town": "res://scenes/world/halmeer.tscn",
        "name": "The Gull's Rest",
        "image": "assets/sprites/tiles/halmeer/interiors/inn_room.png",
        "size": (320, 256),
        "exit": (160, 250), "back_to": "from_houseinn", "spawn": (160, 220),
        "blocks": [
            (0, 0, 320, 78), (0, 0, 36, 256), (284, 0, 320, 256),                       # back wall, the side walls
            (104, 20, 158, 100), (88, 70, 106, 94),                                      # the hearth, a barrel by it
            (36, 60, 100, 146), (36, 130, 90, 160), (36, 166, 80, 208),                  # the stair, barrels
            (120, 128, 154, 160), (100, 172, 138, 206),                                  # the two tables
            (216, 96, 232, 152), (216, 140, 284, 162), (250, 86, 284, 140),              # the bar, the shelves behind it
            (220, 186, 284, 208),                                                        # sacks and crates
            (0, 208, 144, 256), (176, 208, 320, 256),                                    # the front wall round the door
        ],
        "npcs": [("maudie", "Maudie", "maudie", (196, 150), [
            "Come in, shut the door, the wind's got teeth tonight. It's always got teeth. Welcome to the Gull's Rest.",
            "Fish stew, fish pie, or bread with fish in it. We had a cook once who tried soup without fish. We don't talk about him.",
            "My Tom went out on one of the dark nights, three winters back. Said the Company paid double for a hand on the barge. The barge came back. He didn't.",
            "Nessa on the cape keeps the light. Mostly. You can tell the dark nights: the whole village goes to bed early and pulls the shutters.",
            "Racers! We get one a year, maybe. Most of you come for the cape chest and leave before supper. Stay for supper.",
            "The Company man, Grisel, eats in that corner every night with his ledger. Doesn't drink. Doesn't talk. Tips well. I don't trust any of it.",
            "My rooms look out over the harbour. Half a day or the whole day; you'll sleep, the sea'll see to that.",
        ], [])],
        "inn": "maudie",
        "keeper": {"wake_lines": [
                       "There you are. Ferro carried you up off the quay like a wet net. You're in the Gull's Rest. Lie still.",
                       "You gave us a turn. Out cold on the cliff road. Drink this, it's mostly fish.",
                   ],
                   "room_prompt": "A bed by the window and the sea to sing you down. Half a day, or the whole day?",
                   "room_broke": "That's %d gold, love. Sit by the fire as long as you like, mind; the fire's free."},
        "readables": [
            ("The chalkboard behind the bar", (196, 104), [
                "Today's catch, in chalk. Below it, a list of names with ticks: who owes for drink. And at the bottom, smaller: 'Dark night Thursday. Shutters.'",
            ]),
        ],
    },
    "halmeer_lighthouse": {
        "town": "res://scenes/world/halmeer.tscn",
        "name": "The Cape Light",
        "image": "assets/sprites/tiles/halmeer/interiors/lighthouse_room.png",
        "size": (320, 256),
        "exit": (158, 250), "back_to": "from_houselighthouse", "spawn": (158, 220),
        "blocks": [
            (0, 0, 320, 64), (0, 0, 40, 256), (280, 0, 320, 256),                        # the round wall
            (40, 0, 70, 90), (250, 0, 280, 90),
            (0, 200, 60, 256), (60, 215, 140, 256), (176, 215, 260, 256), (260, 200, 320, 256),
            (78, 48, 154, 100), (162, 20, 202, 140), (206, 72, 240, 104),                # the bed, the spiral stair, barrels
            (238, 66, 286, 150), (270, 128, 290, 165),                                   # the shelves, the tools
            (32, 84, 100, 148), (46, 152, 82, 196), (88, 170, 118, 214),                 # the desk, the rocking chair, the stove
            (210, 170, 286, 214),                                                        # crates and barrels
        ],
        "npcs": [("nessa", "Nessa", "nessa", (140, 160), [
            "Mind the stair, it's older than me and less forgiving. Forty years I've kept this light.",
            "A light's a promise. Whoever's out there, whatever they're carrying, you tell them where the rocks are. That's the whole job.",
            "My knees won't do the cut down to the sea cave any more. My ears still work. I hear oars under the cape on the dark nights.",
            "The Company pays well. That's the trouble with them. They always pay well.",
        ], [])],
        "readables": [
            ("The keeper's log", (108, 118), [
                "Forty years of weather in a neat hand. 'Wind SW, light lit, all well.' Then, three winters back, every few weeks: 'Light dark. By order.' And once, underlined: 'Oars. Many.'",
            ]),
            ("The tide chart", (222, 112), [
                "A chart of the cape's waters pinned to the wall. Someone has drawn a dotted line from the sea cave under the cape, round the reef, and off the edge of the chart, south. No harbour is marked at the end of it.",
            ]),
        ],
    },
    "halmeer_cave": {
        "town": "res://scenes/world/halmeer.tscn",
        "name": "The Sea Cave",
        "image": "assets/sprites/tiles/halmeer/interiors/sea_cave.png",
        "size": (320, 256),
        "exit": (165, 206), "back_to": "from_housecave", "spawn": (165, 160),
        "blocks": [
            (0, 0, 320, 20), (0, 0, 50, 256), (272, 0, 320, 256), (248, 30, 272, 100),  # the rock walls
            (40, 20, 190, 100), (40, 100, 104, 130),                                     # the water and the moored barge
            (214, 52, 246, 100),                                                         # crates on the landing stage
            (104, 112, 150, 150), (196, 116, 240, 148),                                  # crates, the chart table
            (48, 146, 64, 180), (56, 176, 96, 214), (248, 190, 272, 210),               # barrels, crates, a bench
            (0, 214, 124, 256), (206, 214, 320, 256), (124, 172, 146, 256), (186, 172, 206, 256),  # the rock arch
        ],
        "npcs": [],
        "readables": [
            ("The barge's log", (218, 158), [
                "A logbook on the chart table, damp at the edges. 'Loaded at the Halmeer landing: uncut, D.M.C., 40 crates. Out on the dark tide, round the reef, to the mainland ship.'",
                "Earlier pages trace the same crates back: 'Received from Vetrassa factors. Received at Frisalle by the ice road. Received from the North Shaft.' The whole island, crate by crate, out of this cave.",
            ]),
            ("D.M.C. crates", (124, 160), [
                "Crates stamped like the ones on every quay of the island. Prised open: uncut cards in straw, thousands of them. A tally tag is caught in the straw of one. Small.",
            ]),
            ("The landing stage", (222, 112), [
                "Planks laid out over the black water to the barge. A rope cleat with a cut rope end still tied to it, in a knot nobody in Halmeer will admit to knowing.",
            ]),
        ],
    },
}


def keeper_props(cfg):
    """The inn keeper's extra properties: rooms, supplies (food and tonics, no card
    trading), their own way of offering a bed, and a meal hour if they keep one."""
    q = lambda text: '"' + text.replace('"', '\\"') + '"'
    arr = lambda lines: "PackedStringArray(" + ", ".join(q(line) for line in lines) + ")"
    k = cfg.get("keeper", {})
    out = "inn_rooms = true\n"
    stock = INN_STOCK[:-1] + "".join(f', &"{x}"' for x in k.get("extra_stock", [])) + "]"
    out += f"shop_stock = Array[StringName]({stock})\nshop_buys_cards = false\nshop_title = {q(cfg['name'])}\n"
    if k.get("wake_lines"):
        out += f"wake_lines = {arr(k['wake_lines'])}\n"
    if k.get("room_prompt"):
        out += f"room_prompt = {q(k['room_prompt'])}\n"
    if k.get("room_broke"):
        out += f"room_broke = {q(k['room_broke'])}\n"
    if k.get("meal_hour") is not None:
        out += f"meal_hour = {k['meal_hour']}\nmeal_lines = {arr(k['meal_lines'])}\npre_meal_lines = {arr(k['pre_meal_lines'])}\n"
    return out


def scaled(cfg, k=ROOM_SCALE):
    """The config in zone coordinates: every position and rect multiplied by k."""
    pt = lambda p: (p[0] * k, p[1] * k)
    out = dict(cfg)
    out["size"] = pt(cfg["size"])
    out["exit"], out["spawn"] = pt(cfg["exit"]), pt(cfg["spawn"])
    out["blocks"] = [tuple(v * k for v in b) for b in cfg["blocks"]]
    out["npcs"] = [(e[0], e[1], e[2], pt(e[3])) + tuple(e[4:]) for e in cfg["npcs"]]
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
    for entry in cfg["npcs"]:
        npc_id, display, sprite_id, (x, y), lines, stock = entry[:6]
        extra = entry[6] if len(entry) > 6 else {}
        rid = f"n_{sprite_id}"
        ext.append(('SpriteFrames', f"res://assets/sprites/npcs/{sprite_id}/{sprite_id}_frames.tres", rid))
        quoted = ", ".join('"' + line.replace('"', '\\"') + '"' for line in lines)
        n.append(f'[node name="Npc_{npc_id}" parent="." instance=ExtResource("9_npc")]\nposition = Vector2({x}, {y})\n'
                 f'npc_id = &"{npc_id}"\ndisplay_name = "{display}"\nsprite_frames = ExtResource("{rid}")\n'
                 f'lines = PackedStringArray({quoted})\n' + (f'shop_stock = Array[StringName]({stock})\n' if stock else "")
                 + ('shop_buys_cards = false\nshop_title = "Greta\'s Provisions"\n' if stock == PROVISIONS else "")
                 + (keeper_props(cfg) if cfg.get("inn") == npc_id else "")
                 # Indoors only part of the day (the resident's outdoor copy has the rest).
                 + (f'out_from = {float(extra["out"][0])}\nout_to = {float(extra["out"][1])}\n' if extra.get("out") else ""))
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
