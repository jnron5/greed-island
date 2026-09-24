"""Kalmora art pass: coastal ground from two chained PixelLab Wang tilesets
(sea -> sand, sand -> cobbles) plus Mediterranean buildings and decor.

Usage: python scripts/tools/build_kalmora.py
Writes assets/sprites/tiles/kalmora/kalmora_ground.png and updates
scenes/world/kalmora.tscn: replaces the flat ColorRect ground, swaps the drawn
fountain/dock for sprites, and (re)places the House*/Decor* nodes. Candidate
spots are skipped if they'd crowd anything already placed (pickups, gates,
spawn and rival markers, dummies, the merchant, the lighthouse yard).
"""
import json
import os
import re

from PIL import Image

os.chdir(os.path.join(os.path.dirname(__file__), "..", ".."))

from build_ground import remove_node, remove_node_prefix  # noqa: E402

TILE = 32
BOUNDS = (-416, -384, 416, 320)
COAST = "assets/sprites/tiles/kalmora/wang/coast"   # lower = sea, upper = sand
TOWN = "assets/sprites/tiles/kalmora/wang/town"     # lower = sand, upper = cobbles
OUT = "assets/sprites/tiles/kalmora/kalmora_ground.png"
SCENE = "scenes/world/kalmora.tscn"

SEA, SAND, COBBLE = 0, 1, 2
SEA_TOP = 205          # the sea wall runs along y ~205..245
TOWN_RECT = (-300, -262, 300, 172)

# (name, prop scene, footprint-bottom position). Skipped if too close to something.
BUILDINGS = [
    ("HouseTall1", "kalmora_townhouse", (-150, -150)),
    ("HouseTall2", "kalmora_townhouse", (165, -195)),
    ("Cottage1", "kalmora_cottage", (-300, -10)),
    ("Cottage2", "kalmora_cottage", (95, -250)),
    ("Tavern", "kalmora_tavern", (255, 125)),
]
DECOR = [
    ("Cypress", "kalmora_cypress", [(-110, -250), (-205, -240), (230, -120), (-360, -200), (-10, 175), (40, -250)]),
    ("Olive", "kalmora_olive", [(-330, 110), (-380, -120), (360, 20), (-250, 170), (140, 175), (-120, 40)]),
]
CLEARANCE = 44
KEEP_OUT = [(285, -262, 385, -105), (175, 165, 225, 300)]  # lighthouse yard, pier


def load(prefix):
    meta = json.load(open(prefix + "_metadata.json"))
    sheet = Image.open(prefix + "_image.png").convert("RGBA")
    tiles = {}
    for t in meta["tileset_data"]["tiles"]:
        c = t["corners"]
        idx = (c["NW"] == "upper") * 8 + (c["NE"] == "upper") * 4 + (c["SW"] == "upper") * 2 + (c["SE"] == "upper")
        b = t["bounding_box"]
        tiles[idx] = sheet.crop((b["x"], b["y"], b["x"] + b["width"], b["y"] + b["height"]))
    return tiles


def terrain(x, y):
    if y >= SEA_TOP:
        return SEA
    x0, y0, x1, y1 = TOWN_RECT
    return COBBLE if x0 <= x <= x1 and y0 <= y <= y1 else SAND


def build_ground():
    coast, town = load(COAST), load(TOWN)
    x0, y0, x1, y1 = BOUNDS
    cols, rows = (x1 - x0) // TILE, (y1 - y0) // TILE
    t = [[terrain(x0 + i * TILE, y0 + j * TILE) for i in range(cols + 1)] for j in range(rows + 1)]
    img = Image.new("RGBA", (cols * TILE, rows * TILE))
    for j in range(rows):
        for i in range(cols):
            c = [t[j][i], t[j][i + 1], t[j + 1][i], t[j + 1][i + 1]]
            if min(c) >= SAND:   # sand/cobble cell: town tileset (sand lower, cobble upper)
                bits, tiles = [v == COBBLE for v in c], town
            else:                 # sea/sand cell (a stray cobble counts as sand here)
                bits, tiles = [v != SEA for v in c], coast
            img.paste(tiles[bits[0] * 8 + bits[1] * 4 + bits[2] * 2 + bits[3]], (i * TILE, j * TILE))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.save(OUT)
    return cols, rows


