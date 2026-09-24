"""Paint zone ground from a PixelLab Wang tileset (two terrains: path = lower,
floor = upper) and wire it into the zone scene.

Usage: python scripts/tools/build_ground.py [zone ...]   (default: all zones below)

For each zone this:
- samples the terrain at every tile corner (path where any path shape covers it),
- assembles the matching Wang tiles into assets/sprites/tiles/<biome>/<zone>_ground.png,
- replaces the scene's flat ColorRect/Polygon2D ground pieces with one Sprite2D,
- removes placeholder trees that now stand on a path,
- scatters extra forest trees (named ForestTree*, replaced on every run) on open
  floor, clear of paths and every node already placed.

The Thornveil palette is darker than the raw tileset, so the ground image is
colour-graded by BIOME_GRADE (shared with build_lake_veyra.py).

Shapes (local coords): ("line", points, width), ("ellipse", cx, cy, rx, ry),
("rect", x0, y0, x1, y1). Edit the layouts here, then re-run.
"""
import json
import math
import os
import random
import re
import sys

from PIL import Image

os.chdir(os.path.join(os.path.dirname(__file__), "..", ".."))

TILE = 32
TILESET = "assets/sprites/tiles/thornveil/wang/forest_path"
## Multiplies the tileset's bright lawn green down to Thornveil's forest palette.
BIOME_GRADE = (0.62, 0.74, 0.58)
TREE_SCENE = "res://scenes/world/props/tree.tscn"

ZONES = {
    "thornveil": {
        "scene": "scenes/world/thornveil.tscn",
        "out": "assets/sprites/tiles/thornveil/thornveil_ground.png",
        "bounds": (-576, -864, 576, 160),
        "remove": ["Ground", "Path", "NorthPath", "EastPath", "WestPath"],
        "extra_trees": 70,
        "paths": [
            ("line", [(0, 170), (0, -880)], 44),        # Kalmora <-> Sorenda trunk road
            ("line", [(0, -250), (-600, -250)], 40),    # west to Lake Veyra
            ("line", [(0, -400), (600, -400)], 40),     # east to Warden's Grove
            ("ellipse", 0, -250, 70, 46),               # crossroads
        ],
    },
    "sorenda": {
        "scene": "scenes/world/sorenda.tscn",
        "out": "assets/sprites/tiles/thornveil/sorenda_ground.png",
        "bounds": (-480, -448, 480, 224),
        "remove": ["Ground", "Clearing", "Path", "GroveFloor"],
        "extra_trees": 20,
        "paths": [
            ("ellipse", 0, -40, 190, 120),              # village green
            ("line", [(0, -20), (0, 240)], 44),         # south road
            ("line", [(120, -110), (395, -290)], 32),   # to the Hollow
            ("rect", 345, -410, 440, -310),             # the Hollow grove
        ],
    },
    "wardens_grove": {
        "scene": "scenes/world/wardens_grove.tscn",
        "out": "assets/sprites/tiles/thornveil/wardens_grove_ground.png",
        "bounds": (-544, -384, 512, 384),
        "remove": ["Ground", "Clearing", "Path", "SanctumFloor"],
        "extra_trees": 0,
        "paths": [
            ("line", [(-560, 0), (-120, 0)], 44),       # entrance trail
            ("ellipse", 60, 0, 160, 115),               # the Warden's trampled arena
            ("rect", 380, -152, 500, 152),              # sanctum floor
        ],
    },
}


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy or 1)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def on_path(shapes, x, y, grow=0.0):
    for s in shapes:
        if s[0] == "line":
            pts, width = s[1], s[2]
            if any(seg_dist(x, y, *pts[i], *pts[i + 1]) <= width / 2 + grow for i in range(len(pts) - 1)):
                return True
        elif s[0] == "ellipse":
            _, cx, cy, rx, ry = s
            if ((x - cx) / (rx + grow)) ** 2 + ((y - cy) / (ry + grow)) ** 2 <= 1.0:
                return True
        elif s[0] == "rect":
            _, x0, y0, x1, y1 = s
            if x0 - grow <= x <= x1 + grow and y0 - grow <= y <= y1 + grow:
                return True
    return False


def grade(img: Image.Image) -> Image.Image:
    r, g, b, a = img.split()
    r = r.point(lambda v: int(v * BIOME_GRADE[0]))
    g = g.point(lambda v: int(v * BIOME_GRADE[1]))
    b = b.point(lambda v: int(v * BIOME_GRADE[2]))
    return Image.merge("RGBA", (r, g, b, a))


def load_tiles():
    meta = json.load(open(TILESET + "_metadata.json"))
    sheet = Image.open(TILESET + "_image.png").convert("RGBA")
    tiles = {}
    for t in meta["tileset_data"]["tiles"]:
        c = t["corners"]
        idx = (c["NW"] == "upper") * 8 + (c["NE"] == "upper") * 4 + (c["SW"] == "upper") * 2 + (c["SE"] == "upper")
        b = t["bounding_box"]
        tiles[idx] = sheet.crop((b["x"], b["y"], b["x"] + b["width"], b["y"] + b["height"]))
    return tiles


