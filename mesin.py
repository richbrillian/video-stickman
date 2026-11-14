# -*- coding: utf-8 -*-
"""Mesin animasi stickman 9:16 (PIL). Dipakai oleh render.py."""
import math, random, os
from PIL import Image, ImageDraw, ImageFont, ImageColor

W, H, SS = 720, 1280, 2
GY = 950  # garis tanah

_FONTS = {}
_FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
]


def font(sz):
    sz = int(sz * SS)
    if sz not in _FONTS:
        for p in _FONT_PATHS:
            if os.path.exists(p):
                _FONTS[sz] = ImageFont.truetype(p, sz)
                break
        else:
            _FONTS[sz] = ImageFont.load_default()
    return _FONTS[sz]


WARNA = {
    "biru": "#2f6fe0", "merah": "#e03a3a", "merah muda": "#f27aa6", "hijau": "#2fae5f",
    "kuning": "#f2c230", "ungu": "#8e5ad6", "oranye": "#f28a2e", "hitam": "#333333",
    "putih": "#f4f4f4", "coklat": "#8a5a36", "abu": "#8d949e", "pirang": "#e8c25a",
}
INK = "#262626"


def warna(n, default="#2f6fe0"):
    return WARNA.get(n, n if isinstance(n, str) and n.startswith("#") else default)


class Kanvas:
    """Kanvas dengan supersampling; semua koordinat dalam piksel logis."""

    def __init__(self, w=W, h=H, rgba=False):
        self.w, self.h = w, h
        self.im = Image.new("RGBA" if rgba else "RGB", (w * SS, h * SS), (0, 0, 0, 0) if rgba else "white")
        self.d = ImageDraw.Draw(self.im, "RGBA" if rgba else "RGB")

    @staticmethod
    def _p(pts):
        return [(x * SS, y * SS) for x, y in pts]

    def garis(self, pts, w=6, fill=INK):
        P = self._p(pts)
        self.d.line(P, fill=fill, width=int(w * SS), joint="curve")
        r = w * SS / 2
        for x, y in (P[0], P[-1]):
            self.d.ellipse([x - r, y - r, x + r, y + r], fill=fill)

    def elips(self, box, fill=None, outline=None, w=0):
        x0, y0, x1, y1 = box
        self.d.ellipse([x0 * SS, y0 * SS, x1 * SS, y1 * SS], fill=fill, outline=outline, width=int(w * SS))

    def lingkaran(self, x, y, r, fill=None, outline=None, w=0):
        self.elips((x - r, y - r, x + r, y + r), fill, outline, w)

    def poli(self, pts, fill=None, outline=None):
        self.d.polygon(self._p(pts), fill=fill, outline=outline)

    def kotak(self, box, r=12, fill=None, outline=None, w=0):
        x0, y0, x1, y1 = box
        self.d.rounded_rectangle([x0 * SS, y0 * SS, x1 * SS, y1 * SS], radius=r * SS, fill=fill,
                                 outline=outline, width=int(w * SS))

    def busur(self, box, a0, a1, fill=INK, w=4):
        x0, y0, x1, y1 = box
        self.d.arc([x0 * SS, y0 * SS, x1 * SS, y1 * SS], a0, a1, fill=fill, width=int(w * SS))

    def juring(self, box, a0, a1, fill):
        x0, y0, x1, y1 = box
        self.d.pieslice([x0 * SS, y0 * SS, x1 * SS, y1 * SS], a0, a1, fill=fill)

    def teks(self, xy, s, size=40, fill="white", anchor="mm", stroke=0, stroke_fill="#222"):
        self.d.text((xy[0] * SS, xy[1] * SS), s, font=font(size), fill=fill, anchor=anchor,
                    stroke_width=int(stroke * SS), stroke_fill=stroke_fill)

    def lebar_teks(self, s, size):
        return self.d.textlength(s, font=font(size)) / SS

    def tempel(self, img, x, y):
        """Tempel gambar RGBA (sudah dalam ukuran SS) dengan titik tengah x,y logis."""
        self.im.paste(img, (int(x * SS - img.width / 2), int(y * SS - img.height / 2)), img)

    def hasil(self):
        return self.im.resize((self.w, self.h), Image.LANCZOS)


def gradien(K, atas, bawah, y0=0, y1=H):
    a = Image.new("RGB", (1, 2))
    a.putpixel((0, 0), ImageColor.getrgb(atas))
    a.putpixel((0, 1), ImageColor.getrgb(bawah))
    g = a.resize((K.w * SS, int((y1 - y0) * SS)), Image.BILINEAR)
    K.im.paste(g, (0, int(y0 * SS)))


# ----------------------------------------------------------------- LATAR
def awan(K, x, y, s=1.0):
    for dx, dy, r in ((0, 0, 36), (40, -12, 44), (84, 0, 34), (40, 14, 38)):
        K.lingkaran(x + dx * s, y + dy * s, r * s, fill=(255, 255, 255, 235))


def gedung(K, rnd, warna_g, jendela, y_dasar=GY, tinggi=(260, 560), geser=0):
    x = -40 + geser
    while x < W + 40:
        w = rnd.randint(110, 190)
        h = rnd.randint(*tinggi)
        K.d.rectangle([x * SS, (y_dasar - h) * SS, (x + w) * SS, y_dasar * SS], fill=warna_g)
        for jx in range(int(x) + 18, int(x + w) - 22, 38):
            for jy in range(int(y_dasar - h) + 24, int(y_dasar) - 40, 52):
                on = rnd.random() < 0.55
                K.d.rectangle([jx * SS, jy * SS, (jx + 20) * SS, (jy + 28) * SS],
                              fill=jendela if on else warna_g)
        x += w + rnd.randint(4, 18)


