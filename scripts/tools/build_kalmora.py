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
import random

from PIL import Image

os.chdir(os.path.join(os.path.dirname(__file__), "..", ".."))

from terrain import CliffSet, compose, merge_rects  # noqa: E402

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
BUILDINGS = [  # (node, prop, position = footprint bottom-centre)
    ("Tavern", "kalmora_tavern", (-360, 110)),
    ("Harbormaster", "kalmora_harbormaster", (-640, 110)),
    ("Townhouse1", "kalmora_townhouse_tall", (-470, -290)),
    ("Cottage1", "kalmora_cottage", (-660, -215)),
    ("CardShop", "kalmora_card_shop", (470, -235)),
    ("Villa", "kalmora_villa", (-330, -720)),
    ("NonnaHouse", "kalmora_townhouse_tall", (250, -790)),
    ("Cottage3", "kalmora_cottage", (-620, -830)),
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
    ("pip", "Pip", "pip", (-120, 60), 90, [
        "Fresh fish! Well. Fresh-ish.",
        "My cousin went to work out in Duskara last spring. Good pay, they said. He hasn't written.",
    ]),
    ("sailor", "Deckhand Luca", "sailor", (330, 40), 110, [
        "Sailed round the whole isle once. Vetrassa's got the tallest spires you ever saw.",
        "You racers bind your cards in town, right? Thieves love a loose card on the road.",
    ]),
    ("baker", "Baker Rosa", "baker", (-220, -330), 120, [
        "Warm bread! Two coins a loaf, one if you tell me a good rumor.",
        "The Runner came through at dawn, all scarf and no manners. Didn't even stop for bread.",
    ]),
    ("tomas", "Keeper Tomas", "tomas", (520, -560), 0, [
        "Lost my lighthouse wick somewhere by the west houses. Can't light the lamp without it.",
        "That lens up there's worth more than my whole cottage. Door stays locked, wick or no wick.",
    ]),
    ("rook", "Guard Rook", "rook", (70, -880), 0, [
        "North road's sealed. A Salt Compass opens it. Old rule, nobody remembers why.",
        "Thornveil's no place to wander with loose cards. The hounds don't care, but the Raider does.",
    ]),
]
CLUE_CRATES = [("crate_sand", (-20, 130)), ("crate_glove", (210, 125)), ("crate_ledger", (-70, 95))]
CARDS = [  # (card, position)
    ("harbor_lantern", (-600, 125)), ("coral_coin", (250, 125)), ("gull_feather", (600, 125)),
    ("sea_glass", (-170, 125)), ("sunken_crown_shard", (112, 300)),
    ("salt_compass", (-300, -230)), ("tide_bell", (230, -370)), ("terracotta_tile", (-150, -470)),
    ("lighthouse_wick", (-560, -620)), ("fishers_knot", (-40, 100)),
]
EXTRA_SALT_COMPASS = (-600, -430)
DUMMIES = [(470, 60), (540, 100), (500, 140)]
RIVAL_SPOTS = {"runner": (-450, -600), "raider": (380, -700), "hoarder": (-140, -660)}
SPAWNS = {"town": (0, -150), "from_thornveil": (0, -860)}
LIGHTHOUSE = (600, -640)      # yard centre; the tower stands in its north half
MERCHANT = (160, -250)
FOUNTAIN = (0, -250)
DECOR_COUNT = {"kalmora_cypress": 14, "kalmora_olive": 10}

