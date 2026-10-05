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
    ],
    "spawns": {"from_kalmora": (1160, 40), "from_lake_serin": (150, -840), "from_verdana": (-500, 820), "from_barrow": (-380, -712)},
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
        # The dune road, closed: a rockfall across it and a broken ore cart.
        + [{"sprite": BOULDER, "pos": p, "foot": (40, 18), "scale": 1.4} for p in [(-1180, 104), (-1170, 146), (-1186, 190), (-1140, 124)]]
        + [{"sprite": KP + "cart.png", "pos": (-1080, 206), "foot": (28, 12), "flip": True}]
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
    "lanterns": [(-470, -10), (-150, -10), (150, -10), (470, -10), (-200, -330), (560, -280), (-170, 280), (460, 280), (-250, 40)],
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
    "groves": [(-700, -420, 5, 50), (-420, -360, 4, 45), (300, -400, 4, 45), (720, -300, 4, 40), (420, -60, 2, 30),
               (-740, -140, 3, 30), (-330, -150, 2, 20), (-760, 60, 2, 30), (160, -480, 3, 40), (720, 20, 2, 25)],
    "under": [("flowers", 5), ("grass_clump", 3), ("berry_bush", 1)],
    "patches": 22,
    "tufts": 60,
    "safe_zone": (-800, -576, 800, 640),
    "entry": (-300, -510),
    "exits": [
        {"name": "ToVerdana", "pos": (-300, -572), "side": "n", "target": "res://scenes/world/verdana.tscn", "spawn": "from_resort"},
    ],
    "spawns": {"from_verdana": (-300, -510), "town": (0, -260)},
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
    w = 18 * math.sin(x / 150.0) + 8 * math.sin(x / 53.0 + 1.0)
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
        ([(560, 44), (-640, 44)], 22),                                         # the upper lane
        ([(-300, 44), (-300, -190)], 18),                                        # up the west stairs
        ([(-300, -190), (420, -190)], 20),                                       # along the top
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
    ],
    # The ice road: the smugglers' tunnel out of the Frost Grotto, at the top of the village.
    "portals": [{"name": "ToGrotto", "pos": (620, -580), "target": "res://scenes/world/starfall_grotto.tscn", "spawn": "from_frisalle"}],
    "spawns": {"from_starfall": (0, 580), "town": (-60, 272), "from_grotto": (620, -500)},
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
    "lanterns": [(-420, 292), (-100, 292), (220, 292), (480, 292), (-560, 66), (-180, 66), (180, 66), (460, 66),
                 (-200, -168), (120, -168), (-460, 520), (100, 600)],
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

ZONES = {"seabright_quay": RESORT, "aurewind_plains": AUREWIND, "verdana": VERDANA, "lake_serin": LAKE_SERIN, "starfall_range": STARFALL, "frisalle": FRISALLE}