def pohon(K, x, y, s=1.0):
    K.d.rectangle([(x - 12 * s) * SS, (y - 150 * s) * SS, (x + 12 * s) * SS, y * SS], fill="#7a5230")
    for dx, dy, r in ((0, -190, 70), (-48, -150, 52), (48, -150, 52), (0, -130, 56)):
        K.lingkaran(x + dx * s, y + dy * s, r * s, fill="#2e9b4a")


GESER = [0.0]


def latar(K, nama, t):
    rnd = random.Random(7)
    if nama == "taman":
        gradien(K, "#8fd3ff", "#e6f6ff", 0, GY)
        K.lingkaran(580, 170, 70, fill="#ffe27a")
        awan(K, (t * 14) % 900 - 150, 230, 1.1)
        awan(K, (t * 9 + 400) % 900 - 150, 380, 0.8)
        K.elips((-200, 700, 520, 1120), fill="#7fcf6b")
        K.elips((300, 740, 960, 1140), fill="#6bc15a")
        gs = GESER[0]
        for bx0, sk in ((110, 1.0), (620, 0.85), (380, 0.7)):
            pohon(K, (bx0 - gs) % (W + 300) - 150, GY - 50, sk)
        K.d.rectangle([0, GY * SS, W * SS, H * SS], fill="#5eb34e")
    elif nama == "kota":
        gradien(K, "#9ccfff", "#f0f8ff", 0, GY)
        awan(K, (t * 12) % 900 - 150, 200, 1.0)
        gedung(K, rnd, "#8ea4bd", "#ffe9a8")
        K.d.rectangle([0, GY * SS, W * SS, H * SS], fill="#6b7078")
        for x in range(-120, W + 120, 120):
            xx = x - GESER[0] % 120
            K.d.rectangle([(xx + 10) * SS, (GY + 60) * SS, (xx + 70) * SS, (GY + 70) * SS], fill="#e8e8e8")
    elif nama == "kafe":
        K.d.rectangle([0, 0, W * SS, GY * SS], fill="#f2dcc0")
        K.kotak((70, 200, 360, 560), 14, fill="#bfe3f5", outline="#8a5a36", w=10)
        K.garis([(215, 200), (215, 560)], 6, "#8a5a36")
        K.garis([(70, 380), (360, 380)], 6, "#8a5a36")
        for x in (480, 620):
            K.garis([(x, 0), (x, 220)], 4, "#6b4a2b")
            K.lingkaran(x, 240, 38, fill="#ffd36b")
        K.kotak((420, 520, 700, 548), 6, fill="#8a5a36")
        for i, c in enumerate(("#d9534f", "#5cb85c", "#f0ad4e", "#5bc0de")):
            K.kotak((440 + i * 62, 470, 480 + i * 62, 520), 5, fill=c)
        K.d.rectangle([0, GY * SS, W * SS, H * SS], fill="#a8744a")
    elif nama == "kamar":
        K.d.rectangle([0, 0, W * SS, GY * SS], fill="#f6e1ec")
        K.kotak((420, 180, 660, 470), 12, fill="#cfeaff", outline="#fff", w=12)
        K.lingkaran(560, 290, 36, fill="#ffe27a")
        K.kotak((30, 700, 320, 950), 16, fill="#8fb7e8")
        K.kotak((30, 660, 320, 740), 22, fill="#e6f0ff")
        K.kotak((30, 640, 140, 720), 22, fill="#ffffff")
        K.d.rectangle([0, GY * SS, W * SS, H * SS], fill="#c9a37a")
    elif nama == "senja":
        gradien(K, "#6a4c93", "#ffb36b", 0, GY)
        K.lingkaran(360, 760, 150, fill="#ffd27a")
        K.elips((-300, 820, 520, 1300), fill="#3d2a5c")
        K.elips((260, 860, 1000, 1300), fill="#2f2048")
        K.d.rectangle([0, GY * SS, W * SS, H * SS], fill="#2a1d40")
    elif nama == "malam":
        gradien(K, "#0b1235", "#27386b", 0, GY)
        for _ in range(60):
            x, y = rnd.randint(0, W), rnd.randint(0, 700)
            r = 1.5 + 1.2 * abs(math.sin(t * 2 + x))
            K.lingkaran(x, y, r, fill="#fff7c9")
        K.lingkaran(560, 190, 62, fill="#fdf3c4")
        K.lingkaran(585, 175, 56, fill="#0e1639")
        gedung(K, rnd, "#1a2349", "#ffd96b", tinggi=(220, 480))
        K.d.rectangle([0, GY * SS, W * SS, H * SS], fill="#161c3a")
    elif nama == "hujan":
        gradien(K, "#6f7f95", "#aab6c4", 0, GY)
        awan(K, 80, 160, 1.4)
        awan(K, 420, 230, 1.2)
        gedung(K, rnd, "#5c6a7c", "#e8d27a", tinggi=(200, 420))
        K.d.rectangle([0, GY * SS, W * SS, H * SS], fill="#4b5563")
        for i in range(70):
            x = (i * 53 + t * 220) % (W + 60) - 30
            y = (i * 97 + t * 900) % (GY + 100)
            K.garis([(x, y), (x - 8, y + 34)], 2.5, (200, 220, 245, 190))
    elif nama == "pantai":
        gradien(K, "#7fd0ff", "#dff4ff", 0, 700)
        K.lingkaran(120, 170, 70, fill="#ffe27a")
        awan(K, (t * 12) % 900 - 150, 260, 0.9)
        K.d.rectangle([0, 640 * SS, W * SS, 860 * SS], fill="#2aa7d8")
        for i in range(8):
            x = (i * 110 + t * 40) % (W + 120) - 60
            K.busur((x, 700 + (i % 3) * 40, x + 100, 740 + (i % 3) * 40), 200, 340, "#bfeaff", 5)
        K.d.rectangle([0, 860 * SS, W * SS, H * SS], fill="#f0d9a0")
    elif nama == "gurun":
        gradien(K, "#ffcf8a", "#fff0c9", 0, GY)
        K.lingkaran(560, 210, 80, fill="#fff4b0")
        K.elips((-260, 780, 560, 1200), fill="#f0b86a")
        K.elips((200, 830, 980, 1220), fill="#e8a955")
        K.d.rectangle([(90 - 14) * SS, 700 * SS, (90 + 14) * SS, 930 * SS], fill="#3b8f4a")
        K.d.rectangle([40 * SS, 780 * SS, 90 * SS, 800 * SS], fill="#3b8f4a")
        K.d.rectangle([40 * SS, 740 * SS, 58 * SS, 800 * SS], fill="#3b8f4a")
        K.d.rectangle([0, GY * SS, W * SS, H * SS], fill="#e0a050")
    else:
        gradien(K, "#cfe9ff", "#ffffff", 0, GY)
        K.d.rectangle([0, GY * SS, W * SS, H * SS], fill="#9aa5b1")


