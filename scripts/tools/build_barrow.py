"""Builds the Old Barrow: the first king's grave, a burial mound on the Stonewatch
Downs above the Aurewind circle.

Aldous's stones tell one story (a crown, and under it a line of figures, each
smaller); the barrow is where it begins. Four parts: the entry passage down from
the mound's stone door, the hall of pillars (carved standing stones, their runes
glowing), the bone niche where the hounds have made a den, and the king's chamber
at the far end: his tomb, the first carving of the line, and a chest of grave goods.

Terrain is composed with terrain.compose() from the Hollow's PixelLab cave cliff set
(assets/sprites/tiles/hollow/cliff/cave), repainted earthen: level 0 is the packed
floor, level 1 rock and turf, its faces hanging one row below it. Collision is every
cell that isn't floor. Layout in cells (32 px): chambers are circles, tunnels
capsules between cell points.

Run: python scripts/tools/build_barrow.py
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

os.chdir(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, "scripts/tools")
from terrain import CliffSet, compose, merge_rects  # noqa: E402

TILE = 32
COLS, ROWS = 38, 30
LEFT, TOP = -COLS * TILE // 2, -ROWS * TILE // 2
ART = "assets/sprites/tiles/barrow/"
GROUND_PNG = ART + "barrow_ground.png"
LEVEL_PNG = ART + "barrow_levels.png"
SCENE = "scenes/world/aurewind_barrow.tscn"
PILLAR = "assets/sprites/tiles/aurewind/stone_pillar.png"

CHAMBERS = {
    "entry": (19, 24, 3.6),
    "hall": (19, 14, 6.4),
    "niche": (6, 13, 4.0),
    "king": (30, 6, 4.8),
}
TUNNELS = [
    ((19, 24), (19, 29.9), 2.0),    # up the steps to the mound's door, at the bottom edge
    ((19, 24), (19, 18), 2.2),
    ((14, 14), (6, 13), 1.8),       # the side passage to the bone niche
    ((24, 10), (30, 6), 1.9),       # on to the king's chamber
]


def cell_px(cx, cy):
    return (LEFT + cx * TILE, TOP + cy * TILE)


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy or 1)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def is_floor(cx, cy):
    wobble = 0.35 * math.sin(cx * 1.3 + cy * 0.7) + 0.25 * math.sin(cx * 0.5 - cy * 1.1)
    for x, y, r in CHAMBERS.values():
        if math.hypot(cx - x, (cy - y) * 1.1) < r + wobble:
            return True
    return any(seg_dist(cx, cy, *a, *b) < w + wobble * 0.5 for a, b, w in TUNNELS)


def build_ground():
    levels = [[0 if is_floor(c, r) and 0 < c < COLS and r > 0 else 1 for c in range(COLS + 1)]
              for r in range(ROWS + 1)]
    cave = CliffSet("assets/sprites/tiles/hollow/cliff/cave")
    img, stand = compose(levels, {(0, 1): cave}, {0: ((0, 1), "lower"), 1: ((0, 1), "upper")}, TILE)
    a = np.array(img).astype(float)
    rock = np.kron(np.array([[1 if v == 1 else 0 for v in row] for row in stand], np.uint8),
                   np.ones((TILE, TILE), np.uint8)).astype(bool)
    a[rock, :3] *= 0.6
    # The set's flat ice floor is a fine grid that reads as tiles: open floor is
    # repainted as frozen ground instead (swirls of frost and clear ice, hairline
    # cracks, a few glints), feathered into the drawn edges along the walls.
    H, W = a.shape[:2]
    rng = np.random.default_rng(7)

    def noise(scale):
        small = rng.random((H // scale + 2, W // scale + 2)).astype(np.float32)
        return np.asarray(Image.fromarray((small * 255).astype(np.uint8)).resize(
            ((W // scale + 2) * scale, (H // scale + 2) * scale), Image.BICUBIC))[:H, :W].astype(np.float32) / 255.0

    open_cells = [[stand[r][c] == 0 for c in range(COLS)] for r in range(ROWS)]
    inner = np.kron(np.array(open_cells, np.uint8), np.ones((TILE, TILE), np.uint8)).astype(np.float32)
    inner = np.pad(inner, ((0, H - inner.shape[0]), (0, W - inner.shape[1])))
    feather = np.asarray(Image.fromarray((inner * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))).astype(np.float32) / 255.0
    frost = np.clip(noise(48) * 0.6 + noise(16) * 0.4, 0, 1)
    floor = (np.array([104, 88, 70], np.float32) * (1 - frost[..., None])
             + np.array([136, 118, 92], np.float32) * frost[..., None])
    floor *= (0.97 + 0.06 * noise(4))[..., None]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    crack = np.abs(np.sin(xx * 0.045 + yy * 0.031 + noise(64) * 9.0)) < 0.018
    floor[crack] *= 0.92
    glint = (rng.random((H, W)) > 0.9985) & (frost > 0.55)
    floor[glint] = (176, 168, 150)                  # bone chips and pale grit
    a[..., :3] = a[..., :3] * (1 - feather[..., None]) + floor * feather[..., None]
    img = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    img.save(GROUND_PNG)
    lv = Image.new("RGB", (COLS, ROWS))
    for r in range(ROWS):
        for c in range(COLS):
            lv.putpixel((c, r), (0, 0, 0) if stand[r][c] == 0 else (255, 0, 0))
    lv.save(LEVEL_PNG)
    return stand


SPAWN_IN = (19, 27.5)
EXIT_AT = (19, 29.6)
WOLVES = [(5, 12), (7.5, 15)]                  # briar hounds denning in the bone niche
CRYSTALS = [(15.5, 11.5), (22.5, 11.5), (15.5, 16.5), (22.5, 16.5), (28, 5), (32, 5)]   # rune pillars
CHESTS = [
    # id, cell, gold, card, item, count
    ("niche_bones", (4.5, 14.5), 20, "", "bread", 2),
    ("grave_goods", (30, 8.2), 80, "", "healers_tonic", 2),
]
NPCS = []
# (sprite, cell (its foot), collision footprint w x h)
PROPS = [
    (ART + "sarcophagus.png", (30, 5.6), (80, 30)),
    (ART + "bone_nest.png", (6.5, 13.6), (34, 12)),
]
READABLES = [
    ("The barrow door", (19, 26.4), [
        "A passage of fitted stones going down into the mound. Over the door the lintel is carved with a crown, very worn, and nothing else.",
        "Fresh scuffs in the dirt of the steps. Somebody has been down here, more than once, and swept up after.",
    ]),
    ("The hall of pillars", (19, 14), [
        "Six carved stones stand in a ring, the same as the circle on the downs above, but whole and sharp-edged down here where no rain falls.",
        "On every one: the crown, and under it the line of figures, each one smaller than the one before. The runes in the cuts glow faintly, green, without any light to catch.",
    ]),
    ("Gnawed bones", (6.2, 11.2), [
        "The hounds have dragged old bones into the niche and made a nest of them. Small bones, mostly.",
        "A copper tag on a cord, green with age: a number, and the same crown as the lintel.",
    ]),
    ("The first king's tomb", (31.4, 6.4), [
        "A long stone box under a carved lid: a king lying with his hands on a sword, a crown on his head. Round the sides of the box, a line of small figures carrying sacks walks all the way round and back to his feet.",
        "Cut into the lid at his feet, in letters older than the island's roads: 'HE WHO HOLDS THE SET HOLDS THE ISLE. WHAT THE SET COSTS IS CARVED BELOW.' Below, the stone has been chiselled smooth.",
    ]),
]

def main():
    stand = build_ground()

    def check(name, cx, cy):
        c, r = int(cx), int(cy)
        if not (0 <= r < ROWS and 0 <= c < COLS) or stand[r][c] != 0:
            raise SystemExit(f"{name} at cell ({cx}, {cy}) is not on the cave floor")

    for name, (cx, cy) in [("spawn", SPAWN_IN)] + [(f"wolf{k}", p) for k, p in enumerate(WOLVES)] \
            + [(f"chest {c[0]}", c[1]) for c in CHESTS] + [(f"readable {t}", p) for t, p, _ in READABLES] \
            + [("pillar", p) for p in CRYSTALS] + [(f"npc {c[0]}", c[2]) for c in NPCS]:
        check(name, cx, cy)

    subs = {}

    def shape(w, h):
        key = f"R{w:g}x{h:g}".replace(".", "_")
        subs[key] = f'[sub_resource type="RectangleShape2D" id="{key}"]\nsize = Vector2({w}, {h})\n'
        return key

    ext = [
        ('Script', "res://scripts/world/zone.gd", "1_zone"),
        ('PackedScene', "res://scenes/characters/player.tscn", "2_player"),
        ('PackedScene', "res://scenes/ui/hud.tscn", "3_hud"),
        ('PackedScene', "res://scenes/ui/binder.tscn", "4_binder"),
        ('PackedScene', "res://scenes/ui/shop_panel.tscn", "5_shop"),
        ('PackedScene', "res://scenes/ui/dialogue_box.tscn", "6_dialogue"),
        ('PackedScene', "res://scenes/systems/zone_exit.tscn", "7_exit"),
        ('Texture2D', "res://" + GROUND_PNG, "8_ground"),
        ('Texture2D', "res://" + LEVEL_PNG, "9_levels"),
        ('PackedScene', "res://scenes/characters/briar_hound.tscn", "10_wolf"),
        ('Script', "res://scripts/systems/chest.gd", "11_chest"),
        ('Texture2D', "res://assets/sprites/tiles/thornveil/props/chest.png", "12_chest_shut"),
        ('Texture2D', "res://assets/sprites/tiles/thornveil/props/chest_open.png", "13_chest_open"),
        ('Script', "res://scripts/systems/readable.gd", "14_read"),
        ('Script', "res://scripts/systems/lamp_light.gd", "15_lamp"),
        ('Texture2D', "res://" + PILLAR, "16_ice"),
        ('PackedScene', "res://scenes/characters/npc.tscn", "17_npc"),
    ]
    n = [f'''[node name="AurewindBarrow" type="Node2D"]
y_sort_enabled = true
script = ExtResource("1_zone")
display_name = "The Old Barrow, under the Stonewatch Downs"
underground = true
water_shimmer = false
level_map = ExtResource("9_levels")
level_cell = {TILE}
level_origin = Vector2({LEFT}, {TOP})

[node name="Dark" type="CanvasModulate" parent="."]
color = Color(0.52, 0.5, 0.48, 1)

[node name="GroundTiles" type="Sprite2D" parent="."]
z_index = -10
position = Vector2({LEFT + COLS * TILE / 2}, {TOP + ROWS * TILE / 2})
texture = ExtResource("8_ground")
''']
    solid = [[stand[r][c] != 0 for c in range(COLS)] for r in range(ROWS)]
    walls = merge_rects(solid, LEFT, TOP, TILE)
    ex, ey = cell_px(*EXIT_AT)
    right, bottom = LEFT + COLS * TILE, TOP + ROWS * TILE
    walls += [(LEFT - 40, TOP - 40, right + 40, TOP), (LEFT - 40, TOP, LEFT, bottom), (right, TOP, right + 40, bottom),
              (LEFT - 40, bottom, ex - 40, bottom + 40), (ex + 40, bottom, right + 40, bottom + 40)]
    n.append('[node name="Walls" type="StaticBody2D" parent="."]\n')
    for k, (x0, y0, x1, y1) in enumerate(walls):
        n.append(f'[node name="W{k}" type="CollisionShape2D" parent="Walls"]\nposition = Vector2({(x0 + x1) / 2}, {(y0 + y1) / 2})\n'
                 f'shape = SubResource("{shape(x1 - x0, y1 - y0)}")\n')
    sx, sy = cell_px(*SPAWN_IN)
    n.append(f'''[node name="Spawns" type="Node2D" parent="."]

[node name="from_aurewind" type="Marker2D" parent="Spawns"]
position = Vector2({sx}, {sy})

[node name="RivalSpots" type="Node2D" parent="."]

[node name="ToAurewind" parent="." instance=ExtResource("7_exit")]
position = Vector2({ex}, {bottom - 4})
target_scene = "res://scenes/world/aurewind_plains.tscn"
target_spawn = &"from_barrow"
exit_hint = true
''')
    for rid in ("runner", "raider", "hoarder"):
        n.append(f'[node name="{rid}" type="Marker2D" parent="RivalSpots"]\nposition = Vector2({sx}, {sy - 20})\n')
    for k, (cx, cy) in enumerate(WOLVES):
        x, y = cell_px(cx, cy)
        n.append(f'[node name="FrostWolf{k}" parent="." instance=ExtResource("10_wolf")]\nposition = Vector2({x}, {y})\n')
    for cid, (cx, cy), gold, card, item, count in CHESTS:
        x, y = cell_px(cx, cy)
        n.append(f'[node name="Chest_{cid}" type="StaticBody2D" parent="."]\nposition = Vector2({x}, {y})\n'
                 f'script = ExtResource("11_chest")\nchest_id = &"grotto_{cid}"\ncard_id = &"{card}"\ngold = {gold}\n'
                 + (f'item_id = &"{item}"\nitem_count = {count}\n' if item else "")
                 + f'closed_texture = ExtResource("12_chest_shut")\nopen_texture = ExtResource("13_chest_open")\n\n'
                 f'[node name="Base" type="CollisionShape2D" parent="Chest_{cid}"]\nposition = Vector2(0, -5)\n'
                 f'shape = SubResource("{shape(30, 10)}")\n')
    for k, (title, (cx, cy), lines) in enumerate(READABLES):
        x, y = cell_px(cx, cy)
        quoted = ", ".join('"' + line.replace('"', '\\"') + '"' for line in lines)
        n.append(f'[node name="Read{k}" type="Node2D" parent="."]\nposition = Vector2({x}, {y})\n'
                 f'script = ExtResource("14_read")\ntitle = "{title}"\nlines = PackedStringArray({quoted})\n')
    for npc_id, display, (cx, cy), lines in NPCS:
        x, y = cell_px(cx, cy)
        ext.append(('SpriteFrames', f"res://assets/sprites/npcs/{npc_id}/{npc_id}_frames.tres", f"n_{npc_id}"))
        quoted = ", ".join('"' + line.replace('"', '\\"') + '"' for line in lines)
        n.append(f'[node name="Npc_{npc_id}" parent="." instance=ExtResource("17_npc")]\nposition = Vector2({x}, {y})\n'
                 f'npc_id = &"{npc_id}"\ndisplay_name = "{display}"\nsprite_frames = ExtResource("n_{npc_id}")\n'
                 f'lines = PackedStringArray({quoted})\n\n'
                 f'[node name="Lantern_{npc_id}" type="PointLight2D" parent="."]\nposition = Vector2({x + 14}, {y - 18})\n'
                 f'texture_scale = 1.3\nscript = ExtResource("15_lamp")\nalways_on = true\nmax_energy = 0.9\n'
                 f'tint = Color(1.0, 0.78, 0.45, 1)\nflicker = 0.12\n')
    h = Image.open(PILLAR).height
    for k, (cx, cy) in enumerate(CRYSTALS):
        x, y = cell_px(cx, cy)
        n.append(f'[node name="Crystal{k}" type="StaticBody2D" parent="."]\nposition = Vector2({x}, {y})\n\n'
                 f'[node name="Sprite" type="Sprite2D" parent="Crystal{k}"]\noffset = Vector2(0, {-h / 2 + 4})\n'
                 f'flip_h = {"true" if k % 2 else "false"}\ntexture = ExtResource("16_ice")\n\n'
                 f'[node name="Base" type="CollisionShape2D" parent="Crystal{k}"]\nposition = Vector2(0, -5)\n'
                 f'shape = SubResource("{shape(28, 10)}")\n\n'
                 f'[node name="CrystalGlow{k}" type="PointLight2D" parent="."]\nposition = Vector2({x}, {y - 20})\n'
                 f'texture_scale = 1.2\nscript = ExtResource("15_lamp")\nalways_on = true\nmax_energy = 0.85\n'
                 f'tint = Color(0.5, 1.0, 0.7, 1)\nflicker = 0.06\n')
    # Furniture of the dead: the king's sarcophagus, the hounds' bone nest.
    for k, (path, (cx, cy), (fw, fh)) in enumerate(PROPS):
        x, y = cell_px(cx, cy)
        im = Image.open(path)
        bottom = im.getbbox()[3]
        ext.append(('Texture2D', "res://" + path, f"p_{k}"))
        n.append(f'[node name="Prop{k}" type="StaticBody2D" parent="."]\nposition = Vector2({x}, {y})\n\n'
                 f'[node name="Sprite" type="Sprite2D" parent="Prop{k}"]\noffset = Vector2(0, {im.height / 2 - bottom})\n'
                 f'texture = ExtResource("p_{k}")\n\n'
                 f'[node name="Base" type="CollisionShape2D" parent="Prop{k}"]\nposition = Vector2(0, {-fh / 2})\n'
                 f'shape = SubResource("{shape(fw, fh)}")\n')
    # A shaft of grey daylight down the entry steps.
    wx, wy = cell_px(19, 27)
    n.append(f'[node name="DoorLight" type="PointLight2D" parent="."]\nposition = Vector2({wx}, {wy})\n'
             f'texture_scale = 1.6\nscript = ExtResource("15_lamp")\nalways_on = true\nmax_energy = 0.6\n'
             f'tint = Color(0.9, 0.9, 0.85, 1)\nflicker = 0.0\n')
    n.append(f'''[node name="Player" parent="." instance=ExtResource("2_player")]
position = Vector2({sx}, {sy})

[node name="HUD" parent="." instance=ExtResource("3_hud")]

[node name="Binder" parent="." instance=ExtResource("4_binder")]

[node name="ShopPanel" parent="." instance=ExtResource("5_shop")]

[node name="DialogueBox" parent="." instance=ExtResource("6_dialogue")]
''')
    head = f'[gd_scene load_steps={len(ext) + len(subs) + 1} format=3]\n\n'
    head += "".join(f'[ext_resource type="{t}" path="{p}" id="{i}"]\n' for t, p, i in ext) + "\n"
    head += "\n".join(subs.values()) + "\n"
    open(SCENE, "w", encoding="utf-8", newline="\n").write(head + "\n".join(n))
    print(f"barrow: {COLS}x{ROWS} cells, {len(walls)} wall rects")


if __name__ == "__main__":
    main()
