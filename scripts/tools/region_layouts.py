"""Layouts for the regions past Kalmora's west gate, built by build_region.py.

All positions are zone-local px. The island map (docs/reference/virelia_map.webp):
the Aurewind Plains lie west of Kalmora, gold and green, with Verdana in their south
and the old standing stones on the downs; Lake Serin lies north of the plains, and
the Starfall Range rises north of the lake, its pass to Frisalle snowed shut but for
the toll gate Frisalle's folk set into the slide.
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
# (edges kept near horizontal or vertical: a diagonal cliff line breaks into a jagged staircase of cliff blocks)
STONEWATCH = [(-1300, -1000), (-150, -1000), (-160, -560), (-200, -530), (-400, -500), (-700, -430), (-1000, -470), (-1300, -420)]
KESTREL = [(460, -1000), (1300, -1000), (1300, -500), (1050, -462), (800, -500), (480, -540)]


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
        ([(1240, 40), (900, 60), (600, 20), (200, 0), (-200, 60), (-600, 120), (-1000, 140), (-1240, 140)], 30),  # the King's Road, on as the dune road
        ([(200, 0), (160, -400), (150, -920)], 24),                         # north, to Lake Serin
        ([(-200, 60), (-350, 400), (-500, 890)], 24),                       # south-west, to Verdana
        ([(-400, 90), (-600, -250), (-640, -400), (-640, -560)], 18),       # up to the stone circle
        ([(-640, -600), (-520, -690), (-380, -716)], 14),                  # across the downs to the barrow
        ([(-760, 100), (-900, -120), (-980, -270)], 14),                   # the old track to the Ashby place
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
        {"name": "ToDunes", "pos": (-1236, 140), "side": "w", "target": "res://scenes/world/siroth_dunes.tscn", "spawn": "from_aurewind"},
    ],
    "spawns": {"from_kalmora": (1160, 40), "from_lake_serin": (150, -840), "from_verdana": (-500, 820), "from_barrow": (-380, -712),
               "from_dunes": (-1160, 140)},
    # The Old Barrow, the first king's grave (build_barrow.py), dug into the downs.
    "portals": [{"name": "ToBarrow", "pos": (-380, -772), "target": "res://scenes/world/aurewind_barrow.tscn", "spawn": "from_aurewind"}],
    "rival_spots": {"runner": (1100, 0), "raider": (1100, 80), "hoarder": (1060, 40)},
    "buildings": [
        {"node": "WorkingBarn", "sprite": VD + "barn.png", "pos": (1000, -110), "foot": 130},
    ],
    "props": (
        # The Old Barrow's door on the downs: a mound with a stone doorway (the way in
        # is a portal between the door stones), and the Ashby farmstead in ruins.
        [{"sprite": AW + "barrow_mound.png", "pos": (-380, -760), "feet": [(-38, -14, 36, 26), (38, -14, 36, 26), (0, -40, 32, 14)]},
         {"sprite": AW + "ruined_cottage.png", "pos": (-980, -300), "foot": (88, 26)}]
        +
        # The stone circle on the Stonewatch Downs, the altar in the middle.
        ring(CIRCLE[0], CIRCLE[1], 120, 8, STONE, (26, 12))
        + [{"sprite": ALTAR, "pos": (CIRCLE[0], CIRCLE[1] + 10), "foot": (56, 16), "light": ((0.7, 0.85, 1.0, 1), 0.35, 1.2)}]
        # The Hensley farm: hay by the barn, scarecrows in the wheat, fences along the fields.
        + [{"sprite": HAY, "pos": p, "foot": (34, 14)} for p in [(870, -80), (900, -40), (1130, -60), (820, 160)]]
        + [{"sprite": SCARECROW, "pos": p, "foot": (10, 6)} for p in [(960, 300), (580, 640)]]
        + fence_row(820, 1100, 190, gap_at=(900,)) + fence_row(820, 1100, 630, gap_at=(1000,))
        # The dune road, "closed": a rockfall across it, two of the rocks rolled aside
        # (just wide enough for a cart), and a broken ore cart.
        + [{"sprite": BOULDER, "pos": p, "foot": (40, 18), "scale": 1.4} for p in [(-1180, 70), (-1140, 86), (-1186, 222), (-1150, 236)]]
        + [{"sprite": KP + "cart.png", "pos": (-1060, 226), "foot": (28, 12), "flip": True}]
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
        {"id": "tilly", "name": "Tilly", "pos": (-150, -140), "wander": 50, "night": (90, 326), "night_wander": 10, "lines": [
            "Mind the rams. They're mine, mostly. The ones with the bristles on their backs aren't anyone's.",
            "The stones up on the downs hum when the wind's in the east. Grandad says they're counting.",
            "Wagons used to come east along the dune road every week. Covered, always. Then the rocks came down and they stopped. Or they go some other way now.",
            "My big sisters Jobelle and Mate both think I can't look after myself. I've got forty sheep that say otherwise.",
            "Sully taught me to whistle for the sheep before he went away. He's our brother. He came to us a long time ago, from somewhere much grander than a farm, and he chose to stay.",
            "If you're in Verdana, say hello to Tally at the Sheaf & Sickle. She'll give you a bed and tell you everyone's business. Best friend I've got.",
        ]},
    ],
    "readables": [
        ("The barrow mound", (-450, -716), [
            "A long grassy mound on the downs, too regular to be a hill. Its door is two standing stones and a lintel carved with a crown.",
            "The turf by the door has been cut and laid back. Somebody comes and goes, and doesn't want it seen.",
        ]),
        ("The Ashby place", (-930, -262), [
            "A farmstead gone to ruin: no roof, the hearth cold for years. A plaque by the door: 'ASHBY. Five generations on this land.'",
            "Nailed to the doorframe, curled with rain: 'NOTICE OF DEBT. Land and tenants assigned to the Duskara Mining Company in settlement.' Tenants.",
        ]),
        ("The Aurewind circle", (CIRCLE[0], CIRCLE[1] + 40), [
            "Eight standing stones round a flat altar, older than any road on the island. The altar's face is carved with a crown and, under it, a long line of small figures, each one smaller than the last.",
            "Someone has laid fresh wheat on the altar. Someone else has scratched a tally beside the figures. The scratches are new.",
        ]),
        ("The dune road", (-1080, 70), [
            "A signpost, freshly painted: 'SIROTH DUNES - DUSKARA. ROAD CLOSED BY ORDER OF THE DUSKARA MINING COMPANY. ROCKFALL.'",
            "The rocks across the road sit on wheel ruts. Rockfalls don't come on carts. Two of them have been rolled aside, just far enough for a cart to squeeze through, and the ruts go on west.",
        ]),
        ("A broken ore cart", (-1000, 250), [
            "An ore cart with a split axle, left where it broke. No ore in it: straw, a water skin, and a length of chain with small cuffs.",
            "Stencilled on the side: 'D.M.C. - RETURN EMPTY'.",
        ]),
        ("The Kestrel tower", (860, -660), [
            "A watchtower older than the King's Road, half fallen. From the top of the rubble you can see the whole of the plains, the dune road west, and the smoke from somewhere beyond the dunes that never seems to stop.",
            "A sentry once scratched a tally here of carts going west. The tally fills the wall.",
        ]),
        ("The crossroads sign", (-240, 150), [
            "North: LAKE SERIN, and the Starfall Range beyond. South: VERDANA. East: KALMORA. West: the dune road to DUSKARA.",
            "Someone has nailed a plank across the west arm: 'CLOSED'. Someone else has prised one end of it loose.",
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
        {"id": "ashby_hearth", "pos": (-1060, -296), "gold": 30, "item": "smoked_fish"},
    ],
    # The Cairn Colossus sleeps on Kestrel Rise, west of the watchtower.
    "boss": {"node": "CairnColossus", "scene": "res://scenes/characters/cairn_colossus.tscn", "pos": (720, -730), "arena": 160},
    "monsters": [(RAM, (420, -180)), (RAM, (-220, -330)), (RAM, (-700, 380)), (RAM, (300, 700)), (RAM, (-950, -640)),
                 (HOUND, (-1000, 520)), (HOUND, (620, 780))],
    "butterflies": [((950, 300), 4), ((-600, -700), 3), ((150, 300), 3), ((-400, 600), 3)],
}

# ---------------------------------------------------------------- Verdana
UPPER_GREEN = [(430, -760), (900, -760), (900, -130), (640, -110), (450, -210)]


def verdana_level(x, y):
    return 2 if in_poly(x + wob(x, y, 14), y + wob(y, x, 10), UPPER_GREEN) else 1


VERDANA = {
    # A street village: the High Street runs east-west through the town with the
    # farmhouse, Oda's cottage, the Sheaf & Sickle and the bakery shoulder to shoulder
    # along its north side, doors on the street. South of the street the Harvest Oak
    # stands on a little green with the market and the well where the road to
    # Seabright turns off; below that the millstream, crossed by two plank bridges, and
    # past it the barn, the windmill and the fields. Aldous lives up on the raised
    # green to the north-east.
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
        ([(-840, -34), (-600, -42), (-300, -36), (0, -44), (300, -36), (560, -44), (840, -30)], 30),   # the High Street
        ([(-200, -660), (-230, -420), (-200, -220), (-200, -40)], 26),                         # the north road, down from the plains
        ([(-130, -40), (-120, 150), (-110, 320), (-100, 440), (-100, 600)], 22),              # the south road over the bridge, to Seabright
        ([(560, -44), (672, -100), (672, -172)], 18),                                          # up the stairs to the green
        ([(672, -172), (640, -260), (612, -320)], 16),                                         # to the scholar's door
        ([(430, -40), (430, 150), (430, 340), (480, 470)], 16),                                # over the mill bridge to the windmill
        ([(-110, 360), (-360, 420), (-560, 500)], 16),                                         # along the south bank to the barn
    ],
    "plazas": [(-60, 110, 92, 46)],                                                             # the market corner by the green
    "meadows": [(-600, -460, 150, 100, [RED, YELLOW, WHITE]), (650, 120, 120, 70, [PURPLE, WHITE]), (-330, 120, 120, 50, [YELLOW, WHITE, RED])],
    # The millstream, east to west across the south of the town (reeds along it).
    "lakes": [(x, 250 + 26 * math.sin(x / 260.0), 118, 30) for x in range(-960, 1000, 150)],
    "deep": (36, 86, 100),
    "docks": [(-140, 186, -82, 320), (402, 186, 458, 320)],                                    # plank bridges for the two roads
    "decor": [{"strip": VD + "hen_anim.png", "frames": 6, "fps": 5, "pos": p, "flip": f}
              for p, f in [((-540, -20), False), ((-580, 6), True), ((-500, 10), False), ((-480, 520), True), ((-440, 510), False)]],
    "instances": [("res://scenes/world/props/forest_oak.tscn", (-300, 110), 1)]                # the Harvest Oak, on the green
                 + [("res://scenes/world/props/forest_oak.tscn", (x, y), 0.6)                  # the orchard behind the bakery, in rows
                    for x in (180, 260, 340) for y in (-470, -395)],
    "fields": [(-790, 330, -640, 540), (560, 380, 800, 540), (-420, 410, -220, 540), (60, 380, 300, 540)],
    "tree_kinds": ["oak"],
    "groves": [(-700, -500, 5, 50), (760, 160, 4, 40), (300, -580, 4, 40), (-740, 120, 3, 40), (720, -40, 2, 30)],
    "under": [("flowers", 6), ("grass_clump", 4), ("clover", 3), ("berry_bush", 1)],
    "patches": 40,
    "tufts": 90,
    "tuft_tint": (1.05, 1.0, 0.85, 1),
    "safe_zone": (-832, -640, 832, 576),
    "entry": (-200, -600),
    "exits": [
        {"name": "ToAurewind", "pos": (-200, -660), "side": "n", "target": "res://scenes/world/aurewind_plains.tscn", "spawn": "from_verdana"},
        {"name": "ToResort", "pos": (-100, 572), "side": "s", "target": "res://scenes/world/seabright_quay.tscn", "spawn": "from_verdana"},
    ],
    "spawns": {"town": (-140, 60), "from_aurewind": (-200, -600), "from_resort": (-100, 515)},
    "rival_spots": {"runner": (-80, 30), "raider": (60, 20), "hoarder": (120, 0)},
    "buildings": [
        {"node": "HouseInn", "sprite": VD + "inn.png", "pos": (0, -92), "foot": 150, "door": "res://scenes/world/interiors/verdana_inn.tscn",
         "back": "from_houseinn"},
        {"node": "HouseFarm", "sprite": VD + "farmhouse.png", "pos": (-620, -92), "foot": 140, "door": "res://scenes/world/interiors/verdana_farmhouse.tscn",
         "back": "from_housefarm"},
        {"node": "HouseScholar", "sprite": VD + "scholar_house.png", "pos": (620, -330), "foot": 124, "door": "res://scenes/world/interiors/verdana_scholar.tscn",
         "back": "from_housescholar"},
        {"node": "HouseBarn", "sprite": VD + "barn.png", "pos": (-560, 480), "foot": 130, "door": "res://scenes/world/interiors/verdana_barn.tscn",
         "back": "from_housebarn"},
        {"node": "HouseBakery", "sprite": VD + "bakery.png", "pos": (270, -92), "foot": 150, "door_dx": 34,
         "door": "res://scenes/world/interiors/verdana_bakery.tscn", "back": "from_housebakery"},
        {"node": "HouseWeaver", "sprite": VD + "weaver_cottage.png", "pos": (-340, -92), "foot": 150, "door_dx": 6,
         "door": "res://scenes/world/interiors/verdana_weaver.tscn", "back": "from_houseweaver"},
        {"node": "HouseMill", "sprite": K2 + "objects/windmill2.png", "pos": (500, 470), "foot": 90,
         "door": "res://scenes/world/interiors/verdana_mill.tscn", "back": "from_housemill",
         "sails": (K2 + "anim/windmill_sails.png", 12, 7, (80, 78))},
    ],
    "props": (
        # The green: the well under the Harvest Oak, benches round it, flower beds.
        [{"sprite": "assets/sprites/tiles/sorenda/sorenda_well.png", "pos": (-400, 150), "foot": (40, 14)}]
        + [{"sprite": K2 + "props/bench.png", "pos": p, "foot": (36, 8)} for p in [(-360, 60), (-240, 176)]]
        + [{"sprite": K2 + "props/flower_bed.png", "pos": p, "foot": (30, 8)} for p in [(-250, 70), (-350, 180)]]
        # The market corner: bread and fruit stalls facing the road, the notice board.
        + [{"sprite": K2 + "props/stall_bread.png", "pos": (-40, 150), "foot": (54, 14)},
           {"sprite": K2 + "props/stall_fruit.png", "pos": (40, 92), "foot": (54, 14)},
           {"sprite": KP + "bread_basket.png", "pos": (-4, 160), "foot": (14, 6)},
           {"sprite": KP + "apples_crate.png", "pos": (78, 100), "foot": (16, 8)},
           {"sprite": K2 + "props/notice_board.png", "pos": (-180, 40), "foot": (30, 8)}]
        # Along the High Street: planters and benches by the doors.
        + [{"sprite": K2 + "props/flower_bed.png", "pos": p, "foot": (30, 8)} for p in [(-96, -66), (96, -66)]]
        + [{"sprite": K2 + "props/bench.png", "pos": p, "foot": (36, 8)} for p in [(-470, -66), (150, -66)]]
        # The fields south of the stream: hay, scarecrows, fences.
        + [{"sprite": HAY, "pos": p, "foot": (34, 14)} for p in [(-420, 370), (-680, 300), (-460, 388)]]
        + [{"sprite": SCARECROW, "pos": p, "foot": (10, 6)} for p in [(-720, 430), (680, 460), (180, 460)]]
        + fence_row(-790, -640, 316) + fence_row(560, 800, 366, gap_at=(680,)) + fence_row(60, 300, 366, gap_at=(180,))
        # The inn: barrels and crates for the cellar, by the side wall.
        + [{"sprite": KP + "barrels.png", "pos": (108, -86), "foot": (26, 8), "scale": 1.2},
           {"sprite": KP + "crates.png", "pos": (-112, -80), "foot": (26, 8), "scale": 1.1}]
        # Marta's farmhouse: washing on the line behind the hens, the wheelbarrow and sacks.
        + [{"sprite": KP + "laundry_line.png", "pos": (-760, -120), "foot": (30, 6), "scale": 1.5},
           {"sprite": KP + "laundry_basket.png", "pos": (-730, -96), "foot": (16, 6)},
           {"sprite": KP + "wheelbarrow.png", "pos": (-520, -70), "foot": (24, 8), "scale": 1.2},
           {"sprite": KP + "sack.png", "pos": (-540, -60), "foot": (14, 6)},
           {"sprite": KP + "geraniums.png", "pos": (-666, -76), "foot": (12, 6)}]
        # Pim's bakery: flour sacks by the side, bread cooling by the door.
        + [{"sprite": KP + "flour_sack.png", "pos": p, "foot": (14, 6)} for p in [(200, -76), (184, -68)]]
        + [{"sprite": KP + "bread_basket.png", "pos": (344, -66), "foot": (14, 6)}]
        # Oda's cottage: dyed wool drying, lavender at the door.
        + [{"sprite": KP + "lavender_planter.png", "pos": p, "foot": (22, 6)} for p in [(-396, -70), (-284, -70)]]
        + [{"sprite": KP + "laundry_line.png", "pos": (-460, -150), "foot": (30, 6), "scale": 1.5}]
        # The barn and the mill: a cart, buckets, the day's flour.
        + [{"sprite": KP + "cart.png", "pos": (-460, 500), "foot": (40, 10), "scale": 1.3},
           {"sprite": KP + "bucket.png", "pos": (-494, 470), "foot": (12, 6)},
           {"sprite": KP + "flour_sack.png", "pos": (552, 484), "foot": (14, 6)},
           {"sprite": KP + "flour_sack.png", "pos": (568, 472), "foot": (14, 6)}]
        # The orchard fenced along its lane.
        + fence_row(150, 370, -332, gap_at=(260,))
    ),
    "merchant": ((120, 150), "assets/sprites/tiles/kalmora/market_stall.png"),
    "lanterns": [(-470, -10), (-150, -10), (150, -10), (470, -10), (-200, -330), (560, -280), (-170, 350), (460, 350), (-250, 40)],
    "string_lights": [((-90, 70), (160, 70), 16)],
    "npcs": [
        {"id": "aldous", "name": "Aldous", "pos": (620, -270), "wander": 20, "night": (720, -230), "lines": [
            "The stones were here before the kings. Before the towns. Before, I think, the cards.",
            "I've spent forty years reading what's carved on them. It's the same story on every one, told smaller each time.",
        ]},
        {"id": "marta", "name": "Marta", "pos": (-560, -20), "wander": 40, "out": (5.0, 20.0), "lines": [
            "Harvest's in early. Half of it's sold before it's cut, to the Company men from Duskara. Paid in scrip.",
            "Scrip spends at the Company store and nowhere else. Funny, that.",
        ]},
        {"id": "oda", "name": "Oda", "pos": (-300, -16), "wander": 30, "out": (6.5, 20.5), "lines": [
            "Every thread on that loom is somebody. I weave them in so they don't get lost.",
            "My grandson went west with the Company carts two harvests ago. They said Lake Serin way, then north. I've not been further than the mill in twenty years.",
        ]},
        {"id": "pim", "name": "Pim", "pos": (340, -20), "wander": 20, "out": (4.5, 18.5), "shop": ["bread", "smoked_fish"],
         "shop_title": "Pim's Bakery", "lines": [
            "Fresh this morning! Well. This morning-ish. The oven's been going since before the larks.",
            "The Company used to take a cartload of hard bread every week for the dune road. Stopped three weeks ago. Nobody's said why. I keep baking it anyway.",
        ]},
        {"id": "bruno", "name": "Bruno", "pos": (60, -20), "wander": 20, "out": (6.0, 20.0), "shop": ["bread", "smoked_fish", "healers_tonic"],
         "shop_title": "Bruno's Kitchen", "lines": [
            "I cook for the Sheaf and Sickle. Tally runs it, inside: beds, cider, and the tally of who owes what. I just feed people.",
            "The last racer through here paid in cards. I don't want cards. I want a quiet life and a full cellar.",
        ]},
    ],
    "readables": [
        ("The harvest board", (-180, 54), [
            "WANTED: HANDS FOR THE DUSKARA WORKS. Small hands preferred for close work. Room, board and a trade. Apply to the Company agent, first of the month.",
            "Somebody has written underneath, in pencil: 'none of ours'. Somebody else has crossed it out.",
        ]),
        # What the Millstream Carries (Oda): things caught in the reeds along the stream.
        ("A snag of red wool", (-640, 196), [
            "Caught on a reed stem at the water's edge: a long tail of knitted wool, red as madder, unravelling in the current.",
        ]),
        ("A scrap of paper in the reeds", (130, 214), [
            "A soaked chit, the ink run but readable: 'D.M.C. North depot. Pay to bearer: one ration.' On the back, in a child's hand, a name scratched out.",
        ]),
        ("A little carved bird", (660, 220), [
            "Wedged between two stones where the stream bends: a small wooden bird, carved the way they carve them in Sorenda, worn smooth by the water.",
        ]),
        ("The mill ledger", (446, 500), [
            "A ledger nailed up by the mill door. 'Flour to D.M.C.: 200 sacks. Rate: one third market, by agreement.'",
            "'By agreement' is underlined twice, hard enough to tear the page.",
        ]),
        ("A stone by the scholar's door", (680, -300), [
            "A fragment of a standing stone, set upright by the door. The same carving as the circle on the downs: a crown, and under it a line of figures, each one smaller.",
        ]),
    ],
    "chests": [
        {"id": "barn_loft", "pos": (-700, 420), "gold": 20, "card": "millers_seal"},
    ],
    "butterflies": [((-300, 110), 3), ((-700, 380), 3), ((680, 460), 3)],
}

# ---------------------------------------------------------------- Lake Serin
# (edges near vertical or horizontal, with only a little wobble: a slanting cliff line
# breaks into a jagged staircase of cliff blocks)
HERON_BLUFFS = [(-1100, -900), (-560, -900), (-570, -280), (-690, -250), (-700, 300), (-1100, 320)]


def serin_level(x, y):
    return 2 if in_poly(x + wob(x, y, 8), y + wob(y, x, 8), HERON_BLUFFS) else 1


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
        ([(-300, -700), (-600, 0), (-864, 400), (-864, 250)], 18),          # the west trail to the bluffs
        ([(-864, 270), (-880, -300)], 14),                                  # up on the bluffs
    ],
    "lakes": [(80, -40, 520, 300)],
    "meadows": [(420, 480, 160, 90, [WHITE, YELLOW]), (-420, -560, 140, 80, [BLUE, WHITE])],
    "land": [(60, -330, 90, 150)],
    "docks": [(470, -90, 640, -58)],
    # Cast off the end of Neri's dock (scripts/systems/fishing_spot.gd).
    # Off Neri's dock, and off the wreck on the south shore (casting north, into the lake).
    "fishing": [(490, -74), (-80, 290, 4, -50)],
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
        [{"sprite": KP + "candle_shrine.png", "pos": (-520, 60), "foot": (20, 8), "light": ((1.0, 0.75, 0.45, 1), 0.7, 1.0)}]
        +
        [{"sprite": "assets/sprites/tiles/lake_serin/wreck.png", "pos": (-170, 284), "foot": (64, 16), "flip": True}]
        +
        [{"sprite": STONE, "pos": (60, -300), "foot": (26, 12), "scale": 1.2, "light": ((0.7, 0.85, 1.0, 1), 0.35, 1.0)}]
        + [{"sprite": KP + "barrel.png", "pos": (610, -100), "foot": (14, 8)}]
        + [{"sprite": KP + "net_crate.png", "pos": (740, -60), "foot": (24, 10)},
           {"sprite": KP + "fishing_rods.png", "pos": (700, -40), "foot": (14, 6)}]
        + [{"sprite": BOULDER, "pos": p, "foot": (40, 18)} for p in [(-380, 250), (330, 330)]]
    ),
    "lanterns": [(640, 420), (600, -140), (130, -470), (-420, -560)],
    "npcs": [
        {"id": "neri", "name": "Neri", "pos": (680, -20), "wander": 30, "night": (560, -60), "lines": [
            "Serin's the stillest water on the island. You can hear a fish change its mind.",
            "Barges used to cross here at night, low in the water. Heading north. They don't cross any more. One of them never got across.",
        ]},
    ],
    "readables": [
        ("A lakeside shrine", (-520, 70), [
            "A little shrine of stacked stones on the west bank, candles in jars, ribbons tied to a stick. A board: 'For the ones the barges took north. The water remembers them.'",
            "Fresh candles. Somebody comes from Verdana every week to light them.",
        ], [
            "At night the candles are lit, a dozen small flames on the bank. Across the water, on the north shore, one light answers, then goes out.",
        ]),
        ("A wreck on the shore", (-120, 300), [
            "An old fishing boat on its side in the reeds, ribs showing through the planks. Fresh rope tied to the mast stump, trailing into the water.",
            "Pull the rope and something heavy shifts out in the deep. Pull harder and the rope comes up cut.",
        ]),
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
        {"id": "pilgrims_shrine", "pos": (-560, 60), "gold": 20, "item": "bread"},
        {"id": "point_cache", "pos": (110, -420), "gold": 25, "card": "serin_lily"},
    ],
    "monsters": [(BOAR, (-300, 330)), (BOAR, (320, 470)), (HOUND, (-200, -560)), (HOUND, (620, -600)), (RAM, (-40, 600))],
    "butterflies": [((600, 300), 3), ((-800, -200), 2)],
}

# ---------------------------------------------------------------- Starfall Range
def starfall_level(x, y):
    # Long gentle swells only: short, steep wiggles in a cliff line break into a
    # jagged staircase of cliff blocks.
    w = 40 * math.sin(x / 240.0)
    spur = lambda at, width: math.exp(-((x - at) / width) ** 2)
    # Rock spurs where a terrace juts out over the one below, and a bay where the
    # snow runs back into the mountain (kept clear of the stairs), broad and shallow.
    lower = w - 64 * spur(-860, 160) - 56 * spur(600, 170) + 48 * spur(80, 150)
    upper = w * 0.8 + 56 * spur(-640, 180) - 64 * spur(720, 170) - 40 * spur(-60, 150)
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
        ([(0, 790), (-60, 420), (-224, 300), (-224, 130), (100, -150), (288, -300), (288, -470), (0, -640), (-100, -820), (-100, -868)], 24),
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
        {"name": "ToFrisalle", "pos": (-100, -892), "side": "n", "gap": 24, "target": "res://scenes/world/frisalle.tscn", "spawn": "from_starfall"},
    ],
    # Frisalle's toll gate in the avalanche (data/gates/starfall_pass.tres: an Iron Wolf Collar).
    "gates": [{"id": "starfall_pass", "pos": (-100, -876), "width": 44}],
    "spawns": {"from_lake_serin": (0, 720), "from_grotto": (860, -150), "from_frisalle": (-100, -826)},
    # The Frost Grotto under the east shoulder (build_grotto.py).
    "portals": [{"name": "ToGrotto", "pos": (860, -224), "target": "res://scenes/world/starfall_grotto.tscn", "spawn": "from_starfall"}],
    "rival_spots": {"runner": (-40, 660), "raider": (40, 660), "hoarder": (0, 620)},
    "buildings": [
        {"node": "HouseHald", "sprite": SF + "hermit_cabin.png", "pos": (620, -110), "foot": 130, "door": "res://scenes/world/interiors/starfall_cabin.tscn",
         "back": "from_househald"},
    ],
    "props": (
        # A frozen climbers' camp on the high west terrace; an old adit in the east valley.
        [{"sprite": SF + "climbers_camp.png", "pos": (-830, -560), "foot": (62, 20)},
         {"sprite": SF + "old_adit.png", "pos": (780, 440), "foot": (90, 30)}]
        +
        # The pass to Frisalle: an avalanche across it, boulders and drifts twice your height,
        # dug through in the middle to a toll gate; a solid bank of boulders either side
        # of the gate, so the only way north is through it.
        [{"sprite": SNOW_BOULDER, "pos": (x, y), "foot": (52, 18), "flip": (x // 10) % 2 == 0}
         for x, y in [(-200, -846), (-150, -862), (-50, -866), (0, -848), (50, -858), (-175, -822),
                      (-25, -828), (25, -822), (-225, -820)]]
        + [{"sprite": SNOW_BOULDER, "pos": (x, -874 + (0 if x in (-146, -54) else (x * 7) % 9 - 4)), "foot": (52, 20), "flip": (x // 10) % 2 == 1}
           for x in list(range(-376, -160, 46)) + [-146, -54] + list(range(-8, 220, 46))]
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
        {"id": "hald", "name": "Hald", "pos": (540, -80), "wander": 30, "night": (520, -4), "night_wander": 10, "lines": [
            "Frisalle's over the pass. Since the slide they've set a toll gate in it: one wolf collar a head. The wolves took their goats, so they want the wolves' collars. Fair, I suppose.",
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
            "Snow and boulders to twice your height, packed hard, dug through in the middle to a stout gate. A sign hammered into the drift: 'FRISALLE. Toll: one Iron Wolf Collar. The wolves took our goats; bring us one of theirs.'",
            "Drill holes in the rock above the slide. Somebody brought it down on purpose.",
        ]),
        ("A frozen camp", (-830, -520), [
            "A tent half buried in the drift, its canvas split by the wind. A rope, an ice axe, a pack frozen to the snow.",
            "In the pack, a journal: 'Three of us. The pass is down, so we'll go over the top. Hald says we're fools. Day four: Brin's feet. Day five:' Nothing after day five.",
        ]),
        ("An old adit", (780, 470), [
            "A mine entrance boarded shut, a rusted ore cart on a stub of rail. A painted sign: 'D.M.C. NORTH WORKINGS. CLOSED.'",
            "The boards are new. The nails are new. The snow in front of it has been trodden flat by a lot of small boots.",
        ]),
        ("Frozen cart tracks", (-200, 380), [
            "Wagon ruts frozen into the old road, heading north. Deep ones: a heavy load, or a lot of people.",
        ]),
    ],
    "chests": [
        {"id": "tarn_cache", "pos": (-700, -80), "gold": 30, "item": "healers_tonic"},
        {"id": "pass_cairn", "pos": (330, -700), "gold": 50, "card": "fallen_star_shard"},
        {"id": "valley_pack", "pos": (700, 520), "item": "bread", "count": 2},
        {"id": "climbers_pack", "pos": (-770, -540), "gold": 45, "item": "healers_tonic"},
    ],
    "monsters": [(WOLF, (-400, 420)), (WOLF, (420, 450)), (WOLF, (-620, -200)), (WOLF, (240, -560)), (WOLF, (-700, -450))],
    # The Rime Stag keeps the high snowfield east of the pass.
    "boss": {"node": "RimeStag", "scene": "res://scenes/characters/rime_stag.tscn", "pos": (610, -620), "arena": 170},
}

# ---------------------------------------------------------------- Seabright Quay (the resort)
# The royal resort south of Verdana, owned by the King's nieces Sparkle and Sassy. The
# road comes down through palms to a forecourt with a fountain, stairs drop to a cobbled
# quay, and from the quay a long boardwalk runs out over clear turquoise water to the
# Saltglass Terrace, an open-air restaurant on its own deck in the bay serving Chef's
# dishes. Jetties run east and west from it, lined with private overwater bungalows (the
# far east one is the sisters' own); a diving pier runs off the terrace's sea side. The
# Seabright Grand stands on the grassy headland to the east, over the bay; west of the
# quay a white beach curls round a cove below the lawns.
RS = "assets/sprites/tiles/resort/"
K2C = K2 + "cliff/"


def resort_coast(x):
    """Where the lawns fall to the sea (west and east of the quay)."""
    if x < 0:
        return -200 + 14 * math.sin(x / 110.0)
    return -30 + 130 * math.exp(-((x - 590) / 150.0) ** 2) + 8 * math.sin(x / 70.0)


def resort_level(x, y):
    """0 the sea (and the beach), 1 the cobbled quay, 2 the lawns above."""
    if -300 <= x <= 300:
        if y > -60:
            return 0
        return 1 if y > -230 else 2
    return 0 if y > resort_coast(x) else 2


def resort_waterline(x):
    """The beach's edge: deepest in the middle of the cove."""
    return 30 + 100 * math.sin(math.pi * min(1.0, max(0.0, (x + 820) / 520.0))) + 10 * math.sin(x / 37.0)


