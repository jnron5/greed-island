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



def in_poly(x, y, pts):
    """Point in polygon (even-odd rule)."""
    inside = False
    for (ax, ay), (bx, by) in zip(pts, pts[1:] + pts[:1]):
        if (ay > y) != (by > y) and x < ax + (y - ay) * (bx - ax) / (by - ay):
            inside = not inside
    return inside

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
WALL = AW + "stone_wall.png"
SNOW_BOULDER = SF + "snow_boulder.png"
ICE = SF + "ice_crystals.png"


def wob(x, y, amp=28):
    return amp * math.sin(x / 97.0 + 0.3) + amp * 0.6 * math.sin(y / 61.0 + 1.1)


def fence_row(x0, x1, y, gap_at=()):
    return [{"sprite": FENCE, "pos": (x, y), "foot": (16, 6)}
            for x in range(x0, x1 + 1, 16) if all(abs(x - g) > 24 for g in gap_at)]


def wall_row(x0, x1, y, gap_at=()):
    """A dry-stone wall along y, in 46 px sections, open where a gate or path goes."""
    return [{"sprite": WALL, "pos": (x, y), "foot": (46, 10)}
            for x in range(x0 + 23, x1 - 22, 46) if all(abs(x - g) > 40 for g in gap_at)]


def wall_col(x, y0, y1):
    """A dry-stone wall running north-south: sections end-on, stacked close."""
    return [{"sprite": AW + "stone_wall_end.png", "pos": (x, y), "foot": (20, 10)} for y in range(y0 + 10, y1 - 4, 10)]


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
YELLOW, WHITE, PURPLE, RED, BLUE = (240, 210, 70), (240, 240, 228), (170, 120, 210), (214, 58, 48), (110, 150, 230)

