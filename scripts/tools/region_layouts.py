"""Layouts for the regions past Kalmora's west gate, built by build_region.py.

All positions are zone-local px. The island map (docs/reference/virelia_map.webp):
the Aurewind Plains lie west of Kalmora, gold and green, with Verdana in their south
and the old standing stones on the downs; Lake Serin lies north of the plains, and
the Starfall Range rises north of the lake, its pass to Frisalle snowed shut.
Exits line up with WorldMap.ZONES origins (scripts/world/world_map.gd).

"Stones That Remember" (Aldous, Verdana) sends you to the three stones: the circle
on the Stonewatch Downs, the stone on Stone Point and the Starfall stone (Readables
titled as in Quests.STONES).
"""
import math

from build_region import in_poly

K2 = "assets/sprites/tiles/kalmora2/"
KP = "assets/sprites/tiles/kalmora/props/"
TV = "assets/sprites/tiles/thornveil/props/"
AW = "assets/sprites/tiles/aurewind/"
VD = "assets/sprites/tiles/verdana/"
LS = "assets/sprites/tiles/lake_serin/"
SF = "assets/sprites/tiles/starfall/"
RAM = "res://scenes/characters/bristle_ram.tscn"
WOLF = "res://scenes/characters/frost_wolf.tscn"
BOAR = "res://scenes/characters/moss_boar.tscn"
HOUND = "res://scenes/characters/briar_hound.tscn"
STONE = AW + "standing_stone.png"
ALTAR = AW + "stone_altar.png"
HAY = AW + "hay_bale.png"
SCARECROW = AW + "scarecrow.png"
FENCE = KP + "fence.png"
BOULDER = K2 + "props/boulder.png"


def wob(x, y, amp=28):
    return amp * math.sin(x / 97.0 + 0.3) + amp * 0.6 * math.sin(y / 61.0 + 1.1)


def fence_row(x0, x1, y, gap_at=()):
    return [{"sprite": FENCE, "pos": (x, y), "foot": (16, 6)}
            for x in range(x0, x1 + 1, 16) if all(abs(x - g) > 24 for g in gap_at)]


def ring(cx, cy, r, count, sprite, foot, start=0.3):
    return [{"sprite": sprite, "pos": (round(cx + math.cos(start + k * math.tau / count) * r),
                                       round(cy + math.sin(start + k * math.tau / count) * r * 0.7)), "foot": foot}
            for k in range(count)]


# ---------------------------------------------------------------- Aurewind Plains
STONEWATCH = [(-1300, -1000), (-150, -1000), (-180, -700), (-380, -500), (-700, -430), (-1000, -470), (-1300, -420)]
KESTREL = [(450, -1000), (1300, -1000), (1300, -500), (1050, -460), (800, -520), (560, -620)]


def aurewind_level(x, y):
    px, py = x + wob(x, y), y + wob(y, x, 22)
    return 2 if in_poly(px, py, STONEWATCH) or in_poly(px, py, KESTREL) else 1


CIRCLE = (-700, -700)