def remove_node(scene: str, name: str) -> str:
    # A node block runs from its header to the next header (or end of file).
    return re.sub(r'\[node name="%s" [^\n]*\]\n(?:(?!\[node )[^\n]*\n)*' % re.escape(name), "", scene)


def build(zone: str, tiles) -> None:
    cfg = ZONES[zone]
    x0, y0, x1, y1 = cfg["bounds"]
    cols, rows = (x1 - x0) // TILE, (y1 - y0) // TILE
    floor = [[not on_path(cfg["paths"], x0 + i * TILE, y0 + j * TILE) for i in range(cols + 1)] for j in range(rows + 1)]
    img = Image.new("RGBA", (cols * TILE, rows * TILE))
    for j in range(rows):
        for i in range(cols):
            idx = floor[j][i] * 8 + floor[j][i + 1] * 4 + floor[j + 1][i] * 2 + floor[j + 1][i + 1]
            img.paste(tiles[idx], (i * TILE, j * TILE))
    os.makedirs(os.path.dirname(cfg["out"]), exist_ok=True)
    grade(img).save(cfg["out"])

    scene = open(cfg["scene"], encoding="utf-8").read()
    for name in cfg["remove"]:
        scene = remove_node(scene, name)
    res = "res://" + cfg["out"]
    if res not in scene:
        scene = scene.replace("\n\n[sub_resource", f'\n[ext_resource type="Texture2D" path="{res}" id="90_ground"]\n\n[sub_resource', 1)
    scene = remove_node(scene, "GroundTiles")
    # First node after the root: the ground sprite, centred on the painted area.
    root_end = scene.index("\n\n", scene.index('[node name="') ) + 2
    scene = (scene[:root_end] + '[node name="GroundTiles" type="Sprite2D" parent="."]\nz_index = -10\n'
             f'position = Vector2({(x0 + x1) / 2}, {(y0 + y1) / 2})\ntexture = ExtResource("90_ground")\n\n' + scene[root_end:])

    removed = []
    def drop_tree(m):
        x, y = float(m.group(2)), float(m.group(3))
        if on_path(cfg["paths"], x, y, grow=14):
            removed.append(m.group(1))
            return ""
        return m.group(0)
    scene = re.sub(r'\[node name="(Tree\d+)" parent="\." instance=ExtResource\("[^"]+"\)\]\nposition = Vector2\((-?[\d.]+), (-?[\d.]+)\)\n(?:(?!\[node )[^\n]*\n)*',
                   drop_tree, scene)
    scene = _scatter_trees(scene, cfg)
    open(cfg["scene"], "w", encoding="utf-8", newline="\n").write(scene)
    print(f"{zone}: {cols}x{rows} tiles, removed trees on paths: {removed}")


def _scatter_trees(scene: str, cfg: dict) -> str:
    scene = remove_node_prefix(scene, "ForestTree")
    count = cfg.get("extra_trees", 0)
    m = re.search(r'\[ext_resource type="PackedScene" path="%s" id="([^"]+)"\]' % re.escape(TREE_SCENE), scene)
    if count == 0 or m is None:
        return scene
    tree_id = m.group(1)
    taken = [(float(a), float(b)) for a, b in re.findall(r'position = Vector2\((-?[\d.]+), (-?[\d.]+)\)', scene)]
    x0, y0, x1, y1 = cfg["bounds"]
    rng = random.Random(cfg["scene"])  # Same trees on every run.
    placed = []
    tries = 0
    while len(placed) < count and tries < count * 200:
        tries += 1
        x, y = rng.randint(x0 + 40, x1 - 40), rng.randint(y0 + 60, y1 - 30)
        if on_path(cfg["paths"], x, y, grow=30):
            continue
        if any((x - a) ** 2 + (y - b) ** 2 < 46 ** 2 for a, b in taken + placed):
            continue
        placed.append((x, y))
    nodes = "".join(f'[node name="ForestTree{k + 1}" parent="." instance=ExtResource("{tree_id}")]\n'
                    f'position = Vector2({x}, {y})\n\n' for k, (x, y) in enumerate(placed))
    at = scene.index('[node name="Player"')  # Keep the Player and UI nodes last.
    return scene[:at] + nodes + scene[at:]


def remove_node_prefix(scene: str, prefix: str) -> str:
    return re.sub(r'\[node name="%s\d+" [^\n]*\]\n(?:(?!\[node )[^\n]*\n)*' % re.escape(prefix), "", scene)


if __name__ == "__main__":
    tiles = load_tiles()
    for zone in sys.argv[1:] or ZONES:
        build(zone, tiles)