# ----------------------------------------------------------------- TOKOH
L_UA, L_LA, L_UL, L_LL, L_TORSO, R_HEAD = 48, 46, 60, 60, 105, 36


def pt(x, y, ang, ln, d):
    a = math.radians(ang)
    return x + d * ln * math.sin(a), y + ln * math.cos(a)


def pose(aksi, t):
    p = dict(F=(10, 5), B=(-10, -5), LF=(3, 3), LB=(-3, -3), bob=0.0, dx=0.0, wajah="senyum",
             efek=[], turun=0.0, miring=0.0, hadap=None)
    s = math.sin
    if aksi in ("diam", None):
        p["bob"] = s(t * 2.4) * 2
        p["F"] = (12 + s(t * 2) * 3, 8); p["B"] = (-12, -8)
    elif aksi in ("jalan", "jalan_masuk", "pergi"):
        w = s(t * 7.5)
        p["F"] = (-w * 32, -w * 32 + 10); p["B"] = (w * 32, w * 32 + 10)
        p["LF"] = (w * 30, w * 30 - 12 * max(0, -w)); p["LB"] = (-w * 30, -w * 30 - 12 * max(0, w))
        p["bob"] = abs(w) * 4
    elif aksi == "melambai":
        p["F"] = (140, 150 + s(t * 9) * 30); p["B"] = (-10, -5); p["bob"] = s(t * 3) * 2
    elif aksi == "tertawa":
        p["bob"] = abs(s(t * 10)) * 10; p["wajah"] = "tawa"
        p["F"] = (35, 105); p["B"] = (-35, -105); p["miring"] = s(t * 5) * 4
    elif aksi == "sedih":
        p["wajah"] = "sedih"; p["F"] = (6, 3); p["B"] = (-6, -3); p["miring"] = 6; p["bob"] = s(t * 1.8) * 2
    elif aksi == "menangis":
        p["wajah"] = "sedih"; p["F"] = (45, 150); p["B"] = (-8, -4); p["efek"] = ["air_mata"]
        p["miring"] = 7; p["bob"] = abs(s(t * 8)) * 3
    elif aksi == "malu":
        p["wajah"] = "malu"; p["F"] = (48, 165); p["B"] = (-48, -165); p["miring"] = s(t * 3) * 5
    elif aksi == "kaget":
        k = min(t * 5, math.pi)
        p["bob"] = abs(s(k)) * 34; p["wajah"] = "kaget"; p["efek"] = ["seru"]
        p["F"] = (125, 150); p["B"] = (-125, -150)
    elif aksi == "cinta":
        p["wajah"] = "cinta"; p["F"] = (30, 135); p["B"] = (-30, -135); p["efek"] = ["hati_kecil"]
        p["miring"] = s(t * 3) * 6; p["bob"] = s(t * 4) * 3
    elif aksi == "memberi":
        p["F"] = (84, 88); p["B"] = (-10, -5); p["miring"] = 4
    elif aksi == "berlutut":
        p["turun"] = 48; p["LF"] = (88, 4); p["LB"] = (-12, -98)
        p["F"] = (86, 88); p["B"] = (-10, -5); p["miring"] = 6
    elif aksi == "pegangan":
        p["F"] = (82, 85); p["B"] = (-10, -5)
    elif aksi == "memayungi":
        p["F"] = (55, 80); p["B"] = (-10, -5)
    elif aksi == "haus":
        p["wajah"] = "haus"; p["F"] = (30, 150); p["B"] = (-8, -4); p["efek"] = ["keringat"]
        p["miring"] = 8 + s(t * 2) * 3
    elif aksi == "main_hp":
        p["F"] = (50, 100); p["B"] = (28, 96); p["miring"] = 10
    elif aksi == "panik":
        p["wajah"] = "kaget"; p["efek"] = ["keringat", "seru"]; p["dx"] = s(t * 30) * 4
        p["F"] = (150 + s(t * 14) * 18, 165); p["B"] = (-150 - s(t * 14) * 18, -165)
    elif aksi == "batuk":
        k = abs(s(t * 9))
        p["wajah"] = "sedih"; p["F"] = (112, 150); p["B"] = (-10, -5); p["efek"] = ["batuk"]
        p["miring"] = 10 + k * 8; p["bob"] = -k * 4
    elif aksi == "minum":
        p["F"] = (100, 162 + s(t * 3) * 4); p["B"] = (-12, -6); p["miring"] = -6
    elif aksi == "joget":
        p["bob"] = abs(s(t * 8)) * 12; p["wajah"] = "tawa"; p["dx"] = s(t * 4) * 14
        p["F"] = (120 + s(t * 8) * 30, 150); p["B"] = (-120 + s(t * 8) * 30, -150); p["miring"] = s(t * 4) * 8
        p["LF"] = (12 + s(t * 8) * 10, 0); p["LB"] = (-12 + s(t * 8) * 10, 0)
    elif aksi == "lompat":
        p["bob"] = abs(s(t * 6)) * 70; p["wajah"] = "tawa"
        p["F"] = (150, 170); p["B"] = (-150, -170); p["LF"] = (25, -20); p["LB"] = (-25, -60)
    return p