DECK = (-160, 296, 160, 544)       # the Saltglass Terrace, out in the bay
JETTY_Y = (372, 420)               # the jetties run east and west from the terrace
BUNGALOWS = (-580, -420, -260, 260, 420, 580)   # along the north side of the jetties
COUSINS = 580                      # the sisters' own bungalow, at the far east end


def bungalow_deck(x):
    """The little plank platform each bungalow stands on, joined to the jetty."""
    return (x - 54, 312, x + 54, JETTY_Y[0] + 4)


RESORT = {
    "scene": "scenes/world/seabright_quay.tscn",
    "root": "SeabrightQuay",
    "display": "Seabright Quay, the Royal Resort",
    "art": RS,
    "bounds": (-800, -576, 800, 640),
    "level": resort_level,
    "cliffs": {(0, 1): K2C + "sea_quay", (1, 2): K2C + "quay_town", (0, 2): K2C + "sea_rock"},
    "flats": {0: ((0, 1), "lower"), 1: ((0, 1), "upper"), 2: ((1, 2), "upper")},
    "sea_level": 0,
    "sea_depth": True,
    "sea_tint": (0.86, 1.08, 1.06, 1),
    "beaches": [[(-830, -260), (-300, -260), (-300, 40)] + [(x, resort_waterline(x)) for x in range(-300, -840, -20)]],
    "stairs": [(-150, -230, 1, 2), (150, -230, 1, 2), (-640, -200, 0, 2)],
    "grade": (1.08, (1.0, 1.0, 1.0)),
    "palette": ((66, 138, 64), (124, 170, 72)),
    "dapple": 0.08,
    "dress_levels": [2],
    "tree_levels": [0, 2],
    "paths": [
        ([(-300, -600), (-300, -450), (-160, -370), (-60, -335)], 26),      # the road down from Verdana
        ([(-90, -300), (-160, -252)], 16),                                  # forecourt to the west stairs
        ([(90, -300), (128, -252)], 16),                                    # and the east stairs
        ([(-330, -440), (-600, -330), (-704, -214)], 16),                   # along the lawns to the beach steps
        ([(120, -330), (380, -250), (560, -110)], 22),                      # up to the Seabright Grand
        ([(560, -110), (600, 30)], 14),                                     # and on to the lookout
    ],
    "plazas": [(0, -320, 150, 50), (560, -104, 96, 28)],                    # the arrival forecourt, the hotel's steps
    "plaza_stone": (222, 214, 196),
    "meadows": [(-560, -440, 120, 60, [RED, WHITE, YELLOW]), (300, -460, 120, 70, [PURPLE, WHITE]), (680, -40, 60, 50, [YELLOW, WHITE])],
    "docks": [
        (-22, -90, 22, DECK[1] + 4),                    # the boardwalk out to the terrace
        DECK,
        (DECK[2] - 4, JETTY_Y[0], 710, JETTY_Y[1]),     # the east jetty (bungalows, the yachts)
        (-710, JETTY_Y[0], DECK[0] + 4, JETTY_Y[1]),    # the west jetty (bungalows, rowboats, fishing)
        (-16, DECK[3] - 4, 16, 626),                    # the diving pier off the terrace
    ] + [bungalow_deck(x) for x in BUNGALOWS],
    "dock_rails": True,
    "fishing": [(-696, 396)],
    "tree_kinds": ["palm"],
    "treeline_kinds": ["palm", "palm", "oak", "oak", "oak"],
    "groves": [(-700, -420, 5, 50), (-420, -360, 4, 45), (300, -400, 4, 45), (720, -300, 4, 40), (420, -60, 2, 30),
               (-740, -140, 3, 30), (-330, -150, 2, 20), (-760, 60, 2, 30), (160, -480, 3, 40), (720, 20, 2, 25)],
    "under": [("flowers", 5), ("grass_clump", 3), ("berry_bush", 1)],
    "patches": 22,
    "tufts": 60,
    "safe_zone": (-800, -576, 800, 640),
    "entry": (-300, -510),
    "exits": [
        {"name": "ToVerdana", "pos": (-300, -572), "side": "n", "target": "res://scenes/world/verdana.tscn", "spawn": "from_resort"},
        {"name": "ToHalmeer", "pos": (-796, -380), "side": "w", "target": "res://scenes/world/halmeer.tscn", "spawn": "from_seabright"},
    ],
    "spawns": {"from_verdana": (-300, -510), "town": (0, -260), "from_halmeer": (-730, -380)},
    "rival_spots": {"runner": (-340, -470), "raider": (-260, -470), "hoarder": (-60, -120)},
    "buildings": [
        {"node": "HouseHotel", "sprite": RS + "pavilion.png", "pos": (560, -150), "foot": 200, "depth": 96,
         "door": "res://scenes/world/interiors/seabright_hotel.tscn", "back": "from_househotel"},
        {"node": "HouseBungalow", "sprite": RS + "bungalow_cousins.png", "pos": (COUSINS, JETTY_Y[0]), "foot": 86, "depth": 44,
         "door": "res://scenes/world/interiors/seabright_bungalow.tscn", "back": "from_housebungalow"},
    ] + [
        # The guest bungalows, numbered from the west, each with its own room.
        {"node": f"Bungalow{k + 1}", "sprite": RS + "bungalow.png", "pos": (x, JETTY_Y[0]), "foot": 86, "depth": 44, "flip": x < 0,
         "door": f"res://scenes/world/interiors/seabright_bungalow{k + 1}.tscn", "back": f"from_bungalow{k + 1}"}
        for k, x in enumerate(x for x in BUNGALOWS if x != COUSINS)
    ],
    "instances": [("res://scenes/world/props/kalmora_fountain.tscn", (0, -330), 1.0)],
    "props": (
        # The beach: loungers in two rows under parasols, cabanas at the back by the
        # rocks, the beach bar where the steps come down.
        [{"sprite": RS + "lounger.png", "pos": (x, y), "foot": (30, 10)}
         for y, xs in ((-60, (-590, -545, -500)), (10, (-620, -575, -530, -485)), (-60, (-420, -375))) for x in xs]
        + [{"sprite": K2 + "props/parasol_table.png", "pos": p, "foot": (34, 12)} for p in [(-700, 40), (-430, 50)]]
        + [{"sprite": RS + "cabana.png", "pos": p, "foot": (40, 14)} for p in [(-760, -60), (-350, -110)]]
        + [{"sprite": RS + "beach_bar.png", "pos": (-520, -128), "foot": (84, 16), "light": ((1.0, 0.78, 0.5, 1), 0.9, 1.5)}]
        # The quay: a promenade of benches facing the bay, lamp posts between them,
        # café tables at the west end, planters at the head of the boardwalk.
        + [{"sprite": K2 + "props/bench.png", "pos": p, "foot": (36, 8)} for p in [(-220, -84), (-120, -84), (120, -84), (220, -84)]]
        + [{"sprite": K2 + "props/lamp_post.png", "pos": p, "foot": (10, 8), "light": ((1.0, 0.85, 0.6, 1), 0.9, 1.2)}
           for p in [(-170, -90), (170, -90)]]
        + [{"sprite": K2 + "props/parasol_table.png", "pos": p, "foot": (34, 12)} for p in [(-240, -170), (-170, -150), (240, -170)]]
        + [{"sprite": K2 + "props/potted_palm.png", "pos": p, "foot": (16, 8)} for p in [(-42, -110), (42, -110)]]
        # The forecourt: flower beds round the fountain, planters at the hotel's steps.
        + [{"sprite": K2 + "props/flower_bed.png", "pos": p, "foot": (30, 8)} for p in [(-110, -310), (110, -310)]]
        + [{"sprite": K2 + "props/potted_palm.png", "pos": p, "foot": (16, 8)} for p in [(480, -110), (640, -110)]]
        # The Saltglass Terrace: the open kitchen at the head of the deck (Pepper at the
        # pass in front of it), the menu board where the boardwalk arrives, tables under
        # parasols down to the sea, lamps and palms at the corners.
        + [{"sprite": RS + "kitchen.png", "pos": (84, 344), "foot": (134, 20)}]
        + [{"sprite": K2 + "props/notice_board.png", "pos": (-60, 330), "foot": (26, 8)}]
        + [{"sprite": K2 + "props/parasol_table.png", "pos": p, "foot": (34, 12)}
           for p in [(-104, 420), (104, 440), (-104, 516), (104, 516)]]
        + [{"sprite": K2 + "props/lamp_post.png", "pos": p, "foot": (10, 8), "light": ((1.0, 0.85, 0.6, 1), 0.9, 1.2)}
           for p in [(-148, 316), (148, 366), (-148, 534), (148, 534)]]
        + [{"sprite": K2 + "props/potted_palm.png", "pos": p, "foot": (16, 8)} for p in [(-30, 316), (30, 316)]]
        # The jetties: a fisherman's crates at the west end.
        + [{"sprite": K2 + "props/fish_crates.png", "pos": (-640, 412), "foot": (26, 8)}]
        # The headland lookout: the brass telescope on its tripod, a bench beside it.
        + [{"sprite": RS + "telescope.png", "pos": (600, 34), "foot": (16, 8)}]
        + [{"sprite": K2 + "props/bench.png", "pos": (650, 60), "foot": (36, 8)}]
        # Lamps for the night: the quay's corners and the foot of both stairs, the
        # boardwalk (posts on its pilings, alternating sides), along both jetties
        # between the bungalows and at their ends, round the fountain, up the hotel road.
        + [{"sprite": K2 + "props/lamp_post.png", "pos": p, "foot": (10, 8), "light": ((1.0, 0.85, 0.6, 1), 0.9, 1.3)}
           for p in [(-210, -206), (176, -206), (-284, -214), (284, -214),
                     (-30, 0), (30, 100), (-30, 200),
                     (-340, 428), (-500, 428), (-700, 428), (340, 428), (500, 428), (700, 428),
                     (-190, -300), (190, -300), (430, -272), (500, -108)]]
    ),
    "afloat": [(K2 + "props/rowboat.png", (-600, 450), False), (K2 + "props/rowboat.png", (-650, 456), True),
               (K2 + "props/sea_rocks.png", (740, 240), False)],
    "npcs": [
        {"id": "sparkle", "name": "Sparkle", "pos": (100, -150), "wander": 90, "night": (0, 598), "lines": [
            "Welcome to Seabright! It's ours, you know. Uncle gave it to us. Well. To Sassy and me. Mostly to me. Sassy would say mostly to her.",
            "Everyone says don't dive off the end of the pier. I own the pier. I've decided it's allowed.",
            "Uncle keeps sending guards to 'keep an eye on us'. We lost them on the first day. They're probably still looking under the boardwalk.",
            "I do the diving and the boats and the frightening the staff. Sassy does the guests and the parties. It's a system.",
            "I swam out past the yachts in the dark last night. There's a little light out on the water some nights, low down, no ship I can see. Nobody here will tell me what it is. Which means it's something.",
            "You can see the sand on the bottom all the way out to the terrace. Then it goes dark blue and you can't. That's where I go.",
            "We got Chef to send Pepper down from Vetrassa. Chef sends the recipes, Pepper cooks them, and Chef sends a very long letter every week about how she's doing it wrong.",
        ]},
        {"id": "sassy", "name": "Sassy", "pos": (-460, -24), "wander": 0, "night": (-20, 470), "night_wander": 24, "lines": [
            "Is it Tuesday? It feels like a Tuesday. Everything here feels like a Tuesday. I love it.",
            "I'm working. This is working. A hostess has to know the loungers are comfortable. All of them. Personally.",
            "Our cousins are the royals, you know. Well, everybody knows. Well, I think everybody knows. Do you know?",
            "Duke has the whole top floor of the Grand again. Duke is lovely. He always talks about mines. Gold mines? Card mines? I stop listening.",
            "The papers say the resort's a gift from Uncle. The bills come from somebody called the Duskara Mining Company. I don't open them. Sparkle doesn't open them. We have a drawer.",
            "Pepper's stew is Chef's stew, really. Chef won't come down himself. He says sand gets in the sauce.",
            "The man at the bar makes a drink that's blue. I don't know what's in it. I don't want to know. I want another one.",
        ]},
        # The Duke at his table on the terrace, two of his 'business guests' either side of
        # him and the third at the door of Bungalow 3.
        {"id": "duke", "name": "Duke", "pos": (0, 474), "wander": 0, "out": (11.0, 2.0), "lines": [
            "Ah, a racer! How thrilling. Sit, sit. Pepper, another tart for our friend. On my account. Everything here is on my account, one way or another.",
            "Chef and I were boys together in Vetrassa. He cooked, I ate. Nothing's changed except the prices, and I pay those too.",
            "Business? Oh, a little of this, a little of that. Shipping. Minerals. Hospitality. One likes to keep busy between lunches.",
            "The young ladies are delightful hostesses. Their uncle's generosity, my small investments. Everyone is happy. That is what investment is for.",
            "Duskara? Dreadfully dusty. I've never been. I have people who go. That is rather the point of having people.",
            "Frisalle? Charming. Snowy. Unlucky with avalanches, I hear. Do try the tart.",
        ]},
        *[{"id": "company_man", "node": f"Npc_company_man{k}", "name": "Company Man", "pos": p, "wander": 0, "lines": [line],
           **({"out": (11.0, 2.0)} if k < 2 else {})}
          for k, (p, line) in enumerate([((-76, 476), "..."), ((76, 476), "We're on holiday."),
                                          ((-222, 400), "This bungalow is occupied. Move along.")])],
        {"id": "waiter", "name": "Waiter", "pos": (-40, 404), "wander": 40, "lines": [
            "Table for one? Lovely. Mind the gentlemen in the suits; they don't like to be looked at. Or spoken to. Or walked past, really.",
            "The Duke tips in silver. Strange silver. Pepper won't take it in the till; she says it's still warm from somewhere.",
            "Miss Sparkle swam under the terrace this morning and came up through the kitchen hatch. Pepper screamed. The Duke applauded.",
            "Specials are on the board. The special is always the stew. Chef won't let it be anything else.",
        ]},
        {"id": "lifeguard", "name": "Lifeguard", "pos": (-560, 90), "wander": 30, "out": (7.0, 19.0), "lines": [
            "Swim between the parasols, please! Not past the yachts. And not off the pier, Miss Sparkle, I can SEE you!",
            "Calm water, clear to the bottom, warm as a bath. Best beach on the island. Worst-behaved owner.",
            "There's a current past the last bungalow that pulls you east at night. Things wash up on the headland rocks: crates, rope, once a boot.",
            "I've pulled Miss Sparkle out of the water four times this week. She's thanked me once. She says that's a fair rate.",
        ]},
        {"id": "pepper", "name": "Pepper", "pos": (84, 372), "wander": 0,
         "shop": ["seabright_stew", "chefs_tart", "bread"], "shop_title": "The Saltglass Terrace", "lines": [
            "Welcome to the Saltglass Terrace! Everything on the menu is Chef's own. I just cook it. Exactly as written. Mostly.",
            "Chef trained me in Vetrassa for six years. He sent me here with a trunk of recipes and a list of things I'm never to do to a mussel.",
            "The stew's the one they come for. Saffron, the morning's catch, and Chef's stock, which arrives sealed by courier and I'm not allowed to know what's in it.",
            "The Duke dines here every night he's in. Same table, same tart, same three quiet gentlemen who never order anything.",
            "A letter came from the inn at Sorenda saying her stew is better than Chef's. I've framed it. Chef doesn't know. Please don't tell him.",
            "Mind the gulls. They've learned what a plate looks like.",
        ]},
    ],
    "readables": [
        ("A brass plaque", (0, -124), [
            "'SEABRIGHT QUAY. Opened by Royal Charter for the rest and pleasure of the Crown's friends. Given by His Majesty into the keeping of the Ladies Sparkle and Sassy.'",
            "Smaller, underneath: 'Built through the generosity of the Duskara Mining Company.'",
        ]),
        ("The Saltglass menu", (-60, 340), [
            "THE SALTGLASS TERRACE. 'The dishes of Chef, of Vetrassa, prepared by Pepper.'",
            "Seabright Stew: saffron, mussels, prawns, the morning's catch. Lemon Tart: Chef's own. Bread: from the oven, when the oven agrees.",
            "At the bottom, in a different hand: 'Private dining for the Company's guests by arrangement. Ask Fennick.'",
        ]),
        ("The pier sign", (-34, 540), [
            "'NO DIVING FROM THE PIER.' Somebody has scratched a little crown under it, and the words 'except us'.",
        ]),
        ("A bungalow door", (-298, 388), [
            "A brass number plate: 'Bungalow 3. Do not disturb.' A tray of untouched breakfast outside. Someone inside is talking quietly about tonnage.",
        ], [
            "The window's dark now, but the step is wet: sea water, and boot prints leading off to the end of the jetty.",
            "A coil of wet rope under the bench. A crate lid propped against the wall, stencilled D.M.C. The lamp in the window is still warm.",
        ]),
        ("A lookout on the headland", (600, 48), [
            "A brass telescope on a post, pointed east along the coast. Through it: open sea, and very far off, a barge with no lights, riding low.",
        ], [
            "Through the telescope, out past the yachts: a barge with no lights, riding low. Then a lantern on it opens and shuts. Three short. One long.",
            "Behind you, down on the west jetty, a bungalow window answers: three short, one long. Then everything is dark again.",
        ]),
        ("The bar's chalkboard", (-470, -112), [
            "'TODAY: the Seabright Blue. Ask for it by name. Do not ask what is in it.' Under it, smaller: 'Racers: cash only.'",
        ]),
    ],
    "butterflies": [((-560, -440), 3), ((300, -440), 3), ((680, -40), 2)],
    # The yachts moored off the east jetty, bobbing (a PixelLab-animated strip).
    "decor": [{"strip": RS + "anim/yacht_bob.png", "frames": 7, "fps": 4, "pos": (x, y + 33), "flip": f, "afloat": True}
              for (x, y), f in [((300, 476), False), ((430, 482), True), ((560, 560), False)]],
    # A bonfire on the beach for the evenings.
    "campfires": [(-640, 104)],
    # Lanterns strung over the Saltglass Terrace and along the quay.
    "string_lights": [((-148, 316), (-148, 534), 16), ((148, 366), (148, 534), 16), ((-148, 316), (148, 366), 20),
                      ((-148, 534), (148, 534), 18), ((-170, -90), (170, -90), 22),
                      # the waterfront along the sea wall, and over the café tables at the back
                      ((-290, -20), (-34, -20), 10), ((34, -20), (290, -20), 10),
                      ((-284, -214), (-60, -200), 16), ((60, -200), (284, -214), 16)],
    "gulls": [((-200, 160), 3, (180, 70)), ((380, 240), 2, (140, 60)), ((-520, 120), 2, (120, 50))],
}

