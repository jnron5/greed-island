"""Builds the open regions past Kalmora's west gate: the Aurewind Plains, Verdana,
Lake Serin and the Starfall Range. Each zone's layout is a dict in
scripts/tools/region_layouts.py; this script turns one into a complete scene.

Usage: python scripts/tools/build_region.py [zone ...]   (default: all of them)

What a layout gives, and what becomes of it (all positions are zone-local px):
- level(x, y) -> int: the corner heightmap. terrain.compose() draws it with the
  zone's PixelLab cliff set (a plateau's wall hangs below its south edge), and every
  cell you can't stand on becomes collision you can see (cliff faces).
- stairs: stone flights cut into south-facing walls (Kalmora's stairs, stretched).
- grade: the whole ground is colour-graded into the biome's palette, then dappled with
  broad soft light so the tiles never read as a grid.
- paths: dirt (or trodden snow) blended per pixel: rounded, ragged edges, a soft rim.
- fields: golden wheat painted per pixel from the wheat tileset, with a darker rim.
- lakes/land: water painted per pixel (ellipses, minus land ellipses such as a
  peninsula), a wet shore band, the forest lake's animated water clipped to it, and
  collision that follows the water pixels. docks: plank decks over the water.
- ice: frozen, walkable water (pale, cracked).
- buildings (front-facing PixelLab sprites; footprint collision; a door into an interior
  and window glow at night), props (with footprints you can see), stones, lanterns,
  campfires, residents, readables, chests (per collector), monsters, exits, spawns.
- Trees: a double treeline just inside the map's edges (the zone's walls are trees you
  can see), groves in the open ground, never on a path, water or anything that matters.
- Undergrowth and soft shadows under everything, baked into the ground.
The build fails if anything that matters can't be reached on foot from the entry.
Edit the layouts in region_layouts.py, not the editor.
"""
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
from scipy import ndimage

os.chdir(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, "scripts/tools")
from terrain import CliffSet, CornerSet, compose, mask_rects, merge_rects  # noqa: E402
import region_layouts as RL  # noqa: E402

TILE = 32
FOREST = "assets/sprites/tiles/forest/"
DIRT = "assets/sprites/tiles/kalmora2/wang/dirt"
PLANKS = "assets/sprites/tiles/kalmora2/wang/planks"
WHEAT = "assets/sprites/tiles/aurewind/wang/wheat"
PAVING = "assets/sprites/tiles/kalmora2/cliff/town_upper"
STAIRS_SRC = "assets/sprites/tiles/kalmora2/objects/stairs.png"
CHEST_SHUT = "assets/sprites/tiles/thornveil/props/chest.png"
CHEST_OPEN = "assets/sprites/tiles/thornveil/props/chest_open.png"
LANTERN_PNG = "assets/sprites/tiles/thornveil/props/trail_lantern.png"
CAMPFIRE_STRIP = "assets/sprites/tiles/thornveil/props/campfire_anim.png"
LAKE_WAVES = "res://assets/sprites/tiles/thornveil/water/lake.png"
TREE_SCENES = {"fir": "res://scenes/world/props/forest_fir.tscn", "oak": "res://scenes/world/props/forest_oak.tscn",
               "pine": "res://scenes/world/props/snow_pine.tscn"}
TREE_R = {"fir": (7, 22), "oak": (10, 30), "pine": (8, 24)}     # trunk radius, shadow radius


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy or 1)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def in_poly(x, y, pts):
    inside = False
    for (ax, ay), (bx, by) in zip(pts, pts[1:] + pts[:1]):
        if (ay > y) != (by > y) and x < ax + (y - ay) * (bx - ax) / (by - ay):
            inside = not inside
    return inside


def bottom_offset(path):
    im = Image.open(path)
    return im.height / 2 - im.getbbox()[3]


