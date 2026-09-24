"""Build Kalmora, Port of Beginnings, as a multilevel harbor town.

Usage: python scripts/tools/build_kalmora.py
Writes the ground image, the level map, and scenes/world/kalmora.tscn (the
whole scene is generated: edit the layout here, not in the editor).

Levels (tile-corner heightmap, see terrain.py):
  0 sea         the harbor water (not walkable)
  1 quay        stone docks and a jetty at the waterline
  2 market      the whitewashed market terrace; its fountain square juts out
                over the harbor as a promontory
  3 upper town  gardens and houses; the lighthouse garden reaches down in the
                north-east, and the north road climbs to the Thornveil gate
Cliffs are three rows tall (WALL_EXTRA adds a row of wall body); stairs are cut
through them, 2 cells wide and 3 rows tall.
"""
import os

from PIL import Image

os.chdir(os.path.join(os.path.dirname(__file__), "..", ".."))

from terrain import CliffSet, CornerSet, compose, merge_rects, overlay  # noqa: E402

TILE = 32
LEFT, TOP, RIGHT, BOTTOM = -768, -992, 768, 416
COLS, ROWS = (RIGHT - LEFT) // TILE, (BOTTOM - TOP) // TILE
SEA, QUAY, MARKET, UPPER = 0, 1, 2, 3
WALL_EXTRA = 1
STAIR_ROWS = 2 + WALL_EXTRA

GROUND_PNG = "assets/sprites/tiles/kalmora/kalmora_ground.png"
LEVEL_PNG = "assets/sprites/tiles/kalmora/kalmora_levels.png"
SCENE = "scenes/world/kalmora.tscn"
CLIFF = "assets/sprites/tiles/kalmora/cliff/"


def level_at(x: float, y: float) -> int:
    if 64 <= x <= 160 and 220 < y <= 352:
        return QUAY  # the jetty
    if y > 220:
        return SEA
    market_edge = -76 if -192 <= x <= 192 else -140  # fountain promontory
    if y > market_edge:
        return QUAY
    upper_edge = -420 if x >= 288 else -520          # lighthouse garden
    if y > upper_edge:
        return MARKET
    return UPPER


# Stairs: (left x, plateau edge y, style). They cover the cliff rows around the edge.
STAIRS = [
    (-480, -140, "town"), (320, -140, "town"), (-32, -76, "town"),
    (-224, -520, "town"), (416, -420, "town"), (-32, -520, "town"),
]


def build_terrain():
    levels = [[level_at(LEFT + c * TILE, TOP + r * TILE) for c in range(COLS + 1)] for r in range(ROWS + 1)]
    sets = {SEA: CliffSet(CLIFF + "sea_quay"), QUAY: CliffSet(CLIFF + "quay_market"), MARKET: CliffSet(CLIFF + "market_upper")}
    img, stand = compose(levels, sets, TILE, extra_wall_rows=WALL_EXTRA)
    # Streets through lawns in the upper town; marble paving on the fountain plaza.
    overlay(img, stand, UPPER, CornerSet(GARDEN_SET, LAWN_GRADE), upper_street, LEFT, TOP, TILE, base_is_upper=True)
    overlay(img, stand, MARKET, CornerSet(PLAZA_SET), plaza, LEFT, TOP, TILE)
    img.save(GROUND_PNG)

    stair_cells = set()
    for x, edge, _ in STAIRS:
        c0, r0 = (x - LEFT) // TILE, (edge - TOP) // TILE - WALL_EXTRA
        for dr in range(STAIR_ROWS):
            for dc in (0, 1):
                stair_cells.add((r0 + dr, c0 + dc))
    blocked = [[(stand[r][c] in (-1, SEA)) and (r, c) not in stair_cells for c in range(COLS)] for r in range(ROWS)]

    # Level map: red = level * 40; 255 = cliff/stairs (counts as any level).
    lm = Image.new("RGB", (COLS, ROWS))
    for r in range(ROWS):
        for c in range(COLS):
            v = stand[r][c]
            lm.putpixel((c, r), (255, 0, 0) if v < 0 or (r, c) in stair_cells else (v * 40, 0, 0))
    lm.save(LEVEL_PNG)
    return stand, blocked, stair_cells