# ---------------------------------------------------------------- Frisalle (the snow village)
# North over the Starfall pass, through Frisalle's toll gate. The road climbs from a
# lower valley (a frozen pond, wolves at the edges) up stairs onto the village terrace:
# a snowy square round the weigh house, the Hearth & Horn inn, chalets with carved
# balconies, a frozen skating pond. Above it all, on the upper terrace, the counting
# house of the trading factors and the bell tower. Alpine chalets, steep roofs, blue
# shadows; snow falling.
FR = "assets/sprites/tiles/frisalle/"


def frisalle_level(x, y):
    """0 the valley (the pass road), 1 the lower lane, 2 the upper lane, 3 the top
    terrace: the village climbs the mountain in steps, each lane backed by the cliff
    of the one above."""
    w = 18 * math.sin(x / 150.0)
    if y > 360 + w:
        return 0
    if y > 120 + w * 0.8:
        return 1
    if y > -120 + w * 0.6:
        return 2
    return 3


FRP = FR + "props/"


# Chimney tops on each building sprite: (sprite w, h, chimney x, chimney top y).
CHIMNEYS = {"chalet_red.png": [(117, 96, 86, 8)], "chalet_green.png": [(117, 97, 85, 10)],
            "chalet_brown.png": [(116, 98, 83, 7)], "inn.png": [(148, 162, 44, 18), (148, 162, 100, 15)]}