class Zone:
    def __init__(self, key):
        self.key = key
        self.cfg = RL.ZONES[key]
        c = self.cfg
        self.x0, self.y0, self.x1, self.y1 = c["bounds"]
        self.cols, self.rows = (self.x1 - self.x0) // TILE, (self.y1 - self.y0) // TILE
        self.W, self.H = self.x1 - self.x0, self.y1 - self.y0
        self.art = c["art"]
        os.makedirs(self.art, exist_ok=True)
        self.rng = random.Random(key)
        self.nprng = np.random.default_rng(len(key) * 7 + 1)

    # ------------------------------------------------------------------ helpers
    def on_path(self, x, y, grow=0.0):
        return any(seg_dist(x, y, *a, *b) <= w + grow for pts, w in self.cfg.get("paths", []) for a, b in zip(pts, pts[1:]))

    def wet(self, x, y, margin=0.0):
        """In a lake's water (or within `margin` px of it). Shores wander a little."""
        x, y = x + 14 * math.sin(y / 53.0 + 0.4) + 8 * math.sin(y / 19.0), y + 12 * math.sin(x / 61.0 + 1.3) + 6 * math.sin(x / 23.0)
        for cx, cy, rx, ry in self.cfg.get("lakes", []):
            if ((x - cx) / (rx + margin)) ** 2 + ((y - cy) / (ry + margin)) ** 2 < 1.0:
                if not any(((x - lx) / max(1, lrx - margin)) ** 2 + ((y - ly) / max(1, lry - margin)) ** 2 < 1.0
                           for lx, ly, lrx, lry in self.cfg.get("land", [])):
                    return True
        return False

    def cell(self, x, y):
        return int((y - self.y0) // TILE), int((x - self.x0) // TILE)

    def noise(self, cell):
        W, H = self.W, self.H
        n = (self.nprng.random((H // cell + 3, W // cell + 3)) * 255).astype(np.uint8)
        return np.asarray(Image.fromarray(n).resize(((W // cell + 3) * cell, (H // cell + 3) * cell),
                                                    Image.BICUBIC))[:H, :W] / 255.0

    def soft_mask(self, inside, blur=5, rough=0.22, res=4):
        """A per-pixel mask from a point test: sampled coarse, blurred, with a ragged edge."""
        W, H = self.W, self.H
        coarse = np.zeros((H // res, W // res), np.uint8)
        for j in range(H // res):
            for i in range(W // res):
                coarse[j, i] = 255 if inside(self.x0 + i * res + 2, self.y0 + j * res + 2) else 0
        m = np.asarray(Image.fromarray(coarse).resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(blur))) / 255.0
        return (m + (self.noise(18) - 0.5) * rough) > 0.5

    # ------------------------------------------------------------------ terrain
    def terrain(self):
        c = self.cfg
        levels = [[c["level"](self.x0 + i * TILE, self.y0 + j * TILE) for i in range(self.cols + 1)]
                  for j in range(self.rows + 1)]
        self.levels = levels
        used = sorted({v for row in levels for v in row})
        cliff = CliffSet(c["cliff"])
        sets = {(a, b): cliff for a in used for b in used if a < b}
        flat = {v: ((used[0], used[-1]) if len(used) > 1 else (v, v + 1), "lower" if v == used[0] else "upper") for v in used}
        if len(used) == 1:
            sets = {(used[0], used[0] + 1): cliff}
        img, stand = compose(levels, sets, flat, TILE, extra_wall_rows=c.get("tall_walls"))
        self.stand = stand
        # Stairs: find the wall edge near each requested spot.
        self.stairs = []
        for sx, sy, lo, hi in c.get("stairs", []):
            base = int((sx - self.x0) // TILE) - 1
            guess = round((sy - self.y0) / TILE)
            spots = sorted(((r, base + dc) for r in range(guess - 8, guess + 9) for dc in range(-7, 8)),
                           key=lambda rc: abs(rc[0] - guess) + abs(rc[1] - base))
            edge, c0 = next(((r, cc0) for r, cc0 in spots
                             if 1 <= r < self.rows - 3 and 1 <= cc0 < self.cols - 3
                             and all(levels[r][cc] == hi and levels[r - 1][cc] == hi and levels[r + 1][cc] == lo
                                     and levels[r + 2][cc] == lo for cc in range(cc0 - 1, cc0 + 4))),
                            (None, None))
            if edge is None:
                raise SystemExit(f"{self.key}: stairs at ({sx}, {sy}): no {hi}->{lo} wall edge near there")
            rows = 2 + (c.get("tall_walls") or {}).get((lo, hi), 0)
            self.stairs.append((c0, edge - (rows - 2), rows))
        self.stair_cells = {(r0 + dr, c0 + dc) for c0, r0, rows in self.stairs for dr in range(rows) for dc in (0, 1)}
        return img

    def paint(self, img, trees, shadows):
        c = self.cfg
        W, H = self.W, self.H
        a = np.asarray(img.convert("RGBA")).astype(np.float32)
        # Grade into the biome's palette.
        sat, mul = c["grade"]
        rgb = Image.fromarray(a[..., :3].astype(np.uint8))
        rgb = ImageEnhance.Color(rgb).enhance(sat)
        a[..., :3] = np.asarray(rgb).astype(np.float32) * np.array(mul, np.float32)
        flat = np.kron(np.array([[1 if (v >= 0) else 0 for v in row] for row in self.stand], np.uint8),
                       np.ones((TILE, TILE), np.uint8)).astype(bool)
        # Break the grass tile's repetition: flip each open flat cell at random (only
        # cells whose neighbours are flat too, so cliff edges stay as drawn).
        if c.get("palette") and not c.get("snow"):
            rng = np.random.default_rng(len(self.key) * 13)
            for r in range(1, self.rows - 1):
                for cc in range(1, self.cols - 1):
                    if all(self.stand[r + dr][cc + dc] >= 0 for dr in (-1, 0, 1) for dc in (-1, 0, 1)) \
                            and (r, cc) not in self.stair_cells:
                        k = rng.integers(0, 4)
                        if k:
                            block = a[r * TILE:(r + 1) * TILE, cc * TILE:(cc + 1) * TILE]
                            block = block[:, ::-1] if k & 1 else block
                            block = block[::-1] if k & 2 else block
                            a[r * TILE:(r + 1) * TILE, cc * TILE:(cc + 1) * TILE] = block
        tile = lambda t: np.tile(np.asarray(t.convert("RGBA")), (H // 32 + 1, W // 32 + 1, 1))[:H, :W].astype(np.float32)
        broad = np.clip(self.noise(140) * 0.65 + self.noise(46) * 0.35, 0, 1)
        # Grass: mapped onto the biome's palette by brightness (the tile's detail stays,
        # its neon green goes), drifting between two colours in broad patches.
        if c.get("palette"):
            col_a, col_b = (np.array(v, np.float32) for v in c["palette"])
            grass = (a[..., 1] > a[..., 0] + 8) & (a[..., 1] > a[..., 2] + 8)
            lum = a[..., 0] * 0.3 + a[..., 1] * 0.59 + a[..., 2] * 0.11
            rel = (lum / max(1.0, float(lum[grass].mean())))[..., None] ** 0.75
            mix = np.clip((broad - 0.5) * 1.7 + 0.5, 0, 1)[..., None]
            tint = col_a * (1 - mix) + col_b * mix
            a[..., :3] = np.where(grass[..., None], tint * rel, a[..., :3])
        # Snow: the tileset's flat snow repeats a diagonal hatch, so flat ground is
        # repainted as soft drifts (broad blue-white swells, fine grain, a few glints).
        if c.get("snow"):
            drift = np.clip(broad * 0.7 + self.noise(22) * 0.3, 0, 1)
            grain = self.nprng.random((H, W)) * 0.035
            snow = (np.array([214, 226, 242], np.float32) * (1 - drift[..., None])
                    + np.array([246, 250, 255], np.float32) * drift[..., None]) * (0.97 + grain[..., None])
            glint = self.nprng.random((H, W)) > 0.9985
            snow = np.where(glint[..., None], np.array([255, 255, 255], np.float32), snow)
            inner = np.asarray(Image.fromarray(flat.astype(np.uint8) * 255).filter(ImageFilter.MinFilter(3))) > 0
            a[..., :3] = np.where(inner[..., None], snow, a[..., :3])
        # Broad soft light, so the ground never reads as tiles.
        dapple = (self.noise(90) * 0.6 + self.noise(30) * 0.4 - 0.5)
        a[..., :3] *= (1.0 + dapple * c.get("dapple", 0.14))[..., None]
        # Wildflower meadows: tiny petals speckled thickly in the middle of each patch,
        # thinning out at its edge (drawn before paths and fields, which cover them).
        for mcx, mcy, mrx, mry, colours in c.get("meadows", []):
            rng = np.random.default_rng(int(abs(mcx) * 7 + abs(mcy)))
            x0p, x1p = max(0, int(mcx - mrx - self.x0)), min(W, int(mcx + mrx - self.x0))
            y0p, y1p = max(0, int(mcy - mry - self.y0)), min(H, int(mcy + mry - self.y0))
            count = int((x1p - x0p) * (y1p - y0p) / 30)
            xs = rng.integers(x0p, max(x0p + 1, x1p - 1), count)
            ys = rng.integers(y0p, max(y0p + 1, y1p - 1), count)
            for px, py in zip(xs, ys):
                d = ((px + self.x0 - mcx) / mrx) ** 2 + ((py + self.y0 - mcy) / mry) ** 2
                if d > 1.0 or rng.random() < d * 0.9 or not flat[py, px]:
                    continue
                col = np.array(colours[rng.integers(0, len(colours))], np.float32)
                a[py, px, :3] = col
                if rng.random() < 0.5 and px + 1 < W:
                    a[py, px + 1, :3] = col * 0.85
                if py + 1 < H:
                    a[py + 1, px, :3] = a[py + 1, px, :3] * 0.8          # a stalk's shadow
        # Wheat fields: golden, in rows, ragged at the edges, a trampled rim.
        fields = c.get("fields", [])
        if fields:
            wheat = tile(CornerSet(WHEAT).tiles[15])
            wl = wheat[..., 0] * 0.3 + wheat[..., 1] * 0.59 + wheat[..., 2] * 0.11
            wrel = (wl / wl.mean())[..., None] ** 0.8
            gold = np.array(c.get("wheat", (214, 176, 84)), np.float32)
            wheat[..., :3] = gold * wrel * (0.92 + 0.16 * broad[..., None])
            yy, xx = np.mgrid[0:H, 0:W]
            rows = (np.sin((yy + 3 * np.sin(xx / 23.0)) * math.tau / 11.0) > 0.72)
            wheat[..., :3] = np.where(rows[..., None], wheat[..., :3] * 0.8, wheat[..., :3])
            on = self.soft_mask(lambda x, y: any(fx0 <= x <= fx1 and fy0 <= y <= fy1 for fx0, fy0, fx1, fy1 in fields),
                                blur=3, rough=0.35) & flat
            rim = on & ~(np.asarray(Image.fromarray(on.astype(np.uint8) * 255).filter(ImageFilter.MinFilter(5))) > 0)
            a = np.where(on[..., None], wheat, a)
            a[..., :3] = np.where(rim[..., None], a[..., :3] * 0.82, a[..., :3])
        # Paths: the distance to each path's centre line, with a wandering edge; wide
        # roads get two darker wheel ruts.
        if c.get("paths"):
            if c.get("snow"):
                path_tex = a.copy()
                trod = np.clip(self.noise(8) * 0.5 + 0.5, 0, 1)[..., None]
                path_tex[..., :3] = path_tex[..., :3] * np.array([0.93, 0.93, 0.95]) * (0.95 + 0.05 * trod) - 4
            else:
                path_tex = tile(CornerSet(DIRT).tiles[15])
                pl = path_tex[..., 0] * 0.3 + path_tex[..., 1] * 0.59 + path_tex[..., 2] * 0.11
                prel = (pl / pl.mean())[..., None] ** 0.7
                earth = np.array(c.get("dirt", (158, 128, 88)), np.float32)
                path_tex[..., :3] = earth * prel * (0.94 + 0.12 * broad[..., None])
            wiggle = (self.noise(26) - 0.5) * 2
            on = np.zeros((H, W), bool)
            ruts = np.zeros((H, W), bool)
            for width in sorted({w for _, w in c["paths"]}):
                line = Image.new("L", (W, H), 0)
                d = ImageDraw.Draw(line)
                for pts, w in c["paths"]:
                    if w == width:
                        d.line([(x - self.x0, y - self.y0) for x, y in pts], fill=255, width=1)
                dist = ndimage.distance_transform_edt(np.asarray(line) == 0)
                on |= dist < width * (1.0 + 0.16 * wiggle)
                if 24 <= width <= 40 and not c.get("snow"):
                    ruts |= np.abs(dist - width * 0.42) < 2.2
            on &= flat | self.stair_px()
            near = np.asarray(Image.fromarray((~on).astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(5))) > 0
            a = np.where(on[..., None], path_tex, a)
            a[..., :3] = np.where((on & ruts)[..., None], a[..., :3] * 0.84, a[..., :3])
            a[..., :3] = np.where((on & near)[..., None], a[..., :3] * 0.86, a[..., :3])
            lip = np.asarray(Image.fromarray(on.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(7))) > 0
            a[..., :3] = np.where((~on & lip & flat)[..., None], a[..., :3] * 0.9, a[..., :3])
        # Plazas: cobbled squares (Kalmora's paving, warmed to the town's stone), a
        # ring of darker setts at the edge.
        if c.get("plazas"):
            pave = tile(CliffSet(PAVING).pick([[1] * 4 for _ in range(4)]))
            pv = pave[..., 0] * 0.3 + pave[..., 1] * 0.59 + pave[..., 2] * 0.11
            stone = np.array(c.get("plaza_stone", (196, 176, 140)), np.float32)
            pave[..., :3] = stone * ((pv / pv.mean())[..., None] ** 0.9) * (0.95 + 0.1 * broad[..., None])
            yy, xx = np.mgrid[0:H, 0:W]
            e = np.full((H, W), 9.0, np.float32)
            for pcx, pcy, prx, pry in c["plazas"]:
                e = np.minimum(e, ((xx + self.x0 - pcx) / prx) ** 2 + ((yy + self.y0 - pcy) / pry) ** 2)
            on = (e < 1.0) & flat
            ring = on & (e > 0.86)
            a = np.where(on[..., None], pave, a)
            a[..., :3] = np.where(ring[..., None], a[..., :3] * 0.78, a[..., :3])
        # Ice: frozen tarns, pale and cracked, walkable.
        for cx, cy, rx, ry in c.get("ice", []):
            yy, xx = np.mgrid[0:H, 0:W]
            e = ((xx + self.x0 - cx) / rx) ** 2 + ((yy + self.y0 - cy) / ry) ** 2 + (self.noise(14) - 0.5) * 0.08
            ice = e < 1.0
            shade = np.clip(1.0 - e, 0, 1)[..., None]
            col = np.array([196, 222, 238], np.float32) * (0.92 + 0.08 * shade) - np.array([20, 10, 0]) * shade
            a[..., :3] = np.where(ice[..., None], col, a[..., :3])
            crack = (np.abs(np.sin((xx * 0.07 + yy * 0.05) + self.noise(40) * 6)) < 0.03) & ice
            a[..., :3] = np.where(crack[..., None], a[..., :3] * 0.8, a[..., :3])
            rim = ice & ~(np.asarray(Image.fromarray(ice.astype(np.uint8) * 255).filter(ImageFilter.MinFilter(5))) > 0)
            a[..., :3] = np.where(rim[..., None], np.array([240, 248, 255], np.float32), a[..., :3])
        # Water.
        self.water = np.zeros((H, W), bool)
        if c.get("lakes"):
            water = self.soft_mask(lambda x, y: self.wet(x, y), blur=4, rough=0.12, res=4)
            for dx0, dy0, dx1, dy1 in c.get("docks", []):
                water[dy0 - self.y0:dy1 - self.y0, dx0 - self.x0:dx1 - self.x0] = False
            near = np.asarray(Image.fromarray(water.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(11))) > 0
            shore = near & ~water
            mud = tile(CornerSet(DIRT).tiles[15]) * np.array([0.7, 0.68, 0.64, 1.0], np.float32)
            a = np.where(shore[..., None], mud, a)
            a[..., :3] = np.where(water[..., None], np.array(c.get("deep", (28, 70, 90)), np.float32), a[..., :3])
            self.water = water
            m = np.zeros((H, W, 4), np.uint8)
            m[water] = 255
            Image.fromarray(m, "RGBA").save(self.art + self.key + "_water_mask.png")
        # Docks: planks laid over the water, dark gaps between boards, posts at the edge.
        for dx0, dy0, dx1, dy1 in c.get("docks", []):
            planks = tile(CornerSet(PLANKS).tiles[15])
            a[dy0 - self.y0:dy1 - self.y0, dx0 - self.x0:dx1 - self.x0] = planks[dy0 - self.y0:dy1 - self.y0, dx0 - self.x0:dx1 - self.x0]
            a[dy1 - self.y0 - 3:dy1 - self.y0, dx0 - self.x0:dx1 - self.x0, :3] *= 0.55
        # Soft shadows under trees, buildings and props.
        mask = Image.new("L", (W, H), 0)
        d = ImageDraw.Draw(mask)
        for kind, x, y in trees:
            r = TREE_R[kind][1]
            d.ellipse((x - self.x0 - r, y - self.y0 - r * 0.45, x - self.x0 + r, y - self.y0 + r * 0.45 + 4), fill=150)
        for x, y, rw, rh, strength in shadows:
            d.ellipse((x - self.x0 - rw, y - self.y0 - rh, x - self.x0 + rw, y - self.y0 + rh), fill=int(255 * strength))
        sm = np.asarray(mask.filter(ImageFilter.GaussianBlur(6))).astype(np.float32)[..., None] / 255.0
        a[..., :3] = a[..., :3] * (1 - sm * 0.5)
        a[..., 3] = 255
        out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
        out.save(self.art + self.key + "_ground.png")
        return out

    def stair_px(self):
        m = np.zeros((self.H, self.W), bool)
        for r, cc in self.stair_cells:
            m[r * TILE:(r + 1) * TILE, cc * TILE:(cc + 1) * TILE] = True
        return m

    def build_stairs(self):
        src = Image.open(STAIRS_SRC).convert("RGBA")
        src = src.crop(src.getbbox())
        w, h = src.size
        paths = {}
        for rows in {rows for _, _, rows in self.stairs}:
            target = rows * TILE
            top, bottom, mid = src.crop((0, 0, w, 14)), src.crop((0, h - 14, w, h)), src.crop((0, 14, w, h - 14))
            body = Image.new("RGBA", (w, target - 28))
            for y in range(0, body.height, mid.height):
                body.paste(mid, (0, y))
            flight = Image.new("RGBA", (w, target))
            flight.paste(top, (0, 0))
            flight.paste(body, (0, 14))
            flight.paste(bottom, (0, target - 14))
            if self.cfg.get("snow"):
                arr = np.asarray(flight).astype(np.float32)
                arr[..., :3] = arr[..., :3] * 0.8 + np.array([48, 52, 60])
                flight = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
            out = Image.new("RGBA", (2 * TILE, target))
            out.paste(flight, ((2 * TILE - w) // 2, 0))
            paths[rows] = f"{self.art}stairs_{rows}.png"
            out.save(paths[rows])
        return paths

    # ------------------------------------------------------------------ dressing
    def layout_trees(self, keep, fronts):
        c = self.cfg
        rng = self.rng
        trees = []
        kinds = c.get("tree_kinds", ["oak", "fir"])

        def ground_ok(x, y):
            r, cc = self.cell(x, y)
            return (0 <= r < self.rows and 0 <= cc < self.cols and self.stand[r][cc] >= 0
                    and (r, cc) not in self.stair_cells and 0 <= r - 1 and self.stand[r - 1][cc] >= 0)

        def free(x, y, gap, path_gap):
            if not ground_ok(x, y) or self.on_path(x, y, path_gap) or self.wet(x, y, 30) or self.in_field(x, y, 20) or self.in_plaza(x, y, 30):
                return False
            if any(self.in_ice(x, y, 20) for _ in [0]):
                return False
            if any((x - a) ** 2 + (y - b) ** 2 < r ** 2 for a, b, r in keep):
                return False
            if any(abs(x - a) < w and 0 < y - b < 140 for a, b, w in fronts):
                return False
            return all((x - a) ** 2 + (y - b) ** 2 >= gap ** 2 for _, a, b in trees)

        x0, y0, x1, y1 = self.x0, self.y0, self.x1, self.y1
        for inset, step, jitter in ((14, 34, 6), (46, 40, 10)):
            for x in range(x0 + 10, x1 - 5, step):
                for y in (y0 + inset + 50, y1 - inset + 6):
                    px, py = x + rng.randint(-jitter, jitter), y + rng.randint(-jitter, jitter)
                    if free(px, py, 26, 30):
                        trees.append((rng.choice(kinds), px, py))
            for y in range(y0 + 60, y1, step):
                for x in (x0 + inset, x1 - inset):
                    px, py = x + rng.randint(-jitter, jitter), y + rng.randint(-jitter, jitter)
                    if free(px, py, 26, 30):
                        trees.append((rng.choice(kinds), px, py))
        for gx, gy, count, spread in c.get("groves", []):
            for _ in range(count * 4):
                if sum(1 for _, a, b in trees if math.hypot(a - gx, b - gy) < spread * 1.6) >= count:
                    break
                ang, r = rng.uniform(0, math.tau), abs(rng.gauss(0, spread))
                px, py = round(gx + math.cos(ang) * r * 1.3), round(gy + math.sin(ang) * r)
                t = rng.choice(kinds)
                if free(px, py, 28, 36 if t != "oak" else 56):
                    trees.append((t, px, py))
        return trees

    def in_field(self, x, y, grow=0):
        return any(fx0 - grow <= x <= fx1 + grow and fy0 - grow <= y <= fy1 + grow for fx0, fy0, fx1, fy1 in self.cfg.get("fields", []))

    def in_plaza(self, x, y, grow=0):
        return any(((x - cx) / (rx + grow)) ** 2 + ((y - cy) / (ry + grow)) ** 2 < 1 for cx, cy, rx, ry in self.cfg.get("plazas", []))

    def in_ice(self, x, y, grow=0):
        return any(((x - cx) / (rx + grow)) ** 2 + ((y - cy) / (ry + grow)) ** 2 < 1 for cx, cy, rx, ry in self.cfg.get("ice", []))

    def layout_under(self, keep, trees):
        c = self.cfg
        rng = self.rng
        names = [n for n, _ in c.get("under", [])]
        weights = [w for _, w in c.get("under", [])]
        props = []
        if not names:
            return props

        def ok(x, y):
            r, cc = self.cell(x, y)
            return (0 <= r < self.rows and 0 <= cc < self.cols and self.stand[r][cc] >= 0 and (r, cc) not in self.stair_cells
                    and not self.on_path(x, y, 6) and not self.wet(x, y, 10) and not self.in_field(x, y, 4)
                    and not self.in_ice(x, y, 4) and not self.in_plaza(x, y, 8)
                    and not any((x - a) ** 2 + (y - b) ** 2 < (r2 * 0.7) ** 2 for a, b, r2 in keep)
                    and all((x - a) ** 2 + (y - b) ** 2 >= 18 ** 2 for _, a, b in props)
                    and all((x - a) ** 2 + (y - b) ** 2 >= 14 ** 2 for _, a, b in trees))
        for _, tx, ty in trees:
            if rng.random() < 0.5:
                px, py = tx + rng.choice([-1, 1]) * rng.randint(16, 26), ty + rng.randint(2, 12)
                if ok(px, py):
                    props.append((rng.choices(names, weights)[0], px, py))
        patches = 0
        for _ in range(3000):
            if patches >= c.get("patches", 40):
                break
            cx, cy = rng.uniform(self.x0 + 40, self.x1 - 40), rng.uniform(self.y0 + 60, self.y1 - 20)
            if not ok(cx, cy):
                continue
            patches += 1
            kind = rng.choices(names, weights)[0]
            for _ in range(rng.randint(2, 5)):
                px, py = round(cx + rng.gauss(0, 16)), round(cy + rng.gauss(0, 10))
                if ok(px, py):
                    props.append((kind, px, py))
        # Along the path edges.
        for _ in range(1500):
            px, py = rng.uniform(self.x0, self.x1), rng.uniform(self.y0, self.y1)
            if self.on_path(px, py, 24) and not self.on_path(px, py, 10) and ok(px, py) and rng.random() < 0.3:
                props.append((rng.choices(names, weights)[0], round(px), round(py)))
        # Reeds along lake shores.
        if c.get("lakes") and "cattails" not in c.get("no_reeds", []):
            for lcx, lcy, rx, ry in c["lakes"]:
                for k in range(220):
                    ang = k / 220 * math.tau
                    if math.sin(ang * 6 + 1.0) < -0.1:
                        continue
                    g = rng.uniform(12, 20)
                    px, py = round(lcx + math.cos(ang) * (rx + g)), round(lcy + math.sin(ang) * (ry + g * 0.6))
                    if self.wet(px, py) or not (self.x0 + 20 < px < self.x1 - 20 and self.y0 + 30 < py < self.y1 - 10):
                        continue
                    if any((px - a) ** 2 + (py - b) ** 2 < r2 ** 2 for a, b, r2 in keep) or self.on_path(px, py, 8):
                        continue
                    if all((px - a) ** 2 + (py - b) ** 2 >= 14 ** 2 for _, a, b in props):
                        props.append(("cattails", px, py))
        return props

    def layout_tufts(self, keep, trees, under):
        """Swaying grass tufts (Kalmora's animated strips) in loose patches on open grass."""
        n = self.cfg.get("tufts", 0)
        rng = random.Random(self.key + "tufts")
        out = []
        tries = 0
        while len(out) < n and tries < n * 60:
            tries += 1
            cx, cy = rng.uniform(self.x0 + 50, self.x1 - 50), rng.uniform(self.y0 + 70, self.y1 - 30)
            for _ in range(rng.randint(3, 7)):
                x, y = round(cx + rng.gauss(0, 22)), round(cy + rng.gauss(0, 12))
                r, cc = self.cell(x, y)
                if not (0 <= r < self.rows and 0 <= cc < self.cols) or self.stand[r][cc] < 0 or (r, cc) in self.stair_cells:
                    continue
                if self.on_path(x, y, 8) or self.wet(x, y, 12) or self.in_field(x, y, 6) or self.in_ice(x, y, 6) or self.in_plaza(x, y, 8):
                    continue
                if any((x - a) ** 2 + (y - b) ** 2 < (r2 * 0.7) ** 2 for a, b, r2 in keep):
                    continue
                if any((x - a) ** 2 + (y - b) ** 2 < 14 ** 2 for _, a, b in trees + under + out):
                    continue
                out.append((("tuft", "tuft_flowers")[rng.random() < 0.3], x, y))
        return out

    # ------------------------------------------------------------------ scene
    def build(self):
        c = self.cfg
        img = self.terrain()
        stair_png = self.build_stairs()
        # Every flight of stairs should carry a path up it (else it looks like a stray).
        for c0, r0, rows in self.stairs:
            sx = self.x0 + (c0 + 1) * TILE
            for sy in (self.y0 + r0 * TILE + 6, self.y0 + (r0 + rows) * TILE - 6):
                if not self.on_path(sx, sy, 10):
                    print(f"  warning: {self.key}: no path reaches the stairs at ({sx}, {sy})")
        subs, ext, tex = {}, [], {}

        def shape(w, h):
            key = f"R{w:g}x{h:g}".replace(".", "_").replace("-", "m")
            subs[key] = f'[sub_resource type="RectangleShape2D" id="{key}"]\nsize = Vector2({w}, {h})\n'
            return key

        def res(kind, path):
            key = (kind, path)
            if key not in tex:
                tex[key] = f"r{len(tex)}_{os.path.basename(path).split('.')[0][:16]}"
                ext.append((kind, path, tex[key]))
            return tex[key]

        def texture(path):
            return res("Texture2D", "res://" + path)

        # Everything that matters, and the room it keeps clear round it.
        keep = []
        fronts = []
        shadows = []
        targets = {}
        for b in c.get("buildings", []):
            x, y = b["pos"]
            fw = b["foot"]
            keep.append((x, y - 30, fw * 0.75))
            fronts.append((x, y, fw * 0.6))
            shadows.append((x, y - 6, fw * 0.55, 14, 0.5))
            if b.get("door"):
                targets[b["node"] + " door"] = (x + b.get("door_dx", 0), y + 24)
        for npc in c.get("npcs", []):
            x, y = npc["pos"]
            keep.append((x, y, 40 + npc.get("wander", 0)))
            targets["resident " + npc["id"]] = (x, y + 10)
        for title, (x, y), _ in c.get("readables", []):
            keep.append((x, y, 30))
            targets["readable " + title] = (x, y + 14)
        for ch in c.get("chests", []):
            x, y = ch["pos"]
            keep.append((x, y, 36))
            targets["chest " + ch["id"]] = (x, y + 16)
        for scene_path, (x, y) in c.get("monsters", []):
            keep.append((x, y, 80))
        if c.get("merchant"):
            keep.append((*c["merchant"][0], 60))
        for ex in c.get("exits", []) + c.get("portals", []):
            keep.append((*ex["pos"], 80))
            targets["exit " + ex["name"]] = ex["pos"]
        for name, (x, y) in c.get("spawns", {}).items():
            keep.append((x, y, 50))
        for p in c.get("props", []):
            x, y = p["pos"]
            fw = p.get("foot", (22, 8))[0]
            keep.append((x, y, 26 + fw / 2))
            shadows.append((x, y - 2, max(10, fw * 0.55), 5, 0.35))
        # Lanterns stand beside a path, never on it: nudge sideways until clear.
        lanterns = []
        for x, y in c.get("lanterns", []):
            for dx in (0, 30, -30, 48, -48, 66, -66):
                if not self.on_path(x + dx, y, 8):
                    x += dx
                    break
            lanterns.append((x, y))
        self.lanterns = lanterns
        for x, y in lanterns:
            keep.append((x, y, 26))
        for x, y in c.get("campfires", []):
            keep.append((x, y, 60))
        trees = self.layout_trees(keep, fronts)
        under = self.layout_under(keep, trees)
        tufts = self.layout_tufts(keep, trees, under)
        ground = self.paint(img, trees, shadows)

        # Level map: red = level * 40, 255 = cliff/stairs.
        lm = Image.new("RGB", (self.cols, self.rows))
        for r in range(self.rows):
            for cc in range(self.cols):
                v = self.stand[r][cc]
                lm.putpixel((cc, r), (255, 0, 0) if v < 0 or (r, cc) in self.stair_cells else (v * 40, 0, 0))
        lm.save(self.art + self.key + "_levels.png")

        ext += [
            ('Script', "res://scripts/world/zone.gd", "1_zone"),
            ('PackedScene', "res://scenes/characters/player.tscn", "2_player"),
            ('PackedScene', "res://scenes/ui/hud.tscn", "3_hud"),
            ('PackedScene', "res://scenes/ui/binder.tscn", "4_binder"),
            ('PackedScene', "res://scenes/ui/shop_panel.tscn", "5_shop"),
            ('PackedScene', "res://scenes/ui/dialogue_box.tscn", "6_dialogue"),
            ('PackedScene', "res://scenes/systems/zone_exit.tscn", "7_exit"),
            ('Script', "res://scripts/systems/lamp_light.gd", "8_lamp"),
        ]
        cx, cy = (self.x0 + self.x1) / 2, (self.y0 + self.y1) / 2
        n = [f'''[node name="{c["root"]}" type="Node2D"]
y_sort_enabled = true
script = ExtResource("1_zone")
display_name = "{c["display"]}"
water_shimmer = false
level_map = ExtResource("{texture(self.art + self.key + "_levels.png")}")
level_cell = {TILE}
level_origin = Vector2({self.x0}, {self.y0})

[node name="GroundTiles" type="Sprite2D" parent="."]
z_index = -10
position = Vector2({cx}, {cy})
texture = ExtResource("{texture(self.art + self.key + "_ground.png")}")
''']
        for k, (c0, r0, rows) in enumerate(self.stairs):
            x, top = self.x0 + c0 * TILE, self.y0 + r0 * TILE
            n.append(f'[node name="Stairs{k + 1}" type="Sprite2D" parent="."]\nz_index = -8\n'
                     f'position = Vector2({x + TILE}, {top + rows * TILE / 2})\ntexture = ExtResource("{texture(stair_png[rows])}")\n')
        if c.get("lakes"):
            n.append(f'[node name="LakeWater" type="Sprite2D" parent="."]\nz_index = -9\nclip_children = 1\n'
                     f'position = Vector2({cx}, {cy})\ntexture = ExtResource("{texture(self.art + self.key + "_water_mask.png")}")\n'
                     + (f'self_modulate = Color(1, 1, 1, 1)\n') + "\n"
                     f'[node name="Waves" type="Sprite2D" parent="LakeWater"]\n'
                     f'modulate = Color{c.get("water_tint", (1, 1, 1, 1))}\n'
                     f'script = ExtResource("{res("Script", "res://scripts/world/tiled_animation.gd")}")\n'
                     f'strip = ExtResource("{res("Texture2D", LAKE_WAVES)}")\nframe_count = 8\nfps = 3.0\n'
                     f'region_rect = Rect2(0, 0, {self.W}, {self.H})\n')

        # Collision: cliffs (visible faces), water pixels, the map edge (behind the treeline).
        solid = [[(self.stand[r][cc] < 0 and (r, cc) not in self.stair_cells) for cc in range(self.cols)] for r in range(self.rows)]
        walls = merge_rects(solid, self.x0, self.y0, TILE)
        if self.water.any():
            walls += mask_rects(self.water, self.x0, self.y0, step=8, erode=4, fill=0.5)
        x0, y0, x1, y1 = self.x0, self.y0, self.x1, self.y1
        edges = {"n": [(x0 - 40, y0 - 40, x1 + 40, y0)], "s": [(x0 - 40, y1, x1 + 40, y1 + 40)],
                 "w": [(x0 - 40, y0, x0, y1)], "e": [(x1, y0, x1 + 40, y1)]}
        for ex in c.get("exits", []):
            ex_x, ex_y = ex["pos"]
            side = ex["side"]
            gap = ex.get("gap", 44)
            if side in "ns":
                edges[side] = self._cut(edges[side], ex_x, gap, horizontal=True)
                ya, yb = (y0 - 80, y0 - 40) if side == "n" else (y1 + 40, y1 + 80)
                edges[side] += [(ex_x - gap - 40, ya, ex_x - gap, yb), (ex_x + gap, ya, ex_x + gap + 40, yb)]
            else:
                edges[side] = self._cut(edges[side], ex_y, gap, horizontal=False)
                xa, xb = (x0 - 80, x0 - 40) if side == "w" else (x1 + 40, x1 + 80)
                edges[side] += [(xa, ex_y - gap - 40, xb, ex_y - gap), (xa, ex_y + gap, xb, ex_y + gap + 40)]
        for side in edges.values():
            walls += side
        n.append('[node name="Walls" type="StaticBody2D" parent="."]\n')
        for k, (a, b, cc2, d) in enumerate(walls):
            n.append(f'[node name="W{k}" type="CollisionShape2D" parent="Walls"]\nposition = Vector2({(a + cc2) / 2}, {(b + d) / 2})\n'
                     f'shape = SubResource("{shape(cc2 - a, d - b)}")\n')

        if c.get("safe_zone"):
            sx0, sy0, sx1, sy1 = c["safe_zone"]
            n.append(f'[node name="SafeZone" type="Area2D" parent="."]\nposition = Vector2({(sx0 + sx1) / 2}, {(sy0 + sy1) / 2})\n'
                     f'collision_layer = 0\ncollision_mask = 6\nmonitorable = false\n'
                     f'script = ExtResource("{res("Script", "res://scripts/systems/safe_zone.gd")}")\n\n'
                     f'[node name="CollisionShape2D" type="CollisionShape2D" parent="SafeZone"]\nshape = SubResource("{shape(sx1 - sx0, sy1 - sy0)}")\n')

        spawns = dict(c.get("spawns", {}))
        for b in c.get("buildings", []):
            if b.get("door"):
                spawns[b["back"]] = (b["pos"][0] + b.get("door_dx", 0), b["pos"][1] + 26)
        n.append('[node name="Spawns" type="Node2D" parent="."]\n')
        for name, (x, y) in spawns.items():
            n.append(f'[node name="{name}" type="Marker2D" parent="Spawns"]\nposition = Vector2({x}, {y})\n')
        n.append('[node name="RivalSpots" type="Node2D" parent="."]\n')
        for name, (x, y) in c.get("rival_spots", {}).items():
            n.append(f'[node name="{name}" type="Marker2D" parent="RivalSpots"]\nposition = Vector2({x}, {y})\n')
        for ex in c.get("exits", []):
            x, y = ex["pos"]
            n.append(f'[node name="{ex["name"]}" parent="." instance=ExtResource("7_exit")]\nposition = Vector2({x}, {y})\n'
                     f'target_scene = "{ex["target"]}"\ntarget_spawn = &"{ex["spawn"]}"\n' + ("exit_hint = true\n" if ex.get("hint") else ""))

        # Portals: walk-in exits inside the zone (a cave mouth), drawn by a prop.
        for p in c.get("portals", []):
            x, y = p["pos"]
            n.append(f'[node name="{p["name"]}" parent="." instance=ExtResource("7_exit")]\nposition = Vector2({x}, {y})\n'
                     f'target_scene = "{p["target"]}"\ntarget_spawn = &"{p["spawn"]}"\n')
        # Buildings: front-facing sprites, footprint collision, doors and window glow.
        solids = []
        for b in c.get("buildings", []):
            path = b["sprite"]
            x, y = b["pos"]
            bb = Image.open(path).getbbox()
            fd = b.get("depth", int(min(90, max(30, (bb[3] - bb[1]) * 0.42))))
            fw = b["foot"]
            node = b["node"]
            solids.append((x - fw / 2, y - fd, x + fw / 2, y))
            n.append(f'[node name="{node}" type="StaticBody2D" parent="."]\nposition = Vector2({x}, {y})\n\n'
                     f'[node name="Sprite" type="Sprite2D" parent="{node}"]\nposition = Vector2(0, {bottom_offset(path)})\n'
                     f'texture = ExtResource("{texture(path)}")\n\n'
                     f'[node name="Base" type="CollisionShape2D" parent="{node}"]\nposition = Vector2(0, {-fd / 2})\n'
                     f'shape = SubResource("{shape(fw, fd)}")\n')
            glow = window_glow(path, self.art + "night/")
            if glow:
                n.append(f'[node name="Windows" type="Sprite2D" parent="{node}"]\nposition = Vector2(0, {bottom_offset(path)})\n'
                         f'texture = ExtResource("{texture(glow)}")\n'
                         f'script = ExtResource("{res("Script", "res://scripts/world/window_glow.gd")}")\n'
                         f'lights_out = {1.0 + (len(node) % 5) * 0.6:.1f}\n')
            if b.get("door"):
                dx = b.get("door_dx", 0)
                n.append(f'[node name="{node}Door" parent="." instance=ExtResource("7_exit")]\nposition = Vector2({x + dx}, {y + 4})\n'
                         f'target_scene = "{b["door"]}"\ntarget_spawn = &"door"\nneeds_interact = true\n\n'
                         f'[node name="{node}Lamp" type="PointLight2D" parent="."]\nposition = Vector2({x + dx}, {y - 30})\n'
                         f'texture_scale = 0.9\nscript = ExtResource("8_lamp")\nmax_energy = 0.9\n')
            if b.get("sails"):
                strip, frames, fps, (hx, hy) = b["sails"]
                im = Image.open(strip)
                sw, sh = im.width // frames, im.height
                key = res("Texture2D", "res://" + strip)
                refs = []
                for f in range(frames):
                    subs[f"sail_{node}_{f}"] = (f'[sub_resource type="AtlasTexture" id="sail_{node}_{f}"]\natlas = ExtResource("{key}")\n'
                                                f'region = Rect2({f * sw}, 0, {sw}, {sh})\n')
                    refs.append(f'{{\n"duration": 1.0,\n"texture": SubResource("sail_{node}_{f}")\n}}')
                subs[f"sails_{node}"] = (f'[sub_resource type="SpriteFrames" id="sails_{node}"]\nanimations = [{{\n"frames": [{", ".join(refs)}],\n'
                                         f'"loop": true,\n"name": &"default",\n"speed": {fps}\n}}]\n')
                sprite = Image.open(path)
                ox = hx - sprite.width / 2
                oy = hy - sprite.height / 2 + bottom_offset(path)
                n.append(f'[node name="Sails" type="AnimatedSprite2D" parent="{node}"]\nposition = Vector2({ox}, {oy})\n'
                         f'sprite_frames = SubResource("sails_{node}")\nautoplay = "default"\n')

        # Props: sprites with a footprint you can see (or none, for flat things).
        for k, p in enumerate(c.get("props", [])):
            path = p["sprite"]
            x, y = p["pos"]
            im = Image.open(path)
            scale = p.get("scale", 1.0)
            off = (bottom_offset(path) + 2) * scale
            flip = "flip_h = true\n" if p.get("flip") else ""
            mod = f"modulate = Color{p['tint']}\n" if p.get("tint") else ""
            sc = f"scale = Vector2({scale}, {scale})\n" if scale != 1.0 else ""
            if p.get("feet"):
                # Several colliders under one sprite (a cave mouth's two pillars).
                n.append(f'[node name="Prop{k}" type="StaticBody2D" parent="."]\nposition = Vector2({x}, {y})\n\n'
                         f'[node name="Sprite" type="Sprite2D" parent="Prop{k}"]\n{sc}{mod}{flip}position = Vector2(0, {off})\n'
                         f'texture = ExtResource("{texture(path)}")\n')
                for j, (dx, dy, fw, fh) in enumerate(p["feet"]):
                    solids.append((x + dx - fw / 2, y + dy - fh / 2, x + dx + fw / 2, y + dy + fh / 2))
                    n.append(f'[node name="Foot{j}" type="CollisionShape2D" parent="Prop{k}"]\nposition = Vector2({dx}, {dy})\n'
                             f'shape = SubResource("{shape(fw, fh)}")\n')
            elif p.get("foot"):
                fw, fh = p["foot"]
                solids.append((x - fw / 2, y - fh, x + fw / 2, y))
                n.append(f'[node name="Prop{k}" type="StaticBody2D" parent="."]\nposition = Vector2({x}, {y})\n\n'
                         f'[node name="Sprite" type="Sprite2D" parent="Prop{k}"]\n{sc}{mod}{flip}position = Vector2(0, {off})\n'
                         f'texture = ExtResource("{texture(path)}")\n\n'
                         f'[node name="Base" type="CollisionShape2D" parent="Prop{k}"]\nposition = Vector2(0, {-fh / 2})\n'
                         f'shape = SubResource("{shape(fw, fh)}")\n')
            else:
                n.append(f'[node name="Prop{k}" type="Sprite2D" parent="."]\nposition = Vector2({x}, {y})\n{sc}{mod}{flip}'
                         f'offset = Vector2(0, {off / scale})\ntexture = ExtResource("{texture(path)}")\n')
            if p.get("light"):
                tint, energy, scale_l = p["light"]
                n.append(f'[node name="PropLight{k}" type="PointLight2D" parent="."]\nposition = Vector2({x}, {y - 20})\n'
                         f'texture_scale = {scale_l}\nscript = ExtResource("8_lamp")\nalways_on = true\nmax_energy = {energy}\n'
                         f'tint = Color{tint}\nflicker = 0.03\n')
        for k, (x, y) in enumerate(self.lanterns):
            solids.append((x - 5, y - 8, x + 5, y))
            n.append(f'[node name="Lantern{k}" type="StaticBody2D" parent="."]\nposition = Vector2({x}, {y})\n\n'
                     f'[node name="Sprite" type="Sprite2D" parent="Lantern{k}"]\nposition = Vector2(0, {bottom_offset(LANTERN_PNG)})\n'
                     f'texture = ExtResource("{texture(LANTERN_PNG)}")\n\n'
                     f'[node name="Base" type="CollisionShape2D" parent="Lantern{k}"]\nposition = Vector2(0, -4)\n'
                     f'shape = SubResource("{shape(10, 8)}")\n\n'
                     f'[node name="LanternLight{k}" type="PointLight2D" parent="."]\nposition = Vector2({x + 6}, {y - 44})\n'
                     f'texture_scale = 1.2\nscript = ExtResource("8_lamp")\n')
        if c.get("campfires"):
            frames = Image.open(CAMPFIRE_STRIP)
            fw, fh = frames.width // 8, frames.height
            key = res("Texture2D", "res://" + CAMPFIRE_STRIP)
            refs = []
            for f in range(8):
                subs[f"fire_{f}"] = (f'[sub_resource type="AtlasTexture" id="fire_{f}"]\natlas = ExtResource("{key}")\n'
                                     f'region = Rect2({f * fw}, 0, {fw}, {fh})\n')
                refs.append(f'{{\n"duration": 1.0,\n"texture": SubResource("fire_{f}")\n}}')
            subs["fire_frames"] = (f'[sub_resource type="SpriteFrames" id="fire_frames"]\nanimations = [{{\n"frames": [{", ".join(refs)}],\n'
                                   f'"loop": true,\n"name": &"default",\n"speed": 9\n}}]\n')
            for k, (x, y) in enumerate(c["campfires"]):
                solids.append((x - 20, y - 20, x + 20, y))
                n.append(f'[node name="Campfire{k}" type="StaticBody2D" parent="."]\nposition = Vector2({x}, {y})\n\n'
                         f'[node name="Fire" type="AnimatedSprite2D" parent="Campfire{k}"]\nscale = Vector2(1.5, 1.5)\n'
                         f'position = Vector2(0, -{(fh - 4) * 0.75})\nsprite_frames = SubResource("fire_frames")\nautoplay = "default"\n\n'
                         f'[node name="Base" type="CollisionShape2D" parent="Campfire{k}"]\nposition = Vector2(0, -10)\n'
                         f'shape = SubResource("{shape(40, 20)}")\n\n'
                         f'[node name="CampfireLight{k}" type="PointLight2D" parent="."]\nposition = Vector2({x}, {y - 24})\n'
                         f'texture_scale = 1.8\nscript = ExtResource("8_lamp")\nalways_on = true\nmax_energy = 0.9\nflicker = 0.18\n')

        # A card merchant's stall (scenes/systems/merchant.tscn).
        if c.get("merchant"):
            (mx, my), stall = c["merchant"]
            solids.append((mx - 30, my - 16, mx + 30, my))
            n.append(f'[node name="Merchant" parent="." instance=ExtResource("{res("PackedScene", "res://scenes/systems/merchant.tscn")}")]\n'
                     f'position = Vector2({mx}, {my})\nstall_texture = ExtResource("{texture(stall)}")\n')
        # Things floating on the water (lily pads, moored boats): no collision, drawn
        # just above the water.
        for k, (path, (x, y), flip) in enumerate(c.get("afloat", [])):
            n.append(f'[node name="Afloat{k}" type="Sprite2D" parent="."]\nz_index = -8\nposition = Vector2({x}, {y})\n'
                     + ("flip_h = true\n" if flip else "") + f'texture = ExtResource("{texture(path)}")\n')
        # Animated decor (a heron fishing, hens pecking): PixelLab frame strips, no collision.
        for k, d in enumerate(c.get("decor", [])):
            strip = d["strip"]
            im = Image.open(strip)
            fw, fh = im.width // d["frames"], im.height
            key = res("Texture2D", "res://" + strip)
            sid = f"decor_{os.path.basename(strip)[:-4]}"
            if f"{sid}_frames" not in subs:
                refs = []
                for f in range(d["frames"]):
                    subs[f"{sid}_{f}"] = (f'[sub_resource type="AtlasTexture" id="{sid}_{f}"]\natlas = ExtResource("{key}")\n'
                                          f'region = Rect2({f * fw}, 0, {fw}, {fh})\n')
                    refs.append(f'{{\n"duration": 1.0,\n"texture": SubResource("{sid}_{f}")\n}}')
                subs[f"{sid}_frames"] = (f'[sub_resource type="SpriteFrames" id="{sid}_frames"]\nanimations = [{{\n"frames": [{", ".join(refs)}],\n'
                                         f'"loop": true,\n"name": &"default",\n"speed": {d.get("fps", 5)}\n}}]\n')
            x, y = d["pos"]
            bottom = max(im.crop((f * fw, 0, (f + 1) * fw, fh)).getbbox()[3] for f in range(d["frames"]))
            n.append(f'[node name="Decor{k}" type="AnimatedSprite2D" parent="."]\nposition = Vector2({x}, {y})\n'
                     + ("z_index = -8\n" if d.get("afloat") else "") + ("flip_h = true\n" if d.get("flip") else "")
                     + f'offset = Vector2(0, {fh / 2 - bottom + 1})\nsprite_frames = SubResource("{sid}_frames")\nautoplay = "default"\n'
                     f'frame = {k * 3 % d["frames"]}\nspeed_scale = {0.8 + (k * 37 % 11) / 25:.2f}\n')
        # Scene instances placed by hand (a great tree in a square, ...).
        for k, (scene_res, (x, y), scale) in enumerate(c.get("instances", [])):
            n.append(f'[node name="Feature{k}" parent="." instance=ExtResource("{res("PackedScene", scene_res)}")]\n'
                     f'position = Vector2({x}, {y})\nscale = Vector2({scale}, {scale})\n')
            solids.append((x - 10 * scale, y - 13 * scale, x + 10 * scale, y + 7 * scale))
        # Trees and undergrowth.
        for kind in {k for k, _, _ in trees}:
            res("PackedScene", TREE_SCENES[kind])
        for k, (kind, x, y) in enumerate(trees):
            tint = f"modulate = Color{self.cfg['tree_tint']}\n" if self.cfg.get("tree_tint") and kind != "pine" else ""
            n.append(f'[node name="Tree{k}" parent="." instance=ExtResource("{tex[("PackedScene", TREE_SCENES[kind])]}")]\n'
                     f'position = Vector2({x}, {y})\n{tint}')
            solids.append((x - TREE_R[kind][0], y - 3 - TREE_R[kind][0], x + TREE_R[kind][0], y - 3 + TREE_R[kind][0]))
        solid_under = set(c.get("solid_under", ["rock", "log", "stump"]))
        utint = f"modulate = Color{c['under_tint']}\n" if c.get("under_tint") else ""
        for k, (name, x, y) in enumerate(under):
            path = FOREST + "props/" + name + ".png"
            h = Image.open(path).height
            flip = "flip_h = true\n" if (x * 7 + y) % 2 else ""
            if name in solid_under:
                solids.append((x - 11, y - 7, x + 11, y + 1))
                n.append(f'[node name="Under{k}" type="StaticBody2D" parent="."]\nposition = Vector2({x}, {y})\n\n'
                         f'[node name="Sprite" type="Sprite2D" parent="Under{k}"]\n{utint}{flip}offset = Vector2(0, {-h / 2 + 2})\n'
                         f'texture = ExtResource("{texture(path)}")\n\n'
                         f'[node name="Base" type="CollisionShape2D" parent="Under{k}"]\nposition = Vector2(0, -3)\n'
                         f'shape = SubResource("{shape(22, 8)}")\n')
            else:
                n.append(f'[node name="Under{k}" type="Sprite2D" parent="."]\nposition = Vector2({x}, {y})\n{utint}{flip}'
                         f'offset = Vector2(0, {-h / 2 + 2})\ntexture = ExtResource("{texture(path)}")\n')

        if tufts:
            for kind, strip in (("tuft", "anim/tuft_sway.png"), ("tuft_flowers", "anim/tuft_flowers_sway.png")):
                key = res("Texture2D", "res://assets/sprites/tiles/kalmora2/" + strip)
                refs = []
                for f in range(8):
                    subs[f"{kind}_{f}"] = (f'[sub_resource type="AtlasTexture" id="{kind}_{f}"]\natlas = ExtResource("{key}")\n'
                                           f'region = Rect2({f * 32}, 0, 32, 32)\n')
                    refs.append(f'{{\n"duration": 1.0,\n"texture": SubResource("{kind}_{f}")\n}}')
                subs[f"{kind}_frames"] = (f'[sub_resource type="SpriteFrames" id="{kind}_frames"]\nanimations = [{{\n"frames": [{", ".join(refs)}],\n'
                                          f'"loop": true,\n"name": &"default",\n"speed": 6\n}}]\n')
            tint = f"modulate = Color{c['tuft_tint']}\n" if c.get("tuft_tint") else ""
            for k, (kind, x, y) in enumerate(tufts):
                n.append(f'[node name="Tuft{k}" type="AnimatedSprite2D" parent="."]\nposition = Vector2({x}, {y})\n{tint}'
                         f'offset = Vector2(0, -12)\nsprite_frames = SubResource("{kind}_frames")\nautoplay = "default"\n'
                         f'frame = {k * 3 % 8}\nspeed_scale = {0.85 + (k * 37 % 11) / 30:.2f}\n')

        # Residents, readables, chests, monsters.
        quote = lambda lines: ", ".join('"' + line.replace('"', '\\"') + '"' for line in lines)
        for npc in c.get("npcs", []):
            x, y = npc["pos"]
            frames = f"res://assets/sprites/npcs/{npc['id']}/{npc['id']}_frames.tres"
            shop = ""
            if npc.get("shop"):
                shop = (f'shop_stock = Array[StringName]([{", ".join("&" + chr(34) + s + chr(34) for s in npc["shop"])}])\n'
                        f'shop_buys_cards = {"true" if npc.get("buys_cards") else "false"}\nshop_title = "{npc.get("shop_title", "")}"\n')
            n.append(f'[node name="{npc.get("node", "Npc_" + npc["id"])}" parent="." instance=ExtResource("{res("PackedScene", "res://scenes/characters/npc.tscn")}")]\n'
                     f'position = Vector2({x}, {y})\nnpc_id = &"{npc["id"]}"\ndisplay_name = "{npc["name"]}"\n'
                     f'sprite_frames = ExtResource("{res("SpriteFrames", frames)}")\n'
                     f'lines = PackedStringArray({quote(npc["lines"])})\nwander_radius = {float(npc.get("wander", 0))}\n{shop}'
                     + (f'sprite_offset_y = {npc["offset"]}\n' if "offset" in npc else ""))
        for k, (title, (x, y), lines) in enumerate(c.get("readables", [])):
            n.append(f'[node name="Read{k}" type="Node2D" parent="."]\nposition = Vector2({x}, {y})\n'
                     f'script = ExtResource("{res("Script", "res://scripts/systems/readable.gd")}")\ntitle = "{title}"\n'
                     f'lines = PackedStringArray({quote(lines)})\n')
        for ch in c.get("chests", []):
            x, y = ch["pos"]
            solids.append((x - 15, y - 10, x + 15, y))
            n.append(f'[node name="Chest_{ch["id"]}" type="StaticBody2D" parent="."]\nposition = Vector2({x}, {y})\n'
                     f'script = ExtResource("{res("Script", "res://scripts/systems/chest.gd")}")\nchest_id = &"{self.key}_{ch["id"]}"\n'
                     f'card_id = &"{ch.get("card", "")}"\ngold = {ch.get("gold", 0)}\n'
                     + (f'item_id = &"{ch["item"]}"\nitem_count = {ch.get("count", 1)}\n' if ch.get("item") else "")
                     + (f'behind_gate = &"{ch["gate"]}"\n' if ch.get("gate") else "")
                     + f'closed_texture = ExtResource("{texture(CHEST_SHUT)}")\nopen_texture = ExtResource("{texture(CHEST_OPEN)}")\n\n'
                     f'[node name="Base" type="CollisionShape2D" parent="Chest_{ch["id"]}"]\nposition = Vector2(0, -5)\n'
                     f'shape = SubResource("{shape(30, 10)}")\n')
        for k, (scene_path, (x, y)) in enumerate(c.get("monsters", [])):
            name = os.path.basename(scene_path)[:-5].title().replace("_", "")
            n.append(f'[node name="{name}{k}" parent="." instance=ExtResource("{res("PackedScene", scene_path)}")]\n'
                     f'position = Vector2({x}, {y})\n')
        for k, ((x, y), count) in enumerate(c.get("butterflies", [])):
            n.append(f'[node name="Butterflies{k}" type="Node2D" parent="."]\nposition = Vector2({x}, {y})\n'
                     f'script = ExtResource("{res("Script", "res://scripts/world/butterflies.gd")}")\ncount = {count}\nseed = {k + 3}\n\n'
                     f'[node name="Fireflies{k}" type="Node2D" parent="."]\nposition = Vector2({x}, {y})\n'
                     f'script = ExtResource("{res("Script", "res://scripts/world/fireflies.gd")}")\ncount = {count * 3}\nseed = {k + 9}\n')
        if c.get("snowfall"):
            n.append(f'[node name="Snowfall" type="Node2D" parent="."]\nz_index = 20\n'
                     f'script = ExtResource("{res("Script", "res://scripts/world/snowfall.gd")}")\n')

        # Reachability: everything that matters can be walked to from the entry.
        errors = self.reach_errors(walls, solids, c["entry"], targets)
        if errors:
            self.debug(ground, walls, solids)
            raise SystemExit(f"{self.key}:\n  " + "\n  ".join(errors))

        entry = c["entry"]
        n.append(f'''[node name="Player" parent="." instance=ExtResource("2_player")]
position = Vector2({entry[0]}, {entry[1]})

[node name="HUD" parent="." instance=ExtResource("3_hud")]

[node name="Binder" parent="." instance=ExtResource("4_binder")]

[node name="ShopPanel" parent="." instance=ExtResource("5_shop")]

[node name="DialogueBox" parent="." instance=ExtResource("6_dialogue")]
''')
        head = f'[gd_scene load_steps={len(ext) + len(subs) + 1} format=3]\n\n'
        head += "".join(f'[ext_resource type="{t}" path="{p}" id="{i}"]\n' for t, p, i in ext) + "\n"
        head += "\n".join(subs.values()) + "\n"
        open(c["scene"], "w", encoding="utf-8", newline="\n").write(head + "\n".join(n))
        print(f"{self.key}: {self.cols}x{self.rows} cells, {len(trees)} trees, {len(under)} undergrowth, "
              f"{len(walls)} wall rects, {len(self.stairs)} stairs")

    @staticmethod
    def _cut(rects, at, gap, horizontal):
        out = []
        for a, b, c2, d in rects:
            if horizontal:
                if a < at - gap:
                    out.append((a, b, at - gap, d))
                if c2 > at + gap:
                    out.append((at + gap, b, c2, d))
            else:
                if b < at - gap:
                    out.append((a, b, c2, at - gap))
                if d > at + gap:
                    out.append((a, at + gap, c2, d))
        return out

    def reach_errors(self, walls, solids, start, targets, step=8, body=6):
        w, h = self.W // step, self.H // step
        grid = np.zeros((h, w), bool)
        for x0, y0, x1, y1 in list(walls) + list(solids):
            gx0, gy0 = max(0, math.ceil((x0 - body - self.x0) / step - 0.5)), max(0, math.ceil((y0 - body - self.y0) / step - 0.5))
            gx1, gy1 = min(w, math.floor((x1 + body - self.x0) / step - 0.5) + 1), min(h, math.floor((y1 + body - self.y0) / step - 0.5) + 1)
            if gx1 > gx0 and gy1 > gy0:
                grid[gy0:gy1, gx0:gx1] = True
        # Stairs cells stay open (their wall rect was never added).
        seen = np.zeros_like(grid)
        sx, sy = int((start[0] - self.x0) // step), int((start[1] - self.y0) // step)
        sx, sy = min(max(sx, 0), w - 1), min(max(sy, 0), h - 1)
        if grid[sy, sx]:
            return [f"the entry at {start} is blocked"]
        stack = [(sy, sx)]
        seen[sy, sx] = True
        while stack:
            y, x = stack.pop()
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and not grid[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    stack.append((ny, nx))
        self.seen = seen
        bad = []
        for name, (x, y) in targets.items():
            gx, gy = int((x - self.x0) // step), int((y - self.y0) // step)
            gx, gy = min(max(gx, 0), w - 1), min(max(gy, 0), h - 1)
            if not seen[max(0, gy - 4):gy + 5, max(0, gx - 4):gx + 5].any():
                bad.append(f"{name} at ({round(x)}, {round(y)}) can't be reached on foot")
        return bad

    def debug(self, ground, walls, solids):
        img = ground.convert("RGBA")
        over = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(over)
        for x0, y0, x1, y1 in list(walls) + list(solids):
            d.rectangle((x0 - self.x0, y0 - self.y0, x1 - self.x0 - 1, y1 - self.y0 - 1), fill=(255, 0, 0, 80))
        if hasattr(self, "seen"):
            ys, xs = np.nonzero(self.seen)
            for y, x in zip(ys[::2], xs[::2]):
                d.rectangle((x * 8 + 3, y * 8 + 3, x * 8 + 4, y * 8 + 4), fill=(0, 255, 0, 255))
        out = os.environ.get("REGION_DEBUG", os.path.join(os.environ.get("TEMP", "/tmp"), f"{self.key}_debug.png"))
        Image.alpha_composite(img, over).save(out)
        print("debug view:", out)


def window_glow(path, night_dir):
    """The lit-window overlay for a building: the warm window panes painted on the sprite
    (bright, compact blobs), brightened. None if the sprite has no lit windows."""
    a = np.array(Image.open(path).convert("RGBA")).astype(int)
    r, g, b, al = (a[..., i] for i in range(4))
    lit = (al > 200) & (r > 185) & (g > 145) & (b < 170) & (r - b > 45) & (r - g < 75)
    lab, _ = ndimage.label(ndimage.binary_dilation(lit, iterations=1))
    keep = np.zeros_like(lit)
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        blob = (lab[sl] == i) & lit[sl]
        if 3 <= blob.sum() <= 220 and h <= 26 and w <= 26 and blob.sum() >= 0.22 * h * w:
            keep[sl] |= blob
    if not keep.any():
        return None
    out = np.zeros_like(a)
    out[keep] = (255, 214, 130, 240)
    os.makedirs(night_dir, exist_ok=True)
    dst = night_dir + os.path.basename(path)[:-4] + "_windows.png"
    Image.fromarray(out.astype(np.uint8)).save(dst)
    return dst


if __name__ == "__main__":
    for key in sys.argv[1:] or list(RL.ZONES):
        Zone(key).build()