# ------------------------------------------------------------------ content
# The town hangs off one axis: the north gate, a cypress avenue down the upper
# town, stairs to the fountain plaza on the promontory, stairs to the quay, and
# the jetty. Everything else is laid out along streets that branch off it.
BUILDINGS = [  # (node, prop, position = footprint bottom-centre)
    # Quay: the harbor front, backed against the market wall.
    ("Harbormaster", "kalmora_harbormaster", (-640, 100)),
    ("Tavern", "kalmora_tavern", (-340, 100)),
    # Market terrace: the café street west of the plaza, the card shop east.
    ("Townhouse1", "kalmora_townhouse_tall", (-650, -410)),
    ("Bakery", "kalmora_cottage", (-510, -410)),
    ("CardShop", "kalmora_card_shop", (470, -235)),
    # Upper town: a row of houses fronting the cross street...
    ("Cottage1", "kalmora_cottage", (-690, -776)),
    ("Villa", "kalmora_villa", (-500, -776)),
    ("Townhouse2", "kalmora_townhouse", (-330, -776)),
    ("Townhouse3", "kalmora_townhouse_tall", (-170, -776)),
    ("NonnaHouse", "kalmora_townhouse_tall", (140, -776)),
    ("Cottage2", "kalmora_cottage", (290, -776)),
    ("Townhouse4", "kalmora_townhouse", (420, -776)),
    # ...and two cottages framing the gate square.
    ("Cottage3", "kalmora_cottage", (-260, -905)),
    ("Cottage4", "kalmora_cottage", (250, -905)),
]
# Enterable buildings: node -> (door x offset from the building, interior scene).
DOORS = {
    "Tavern": (0, "res://scenes/world/interiors/kalmora_tavern.tscn"),
    "CardShop": (-33, "res://scenes/world/interiors/kalmora_card_shop.tscn"),
    "NonnaHouse": (-17, "res://scenes/world/interiors/kalmora_nonna_house.tscn"),
}
# Residents (dogs and cats). (id, name, sprite id, position, wander radius, lines)
NPCS = [
    ("bram", "Bram", "bram", (170, 70), 0, ["Tide's good today. Good for ships, anyway."]),
    ("mirela", "Harbormaster Mirela", "mirela", (-560, 135), 0, [
        "Manifests, manifests. Everything that lands in Kalmora gets a stamp. Everything.",
        "The race? The whole island's talking. Somebody's walking into Vetrassa with a full set, mark my words.",
    ]),
    ("pip", "Pip", "pip", (-170, 70), 50, [
        "Fresh fish! Well. Fresh-ish.",
        "My cousin went to work out in Duskara last spring. Good pay, they said. He hasn't written.",
    ]),
    ("sailor", "Deckhand Luca", "sailor", (360, 60), 70, [
        "Sailed round the whole isle once. Vetrassa's got the tallest spires you ever saw.",
        "You racers bind your cards in town, right? Thieves love a loose card on the road.",
    ]),
    ("baker", "Baker Rosa", "baker", (-470, -350), 50, [
        "Warm bread! Two coins a loaf, one if you tell me a good rumor.",
        "The Runner came through at dawn, all scarf and no manners. Didn't even stop for bread.",
    ]),
    ("tomas", "Keeper Tomas", "tomas", (520, -540), 0, [
        "Lost my lighthouse wick somewhere by the west houses. Can't light the lamp without it.",
        "That lens up there's worth more than my whole cottage. Door stays locked, wick or no wick.",
    ]),
    ("rook", "Guard Rook", "rook", (70, -880), 0, [
        "North road's sealed. A Salt Compass opens it. Old rule, nobody remembers why.",
        "Thornveil's no place to wander with loose cards. The hounds don't care, but the Raider does.",
    ]),
]
# The unmarked shipment: three crates piled by the jetty, where Bram works.
CLUE_CRATES = [("crate_sand", (205, 150)), ("crate_glove", (240, 118)), ("crate_ledger", (205, 104))]
CARDS = [  # (card, position)
    ("harbor_lantern", (-600, 125)), ("coral_coin", (360, 120)), ("gull_feather", (600, 125)),
    ("sea_glass", (-170, 125)), ("sunken_crown_shard", (112, 300)),
    ("salt_compass", (-380, -300)), ("tide_bell", (620, -330)), ("terracotta_tile", (-150, -470)),
    ("lighthouse_wick", (-560, -620)), ("fishers_knot", (-60, 110)),
]
EXTRA_SALT_COMPASS = (-720, -300)
DUMMIES = [(530, -10), (610, -10), (690, -10)]
RIVAL_SPOTS = {"runner": (-450, -600), "raider": (380, -700), "hoarder": (-140, -660)}
SPAWNS = {"town": (0, -150), "from_thornveil": (0, -860)}
LIGHTHOUSE = (600, -640)      # yard centre; the tower stands in its north half
MERCHANT = (240, -240)
FOUNTAIN = (0, -235)