def ext(scene, path, rid, kind="PackedScene"):
    if f'path="{path}"' in scene:
        return re.search(r'path="%s" id="([^"]+)"' % re.escape(path), scene).group(1), scene
    line = f'[ext_resource type="{kind}" path="{path}" id="{rid}"]\n'
    at = scene.index("\n[sub_resource")
    return rid, scene[:at] + "\n" + line.rstrip("\n") + scene[at:]


def main():
    cols, rows = build_ground()
    scene = open(SCENE, encoding="utf-8").read()
    for name in ["Ground", "NorthPath", "TownPaving", "Plaza", "Sea", "Dock", "GroundTiles", "PierSprite"]:
        scene = remove_node(scene, name)
    # Drawn fountain -> sprite prop (drop its children too).
    scene = re.sub(r'\[node name="[^"]+" [^\n]*parent="Fountain"[^\n]*\]\n(?:(?!\[node )[^\n]*\n)*', "", scene)
    scene = remove_node(scene, "Fountain")
    for prefix in ["House", "Cottage", "Tavern", "Cypress", "Olive"]:
        scene = re.sub(r'\[node name="%s\d*" [^\n]*\]\n(?:(?!\[node )[^\n]*\n)*' % prefix, "", scene)

    ground_id, scene = ext(scene, "res://" + OUT, "80_ground", "Texture2D")
    pier_id, scene = ext(scene, "res://assets/sprites/tiles/kalmora/pier.png", "81_pier", "Texture2D")
    fountain_id, scene = ext(scene, "res://scenes/world/props/kalmora_fountain.tscn", "82_fountain")
    stall_id, scene = ext(scene, "res://assets/sprites/tiles/kalmora/market_stall.png", "83_stall", "Texture2D")

    x0, y0, x1, y1 = BOUNDS
    root_end = scene.index("\n\n", scene.index('[node name="')) + 2
    scene = (scene[:root_end]
             + f'[node name="GroundTiles" type="Sprite2D" parent="."]\nz_index = -10\n'
               f'position = Vector2({(x0 + x1) / 2}, {(y0 + y1) / 2})\ntexture = ExtResource("{ground_id}")\n\n'
             + f'[node name="PierSprite" type="Sprite2D" parent="."]\nz_index = -8\nposition = Vector2(200, 232)\n'
               f'texture = ExtResource("{pier_id}")\n\n'
             + f'[node name="Fountain" parent="." instance=ExtResource("{fountain_id}")]\nposition = Vector2(0, -8)\n\n'
             + scene[root_end:])
    if "stall_texture" not in scene:
        scene = scene.replace('[node name="Merchant" parent="." instance=ExtResource("7_merchant")]\n',
                              f'[node name="Merchant" parent="." instance=ExtResource("7_merchant")]\nstall_texture = ExtResource("{stall_id}")\n')

    taken = [(float(a), float(b)) for a, b in re.findall(r'position = Vector2\((-?[\d.]+), (-?[\d.]+)\)', scene)]
    def free(x, y, r=CLEARANCE):
        if any(ax0 - 20 <= x <= ax1 + 20 and ay0 - 20 <= y <= ay1 + 20 for ax0, ay0, ax1, ay1 in KEEP_OUT):
            return False
        return all((x - a) ** 2 + (y - b) ** 2 >= r * r for a, b in taken)

    nodes, skipped = [], []
    for name, prop, (x, y) in BUILDINGS:
        if not free(x, y, 60):
            skipped.append(name)
            continue
        rid, scene = ext(scene, f"res://scenes/world/props/{prop}.tscn", f"84_{prop}")
        nodes.append(f'[node name="{name}" parent="." instance=ExtResource("{rid}")]\nposition = Vector2({x}, {y})\n\n')
        taken.append((x, y))
    for prefix, prop, spots in DECOR:
        rid, scene = ext(scene, f"res://scenes/world/props/{prop}.tscn", f"85_{prop}")
        for k, (x, y) in enumerate(spots):
            if not free(x, y):
                skipped.append(f"{prefix}{k + 1}")
                continue
            nodes.append(f'[node name="{prefix}{k + 1}" parent="." instance=ExtResource("{rid}")]\nposition = Vector2({x}, {y})\n\n')
            taken.append((x, y))
    at = scene.index('[node name="Player"')
    scene = scene[:at] + "".join(nodes) + scene[at:]
    open(SCENE, "w", encoding="utf-8", newline="\n").write(scene)
    print(f"kalmora: {cols}x{rows} tiles, {len(nodes)} props placed, skipped (crowded): {skipped}")


if __name__ == "__main__":
    main()
