"""Synthesises looping ambient beds into assets/audio/ambience/*.wav (seamless: each
loop is built so its end runs into its start). Soft, low in the mix, placeholder
until real field recordings or composed audio exist.
  harbor: surf rolling in and out, now and then a gull.
  forest_day: wind in the leaves and birdsong.
  forest_night: crickets and a slow breeze.
  cave: a low hollow hum and water dripping.
  room: a quiet indoor hush with a crackling hearth.
Run: python scripts/tools/make_ambience.py
"""
import math
import os
import wave

import numpy as np

os.chdir(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = "assets/audio/ambience/"
RATE = 22050
SECONDS = 24
N = RATE * SECONDS
rng = np.random.default_rng(11)
T = np.arange(N) / RATE


def lowpass(x, k):
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += k * (x[i] - acc)
        y[i] = acc
    return y


def looped_noise(k, fade=RATE):
    """Low-passed noise exactly N samples long that loops without a seam: made
    `fade` longer, and that extra tail is crossfaded into the start."""
    x = lowpass(rng.uniform(-1, 1, N + fade + RATE), k)[RATE:]    # skip the filter's warm-up
    ramp = np.linspace(0, 1, fade)
    out = x[:N].copy()
    out[:fade] = x[N:N + fade] * (1 - ramp) + x[:fade] * ramp
    return out


def slow(period_s, phase=0.0):
    """A slow sine that completes a whole number of cycles in the loop."""
    cycles = max(1, round(SECONDS / period_s))
    return np.sin(2 * math.pi * cycles * T / SECONDS + phase)


def chirp(at, f0, f1, dur, amp):
    n = int(dur * RATE)
    t = np.arange(n) / RATE
    f = np.linspace(f0, f1, n)
    s = np.sin(2 * math.pi * np.cumsum(f) / RATE) * np.sin(math.pi * t / dur) ** 2 * amp
    out = np.zeros(N)
    i = int(at * RATE) % N
    end = min(N, i + n)
    out[i:end] += s[:end - i]
    if i + n > N:
        out[:i + n - N] += s[end - i:]
    return out


def save(name, x, gain):
    x = x / (np.abs(x).max() or 1) * gain
    with wave.open(OUT + name + ".wav", "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def main():
    os.makedirs(OUT, exist_ok=True)
    # Harbor: surf that swells every ~6s, a low wash under it, and gulls.
    surf = looped_noise(0.08) * (0.45 + 0.55 * np.clip(slow(6.0), 0, 1) ** 2)
    wash = looped_noise(0.02) * 0.6
    gulls = sum(chirp(t0, 1900, 1300, 0.28, 0.08) + chirp(t0 + 0.35, 2000, 1400, 0.22, 0.06)
                for t0 in (3.1, 13.7, 19.4))
    save("harbor", surf + wash + gulls, 0.35)
    # Forest by day: leaves in the wind and birds.
    wind = looped_noise(0.05) * (0.5 + 0.5 * (slow(9.0) * 0.5 + 0.5))
    birds = np.zeros(N)
    for _ in range(26):
        t0 = rng.uniform(0, SECONDS)
        f = rng.uniform(2400, 4200)
        for k in range(rng.integers(2, 5)):
            birds += chirp(t0 + k * 0.13, f, f * rng.uniform(0.8, 1.25), 0.09, 0.05)
    save("forest_day", wind * 0.8 + birds, 0.3)
    # Forest at night: crickets (a fast pulsing tone) and a slow breeze.
    pulse = (np.sin(2 * math.pi * 30 * T) > 0.2).astype(float) * (np.sin(2 * math.pi * 0.5 * T) > -0.3)
    crickets = np.sin(2 * math.pi * 4400 * T) * pulse * 0.05 + np.sin(2 * math.pi * 3900 * T + 1) * np.roll(pulse, 3000) * 0.035
    save("forest_night", looped_noise(0.03) * 0.5 + crickets, 0.25)
    # Cave: a low hum and drips.
    hum = np.sin(2 * math.pi * 55 * T) * 0.2 + np.sin(2 * math.pi * 82.5 * T) * 0.1 + looped_noise(0.01) * 0.5
    drips = sum(chirp(rng.uniform(0, SECONDS), 1400, 700, 0.06, 0.25) for _ in range(9))
    save("cave", hum + drips, 0.3)
    # Room: a hush and a crackling hearth.
    crackle = np.zeros(N)
    for _ in range(420):
        i = rng.integers(0, N - 60)
        crackle[i:i + 30] += rng.uniform(-1, 1, 30) * np.exp(-np.arange(30) / 6) * rng.uniform(0.05, 0.3)
    save("room", looped_noise(0.015) * 0.3 + crackle, 0.2)
    # Meadow (the Aurewind Plains, Verdana): grass hissing in long gusts and skylarks.
    gusts = looped_noise(0.09) * (0.35 + 0.65 * np.clip(slow(7.0) * 0.6 + slow(3.0, 1.0) * 0.4, 0, 1))
    larks = np.zeros(N)
    for _ in range(14):
        t0 = rng.uniform(0, SECONDS)
        for k in range(rng.integers(6, 12)):
            f = rng.uniform(3000, 5200)
            larks += chirp(t0 + k * 0.07, f, f * rng.uniform(0.9, 1.3), 0.05, 0.035)
    save("meadow", gusts * 0.7 + larks, 0.28)
    # Lake: slow lapping at the shore, a low breeze, a few water birds.
    lap = looped_noise(0.04) * (0.4 + 0.6 * np.clip(slow(3.0), 0, 1) ** 3)
    calls = sum(chirp(t0, 900, 700, 0.35, 0.06) + chirp(t0 + 0.45, 950, 650, 0.3, 0.05) for t0 in (4.2, 15.8))
    save("lake", lap + looped_noise(0.015) * 0.4 + calls, 0.3)
    # Mountain: wind moaning over the ridges (a slow whistling tone riding the gusts).
    gust = np.clip(slow(8.0) * 0.5 + slow(3.4, 2.0) * 0.3 + 0.5, 0, 1)
    moan = np.sin(2 * math.pi * np.cumsum(420 + 90 * slow(8.0)) / RATE) * gust ** 2 * 0.06
    save("mountain", looped_noise(0.06) * (0.3 + 0.7 * gust) + moan, 0.3)
    print("ambience:", sorted(os.listdir(OUT)))


if __name__ == "__main__":
    main()