# Surfaces painted over the flat ground (terrain.overlay).
GARDEN_SET = "assets/sprites/tiles/kalmora/wang/garden"   # lawn (lower) / limestone street (upper)
PLAZA_SET = "assets/sprites/tiles/kalmora/wang/plaza"     # sandstone (lower) / marble plaza (upper)
LAWN_GRADE = (0.72, (1.06, 0.98, 0.86))                     # sun-warmed, less saturated grass


def upper_street(x, y):
    """Upper-town corners that are paved street; everything else is lawn."""
    return bool(
        -32 <= x <= 32                                  # the avenue from the gate to the stairs
        or -768 <= y <= -704 and x <= 512               # the cross street
        or y <= -864 and -96 <= x <= 96                 # the gate square
        or -224 <= x <= -160 and y >= -768              # down to the west stairs
        or 416 <= x <= 480 and y >= -768                # down to the east stairs
        or x >= 288 and y >= -552                       # the lighthouse forecourt
        or level_at(x, y + 96) != UPPER                 # the promenade along the terrace edge
    )


PLAZA_CENTRE, PLAZA_RADIUS = (0, -300), 172


def plaza(x, y):
    """A round marble plaza around the fountain."""
    return (x - PLAZA_CENTRE[0]) ** 2 + (y - PLAZA_CENTRE[1]) ** 2 <= PLAZA_RADIUS ** 2


# Trees: (scene, position). Cypresses line the avenue; olives shade the verge.
TREES = (
    [("kalmora_cypress", (sx * 72, y)) for sx in (-1, 1) for y in (-800, -845)]
    + [("kalmora_cypress", (sx * 72, -650)) for sx in (-1, 1)]
    + [("kalmora_olive", (x, -650)) for x in (-690, -340, 130, 250, 370)]
    + [("kalmora_olive", (x, y)) for x in (-720, -620) for y in (-940, -880)]  # orchard behind the houses
    + [("kalmora_cypress", (x, -470)) for x in (-736,)]
)


def row(name, x0, x1, y, step):
    return [(name, x, y) for x in range(x0, x1 + 1, step)]