def gambar_prop(K, jenis, hx, hy, d, t, produk_ikon=None):
    if not jenis:
        return
    if jenis == "produk":
        if produk_ikon is not None:
            K.tempel(produk_ikon, hx + d * 4, hy - 30)
        else:
            K.kotak((hx - 34, hy - 70, hx + 34, hy + 4), 8, fill="#f2a93b", outline=INK, w=3)
            K.garis([(hx, hy - 70), (hx, hy + 4)], 5, "#fff")
    elif jenis == "bunga":
        K.garis([(hx, hy), (hx, hy - 70)], 5, "#2e9b4a")
        for i in range(5):
            a = i * 72 + t * 20
            K.lingkaran(hx + 18 * math.cos(math.radians(a)), hy - 78 + 18 * math.sin(math.radians(a)), 11, fill="#ff5a8a")
        K.lingkaran(hx, hy - 78, 9, fill="#ffd54a")
    elif jenis == "cincin":
        K.lingkaran(hx, hy - 14, 14, outline="#ffd54a", w=6)
        K.poli([(hx - 8, hy - 34), (hx + 8, hy - 34), (hx, hy - 24)], fill="#7fe0ff")
    elif jenis == "hadiah":
        K.kotak((hx - 32, hy - 60, hx + 32, hy + 2), 6, fill="#e84a5f")
        K.d.rectangle([(hx - 5) * SS, (hy - 60) * SS, (hx + 5) * SS, (hy + 2) * SS], fill="#ffd54a")
        K.garis([(hx, hy - 60), (hx - 16, hy - 78)], 5, "#ffd54a"); K.garis([(hx, hy - 60), (hx + 16, hy - 78)], 5, "#ffd54a")
    elif jenis == "payung":
        K.garis([(hx, hy + 10), (hx, hy - 170)], 5, "#444")
        K.juring((hx - 120, hy - 290, hx + 120, hy - 50), 180, 360, "#e84a5f")
        for i in range(-1, 2):
            K.garis([(hx + i * 40, hy - 170), (hx, hy - 290 + abs(i) * 20)], 2, "#b53046")
    elif jenis == "gelas":
        K.poli([(hx - 20, hy - 66), (hx + 20, hy - 66), (hx + 14, hy), (hx - 14, hy)], fill=(190, 230, 255, 230), outline=INK)
        K.poli([(hx - 18, hy - 40), (hx + 18, hy - 40), (hx + 14, hy), (hx - 14, hy)], fill="#8b5a2b")
        K.garis([(hx + 4, hy - 90), (hx + 4, hy - 40)], 5, "#e84a5f")
    elif jenis == "surat":
        K.kotak((hx - 34, hy - 52, hx + 34, hy), 4, fill="#fffdf2", outline=INK, w=3)
        K.garis([(hx - 34, hy - 52), (hx, hy - 24), (hx + 34, hy - 52)], 3, INK)
    elif jenis == "hp":
        K.kotak((hx - 18, hy - 54, hx + 18, hy + 2), 6, fill="#222", outline="#999", w=2)
        K.kotak((hx - 14, hy - 48, hx + 14, hy - 6), 3, fill="#7fd0ff")


def hati(K, x, y, r, fill="#ff4d7a"):
    K.lingkaran(x - r * 0.5, y - r * 0.2, r * 0.58, fill=fill)
    K.lingkaran(x + r * 0.5, y - r * 0.2, r * 0.58, fill=fill)
    K.poli([(x - r * 1.04, y - r * 0.05), (x + r * 1.04, y - r * 0.05), (x, y + r * 1.15)], fill=fill)


KULIT = "#ffe0c2"


