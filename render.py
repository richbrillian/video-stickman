# -*- coding: utf-8 -*-
"""Render cerita/*.json -> video/<nama>.mp4 (720x1280, 24 fps). Dijalankan GitHub Actions."""
import glob, io, json, math, os, subprocess, sys, tempfile, urllib.request, wave
import numpy as np
from PIL import Image

import mesin as M
import musik

FPS = 24
MIN_DETIK = 15.0
SR = musik.SR


# ------------------------------------------------------------- suara
def tts_eleven(teks, voice_id, out):
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        return False
    try:
        req = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=mp3_44100_128",
            data=json.dumps({"text": teks, "model_id": "eleven_multilingual_v2",
                             "voice_settings": {"stability": 0.4, "similarity_boost": 0.8, "style": 0.35}}).encode(),
            headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg"})
        with urllib.request.urlopen(req, timeout=90) as r, open(out, "wb") as f:
            f.write(r.read())
        return os.path.getsize(out) > 2000
    except Exception as e:
        print("ElevenLabs gagal, pakai edge-tts:", e)
        return False


def tts_edge(teks, voice, out):
    r = subprocess.run([sys.executable, "-m", "edge_tts", "--voice", voice, "--rate=+4%", "--text", teks,
                        "--write-media", out], capture_output=True, text=True)
    return r.returncode == 0 and os.path.exists(out) and os.path.getsize(out) > 1000


