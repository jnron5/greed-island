"""Thornveil's water, as frame animations (never shader warping):

- lake.png: Kalmora's PixelLab-animated wave tile, recoloured to a calm forest lake:
  the concept's clear blue, the whitecaps softened to pale glints (a lake doesn't
  break like the sea).
- stream_flow.png: a PixelLab stream tile (water/stream_tile.png, fine ripple lines
  running downstream), made seamless and moved one step downstream per frame, so the
  streams visibly flow.
- fall_flow.png: a PixelLab falling-water tile (water/fall_tile.png, ribbons of white
  and blue), made seamless and dropped a quarter tile per frame: water pouring down.

All three share one palette so the streams run into the lake and over the falls
without a seam in colour. Each strip is FRAMES tiles side by side.
Run: python scripts/tools/make_forest_water.py (build_thornveil.py uses the output).
"""
import os

import numpy as np
from PIL import Image

os.chdir(os.path.join(os.path.dirname(__file__), "..", ".."))
D = "assets/sprites/tiles/thornveil/water/"
BAY = "assets/sprites/tiles/kalmora2/anim/bay_water.png"
FRAMES = 8
# The forest water ramp, dark to light (by brightness).
RAMP = np.array([(18, 46, 110), (24, 72, 160), (36, 104, 200), (64, 142, 224), (130, 196, 240), (210, 236, 252)], np.float32)


def ramp(lum):
    """Maps brightness 0..1 onto the forest water ramp."""
    t = np.clip(lum, 0, 1) * (len(RAMP) - 1)
    i = np.floor(t).astype(int).clip(0, len(RAMP) - 2)
    f = (t - i)[..., None]
    return RAMP[i] * (1 - f) + RAMP[i + 1] * f


def quantise(rgb, levels=10):
    """Snap to a small set of shades, so the result stays crisp pixel art."""
    lum = rgb.mean(axis=-1) / 255.0
    return ramp(np.round(lum * levels) / levels)


def trimmed(path):
    """The tile without the 1-2px frame PixelLab's candidates come with."""
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.float32)
    return a[2:-2, 2:-2]


def seamless(a, band=8):
    """Blend each edge with the opposite one so the tile wraps without a seam."""
    h, w = a.shape[:2]
    out = a.copy()
    for k in range(band):
        t = 0.5 * (1 - k / band)
        out[k] = a[k] * (1 - t) + a[h - 1 - k] * t
        out[h - 1 - k] = a[h - 1 - k] * (1 - t) + a[k] * t
    b = out.copy()
    for k in range(band):
        t = 0.5 * (1 - k / band)
        out[:, k] = b[:, k] * (1 - t) + b[:, w - 1 - k] * t
        out[:, w - 1 - k] = b[:, w - 1 - k] * (1 - t) + b[:, k] * t
    return out


def flow_strip(tile, lum_scale, lum_bias):
    """FRAMES frames of `tile` sliding down by an even step each frame (one full tile
    per loop), recoloured to the forest ramp."""
    h = tile.shape[0]
    frames = []
    for f in range(FRAMES):
        shifted = np.roll(tile, round(f * h / FRAMES), axis=0)
        lum = shifted.mean(axis=-1) / 255.0 * lum_scale + lum_bias
        frames.append(ramp(np.round(np.clip(lum, 0, 1) * 10) / 10))
    return np.concatenate(frames, axis=1)


def main():
    os.makedirs(D, exist_ok=True)
    # Lake: the sea's rolling tile, dimmed and tinted; its brightest foam becomes soft glints.
    bay = np.asarray(Image.open(BAY).convert("RGB")).astype(np.float32)
    lum = bay.mean(axis=-1) / 255.0
    lum = np.where(lum > 0.7, 0.78 + (lum - 0.7) * 0.4, lum * 0.75 + 0.24)
    lake = ramp(np.round(lum * 10) / 10)
    Image.fromarray(lake.clip(0, 255).astype(np.uint8)).save(D + "lake.png")
    # Streams: bright, shallow water, the ripple lines lighter than the lake.
    stream = seamless(trimmed(D + "stream_tile.png"))
    Image.fromarray(flow_strip(stream, 0.9, 0.12).clip(0, 255).astype(np.uint8)).save(D + "stream_flow.png")
    # Falls: pale and bright, mostly foam-white ribbons over blue.
    fall = seamless(trimmed(D + "fall_tile.png"))
    Image.fromarray(flow_strip(fall, 1.0, 0.05).clip(0, 255).astype(np.uint8)).save(D + "fall_flow.png")
    for n in ("lake", "stream_flow", "fall_flow"):
        print(n, Image.open(D + n + ".png").size)


if __name__ == "__main__":
    main()