def smoke(sprite, x, y, flip=False):
    """Animated smoke (a PixelLab strip) rising from each chimney of a building drawn
    with its bottom centre at (x, y)."""
    return [{"strip": FR + "anim/chimney_smoke.png", "frames": 9, "fps": 5,
             "pos": (x - w / 2 + (w - cx if flip else cx), y - h + cy)} for w, h, cx, cy in CHIMNEYS[sprite]]


def chalet(sprite, x, y, flip=False):
    """A private chalet (no way in): drawn and solid like a building, but a prop."""
    return {"sprite": FR + sprite, "pos": (x, y), "foot": (104, 40), "flip": flip, "glow": True}


FRISALLE = {
    # A mountain village that climbs: no square, a street that switchbacks up four
    # heights. The pass road comes into the valley (the frozen pond, the fire pit),
    # stairs at the west end lead up to the lower lane (the weigh house where the carts
    # come in, the Hearth & Horn, Liesl's workshop), stairs at its east end to the upper
    # lane (Bodo's house, Sven's lodge, the stalls, the goat pen), and stairs at the
    # west end again to the top: the factors' counting house over everything, the bell
    # tower, and the cave mouth of the ice road. Every house backs onto the cliff of
    # the lane above.
    "scene": "scenes/world/frisalle.tscn",
    "root": "Frisalle",
    "display": "Frisalle, the Village Under the Stars",
    "art": FR,
    "bounds": (-832, -640, 832, 640),
    "cliff": SF + "cliff/snow",
    "level": frisalle_level,
    "tall_walls": {(0, 1): 1, (1, 2): 1, (2, 3): 1},
    "stairs": [(-520, 360, 0, 1), (520, 120, 1, 2), (-300, -120, 2, 3)],
    "grade": (0.95, (0.98, 1.0, 1.05)),
    "dapple": 0.08,
    "snow": True,
    "snowfall": True,
    "paths": [
        ([(0, 650), (0, 560), (-260, 520), (-544, 500), (-544, 410)], 24),       # the pass road up the valley
        ([(-544, 326), (-520, 268), (620, 268)], 22),                            # the lower lane
        ([(520, 268), (520, 40)], 18),                                          # up the east stairs
        ([(560, 44), (-640, 44), (-850, 44)], 22),                             # the upper lane, on west as the road down to Vetrassa
        ([(-256, 44), (-256, -190)], 18),                                        # up the west stairs
        ([(-256, -190), (420, -190)], 20),                                       # along the top
        ([(420, -190), (560, -360), (620, -520)], 14),                           # the cart ruts to the ice road
    ],
    "plazas": [(220, -182, 100, 22), (-280, 268, 70, 20)],
    "plaza_stone": (184, 192, 206),
    "ice": [(-420, 570, 170, 44)],
    "tree_kinds": ["pine"],
    "groves": [(-700, -500, 6, 50), (-120, -520, 4, 50), (760, -300, 3, 40), (-760, 560, 3, 40), (760, 560, 3, 40),
               (-740, -60, 2, 25), (740, 20, 2, 25),
               # stands of snowy pines on the empty upper slope and at the ends of the lanes
               (560, -440, 5, 60), (-520, -440, 3, 40), (380, -560, 3, 40), (-680, 200, 3, 30), (700, 220, 2, 26),
               (-300, 520, 3, 40), (420, 530, 3, 40)],
    "under": [("snow_shrub", 3), ("frost_grass", 3), ("snow_rocks", 1)],
    "solid_under": ["snow_rocks"],
    "patches": 18,
    "safe_zone": (-832, -640, 832, 456),
    "entry": (0, 580),
    "exits": [
        {"name": "ToStarfall", "pos": (0, 636), "side": "s", "target": "res://scenes/world/starfall_range.tscn", "spawn": "from_frisalle"},
        {"name": "ToVetrassa", "pos": (-828, 44), "side": "w", "target": "res://scenes/world/vetrassa.tscn", "spawn": "from_frisalle"},
    ],
    # The ice road: the smugglers' tunnel out of the Frost Grotto, at the top of the village.
    "portals": [{"name": "ToGrotto", "pos": (620, -580), "target": "res://scenes/world/starfall_grotto.tscn", "spawn": "from_frisalle"}],
    "spawns": {"from_starfall": (0, 580), "town": (-60, 272), "from_grotto": (620, -500), "from_vetrassa": (-760, 44)},
    "rival_spots": {"runner": (-40, 560), "raider": (40, 560), "hoarder": (-20, 278)},
    "buildings": [
        # The lower lane.
        {"node": "HouseInn", "sprite": FR + "inn.png", "pos": (80, 240), "foot": 140,
         "door": "res://scenes/world/interiors/frisalle_inn.tscn", "back": "from_houseinn"},
        {"node": "HouseCarver", "sprite": FR + "chalet_red.png", "pos": (340, 240), "foot": 110,
         "door": "res://scenes/world/interiors/frisalle_carver.tscn", "back": "from_housecarver"},
        # The upper lane.
        {"node": "HouseWeigh", "sprite": FR + "chalet_brown.png", "pos": (-80, 20), "foot": 110,
         "door": "res://scenes/world/interiors/frisalle_weighmaster.tscn", "back": "from_houseweigh"},
        {"node": "HouseGuide", "sprite": FR + "chalet_green.png", "pos": (330, 20), "foot": 110,
         "door": "res://scenes/world/interiors/frisalle_guide.tscn", "back": "from_houseguide"},
        # The top.
        {"node": "HouseCounting", "sprite": FR + "counting_house.png", "pos": (220, -214), "foot": 118,
         "door": "res://scenes/world/interiors/frisalle_counting.tscn", "back": "from_housecounting"},
    ],
    "props": (
        # The lower lane: the weigh house where the carts come up from the pass, a loaded sled.
        [{"sprite": FR + "weigh_house.png", "pos": (-250, 244), "foot": (104, 22)}]
        + [{"sprite": FRP + "sled.png", "pos": (-150, 250), "foot": (52, 14)}]
        + [chalet("chalet_green.png", -640, 240, True), chalet("chalet_brown.png", 560, 240)]
        + [{"sprite": FRP + "woodpile.png", "pos": (450, 250), "foot": (70, 14)}]
        # The upper lane: the knitwear stall, neighbours' chalets, the goat pen at the west end.
        + [{"sprite": FRP + "stall_knits.png", "pos": (120, 28), "foot": (60, 14)}]
        + [chalet("chalet_red.png", -440, 20), chalet("chalet_brown.png", 560, 20, True)]
        + [{"sprite": FRP + "woodpile.png", "pos": (-200, 28), "foot": (70, 14), "flip": True},
           {"sprite": FRP + "sled_blue.png", "pos": (430, 34), "foot": (52, 14)}]
        + [{"sprite": FRP + "fence.png", "pos": (x, y), "foot": (58, 8)} for x, y in
           [(-780, -30), (-722, -30), (-664, -30), (-780, 30), (-664, 30)]]
        # The top: the bell tower, the chalets of the better-off, the cave of the ice road.
        + [{"sprite": FR + "bell_tower.png", "pos": (-360, -250), "foot": (44, 18)}]
        # The guides' graveyard beside the bell tower, fenced in iron: a row of stones,
        # the newest (Anselm's) at the end with fresh flowers.
        + [{"sprite": FRP + "grave_" + "abcab"[i] + ".png", "pos": (-740 + i * 40, -330 + (i % 2) * 6), "foot": (22, 8)} for i in range(5)]
        + [{"sprite": FRP + "grave_c.png", "pos": (-740 + 5 * 40, -330), "foot": (22, 8)}]
        + [{"sprite": FRP + "iron_fence.png", "pos": (x, -380), "foot": (56, 8)} for x in (-750, -690, -630, -570, -510)]
        + [chalet("chalet_green.png", -150, -250), chalet("chalet_red.png", 40, -240, True)]
        + [{"sprite": SF + "ice_cave_mouth.png", "pos": (620, -552), "feet": [(-56, -20, 50, 40), (56, -20, 50, 40), (0, -52, 64, 22)],
            "light": ((0.55, 0.85, 1.0, 1), 0.5, 1.0)}]
        # The valley: the skating pond and its snowman, the signpost at the stairs.
        + [{"sprite": FRP + "snowman.png", "pos": (-250, 600), "foot": (26, 10)}]
        + [{"sprite": FRP + "signpost.png", "pos": (-430, 470), "foot": (16, 8)}]
        + [{"sprite": SNOW_BOULDER, "pos": p, "foot": (52, 18), "flip": i % 2 == 1} for i, p in enumerate(
            [(-760, 470), (330, 600), (760, 480), (-700, -400), (720, -440)])]
        + [{"sprite": ICE, "pos": p, "foot": (28, 10), "light": ((0.55, 0.85, 1.0, 1), 0.6, 0.9)} for p in
           [(-480, -500), (300, -560), (-780, 620), (600, 620)]]
    ),
    # Smoke from every chimney in the village.
    "decor": [d for args in [("inn.png", 80, 240), ("chalet_red.png", 340, 240), ("chalet_brown.png", -80, 20),
                             ("chalet_green.png", 330, 20), ("chalet_green.png", -640, 240, True), ("chalet_brown.png", 560, 240),
                             ("chalet_red.png", -440, 20), ("chalet_brown.png", 560, 20, True), ("chalet_green.png", -150, -250),
                             ("chalet_red.png", 40, -240, True)] for d in smoke(*args)],
    # The card merchant keeps the toy stall on the upper lane (scenes/systems/merchant.tscn).
    "merchant": ((-240, 32), FRP + "stall_toys.png"),
    "campfires": [(220, 540)],
    # Lanterns stand between the houses on the cliff side of each lane, never on the lip.
    "lanterns": [(-420, 250), (-100, 250), (220, 250), (480, 250), (-560, 30), (-180, 30), (180, 30), (460, 30),
                 (-53, -230), (120, -200), (-460, 520), (100, 600)],
    "string_lights": [((-200, 222), (200, 222), 16), ((-180, 0), (240, 0), 16), ((120, -232), (320, -232), 12)],
    "npcs": [
        {"id": "bodo", "name": "Bodo", "pos": (-190, 272), "wander": 0, "out": (6.0, 21.0), "lines": [
            "Weigh master. Everything that comes into Frisalle comes across my scales. Everything.",
            "Carts? No, no carts since the slide. Well. Hardly any. The scales are for... flour. Mostly flour.",
            "My house? Inherited. From an uncle. A very generous uncle. Why do you ask?",
            "The factors pay me to weigh, not to wonder. I recommend it. Weighing. Not wondering.",
            "Lovely evening for staying indoors, racer. All evening. Whatever you hear.",
        ]},
        {"id": "liesl", "name": "Liesl", "pos": (400, 272), "wander": 30, "out": (7.0, 20.0), "lines": [
            "Mind the shavings. Everything in Frisalle is carved by me or by the frost, and the frost does the cleaner job.",
            "I carved the bell tower's star. Gold leaf over pine. From the square it looks like the real thing. Most things here do.",
            "The children used to buy my little wolves. Now the wolves come down to the village by themselves and nobody's buying.",
            "Bodo bought a carved armchair off me last month. Paid in coin, too much coin, and asked me to forget I'd sold it.",
            "There's a night every winter when the stars fall into the snow up the pass. We go up and gather the shards. Went up this year. Found tracks instead. Cart tracks, going into the mountain.",
        ]},
        {"id": "sven", "name": "Sven", "pos": (380, 48), "wander": 30, "night": (180, 560), "night_wander": 20, "lines": [
            "Sven. I guide folk over the pass. Did. Then the slide came down, very tidy, right where the road was.",
            "Somebody drilled the rock above the pass and brought it down. Don't let anyone tell you it was the weather. Weather doesn't use drills.",
            "The wolves have been bold since the slide. You can thank them for the toll. Ottilie's idea: one collar a head.",
            "There's another way through the mountain, if you're a smuggler or a fool. The ice caves. I won't take anyone. I'm neither.",
            "The south road runs on down to Duskara if you go far enough. Nobody from here goes far enough, and nobody from there comes back up it.",
        ]},
        # Goats in the pen at the west end of the upper lane.
        *[{"id": "goat", "node": f"Npc_goat{k}", "name": "Mountain Goat", "pos": p, "wander": 16, "offset": -16.0, "lines": [line]}
          for k, (p, line) in enumerate([((-740, 0), "Meh."), ((-700, -10), "Meh-eh."), ((-720, 10), "...Mehh.")])],
    ],
    "readables": [
        ("The weigh house tally board", (-300, 268), [
            "Chalk on slate, columns ruled straight: date, cart, weight, sealed by. Bodo's square hand.",
            "Since the slide: 'nil, nil, nil' all down the 'over the pass' column. And then a second column, unheaded, that isn't nil at all. Forty carts this winter, heavy ones, all 'sealed by' the same little crossed-pick mark.",
        ]),
        ("The guides' graves", (-540, -300), [
            "Six stones in a row, each carved with an ice axe and a name: guides of the Starfall pass, lost to the mountain over a hundred winters.",
            "The last is new, the snow brushed off it every morning: 'ANSELM. He knew the way.' Ottilie's handwriting on the tag of the wreath.",
        ]),
        ("The bell tower", (-410, -226), [
            "A carved gold star on the spire, and a bronze bell green with age. Carved round the door: the names of every guide lost on the pass.",
            "The last name is fresh: Anselm, the year of the slide.",
        ]),
        ("The toll hut notice", (60, 560), [
            "'TRAVELLERS. Frisalle welcomes all who pay the toll at the pass. Wolves are not travellers. The Hearth & Horn serves supper at dusk.'",
        ]),
        ("The frozen pond", (-200, 540), [
            "Skates hung on a peg by the bank. Scratched into the ice, in a child's careful hand: a crown, and a little figure under it, and another, and another.",
        ]),
        ("The signpost", (-430, 484), [
            "Three arrows. 'THE PASS' (south). 'THE HEARTH & HORN' (west, with a little painted horn). The third has been sawn off; the stump points north, at the mountain.",
        ]),
    ],
    "chests": [
        {"id": "bell_tower", "pos": (-440, -270), "card": "snowglass_lantern", "gold": 20},
        {"id": "valley_cache", "pos": (720, 600), "gold": 40, "item": "healers_tonic"},
    ],
    "monsters": [(WOLF, (-700, 600)), (WOLF, (650, 560))],
    "butterflies": [],
}