def wajah(K, hx, hy, d, jenis, t, bicara=False):
    ex = [hx + d * 9 - 14, hx + d * 9 + 14]
    ey = hy - 4
    kedip = (t % 3.3) < 0.12 and jenis not in ("cinta", "kaget", "tawa")
    # alis
    if jenis == "sedih" or jenis == "haus":
        K.garis([(ex[0] - 9, ey - 14), (ex[0] + 8, ey - 20)], 3.5)
        K.garis([(ex[1] + 9, ey - 14), (ex[1] - 8, ey - 20)], 3.5)
    elif jenis == "kaget":
        K.busur((ex[0] - 9, ey - 26, ex[0] + 9, ey - 12), 200, 340, INK, 3.5)
        K.busur((ex[1] - 9, ey - 26, ex[1] + 9, ey - 12), 200, 340, INK, 3.5)
    else:
        K.garis([(ex[0] - 8, ey - 15), (ex[0] + 7, ey - 17)], 3.5)
        K.garis([(ex[1] - 7, ey - 17), (ex[1] + 8, ey - 15)], 3.5)
    # mata
    if jenis == "cinta":
        for x in ex:
            hati(K, x, ey, 8)
    elif jenis == "kaget":
        for x in ex:
            K.lingkaran(x, ey, 9, fill="white", outline=INK, w=2.5)
            K.lingkaran(x + d * 2, ey, 3.5, fill=INK)
    elif jenis == "tawa":
        for x in ex:
            K.busur((x - 8, ey - 4, x + 8, ey + 12), 200, 340, INK, 4)
    elif kedip:
        for x in ex:
            K.garis([(x - 6, ey), (x + 6, ey)], 3.5)
    else:
        for x in ex:
            K.elips((x - 5.5, ey - 7, x + 5.5, ey + 7), fill=INK)
            K.lingkaran(x + d * 1.5 + 1.5, ey - 3, 2, fill="white")
    # pipi
    for x in ex:
        K.lingkaran(x + (-6 if x == ex[0] else 6), ey + 15, 7 if jenis != "malu" else 9,
                    fill=(255, 120, 150, 90 if jenis != "malu" else 170))
    mx = hx + d * 9
    my = hy + 15
    buka = bicara and (math.sin(t * 22) + math.sin(t * 13)) > 0.2
    if jenis == "tawa" or (buka and jenis not in ("sedih", "kaget")):
        h = 16 if jenis == "tawa" else 10 + 4 * abs(math.sin(t * 17))
        K.d.chord([(mx - 13) * SS, (my - 8) * SS, (mx + 13) * SS, (my + h) * SS], 0, 180, fill="#7a1f2b", outline=INK, width=3 * SS)
        K.elips((mx - 6, my + h * 0.35, mx + 6, my + h * 0.8), fill="#ff7b9a")
    elif jenis == "kaget":
        K.elips((mx - 8, my - 4, mx + 8, my + 16), fill="#7a1f2b", outline=INK, w=2.5)
    elif jenis == "sedih":
        K.busur((mx - 12, my + 2, mx + 12, my + 22), 200, 340, INK, 4)
    elif jenis == "haus":
        K.elips((mx - 9, my - 2, mx + 9, my + 12), fill="#7a1f2b", outline=INK, w=2.5)
    else:
        K.busur((mx - 13, my - 10, mx + 13, my + 12), 20, 160, INK, 4)