# Props (assets/sprites/tiles/kalmora/props, or EXTRA_TEX): (name, x, y), grouped
# by where a resident would have put them.
PROPS = (
    # --- Quay -----------------------------------------------------------------
    # Boat store beside the harbormaster's office.
    [("rowboat", -738, 30), ("oars", -738, 64), ("net_crate", -738, 98), ("fishing_rods", -708, 64)]
    # Ship's chandlery display between the harbormaster and the tavern stairs.
    + [("anchor", -560, -10), ("ship_wheel", -528, -10), ("cannonballs", -560, 30), ("buoy", -528, 30)]
    # Tavern front: barrels and a menu board either side of the door.
    + [("barrels", -430, 116), ("barrel", -405, 122), ("menu_board", -278, 118), ("barrel", -252, 122)]
    # Fish market under the promontory: two stalls and the day's catch.
    + [("market_stall", -225, -6), ("market_stall", -125, -6)]
    + [("fish_basket", -250, 32), ("ice_crates", -215, 32), ("fish_basket", -140, 32), ("lobster_trap", -105, 32)]
    + [("bucket", -75, 20), ("mop_bucket", -270, 20)]
    # The jetty root: traps and buoys waiting to go out.
    + [("lobster_trap", 40, 148), ("buoy", 10, 148), ("rope", 176, 150)]
    # Cargo yard east of the jetty, stacked in blocks.
    + row("crates", 232, 296, -50, 32) + [("crate", 232, -16), ("barrels", 264, -16), ("crates", 296, -16)]
    + [("sack", 232, 20), ("flour_sack", 264, 20), ("sack", 296, 20), ("cart", 420, -50)]
    + [("crates", 240, 152), ("barrel", 170, 110)]
    # Training yard at the east end, fenced along the back.
    + row("fence", 480, 736, -84, 32) + [("fence", 480, 40), ("fence", 736, 40)]
    + [("oars", 736, -40), ("tackle_box", 480, -40)]
    # --- Market terrace -------------------------------------------------------
    # The fountain plaza: benches facing the fountain, flowers at the corners.
    + [("bench_stone", -110, -190), ("bench_stone", 110, -190), ("bench_stone", -120, -400), ("bench_stone", 120, -400)]
    + [("bougainvillea_box", -176, -436), ("bougainvillea_box", 176, -436),
       ("bougainvillea_box", -176, -140), ("bougainvillea_box", 176, -140)]
    + [("lemon_tree_pot", -62, -440), ("lemon_tree_pot", 62, -440)]
    # Market stalls flanking the plaza, produce stacked beside them.
    + [("market_stall", -280, -420), ("market_stall", -280, -330), ("market_stall", -280, -240)]
    + [("oranges_basket", -322, -420), ("apples_crate", -322, -330), ("bread_basket", -322, -240)]
    + [("market_stall", 240, -420), ("market_stall", 240, -330)]
    + [("lemons_crate", 284, -340), ("amphorae", 284, -300), ("amphora", 284, -268)]
    # Café street: tables under umbrellas in front of the townhouse and bakery.
    + [("umbrella_table", x, y) for x in (-690, -620) for y in (-330, -262)]
    + [("menu_board", -580, -380), ("bread_basket", -466, -396), ("flour_sack", -552, -396)]
    + [("signpost", -392, -210), ("wheelbarrow", -720, -220)]
    # Card shop: palms by the door, a pair of tables, amphorae stacked by the wall.
    + [("potted_palm", 396, -222), ("potted_palm", 546, -222)]
    + [("cafe_table", 640, -272), ("cafe_table", 700, -272), ("amphorae", 730, -200), ("amphora", 704, -210)]
    # --- Upper town -----------------------------------------------------------
    # Flowers either side of every front door on the cross street.
    + [(("geraniums", "lavender_planter")[k % 2], x + DOORS.get(name, (0,))[0] + dx, -762)
       for k, (name, prop, (x, y)) in enumerate(BUILDINGS) if y == -776 for dx in (-30, 30)]
    # Benches along the terrace-edge promenade, looking out over the harbor.
    + [("bench_stone", x, -592) for x in (-690, -560, -390, -300, 100, 220)]
    # The gate square.
    + [("lavender_planter", -80, -960), ("lavender_planter", 80, -960), ("signpost", 48, -852)]
    # Kitchen gardens behind the east houses.
    + [("laundry_line", 520, -870), ("laundry_line", 560, -870), ("laundry_basket", 600, -856),
       ("wheelbarrow", 680, -840), ("lemon_tree_pot", 640, -910)] + row("fence", 544, 736, -800, 32)
    # Lighthouse forecourt.
    + [("candle_shrine", 690, -500), ("bench_wood", 360, -500), ("potted_palm", 470, -495), ("potted_palm", 736, -495)]
)
PROP_DIR = "assets/sprites/tiles/kalmora/props/"
EXTRA_TEX = {"market_stall": "assets/sprites/tiles/kalmora/market_stall.png"}
# Collision footprint (w, h) at the base; anything else gets 16x8.
FOOTPRINTS = {"market_stall": (44, 12), "fence": (32, 6), "bench_stone": (28, 8), "bench_wood": (28, 8),
              "cart": (28, 10), "umbrella_table": (24, 10), "rowboat": (28, 10)}
# Lamp posts: the quay's waterfront, the plaza corners, the café street, the cross street.
LAMPS = ([("lamp_post", x, 128) for x in (-700, -480, -200, 20, 300, 520, 720)]
         + [("lamp_post", x, y) for x in (-150, 150) for y in (-420, -150)]
         + [("lamp_post", -560, -250), ("lamp_post", 600, -205)]
         + [("lamp_post", x, -698) for x in (-600, -420, -250, 90, 360)]
         + [("lamp_post", -80, -900)])
BOLLARD_ROW = (150, range(-736, 736, 96))
# Ground clutter that isn't solid: leaves under trees, puddles by the water.
DECALS = ([("leaves", x + 10, y + 6) for prop, (x, y) in TREES if prop == "kalmora_olive"]
          + [("puddle", x, 140) for x in (-620, -150, 280, 470)]
          + [("cracks", -260, -150), ("cracks", 380, -200), ("moss", -700, -560), ("moss", 640, -455)])
# Birds on the jetty (free sprites, y-sorted, no collision).
BIRDS = [("seagull", 84, 262), ("seagull", 140, 318), ("seagull", 110, 200)]


