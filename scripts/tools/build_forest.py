"""Dress a Thornveil-biome zone as a real forest (instead of scattered single trees).

Usage: python scripts/tools/build_forest.py [zone ...]   (default: every zone in FORESTS)

For each zone (layouts and path shapes come from build_ground.ZONES):
- Ground: the emerald meadow grass Kalmora uses, shaded darker and dappled like light
  through leaves, with dirt paths (Kalmora's dirt) blended per pixel: rounded,
  slightly ragged edges and a soft rim, never tile steps.
- Treeline: a double row of trees just inside the zone's edges, so its walls are a
  forest you can see, open only where a path leaves the map.
- Groves: clusters of firs and oaks (PixelLab-animated sway, scenes/world/props/
  forest_*.tscn) in the open ground, thick in places and thin in others, never on a
  path or near anything that matters (cards, monsters, exits, markers).
- Undergrowth: ferns, bushes, flowers, mushrooms, logs, rocks and stumps at the
  foot of the trees and along the path edges (decoration; rocks, logs and stumps
  have small colliders you can see).
- Soft shadows under everything, baked into the ground.
Replaces the zone's old Tree*/ForestTree* nodes and its previous forest dressing.
"""
import math
import os
import random
import re
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

os.chdir(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from build_ground import ZONES, remove_node  # noqa: E402
from build_ground import on_path as straight_path  # noqa: E402


def on_path(shapes, x, y, grow=0.0):
    """The zone's path shapes, bent into gentle meanders (the ends, where paths meet
    exits at the map edge, and the crossroads stay put: the bend fades out near them)."""
    return straight_path(shapes, x + MEANDER * math.sin(y / 83.0) * math.sin(x / 211.0 + 1.3),
                         y + MEANDER * math.sin(x / 97.0 + 0.7) * math.sin(y / 173.0), grow)


MEANDER = 16
from terrain import CornerSet  # noqa: E402

FOREST = "assets/sprites/tiles/forest/"
PROPS = FOREST + "props/"
GRASS = "assets/sprites/tiles/kalmora2/wang/grass_meadow"
DIRT = "assets/sprites/tiles/kalmora2/wang/dirt"
TREES = {  # kind -> (strip, frames, fps, trunk radius, shadow radius)
    "fir": (FOREST + "fir_sway.png", 8, 5, 7, 22),
    "oak": (FOREST + "oak_sway.png", 8, 5, 10, 30),
}
# Undergrowth: (prop, weight, collides)
UNDER = [("fern", 5, False), ("grass_clump", 4, False), ("berry_bush", 2, False), ("flowers", 3, False),
         ("mushrooms", 2, False), ("pale_mushrooms", 1, False), ("clover", 2, False), ("acorns", 1, False),
         ("pinecones", 1, False), ("branch", 1, False)]
LANDMARKS = [("rock", True), ("log", True), ("stump", True)]
FORESTS = ["sorenda", "wardens_grove", "lake_veyra"]   # Thornveil: build_thornveil.py

# Zones build_ground.py doesn't paint. Lake Veyra's scene comes from
# build_lake_veyra.py (run that first); its lake is an ellipse with an island, the
# same shape that script uses for the water collision.
EXTRA = {
    "lake_veyra": {
        "scene": "scenes/world/lake_veyra.tscn",
        "out": "assets/sprites/tiles/thornveil/lake_veyra_ground.png",
        "bounds": (-512, -400, 512, 400),
        "lake": (0.0, -60.0, 330.0, 190.0, 72.0),
        "paths": [
            ("line", [(560, 250), (400, 246), (250, 222), (80, 196), (0, 176)], 40),     # in from Thornveil to the bridge
            ("line", [(0, 180), (-200, 172), (-330, 96), (-352, 10), (-352, -44)], 32),  # round the south shore to the Shore Path
            ("line", [(-352, -76), (-310, -200), (-160, -306), (150, -312)], 28),        # the north shore
            ("line", [(-340, -150), (-446, -262), (-446, -312)], 26),                   # up to the Elder Grove seal
        ],
    },
}


def lake_water(cfg, x, y):
    if "lake" not in cfg:
        return False
    cx, cy, rx, ry, island = cfg["lake"]
    return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 < 1.0 and math.hypot(x - cx, y - cy) >= island


def near_lake(cfg, x, y, margin):
    """In the lake, or within `margin` px of its water."""
    if "lake" not in cfg:
        return False
    cx, cy, rx, ry, island = cfg["lake"]
    outer = ((x - cx) / (rx + margin)) ** 2 + ((y - cy) / (ry + margin)) ** 2 < 1.0
    return outer and math.hypot(x - cx, y - cy) >= island - margin

# Residents and story objects per zone (local coords). Residents are dogs and cats
# (sprites in assets/sprites/npcs/<id>/); readables use scripts/systems/readable.gd.
# Sorenda carries "What the Trees Remember": the village half knows where the Duskara
# work goes, and the Hollow keeps what a runaway child left behind.
LIFE = {
    "sorenda": {
        # The homes, the inn, lanterns and campfire are placed by build_sorenda.py; these
        # are the things round them: the woodcutter's pile and the herbalist's drying rack.
        "props": [
            ('res://assets/sprites/tiles/sorenda/woodpile.png', (-610, 20), True, (50, 16)),
            ('res://assets/sprites/tiles/sorenda/drying_rack.png', (560, -190), True, (40, 10)),
        ],
        # Extra open ground (x, y, radius): the Copper Kettle is wider than a home, so
        # its front corners and doorstep stay clear of trees.
        "clear": [(110, 236, 64), (320, 236, 64), (215, 280, 56), (110, 280, 40),
                  # the glades
                  (30, 160, 100), (-60, -300, 130), (-470, 100, 90), (430, 60, 80)],
        "butterflies": [((40, 160), 3), ((-80, -300), 2), ((-470, 90), 2), ((440, -80), 2)],
        # The woods between the glades: (x, y, rx, ry, trees).
        "thickets": [(-170, -110, 110, 90, 9), (190, -100, 100, 110, 9), (-240, 120, 70, 50, 4), (240, 10, 90, 60, 6),
                     (-460, -160, 120, 60, 7), (130, -380, 90, 60, 5)],
        "npcs": [
            ("moss", "Elder Moss", (60, -290), 0, [
                "Sorenda sits where the old roads cross. Every race, the racers come through. Some are running to something. Some from it.",
                "The trees here remember everyone who passes. That's not a story, dear. Put your hand on the bark by the Hollow and you'll see.",
                "We carve a notch in the longhouse post for every one of ours who goes east for the Duskara work. We haven't had to carve a homecoming in years.",
            ], {"night": (0, 200), "night_wander": 10}),
            ("harl", "Harl", (-430, 60), 20, [
                "Cut timber for the Duskara road three winters running. Good coin. Then they wanted timber for pens. Small pens. I came home.",
                "Hounds are bolder this year. Something out east has them spooked, or hungry. Keep your cards bound on the road.",
                "The Runner came through last week, fast as ever. Stopped at the Hollow, though. Stood there a long time. Didn't say why.",
            ], {"out": (6.0, 20.0)}),
            ("pell", "Pell", (-350, 230), 30, [
                "Mushrooms by the well are fine to eat. The glowing ones down in the Hollow aren't. Trust me.",
                "I found a little boot in the moss by the Hollow. Too small to be a racer's. Too far from any house to be one of ours.",
                "The Hollow gate wants a card to open. Elder Moss says it's to keep the forest's secrets. I think it's to keep us from finding them.",
            ], {"night": (100, 196), "night_wander": 16}),
            ("wren", "Wren", (-250, -260), 12, [
                "I copy the village's stories out every winter, so they don't fade. Some of them I'd rather let fade.",
                "Seven children went east last spring. I wrote their names in the book. I write a lot of names in the book.",
            ], {"out": (8.0, 19.0)}),
            ("juniper", "Juniper", (500, -160), 12, [
                "Mind the drying rack. That's feverfew, and it doesn't like being walked through.",
                "Something in the Hollow has been clawing at the roots. The whole hill smells of bear.",
            ], {"night": (520, -330), "night_wander": 30}),
        ],
        "readables": [
            ("The longhouse post", (-80, -300), [
                "A carved post by the longhouse door, covered in names. Beside each name, a notch.",
                "The oldest notches are wide and deep. The newest ones are small, low down, and there are a great many of them.",
            ]),
            ("A child's boot", (560, -420), [
                "A little leather boot, stiff with mud, caught in the moss by the gate. Too small to be a racer's.",
                "Small footprints lead from it to the cave mouth, and don't come back.",
            ]),
        ],
    },
}


def scene_nodes(scene):
    """Top-level nodes: name -> (x, y) for everything with a position."""
    out = {}
    for m in re.finditer(r'\[node name="([^"]+)"[^\]]*parent="\."[^\]]*\]\n((?:(?!\[node )[^\n]*\n)*)', scene):
        p = re.search(r'position = Vector2\((-?[\d.]+), (-?[\d.]+)\)', m.group(2))
        if p:
            out[m.group(1)] = (float(p.group(1)), float(p.group(2)))
    return out


def strip_forest(scene):
    for prefix in ("Tree", "ForestTree", "Under", "Landmark", "Read"):
        scene = re.sub(r'\[node name="%s\d+"[^\n]*\]\n(?:(?!\[node )[^\n]*\n)*' % prefix, "", scene)
    # ...and their children (a landmark's sprite and collider).
    scene = re.sub(r'\[node name="[^"]+"[^\n]*parent="Landmark\d+"[^\n]*\]\n(?:(?!\[node )[^\n]*\n)*', "", scene)
    for npc in {n for life in LIFE.values() for n, *_ in life["npcs"]}:
        scene = re.sub(r'\[node name="Npc_%s"[^\n]*\]\n(?:(?!\[node )[^\n]*\n)*' % npc, "", scene)
    for prefix in ():
        scene = re.sub(r'\[node name="%s\d+"[^\n]*\]\n(?:(?!\[node )[^\n]*\n)*' % prefix, "", scene)
    return scene


def write_tree_scene(kind):
    strip, count, fps, trunk, _ = TREES[kind]
    im = Image.open(strip)
    w, h = im.width // count, im.height
    bottom = max(im.crop((k * w, 0, (k + 1) * w, h)).getbbox()[3] for k in range(count))
    atlases = "".join(f'[sub_resource type="AtlasTexture" id="F{k}"]\natlas = ExtResource("1_strip")\nregion = Rect2({k * w}, 0, {w}, {h})\n\n'
                      for k in range(count))
    refs = ", ".join(f'{{\n"duration": 1.0,\n"texture": SubResource("F{k}")\n}}' for k in range(count))
    path = f"scenes/world/props/forest_{kind}.tscn"
    open(path, "w", encoding="utf-8", newline="\n").write(f'''[gd_scene load_steps={count + 5} format=3]

[ext_resource type="Texture2D" path="res://{strip}" id="1_strip"]
[ext_resource type="Script" path="res://scripts/world/forest_tree.gd" id="2_tree"]

{atlases}[sub_resource type="SpriteFrames" id="Frames"]
animations = [{{
"frames": [{refs}],
"loop": true,
"name": &"default",
"speed": {fps}
}}]

[sub_resource type="CircleShape2D" id="Trunk"]
radius = {trunk}.0

[node name="ForestTree" type="StaticBody2D"]
script = ExtResource("2_tree")

[node name="AnimatedSprite2D" type="AnimatedSprite2D" parent="."]
position = Vector2(0, {h / 2 - bottom + 2})
sprite_frames = SubResource("Frames")

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
position = Vector2(0, -3)
shape = SubResource("Trunk")
''')
    return "res://" + path


def paint_ground(cfg, trees, props, garden=None):
    x0, y0, x1, y1 = cfg["bounds"]
    W, H = x1 - x0, y1 - y0
    grass = np.asarray(CornerSet(GRASS).tiles[15].convert("RGBA"))
    dirt = np.asarray(CornerSet(DIRT).tiles[15].convert("RGBA"))
    tile = lambda t: np.tile(t, (H // 32 + 1, W // 32 + 1, 1))[:H, :W].astype(np.float32)
    g, d = tile(grass), tile(dirt)
    rng = np.random.default_rng(len(cfg["out"]))

    def noise(cell):
        n = (rng.random((H // cell + 3, W // cell + 3)) * 255).astype(np.uint8)
        return np.asarray(Image.fromarray(n).resize(((W // cell + 3) * cell, (H // cell + 3) * cell), Image.BICUBIC))[:H, :W] / 255.0

    # Forest floor: the meadow grass, deeper and cooler, dappled in broad soft patches.
    dapple = np.round((noise(70) * 0.6 + noise(24) * 0.4 - 0.5) * 4) / 4
    shade = (0.82 + dapple * 0.16)[..., None]
    g[..., :3] = g[..., :3] * shade * np.array([0.86, 0.9, 0.84])
    # Paths: blurred mask with a wandering edge.
    res = 4
    coarse = np.zeros((H // res, W // res), np.uint8)
    for j in range(H // res):
        for i in range(W // res):
            coarse[j, i] = 255 if on_path(cfg["paths"], x0 + i * res + 2, y0 + j * res + 2) else 0
    m = np.asarray(Image.fromarray(coarse).resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(6))) / 255.0
    on = (m + (noise(20) - 0.5) * 0.22) > 0.5
    out = np.where(on[..., None], d, g)
    near_grass = np.asarray(Image.fromarray((~on).astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(5))) > 0
    out[..., :3] = np.where((on & near_grass)[..., None], out[..., :3] * 0.8, out[..., :3])     # a rim along the path
    near_path = np.asarray(Image.fromarray(on.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(7))) > 0
    out[..., :3] = np.where((~on & near_path)[..., None], out[..., :3] * 0.88, out[..., :3])    # grass lips over it
    if garden:
        # Tilled rows of dark earth with green shoots, inside the garden fence.
        gx0, gy0, gx1, gy1 = garden
        for y in range(gy0 + 14, gy1 - 6, 12):
            for x in range(gx0 + 6, gx1 - 6):
                px, py = x - x0, y - y0
                out[py:py + 6, px, :3] = np.array([92, 62, 40])
                out[py + 1, px, :3] = np.array([112, 78, 50])
                if (x * 7 + y) % 9 == 0:
                    out[py - 2:py + 1, px, :3] = np.array([88, 150, 60])
                    out[py - 3, px, :3] = np.array([120, 180, 80])
    # Soft shadows under trees and props.
    mask = Image.new("L", (W, H), 0)
    dr = ImageDraw.Draw(mask)
    for kind, x, y in trees:
        r = TREES[kind][4]
        dr.ellipse((x - x0 - r, y - y0 - r * 0.45, x - x0 + r, y - y0 + r * 0.45 + 4), fill=150)
    for name, x, y in props:
        dr.ellipse((x - x0 - 10, y - y0 - 4, x - x0 + 10, y - y0 + 4), fill=90)
    sm = np.asarray(mask.filter(ImageFilter.GaussianBlur(6))).astype(np.float32)[..., None] / 255.0
    out[..., :3] = out[..., :3] * (1 - sm * 0.55) + np.array([16, 30, 22]) * sm * 0.55 * 0.4
    if "lake" in cfg:
        # The lake: a smooth shoreline with a band of wet, darker earth, deep water beneath
        # (the animated water layer draws over it, clipped by the saved water mask).
        yy, xx = np.mgrid[0:H, 0:W]
        cx, cy, rx, ry, island = cfg["lake"]
        px, py = xx + x0 + 0.5, yy + y0 + 0.5
        wobble = (noise(16) - 0.5) * 0.05
        e = ((px - cx) / rx) ** 2 + ((py - cy) / ry) ** 2 + wobble
        dist = np.hypot(px - cx, py - cy)
        water = (e < 1.0) & (dist >= island + wobble * 60)
        near = np.asarray(Image.fromarray(water.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(9))) > 0
        shore = near & ~water
        mud = d.copy()
        mud[..., :3] *= np.array([0.72, 0.7, 0.66])
        out = np.where(shore[..., None], mud, out)
        deep = np.array([28, 70, 78], np.float32)
        out[..., :3] = np.where(water[..., None], deep, out[..., :3])
        mask_img = np.zeros((H, W, 4), np.uint8)
        mask_img[water] = 255
        Image.fromarray(mask_img, "RGBA").save(cfg["out"].replace("_ground.png", "_water_mask.png"))
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA").save(cfg["out"])


def layout(cfg, keep, fronts=()):
    """Tree and undergrowth positions: (kind, x, y) lists."""
    x0, y0, x1, y1 = cfg["bounds"]
    rng = random.Random(cfg["scene"] + "forest")
    trees = []

    def free(x, y, gap, path_gap):
        if on_path(cfg["paths"], x, y, grow=path_gap) or near_lake(cfg, x, y, 26):
            return False
        if any((x - a) ** 2 + (y - b) ** 2 < r ** 2 for a, b, r in keep):
            return False
        # A tree just south of a building would stand in front of it and hide it.
        if any(abs(x - a) < 70 and 0 < y - b < 140 for a, b in fronts):
            return False
        return all((x - a) ** 2 + (y - b) ** 2 >= gap ** 2 for _, a, b in trees)

    # Treeline: two staggered rows inside each edge (the bottom row sits lower so the
    # canopy covers the wall; the top row at the very edge).
    for inset, step, jitter in ((14, 34, 6), (46, 40, 10)):
        for x in range(x0 + 10, x1 - 5, step):
            for y in (y0 + inset + 50, y1 - inset + 6):
                px, py = x + rng.randint(-jitter, jitter), y + rng.randint(-jitter, jitter)
                if free(px, py, 26, 26):
                    trees.append((rng.choice(["fir", "fir", "oak"]), px, py))
        for y in range(y0 + 60, y1, step):
            for x in (x0 + inset, x1 - inset):
                px, py = x + rng.randint(-jitter, jitter), y + rng.randint(-jitter, jitter)
                if free(px, py, 26, 26):
                    trees.append((rng.choice(["fir", "fir", "oak"]), px, py))
    # Groves: cluster centres, then trees gathered round them.
    centres = []
    for _ in range(400):
        cx, cy = rng.uniform(x0 + 60, x1 - 60), rng.uniform(y0 + 90, y1 - 40)
        if not on_path(cfg["paths"], cx, cy, grow=70) and all((cx - a) ** 2 + (cy - b) ** 2 > 150 ** 2 for a, b, _ in centres):
            centres.append((cx, cy, rng.choice(["fir", "fir", "oak", "mixed"])))
    for cx, cy, kind in centres:
        for _ in range(rng.randint(5, 11)):
            a, r = rng.uniform(0, math.tau), abs(rng.gauss(0, 42))
            px, py = round(cx + math.cos(a) * r * 1.3), round(cy + math.sin(a) * r)
            t = kind if kind != "mixed" else rng.choice(["fir", "oak"])
            if free(px, py, 28, 34 if t == "fir" else 58):             # oak crowns are wide
                trees.append((t, px, py))
    # Thickets: woods planted on purpose (between a village's glades), filled densely.
    for tx, ty, rx, ry, count in cfg.get("thickets", []):
        for _ in range(count * 6):
            if sum(1 for _, a, b in trees if ((a - tx) / rx) ** 2 + ((b - ty) / ry) ** 2 < 1.0) >= count:
                break
            a, r = rng.uniform(0, math.tau), math.sqrt(rng.random())
            px, py = round(tx + math.cos(a) * r * rx), round(ty + math.sin(a) * r * ry)
            t = rng.choice(["fir", "fir", "oak"])
            if free(px, py, 30, 30 if t == "fir" else 50):
                trees.append((t, px, py))
    # Undergrowth: at tree feet and along the path edges.
    props = []
    weights = [w for _, w, _ in UNDER]
    names = [n for n, _, _ in UNDER]

    def prop_free(x, y):
        return (x0 + 12 < x < x1 - 12 and y0 + 20 < y < y1 - 6 and not on_path(cfg["paths"], x, y, grow=6)
                and not near_lake(cfg, x, y, 8)
                and not any((x - a) ** 2 + (y - b) ** 2 < r ** 2 for a, b, r in keep)
                and all((x - a) ** 2 + (y - b) ** 2 >= 18 ** 2 for _, a, b in props)
                and all((x - a) ** 2 + (y - b) ** 2 >= 14 ** 2 for _, a, b in trees))
    for _, tx, ty in trees:
        if rng.random() < 0.55:
            px, py = tx + rng.choice([-1, 1]) * rng.randint(16, 26), ty + rng.randint(2, 12)
            if prop_free(px, py):
                props.append((rng.choices(names, weights)[0], px, py))
    for _ in range(900):
        px, py = rng.uniform(x0, x1), rng.uniform(y0, y1)
        if on_path(cfg["paths"], px, py, grow=26) and not on_path(cfg["paths"], px, py, grow=10) and prop_free(px, py):
            if rng.random() < 0.35:
                props.append((rng.choices(names, weights)[0], round(px), round(py)))
    # Glades: low flowers, clover and grass in small patches (a few of one kind
    # together, the way they grow), not an even sprinkle.
    low = ["flowers", "clover", "grass_clump"]
    patches = 0
    for _ in range(600):
        if patches >= 34:
            break
        cx, cy = rng.uniform(x0 + 40, x1 - 40), rng.uniform(y0 + 60, y1 - 20)
        if on_path(cfg["paths"], cx, cy, grow=20) or any((cx - a) ** 2 + (cy - b) ** 2 < 44 ** 2 for _, a, b in trees):
            continue
        patches += 1
        kind = rng.choice(low)
        for _ in range(rng.randint(2, 5)):
            px, py = round(cx + rng.gauss(0, 14)), round(cy + rng.gauss(0, 9))
            if not on_path(cfg["paths"], px, py, grow=12) and prop_free(px, py):
                props.append((kind if rng.random() < 0.8 else rng.choice(low), px, py))
    # Reeds along a lake's shore, in clumps, leaving gaps to reach the water.
    if "lake" in cfg:
        cx, cy, rx, ry, _ = cfg["lake"]
        for k in range(160):
            a = k / 160 * math.tau + rng.uniform(-0.01, 0.01)
            if math.sin(a * 5 + 1.0) < -0.2:                  # gaps between the reed beds
                continue
            grow = rng.uniform(10, 18)
            px, py = round(cx + math.cos(a) * (rx + grow)), round(cy + math.sin(a) * (ry + grow * 0.6))
            if not on_path(cfg["paths"], px, py, grow=8) and not any((px - a2) ** 2 + (py - b2) ** 2 < r2 ** 2 for a2, b2, r2 in keep) \
                    and all((px - a2) ** 2 + (py - b2) ** 2 >= 14 ** 2 for _, a2, b2 in props):
                props.append(("cattails", px, py))
    landmarks = []
    for _ in range(300):
        px, py = rng.uniform(x0 + 60, x1 - 60), rng.uniform(y0 + 90, y1 - 40)
        if (len(landmarks) < 14 and not on_path(cfg["paths"], px, py, grow=34) and prop_free(px, py)
                and all((px - a) ** 2 + (py - b) ** 2 > 90 ** 2 for _, a, b in landmarks)):
            landmarks.append((rng.choice(LANDMARKS)[0], round(px), round(py)))
    return trees, props, landmarks


def add_ext(scene, line):
    """Adds an [ext_resource] line right after the scene's last one."""
    last = [m.end() for m in re.finditer(r'\[ext_resource [^\n]*\]\n', scene)][-1]
    return scene[:last] + line + "\n" + scene[last:]


def build(zone):
    cfg = ZONES[zone] if zone in ZONES else EXTRA[zone]
    scene = strip_forest(open(cfg["scene"], encoding="utf-8").read())
    # Keep clear of everything that matters: its spot and a margin (monsters roam more).
    keep = []
    for name, (x, y) in scene_nodes(scene).items():
        if name in ("GroundTiles", "Player", "HUD", "Binder", "ShopPanel", "DialogueBox", "Walls", "Spawns",
                    "RivalSpots", "SafeZone") or name.startswith("Glow"):
            continue
        if any(k in name for k in ("Hound", "Monster")):
            margin = 90                                   # they roam
        elif any(k in name for k in ("Hut", "Longhouse", "House", "Shrine", "Well", "Merchant", "Npc")):
            margin = 76                                   # buildings keep a yard; residents room to stand
        elif name.startswith("To") or "Gate" in name:
            margin = 60                                   # exits and gates stay open to walk up to
        else:
            margin = 44
        keep.append((x, y, margin))
    for block in ("Spawns", "RivalSpots"):
        for m in re.finditer(r'\[node name="[^"]+" type="Marker2D" parent="%s"\]\nposition = Vector2\((-?[\d.]+), (-?[\d.]+)\)' % block, scene):
            keep.append((float(m.group(1)), float(m.group(2)), 50))
    life = LIFE.get(zone, {"npcs": [], "readables": []})
    for entry in life["npcs"]:
        (x, y), wander = entry[2], entry[3]
        keep.append((x, y, 40 + wander))
        hours = entry[5] if len(entry) > 5 else {}
        if hours.get("night"):
            keep.append((*hours["night"], 30 + hours.get("night_wander", 0)))
    for _, (x, y), _ in life["readables"]:
        keep.append((x, y, 30))
    for prop in life.get("props", []):
        (x, y), fp = prop[1], (prop[3] if len(prop) > 3 else (22, 8))
        keep.append((x, y, 34 + fp[0] // 2 + (40 if fp[0] >= 60 else 0)))
    keep += life.get("clear", [])
    if life.get("garden"):
        gx0, gy0, gx1, gy1 = life["garden"]
        for gx in range(gx0, gx1 + 1, 24):
            for gy in range(gy0, gy1 + 1, 24):
                keep.append((gx, gy, 30))
    fronts = [(x, y) for name, (x, y) in scene_nodes(scene).items()
              if any(k in name for k in ("Hut", "Longhouse", "House", "Shrine", "Merchant"))]
    fronts += [prop[1] for prop in life.get("props", []) if len(prop) > 3 and prop[3][0] >= 60]   # new buildings
    trees, props, landmarks = layout({**cfg, "thickets": life.get("thickets", [])}, keep, fronts)
    paint_ground(cfg, trees, props + landmarks, life.get("garden"))

    ids = {}

    def resource(scene, kind, path, new_id):
        """The id `path` already has in the scene, or add it under `new_id`."""
        m = re.search(r'\[ext_resource type="%s" path="%s" id="([^"]+)"\]' % (kind, re.escape(path)), scene)
        if m:
            return scene, m.group(1)
        return add_ext(scene, f'[ext_resource type="{kind}" path="{path}" id="{new_id}"]'), new_id

    for kind in TREES:
        scene, ids[kind] = resource(scene, "PackedScene", write_tree_scene(kind), f"80_{kind}")
    tex = {}
    for name in {n for n, _, _ in props + landmarks}:
        scene, tex[name] = resource(scene, "Texture2D", f"res://{PROPS}{name}.png", f"81_{name}")
    feet = {}

    def foot(w, h):
        key = f"Foot{w}x{h}"
        feet[key] = f'[sub_resource type="RectangleShape2D" id="{key}"]\nsize = Vector2({w}, {h})\n'
        return key
    scene = re.sub(r'\[sub_resource type="RectangleShape2D" id="Foot\d+x\d+"\]\nsize = [^\n]*\n\n', "", scene)
    if 'id="RockBase"' not in scene:
        scene = scene.replace("\n\n[node name=", '\n\n[sub_resource type="RectangleShape2D" id="RockBase"]\nsize = Vector2(22, 8)\n\n[node name=', 1)
    nodes = []
    for k, (kind, x, y) in enumerate(trees):
        nodes.append(f'[node name="ForestTree{k + 1}" parent="." instance=ExtResource("{ids[kind]}")]\nposition = Vector2({x}, {y})\n')
    for k, (name, x, y) in enumerate(props):
        h = Image.open(PROPS + name + ".png").height
        flip = "flip_h = true\n" if (x * 7 + y) % 2 else ""
        nodes.append(f'[node name="Under{k + 1}" type="Sprite2D" parent="."]\nposition = Vector2({x}, {y})\n'
                     f'offset = Vector2(0, {-h / 2 + 2})\n{flip}texture = ExtResource("{tex[name]}")\n')
    for k, (name, x, y) in enumerate(landmarks):
        h = Image.open(PROPS + name + ".png").height
        nodes.append(f'[node name="Landmark{k + 1}" type="StaticBody2D" parent="."]\nposition = Vector2({x}, {y})\n\n'
                     f'[node name="Sprite2D" type="Sprite2D" parent="Landmark{k + 1}"]\noffset = Vector2(0, {-h / 2 + 2})\n'
                     f'texture = ExtResource("{tex[name]}")\n\n'
                     f'[node name="CollisionShape2D" type="CollisionShape2D" parent="Landmark{k + 1}"]\nposition = Vector2(0, -3)\n'
                     f'shape = SubResource("RockBase")\n')
    if life["npcs"]:
        if "res://scenes/characters/npc.tscn" not in scene:
            scene = add_ext(scene, '[ext_resource type="PackedScene" path="res://scenes/characters/npc.tscn" id="82_npc"]')
        for npc_id, *_ in life["npcs"]:
            res = f"res://assets/sprites/npcs/{npc_id}/{npc_id}_frames.tres"
            if res not in scene:
                scene = add_ext(scene, f'[ext_resource type="SpriteFrames" path="{res}" id="82_{npc_id}"]')
    if life["readables"] and "res://scripts/systems/readable.gd" not in scene:
        scene = add_ext(scene, '[ext_resource type="Script" path="res://scripts/systems/readable.gd" id="82_read"]')
    npc_ref = re.search(r'path="res://scenes/characters/npc.tscn" id="([^"]+)"', scene)
    read_ref = re.search(r'path="res://scripts/systems/readable.gd" id="([^"]+)"', scene)
    quote = lambda lines: ", ".join('"' + line.replace('"', '\\"') + '"' for line in lines)
    for entry in life["npcs"]:
        npc_id, display, (x, y), wander, lines = entry[:5]
        hours = entry[5] if len(entry) > 5 else {}
        frames = re.search(r'path="res://assets/sprites/npcs/%s/%s_frames.tres" id="([^"]+)"' % (npc_id, npc_id), scene).group(1)
        nodes.append(f'[node name="Npc_{npc_id}" parent="." instance=ExtResource("{npc_ref.group(1)}")]\nposition = Vector2({x}, {y})\n'
                     f'npc_id = &"{npc_id}"\ndisplay_name = "{display}"\nsprite_frames = ExtResource("{frames}")\n'
                     f'lines = PackedStringArray({quote(lines)})\nwander_radius = {float(wander)}\n'
                     # Day and night (npc.gd): hours out here, and a night spot.
                     + (f'out_from = {float(hours["out"][0])}\nout_to = {float(hours["out"][1])}\n' if hours.get("out") else "")
                     + (f'has_night_spot = true\nnight_spot = Vector2{tuple(hours["night"])}\nnight_wander = {float(hours.get("night_wander", 0))}\n'
                        if hours.get("night") else ""))
    for k, prop in enumerate(life.get("props", [])):
        res, (x, y), collides = prop[:3]
        fw, fh = prop[3] if len(prop) > 3 else (22, 8)
        scene, tid = resource(scene, "Texture2D", res, f"85_{os.path.basename(res)[:-4]}")
        h = Image.open(res.replace("res://", "")).height
        if collides:
            nodes.append(f'[node name="Landmark{len(landmarks) + k + 1}" type="StaticBody2D" parent="."]\nposition = Vector2({x}, {y})\n\n'
                         f'[node name="Sprite2D" type="Sprite2D" parent="Landmark{len(landmarks) + k + 1}"]\noffset = Vector2(0, {-h / 2 + 2})\n'
                         f'texture = ExtResource("{tid}")\n\n'
                         f'[node name="CollisionShape2D" type="CollisionShape2D" parent="Landmark{len(landmarks) + k + 1}"]\n'
                         f'position = Vector2(0, {-fh / 2})\nshape = SubResource("{foot(fw, fh)}")\n')
        else:
            nodes.append(f'[node name="Under{len(props) + k + 1}" type="Sprite2D" parent="."]\nposition = Vector2({x}, {y})\n'
                         f'offset = Vector2(0, {-h / 2 + 2})\ntexture = ExtResource("{tid}")\n')
    for k, (title, (x, y), lines) in enumerate(life["readables"]):
        nodes.append(f'[node name="Read{k + 1}" type="Node2D" parent="."]\nposition = Vector2({x}, {y})\n'
                     f'script = ExtResource("{read_ref.group(1)}")\ntitle = "{title}"\nlines = PackedStringArray({quote(lines)})\n')
    if "lake" in cfg:
        # The lake's water: the forest lake's animated tile (make_forest_water.py, the
        # same calm teal as Thornveil's lake), clipped to the lake.
        scene = re.sub(r'\[node name="LakeWater"[^\n]*\]\n(?:(?!\[node )[^\n]*\n)*', "", scene)
        scene = re.sub(r'\[node name="Waves"[^\n]*parent="LakeWater"[^\n]*\]\n(?:(?!\[node )[^\n]*\n)*', "", scene)
        scene = re.sub(r'\[ext_resource [^\n]*id="84_waves"\]\n', "", scene)
        mask_res = "res://" + cfg["out"].replace("_ground.png", "_water_mask.png")
        for line in (f'[ext_resource type="Texture2D" path="{mask_res}" id="84_lakemask"]',
                     '[ext_resource type="Script" path="res://scripts/world/tiled_animation.gd" id="84_tiled"]',
                     '[ext_resource type="Texture2D" path="res://assets/sprites/tiles/thornveil/water/lake.png" id="84_waves"]'):
            if line.split('path="')[1].split('"')[0] not in scene:
                scene = add_ext(scene, line)
        x0, y0, x1, y1 = cfg["bounds"]
        nodes.append(f'[node name="LakeWater" type="Sprite2D" parent="."]\nz_index = -9\nclip_children = 1\n'
                     f'position = Vector2({(x0 + x1) / 2}, {(y0 + y1) / 2})\ntexture = ExtResource("84_lakemask")\n\n'
                     f'[node name="Waves" type="Sprite2D" parent="LakeWater"]\n'
                     f'script = ExtResource("84_tiled")\nstrip = ExtResource("84_waves")\nframe_count = 8\nfps = 3.0\n'
                     f'region_rect = Rect2(0, 0, {x1 - x0}, {y1 - y0})\n')
    if feet:
        scene = scene.replace("\n\n[node name=", "\n\n" + "\n".join(feet.values()) + "\n[node name=", 1)
    # Butterflies over the village green and glades.
    scene = re.sub(r'\[node name="(?:Butterflies|Fireflies)\d+"[^\n]*\]\n(?:(?!\[node )[^\n]*\n)*', "", scene)
    if life.get("butterflies"):
        scene, bid = resource(scene, "Script", "res://scripts/world/butterflies.gd", "86_butterflies")
        for k, ((x, y), count) in enumerate(life["butterflies"]):
            nodes.append(f'[node name="Butterflies{k + 1}" type="Node2D" parent="."]\nposition = Vector2({x}, {y})\n'
                         f'script = ExtResource("{bid}")\ncount = {count}\nseed = {k + 2}\n')
        scene, fid = resource(scene, "Script", "res://scripts/world/fireflies.gd", "86_fireflies")
        for k, ((x, y), count) in enumerate(life["butterflies"]):
            nodes.append(f'[node name="Fireflies{k + 1}" type="Node2D" parent="."]\nposition = Vector2({x}, {y})\n'
                         f'script = ExtResource("{fid}")\ncount = {count * 3}\nseed = {k + 7}\n')
    at = scene.index('[node name="Player"')
    scene = scene[:at] + "\n".join(nodes) + "\n" + scene[at:]
    open(cfg["scene"], "w", encoding="utf-8", newline="\n").write(scene)
    print(f"{zone}: {len(trees)} trees, {len(props)} undergrowth, {len(landmarks)} landmarks")


if __name__ == "__main__":
    for zone in sys.argv[1:] or FORESTS:
        build(zone)