def tokoh(K, cfg, x, aksi, t, d, bawa=None, scale=1.0, produk_ikon=None, gy=GY, bicara=False):
    """Stickman detail. (x, gy) = titik kaki. d = arah hadap (+1 kanan, -1 kiri)."""
    p = pose(aksi, t)
    jenis = cfg.get("jenis", "laki")
    cb = warna(cfg.get("baju", "biru"))
    ch = warna(cfg.get("rambut", "hitam" if jenis == "laki" else "coklat"), "#333")
    cc_ = warna(cfg.get("celana", "#3a4a6b"))
    S = scale
    x = x + p["dx"] * S
    hip_y = gy - (L_UL + L_LL) * S + p["turun"] * S - p["bob"] * S
    sh_y = hip_y - L_TORSO * S
    head_y = sh_y - (10 + R_HEAD) * S
    lean = p["miring"] * d
    head_x = x + math.sin(math.radians(lean)) * 16 * S
    sh_x = x + math.sin(math.radians(lean)) * 6 * S
    lw = 9 * S
    K.elips((x - 64 * S, gy - 9 * S, x + 64 * S, gy + 9 * S), fill=(0, 0, 0, 55))

    def tungkai(u, l, ln1, ln2, sx, sy):
        kx, ky = pt(sx, sy, u, ln1 * S, d)
        fx, fy = pt(kx, ky, l, ln2 * S, d)
        return (sx, sy), (kx, ky), (fx, fy)

    def anggota(pts, warna_isi, tebal):
        K.garis(pts, tebal + 4 * S, INK)
        K.garis(pts, tebal, warna_isi)

    # kaki + sepatu
    for kk in ("B", "F"):
        u, l = p["L" + kk]
        a, b, c = tungkai(u, l, L_UL, L_LL, x + (-6 if kk == "B" else 6) * S, hip_y)
        if jenis == "laki":
            anggota([a, b, c], cc_, lw * 1.7)
        else:
            anggota([a, b, c], KULIT, lw * 0.95)
        sx = c[0] + d * 9 * S
        K.elips((sx - 17 * S, c[1] - 9 * S, sx + 17 * S, c[1] + 7 * S), fill="#2b2b2b" if jenis == "laki" else "#e8546c", outline=INK, w=2.5 * S)
        K.elips((sx - 6 * S, c[1] - 6 * S, sx + 10 * S, c[1] - 2 * S), fill=(255, 255, 255, 120))
    # badan
    if jenis == "perempuan":
        K.d.polygon([((sh_x - 20 * S) * SS, sh_y * SS), ((sh_x + 20 * S) * SS, sh_y * SS),
                     ((x + 52 * S) * SS, (hip_y + 40 * S) * SS), ((x - 52 * S) * SS, (hip_y + 40 * S) * SS)],
                    fill=cb, outline=INK, width=int(3 * S * SS))
        K.d.rectangle([(x - 18 * S) * SS, (hip_y - 30 * S) * SS, (x + 18 * S) * SS, (hip_y - 22 * S) * SS], fill="#ffffff")
        for i in range(3):
            K.lingkaran(x - 30 * S + i * 30 * S, hip_y + 18 * S, 5 * S, fill=(255, 255, 255, 140))
    else:
        K.d.polygon([((sh_x - 26 * S) * SS, (sh_y - 2 * S) * SS), ((sh_x + 26 * S) * SS, (sh_y - 2 * S) * SS),
                     ((x + 22 * S) * SS, (hip_y + 6 * S) * SS), ((x - 22 * S) * SS, (hip_y + 6 * S) * SS)],
                    fill=cb, outline=INK, width=int(3 * S * SS))
        K.d.rectangle([(x - 22 * S) * SS, (hip_y - 2 * S) * SS, (x + 22 * S) * SS, (hip_y + 6 * S) * SS], fill="#5a3a22")
        for i in range(3):
            K.lingkaran(sh_x + (x - sh_x) * (i + 1) / 4, sh_y + L_TORSO * S * (i + 1) / 4 - 8 * S, 3 * S, fill="white")
    # kerah + leher
    K.garis([(sh_x, sh_y + 2 * S), (head_x, head_y + R_HEAD * S)], lw * 1.1, INK)
    K.garis([(sh_x, sh_y + 2 * S), (head_x, head_y + R_HEAD * S)], lw * 0.6, KULIT)
    K.poli([(sh_x - 14 * S, sh_y - 3 * S), (sh_x, sh_y + 12 * S), (sh_x + 14 * S, sh_y - 3 * S)], fill="white")

    # lengan (lengan baju + tangan)
    tangan = {}
    for kk in ("B", "F"):
        u, l = p[kk]
        a, b, c = tungkai(u, l, L_UA, L_LA, sh_x + (-10 if kk == "B" else 10) * S * d, sh_y + 8 * S)
        anggota([a, b], cb, lw * 1.5)
        anggota([b, c], KULIT, lw * 0.85)
        K.lingkaran(c[0], c[1], 9 * S, fill=KULIT, outline=INK, w=2.5 * S)
        tangan[kk] = c

    # rambut belakang
    if jenis == "perempuan":
        hb = head_x - d * 18 * S
        K.elips((hb - (R_HEAD + 2) * S, head_y - (R_HEAD + 8) * S, hb + (R_HEAD + 2) * S, head_y + (R_HEAD + 46) * S), fill=ch, outline=INK, w=2.5 * S)
    # telinga + kepala
    ex_ = head_x - d * (R_HEAD - 4) * S
    K.lingkaran(ex_, head_y + 4 * S, 9 * S, fill=KULIT, outline=INK, w=2.5 * S)
    K.lingkaran(head_x, head_y, R_HEAD * S, fill=KULIT, outline=INK, w=4 * S)
    # rambut depan (poni)
    K.d.chord([(head_x - (R_HEAD + 4) * S) * SS, (head_y - (R_HEAD + 6) * S) * SS,
               (head_x + (R_HEAD + 4) * S) * SS, (head_y + (R_HEAD - 6) * S) * SS], 182, 358, fill=ch, outline=INK, width=int(2.5 * S * SS))
    if jenis == "laki":
        for i in range(3):
            bx = head_x + (-14 + i * 14) * S
            K.poli([(bx - 9 * S, head_y - (R_HEAD - 2) * S), (bx + 9 * S, head_y - (R_HEAD - 2) * S), (bx + d * 6 * S, head_y - (R_HEAD + 16) * S)], fill=ch)
    else:
        bx = head_x - d * (R_HEAD - 6) * S
        K.lingkaran(bx - 7 * S, head_y - 28 * S, 10 * S, fill="#ff5a8a", outline=INK, w=2 * S)
        K.lingkaran(bx + 7 * S, head_y - 28 * S, 10 * S, fill="#ff5a8a", outline=INK, w=2 * S)
        K.lingkaran(bx, head_y - 28 * S, 5 * S, fill="#ffd54a")
    # wajah
    if S == 1.0:
        wajah(K, head_x, head_y, d, p["wajah"], t, bicara)
    else:
        kecil = Kanvas(120, 120, rgba=True)
        wajah(kecil, 60, 60, d, p["wajah"], t, bicara)
        img = kecil.im.resize((int(120 * S * SS), int(120 * S * SS)), Image.LANCZOS)
        K.tempel(img, head_x, head_y)

    # efek karakter
    for e in p["efek"]:
        if e == "air_mata":
            for i in range(2):
                yy = head_y + 6 * S + ((t * 60 + i * 30) % 60) * S
                K.elips((head_x + d * 9 * S - 22 * S + i * 28 * S, yy, head_x + d * 9 * S - 14 * S + i * 28 * S, yy + 16 * S), fill=(110, 190, 255, 230))
        elif e == "seru":
            K.teks((head_x + 52 * S, head_y - 52 * S - abs(math.sin(t * 8)) * 6), "!", int(54 * S), "#ff3b3b", stroke=3, stroke_fill="white")
        elif e == "keringat":
            yy = head_y - 20 * S + ((t * 70) % 40) * S
            K.elips((head_x - d * 52 * S - 5 * S, yy, head_x - d * 52 * S + 5 * S, yy + 18 * S), fill=(110, 190, 255, 230))
        elif e == "hati_kecil":
            for i in range(3):
                ph = (t * 0.8 + i * 0.33) % 1
                hati(K, head_x + (i - 1) * 34 * S + math.sin(ph * 6) * 8, head_y - 52 * S - ph * 80 * S, 9 * S, (255, 77, 122, int(255 * (1 - ph))))
        elif e == "batuk":
            for i in range(3):
                ph = (t * 1.6 + i * 0.33) % 1
                K.lingkaran(head_x + d * (40 + ph * 70) * S, head_y + (14 - ph * 20) * S, (6 + ph * 12) * S, fill=(200, 200, 200, int(220 * (1 - ph))))
            K.teks((head_x + d * 70 * S, head_y - 50 * S), "uhuk!", int(28 * S), "#555", stroke=2, stroke_fill="white")

    if bawa:
        hx, hy = tangan["F"]
        ikon = produk_ikon
        if S != 1.0 and ikon is not None:
            ikon = ikon.resize((int(ikon.width * S), int(ikon.height * S)), Image.LANCZOS)
        gambar_prop_skala(K, bawa, hx, hy, d, t, ikon, S)
    return x, head_y