def cell_of(x, y):
    return int((y - TOP) // TILE), int((x - LEFT) // TILE)


def check_spot(stand, blocked, name, x, y, want=None):
    r, c = cell_of(x, y)
    ok = 0 <= r < ROWS and 0 <= c < COLS and not blocked[r][c] and (want is None or stand[r][c] == want)
    if not ok:
        raise SystemExit(f"{name} at ({x}, {y}) is not on walkable ground (cell level {stand[r][c]})")


def main():
    stand, blocked, stair_cells = build_terrain()
    # Coming back out of a building puts you on its doorstep.
    for name, _, (x, y) in BUILDINGS:
        if name in DOORS:
            SPAWNS[f"from_{name.lower()}"] = (x + DOORS[name][0], y + 26)
    for card, (x, y) in CARDS:
        check_spot(stand, blocked, card, x, y)
    for name, (x, y) in {**SPAWNS, **RIVAL_SPOTS}.items():
        check_spot(stand, blocked, name, x, y)

    subs = {}
    def shape(w, h):
        key = f"R{w}x{h}"
        subs[key] = f'[sub_resource type="RectangleShape2D" id="{key}"]\nsize = Vector2({w}, {h})\n'
        return key

    ext = [
        ('Script', "res://scripts/world/zone.gd", "1_zone"),
        ('PackedScene', "res://scenes/characters/player.tscn", "2_player"),
        ('PackedScene', "res://scenes/ui/hud.tscn", "3_hud"),
        ('PackedScene', "res://scenes/ui/binder.tscn", "4_binder"),
        ('PackedScene', "res://scenes/ui/shop_panel.tscn", "5_shop"),
        ('PackedScene', "res://scenes/systems/card_pickup.tscn", "6_pick"),
        ('PackedScene', "res://scenes/characters/training_dummy.tscn", "7_dummy"),
        ('PackedScene', "res://scenes/systems/merchant.tscn", "8_merchant"),
        ('Script', "res://scripts/systems/safe_zone.gd", "9_safe"),
        ('PackedScene', "res://scenes/systems/card_gate.tscn", "10_gate"),
        ('PackedScene', "res://scenes/systems/zone_exit.tscn", "11_exit"),
        ('Texture2D', "res://" + GROUND_PNG, "12_ground"),
        ('Texture2D', "res://" + LEVEL_PNG, "13_levels"),
        ('Texture2D', "res://assets/sprites/tiles/kalmora/stairs_town.png", "14_stairs_town"),
        ('Texture2D', "res://assets/sprites/tiles/kalmora/stairs_stone.png", "15_stairs_stone"),
        ('Texture2D', "res://assets/sprites/tiles/kalmora/market_stall.png", "16_stall"),
        ('PackedScene', "res://scenes/world/props/lighthouse.tscn", "17_lighthouse"),
        ('PackedScene', "res://scenes/world/props/kalmora_fountain.tscn", "18_fountain"),
        ('PackedScene', "res://scenes/characters/npc.tscn", "19_npc"),
        ('Script', "res://scripts/systems/lamp_light.gd", "20_lamp"),
        ('PackedScene', "res://scenes/systems/clue_crate.tscn", "21_clue"),
        ('PackedScene', "res://scenes/ui/dialogue_box.tscn", "22_dialogue"),
    ]
    prop_ids = {}
    for _, prop, _ in BUILDINGS:
        prop_ids.setdefault(prop, f"{30 + len(prop_ids)}_{prop}")
    for prop, _ in TREES:
        prop_ids.setdefault(prop, f"{30 + len(prop_ids)}_{prop}")
    for prop, rid in prop_ids.items():
        ext.append(('PackedScene', f"res://scenes/world/props/{prop}.tscn", rid))

    n = []
    cx, cy = (LEFT + RIGHT) / 2, (TOP + BOTTOM) / 2
    n.append(f'''[node name="Kalmora" type="Node2D"]
y_sort_enabled = true
script = ExtResource("1_zone")
display_name = "Kalmora, Port of Beginnings"
level_map = ExtResource("13_levels")
level_cell = {TILE}
level_origin = Vector2({LEFT}, {TOP})

[node name="GroundTiles" type="Sprite2D" parent="."]
z_index = -10
position = Vector2({cx}, {cy})
texture = ExtResource("12_ground")
''')
    for k, (x, edge, style) in enumerate(STAIRS):
        top = edge - WALL_EXTRA * TILE
        n.append(f'[node name="Stairs{k + 1}" type="Sprite2D" parent="."]\nz_index = -8\nposition = Vector2({x + TILE}, {top + STAIR_ROWS * TILE / 2})\n'
                 f'texture = ExtResource("{"14_stairs_town" if style == "town" else "15_stairs_stone"}")\n')

    # Cliffs, sea and the town's outer walls, merged into rectangles.
    walls = merge_rects(blocked, LEFT, TOP, TILE)
    walls += [(LEFT - 40, TOP - 40, -24, TOP), (24, TOP - 40, RIGHT + 40, TOP),   # north, gap for the road
              (-64, TOP - 80, -24, TOP - 40), (24, TOP - 80, 64, TOP - 40),     # road walls beyond the edge
              (LEFT - 40, TOP, LEFT, BOTTOM), (RIGHT, TOP, RIGHT + 40, BOTTOM),
              (LEFT - 40, BOTTOM, RIGHT + 40, BOTTOM + 40)]
    n.append('[node name="Walls" type="StaticBody2D" parent="."]\n')
    for k, (x0, y0, x1, y1) in enumerate(walls):
        n.append(f'[node name="W{k}" type="CollisionShape2D" parent="Walls"]\nposition = Vector2({(x0 + x1) / 2}, {(y0 + y1) / 2})\n'
                 f'shape = SubResource("{shape(x1 - x0, y1 - y0)}")\n')

    # Lighthouse yard: low walls around the tower with the door gate in front.
    lx, ly = LIGHTHOUSE
    n.append(f'''[node name="LighthouseYard" type="StaticBody2D" parent="."]
position = Vector2({lx}, {ly})

[node name="West" type="CollisionShape2D" parent="LighthouseYard"]
position = Vector2(-60, 0)
shape = SubResource("{shape(10, 170)}")

[node name="East" type="CollisionShape2D" parent="LighthouseYard"]
position = Vector2(60, 0)
shape = SubResource("{shape(10, 170)}")

[node name="North" type="CollisionShape2D" parent="LighthouseYard"]
position = Vector2(0, -85)
shape = SubResource("{shape(120, 10)}")

[node name="FrontWest" type="CollisionShape2D" parent="LighthouseYard"]
position = Vector2(-41, 85)
shape = SubResource("{shape(38, 10)}")

[node name="FrontEast" type="CollisionShape2D" parent="LighthouseYard"]
position = Vector2(41, 85)
shape = SubResource("{shape(38, 10)}")

[node name="YardWall" type="Line2D" parent="LighthouseYard"]
z_index = -7
points = PackedVector2Array(-22, 85, -60, 85, -60, -85, 60, -85, 60, 85, 22, 85)
width = 6.0
default_color = Color(0.95, 0.93, 0.87, 1)

[node name="Lighthouse" parent="." instance=ExtResource("17_lighthouse")]
position = Vector2({lx}, {ly - 25})

[node name="LighthouseDoor" parent="." instance=ExtResource("10_gate")]
position = Vector2({lx}, {ly + 85})
gate_id = &"kalmora_lighthouse_door"

[node name="Card_lighthouse_lens" parent="." instance=ExtResource("6_pick")]
position = Vector2({lx}, {ly + 40})
card_id = &"lighthouse_lens"
behind_gate = &"kalmora_lighthouse_door"
''')
    check_spot(stand, blocked, "lighthouse lens", lx, ly + 40, UPPER)

    n.append(f'''[node name="Fountain" parent="." instance=ExtResource("18_fountain")]
position = Vector2{FOUNTAIN}

[node name="Merchant" parent="." instance=ExtResource("8_merchant")]
position = Vector2{MERCHANT}
stall_texture = ExtResource("16_stall")

[node name="NorthGate" parent="." instance=ExtResource("10_gate")]
position = Vector2(0, {TOP + 90})
gate_id = &"kalmora_north_gate"

[node name="ToThornveil" parent="." instance=ExtResource("11_exit")]
position = Vector2(0, {TOP - 20})
target_scene = "res://scenes/world/thornveil.tscn"
target_spawn = &"from_kalmora"

[node name="SafeZone" type="Area2D" parent="."]
collision_layer = 0
collision_mask = 6
monitorable = false
script = ExtResource("9_safe")

[node name="CollisionShape2D" type="CollisionShape2D" parent="SafeZone"]
position = Vector2({cx}, {cy})
shape = SubResource("{shape(RIGHT - LEFT, BOTTOM - TOP)}")

[node name="Spawns" type="Node2D" parent="."]
''')
    # The gate road must be walkable ground on the upper level.
    check_spot(stand, blocked, "north gate", 0, TOP + 110, UPPER)
    for name, (x, y) in SPAWNS.items():
        n.append(f'[node name="{name}" type="Marker2D" parent="Spawns"]\nposition = Vector2({x}, {y})\n')
    n.append('[node name="RivalSpots" type="Node2D" parent="."]\n')
    for name, (x, y) in RIVAL_SPOTS.items():
        n.append(f'[node name="{name}" type="Marker2D" parent="RivalSpots"]\nposition = Vector2({x}, {y})\n')

    taken = [p for _, p in CARDS] + DUMMIES + list(RIVAL_SPOTS.values()) + list(SPAWNS.values()) \
        + [EXTRA_SALT_COMPASS, MERCHANT, FOUNTAIN, (lx, ly), (0, TOP + 90)]
    for card, (x, y) in CARDS:
        n.append(f'[node name="Card_{card}" parent="." instance=ExtResource("6_pick")]\nposition = Vector2({x}, {y})\ncard_id = &"{card}"\n')
    n.append(f'[node name="Card_salt_compass_2" parent="." instance=ExtResource("6_pick")]\nposition = Vector2{EXTRA_SALT_COMPASS}\ncard_id = &"salt_compass"\n')
    for k, (x, y) in enumerate(DUMMIES):
        check_spot(stand, blocked, "dummy", x, y, QUAY)
        n.append(f'[node name="TrainingDummy{k + 1}" parent="." instance=ExtResource("7_dummy")]\nposition = Vector2({x}, {y})\n')
    for name, prop, (x, y) in BUILDINGS:
        check_spot(stand, blocked, name, x, y)
        n.append(f'[node name="{name}" parent="." instance=ExtResource("{prop_ids[prop]}")]\nposition = Vector2({x}, {y})\n')
        taken.append((x, y))
        # A lantern by every front door.
        n.append(f'[node name="{name}Lamp" type="PointLight2D" parent="."]\nposition = Vector2({x}, {y - 30})\n'
                 f'texture_scale = 0.9\nscript = ExtResource("20_lamp")\nmax_energy = 0.8\n')
        if name in DOORS:
            dx, interior = DOORS[name]
            n.append(f'[node name="{name}Door" parent="." instance=ExtResource("11_exit")]\nposition = Vector2({x + dx}, {y + 4})\n'
                     f'scale = Vector2(0.5, 1)\ntarget_scene = "{interior}"\ntarget_spawn = &"door"\n')

    # Residents and the quay's unmarked crates.
    for npc_id, display, sprite_id, (x, y), wander, lines in NPCS:
        check_spot(stand, blocked, npc_id, x, y)
        frames_id = f"n_{sprite_id}"
        ext.append(('SpriteFrames', f"res://assets/sprites/npcs/{sprite_id}/{sprite_id}_frames.tres", frames_id))
        quoted = ", ".join('"' + line.replace('"', '\\"') + '"' for line in lines)
        n.append(f'[node name="Npc_{npc_id}" parent="." instance=ExtResource("19_npc")]\nposition = Vector2({x}, {y})\n'
                 f'npc_id = &"{npc_id}"\ndisplay_name = "{display}"\nsprite_frames = ExtResource("{frames_id}")\n'
                 f'lines = PackedStringArray({quoted})\nwander_radius = {float(wander)}\n')
        taken.append((x, y))
    for clue, (x, y) in CLUE_CRATES:
        check_spot(stand, blocked, clue, x, y, QUAY)
        n.append(f'[node name="Clue_{clue}" parent="." instance=ExtResource("21_clue")]\nposition = Vector2({x}, {y})\nclue_id = &"{clue}"\n')
        taken.append((x, y))

    # Trees, then props. Everything is placed on purpose (see TREES/PROPS/LAMPS);
    # a spot that lands on a wall, stairs, or something already placed is an error
    # in the layout, so the build stops and says where.
    crowd = lambda x, y, r: next(((a, b) for a, b in taken if (x - a) ** 2 + (y - b) ** 2 < r ** 2), None)

    def place_check(name, x, y, clearance=18):
        r, c = cell_of(x, y)
        if not (0 <= r < ROWS and 0 <= c < COLS) or blocked[r][c] or stand[r][c] < 0 or (r, c) in stair_cells:
            raise SystemExit(f"{name} at ({x}, {y}) is not on open ground")
        hit = crowd(x, y, clearance)
        if hit:
            raise SystemExit(f"{name} at ({x}, {y}) crowds something at {hit}")

    for k, (prop, (x, y)) in enumerate(TREES):
        place_check(prop, x, y, 24)
        taken.append((x, y))
        n.append(f'[node name="{prop.split("_")[1].title()}{k + 1}" parent="." instance=ExtResource("{prop_ids[prop]}")]\nposition = Vector2({x}, {y})\n')

    prop_tex = {}
    prop_count = [0]
    def prop_node(name, x, y, kind="solid"):
        """kind: solid (collides at its base), decal (flat on the ground), free (y-sorted, no collision)."""
        path = EXTRA_TEX.get(name, f"{PROP_DIR}{name}.png")
        if name not in prop_tex:
            prop_tex[name] = f"p_{name}"
            ext.append(('Texture2D', f"res://{path}", prop_tex[name]))
        im = Image.open(path)
        bottom = im.getbbox()[3]
        prop_count[0] += 1
        node = f"P{prop_count[0]}_{name}"
        if kind == "decal":
            return (f'[node name="{node}" type="Sprite2D" parent="."]\nz_index = -9\nposition = Vector2({x}, {y})\n'
                    f'texture = ExtResource("{prop_tex[name]}")\n')
        taken.append((x, y))
        if kind == "free":
            return (f'[node name="{node}" type="Sprite2D" parent="."]\nposition = Vector2({x}, {y})\n'
                    f'offset = Vector2(0, {im.height / 2 - bottom})\ntexture = ExtResource("{prop_tex[name]}")\n')
        fw, fh = FOOTPRINTS.get(name, (16, 8))
        return (f'[node name="{node}" type="StaticBody2D" parent="."]\nposition = Vector2({x}, {y})\n\n'
                f'[node name="Sprite" type="Sprite2D" parent="{node}"]\nposition = Vector2(0, {im.height / 2 - bottom})\n'
                f'texture = ExtResource("{prop_tex[name]}")\n\n'
                f'[node name="Base" type="CollisionShape2D" parent="{node}"]\nposition = Vector2(0, {-fh / 2})\n'
                f'shape = SubResource("{shape(fw, fh)}")\n')

    for name, x, y in PROPS:
        place_check(name, x, y)
        n.append(prop_node(name, x, y))
    for name, x, y in LAMPS:
        place_check(name, x, y)
        n.append(prop_node(name, x, y))
        n.append(f'[node name="Light{prop_count[0]}" type="PointLight2D" parent="."]\nposition = Vector2({x + 6}, {y - 26})\n'
                 f'texture_scale = 1.3\nscript = ExtResource("20_lamp")\n')
    # Bollards line the harbor edge wherever the waterfront is clear.
    y, xs = BOLLARD_ROW
    for x in xs:
        r, c = cell_of(x, y)
        if not blocked[r][c] and not crowd(x, y, 30) and not 48 <= x <= 176:  # keep the jetty open
            n.append(prop_node("bollard", x, y))
    for name, x, y in DECALS:
        n.append(prop_node(name, x, y, "decal"))
    for name, x, y in BIRDS:
        n.append(prop_node(name, x, y, "free"))

    n.append('''[node name="Player" parent="." instance=ExtResource("2_player")]
position = Vector2(0, -150)

[node name="HUD" parent="." instance=ExtResource("3_hud")]

[node name="Binder" parent="." instance=ExtResource("4_binder")]

[node name="ShopPanel" parent="." instance=ExtResource("5_shop")]

[node name="DialogueBox" parent="." instance=ExtResource("22_dialogue")]
''')
    head = f'[gd_scene load_steps={len(ext) + len(subs) + 1} format=3]\n\n' + "".join(
        f'[ext_resource type="{t}" path="{p}" id="{i}"]\n' for t, p, i in ext) + "\n"
    open(SCENE, "w", encoding="utf-8", newline="\n").write(head + "\n".join(subs.values()) + "\n" + "\n".join(n))
    print(f"kalmora: {COLS}x{ROWS} cells, {len(walls)} wall rects, {len(taken)} placed things")


if __name__ == "__main__":
    main()
