"""Multilevel terrain from PixelLab cliff Wang tilesets.

A zone is described as a heightmap of *levels* sampled at tile corners
(0 = lowest, e.g. sea). Each pair of adjacent levels (k, k+1) has its own
cliff tileset (transition_size 1.0: 25 tiles, walls on south-facing edges).
A cell whose corners span levels k and k+1 is drawn from that pair's set,
picking the tile whose pattern_4x4 best matches the surrounding corners
(PixelLab's documented scoring). Cells must never span more than two
adjacent levels, and every plateau needs a row of lower ground south of it
for its wall.

compose() returns the ground image plus, per cell, the level you stand on
(-1 where the cell is a cliff/edge you can't walk), which build scripts turn
into collision and a level map the game reads at runtime.
"""
import json

from PIL import Image

CENTER = {(1, 1), (1, 2), (2, 1), (2, 2)}


class CliffSet:
    def __init__(self, prefix: str):
        meta = json.load(open(prefix + "_metadata.json"))
        sheet = Image.open(prefix + "_image.png").convert("RGBA")
        self.tiles = []
        for t in meta["tileset_data"]["tiles"]:
            b = t["bounding_box"]
            p = t["pattern_4x4"]
            self.tiles.append({
                "image": sheet.crop((b["x"], b["y"], b["x"] + b["width"], b["y"] + b["height"])),
                "pattern": [p["row_0"], p["row_1"], p["row_2"], p["row_3"]],
            })

    def pick(self, around):
        """around: 4x4 vertex values (0 lower, 1 upper, 2 wall, None outside the map)."""
        best, best_score = None, -10 ** 9
        for tile in self.tiles:
            score = 0
            for i in range(4):
                for j in range(4):
                    want, have = tile["pattern"][i][j], around[i][j]
                    if want == 255 or have is None:
                        continue
                    center = (i, j) in CENTER
                    if have == want:
                        score += 10 if center else 1
                    else:
                        score -= 30 if center else 1
            if score > best_score:
                best, best_score = tile, score
        return best["image"]


def compose(levels, sets, tile=32, extra_wall_rows=0):
    """levels: (rows+1) x (cols+1) corner levels. sets: {k: CliffSet for (k, k+1)}.
    extra_wall_rows makes every cliff that many rows taller: the wall's cap moves
    up onto the plateau and the gap is filled with wall body (the top half of the
    plain wall tile under the cap, repeated), so plateaus need that much extra depth.
    Returns (image, stand) where stand[r][c] is the walkable level of the cell or -1."""
    rows, cols = len(levels) - 1, len(levels[0]) - 1
    img = Image.new("RGBA", (cols * tile, rows * tile))
    stand = [[-1] * cols for _ in range(rows)]
    lips = []  # (r, c, cap tile image): cells holding a wall's top edge

    def lv(r, c):
        if 0 <= r <= rows and 0 <= c <= cols:
            return levels[r][c]
        return None

    for r in range(rows):
        for c in range(cols):
            corners = [levels[r][c], levels[r][c + 1], levels[r + 1][c], levels[r + 1][c + 1]]
            lo, hi = min(corners), max(corners)
            above = [a for a in (lv(r - 1, c), lv(r - 1, c + 1)) if a is not None]
            if hi > lo or any(a > lo for a in above):
                # An edge cell, or a flat cell with a plateau right above it (the
                # wall hangs one row below a plateau's south edge): the (lo, lo+1) set.
                pair = lo
            else:
                # Plain flat ground: draw it as the lower side of its own pair, or
                # as the upper side of the pair below for the topmost level.
                pair = lo if lo in sets else lo - 1
            around = []
            for i in range(4):
                row = []
                for j in range(4):
                    v = lv(r - 1 + i, c - 1 + j)
                    if v is None:
                        row.append(None)
                        continue
                    north = lv(r - 2 + i, c - 1 + j)
                    if v <= pair and north is not None and north > pair:
                        row.append(2)          # lower corner directly south of the plateau: wall
                    else:
                        row.append(1 if v > pair else 0)
                around.append(row)
            chosen = sets[pair].pick(around)
            img.paste(chosen, (c * tile, r * tile))
            walled = any(around[i][j] == 2 for i, j in CENTER)
            if lo == hi and not walled:
                stand[r][c] = lo
            if 1 in around[1][1:3] and 2 in around[2][1:3]:
                lips.append((r, c, chosen))

    if extra_wall_rows:
        # Raise each wall: cap up by N rows, wall body in between.
        for r, c, cap in lips:
            if r - extra_wall_rows < 0:
                continue
            body = img.crop((c * tile, (r + 1) * tile, (c + 1) * tile, (r + 1) * tile + tile // 2))
            for k in range(1, extra_wall_rows + 1):
                img.paste(body, (c * tile, (r - k + 1) * tile))
                img.paste(body, (c * tile, (r - k + 1) * tile + tile // 2))
                stand[r - k][c] = -1
            img.paste(cap, (c * tile, (r - extra_wall_rows) * tile))
    return img, stand


def merge_rects(mask, left, top, tile=32):
    """Row runs of True cells merged vertically into rectangles (x0, y0, x1, y1)."""
    rows, cols = len(mask), len(mask[0])
    runs = {}
    rects = []
    for r in range(rows):
        c = 0
        row_runs = {}
        while c < cols:
            if not mask[r][c]:
                c += 1
                continue
            s = c
            while c < cols and mask[r][c]:
                c += 1
            row_runs[(s, c)] = runs.pop((s, c), r)
        for (s, e), r0 in runs.items():
            rects.append((left + s * tile, top + r0 * tile, left + e * tile, top + r * tile))
        runs = row_runs
    for (s, e), r0 in runs.items():
        rects.append((left + s * tile, top + r0 * tile, left + e * tile, top + rows * tile))
    return rects
