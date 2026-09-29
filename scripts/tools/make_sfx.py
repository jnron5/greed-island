"""Synthesises the game's sound effects (placeholder-quality but real, soft and
retro, to suit the pixel art) into assets/audio/sfx/*.wav. No samples are used:
every sound is built from noise and tones with envelopes here.
Run: python scripts/tools/make_sfx.py
"""
import math
import os
import wave

import numpy as np

os.chdir(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = "assets/audio/sfx/"
RATE = 22050
rng = np.random.default_rng(3)


def t_(sec):
    return np.arange(int(RATE * sec)) / RATE


def env(n, attack=0.005, decay=0.2, sustain=0.0, curve=3.0):
    t = np.arange(n) / RATE
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    d = np.exp(-np.maximum(t - attack, 0) / max(decay, 1e-4) * curve / 3.0)
    return a * (sustain + (1 - sustain) * d)


def lowpass(x, k):
    """A cheap one-pole low-pass (k 0..1, lower = darker)."""
    y = np.zeros_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += k * (v - acc)
        y[i] = acc
    return y


def tone(freq, sec, shape="sine"):
    t = t_(sec)
    ph = 2 * math.pi * np.cumsum(np.broadcast_to(freq, t.shape)) / RATE
    if shape == "square":
        return np.sign(np.sin(ph)) * 0.6
    if shape == "tri":
        return 2 / math.pi * np.arcsin(np.sin(ph))
    return np.sin(ph)


def noise(sec):
    return rng.uniform(-1, 1, int(RATE * sec))


def save(name, x, gain=0.7):
    x = np.asarray(x, np.float64)
    x = x / (np.abs(x).max() or 1) * gain
    fade = min(len(x), 200)
    x[-fade:] *= np.linspace(1, 0, fade)
    data = (x * 32767).astype(np.int16)
    with wave.open(OUT + name + ".wav", "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(data.tobytes())


def sweep(f0, f1, sec, shape="sine"):
    return tone(np.linspace(f0, f1, int(RATE * sec)), sec, shape)


def main():
    os.makedirs(OUT, exist_ok=True)
    # Sword: a quick airy swish, filtered noise that brightens then fades.
    n = noise(0.18)
    save("sword", lowpass(n, 0.35) * env(len(n), 0.03, 0.08) + lowpass(n, 0.8) * env(len(n), 0.05, 0.04) * 0.4, 0.5)
    # Pistol: a sharp crack and a short low thump.
    n = noise(0.22)
    save("pistol", lowpass(n, 0.9) * env(len(n), 0.001, 0.03) + sweep(160, 50, 0.22) * env(len(n), 0.001, 0.08) * 0.9, 0.6)
    # Hit (you landing a blow): a dull thud with a click on top.
    n = noise(0.12)
    save("hit", sweep(220, 70, 0.12) * env(len(n), 0.001, 0.05) + lowpass(n, 0.5) * env(len(n), 0.001, 0.015) * 0.5, 0.6)
    # Hurt (you taking one): a lower, rougher thump.
    n = noise(0.2)
    save("hurt", sweep(140, 45, 0.2, "tri") * env(len(n), 0.001, 0.09) + lowpass(n, 0.25) * env(len(n), 0.001, 0.05) * 0.7, 0.6)
    # Dash: a soft whoosh that rises.
    n = noise(0.22)
    save("dash", lowpass(n, 0.2) * env(len(n), 0.06, 0.08) * (0.6 + 0.4 * np.linspace(0, 1, len(n))), 0.4)
    # Chest: a wooden creak and a thunk.
    c = sweep(300, 180, 0.25, "tri") * (0.5 + 0.5 * np.sin(t_(0.25) * 2 * math.pi * 23)) * env(int(RATE * 0.25), 0.02, 0.2)
    th = sweep(120, 60, 0.12) * env(int(RATE * 0.12), 0.001, 0.05)
    save("chest", np.concatenate([c, th]), 0.55)
    # Coins: two bright little pings.
    p1 = tone(1760, 0.12) * env(int(RATE * 0.12), 0.001, 0.06) + tone(2637, 0.12) * env(int(RATE * 0.12), 0.001, 0.04) * 0.4
    save("coins", np.concatenate([p1, np.zeros(int(RATE * 0.04)), p1 * 0.8]), 0.4)
    # Card: a small rising three-note fanfare (a new card in hand).
    notes = []
    for f in (784, 988, 1319):
        s = 0.11 if f != 1319 else 0.3
        notes.append((tone(f, s, "tri") + tone(f * 2, s) * 0.25) * env(int(RATE * s), 0.005, 0.12 if f != 1319 else 0.25))
    save("card", np.concatenate(notes), 0.45)
    # Gate: a deep stone scrape and a low chime.
    n = noise(0.6)
    save("gate", lowpass(n, 0.06) * env(len(n), 0.08, 0.4, 0.2) + tone(196, 0.6, "tri") * env(len(n), 0.2, 0.4) * 0.5, 0.5)
    # UI: a soft click and a softer tick.
    save("ui_click", tone(880, 0.05, "tri") * env(int(RATE * 0.05), 0.001, 0.02), 0.3)
    save("ui_tick", tone(1320, 0.03) * env(int(RATE * 0.03), 0.001, 0.012), 0.2)
    # Talk: the soft blip under typing dialogue.
    save("talk", tone(620, 0.03, "square") * env(int(RATE * 0.03), 0.001, 0.015), 0.12)
    # Heal: a gentle rising shimmer.
    s = sweep(520, 1040, 0.4, "tri") * env(int(RATE * 0.4), 0.05, 0.3)
    save("heal", s + tone(1560, 0.4) * env(int(RATE * 0.4), 0.15, 0.2) * 0.3, 0.35)
    # Monster down: a short falling grunt.
    save("monster_down", sweep(260, 60, 0.3, "square") * env(int(RATE * 0.3), 0.005, 0.15) * 0.5
         + lowpass(noise(0.3), 0.2) * env(int(RATE * 0.3), 0.005, 0.1), 0.45)
    # Footsteps on dirt (two variants), very quiet.
    for k in (1, 2):
        n = noise(0.07)
        save(f"step{k}", lowpass(n, 0.12 + 0.05 * k) * env(len(n), 0.002, 0.025), 0.15)
    # Door: a latch and a soft swing.
    save("door", np.concatenate([tone(700, 0.03, "square") * env(int(RATE * 0.03), 0.001, 0.01),
                                 sweep(240, 160, 0.3, "tri") * env(int(RATE * 0.3), 0.03, 0.2) * 0.6]), 0.4)
    # Roar: a big beast noticing you: a growling low sweep with rough noise.
    n = noise(0.9)
    growl = sweep(110, 70, 0.9, "square") * (0.6 + 0.4 * np.sin(t_(0.9) * 2 * math.pi * 31))
    save("roar", (growl * 0.6 + lowpass(n, 0.12) * 0.8) * env(len(n), 0.08, 0.5, 0.3), 0.6)
    # Steal: a sly little two-note flick.
    save("steal", np.concatenate([tone(1175, 0.06) * env(int(RATE * 0.06), 0.001, 0.03),
                                  tone(880, 0.1) * env(int(RATE * 0.1), 0.001, 0.05)]), 0.35)
    print("sfx:", sorted(f[:-4] for f in os.listdir(OUT) if f.endswith(".wav")))


if __name__ == "__main__":
    main()