# ---------------------------------------------------------------- Siroth Dunes
# West of the plains, through the rockfall on the dune road (two of the "fallen"
# rocks rolled aside, just wide enough for a cart). Open dunes between red sandstone
# mesas: the Company's haul road runs from the plains west through a canyon to
# Duskara; Zahra keeps a caravan camp at the Sunwell oasis in the middle; up on the
# north mesa, the Sun Temple's columns (the fourth carving of the crown and the
# small figures); in the south the Bone Hollow, where a sand serpent's skeleton lies
# half buried, and under the sand beside it, Hollowmaw, the living one (Siroth's
# boss, scripts/characters/sand_serpent.gd); and below the south
# mesa the D.M.C. waystation, where the carts stop to water and to count.
SR = "assets/sprites/tiles/siroth/"
SRP = SR + "props/"
DK = "assets/sprites/tiles/duskara/"
CARACAL = "res://scenes/characters/dune_caracal.tscn"
LION = "res://scenes/characters/sand_lion.tscn"
# Mesas (level 2). Edges kept near horizontal or vertical: a slanting cliff line
# breaks into a staircase of cliff blocks.
NORTH_MESA = [(-1300, -1000), (1300, -1000), (1300, -250), (1020, -250), (1020, -600), (700, -600), (700, -440),
              (180, -440), (180, -600), (-480, -600), (-480, -680), (-1020, -680), (-1020, -170), (-1300, -170)]
SOUTH_MESA = [(-1300, 1000), (1300, 1000), (1300, 260), (1060, 260), (1060, 700), (860, 700), (860, 780),
              (280, 780), (280, 840), (-320, 840), (-320, 720), (-1040, 720), (-1040, 380), (-1300, 380)]
LOOKOUT = [(-700, -380), (-430, -380), (-430, -190), (-700, -190)]


def siroth_level(x, y):
    # Long gentle swells only (short wiggles break a cliff into a staircase of blocks).
    px, py = x + 30 * math.sin(y / 230.0 + 0.5), y + 26 * math.sin(x / 260.0 + 1.3)
    return 2 if in_poly(px, py, NORTH_MESA) or in_poly(px, py, SOUTH_MESA) or in_poly(px, py, LOOKOUT) else 1


TEMPLE = (440, -760)
OASIS = (-60, -60)
TEMPLE_RING = [(round(TEMPLE[0] + 150 * math.cos(a)), round(TEMPLE[1] + 70 * math.sin(a)))
               for a in [math.pi * (1.1 + 0.8 * i / 5) for i in range(6)]]

SIROTH = {
    "scene": "scenes/world/siroth_dunes.tscn",
    "root": "SirothDunes",
    "display": "The Siroth Dunes, Road to Duskara",
    "art": SR,
    "bounds": (-1280, -960, 1280, 960),
    "cliff": SR + "cliff/sandstone",
    "level": siroth_level,
    "tall_walls": {(1, 2): 1},
    "stairs": [(440, -440, 1, 2), (-565, -190, 1, 2)],
    "grade": (1.0, (1.0, 1.0, 1.0)),
    "desert": True,
    "treeline": False,
    "dapple": 0.06,
    "dirt": (176, 134, 90),
    "paths": [
        # The haul road: in from the plains, round the oasis, west through the canyon.
        ([(1300, 0), (900, 20), (520, 120), (200, 170), (-120, 150), (-460, 90), (-800, 110), (-1300, 100)], 28),
        ([(400, 140), (480, -280), (480, -470), (460, -560), (440, -680)], 16),  # up to the Sun Temple
        ([(-200, 150), (-400, 300), (-560, 470)], 14),                      # down into the Bone Hollow
        ([(620, 110), (600, 400), (600, 640)], 16),                          # down to the waystation
        ([(-460, 90), (-565, -60), (-565, -200)], 12),                       # up the lookout butte
    ],
    "lakes": [(OASIS[0], OASIS[1], 150, 80)],
    "deep": (30, 104, 112),
    "water_tint": (0.9, 1.08, 1.06, 1),
    "tree_kinds": ["palm"],
    "groves": [(-60, -190, 7, 70), (-240, -40, 4, 40), (130, 20, 4, 40), (-150, 60, 3, 40)],
    "under_dir": SRP,
    "under": [("dry_bush", 4), ("tumbleweed", 2), ("cactus_barrel", 2), ("cactus_cluster", 2), ("cactus_tall", 1),
              ("thorn_bush", 2), ("rubble_small", 2)],
    "solid_under": ["cactus_barrel", "cactus_cluster", "cactus_tall", "rubble_small"],
    "patches": 45,
    "tufts": 0,
    "no_reeds": ["cattails"],
    "entry": (1200, 0),
    "exits": [
        {"name": "ToAurewind", "pos": (1276, 0), "side": "e", "target": "res://scenes/world/aurewind_plains.tscn", "spawn": "from_dunes"},
        {"name": "ToDuskara", "pos": (-1276, 100), "side": "w", "target": "res://scenes/world/duskara.tscn", "spawn": "from_dunes"},
    ],
    "spawns": {"from_aurewind": (1200, 0), "from_duskara": (-1200, 100), "from_mine": (-960, 495)},
    "rival_spots": {"runner": (1100, -40), "raider": (1100, 60), "hoarder": (1060, 10)},
    "props": (
        # The Sun Temple on the north mesa: a ring of broken columns behind the altar.
        [{"sprite": SR + ("column_a.png", "column_b.png", "column_c.png")[k % 3], "pos": p, "foot": (24, 12)}
         for k, p in enumerate(TEMPLE_RING)]
        + [{"sprite": ALTAR, "pos": (TEMPLE[0], TEMPLE[1] + 10), "foot": (56, 16), "light": ((1.0, 0.8, 0.45, 1), 0.35, 1.2)}]
        + [{"sprite": SRP + "rubble.png", "pos": p, "foot": (30, 12)} for p in [(250, -660), (640, -660), (580, -880)]]
        # Zahra's caravan camp by the oasis: the tent, pots, the cart.
        + [{"sprite": SR + "tent.png", "pos": (250, -150), "foot": (70, 20)},
           {"sprite": SRP + "pots_cluster.png", "pos": (180, -130), "foot": (26, 10)},
           {"sprite": SRP + "amphora.png", "pos": (320, -136), "foot": (12, 6)},
           {"sprite": KP + "cart.png", "pos": (340, -80), "foot": (28, 12)}]
        # The Bone Hollow: the serpent's skeleton half sunk in the sand, skulls, rubble.
        + [{"sprite": SR + "serpent_bones.png", "pos": (-880, 590), "feet": [(-50, -10, 40, 14), (10, -20, 50, 12), (56, -4, 40, 14)], "scale": 1.5},
           {"sprite": SRP + "skull_bones.png", "pos": (-360, 420), "foot": (20, 8)},
           {"sprite": SRP + "skull_bones.png", "pos": (-880, 520), "foot": (20, 8), "flip": True}]
        # The escape line's hatch: where the crawl from the North Shaft comes up.
        + [{"sprite": SR + "hatch.png", "pos": (-960, 470)}]
        # The D.M.C. waystation: ore carts lined up, water jars, crates, a cairn.
        + [{"sprite": KP + "cart.png", "pos": p, "foot": (28, 12), "scale": 1.2} for p in [(700, 470), (760, 500), (820, 530)]]
        + [{"sprite": SRP + "pots_big.png", "pos": (680, 580), "foot": (30, 12)},
           {"sprite": KP + "crates.png", "pos": (740, 610), "foot": (26, 8), "scale": 1.1},
           {"sprite": SRP + "rock_stack.png", "pos": (470, 420), "foot": (22, 10)}]
        # Mile stones along the haul road, and a signpost at the canyon.
        + [{"sprite": SRP + "rock_stack.png", "pos": p, "foot": (22, 10)} for p in [(900, 70), (-300, 200), (-900, 160)]]
        + [{"sprite": KP + "signpost.png", "pos": (-1060, 40), "foot": (8, 6)}]
        # Rubble under the cliffs.
        + [{"sprite": SRP + "rubble.png", "pos": p, "foot": (30, 12)} for p in [(-990, -120), (980, -200), (-1000, 430), (1010, 310), (100, -390)]]
    ),
    "campfires": [(260, -60)],
    "lanterns": [(140, -110), (-260, -120), (600, 380), (-1000, 150), (470, -520)],
    "npcs": [
        {"id": "zahra", "name": "Zahra", "pos": (200, -60), "wander": 30, "lines": [
            "Water first, questions after. The Sunwell's the only sweet water between the plains and Duskara. Drink.",
            "I've guided caravans across Siroth for twenty years. The dunes move, the road moves, the Company's carts never stop.",
            "The carts go west full of food and come back east full of crates, under canvas, always at night. I don't ask what's in them. I've stopped asking.",
            "Mind the sand lions. They sleep in the heat and hunt at dusk, and they've learned the carts mean food.",
            "There's a temple up on the north mesa older than any king. Sun on every column. Go up at noon and the stones are warm as bread.",
            "My cousin Rafi sells water in Duskara. Tell him the bell still rings. He'll know what it means.",
        ]},
    ],
    "readables": [
        ("The Sun Temple altar", (TEMPLE[0], TEMPLE[1] + 50), [
            "An altar on the mesa, ringed with broken columns, each one carved with a rising sun. On the altar's face, worn almost smooth: a crown, and under it a long line of small figures, each one smaller than the last, walking down into the ground.",
            "Someone has cut a new line into the stone, crisp and recent: a little figure walking back up.",
        ]),
        ("The serpent's skull", (-780, 640), [
            "A skull the size of a cart, horned, its jaw sunk in the sand. Whatever this was, it was longer than the Kalmora quay.",
            "The sand around the bones is ridged in long curves, as though something heavy has been through it. Recently.",
        ]),
        ("The waystation board", (620, 650), [
            "A tally board nailed to a post: 'D.M.C. WAYSTATION. CARTS WATER HERE. HEADS COUNTED HERE.' Columns of marks, a total at the bottom of each.",
            "The 'out' column is longer than the 'in' column. Every week.",
        ]),
        ("A hatch in the sand", (-920, 470), [
            "A trapdoor of grey boards, half buried by drifting sand, with a green sun painted faintly on one board. It's nailed shut from below.",
            "The sand round it is swept smooth, the way you'd sweep away footprints.",
        ]),
        ("The canyon signpost", (-1060, 70), [
            "'DUSKARA. Property of the Duskara Mining Company. Visitors welcome at the Cistern. Visitors do not go past the upper gate.'",
        ]),
        ("A half-buried cart", (880, 570), [
            "An ore cart buried to its axles. Inside: a child's sandal, very small, and a brass tag on a string, stamped with a number and a red sun.",
        ]),
    ],
    "chests": [
        {"id": "sun_temple", "pos": (TEMPLE[0] + 90, TEMPLE[1] - 30), "card": "sunstone_shard", "gold": 30},
        {"id": "lookout_cache", "pos": (-600, -320), "gold": 45, "item": "healers_tonic"},
        {"id": "bone_hollow", "pos": (-990, 670), "gold": 35, "item": "bread", "count": 2},
        {"id": "oasis_pack", "pos": (330, -30), "gold": 15, "item": "bread"},
    ],
    # Hollowmaw, the sand serpent, hunts under the Bone Hollow beside its mate's bones.
    "boss": {"node": "SandSerpent", "scene": "res://scenes/characters/sand_serpent.tscn", "pos": (-560, 540), "arena": 170},
    "monsters": [(CARACAL, (700, -150)), (CARACAL, (-300, 420)), (CARACAL, (-800, -60)), (CARACAL, (300, 500)),
                 (LION, (-180, 560)), (LION, (900, 380)), (LION, (-850, -420))],
    "butterflies": [],
}