AUREWIND = {
    "scene": "scenes/world/aurewind_plains.tscn",
    "root": "AurewindPlains",
    "display": "Aurewind Plains, the Golden Downs",
    "art": AW,
    "bounds": (-1216, -896, 1216, 864),
    "cliff": "assets/sprites/tiles/thornveil/cliff/forest_terrace",
    "level": aurewind_level,
    "tall_walls": {(1, 2): 1},
    "stairs": [(-620, -450, 1, 2), (900, -496, 1, 2)],
    "grade": (1.0, (1.0, 1.0, 1.0)),
    "palette": ((96, 132, 56), (176, 160, 78)),
    "paths": [
        ([(1240, 40), (900, 60), (600, 20), (200, 0), (-200, 60), (-600, 120), (-1000, 140), (-1140, 140)], 30),  # the King's Road
        ([(200, 0), (160, -400), (150, -920)], 24),                         # north, to Lake Serin
        ([(-200, 60), (-350, 400), (-500, 890)], 24),                       # south-west, to Verdana
        ([(-400, 90), (-560, -200), (-600, -380), (-640, -560)], 18),       # up to the stone circle
        ([(700, 40), (860, -250), (900, -420), (900, -650)], 18),           # up Kestrel Rise
        ([(600, 20), (700, 300), (760, 560)], 16),                          # the farm lane
    ],
    "fields": [(820, 200, 1100, 380), (820, 440, 1100, 620), (470, 560, 700, 720)],
    "lakes": [(150, 470, 200, 110)],
    "tree_kinds": ["oak", "oak", "fir"],
    "groves": [(-300, -180, 6, 50), (480, -300, 7, 60), (-820, 620, 10, 70), (350, 760, 5, 50), (-1000, -120, 8, 60),
               (-950, -760, 6, 60), (1100, -760, 6, 50)],
    "under": [("flowers", 4), ("grass_clump", 6), ("clover", 3), ("berry_bush", 1), ("rock", 1), ("stump", 1)],
    "patches": 90,
    "tufts": 260,
    "tuft_tint": (1.08, 1.0, 0.8, 1),
    "entry": (1160, 40),
    "exits": [
        {"name": "ToKalmora", "pos": (1236, 40), "side": "e", "target": "res://scenes/world/kalmora.tscn", "spawn": "from_aurewind"},
        {"name": "ToLakeSerin", "pos": (150, -916), "side": "n", "target": "res://scenes/world/lake_serin.tscn", "spawn": "from_aurewind"},
        {"name": "ToVerdana", "pos": (-500, 884), "side": "s", "target": "res://scenes/world/verdana.tscn", "spawn": "from_aurewind"},
    ],
    "spawns": {"from_kalmora": (1160, 40), "from_lake_serin": (150, -840), "from_verdana": (-500, 820)},
    "rival_spots": {"runner": (1100, 0), "raider": (1100, 80), "hoarder": (1060, 40)},
    "buildings": [
        {"node": "WorkingBarn", "sprite": VD + "barn.png", "pos": (1000, -110), "foot": 130},
    ],
    "props": (
        # The stone circle on the Stonewatch Downs, the altar in the middle.
        ring(CIRCLE[0], CIRCLE[1], 120, 8, STONE, (26, 12))
        + [{"sprite": ALTAR, "pos": (CIRCLE[0], CIRCLE[1] + 10), "foot": (56, 16), "light": ((0.7, 0.85, 1.0, 1), 0.35, 1.2)}]
        # The Hensley farm: hay by the barn, scarecrows in the wheat, fences along the fields.
        + [{"sprite": HAY, "pos": p, "foot": (34, 14)} for p in [(870, -80), (900, -40), (1130, -60), (820, 160)]]
        + [{"sprite": SCARECROW, "pos": p, "foot": (10, 6)} for p in [(960, 300), (580, 640)]]
        + fence_row(820, 1100, 190, gap_at=(900,)) + fence_row(820, 1100, 630, gap_at=(1000,))
        # The dune road, closed: a rockfall across it and a broken ore cart.
        + [{"sprite": BOULDER, "pos": p, "foot": (40, 18), "scale": 1.4} for p in [(-1180, 104), (-1170, 146), (-1186, 190), (-1140, 124)]]
        + [{"sprite": KP + "cart.png", "pos": (-1080, 206), "foot": (44, 14), "flip": True}]
        # The travellers' camp.
        + [{"sprite": TV + "tent.png", "pos": (-120, 300), "foot": (60, 20)}]
        + [{"sprite": KP + "signpost.png", "pos": (-240, 120), "foot": (8, 6)}]
    ),
    "campfires": [(-30, 330)],
    "lanterns": [(-300, 20), (420, -30), (820, 110), (-820, 80), (-640, -520), (120, -330)],
    "npcs": [
        {"id": "tilly", "name": "Tilly", "pos": (-150, -140), "wander": 50, "lines": [
            "Mind the rams. They're mine, mostly. The ones with the bristles on their backs aren't anyone's.",
            "The stones up on the downs hum when the wind's in the east. Grandad says they're counting.",
            "Wagons used to come east along the dune road every week. Covered, always. Then the rocks came down and they stopped. Or they go some other way now.",
        ]},
    ],
    "readables": [
        ("The Aurewind circle", (CIRCLE[0], CIRCLE[1] + 40), [
            "Eight standing stones round a flat altar, older than any road on the island. The altar's face is carved with a crown and, under it, a long line of small figures, each one smaller than the last.",
            "Someone has laid fresh wheat on the altar. Someone else has scratched a tally beside the figures. The scratches are new.",
        ]),
        ("The dune road", (-1060, 250), [
            "A signpost, freshly painted: 'SIROTH DUNES - DUSKARA. ROAD CLOSED BY ORDER OF THE DUSKARA MINING COMPANY. ROCKFALL.'",
            "The rocks across the road sit on wheel ruts. Rockfalls don't come on carts.",
        ]),
        ("A broken ore cart", (-1020, 230), [
            "An ore cart with a split axle, left where it broke. No ore in it: straw, a water skin, and a length of chain with small cuffs.",
            "Stencilled on the side: 'D.M.C. - RETURN EMPTY'.",
        ]),
        ("A wayside shrine", (-60, -20), [
            "A little cairn of stacked stones by the King's Road, heaped with wheat and ribbons. A board says: 'For the ones who walked west.'",
            "Nobody has written who they were.",
        ]),
    ],
    "chests": [
        {"id": "camp_pack", "pos": (-190, 330), "gold": 15, "item": "bread", "count": 2},
        {"id": "kestrel_cache", "pos": (900, -720), "gold": 40, "card": "sunken_crown_shard"},
        {"id": "circle_offering", "pos": (-560, -600), "gold": 25, "item": "healers_tonic"},
        {"id": "hay_loft", "pos": (1150, -30), "gold": 10, "item": "bread"},
    ],
    "monsters": [(RAM, (420, -180)), (RAM, (-220, -330)), (RAM, (-700, 380)), (RAM, (300, 700)), (RAM, (-950, -640)),
                 (HOUND, (-1000, 520)), (HOUND, (620, 780))],
    "butterflies": [((950, 300), 4), ((-600, -700), 3), ((150, 300), 3), ((-400, 600), 3)],
}