# Prop pack (assets/sprites/tiles/kalmora/props): what each district is dressed with.
PROP_DIR = "assets/sprites/tiles/kalmora/props/"
DISTRICT_PROPS = {
    QUAY: (["barrel", "barrels", "crate", "crates", "sack", "rope", "anchor", "net_crate", "fish_basket",
             "lobster_trap", "buoy", "oars", "ice_crates", "cannonballs", "ship_wheel", "rowboat", "fishing_rods",
             "tackle_box", "bucket", "mop_bucket", "straw_hat_crate", "flour_sack", "lemons_crate"], 46),
    MARKET: (["oranges_basket", "bread_basket", "apples_crate", "lemons_crate", "amphora", "amphorae", "signpost",
               "menu_board", "cart", "wheelbarrow", "bench_wood", "geraniums", "lemon_tree_pot", "lavender_planter",
               "cafe_table", "umbrella_table", "bougainvillea_box", "small_well", "water_tap", "barrel", "sack"], 40),
    UPPER: (["bench_stone", "bench_wood", "geraniums", "lemon_tree_pot", "lavender_planter", "potted_palm",
              "laundry_basket", "laundry_line", "candle_shrine", "fence", "low_wall", "cactus", "amphora",
              "bougainvillea_box", "wheelbarrow"], 34),
}
DECALS = (["puddle", "leaves", "moss"], 60)
# Lamp posts line the quay's edge and the market wall; bollards line the harbor.
LAMP_ROWS = [(125, range(-700, 700, 224)), (-110, range(-640, 700, 256))]
BOLLARD_ROW = (150, range(-736, 736, 96))


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
    for prop in DECOR_COUNT:
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

    # Decor on open ground of the three walkable levels, clear of everything placed.
    rng = random.Random(7)
    blocked_near = lambda x, y: any((x - a) ** 2 + (y - b) ** 2 < 70 ** 2 for a, b in taken)
    for prop, count in DECOR_COUNT.items():
        placed = 0
        for _ in range(4000):
            if placed == count:
                break
            x, y = rng.randint(LEFT + 40, RIGHT - 40), rng.randint(TOP + 60, 200)
            r, c = cell_of(x, y)
            ok = all(0 <= r + dr < ROWS and 0 <= c + dc < COLS and not blocked[r + dr][c + dc]
                     and (r + dr, c + dc) not in stair_cells for dr in (-2, -1, 0, 1) for dc in (-1, 0, 1))
            if not ok or blocked_near(x, y) or abs(x) < 70 and y < -500:
                continue
            placed += 1
            taken.append((x, y))
            n.append(f'[node name="{prop.split("_")[1].title()}{placed}" parent="." instance=ExtResource("{prop_ids[prop]}")]\nposition = Vector2({x}, {y})\n')

    # Props: lamp and bollard rows, then each district's clutter, favoring spots
    # against walls and buildings like a lived-in town; decals go on the ground.
    prop_tex = {}
    prop_count = [0]
    def prop_node(name, x, y, solid=True):
        if name not in prop_tex:
            rid = f"p_{name}"
            prop_tex[name] = rid
            ext.append(('Texture2D', f"res://{PROP_DIR}{name}.png", rid))
        im = Image.open(PROP_DIR + name + ".png")
        bottom = im.getbbox()[3]
        prop_count[0] += 1
        node = f"P{prop_count[0]}_{name}"
        taken.append((x, y))
        if not solid:
            return (f'[node name="{node}" type="Sprite2D" parent="."]\nz_index = -9\nposition = Vector2({x}, {y})\n'
                    f'texture = ExtResource("{prop_tex[name]}")\n')
        return (f'[node name="{node}" type="StaticBody2D" parent="."]\nposition = Vector2({x}, {y})\n\n'
                f'[node name="Sprite" type="Sprite2D" parent="{node}"]\nposition = Vector2(0, {im.height / 2 - bottom})\n'
                f'texture = ExtResource("{prop_tex[name]}")\n\n'
                f'[node name="Base" type="CollisionShape2D" parent="{node}"]\nposition = Vector2(0, -4)\n'
                f'shape = SubResource("{shape(16, 8)}")\n')

    def open_spot(x, y, clearance):
        r, c = cell_of(x, y)
        if not (0 <= r < ROWS and 0 <= c < COLS) or blocked[r][c] or (r, c) in stair_cells:
            return False
        if r + 1 < ROWS and blocked[r + 1][c] and stand[r][c] == QUAY and y > 100:
            return False  # keep the harbor edge walkable
        return all((x - a) ** 2 + (y - b) ** 2 >= clearance ** 2 for a, b in taken)

    for y, xs in LAMP_ROWS:
        for x in xs:
            if open_spot(x, y, 40):
                n.append(prop_node("lamp_post", x, y))
                n.append(f'[node name="Light{prop_count[0]}" type="PointLight2D" parent="."]\nposition = Vector2({x + 6}, {y - 26})\n'
                         f'texture_scale = 1.3\nscript = ExtResource("20_lamp")\n')
    y, xs = BOLLARD_ROW
    for x in xs:
        if open_spot(x, y, 30):
            n.append(prop_node("bollard", x, y))

    for level, (names, count) in DISTRICT_PROPS.items():
        placed = 0
        for _ in range(20000):
            if placed == count:
                break
            x, y = rng.randint(LEFT + 24, RIGHT - 24), rng.randint(TOP + 40, 200)
            r, c = cell_of(x, y)
            if not (0 <= r < ROWS and 0 <= c < COLS) or stand[r][c] != level or not open_spot(x, y, 34):
                continue
            against = (r > 0 and blocked[r - 1][c]) or any((x - a) ** 2 + (y - b) ** 2 < 90 ** 2 for _, _, (a, b) in BUILDINGS)
            if not against and rng.random() > 0.3:
                continue
            n.append(prop_node(rng.choice(names), x, y))
            placed += 1
    names, count = DECALS
    for _ in range(count):
        for _ in range(200):
            x, y = rng.randint(LEFT + 24, RIGHT - 24), rng.randint(TOP + 40, 200)
            r, c = cell_of(x, y)
            if 0 <= r < ROWS and 0 <= c < COLS and not blocked[r][c] and (r, c) not in stair_cells:
                n.append(prop_node(rng.choice(names), x, y, solid=False))
                taken.pop()  # decals don't crowd anything
                break

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