# ---------------------------------------------------------------- Duskara
# The desert town at the end of the haul road, packed into a red canyon bowl: the road
# comes in through the canyon mouth in the east to the bazaar (spice stalls under
# striped awnings round the old cistern, the card merchant). A row of houses stands
# shoulder to shoulder along its north side, the Cistern inn under its blue dome in
# the middle; another row along the south lane, Oren's glassworks glowing among them.
# A lane between the houses climbs the stairs, past two Company men, to the Company's
# terrace under the north rim: the D.M.C. office and the mine shaft, chained shut,
# where the foreman keeps her count. The mine itself is for "Beneath the Dunes" (to
# come); its door is a prop for now. South-east of the bazaar, under the haul road,
# the Card Souk: five stalls in a row behind a sandstone arch hung with card
# bunting, each its own trade (spells, brews, charms, way-cards for every town, and
# a broker who sells the island's own set cards, fresh from the seam).
SOUK = (458, 290)                         # the souk's paving
SOUK_STALLS = [290, 374, 458, 542, 626]   # stall x positions, along its north side
SOUK_ROW = 244                            # the stalls' feet
SKP = DK + "souk/"
BOWL = [(-680, -620), (680, -620), (680, -40), (900, -40), (900, 300), (680, 300), (680, 540), (-680, 540)]
TERRACE_Y = -300
BAZAAR = (60, 130)
NORTH_ROW = -60          # the north row's doorsteps (sprite bottoms)
SOUTH_ROW = 400          # the south row's


def duskara_level(x, y):
    px, py = x + 18 * math.sin(y / 210.0 + 0.4), y + 16 * math.sin(x / 250.0 + 1.1)
    if not in_poly(px, py, BOWL):
        return 3
    return 2 if py < TERRACE_Y else 1


def row_home(sprite, x, y):
    """A neighbour's house in a row: private, so a prop, with glowing windows."""
    tall = "tower" in sprite
    return {"sprite": DK + sprite, "pos": (x, y), "foot": ((76 if tall else 106), (60 if tall else 44)), "glow": True}


DUSKARA = {
    "scene": "scenes/world/duskara.tscn",
    "root": "Duskara",
    "display": "Duskara, Town of the Deep Well",
    "art": DK,
    "bounds": (-800, -736, 800, 672),
    "cliff": SR + "cliff/sandstone",
    "level": duskara_level,
    "tall_walls": {(1, 2): 1, (2, 3): 2, (1, 3): 2},
    "stairs": [(-56, TERRACE_Y, 1, 2)],
    "grade": (1.0, (1.0, 1.0, 1.0)),
    "desert": "town",
    "treeline": False,
    "dapple": 0.06,
    "dirt": (184, 146, 104),
    "plaza_stone": (214, 182, 136),
    "paths": [
        ([(900, 130), (600, 130), (BAZAAR[0] + 190, BAZAAR[1])], 30),                     # the haul road in from the canyon
        ([(BAZAAR[0] - 190, BAZAAR[1]), (-400, 120), (-640, 110)], 24),                   # west to the end of the bowl
        ([(BAZAAR[0], BAZAAR[1] - 80), (BAZAAR[0], NORTH_ROW + 10)], 22),                 # to the Cistern's door
        ([(-60, BAZAAR[1] - 40), (-56, NORTH_ROW), (-56, TERRACE_Y + 20)], 22),           # the lane up to the stairs
        ([(-56, TERRACE_Y - 60), (-56, -420), (-300, -440)], 20),                          # the terrace: to the office
        ([(-56, -420), (240, -450)], 20),                                                  # and to the mine
        ([(-640, SOUTH_ROW + 20), (640, SOUTH_ROW + 20)], 20),                             # the south lane
        ([(-250, 140), (-250, SOUTH_ROW + 20)], 18),                                       # down between the houses
        ([(230, 150), (230, SOUTH_ROW + 20)], 18),
        ([(SOUK[0], SOUK[1] + 60), (SOUK[0], SOUTH_ROW + 20)], 20),                       # through the souk's arch
        ([(-560, NORTH_ROW + 10), (-560, 110)], 14),                                       # Rafi's door
    ],
    "plazas": [(BAZAAR[0], BAZAAR[1], 200, 92), (SOUK[0], SOUK[1], 210, 82)],
    "pools": [(BAZAAR[0] - 44, BAZAAR[1] - 20, BAZAAR[0] + 44, BAZAAR[1] + 16)],          # the town cistern
    "tree_kinds": ["palm"],
    "groves": [(-640, 260, 2, 30), (620, 230, 2, 30), (-120, 270, 1, 20)],
    "under_dir": SRP,
    "under": [("dry_bush", 3), ("cactus_barrel", 1), ("rubble_small", 2), ("tumbleweed", 1)],
    "solid_under": ["cactus_barrel", "rubble_small"],
    "patches": 8,
    "tufts": 0,
    "safe_zone": (-680, -620, 900, 540),
    "entry": (740, 130),
    "exits": [
        {"name": "ToDunes", "pos": (796, 130), "side": "e", "target": "res://scenes/world/siroth_dunes.tscn", "spawn": "from_duskara"},
    ],
    "spawns": {"town": (BAZAAR[0] + 230, BAZAAR[1] + 20), "from_dunes": (740, 130), "from_mine": (250, -460)},
    # Down the North Shaft (the tally gate is at the bottom, at the lift landing).
    "portals": [{"name": "ToMine", "pos": (250, -500), "target": "res://scenes/world/duskara_mine.tscn", "spawn": "from_duskara"}],
    "rival_spots": {"runner": (520, 100), "raider": (520, 170), "hoarder": (580, 140)},
    "buildings": [
        {"node": "HouseInn", "sprite": DK + "inn.png", "pos": (BAZAAR[0], NORTH_ROW), "foot": 144,
         "door": "res://scenes/world/interiors/duskara_inn.tscn", "back": "from_houseinn"},
        {"node": "HouseRafi", "sprite": DK + "house_a.png", "pos": (-560, NORTH_ROW), "foot": 106,
         "door": "res://scenes/world/interiors/duskara_rafi.tscn", "back": "from_houserafi"},
        {"node": "HouseGlass", "sprite": DK + "glassworks.png", "pos": (40, SOUTH_ROW), "foot": 128, "door_dx": -12,
         "door": "res://scenes/world/interiors/duskara_glassworks.tscn", "back": "from_houseglass"},
        {"node": "HouseOffice", "sprite": DK + "company_office.png", "pos": (-300, -460), "foot": 148,
         "door": "res://scenes/world/interiors/duskara_office.tscn", "back": "from_houseoffice"},
    ],
    "props": (
        # The north row, shoulder to shoulder either side of the inn (the lane to the
        # stairs between them west of the inn).
        [row_home(s, x, NORTH_ROW) for s, x in [("tower_a.png", -660), ("house_c.png", -440), ("tower_b.png", -330),
                                                 ("house_b.png", -220), ("tower_a.png", 180), ("house_c.png", 290),
                                                 ("house_b.png", 405), ("tower_b.png", 505), ("house_a.png", 610)]]
        # The south row along the south lane (gaps at the two lanes down from the bazaar).
        + [row_home(s, x, SOUTH_ROW) for s, x in [("tower_b.png", -620), ("house_c.png", -510), ("house_a.png", -395),
                                                   ("house_b.png", -120), ("tower_a.png", 160)]]
        # The bazaar: spice stalls and a plain stall facing the cistern, amphorae, pots.
        + [{"sprite": DK + "stall_spice.png", "pos": p, "foot": (50, 14)} for p in [(BAZAAR[0] - 150, BAZAAR[1] - 30), (BAZAAR[0] + 150, BAZAAR[1] + 64)]]
        + [{"sprite": DK + "stall_plain.png", "pos": (BAZAAR[0] - 150, BAZAAR[1] + 70), "foot": (50, 14)}]
        + [{"sprite": SRP + "amphora.png", "pos": p, "foot": (12, 6)} for p in [(BAZAAR[0] - 70, BAZAAR[1] - 50), (BAZAAR[0] + 70, BAZAAR[1] - 50)]]
        + [{"sprite": SRP + "pots_cluster.png", "pos": (BAZAAR[0] + 215, BAZAAR[1] - 50), "foot": (26, 10)},
           {"sprite": SRP + "pots_small.png", "pos": (BAZAAR[0] - 215, BAZAAR[1] + 40), "foot": (22, 8)},
           {"sprite": K2 + "props/notice_board.png", "pos": (BAZAAR[0] + 240, BAZAAR[1] - 20), "foot": (30, 8)}]
        # Pots and palms at the doors.
        + [{"sprite": K2 + "props/potted_palm.png", "pos": p, "foot": (14, 6)} for p in [(BAZAAR[0] - 84, NORTH_ROW + 14), (BAZAAR[0] + 84, NORTH_ROW + 14)]]
        + [{"sprite": SRP + "pots_big.png", "pos": p, "foot": (30, 12)} for p in [(-470, NORTH_ROW + 18), (640, SOUTH_ROW + 30)]]
        # The Card Souk: five stalls in a row, the arch at its south side, pots and
        # amphorae round the edge.
        + [{"sprite": SKP + f"stall_{k}.png", "pos": (x, SOUK_ROW), "foot": (60, 16)}
           for k, x in zip(["spells", "brews", "charms", "ways", "broker"], SOUK_STALLS)]
        + [{"sprite": SKP + "arch.png", "pos": (SOUK[0], SOUK[1] + 110), "scale": 0.8, "feet": [(-38, -5, 22, 12), (38, -5, 22, 12)]}]
        + [{"sprite": SRP + "amphora.png", "pos": p, "foot": (12, 6)} for p in [(SOUK[0] - 190, SOUK[1] + 30), (SOUK[0] + 190, SOUK[1] + 30)]]
        + [{"sprite": SRP + "pots_small.png", "pos": (SOUK[0] - 150, SOUK[1] + 60), "foot": (22, 8)},
           {"sprite": SRP + "pots_cluster.png", "pos": (SOUK[0] + 150, SOUK[1] + 62), "foot": (26, 10)}]
        # The glassworks' yard: a spilled pot, the cart.
        + [{"sprite": SRP + "pot_spilled.png", "pos": (122, SOUTH_ROW + 34), "foot": (26, 10)},
           {"sprite": KP + "cart.png", "pos": (-30, SOUTH_ROW + 44), "foot": (28, 12)}]
        # The Company terrace: the mine shaft under the rim, ore carts, crates, a tally post.
        + [{"sprite": DK + "mine_shaft.png", "pos": (250, -510), "foot": (96, 30)}]
        + [{"sprite": KP + "cart.png", "pos": p, "foot": (28, 12), "scale": 1.2} for p in [(110, -470), (400, -470)]]
        + [{"sprite": KP + "crates.png", "pos": p, "foot": (26, 8), "scale": 1.1} for p in [(-150, -500), (470, -400)]]
        + [{"sprite": SRP + "rock_stack.png", "pos": (-110, -390), "foot": (14, 8)},
           {"sprite": SRP + "rock_stack.png", "pos": (-560, -420), "foot": (22, 10)}]
    ),
    "merchant": ((BAZAAR[0] + 150, BAZAAR[1] - 50), DK + "stall_plain.png"),
    "lanterns": [(BAZAAR[0] - 240, BAZAAR[1] - 60), (BAZAAR[0] + 240, BAZAAR[1] + 70), (-400, 150), (-250, 300), (330, 300),
                 (-100, TERRACE_Y + 30), (0, TERRACE_Y + 30), (-170, -420), (380, -420), (640, 180), (-460, SOUTH_ROW + 30), (250, SOUTH_ROW + 30)],
    "string_lights": [((BAZAAR[0] - 190, BAZAAR[1] - 80), (BAZAAR[0] + 190, BAZAAR[1] - 80), 14),
                      ((SOUK_STALLS[0] - 30, SOUK_ROW + 6), (SOUK_STALLS[-1] + 30, SOUK_ROW + 6), 16),
                      ((-640, SOUTH_ROW + 50), (-260, SOUTH_ROW + 50), 10)],
    "npcs": [
        {"id": "rafi", "name": "Rafi", "pos": (BAZAAR[0] - 90, BAZAAR[1] + 40), "wander": 40, "out": (6.0, 21.0),
         "shop": ["bread", "healers_tonic"], "shop_title": "Rafi's Water & Bread", "lines": [
            "Water! Sweet water from the Sunwell, not the Company tank! A copper a cup, and you don't have to sign anything for it.",
            "The Company sells water too. Cheaper. You pay in scrip, and the scrip comes out of your wages, and the wages come out of the mine. I sell it for copper.",
            "Duskara has two kinds of people: those who go down the shaft, and those who count them coming up. I sell water to both. I'd rather sell to the first.",
            "Zahra says the bell still rings? ...Good. That's good. Thank you, friend. Don't say it again where the foreman can hear.",
            "The cistern under the square is older than the Company, older than the King. The Company built a tank and a meter. The cistern doesn't charge.",
        ]},
        {"id": "nib", "name": "Nib", "pos": (BAZAAR[0] + 40, BAZAAR[1] + 60), "wander": 80, "out": (6.0, 20.0), "lines": [
            "Message for the office? I run 'em. Fastest legs in Duskara. Fastest legs above ground, anyway.",
            "I used to work down the shaft. Then my legs got too long for the low seams, so they made me a runner. Lucky.",
            "Don't look at my wrist. It's just a mark. Everybody's got one. Well. Everybody who came from down there.",
            "The foreman's fair. That's what everybody says. She's fair. She counts us every night, fair and square.",
            "If you see a light under the dunes at night, it isn't ghosts. Don't tell anyone I said that.",
        ]},
        {"id": "xena", "name": "Xena", "pos": (80, -420), "wander": 30, "lines": [
            "You're on Company ground. Say what you want or go back down the stairs.",
            "I'm the foreman. I keep the shaft working and the count true. Every name in, every name out. That's the job.",
            "People think a mine is cruelty. A mine is bread. Without the shaft, this town is sand. I keep them working because working keeps them fed.",
            "Racers. You'll spend more cards in a week than my diggers bring up in a season, and you'll never once ask where they came from.",
            "My husband likes to travel. My son likes to hide. Somebody in this family has to stay and keep the books.",
            "The lower gate is closed to visitors. That isn't a request.",
        ]},
        # The Card Souk's five dealers, each in front of their own stall.
        {"id": "vash", "name": "Vash", "pos": (SOUK_STALLS[0], SOUK_ROW + 24), "wander": 0, "out": (7.0, 23.0),
         "shop": ["pickpockets_whisper", "lockbox_seal", "mirage_veil", "dust_devil"], "shop_title": "Vash's Spellcards", "lines": [
            "Spells! Spells for the bold and the sticky-fingered! Step up, step up, and keep one hand on your purse. Not because of me. Probably.",
            "A Mirage Veil, my friend, and the rivals on your heels will see nothing but heat on the sand. Twenty seconds of being nobody. Priceless. Sixty gold.",
            "Dust Devils come in from the dunes in the afternoon. I catch them in the cards. Cast one in a crowd and watch everybody close by rub their eyes.",
            "The Company buys my Lockbox Seals by the crate. What a mining company needs with that many locks, I couldn't tell you. I could. I won't.",
        ]},
        {"id": "hana", "name": "Hana", "pos": (SOUK_STALLS[1], SOUK_ROW + 24), "wander": 0, "out": (7.0, 22.0),
         "shop": ["second_wind", "scarab_fury", "glass_skin", "swiftsand_draught", "healers_tonic"], "shop_title": "Hana's Brews", "lines": [
            "Brews! Fresh this morning! Well, this week. Brews don't go off, they just get more interesting.",
            "Scarab Fury puts fire in your sword arm for half a minute. Glass Skin makes you hard as a bottle for a few breaths. Swiftsand makes you fast. Don't mix them. Or do, and tell me what happens.",
            "My best customer is a courier who drinks a Swiftsand every morning to beat the carts to Duskara. He's very fast. He's also never once sat down.",
            "Oren lends me his sand for the Glass Skin. Rafi lends me his water. I lend everyone my opinions. It's a good market.",
        ]},
        {"id": "ammar", "name": "Ammar", "pos": (SOUK_STALLS[2], SOUK_ROW + 24), "wander": 0, "out": (8.0, 21.0),
         "shop": ["hollowpoint_charm", "tidewalker_anklet", "scarab_ward", "prospectors_charm"], "shop_title": "Ammar's Charms", "lines": [
            "Sit, child, sit. A charm isn't bought, it's chosen. Well. It's chosen, then it's bought. I'm old, not foolish.",
            "The Scarab Ward. The scarab rolls the sun across the sky every morning. It can roll a claw aside, if it likes you. One in four times, it likes you.",
            "My grandfather was a prospector, before the Company. He wore a little brass pick on a coin and found gold in the dry wadis. Then the Company bought the wadis. Now I make the charms and he's in the ground.",
            "Wear two charms at most. More than that and they argue among themselves, and you'll lose the argument.",
        ]},
        {"id": "tamsa", "name": "Tamsa", "pos": (SOUK_STALLS[3], SOUK_ROW + 24), "wander": 0, "out": (7.0, 22.0),
         "shop": ["kalmora_return", "sorenda_return", "verdana_return", "seabright_return", "frisalle_return", "duskara_return", "vetrassa_return", "halmeer_return"],
         "shop_title": "Tamsa's Way-Cards", "lines": [
            "Way-cards for every town on Virelia! Every one I've been to, anyway, and I've been to all of them that'll have me.",
            "Kalmora, Sorenda, Verdana, Seabright, Frisalle, here. A return to any of them, at the same price the towns charge. Saves you the walk back.",
            "There's Halmeer on the south cape and Vetrassa in the north-west, of course, but nobody sells a way to Vetrassa. You have to earn that road.",
            "I've walked every road on this island twice. The roads to Duskara are the only ones with more carts coming back than going.",
        ]},
        {"id": "isra", "name": "Isra", "pos": (SOUK_STALLS[4], SOUK_ROW + 24), "wander": 0, "out": (9.0, 23.5),
         "shop": ["lockbox_seal"], "daily_cards": 4, "buys_cards": True, "shop_title": "Isra's Rarities", "lines": [
            "Rarities. Set cards, the real thing, the kind racers bleed for. Four a day, never the same four. I don't haggle and I don't explain.",
            "Where do they come from? Out of the ground, darling. Where else does anything come from?",
            "The Company counts every card that comes up the North Shaft. Nearly every card. The ones it doesn't count come to me, and then to you.",
            "I'll buy too. I pay fair. Fairer than the merchants in the towns. They only resell to the Company anyway; I cut out the middle.",
            "A racer's family from Vetrassa buys from me by the crate. Old money, older debts. Discreet people. I like discreet people.",
        ]},
        *[{"id": "company_man", "node": f"Npc_company_man{k}", "name": "Company Man", "pos": p, "wander": 0, "lines": [line]}
          for k, (p, line) in enumerate([((-104, TERRACE_Y + 24), "Terrace is Company ground. Mind your business up there."),
                                         ((-8, TERRACE_Y + 24), "Foreman's busy. She's always busy.")])],
    ],
    "readables": [
        ("The souk's arch", (SOUK[0] + 56, SOUK[1] + 122), [
            "A sandstone arch hung with bunting made of real cards, faded and cracked: commons nobody wanted, strung up for luck. A painted sign: 'THE CARD SOUK. ALL CARDS. ALL PRICES. NO QUESTIONS.'",
            "Someone has scratched underneath it, small: 'ask where they come from'.",
        ]),
        ("The cistern plaque", (BAZAAR[0], BAZAAR[1] + 40), [
            "A bronze plaque on the cistern's rim, green with age: 'THE DEEP WELL OF DUSKARA. Free to all who thirst. By order of the first king.'",
            "Below it, a newer brass plate bolted over the old words: 'Water rights: Duskara Mining Company. Metered supply at the Company tank.'",
        ]),
        ("The Company notice board", (BAZAAR[0] + 240, BAZAAR[1] + 6), [
            "'D.M.C. HIRING. Small hands preferred for close work. Room, board and a trade. Apply to the foreman, upper terrace.' The same notice as the one in Verdana.",
            "Under it, a list headed 'DEBTS DISCHARGED THIS MONTH': two names. A longer list beside it, headed 'DEBTS OUTSTANDING', runs off the bottom of the board.",
        ]),
        ("The mine shaft gate", (250, -480), [
            "A shaft cut into the rim, timbered, with a pulley wheel over it and an iron gate chained across. A sign: 'NORTH SHAFT. COMPANY BUSINESS ONLY. HEADS COUNTED AT THE GATE.'",
            "Through the bars the air comes up cool and smells of wet stone. Far down, very faintly, someone is singing.",
        ]),
        ("A tally post", (-110, -370), [
            "A post at the top of the stairs, scored with notches in long rows. Each row is a day. Each notch is somebody going down. A second, shorter row beside it: coming up.",
        ]),
        ("A chalk drawing", (-270, NORTH_ROW + 20), [
            "Drawn low on a wall in white chalk, at a child's height: a sun, a dune, and a long line of little stick figures walking into a hole in the ground. One of them is walking the other way.",
        ]),
    ],
    "chests": [
        {"id": "duskara_rooftop", "pos": (-640, 200), "gold": 40, "item": "healers_tonic"},
    ],
    "butterflies": [],
}