# ---------------------------------------------------------------- Verdana
UPPER_GREEN = [(250, -760), (900, -760), (900, -130), (600, -110), (300, -210)]


def verdana_level(x, y):
    return 2 if in_poly(x + wob(x, y, 14), y + wob(y, x, 10), UPPER_GREEN) else 1


VERDANA = {
    "scene": "scenes/world/verdana.tscn",
    "root": "Verdana",
    "display": "Verdana, Town of the Long Harvest",
    "art": VD,
    "bounds": (-832, -640, 832, 576),
    "cliff": "assets/sprites/tiles/thornveil/cliff/forest_terrace",
    "level": verdana_level,
    "tall_walls": {(1, 2): 1},
    "stairs": [(420, -170, 1, 2)],
    "grade": (1.0, (1.0, 1.0, 1.0)),
    "palette": ((92, 136, 58), (150, 152, 70)),
    "paths": [
        ([(-200, -660), (-230, -420), (-140, -140), (0, 20)], 26),          # the north road, down from the plains
        ([(0, -60), (0, -210)], 22),                                         # to the inn door
        ([(-120, 20), (-300, -40), (-460, -100)], 18),                       # to the farmhouse
        ([(-100, 140), (-330, 260), (-560, 300)], 18),                       # to the barn
        ([(100, 140), (300, 250), (470, 350)], 18),                          # to the windmill
        ([(140, -20), (420, -110), (420, -180)], 18),                        # to the stairs
        ([(430, -260), (600, -300), (620, -320)], 16),                       # up on the green, to the scholar's door
    ],
    "plazas": [(0, 60, 250, 150)],                                           # the square, cobbled
    "instances": [("res://scenes/world/props/forest_oak.tscn", (0, 50), 1)],  # the Harvest Oak
    "fields": [(-790, -40, -640, 200), (-790, 360, -640, 540), (560, 380, 800, 540), (-420, 400, -220, 540)],
    "tree_kinds": ["oak"],
    "groves": [(-700, -500, 5, 50), (760, 200, 4, 40), (300, -560, 4, 40), (-40, 480, 3, 30)],
    "under": [("flowers", 6), ("grass_clump", 4), ("clover", 3), ("berry_bush", 1)],
    "patches": 40,
    "tufts": 90,
    "tuft_tint": (1.05, 1.0, 0.85, 1),
    "safe_zone": (-832, -640, 832, 576),
    "entry": (-200, -600),
    "exits": [
        {"name": "ToAurewind", "pos": (-200, -660), "side": "n", "target": "res://scenes/world/aurewind_plains.tscn", "spawn": "from_verdana"},
    ],
    "spawns": {"town": (0, 120), "from_aurewind": (-200, -600)},
    "rival_spots": {"runner": (-80, 150), "raider": (90, 150), "hoarder": (60, -40)},
    "buildings": [
        {"node": "HouseInn", "sprite": VD + "inn.png", "pos": (0, -230), "foot": 150, "door": "res://scenes/world/interiors/verdana_inn.tscn",
         "back": "from_houseinn"},
        {"node": "HouseFarm", "sprite": VD + "farmhouse.png", "pos": (-460, -120), "foot": 140, "door": "res://scenes/world/interiors/verdana_farmhouse.tscn",
         "back": "from_housefarm"},
        {"node": "HouseScholar", "sprite": VD + "scholar_house.png", "pos": (620, -330), "foot": 124, "door": "res://scenes/world/interiors/verdana_scholar.tscn",
         "back": "from_housescholar"},
        {"node": "WorkingBarn", "sprite": VD + "barn.png", "pos": (-560, 290), "foot": 130},
        {"node": "WorkingMill", "sprite": K2 + "objects/windmill2.png", "pos": (480, 340), "foot": 90,
         "sails": (K2 + "anim/windmill_sails.png", 12, 7, (80, 78))},
    ],
    "props": (
        [{"sprite": "assets/sprites/tiles/sorenda/sorenda_well.png", "pos": (-215, 20), "foot": (40, 14)}]
        + [{"sprite": K2 + "props/stall_bread.png", "pos": (-150, 150), "foot": (54, 14)},
           {"sprite": K2 + "props/stall_fruit.png", "pos": (150, 150), "foot": (54, 14)},
           {"sprite": KP + "bread_basket.png", "pos": (-110, 160), "foot": (14, 6)},
           {"sprite": KP + "apples_crate.png", "pos": (190, 160), "foot": (16, 8)},
           {"sprite": K2 + "props/bench.png", "pos": (-120, -40), "foot": (36, 8)},
           {"sprite": K2 + "props/bench.png", "pos": (120, -40), "foot": (36, 8)},
           {"sprite": K2 + "props/flower_bed.png", "pos": (-90, -170), "foot": (30, 8)},
           {"sprite": K2 + "props/flower_bed.png", "pos": (90, -170), "foot": (30, 8)},
           {"sprite": K2 + "props/notice_board.png", "pos": (-190, -60), "foot": (30, 8)}]
        + [{"sprite": HAY, "pos": p, "foot": (34, 14)} for p in [(-420, 330), (-690, 300), (-460, 360)]]
        + [{"sprite": SCARECROW, "pos": p, "foot": (10, 6)} for p in [(-720, 80), (680, 460)]]
        + fence_row(-790, -640, -52) + fence_row(-790, -640, 212) + fence_row(560, 800, 372, gap_at=(680,))
    ),
    "lanterns": [(-230, -20), (230, -20), (-230, 170), (230, 170), (-200, -380), (380, -120), (560, -280), (-380, -60), (380, 280),
                 (-60, 110), (60, 110)],
    "npcs": [
        {"id": "aldous", "name": "Aldous", "pos": (620, -270), "wander": 20, "lines": [
            "The stones were here before the kings. Before the towns. Before, I think, the cards.",
            "I've spent forty years reading what's carved on them. It's the same story on every one, told smaller each time.",
        ]},
        {"id": "marta", "name": "Marta", "pos": (-400, -60), "wander": 40, "lines": [
            "Harvest's in early. Half of it's sold before it's cut, to the Company men from Duskara. Paid in scrip.",
            "Scrip spends at the Company store and nowhere else. Funny, that.",
        ]},
        {"id": "bruno", "name": "Bruno", "pos": (70, -180), "wander": 20, "shop": ["bread", "smoked_fish", "healers_tonic"],
         "shop_title": "The Sheaf & Sickle", "lines": [
            "Welcome to the Sheaf and Sickle! Warm bread, cold cider, and beds that don't have racers in them. Usually.",
            "The last racer through here paid in cards. I don't want cards. I want a quiet life and a full cellar.",
        ]},
    ],
    "readables": [
        ("The harvest board", (-190, -30), [
            "WANTED: HANDS FOR THE DUSKARA WORKS. Small hands preferred for close work. Room, board and a trade. Apply to the Company agent, first of the month.",
            "Somebody has written underneath, in pencil: 'none of ours'. Somebody else has crossed it out.",
        ]),
        ("The mill ledger", (430, 380), [
            "A ledger nailed up by the mill door. 'Flour to D.M.C.: 200 sacks. Rate: one third market, by agreement.'",
            "'By agreement' is underlined twice, hard enough to tear the page.",
        ]),
        ("A stone by the scholar's door", (680, -300), [
            "A fragment of a standing stone, set upright by the door. The same carving as the circle on the downs: a crown, and under it a line of figures, each one smaller.",
        ]),
    ],
    "chests": [
        {"id": "barn_loft", "pos": (-700, 240), "gold": 20, "item": "bread"},
    ],
    "butterflies": [((0, 60), 3), ((-700, 100), 3), ((680, 460), 3)],
}