def gambar_prop_skala(K, jenis, hx, hy, d, t, ikon, S):
    if S == 1.0:
        gambar_prop(K, jenis, hx, hy, d, t, ikon)
        return
    kecil = Kanvas(400, 400, rgba=True)
    gambar_prop(kecil, jenis, 200, 300, d, t, ikon.resize((int(ikon.width / S), int(ikon.height / S))) if ikon is not None else None)
    img = kecil.im.resize((int(400 * S * SS), int(400 * S * SS)), Image.LANCZOS)
    K.tempel(img, hx, hy - 100 * S)


# ----------------------------------------------------------------- PRODUK
def ikon_produk(K, cx, cy, s, jenis, label, warna_utama="#f2a93b"):
    if jenis == "toples":
        K.kotak((cx - 0.30 * s, cy - 0.30 * s, cx + 0.30 * s, cy + 0.38 * s), 0.08 * s, fill=(255, 255, 255, 120), outline="#8a6a2b", w=0.012 * s)
        K.kotak((cx - 0.28 * s, cy - 0.05 * s, cx + 0.28 * s, cy + 0.36 * s), 0.07 * s, fill=warna_utama)
        K.kotak((cx - 0.34 * s, cy - 0.42 * s, cx + 0.34 * s, cy - 0.30 * s), 0.04 * s, fill="#c0392b")
        K.kotak((cx - 0.20 * s, cy + 0.02 * s, cx + 0.20 * s, cy + 0.26 * s), 0.03 * s, fill="#fffdf2")
        K.teks((cx, cy + 0.14 * s), label, int(0.085 * s), "#8a4b08")
        K.poli([(cx - 0.06 * s, cy - 0.30 * s), (cx + 0.06 * s, cy - 0.30 * s), (cx + 0.03 * s, cy - 0.12 * s), (cx - 0.03 * s, cy - 0.12 * s)], fill=warna_utama)
    elif jenis == "botol":
        K.kotak((cx - 0.17 * s, cy - 0.12 * s, cx + 0.17 * s, cy + 0.40 * s), 0.06 * s, fill=warna_utama, outline=INK, w=0.012 * s)
        K.kotak((cx - 0.08 * s, cy - 0.34 * s, cx + 0.08 * s, cy - 0.12 * s), 0.03 * s, fill=warna_utama, outline=INK, w=0.012 * s)
        K.kotak((cx - 0.10 * s, cy - 0.42 * s, cx + 0.10 * s, cy - 0.34 * s), 0.02 * s, fill="#444")
        K.kotak((cx - 0.13 * s, cy + 0.06 * s, cx + 0.13 * s, cy + 0.26 * s), 0.02 * s, fill="#fff")
        K.teks((cx, cy + 0.16 * s), label, int(0.06 * s), "#333")
    else:
        K.kotak((cx - 0.30 * s, cy - 0.22 * s, cx + 0.30 * s, cy + 0.30 * s), 0.05 * s, fill=warna_utama, outline=INK, w=0.012 * s)
        K.d.rectangle([(cx - 0.04 * s) * SS, (cy - 0.22 * s) * SS, (cx + 0.04 * s) * SS, (cy + 0.30 * s) * SS], fill="white")
        K.teks((cx, cy + 0.06 * s), label, int(0.07 * s), "white", stroke=1)