# ---------------------------------------------------------------- Vetrassa
# The royal port on the north-west coast, where the race ends: down the mountain road
# from Frisalle into a cool grey stone town over a sheltered bay. Three heights: the
# quay along the water (the Crown & Anchor inn, the customs house, three piers), the
# Crown Square above it (the fountain, slate-roofed townhouses shoulder to shoulder
# along its north side, Chef's restaurant the whole island talks about, the Duke's
# townhouse with his crest), and up the grand stairs past the King's Guard, the palace
# terrace: the royal palace, where the Steward of the Set waits by the empty throne for
# whoever brings him the whole set. Kalmora's mirror image across the island.
VT = "assets/sprites/tiles/vetrassa/"
VTP = VT + "props/"
CROWN = (0, 60)            # the Crown Square
NROW = -110                # the north row's doorsteps
QROW = 400                 # the quay buildings' doorsteps


def vetrassa_coast(x):
    return 520 + 26 * math.sin(x / 180.0) + 12 * math.sin(x / 61.0)


def vetrassa_level(x, y):
    """0 the bay, 1 the quay, 2 the Crown Square and its streets, 3 the palace terrace."""
    if y > vetrassa_coast(x):
        return 0
    if y > 250 + 10 * math.sin(x / 230.0):
        return 1
    if y > -250 + 10 * math.sin(x / 210.0):
        return 2
    return 3


def v_home(sprite, x, y=NROW):
    w = Image_w(VT + sprite)
    return {"sprite": VT + sprite, "pos": (x, y), "foot": (w - 8, 48), "glow": True}


def Image_w(path):
    from PIL import Image as _I
    return _I.open(path).width


VETRASSA = {
    "scene": "scenes/world/vetrassa.tscn",
    "root": "Vetrassa",
    "display": "Vetrassa, the Crown of the North",
    "art": VT,
    "bounds": (-960, -832, 960, 800),
    "level": vetrassa_level,
    "cliffs": {(0, 1): K2C + "sea_quay", (1, 2): K2C + "quay_town", (2, 3): K2C + "quay_town", (0, 2): K2C + "sea_rock"},
    "flats": {0: ((0, 1), "lower"), 1: ((0, 1), "upper"), 2: ((1, 2), "upper"), 3: ((2, 3), "upper")},
    "tall_walls": {(2, 3): 1},
    "sea_level": 0,
    "sea_depth": True,
    "sea_tint": (0.82, 0.92, 1.0, 1),
    "turquoise": (70, 150, 170),
    "stairs": [(-380, 250, 1, 2), (380, 250, 1, 2), (0, -250, 2, 3)],
    "grade": (0.82, (0.94, 0.97, 1.04)),
    "palette": ((70, 112, 76), (104, 130, 86)),
    "dapple": 0.08,
    "dress_levels": [3],
    "tree_levels": [3],
    "plaza_stone": (184, 188, 196),
    "paved_levels": [1, 2],
    "pave_stone": (150, 156, 166),
    "paths": [
        ([(980, 0), (700, 10), (CROWN[0] + 260, CROWN[1])], 28),                                  # the mountain road in from Frisalle
        ([(CROWN[0] - 260, CROWN[1]), (-700, 40), (-880, 60)], 22),                               # west along the square
        ([(-380, 120), (-380, 330)], 20), ([(380, 120), (380, 330)], 20),                         # down to the stairs to the quay
        ([(-900, 330), (900, 330)], 24),                                                          # the quay promenade
        ([(0, CROWN[1] - 60), (0, -200)], 30),                                                    # up to the grand stairs
        ([(0, -320), (0, -410)], 34),                                                             # the palace approach
    ],
    "plazas": [(CROWN[0], CROWN[1], 290, 120), (0, -350, 210, 70), (-600, 40, 110, 50)],
    "docks": [(-660, 470, -610, 760), (-25, 470, 25, 760), (610, 470, 660, 760), (-740, 700, -530, 740)],
    "dock_rails": True,
    "afloat": [(K2 + "props/rowboat.png", (-580, 600), False), (K2 + "props/rowboat.png", (-690, 560), True),
               (K2 + "props/rowboat.png", (580, 620), True), (K2 + "props/rowboat.png", (60, 680), False)],
    "fishing": [(-660, 740)],
    "tree_kinds": ["oak", "fir"],
    "treeline_kinds": ["fir", "oak"],
    "groves": [(-600, -520, 4, 60), (600, -520, 4, 60), (-820, -380, 3, 40), (820, -380, 3, 40), (-300, -700, 3, 40), (300, -700, 3, 40)],
    "under": [("flowers", 3), ("grass_clump", 3), ("berry_bush", 1)],
    "patches": 16,
    "tufts": 30,
    "tuft_tint": (0.9, 1.0, 1.02, 1),
    "safe_zone": (-960, -832, 960, 800),
    "entry": (900, 0),
    "exits": [
        {"name": "ToFrisalle", "pos": (956, 0), "side": "e", "target": "res://scenes/world/frisalle.tscn", "spawn": "from_vetrassa"},
    ],
    "spawns": {"from_frisalle": (900, 0), "town": (CROWN[0] + 120, CROWN[1] + 40)},
    "rival_spots": {"runner": (820, -30), "raider": (820, 40), "hoarder": (760, 0)},
    "buildings": [
        {"node": "HousePalace", "sprite": VT + "palace.png", "pos": (0, -410), "foot": 136,
         "door": "res://scenes/world/interiors/vetrassa_palace.tscn", "back": "from_housepalace"},
        {"node": "HouseRestaurant", "sprite": VT + "restaurant.png", "pos": (-520, NROW), "foot": 122,
         "door": "res://scenes/world/interiors/vetrassa_restaurant.tscn", "back": "from_houserestaurant"},
        {"node": "HouseInn", "sprite": VT + "inn.png", "pos": (-560, QROW), "foot": 130,
         "door": "res://scenes/world/interiors/vetrassa_inn.tscn", "back": "from_houseinn"},
    ],
    "props": (
        # The north row of the Crown Square, shoulder to shoulder (the grand stairs'
        # street between them), the Duke's crested townhouse among them.
        [v_home(s, x) for s, x in [("townhouse_c.png", -790), ("townhouse_a.png", -690), ("townhouse_d.png", -360),
                                   ("townhouse_b.png", -255), ("townhouse_a.png", 410), ("townhouse_c.png", 505),
                                   ("townhouse_d.png", 600), ("townhouse_b.png", 700), ("townhouse_c.png", 790)]]
        + [{"sprite": VT + "duke_house.png", "pos": (270, NROW), "foot": (112, 50), "glow": True}]
        # The quay: the customs house, crates and barrels by the piers, a crane.
        + [{"sprite": VT + "customs_house.png", "pos": (560, QROW), "foot": (140, 50), "glow": True}]
        + [v_home("townhouse_a.png", -320, QROW), v_home("townhouse_d.png", 300, QROW)]
        + [{"sprite": KP + "crates.png", "pos": p, "foot": (26, 8), "scale": 1.1} for p in [(-700, 450), (120, 452), (700, 452)]]
        + [{"sprite": KP + "barrels.png", "pos": p, "foot": (26, 8), "scale": 1.1} for p in [(-470, 450), (440, 452)]]
        # The square: benches, flower beds, the notice board.
        + [{"sprite": K2 + "props/bench.png", "pos": p, "foot": (36, 8)} for p in [(-160, CROWN[1] + 80), (160, CROWN[1] + 80)]]
        + [{"sprite": K2 + "props/flower_bed.png", "pos": p, "foot": (30, 8)} for p in [(-230, CROWN[1] - 20), (230, CROWN[1] - 20)]]
        + [{"sprite": K2 + "props/notice_board.png", "pos": (-200, CROWN[1] + 110), "foot": (30, 8)}]
        # The south row along the top of the quay wall, backs to the drop, gaps left
        # for the two stairs down and the view over the bay from the fountain.
        + [v_home(s, x, 226) for s, x in [("townhouse_b.png", -840), ("townhouse_c.png", -745), ("townhouse_a.png", -650),
                                          ("townhouse_d.png", -540), ("townhouse_c.png", -250), ("townhouse_b.png", 250),
                                          ("townhouse_a.png", 530), ("townhouse_d.png", 640), ("townhouse_c.png", 745), ("townhouse_b.png", 840)]]
        # The first king in stone, on his own little square on the west street.
        + [{"sprite": VTP + "statue_king.png", "pos": (-600, 30), "foot": (36, 14)}]
        + [{"sprite": VTP + "cypress_planter.png", "pos": p, "foot": (24, 12)} for p in
           [(-680, 40), (-520, 40), (-170, -60), (170, -60), (-420, -50), (420, -50)]]
        + [{"sprite": VTP + "topiary_planter.png", "pos": p, "foot": (24, 12)} for p in [(-300, -60), (300, -60), (-60, -200), (60, -200)]]
        # Chef's terrace: tables out front of the restaurant.
        + [{"sprite": VTP + ("cafe_table.png" if i % 2 else "cafe_table_b.png"), "pos": p, "foot": (34, 10)}
           for i, p in enumerate([(-600, -55), (-520, -40), (-440, -55)])]
        # The market where the mountain road comes in: three stalls along its north side.
        + [{"sprite": VTP + s, "pos": p, "foot": (54, 14)} for s, p in [("stall_a.png", (470, -40)), ("stall_b.png", (560, -32)), ("stall_c.png", (650, -40))]]
        + [{"sprite": VTP + "flower_cart.png", "pos": (240, -40), "foot": (36, 10)}]
        # Fish off the boats, sold on the quay.
        + [{"sprite": VTP + s, "pos": p, "foot": (54, 14)} for s, p in [("stall_c.png", (-100, 410)), ("stall_a.png", (40, 410))]]
        # The palace terrace: royal banners either side of the approach, planters.
        + [{"sprite": VTP + "royal_banner.png", "pos": p, "foot": (10, 6)} for p in [(-150, -300), (150, -300), (-90, -440), (90, -440)]]
        + [{"sprite": K2 + "props/potted_palm.png", "pos": p, "foot": (14, 6)} for p in [(-110, -380), (110, -380)]]
    ),
    "instances": [("res://scenes/world/props/kalmora_fountain.tscn", (CROWN[0], CROWN[1] + 10), 1.0)],
    "merchant": ((740, -36), "assets/sprites/tiles/kalmora/market_stall.png"),
    "lanterns": [(-290, CROWN[1] + 110), (290, CROWN[1] + 110), (-110, -160), (110, -160), (-160, -420), (160, -420),
                 (-760, 340), (-200, 340), (200, 340), (760, 340), (-860, 40), (860, 60)],
    "string_lights": [((-260, CROWN[1] - 60), (260, CROWN[1] - 60), 16)],
    "npcs": [
        {"id": "freya", "name": "Freya", "pos": (60, -330), "wander": 30, "lines": [
            "You've come a long way, racer. Everyone does, in the end. Vetrassa's where the roads stop.",
            "Captain of the King's Guard. Which mostly means guarding an empty chair. My father hasn't sat in it in months. He travels.",
            "My brother cooks. My other brother hides. My mother counts. I stand on these steps with a sword and wait for someone to bring the whole set up them.",
            "The Steward will see you in the throne room if you hold all of it. Not before. He's very particular about 'all'.",
            "There's a ledger in the throne room nobody's allowed to read but the King. I've read it. Don't ask me what's in it. Not yet.",
        ]},
        {"id": "kings_guard", "node": "Npc_guard0", "name": "King's Guard", "pos": (-64, -160), "wander": 0,
         "lines": ["The palace terrace is open to racers. Mind the steps; they've been worn by a lot of hopeful feet."]},
        {"id": "kings_guard", "node": "Npc_guard1", "name": "King's Guard", "pos": (64, -160), "wander": 0,
         "lines": ["Only one of you ever goes up those steps with a full binder. The rest come back down."]},
        {"id": "kings_guard", "node": "Npc_guard2", "name": "King's Guard", "pos": (-70, -390), "wander": 0,
         "lines": ["The throne room. The Steward's inside."]},
    ],
    "readables": [
        ("The Crown Square fountain", (CROWN[0] + 50, CROWN[1] + 40), [
            "The same fountain as Kalmora's, stone for stone: the two ports were built by the same first king, at the two ends of his island.",
            "Round the rim, in old letters: 'WHAT IS GATHERED AT ONE END IS CROWNED AT THE OTHER.'",
        ]),
        ("The race board", (-200, CROWN[1] + 140), [
            "A board by the fountain, freshly painted: 'THE RACE. Present the complete set to the Steward of the Set in the throne room. The first to do so is owed what was promised.'",
            "What was promised isn't written anywhere. Underneath, someone has chalked: 'riches beyond your wildest dreams'. Someone else has chalked: 'ask what they cost'.",
        ]),
        ("A crest over a door", (330, NROW + 20), [
            "A coat of arms carved over the door of the grandest townhouse on the square: a dachshund's head over a crossed pick. The Duke's. The same mark as the seal on the Frisalle letters.",
        ]),
        ("The customs house ledger", (500, QROW + 20), [
            "A ledger chained to a lectern by the cargo doors. 'Arrivals: cards, uncut, from D.M.C. (north road, by the shoulder). Duty: waived, by order.' By whose order isn't written.",
        ]),
    ],
    "chests": [
        {"id": "vetrassa_pier", "pos": (-720, 720), "gold": 60, "item": "healers_tonic"},
    ],
    "butterflies": [],
}