# ---------------------------------------------------------------- Lake Serin
HERON_BLUFFS = [(-1100, -900), (-560, -900), (-600, -400), (-700, -100), (-760, 300), (-1100, 320)]


def serin_level(x, y):
    return 2 if in_poly(x + wob(x, y, 20), y + wob(y, x, 16), HERON_BLUFFS) else 1


LAKE_SERIN = {
    "scene": "scenes/world/lake_serin.tscn",
    "root": "LakeSerin",
    "display": "Lake Serin, the Still Water",
    "art": LS,
    "bounds": (-1024, -768, 1024, 768),
    "cliff": "assets/sprites/tiles/thornveil/cliff/forest_terrace",
    "level": serin_level,
    "tall_walls": {(1, 2): 1},
    "stairs": [(-900, 310, 1, 2)],
    "grade": (1.0, (1.0, 1.0, 1.0)),
    "palette": ((64, 112, 64), (104, 136, 68)),
    "paths": [
        ([(700, 790), (650, 450), (720, 100), (650, -400), (200, -560), (-300, -790)], 26),   # round the east shore, north to the Range
        ([(40, -470), (60, -250)], 18),                                     # out onto Stone Point
        ([(720, 60), (660, -60), (560, -74)], 16),                          # to Neri's dock
        ([(-300, -700), (-600, 0), (-900, 360), (-900, 250)], 18),          # the west trail to the bluffs
        ([(-900, 180), (-860, -300)], 14),                                  # up on the bluffs
    ],
    "lakes": [(80, -40, 520, 300)],
    "land": [(60, -330, 90, 150)],
    "docks": [(470, -90, 640, -58)],
    "deep": (26, 72, 104),
    "water_tint": (0.9, 1.0, 1.12, 1),
    "tree_kinds": ["fir", "fir", "oak"],
    "groves": [(-850, -500, 10, 70), (-850, 0, 8, 60), (850, -500, 7, 60), (-500, 560, 8, 60), (350, 620, 6, 50), (880, 450, 5, 40)],
    "under": [("fern", 4), ("grass_clump", 4), ("flowers", 2), ("rock", 2), ("mushrooms", 1), ("log", 1)],
    "patches": 50,
    "tufts": 160,
    "entry": (700, 720),
    "exits": [
        {"name": "ToAurewind", "pos": (700, 788), "side": "s", "target": "res://scenes/world/aurewind_plains.tscn", "spawn": "from_lake_serin"},
        {"name": "ToStarfall", "pos": (-300, -788), "side": "n", "target": "res://scenes/world/starfall_range.tscn", "spawn": "from_lake_serin"},
    ],
    "spawns": {"from_aurewind": (700, 720), "from_starfall": (-300, -710)},
    "rival_spots": {"runner": (660, 660), "raider": (740, 660), "hoarder": (700, 620)},
    "buildings": [
        {"node": "HouseNeri", "sprite": LS + "fisher_hut.png", "pos": (820, -110), "foot": 120, "door": "res://scenes/world/interiors/serin_fisher_hut.tscn",
         "back": "from_houseneri"},
    ],
    "props": (
        [{"sprite": STONE, "pos": (60, -300), "foot": (26, 12), "scale": 1.2, "light": ((0.7, 0.85, 1.0, 1), 0.35, 1.0)}]
        + [{"sprite": KP + "barrel.png", "pos": (610, -100), "foot": (14, 8)}]
        + [{"sprite": KP + "net_crate.png", "pos": (740, -60), "foot": (24, 10)},
           {"sprite": KP + "fishing_rods.png", "pos": (700, -40), "foot": (14, 6)}]
        + [{"sprite": BOULDER, "pos": p, "foot": (40, 18)} for p in [(-380, 250), (330, 330)]]
    ),
    "lanterns": [(640, 420), (600, -140), (130, -470), (-420, -560)],
    "npcs": [
        {"id": "neri", "name": "Neri", "pos": (680, -20), "wander": 30, "lines": [
            "Serin's the stillest water on the island. You can hear a fish change its mind.",
            "Barges used to cross here at night, low in the water. Heading north. They don't cross any more. One of them never got across.",
        ]},
    ],
    "readables": [
        ("The stone on Stone Point", (60, -260), [
            "A lone standing stone at the tip of the point, the water all round it. The carving is the one from the circle: a crown, and a line of figures under it.",
            "Here the line goes on round the back of the stone. The last figures are no bigger than a thumbnail, and there are more of them than you can count.",
        ]),
        ("A drowned barge", (-380, 290), [
            "A flat barge, sunk at its mooring in the shallows. Its hold was lined with straw, and fitted with rings for chains.",
            "Stencilled on the stern, under the weed: 'D.M.C. - NORTH'.",
        ]),
        ("Neri's tally board", (760, -30), [
            "A board of chalk tallies: fish, by the day. On the back, a different tally, not fish. Barges crossing, by the night. It stops last spring.",
        ]),
    ],
    "chests": [
        {"id": "bluff_nest", "pos": (-850, -300), "gold": 35, "item": "sea_salt_elixir"},
        {"id": "reed_bed", "pos": (-470, 380), "item": "smoked_fish", "count": 2},
        {"id": "point_cache", "pos": (110, -420), "gold": 25},
    ],
    "monsters": [(BOAR, (-300, 330)), (BOAR, (320, 470)), (HOUND, (-200, -560)), (HOUND, (620, -600)), (RAM, (-40, 600))],
    "butterflies": [((600, 300), 3), ((-800, -200), 2)],
}