def siapkan_produk(foto=None, ikon="kotak", label="PRODUK", ukuran=420):
    """Kembalikan (kartu RGBA ukuran SS, thumbnail RGBA kecil untuk dipegang tokoh)."""
    def isi_persegi(px):
        k = Kanvas(px, px, rgba=True)
        if foto is not None:
            im = foto.convert("RGB")
            sisi = min(im.size)
            im = im.crop(((im.width - sisi) // 2, (im.height - sisi) // 2, (im.width + sisi) // 2, (im.height + sisi) // 2))
            im = im.resize((px * SS, px * SS), Image.LANCZOS).convert("RGBA")
            k.im.paste(im, (0, 0))
        else:
            gradien_bg = Image.new("RGB", (1, 2), "#fff3d1")
            gradien_bg.putpixel((0, 1), (255, 214, 120))
            k.im.paste(gradien_bg.resize((px * SS, px * SS), Image.BILINEAR).convert("RGBA"), (0, 0))
            for i in range(6):  # sarang lebah dekor
                for j in range(5):
                    cx, cy = 40 + i * 78 + (j % 2) * 39, 30 + j * 70
                    pts = [(cx + 34 * math.cos(math.radians(60 * q + 30)) * px / 420, cy + 34 * math.sin(math.radians(60 * q + 30)) * px / 420) for q in range(6)]
                    k.poli(pts, outline=(255, 190, 70, 120))
            ikon_produk(k, px / 2, px / 2, px * 0.9, ikon, label)
        return k.im

    # kartu
    pad = 22
    k = Kanvas(ukuran + pad * 2, ukuran + pad * 2, rgba=True)
    k.kotak((pad + 6, pad + 10, pad + ukuran + 6, pad + ukuran + 14), 30, fill=(0, 0, 0, 60))
    k.kotak((pad, pad, pad + ukuran, pad + ukuran), 30, fill="white")
    inner = ukuran - 28
    isi = isi_persegi(inner)
    mask = Image.new("L", isi.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, isi.width, isi.height], radius=20 * SS, fill=255)
    k.im.paste(isi, ((pad + 14) * SS, (pad + 14) * SS), mask)
    kartu = k.im
    thumb = isi_persegi(110)
    m2 = Image.new("L", thumb.size, 0)
    ImageDraw.Draw(m2).rounded_rectangle([0, 0, thumb.width, thumb.height], radius=14 * SS, fill=255)
    tk = Kanvas(120, 120, rgba=True)
    tk.kotak((2, 2, 118, 118), 16, fill="white")
    tk.im.paste(thumb, (5 * SS, 5 * SS), m2)
    return kartu, tk.im


def rotasi(img, sudut, skala=1.0):
    if skala != 1.0:
        img = img.resize((int(img.width * skala), int(img.height * skala)), Image.BICUBIC)
    return img.rotate(sudut, resample=Image.BICUBIC, expand=True)


# ----------------------------------------------------------------- EFEK & UI
def efek_layar(K, nama, t):
    rnd = random.Random(11)
    if nama == "hati":
        for i in range(9):
            ph = (t * 0.35 + i / 9) % 1
            hati(K, 80 + (i * 83) % 600 + math.sin(ph * 8 + i) * 22, 1000 - ph * 900, 14 + (i % 3) * 6, (255, 77, 122, int(230 * (1 - ph))))
    elif nama == "hujan":
        for i in range(60):
            x = (i * 53 + t * 240) % (W + 60) - 30
            y = (i * 97 + t * 950) % H
            K.garis([(x, y), (x - 8, y + 36)], 2.5, (190, 215, 245, 170))
    elif nama == "bintang":
        for i in range(14):
            x, y = rnd.randint(30, W - 30), rnd.randint(60, 900)
            r = 8 + 10 * abs(math.sin(t * 3 + i))
            pts = []
            for q in range(10):
                rr = r if q % 2 == 0 else r * 0.42
                a = math.radians(q * 36 - 90)
                pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
            K.poli(pts, fill=(255, 220, 60, 230))
    elif nama == "panah":
        b = abs(math.sin(t * 5)) * 26
        cx, cy = 360, 440 - b
        K.poli([(cx - 40, cy - 90), (cx + 40, cy - 90), (cx + 40, cy - 30), (cx + 80, cy - 30), (cx, cy + 50), (cx - 80, cy - 30), (cx - 40, cy - 30)], fill="#ffd21f", outline="#e0a800")
        # tombol keranjang kuning
        sk = 1 + 0.04 * math.sin(t * 6)
        K.kotak((360 - 190 * sk, 540 - 40 * sk, 360 + 190 * sk, 540 + 40 * sk), 40, fill="#ee4d2d", outline="white", w=4)
        K.teks((360, 540), "KERANJANG KUNING", 32, "white")


def bubble_chat(K, daftar, t, y0=560):
    for i, c in enumerate(daftar[:3]):
        t0 = 0.5 + i * 0.8
        if t < t0:
            continue
        k = min((t - t0) / 0.25, 1)
        k = 1 - (1 - k) ** 3
        teks = c.get("teks", "")
        lw = K.lebar_teks(teks, 34) + 70
        h = 58
        y = y0 + i * 70
        kiri = c.get("dari", "kiri") == "kiri"
        x0 = 30 if kiri else W - 30 - lw
        cx = x0 + lw / 2
        ww, hh = lw * k / 2, h * k / 2
        K.kotak((cx - ww, y + h / 2 - hh, cx + ww, y + h / 2 + hh), 26, fill="#ffffff" if kiri else "#d9fdd3", outline="#d0d0d0", w=2)
        if k > 0.9:
            K.teks((cx - (14 if c.get("centang", True) else 0), y + h / 2), teks, 34, "#222")
            if c.get("centang", True):
                K.teks((x0 + lw - 22, y + h / 2 + 8), "vv", 20, "#34b7f1")


def keterangan(K, teks, t, durasi_bicara, mulai=0.25):
    """Teks subtitle bawah dengan sorotan kata saat ini."""
    kata = teks.split()
    if not kata:
        return
    maks = 640
    baris, cur = [], []
    for w in kata:
        uji = " ".join(cur + [w])
        if K.lebar_teks(uji, 40) > maks and cur:
            baris.append(cur); cur = [w]
        else:
            cur.append(w)
    baris.append(cur)
    total = sum(len(w) for w in kata) + len(kata)
    prog = max(0.0, min(1.0, (t - mulai) / max(durasi_bicara, 0.1)))
    tinggi = len(baris) * 52 + 30
    y_atas = 1260 - tinggi
    K.kotak((30, y_atas, W - 30, 1250), 26, fill=(0, 0, 0, 150))
    hitung = 0
    y = y_atas + 15 + 28
    for b in baris:
        lebar = K.lebar_teks(" ".join(b), 40)
        x = (W - lebar) / 2
        for w in b:
            lw = K.lebar_teks(w, 40)
            aktif = hitung / total <= prog < (hitung + len(w) + 1) / total
            K.teks((x, y), w, 40, "#ffe14d" if aktif else "white", anchor="lm", stroke=3 if aktif else 2)
            x += lw + K.lebar_teks(" ", 40)
            hitung += len(w) + 1
        y += 52


def banner_harga(K, harga, coret, t):
    cx = 360
    y = 470
    k = 1 + 0.03 * math.sin(t * 6)
    K.kotak((cx - 230 * k, y - 66 * k, cx + 230 * k, y + 66 * k), 36, fill="#ee4d2d", outline="white", w=5)
    if coret:
        K.teks((cx, y - 36), coret, 28, "#ffd6cc")
        wlen = K.lebar_teks(coret, 28)
        K.garis([(cx - wlen / 2, y - 36), (cx + wlen / 2, y - 36)], 4, "#fff")
    K.teks((cx, y + 14 if coret else y), harga, 60, "white", stroke=2, stroke_fill="#a0200f")
    # burst diskon
    pts = []
    for q in range(20):
        r = 56 if q % 2 == 0 else 42
        a = math.radians(q * 18 + t * 40)
        pts.append((cx + 235 + r * math.cos(a) - 20, y - 78 + r * math.sin(a)))
    K.poli(pts, fill="#ffd21f")
    K.teks((cx + 215, y - 78), "HEMAT", 22, "#c0392b")