# ---------------------------------------------------------------- Halmeer
# The last port on the south coast, west of Seabright along the cliff road: a small
# weathered fishing village clinging to the cliff over a rough sea. Three heights: a
# cobbled quay inside a tight harbour cove (the smokehouse, the Company's 'salt house',
# two plank piers), the village street above it (cottages shoulder to shoulder, the
# Gull's Rest inn, the card stall), and the windswept heath on top where the
# smugglers' cut runs down through the cliff to a sea cave. On the cape to the west,
# Nessa's lighthouse, paid to keep dark on certain nights.
HM = "assets/sprites/tiles/halmeer/"


def halmeer_coast(x):
    """Where the land meets the sea: a tight cove in the middle, the cape running out
    south to the west."""
    if -330 <= x <= 330:
        return 240
    base = 330 + 18 * math.sin(x / 140.0)
    if x < -480:
        base += min(250, (-480 - x) * 0.9)
    return base


def halmeer_level(x, y):
    """0 the sea, 1 the harbour quay, 2 the village street and the cape, 3 the heath."""
    if y > halmeer_coast(x):
        return 0
    if -330 <= x <= 330 and y > 40:
        return 1
    if y > -180 + 8 * math.sin(x / 120.0):
        return 2
    return 3


def h_home(sprite, x, y):
    w = Image_w(HM + sprite)
    return {"sprite": HM + sprite, "pos": (x, y), "foot": (w - 8, 40), "glow": True}


HALMEER = {
    "scene": "scenes/world/halmeer.tscn",
    "root": "Halmeer",
    "display": "Halmeer, the End of the Coast",
    "art": HM,
    "bounds": (-960, -640, 960, 640),
    "level": halmeer_level,
    "cliffs": {(0, 1): K2C + "sea_quay", (1, 2): K2C + "quay_town", (2, 3): K2C + "quay_town", (0, 2): K2C + "sea_rock"},
    "flats": {0: ((0, 1), "lower"), 1: ((0, 1), "upper"), 2: ((1, 2), "upper"), 3: ((2, 3), "upper")},
    "sea_level": 0,
    "sea_depth": True,
    "sea_tint": (0.78, 0.88, 0.95, 1),
    "turquoise": (60, 130, 140),
    "stairs": [(-200, 40, 1, 2), (200, 40, 1, 2), (-420, -180, 2, 3), (380, -180, 2, 3)],
    "grade": (0.8, (0.96, 0.98, 1.02)),
    "palette": ((78, 110, 66), (124, 142, 86)),
    "dapple": 0.1,
    "dress_levels": [2, 3],
    "tree_levels": [3],
    "plaza_stone": (170, 166, 158),
    "paved_levels": [1],
    "pave_stone": (150, 148, 142),
    "paths": [
        ([(980, -100), (700, -90), (460, -40), (330, -20)], 26),                                  # the cliff road in from Seabright
        ([(330, -20), (-620, -20)], 24),                                                          # the village street
        ([(-620, -20), (-700, 120), (-740, 330)], 18),                                            # out to the lighthouse on the cape
        ([(-200, -20), (-200, 30)], 18), ([(200, -20), (200, 30)], 18),                           # down to the quay stairs
        ([(-420, -40), (-420, -170)], 16), ([(380, -40), (380, -170)], 16),                       # up to the heath
        ([(-420, -200), (-640, -230)], 14),                                                       # along the heath to the cut
    ],
    "docks": [(-70, 240, -30, 490), (70, 240, 110, 450), (-130, 460, -30, 490)],
    "dock_rails": True,
    "afloat": [(K2 + "props/rowboat.png", (10, 360), False), (K2 + "props/rowboat.png", (150, 320), True),
               (K2 + "props/rowboat.png", (-170, 410), True)],
    "fishing": [(-110, 476)],
    "tree_kinds": ["fir", "oak"],
    "treeline_kinds": ["fir", "oak"],
    "groves": [(-200, -420, 4, 70), (300, -460, 4, 70), (700, -380, 3, 60), (-720, -420, 3, 60), (720, 200, 3, 50)],
    "under": [("grass_clump", 4), ("flowers", 2), ("berry_bush", 1)],
    "patches": 18,
    "tufts": 40,
    "tuft_tint": (0.92, 0.98, 1.0, 1),
    "gulls": [((0, 300), 5, (220, 90)), ((-700, 560), 3, (120, 60))],
    "safe_zone": (-620, -180, 620, 240),
    "entry": (900, -100),
    "exits": [
        {"name": "ToSeabright", "pos": (956, -100), "side": "e", "target": "res://scenes/world/seabright_quay.tscn", "spawn": "from_halmeer"},
    ],
    "spawns": {"from_seabright": (900, -100), "town": (60, -10)},
    "rival_spots": {"runner": (820, -120), "raider": (820, -60), "hoarder": (760, -90)},
    "buildings": [
        {"node": "HouseInn", "sprite": HM + "inn.png", "pos": (-250, -70), "foot": 120,
         "door": "res://scenes/world/interiors/halmeer_inn.tscn", "back": "from_houseinn"},
        {"node": "HouseLighthouse", "sprite": HM + "lighthouse.png", "pos": (-760, 420), "foot": 86,
         "door": "res://scenes/world/interiors/halmeer_lighthouse.tscn", "back": "from_houselighthouse"},
        {"node": "HouseCave", "sprite": HM + "cave_mouth.png", "pos": (-680, -122), "foot": 90,
         "door": "res://scenes/world/interiors/halmeer_cave.tscn", "back": "from_housecave"},
    ],
    "props": (
        # The village street: cottages shoulder to shoulder on the north side, a few
        # on the south side along the top of the quay wall.
        [h_home(s, x, -70) for s, x in [("cottage_a.png", -560), ("cottage_b.png", -470), ("cottage_c.png", -90),
                                        ("cottage_a.png", 0), ("cottage_b.png", 90), ("cottage_c.png", 450), ("cottage_a.png", 540)]]
        + [h_home(s, x, 30) for s, x in [("cottage_c.png", -520), ("cottage_b.png", -420), ("cottage_a.png", 430), ("cottage_c.png", 520)]]
        # The quay: the smokehouse and the Company's salt house, nets and crates.
        + [{"sprite": HM + "smokehouse.png", "pos": (-210, 205), "foot": (76, 30)}]
        + [{"sprite": HM + "warehouse.png", "pos": (190, 205), "foot": (114, 40), "glow": True}]
        + [{"sprite": KP + "crates.png", "pos": p, "foot": (26, 8), "scale": 1.1} for p in [(285, 222), (95, 222)]]
        + [{"sprite": KP + "barrels.png", "pos": p, "foot": (26, 8), "scale": 1.1} for p in [(-120, 222), (-295, 222)]]
        + [{"sprite": K2 + "props/fish_crates.png", "pos": (-20, 190), "foot": (30, 8)}]
        + [{"sprite": K2 + "props/bench.png", "pos": p, "foot": (36, 8)} for p in [(-330, 10), (330, 10)]]
        # The cape: wind-bent bushes, boulders, a bench where Nessa watches the sea.
        + [{"sprite": K2 + "props/boulder.png", "pos": p, "foot": (30, 12)} for p in [(-860, 260), (-580, 420), (-880, 470), (-540, 300)]]
        + [{"sprite": K2 + "props/bush.png", "pos": p, "foot": (24, 8)} for p in [(-820, 120), (-640, 260), (-900, 360), (-760, 220)]]
        + [{"sprite": K2 + "props/bush_flowers.png", "pos": p, "foot": (24, 8)} for p in [(-690, 330), (-830, 400)]]
        + [{"sprite": K2 + "props/bench.png", "pos": (-660, 400), "foot": (36, 8)}]
    ),
    "merchant": ((250, -30), "assets/sprites/tiles/kalmora/market_stall.png"),
    "lanterns": [(-380, 0), (-140, 0), (150, 0), (380, 0), (-60, 120), (40, 200), (-680, 200), (620, -60)],
    "npcs": [
        {"id": "ferro", "name": "Ferro", "pos": (-60, 160), "wander": 50, "lines": [
            "Rough sea today. It's always rough. Halmeer's the end of the coast; the sea takes it personally.",
            "The Company buys our catch for salt-fish. Never seen them salt a single fish. Never seen them eat one either.",
            "Old Nessa up on the cape keeps the light. Most nights. Ask her about the other nights, if you're brave.",
            "On a still night you can hear oars under the cape. Seals, the Company man says. Seals don't row.",
            "Nobody comes to Halmeer unless they're lost, a racer, or the Company. You're not lost, are you?",
        ]},
        {"id": "grisel", "name": "Grisel", "pos": (255, 226), "wander": 0, "lines": [
            "Duskara Mining Company, Halmeer office. Salt and fish. Mostly salt. Please don't lean on the crates.",
            "I'm not permitted to discuss the salt house's contents. Salt. The contents are salt.",
            "Vetrassa had theatres. Halmeer has gulls. I have been very patient with the gulls.",
        ]},
    ],
    "readables": [
        ("The tide board", (-80, 140), [
            "A slate board on the quay with the month's tides chalked in neat columns. Beside some nights, a little mark: a pick. The same nights, every month: no moon.",
            "Underneath, in a different hand: 'LIGHT DARK. By order. D.M.C.'",
        ]),
        ("The salt house door", (160, 224), [
            "The Company's warehouse: 'D.M.C. SALT AND FISH'. The doors are barred and padlocked, and the padlock is new. There's no smell of fish at all.",
            "Through a gap in the boards, crates stamped like the ones on Kalmora's quay. On one the lid's been prised up: no salt. Cards, uncut, packed in straw.",
        ]),
        ("A memorial on the cliff", (620, 200), [
            "A stone on the cliff edge with the names of Halmeer's drowned, a century of them. The newest line is cut shallow, in a hurry: 'and the ones who rowed out on the dark nights'.",
        ]),
    ],
    "chests": [
        {"id": "halmeer_cape", "pos": (-720, 450), "card": "smugglers_knot", "gold": 20},
        {"id": "halmeer_heath", "pos": (120, -300), "gold": 35, "item": "smoked_fish"},
    ],
    "butterflies": [],
}

ZONES = {"seabright_quay": RESORT, "aurewind_plains": AUREWIND, "verdana": VERDANA, "lake_serin": LAKE_SERIN, "starfall_range": STARFALL, "frisalle": FRISALLE, "siroth_dunes": SIROTH, "duskara": DUSKARA, "vetrassa": VETRASSA, "halmeer": HALMEER}