# ---------------------------------------------------------------- Starfall Range
def starfall_level(x, y):
    w = 44 * math.sin(x / 190.0) + 14 * math.sin(x / 70.0 + 1.0)
    if y + w > 150:
        return 0
    if y + w * 0.8 > -350:
        return 1
    return 2


STARFALL = {
    "scene": "scenes/world/starfall_range.tscn",
    "root": "StarfallRange",
    "display": "The Starfall Range, Road to Frisalle",
    "art": SF,
    "bounds": (-1024, -896, 1024, 768),
    "cliff": SF + "cliff/snow",
    "level": starfall_level,
    "tall_walls": {(0, 1): 1, (1, 2): 2},
    "stairs": [(-100, 150, 0, 1), (300, -350, 1, 2), (-700, 150, 0, 1)],
    "grade": (0.95, (1.0, 1.0, 1.04)),
    "dapple": 0.08,
    "snow": True,
    "snowfall": True,
    "paths": [
        ([(0, 790), (-60, 420), (-100, 200), (-100, 60), (100, -150), (300, -300), (300, -450), (0, -640), (-100, -820)], 24),
        ([(100, -150), (450, -60), (550, -60)], 16),                        # to the hermit's cabin
        ([(-100, 100), (-450, 40), (-700, 120), (-700, 250)], 16),          # round the tarn, down the west stairs
    ],
    "ice": [(-480, -120, 170, 90)],
    "tree_kinds": ["pine"],
    "groves": [(-800, -600, 8, 60), (700, -650, 8, 60), (-600, 520, 7, 60), (600, 420, 8, 60), (800, 0, 5, 50), (-850, -200, 5, 50)],
    "under": [("rock", 3), ("branch", 2), ("pinecones", 2), ("stump", 1)],
    "under_tint": (0.86, 0.92, 1.0, 1),
    "patches": 26,
    "entry": (0, 720),
    "exits": [
        {"name": "ToLakeSerin", "pos": (0, 788), "side": "s", "target": "res://scenes/world/lake_serin.tscn", "spawn": "from_starfall"},
    ],
    "spawns": {"from_lake_serin": (0, 720)},
    "rival_spots": {"runner": (-40, 660), "raider": (40, 660), "hoarder": (0, 620)},
    "buildings": [
        {"node": "HouseHald", "sprite": SF + "hermit_cabin.png", "pos": (620, -110), "foot": 130, "door": "res://scenes/world/interiors/starfall_cabin.tscn",
         "back": "from_househald"},
    ],
    "props": (
        # The pass to Frisalle: an avalanche across it, boulders and drifts twice your height.
        [{"sprite": BOULDER, "pos": (x, y), "foot": (40, 18), "scale": 1.6, "tint": (0.92, 0.96, 1.05, 1)}
         for x, y in [(-180, -840), (-130, -860), (-80, -845), (-30, -862), (20, -840), (-110, -815), (-50, -820)]]
        + [{"sprite": STONE, "pos": (120, -700), "foot": (26, 12), "scale": 1.3, "light": ((0.7, 0.85, 1.0, 1), 0.45, 1.2)}]
    ),
    "campfires": [(500, -40)],
    "lanterns": [(-80, 260), (330, -250), (-40, -600)],
    "npcs": [
        {"id": "hald", "name": "Hald", "pos": (540, -80), "wander": 30, "lines": [
            "Frisalle's over the pass. Nobody's crossed since the slide. Nobody's tried very hard.",
            "The slide came down the week after the last barge went north. The Company men were up here with powder the week before. Make of that what you like.",
        ]},
    ],
    "readables": [
        ("The Starfall stone", (120, -660), [
            "The last of the stones, high under the pass. The crown is carved here too, and the line of figures. But on this one the line doesn't stop: it runs down the stone and into the snow.",
            "Scratched at the bottom, fresh: a crown, crossed out.",
        ]),
        ("The pass to Frisalle", (-60, -780), [
            "Snow and boulders to twice your height, packed hard. A sign hammered into the drift: 'PASS CLOSED. Frisalle beyond.'",
            "Drill holes in the rock above the slide. Somebody brought it down on purpose.",
        ]),
        ("Frozen cart tracks", (-200, 380), [
            "Wagon ruts frozen into the old road, heading north. Deep ones: a heavy load, or a lot of people.",
        ]),
    ],
    "chests": [
        {"id": "tarn_cache", "pos": (-700, -80), "gold": 30, "item": "healers_tonic"},
        {"id": "pass_cairn", "pos": (330, -700), "gold": 50, "card": "elderwood_heart"},
        {"id": "valley_pack", "pos": (700, 520), "item": "bread", "count": 2},
    ],
    "monsters": [(WOLF, (-400, 420)), (WOLF, (420, 450)), (WOLF, (-620, -200)), (WOLF, (240, -560)), (WOLF, (720, -520))],
}

ZONES = {"aurewind_plains": AUREWIND, "verdana": VERDANA, "lake_serin": LAKE_SERIN, "starfall_range": STARFALL}