AUREWIND = {
    "scene": "scenes/world/aurewind_plains.tscn",
    "root": "AurewindPlains",
    "display": "Aurewind Plains, the Golden Downs",
    "art": AW,
    "bounds": (-1216, -896, 1216, 864),
    "cliff": "assets/sprites/tiles/thornveil/cliff/forest_terrace",
    "level": aurewind_level,
    "tall_walls": {(1, 2): 1},
    "stairs": [(-620, -450, 1, 2), (992, -496, 1, 2)],
    "grade": (1.0, (1.0, 1.0, 1.0)),
    "palette": ((96, 132, 56), (176, 160, 78)),
    "paths": [
        ([(1240, 40), (900, 60), (600, 20), (200, 0), (-200, 60), (-600, 120), (-1000, 140), (-1140, 140)], 30),  # the King's Road
        ([(200, 0), (160, -400), (150, -920)], 24),                         # north, to Lake Serin
        ([(-200, 60), (-350, 400), (-500, 890)], 24),                       # south-west, to Verdana
        ([(-400, 90), (-600, -250), (-640, -400), (-640, -560)], 18),       # up to the stone circle
        ([(700, 40), (900, -250), (992, -400), (992, -580), (930, -650)], 18),  # up Kestrel Rise
        ([(600, 20), (700, 300), (760, 560)], 16),                          # the farm lane
    ],
    "fields": [(820, 200, 1100, 380), (820, 440, 1100, 620), (470, 560, 700, 720)],
    "meadows": [(-900, 330, 190, 110, [YELLOW, WHITE, YELLOW]), (470, -260, 170, 100, [PURPLE, WHITE]),
                (-320, 640, 210, 120, [RED, RED, WHITE]), (-950, -620, 150, 90, [BLUE, WHITE]), (30, -560, 140, 90, [YELLOW, PURPLE])],
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
        # Tilly's sheepfold: a dry-stone pen by the road, open to the south.
        + wall_row(-270, -30, -260) + wall_row(-270, -30, -50, gap_at=(-150,)) + wall_col(-270, -260, -50) + wall_col(-30, -260, -50)
        # The old watchtower on Kestrel Rise.
        + [{"sprite": AW + "watchtower.png", "pos": (900, -700), "foot": (64, 30)}]
        # The travellers' camp.
        + [{"sprite": TV + "tent.png", "pos": (-120, 300), "foot": (60, 20)}]
        # Loki's card table by the fire, and log benches round it.
        + [{"sprite": AW + "card_table.png", "pos": (92, 304), "foot": (48, 14)}]
        + [{"sprite": AW + "log_bench.png", "pos": p, "foot": (36, 10)} for p in [(-30, 286), (-96, 364)]]
        + [{"sprite": KP + "signpost.png", "pos": (-240, 120), "foot": (8, 6)}]
    ),
    "campfires": [(-30, 330)],
    "lanterns": [(-300, 20), (420, -30), (820, 110), (-820, 80), (-640, -520), (120, -330)],
    "npcs": [
        # Tilly's flock, in the sheepfold.
        *[{"id": "sheep", "node": f"Npc_sheep{k}", "name": "Sheep", "pos": p, "wander": 36, "offset": -14.0, "lines": [line]}
          for k, (p, line) in enumerate([((-210, -200), "Baa."), ((-110, -210), "Baaa."), ((-70, -130), "Mm-baa."),
                                          ((-220, -110), "...Baa?")])],
        # Loki, the King of Virelia, travelling incognito: cards by the travellers' fire,
        # watching the racers go by. Nobody knows, and he never says.
        {"id": "loki", "name": "Loki", "pos": (40, 296), "wander": 0, "shop": ["pickpockets_whisper", "lockbox_seal", "second_wind"],
         "shop_title": "Loki's Table", "buys_cards": True, "lines": [
            "Sit, sit. Cut the deck. No? Wise. Nobody ever wins at my fire, not even me.",
            "Racers, every one of you, looking at the horizon. The good cards are always behind you, in somebody's pocket.",
            "I've watched a lot of races from this fire. The ones who win are never the ones you'd bet on. That's what keeps me watching.",
            "My boy cooks for the whole island and won't cook for his father. Children. You give them everything, and they want it on their own terms.",
            "Do you know what you're racing for? No? Neither does anyone. It's better that way. A thing like that changes how people run.",
            "Somewhere up north my youngest is hiding from his mother. I don't blame him. I'd hide from her too, if I had the nerve.",
        ]},
        {"id": "tilly", "name": "Tilly", "pos": (-150, -140), "wander": 50, "lines": [
            "Mind the rams. They're mine, mostly. The ones with the bristles on their backs aren't anyone's.",
            "The stones up on the downs hum when the wind's in the east. Grandad says they're counting.",
            "Wagons used to come east along the dune road every week. Covered, always. Then the rocks came down and they stopped. Or they go some other way now.",
            "My big sisters Jobelle and Mate both think I can't look after myself. I've got forty sheep that say otherwise.",
            "Sully taught me to whistle for the sheep before he went away. He's our brother. He came to us a long time ago, from somewhere much grander than a farm, and he chose to stay.",
            "If you're in Verdana, say hello to Tally at the Sheaf & Sickle. She'll give you a bed and tell you everyone's business. Best friend I've got.",
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
        ("The Kestrel tower", (860, -660), [
            "A watchtower older than the King's Road, half fallen. From the top of the rubble you can see the whole of the plains, the dune road west, and the smoke from somewhere beyond the dunes that never seems to stop.",
            "A sentry once scratched a tally here of carts going west. The tally fills the wall.",
        ]),
        ("The crossroads sign", (-240, 150), [
            "North: LAKE SERIN, and the Starfall Range beyond. South: VERDANA. East: KALMORA. West: the dune road to DUSKARA.",
            "Someone has nailed a plank across the west arm: 'CLOSED'.",
        ]),
        ("A wayside shrine", (-60, -20), [
            "A little cairn of stacked stones by the King's Road, heaped with wheat and ribbons. A board says: 'For the ones who walked west.'",
            "Nobody has written who they were.",
        ]),
    ],
    "chests": [
        {"id": "camp_pack", "pos": (-190, 330), "gold": 15, "item": "bread", "count": 2},
        {"id": "kestrel_cache", "pos": (980, -640), "gold": 40, "card": "crown_stone_rubbing"},
        {"id": "circle_offering", "pos": (-560, -600), "gold": 25, "item": "healers_tonic"},
        {"id": "hay_loft", "pos": (1150, -30), "gold": 10, "item": "bread"},
    ],
    # The Cairn Colossus sleeps on Kestrel Rise, west of the watchtower.
    "boss": {"node": "CairnColossus", "scene": "res://scenes/characters/cairn_colossus.tscn", "pos": (720, -730), "arena": 160},
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
    "stairs": [(608, -150, 1, 2)],
    "grade": (1.0, (1.0, 1.0, 1.0)),
    "palette": ((92, 136, 58), (150, 152, 70)),
    "paths": [
        ([(-200, -660), (-230, -420), (-140, -140), (0, 20)], 26),          # the north road, down from the plains
        ([(0, -60), (0, -210)], 22),                                         # to the inn door
        ([(-120, 20), (-300, -40), (-460, -100)], 18),                       # to the farmhouse
        ([(-100, 140), (-330, 260), (-560, 300)], 18),                       # to the barn
        ([(100, 140), (300, 250), (470, 350)], 18),                          # to the windmill
        ([(140, -20), (450, -40), (608, -50), (608, -170)], 18),            # to the stairs
        ([(608, -170), (612, -320)], 16),                                    # up on the green, to the scholar's door
        ([(240, 110), (394, 140)], 16),                                      # to the bakery door
        ([(40, 200), (86, 410)], 16),                                        # to the weaver's door
    ],
    "plazas": [(0, 60, 250, 150)],
    "meadows": [(-600, -460, 150, 100, [RED, YELLOW, WHITE]), (650, 120, 120, 70, [PURPLE, WHITE])],
    # Hens scratching round the farmhouse and the barn.
    "decor": [{"strip": VD + "hen_anim.png", "frames": 6, "fps": 5, "pos": p, "flip": f}
              for p, f in [((-360, -40), False), ((-400, -10), True), ((-330, -5), False), ((-480, 350), True), ((-440, 340), False)]],                                           # the square, cobbled
    "instances": [("res://scenes/world/props/forest_oak.tscn", (0, 50), 1)]    # the Harvest Oak
                 + [("res://scenes/world/props/forest_oak.tscn", (x, y), 0.6)       # the orchard, in rows
                    for x in (180, 260, 340) for y in (-470, -395)],
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
        {"node": "HouseBarn", "sprite": VD + "barn.png", "pos": (-560, 290), "foot": 130, "door": "res://scenes/world/interiors/verdana_barn.tscn",
         "back": "from_housebarn"},
        {"node": "HouseBakery", "sprite": VD + "bakery.png", "pos": (360, 120), "foot": 150, "door_dx": 34,
         "door": "res://scenes/world/interiors/verdana_bakery.tscn", "back": "from_housebakery"},
        {"node": "HouseWeaver", "sprite": VD + "weaver_cottage.png", "pos": (80, 400), "foot": 150, "door_dx": 6,
         "door": "res://scenes/world/interiors/verdana_weaver.tscn", "back": "from_houseweaver"},
        {"node": "HouseMill", "sprite": K2 + "objects/windmill2.png", "pos": (480, 340), "foot": 90,
         "door": "res://scenes/world/interiors/verdana_mill.tscn", "back": "from_housemill",
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
        # Flower beds round the Harvest Oak, open to the north and south.
        + [{"sprite": K2 + "props/flower_bed.png", "pos": p, "foot": (30, 8)} for p in [(-70, 40), (70, 40), (-56, 96), (56, 96)]]
        + [{"sprite": HAY, "pos": p, "foot": (34, 14)} for p in [(-420, 330), (-690, 300), (-460, 360)]]
        + [{"sprite": SCARECROW, "pos": p, "foot": (10, 6)} for p in [(-720, 80), (680, 460)]]
        + fence_row(-790, -640, -52) + fence_row(-790, -640, 212) + fence_row(560, 800, 372, gap_at=(680,))
        # Every door has its own clutter: what each household does, left outside.
        # The inn: barrels and crates for the cellar, a bench for the regulars.
        + [{"sprite": KP + "barrels.png", "pos": (104, -226), "foot": (26, 8), "scale": 1.2},
           {"sprite": KP + "crates.png", "pos": (130, -214), "foot": (26, 8), "scale": 1.1},
           {"sprite": K2 + "props/bench.png", "pos": (-112, -222), "foot": (36, 8)}]
        # Marta's farmhouse: washing on the line, the wheelbarrow and sacks, geraniums at the door.
        + [{"sprite": KP + "laundry_line.png", "pos": (-610, -150), "foot": (30, 6), "scale": 1.5},
           {"sprite": KP + "laundry_basket.png", "pos": (-580, -128), "foot": (16, 6)},
           {"sprite": KP + "wheelbarrow.png", "pos": (-372, -110), "foot": (24, 8), "scale": 1.2},
           {"sprite": KP + "sack.png", "pos": (-392, -96), "foot": (14, 6)},
           {"sprite": KP + "geraniums.png", "pos": (-506, -106), "foot": (12, 6)},
           {"sprite": KP + "geraniums.png", "pos": (-414, -106), "foot": (12, 6)}]
        # Pim's bakery: flour sacks by the side, bread cooling by the door.
        + [{"sprite": KP + "flour_sack.png", "pos": p, "foot": (14, 6)} for p in [(296, 128), (278, 136)]]
        + [{"sprite": KP + "bread_basket.png", "pos": (432, 132), "foot": (14, 6)}]
        # Oda's cottage: dyed wool drying on a line, lavender in a box.
        + [{"sprite": KP + "laundry_line.png", "pos": (210, 380), "foot": (30, 6), "scale": 1.5},
           {"sprite": KP + "laundry_basket.png", "pos": (232, 402), "foot": (16, 6)},
           {"sprite": KP + "lavender_planter.png", "pos": (26, 412), "foot": (22, 6)},
           {"sprite": KP + "lavender_planter.png", "pos": (140, 412), "foot": (22, 6)}]
        # The barn and the mill: a cart, buckets, the day's flour.
        + [{"sprite": KP + "cart.png", "pos": (-460, 312), "foot": (40, 10), "scale": 1.3},
           {"sprite": KP + "bucket.png", "pos": (-494, 286), "foot": (12, 6)},
           {"sprite": KP + "sack.png", "pos": (-648, 306), "foot": (14, 6)},
           {"sprite": KP + "flour_sack.png", "pos": (532, 352), "foot": (14, 6)},
           {"sprite": KP + "flour_sack.png", "pos": (548, 340), "foot": (14, 6)}]
        # Flowering hedges along the lanes, where the lawns were bare.
        + [{"sprite": K2 + "props/bush_flowers_g.png" if i % 2 else K2 + "props/bush_g.png", "pos": p, "foot": (40, 12), "scale": 0.7}
           for i, p in enumerate([(-300, -200), (-252, -222), (300, 40), (344, 22), (-300, 176), (-256, 196)])]
        # The orchard north-east of the inn, fenced along the lane.
        + fence_row(150, 370, -332, gap_at=(260,))
    ),
    "merchant": ((200, 40), "assets/sprites/tiles/kalmora/market_stall.png"),
    "lanterns": [(-230, -20), (230, -20), (-230, 170), (230, 170), (-200, -380), (380, -120), (560, -280), (-380, -60), (380, 280),
                 ],
    "npcs": [
        {"id": "aldous", "name": "Aldous", "pos": (620, -270), "wander": 20, "lines": [
            "The stones were here before the kings. Before the towns. Before, I think, the cards.",
            "I've spent forty years reading what's carved on them. It's the same story on every one, told smaller each time.",
        ]},
        {"id": "marta", "name": "Marta", "pos": (-400, -60), "wander": 40, "lines": [
            "Harvest's in early. Half of it's sold before it's cut, to the Company men from Duskara. Paid in scrip.",
            "Scrip spends at the Company store and nowhere else. Funny, that.",
        ]},
        {"id": "oda", "name": "Oda", "pos": (170, 440), "wander": 30, "lines": [
            "Every thread on that loom is somebody. I weave them in so they don't get lost.",
            "My grandson went west with the Company carts two harvests ago. They said Lake Serin way, then north. I've not been further than the mill in twenty years.",
        ]},
        {"id": "pim", "name": "Pim", "pos": (440, 170), "wander": 20, "shop": ["bread", "smoked_fish"],
         "shop_title": "Pim's Bakery", "lines": [
            "Fresh this morning! Well. This morning-ish. The oven's been going since before the larks.",
            "The Company used to take a cartload of hard bread every week for the dune road. Stopped three weeks ago. Nobody's said why. I keep baking it anyway.",
        ]},
        {"id": "bruno", "name": "Bruno", "pos": (70, -180), "wander": 20, "shop": ["bread", "smoked_fish", "healers_tonic"],
         "shop_title": "Bruno's Kitchen", "lines": [
            "I cook for the Sheaf and Sickle. Tally runs it, inside: beds, cider, and the tally of who owes what. I just feed people.",
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
        {"id": "barn_loft", "pos": (-700, 240), "gold": 20, "card": "millers_seal"},
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
    "stairs": [(-960, 310, 1, 2)],
    "grade": (1.0, (1.0, 1.0, 1.0)),
    "palette": ((64, 112, 64), (104, 136, 68)),
    "paths": [
        ([(700, 790), (650, 450), (720, 100), (650, -400), (200, -560), (-300, -790)], 26),   # round the east shore, north to the Range
        ([(40, -470), (60, -250)], 18),                                     # out onto Stone Point
        ([(720, 60), (660, -60), (560, -74)], 16),                          # to Neri's dock
        ([(-300, -700), (-600, 0), (-960, 400), (-960, 250)], 18),          # the west trail to the bluffs
        ([(-960, 270), (-880, -300)], 14),                                  # up on the bluffs
    ],
    "lakes": [(80, -40, 520, 300)],
    "meadows": [(420, 480, 160, 90, [WHITE, YELLOW]), (-420, -560, 140, 80, [BLUE, WHITE])],
    "land": [(60, -330, 90, 150)],
    "docks": [(470, -90, 640, -58)],
    # Cast off the end of Neri's dock (scripts/systems/fishing_spot.gd).
    "fishing": [(490, -74)],
    # Lily pads in the shallows and Neri's boats tied up at his dock.
    "afloat": [(LS + "barge.png", (-330, 95), False)] + [(TV + "lily_pads.png", p, f) for p, f in [((-250, 180), False), ((-200, -200), True), ((-250, -250), False),
                                                         ((300, 200), True), ((380, 150), False), ((-100, 200), True),
                                                         ((420, -250), False), ((-400, -120), True)]]
              + [(K2 + "props/rowboat.png", (520, -20), False), (K2 + "props/rowboat.png", (515, -150), True)],
    "deep": (26, 72, 104),
    # Herons fishing in the shallows.
    "decor": [{"strip": LS + "heron_anim.png", "frames": 8, "fps": 3, "pos": p, "afloat": True, "flip": f}
              for p, f in [((-350, 30), False), ((330, 190), True)]],
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
        ("A drowned barge", (-400, 160), [
            "A flat barge, sunk at its mooring in the shallows. Its hold was lined with straw, and fitted with rings for chains.",
            "Stencilled on the stern, under the weed: 'D.M.C. - NORTH'.",
        ]),
        ("Neri's tally board", (760, -30), [
            "A board of chalk tallies: fish, by the day. On the back, a different tally, not fish. Barges crossing, by the night. It stops last spring.",
        ]),
    ],
    "chests": [
        {"id": "bluff_nest", "pos": (-850, -300), "gold": 35, "card": "barge_bell"},
        {"id": "reed_bed", "pos": (-470, 380), "item": "smoked_fish", "count": 2},
        {"id": "point_cache", "pos": (110, -420), "gold": 25, "card": "serin_lily"},
    ],
    "monsters": [(BOAR, (-300, 330)), (BOAR, (320, 470)), (HOUND, (-200, -560)), (HOUND, (620, -600)), (RAM, (-40, 600))],
    "butterflies": [((600, 300), 3), ((-800, -200), 2)],
}

# ---------------------------------------------------------------- Starfall Range
def starfall_level(x, y):
    w = 44 * math.sin(x / 190.0) + 14 * math.sin(x / 70.0 + 1.0)
    spur = lambda at, width: math.exp(-((x - at) / width) ** 2)
    # Rock spurs where a terrace juts out over the one below, and a bay where the
    # snow runs back into the mountain (kept clear of the stairs).
    lower = w - 80 * spur(-860, 80) - 70 * spur(600, 90) + 60 * spur(80, 70)
    upper = w * 0.8 + 70 * spur(-640, 100) - 80 * spur(720, 80) - 50 * spur(-60, 70)
    if y + lower > 150:
        return 0
    if y + upper > -350:
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
    "stairs": [(-224, 150, 0, 1), (288, -350, 1, 2), (-544, 150, 0, 1)],
    "grade": (0.95, (1.0, 1.0, 1.04)),
    "dapple": 0.08,
    "snow": True,
    "snowfall": True,
    "paths": [
        ([(0, 790), (-60, 420), (-224, 300), (-224, 130), (100, -150), (288, -300), (288, -470), (0, -640), (-100, -820)], 24),
        ([(100, -150), (450, -60), (550, -60)], 16),                        # to the hermit's cabin
        ([(560, -60), (860, -156)], 14),                                    # on to the ice grotto
        ([(-224, 100), (-450, 40), (-544, 100), (-544, 260)], 16),          # round the tarn, down the west stairs
    ],
    "ice": [(-480, -120, 170, 90)],
    "tree_kinds": ["pine"],
    # Pines stand in windbreaks: tucked under each terrace wall and round the cabin,
    # thinning out onto the open snowfields.
    "groves": [(-800, -600, 8, 60), (880, -790, 6, 50), (-600, 520, 7, 60), (600, 420, 8, 60), (800, 0, 5, 50), (-850, -200, 5, 50),
               (-420, -560, 6, 55), (-140, 560, 5, 50), (420, 230, 5, 50), (-820, 140, 5, 50),
               (760, -240, 4, 40), (-40, -420, 4, 45)],
    # What pokes up through the snow: frosted juniper, winter grass, rocks.
    "under": [("snow_shrub", 3), ("frost_grass", 3), ("snow_rocks", 1)],
    "solid_under": ["snow_rocks"],
    "patches": 34,
    "entry": (0, 720),
    "exits": [
        {"name": "ToLakeSerin", "pos": (0, 788), "side": "s", "target": "res://scenes/world/lake_serin.tscn", "spawn": "from_starfall"},
    ],
    "spawns": {"from_lake_serin": (0, 720), "from_grotto": (860, -150)},
    # The Frost Grotto under the east shoulder (build_grotto.py).
    "portals": [{"name": "ToGrotto", "pos": (860, -224), "target": "res://scenes/world/starfall_grotto.tscn", "spawn": "from_starfall"}],
    "rival_spots": {"runner": (-40, 660), "raider": (40, 660), "hoarder": (0, 620)},
    "buildings": [
        {"node": "HouseHald", "sprite": SF + "hermit_cabin.png", "pos": (620, -110), "foot": 130, "door": "res://scenes/world/interiors/starfall_cabin.tscn",
         "back": "from_househald"},
    ],
    "props": (
        # The pass to Frisalle: an avalanche across it, boulders and drifts twice your height.
        [{"sprite": SNOW_BOULDER, "pos": (x, y), "foot": (52, 18), "flip": (x // 10) % 2 == 0}
         for x, y in [(-200, -846), (-150, -862), (-100, -850), (-50, -866), (0, -848), (50, -858), (-175, -822),
                      (-125, -826), (-75, -820), (-25, -828), (25, -822)]]
        + [{"sprite": STONE, "pos": (120, -700), "foot": (26, 12), "scale": 1.3, "light": ((0.7, 0.85, 1.0, 1), 0.45, 1.2)}]
        + [{"sprite": SF + "ice_cave_mouth.png", "pos": (860, -196), "feet": [(-56, -20, 50, 40), (56, -20, 50, 40), (0, -52, 64, 22)],
            "light": ((0.55, 0.85, 1.0, 1), 0.5, 1.0)}]
        # Snow-capped boulders where the slopes shed them, and ice crystals that glow blue.
        + [{"sprite": SNOW_BOULDER, "pos": p, "foot": (52, 18), "flip": i % 2 == 1} for i, p in enumerate(
            [(-820, 420), (-300, 560), (260, 600), (820, 250), (-760, -330), (560, -420), (-380, -520), (760, -760), (180, 330)])]
        + [{"sprite": ICE, "pos": p, "foot": (28, 10), "light": ((0.55, 0.85, 1.0, 1), 0.6, 0.9)} for p in
           [(-660, -170), (-300, -40), (-560, 30), (380, -660), (-280, -760), (700, 120)]]
    ),
    "campfires": [(500, -40)],
    "lanterns": [(-80, 260), (330, -250), (-40, -600)],
    "npcs": [
        # Mountain goats picking their way along the slopes.
        *[{"id": "goat", "node": f"Npc_goat{k}", "name": "Mountain Goat", "pos": p, "wander": 60, "offset": -16.0, "lines": [line]}
          for k, (p, line) in enumerate([((-620, 470), "Meh-eh-eh."), ((-540, 530), "..."), ((620, -640), "Mehh.")])],
        {"id": "hald", "name": "Hald", "pos": (540, -80), "wander": 30, "lines": [
            "Frisalle's over the pass. Nobody's crossed since the slide. Nobody's tried very hard.",
            "The slide came down the week after the last barge went north. The Company men were up here with powder the week before. Make of that what you like.",
            "There's a cave in the east shoulder, past my woodpile. Ice all the way through. The wolves den in it now. The Company used it before the wolves did.",
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
        {"id": "pass_cairn", "pos": (330, -700), "gold": 50, "card": "fallen_star_shard"},
        {"id": "valley_pack", "pos": (700, 520), "item": "bread", "count": 2},
    ],
    "monsters": [(WOLF, (-400, 420)), (WOLF, (420, 450)), (WOLF, (-620, -200)), (WOLF, (240, -560)), (WOLF, (-700, -450))],
    # The Rime Stag keeps the high snowfield east of the pass.
    "boss": {"node": "RimeStag", "scene": "res://scenes/characters/rime_stag.tscn", "pos": (610, -620), "arena": 170},
}

ZONES = {"aurewind_plains": AUREWIND, "verdana": VERDANA, "lake_serin": LAKE_SERIN, "starfall_range": STARFALL}
