# -*- coding: utf-8 -*-
"""Musik latar sederhana (numpy). Pelan, dipakai sebagai latar di bawah suara."""
import numpy as np

SR = 44100


def frek(n):  # n = nomor MIDI
    return 440.0 * 2 ** ((n - 69) / 12)


def nada(f, dur, vol=0.3, jenis="pluck"):
    t = np.arange(int(dur * SR)) / SR
    if jenis == "pad":
        env = np.minimum(t / 0.3, 1) * np.exp(-t / (dur * 1.6))
        w = np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.003 * t)
    else:
        env = np.exp(-t * 5.5) * np.minimum(t / 0.01, 1)
        w = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * f * 2 * t) + 0.12 * np.sin(2 * np.pi * f * 3 * t)
    return (w * env * vol).astype(np.float32)


MOOD = {
    "ceria": dict(bpm=112, akor=[(60, 64, 67), (55, 59, 62), (57, 60, 64), (53, 57, 60)], pola=[0, 1, 2, 1, 2, 1, 0, 1]),
    "romantis": dict(bpm=76, akor=[(60, 64, 67), (57, 60, 64), (53, 57, 60), (55, 59, 62)], pola=[0, 1, 2, 1]),
    "sedih": dict(bpm=66, akor=[(57, 60, 64), (53, 57, 60), (48, 52, 55), (52, 55, 59)], pola=[0, 1, 2, 1]),
    "tegang": dict(bpm=124, akor=[(57, 60, 63), (57, 60, 63), (56, 59, 62), (55, 58, 62)], pola=[0, 0, 1, 0, 2, 0, 1, 0]),
}


def buat(mood, durasi):
    n = int(durasi * SR)
    out = np.zeros(n + SR, dtype=np.float32)
    if mood in (None, "tanpa") or mood not in MOOD:
        return out[:n]
    m = MOOD[mood]
    beat = 60.0 / m["bpm"]
    langkah = beat / 2
    i = 0
    t0 = 0.0
    while t0 < durasi:
        akor = m["akor"][(int(t0 / (beat * 4))) % len(m["akor"])]
        if i % 8 == 0:
            for nt in akor:
                s = nada(frek(nt - 12), beat * 4, 0.10, "pad")
                a = int(t0 * SR); out[a:a + len(s)] += s[:len(out) - a]
            s = nada(frek(akor[0] - 24), beat * 1.5, 0.22)
            a = int(t0 * SR); out[a:a + len(s)] += s[:len(out) - a]
        nt = akor[m["pola"][i % len(m["pola"])]] + (12 if mood != "tegang" else 0)
        s = nada(frek(nt), langkah * 1.8, 0.20)
        a = int(t0 * SR); out[a:a + len(s)] += s[:len(out) - a]
        i += 1
        t0 += langkah
    out = out[:n]
    fade = min(int(1.5 * SR), n // 2)
    out[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)
    mx = float(np.max(np.abs(out)) or 1)
    return out / mx * 0.5