def suara(teks, cerita, out_wav, tmp, idx):
    mp3 = os.path.join(tmp, f"s{idx}.mp3")
    ok = False
    if os.environ.get("TTS_PALSU") != "1":
        voice_id = cerita.get("suara_eleven") or os.environ.get("ELEVENLABS_VOICE_ID") or "EXAVITQu4vr4xnSDxMaL"
        ok = tts_eleven(teks, voice_id, mp3) or tts_edge(teks, cerita.get("suara", "id-ID-GadisNeural"), mp3)
    if ok:
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp3, "-ar", str(SR), "-ac", "1", out_wav], check=True)
    else:  # senyap sebanding jumlah kata (uji lokal / cadangan)
        n = int(max(1.5, len(teks.split()) * 0.38) * SR)
        with wave.open(out_wav, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(b"\0\0" * n)
    with wave.open(out_wav) as w:
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    return data


# ------------------------------------------------------------- foto produk
def muat_foto(sumber, folder):
    if not sumber:
        return None
    try:
        if sumber.startswith("http"):
            req = urllib.request.Request(sumber, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=40) as r:
                return Image.open(io.BytesIO(r.read())).convert("RGB")
        p = sumber if os.path.exists(sumber) else os.path.join(folder, sumber)
        return Image.open(p).convert("RGB")
    except Exception as e:
        print("Foto produk tidak terbaca, pakai ikon:", e)
        return None


# ------------------------------------------------------------- adegan
POS = {"kiri": 175, "tengah": 360, "kanan": 545}


def gambar_adegan(ad, cerita, t, dur_bicara, kartu, thumb, judul_layar=None, dur=5.0):
    K = M.Kanvas()
    tata = ad.get("tata", "penuh")
    tokoh_list = ad.get("tokoh", [])
    jalan = any(tk.get("aksi") in ("jalan", "jalan_masuk") for tk in tokoh_list) or ad.get("geser")
    M.GESER[0] = t * 140 if jalan else 0.0
    M.latar(K, ad.get("latar", "kota"), t)
    tokoh_def = cerita.get("tokoh", {})
    n_tok = len(tokoh_list)
    k_in = min(t / 0.35, 1); k_in = 1 - (1 - k_in) ** 3

    if tata == "penuh":  # stickman penuh, produk goyang pelan di tengah
        if kartu is not None:
            K.tempel(M.rotasi(kartu, math.sin(t * 1.8) * 4, max(0.40 * k_in, 0.05)), 360, 470 + math.sin(t * 2.2) * 8)
        skala = 1.35
    elif tata == "atas_produk":  # produk di atas, stickman di bawah
        if kartu is not None:
            K.tempel(M.rotasi(kartu, math.sin(t * 2) * 2, max(0.6 * k_in, 0.05)), 360, 250 + math.sin(t * 2.5) * 4)
        M.banner_harga(K, ad.get("harga", ""), ad.get("coret", ""), t)
        skala = 1.0
    else:  # goyang: stickman + produk goyang sedikit
        if kartu is not None:
            sk = (0.42 if ad.get("efek") == "panah" else 0.5) * (1 + 0.02 * math.sin(t * 5)) * (0.6 + 0.4 * k_in)
            K.tempel(M.rotasi(kartu, math.sin(t * 3.5) * 3, sk), 360, (235 if ad.get("efek") == "panah" else 260) + math.sin(t * 3) * 5)
        skala = 1.0 if (ad.get("chat") or ad.get("efek")) else 1.1
        if ad.get("chat"):
            M.bubble_chat(K, ad["chat"], t, 440)

    bicara_aktif = 0.25 < t < 0.25 + dur_bicara
    for tk in tokoh_list:
        cfg = tokoh_def.get(tk["nama"], {})
        pos = tk.get("posisi", "tengah")
        x = POS[pos]
        d = 1 if pos in ("kiri", "tengah") else -1
        if n_tok >= 2:
            d = 1 if x < 360 else -1
        aksi = tk.get("aksi", "diam")
        tt = t
        if aksi == "jalan_masuk":
            kk = min(t / 1.4, 1)
            x += -(1 - kk) * 460 * d
            if kk < 1:
                aksi = "jalan"
            else:
                aksi = tk.get("lalu", "diam"); tt = t - 1.4
        elif aksi == "pergi":
            x += -d * t * 260; d = -d; aksi = "jalan"
        M.tokoh(K, cfg, x, aksi, tt, d, tk.get("bawa"), skala, thumb, M.GY,
                bicara=bool(tk.get("bicara")) and bicara_aktif)

    if ad.get("efek"):
        M.efek_layar(K, ad["efek"], t)
    if judul_layar:
        kata, baris, cur = judul_layar.split(), [], []
        for w in kata:
            if K.lebar_teks(" ".join(cur + [w]), 46) > 600 and cur:
                baris.append(" ".join(cur)); cur = [w]
            else:
                cur.append(w)
        baris.append(" ".join(cur))
        h = 70 * len(baris) + 30
        yo = -(1 - min(t / 0.3, 1)) * 300
        K.kotak((30, 70 + yo, 690, 70 + h + yo), 30, fill="#ffd21f", outline="white", w=5)
        for j, b in enumerate(baris):
            K.teks((360, 120 + j * 70 + yo), b, 46, "#3b2300")
    M.keterangan(K, ad.get("teks", ""), t, dur_bicara)
    img = K.hasil()
    # kamera: zoom pelan + sedikit geser, hentakan saat kaget
    z = 1.0 + 0.06 * (t / max(dur, 0.1))
    if any(tk.get("aksi") in ("kaget", "panik") for tk in tokoh_list) and t < 0.5:
        z += 0.03 * math.sin(t * 40)
    if z > 1.001:
        cw, chh = M.W / z, M.H / z
        ox = (M.W - cw) / 2 + math.sin(t * 0.7) * 6
        oy = (M.H - chh) * 0.85
        img = img.crop((ox, oy, ox + cw, oy + chh)).resize((M.W, M.H), Image.BILINEAR)
    if t < 0.15:
        img = Image.blend(Image.new("RGB", img.size, "white"), img, 0.5 + t / 0.15 * 0.5)
    return img


# ------------------------------------------------------------- utama
def render(path_json, out_mp4):
    folder = os.path.dirname(path_json)
    cerita = json.load(open(path_json, encoding="utf-8"))
    adegan = cerita["adegan"]
    foto = muat_foto(cerita.get("produk_foto"), folder)
    ikon = cerita.get("produk_ikon", "kotak")
    label = cerita.get("produk_label", "PRODUK")
    kartu, thumb = (None, None)
    if cerita.get("produk_foto") is not None or "produk_ikon" in cerita:
        kartu, thumb = M.siapkan_produk(foto, ikon, label)

    with tempfile.TemporaryDirectory() as tmp:
        suaras = [suara(a.get("teks", ""), cerita, os.path.join(tmp, f"s{i}.wav"), tmp, i) for i, a in enumerate(adegan)]
        jeda_awal, jeda_akhir = 0.3, 0.55
        durs = [max(len(s) / SR + jeda_awal + jeda_akhir, a.get("min", 3.0)) for s, a in zip(suaras, adegan)]
        kurang = MIN_DETIK - sum(durs)
        if kurang > 0:
            durs[-1] += kurang
        total = sum(durs)

        suara_all = np.zeros(int((total + 1) * SR), dtype=np.float32)
        pos = 0.0
        for s, d in zip(suaras, durs):
            a = int((pos + jeda_awal) * SR)
            suara_all[a:a + len(s)] += s
            pos += d
        mus = musik.buat(cerita.get("musik", "ceria"), total + 1)
        campur = suara_all[:len(mus)] + mus * 0.16
        campur = campur / max(1.0, float(np.max(np.abs(campur))) / 0.95)
        wav = os.path.join(tmp, "mix.wav")
        with wave.open(wav, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((campur * 32767).astype(np.int16).tobytes())

        os.makedirs(os.path.dirname(out_mp4) or ".", exist_ok=True)
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                               "-s", f"{M.W}x{M.H}", "-r", str(FPS), "-i", "-", "-i", wav,
                               "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p",
                               "-c:a", "aac", "-b:a", "128k", "-t", f"{total:.2f}", "-movflags", "+faststart", out_mp4],
                              stdin=subprocess.PIPE)
        for i, (a, d) in enumerate(zip(adegan, durs)):
            dur_bicara = len(suaras[i]) / SR
            judul = cerita.get("judul_layar") if i == 0 else None
            for f in range(int(round(d * FPS))):
                img = gambar_adegan(a, cerita, f / FPS, dur_bicara, kartu, thumb, judul, d)
                ff.stdin.write(img.tobytes())
        ff.stdin.close()
        ff.wait()
    print(f"selesai {out_mp4} ({total:.1f} dtk)")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    semua = "--semua" in sys.argv
    files = [a for a in args] or sorted(glob.glob("cerita/*.json"))
    for f in files:
        nama = os.path.splitext(os.path.basename(f))[0]
        out = os.path.join("video", nama + ".mp4")
        if os.path.exists(out) and not semua and not args:
            continue
        render(f, out)


if __name__ == "__main__":
    main()
