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
FORESTS = ["thornveil"]


def scene_nodes(scene):
    """Top-level nodes: name -> (x, y) for everything with a position."""
    out = {}
    for m in re.finditer(r'\[node name="([^"]+)"[^\]]*parent="\."[^\]]*\]\n((?:(?!\[node )[^\n]*\n)*)', scene):
        p = re.search(r'position = Vector2\((-?[\d.]+), (-?[\d.]+)\)', m.group(2))
        if p:
            out[m.group(1)] = (float(p.group(1)), float(p.group(2)))
    return out


def strip_forest(scene):
    for prefix in ("Tree", "ForestTree", "Under", "Landmark"):
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


def paint_ground(cfg, trees, props):
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
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA").save(cfg["out"])


def layout(cfg, keep):
    """Tree and undergrowth positions: (kind, x, y) lists."""
    x0, y0, x1, y1 = cfg["bounds"]
    rng = random.Random(cfg["scene"] + "forest")
    trees = []

    def free(x, y, gap, path_gap):
        if on_path(cfg["paths"], x, y, grow=path_gap):
            return False
        if any((x - a) ** 2 + (y - b) ** 2 < r ** 2 for a, b, r in keep):
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
    # Undergrowth: at tree feet and along the path edges.
    props = []
    weights = [w for _, w, _ in UNDER]
    names = [n for n, _, _ in UNDER]

    def prop_free(x, y):
        return (x0 + 12 < x < x1 - 12 and y0 + 20 < y < y1 - 6 and not on_path(cfg["paths"], x, y, grow=6)
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
    landmarks = []
    for _ in range(300):
        px, py = rng.uniform(x0 + 60, x1 - 60), rng.uniform(y0 + 90, y1 - 40)
        if (len(landmarks) < 14 and not on_path(cfg["paths"], px, py, grow=34) and prop_free(px, py)
                and all((px - a) ** 2 + (py - b) ** 2 > 90 ** 2 for _, a, b in landmarks)):
            landmarks.append((rng.choice(LANDMARKS)[0], round(px), round(py)))
    return trees, props, landmarks


def build(zone):
    cfg = ZONES[zone]
    scene = strip_forest(open(cfg["scene"], encoding="utf-8").read())
    # Keep clear of everything that matters: its spot and a margin (monsters roam more).
    keep = []
    for name, (x, y) in scene_nodes(scene).items():
        if name in ("GroundTiles", "Player", "HUD", "Binder", "ShopPanel", "DialogueBox", "Walls", "Spawns",
                    "RivalSpots", "SafeZone") or name.startswith("Glow"):
            continue
        keep.append((x, y, 90 if "Hound" in name or "Monster" in name else 44))
    for block in ("Spawns", "RivalSpots"):
        for m in re.finditer(r'\[node name="[^"]+" type="Marker2D" parent="%s"\]\nposition = Vector2\((-?[\d.]+), (-?[\d.]+)\)' % block, scene):
            keep.append((float(m.group(1)), float(m.group(2)), 50))
    trees, props, landmarks = layout(cfg, keep)
    paint_ground(cfg, trees, props + landmarks)

    ids = {}
    for kind in TREES:
        res = write_tree_scene(kind)
        ids[kind] = f"80_{kind}"
        if res not in scene:
            scene = scene.replace("\n\n[sub_resource", f'\n[ext_resource type="PackedScene" path="{res}" id="80_{kind}"]\n\n[sub_resource', 1)
    for name in {n for n, _, _ in props + landmarks}:
        res = f"res://{PROPS}{name}.png"
        if res not in scene:
            scene = scene.replace("\n\n[sub_resource", f'\n[ext_resource type="Texture2D" path="{res}" id="81_{name}"]\n\n[sub_resource', 1)
    if 'id="RockBase"' not in scene:
        scene = scene.replace("\n\n[node name=", '\n\n[sub_resource type="RectangleShape2D" id="RockBase"]\nsize = Vector2(22, 8)\n\n[node name=', 1)
    nodes = []
    for k, (kind, x, y) in enumerate(trees):
        nodes.append(f'[node name="ForestTree{k + 1}" parent="." instance=ExtResource("{ids[kind]}")]\nposition = Vector2({x}, {y})\n')
    for k, (name, x, y) in enumerate(props):
        h = Image.open(PROPS + name + ".png").height
        flip = "flip_h = true\n" if (x * 7 + y) % 2 else ""
        nodes.append(f'[node name="Under{k + 1}" type="Sprite2D" parent="."]\nposition = Vector2({x}, {y})\n'
                     f'offset = Vector2(0, {-h / 2 + 2})\n{flip}texture = ExtResource("81_{name}")\n')
    for k, (name, x, y) in enumerate(landmarks):
        h = Image.open(PROPS + name + ".png").height
        nodes.append(f'[node name="Landmark{k + 1}" type="StaticBody2D" parent="."]\nposition = Vector2({x}, {y})\n\n'
                     f'[node name="Sprite2D" type="Sprite2D" parent="Landmark{k + 1}"]\noffset = Vector2(0, {-h / 2 + 2})\n'
                     f'texture = ExtResource("81_{name}")\n\n'
                     f'[node name="CollisionShape2D" type="CollisionShape2D" parent="Landmark{k + 1}"]\nposition = Vector2(0, -3)\n'
                     f'shape = SubResource("RockBase")\n')
    at = scene.index('[node name="Player"')
    scene = scene[:at] + "\n".join(nodes) + "\n" + scene[at:]
    # The ground sprite stays; make sure it has y-sort for trees to overlap properly.
    open(cfg["scene"], "w", encoding="utf-8", newline="\n").write(scene)
    print(f"{zone}: {len(trees)} trees, {len(props)} undergrowth, {len(landmarks)} landmarks")


if __name__ == "__main__":
    for zone in sys.argv[1:] or FORESTS:
        build(zone)
