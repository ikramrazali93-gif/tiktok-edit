"""Render video 'Bersedia' — animasi hitam putih + tipografi kinetik (9:16, 30fps).

  python3 video.py               # render penuh -> output/bersedia.mp4
  python3 video.py --still 12.5  # simpan bingkai PNG
  python3 video.py --sheet       # helaian kenalan setiap babak
"""
import argparse
import json
import math
import random
import subprocess
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import skia

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT.parent / "karung-beras"))
from lukis import (BG, POSE, H, W, clamp, curve, ease, ease_out, ellipse, fill, lerp, pen, person,  # noqa: E402
                   poly, prog, walk_pose)

BUILD = ROOT / "build"
OUT = ROOT / "output"
FPS = 30
KAD_AKHIR = 4.2
WHITE = (242, 242, 242)
GREY = (150, 150, 150)
FONT_DIR = "/usr/share/fonts/truetype/montserrat/"

MASA = json.loads((BUILD / "masa.json").read_text())
BARIS = MASA["baris"]
JUMLAH = MASA["jumlah"] + KAD_AKHIR
BY = {b["babak"]: b for b in BARIS}


def word_t(babak, prefix, nth=0):
    """Masa mula perkataan ke-n dalam baris yang bermula dengan prefix."""
    hits = [w["mula"] for w in BY[babak]["kata"] if w["k"].lower().startswith(prefix)]
    return hits[min(nth, len(hits) - 1)]


# ------------------------------------------------------------------ alat lukisan

def line(c, path, p=1.0, w=3.5, a=1.0, glow=True, col=WHITE):
    """Lukis garis neon putih; p = peratus laluan yang sudah 'dilukis'."""
    if p <= 0:
        return
    eff = skia.TrimPathEffect.Make(0, min(1.0, p)) if p < 1 else None
    paints = [pen(col, w, a)]
    if glow:
        paints = [pen(col, w * 4, 0.16 * a, glow=14), pen(col, w * 1.8, 0.35 * a, glow=4)] + paints
    for pt in paints:
        if eff:
            pt.setPathEffect(eff)
        c.drawPath(path, pt)


def resample(pts, n, closed=True):
    pts = np.asarray(pts, float)
    if closed:
        pts = np.vstack([pts, pts[:1]])
    seg = np.hypot(*np.diff(pts, axis=0).T)
    d = np.concatenate([[0], np.cumsum(seg)])
    s = np.linspace(0, d[-1], n, endpoint=not closed)
    return np.stack([np.interp(s, d, pts[:, 0]), np.interp(s, d, pts[:, 1])], 1)


def heart_pts(cx, cy, s, n=240):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    x = 16 * np.sin(t) ** 3
    y = -(13 * np.cos(t) - 5 * np.cos(2 * t) - 2 * np.cos(3 * t) - np.cos(4 * t))
    return np.stack([cx + x * s, cy + y * s], 1)


def arrow_pts(cx, cy, s):
    base = [(-1.3, -0.3), (0.25, -0.3), (0.25, -0.75), (1.3, 0), (0.25, 0.75), (0.25, 0.3), (-1.3, 0.3)]
    # mulakan dari puncak supaya selari dengan titik permulaan hati
    base = base[3:] + base[:3]
    return [(cx + x * s, cy + y * s) for x, y in base]


def pts_path(pts, closed=True):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if closed:
        p.close()
    return p


def circle_path(cx, cy, r):
    p = skia.Path()
    p.addCircle(cx, cy, r)
    return p


def rrect(x, y, w, h, r):
    p = skia.Path()
    p.addRoundRect(skia.Rect.MakeXYWH(x, y, w, h), r, r)
    return p


def camera(c, z, cx, cy):
    c.translate(W / 2, H / 2)
    c.scale(z, z)
    c.translate(-cx, -cy)


# ------------------------------------------------------------------ partikel mengalir (sepanjang video)
_pr = random.Random(4)
PARTS = [(_pr.uniform(0, W + 200), _pr.uniform(0, H), _pr.uniform(15, 45), _pr.uniform(-35, -8),
          _pr.uniform(0, 6.3), _pr.uniform(0.4, 1.0)) for _ in range(150)]


def flow(c, T, a=1.0, speed=1.0):
    p = skia.Path()
    dots = skia.Path()
    for x0, y0, vx, vy, ph, sz in PARTS:
        trail = []
        for k in range(6):
            t = T - k * 0.05
            x = (x0 + vx * t * speed + 50 * math.sin(0.6 * t + ph)) % (W + 200) - 100
            y = (y0 + vy * t * speed + 40 * math.sin(0.45 * t + ph * 1.7)) % (H + 100) - 50
            trail.append((x, y))
        if max(abs(trail[0][0] - trail[-1][0]), abs(trail[0][1] - trail[-1][1])) > 200:
            continue
        p.addPath(poly(trail))
        dots.addCircle(trail[0][0], trail[0][1], 1.6 * sz)
    c.drawPath(p, pen(WHITE, 1.2, 0.10 * a))
    c.drawPath(dots, pen(WHITE, 0, 0.35 * a, fill=True))


# ------------------------------------------------------------------ babak

def b_hook(c, lt, dur, T):
    u = ease(lt / dur)
    camera(c, lerp(1.0, 1.08, u), 540, 860)
    sun = circle_path(790, 640, 170)
    line(c, sun, ease(prog(lt, 0.0, 1.0)), 3)
    rays = skia.Path()
    for i in range(16):
        a = math.radians(i * 22.5 + lt * 8)
        rays.addPath(poly([(790 + math.cos(a) * 200, 640 + math.sin(a) * 200), (790 + math.cos(a) * 240, 640 + math.sin(a) * 240)]))
    line(c, rays, ease(prog(lt, 0.6, 1.4)), 2.5, 0.6)
    horizon = poly([(500, 900), (1150, 900)])
    line(c, horizon, ease(prog(lt, 0.1, 0.8)), 2.5, 0.7)
    for i in range(5):
        y = 940 + i * 38
        line(c, poly([(560 + i * 30, y), (1150, y)]), ease(prog(lt, 0.3 + i * 0.08, 1.0)), 1.6, 0.25, glow=False)
    cliff = curve([(-80, 1400), (120, 1180), (330, 1040), (520, 985), (560, 1010), (585, 1100), (640, 1300), (700, 1500), (760, 1900)])
    line(c, cliff, ease(prog(lt, 0.0, 0.9)), 3.5)
    if lt > 0.5:
        k = ease_out(prog(lt, 0.5, 1.0))
        c.saveLayerAlpha(None, int(255 * k))
        person(c, 470, 990, 330, POSE["stand"], facing=1, col=WHITE, hat=False, kid="bag")
        c.restore()


HEART = heart_pts(540, 760, 15)
ARROW = resample(arrow_pts(540, 760, 230), len(HEART))


def b_keputusan(c, lt, dur, T):
    T0 = BY["keputusan"]["mula"] - 0.15
    t_bukan, t_kep = word_t("keputusan", "bukan") - T0, word_t("keputusan", "keputusan") - T0
    m = ease(prog(lt, t_kep - 0.1, t_kep + 0.5))
    beat = 1 + 0.06 * max(0, math.sin(lt * 7)) ** 8 * (1 - m)
    pts = HEART * (1 - m) + ARROW * m
    pts = (pts - [540, 760]) * beat + [540 + 60 * ease(prog(lt, t_kep + 0.5, dur)), 760]
    line(c, pts_path(pts), ease(prog(lt, 0.0, 0.8)), 5)
    # coretan 'bukan'
    k = ease(prog(lt, t_bukan, t_bukan + 0.35))
    if k > 0 and m < 1:
        c.saveLayerAlpha(None, int(255 * (1 - m)))
        line(c, poly([(300, 1000), (790, 520)]), k, 7)
        c.restore()
    if m > 0.6:
        for i in range(4):
            y = 700 + i * 40
            x0 = 220 - 120 * ease(prog(lt, t_kep + 0.4 + i * 0.05, dur))
            line(c, poly([(x0 - 120, y), (x0, y)]), 1, 2.5, 0.5 * (m - 0.6) / 0.4)


def clock(c, cx, cy, r, hm, hh, p=1.0):
    line(c, circle_path(cx, cy, r), p, 5)
    line(c, circle_path(cx, cy, r * 0.9), p, 1.6, 0.4, glow=False)
    ticks = skia.Path()
    for i in range(12):
        a = math.radians(i * 30)
        r0 = r * (0.74 if i % 3 == 0 else 0.8)
        ticks.addPath(poly([(cx + math.cos(a) * r0, cy + math.sin(a) * r0), (cx + math.cos(a) * r * 0.86, cy + math.sin(a) * r * 0.86)]))
    line(c, ticks, p, 3, 0.8, glow=False)
    am, ah = math.radians(hm - 90), math.radians(hh - 90)
    line(c, poly([(cx, cy), (cx + math.cos(am) * r * 0.72, cy + math.sin(am) * r * 0.72)]), p, 5)
    line(c, poly([(cx, cy), (cx + math.cos(ah) * r * 0.48, cy + math.sin(ah) * r * 0.48)]), p, 7)
    c.drawCircle(cx, cy, 9, pen(WHITE, 0, 1, fill=True))


def b_tunggu(c, lt, dur, T):
    camera(c, lerp(1.0, 1.05, lt / dur), 540, 860)
    clock(c, 540, 480, 190, lt * 420, lt * 35, ease(prog(lt, 0, 0.7)))
    # lengkung siang-malam berputar di belakang jam
    for k in range(2):
        a = lt * 2.2 + k * math.pi
        x, y = 540 + math.cos(a) * 330, 480 + math.sin(a) * 330
        if k == 0:
            c.drawCircle(x, y, 26, pen(WHITE, 0, 0.9, fill=True))
            c.drawCircle(x, y, 60, pen(WHITE, 0, 0.15, glow=20, fill=True))
        else:
            line(c, circle_path(x, y, 22), 1, 3, 0.7)
    bench = poly([(170, 1060), (910, 1060)])
    bench.addPath(poly([(200, 1060), (200, 1180)]))
    bench.addPath(poly([(880, 1060), (880, 1180)]))
    bench.addPath(poly([(170, 960), (910, 960)]))
    line(c, bench, ease(prog(lt, 0.1, 0.8)), 4)
    line(c, poly([(-50, 1180), (1130, 1180)]), 1, 2, 0.35, glow=False)
    for i, x in enumerate((300, 540, 780)):
        pose = dict(POSE["sit"])
        if i == 1:
            pose["aF"] = (70 + 10 * math.sin(lt * 3), 70)   # tengok jam tangan
            pose["head"] = 20
        if i == 2:
            pose["lF"] = (88, -88 + 12 * max(0, math.sin(lt * 12)))  # kaki menghentak
        k = ease_out(prog(lt, 0.2 + i * 0.12, 0.7 + i * 0.12))
        if k > 0:
            c.saveLayerAlpha(None, int(255 * k))
            person(c, x, 1180, 330, pose, facing=1, col=WHITE, hat=False, glow=True)
            c.restore()


CLOCK_PIECES = None


def b_takdatang(c, lt, dur, T):
    T0 = BY["takdatang"]["mula"] - 0.15
    t_crack = word_t("takdatang", "takkan") - T0
    t_break = word_t("takdatang", "datang") - T0
    cx, cy, r = 540, 700, 230
    if lt < t_break:
        jit = 6 * prog(lt, t_crack, t_break) * math.sin(lt * 80)
        clock(c, cx + jit, cy, r, 4.2 * 420 + 120, 4.2 * 35 + 40)
        k = ease(prog(lt, t_crack, t_crack + 0.25))
        crack = poly([(cx - 30, cy - r), (cx + 10, cy - 120), (cx - 40, cy - 40), (cx + 30, cy + 40), (cx - 10, cy + 130), (cx + 20, cy + r)])
        line(c, crack, k, 4)
        return
    s = lt - t_break
    rnd = random.Random(9)
    for i in range(24):
        a0 = math.radians(i * 15)
        arc = skia.Path()
        arc.addArc(skia.Rect.MakeXYWH(cx - r, cy - r, 2 * r, 2 * r), i * 15, 15)
        vx, vy = math.cos(a0 + math.radians(7)) * rnd.uniform(200, 600), math.sin(a0) * rnd.uniform(200, 600) - 300
        c.save()
        c.translate(vx * s, vy * s + 900 * s * s)
        mx, my = cx + math.cos(a0) * r, cy + math.sin(a0) * r
        c.translate(mx, my)
        c.rotate(rnd.uniform(-400, 400) * s)
        c.translate(-mx, -my)
        line(c, arc, 1, 5, max(0, 1 - s * 0.9))
        c.restore()
    for i, (L, wdt) in enumerate(((r * 0.72, 5), (r * 0.48, 7))):
        c.save()
        c.translate((i * 2 - 1) * 250 * s, -200 * s + 1000 * s * s)
        c.rotate((i * 2 - 1) * 300 * s)
        line(c, poly([(cx, cy), (cx, cy - L)]), 1, wdt, max(0, 1 - s))
        c.restore()


def icon_case(c, p):
    line(c, rrect(330, 640, 420, 290, 30), p, 5)
    line(c, rrect(470, 580, 140, 70, 18), p, 5)
    line(c, poly([(330, 740), (750, 740)]), p, 3, 0.7)
    line(c, rrect(515, 715, 50, 50, 8), p, 4)


def icon_chat(c, p, lt):
    b1 = rrect(230, 560, 400, 230, 50)
    b1.addPath(poly([(320, 790), (300, 860), (390, 790)]))
    line(c, b1, p, 5)
    b2 = rrect(450, 820, 400, 200, 50)
    b2.addPath(poly([(760, 1020), (790, 1080), (700, 1020)]))
    line(c, b2, ease(prog(p, 0.3, 1)), 5)
    for i in range(3):
        up = 10 * max(0, math.sin(lt * 9 - i * 0.8))
        c.drawCircle(370 + i * 60, 675 - up, 13, pen(WHITE, 0, p, fill=True))


def icon_trip(c, p, lt):
    trail = skia.Path()
    trail.moveTo(160, 1050)
    trail.cubicTo(360, 1000, 420, 700, 900, 560)
    eff = skia.DashPathEffect.Make([18, 18], -lt * 60)
    pt = pen(WHITE, 4, 0.6)
    pt.setPathEffect(skia.PathEffect.MakeCompose(eff, skia.TrimPathEffect.Make(0, min(1.0, p))) if p < 1 else eff)
    c.drawPath(trail, pt)
    meas = skia.PathMeasure(trail, False)
    pos, tan = meas.getPosTan(meas.getLength() * min(1.0, p))
    ang = math.degrees(math.atan2(tan.y(), tan.x()))
    plane = pts_path([(60, 0), (20, -10), (-10, -60), (-30, -60), (-10, -10), (-45, -10), (-60, -30), (-72, -30), (-62, 0),
                      (-72, 30), (-60, 30), (-45, 10), (-10, 10), (-30, 60), (-10, 60), (20, 10)])
    c.save()
    c.translate(pos.x(), pos.y())
    c.rotate(ang)
    c.scale(1.4, 1.4)
    fill(c, plane, BG)
    line(c, plane, 1, 3.5)
    c.restore()


def b_bukan(c, lt, dur, T):
    T0 = BY["bukan"]["mula"] - 0.15
    starts = [word_t("bukan", "bukan", i) - T0 for i in range(3)] + [dur + 0.2]
    for i in range(3):
        t0, t1 = starts[i] - 0.1, starts[i + 1] - 0.1
        if not (t0 <= lt < t1 + 0.2):
            continue
        k = lt - t0
        out = ease(prog(lt, t1 - 0.05, t1 + 0.2))
        c.save()
        c.translate(-500 * out, 0)
        c.saveLayerAlpha(None, int(255 * (1 - out)))
        p = ease(prog(k, 0, 0.55))
        [lambda: icon_case(c, p), lambda: icon_chat(c, p, k), lambda: icon_trip(c, p, k)][i]()
        c.restore()
        c.restore()


def scribble(c, cx, cy, r, T, a=1.0, n=5):
    for j in range(n):
        pts = []
        for i in range(36):
            ang = i / 36 * 2 * math.pi
            rr = r * (1 + 0.25 * math.sin(ang * 3 + T * 7 + j * 2) + 0.15 * math.sin(ang * 7 - T * 11 + j))
            pts.append((cx + math.cos(ang + j) * rr, cy + math.sin(ang + j) * rr * 0.8))
        line(c, curve(pts, closed=True), 1, 2.2, 0.55 * a, glow=False)


def b_gementar(c, lt, dur, T):
    T0 = BY["gementar"]["mula"] - 0.15
    t_kep = word_t("gementar", "keputusan") - T0
    t_go = word_t("gementar", "terus") - T0
    calm = ease(prog(lt, t_kep, t_kep + 0.6))
    walk = prog(lt, t_go, dur)
    x = 470 + 160 * walk
    line(c, poly([(-50, 1200), (1130, 1200)]), 1, 2, 0.35, glow=False)
    path = poly([(x + 60, 1200), (1150, 1200)])
    line(c, path, ease(prog(lt, t_go - 0.2, t_go + 0.6)), 5)
    shake = (1 - calm) * 5
    jx = shake * math.sin(lt * 70)
    if walk > 0:
        pose = walk_pose(lt * 7, ease(walk * 3), 8)
    else:
        pose = dict(POSE["stand"])
        pose["aF"], pose["aB"] = (20, 60), (15, 70)
    person(c, x + jx, 1200, 560, pose, facing=1, col=WHITE, hat=False, kid="bag")
    scribble(c, x + jx + 10, 680, lerp(230, 150, calm), T, lerp(1, 0.6, calm), 6)


def b_menyusul(c, lt, dur, T):
    u = lt / dur
    road = curve([(-100, 1300), (200, 1230), (500, 1260), (800, 1210), (1200, 1240)])
    line(c, road, 1, 4)
    line(c, curve([(-100, 1400), (300, 1350), (700, 1380), (1200, 1340)]), 1, 2, 0.3, glow=False)
    x = lerp(460, 640, u)
    T0 = BY["menyusul"]["mula"] - 0.15
    t_meet = word_t("menyusul", "di") - T0
    orb_x = lerp(-80, x, ease(prog(lt, 0.2, t_meet)))
    orb_y = 960 + 60 * math.sin(lt * 4) * (1 - prog(lt, 0, t_meet))
    if lt < t_meet + 0.3:
        a = 1 - prog(lt, t_meet, t_meet + 0.3)
        trail = [(orb_x - i * 40, orb_y + 30 * math.sin(lt * 4 - i * 0.4)) for i in range(8)]
        line(c, curve(trail), 1, 3, 0.5 * a)
        c.drawCircle(orb_x, orb_y, 70, pen(WHITE, 0, 0.25 * a, glow=30, fill=True))
        c.drawCircle(orb_x, orb_y, 22, pen(WHITE, 0, a, fill=True))
    glow = ease(prog(lt, t_meet, t_meet + 0.5))
    if glow > 0:
        c.drawCircle(x + 20, 960, 260 * (1 + 0.05 * math.sin(lt * 6)), pen(WHITE, 0, 0.12 * glow, glow=80, fill=True))
        k = prog(lt, t_meet, t_meet + 0.7)
        if k < 1:
            c.drawCircle(x + 20, 960, 40 + 400 * k, pen(WHITE, 3, 0.7 * (1 - k)))
    person(c, x, 1250, 520, walk_pose(lt * 7, 1.0, 6), facing=1, col=WHITE, hat=False, kid="bag")


WORDS_WIND = ["TUNGGU", "NANTI", "BELUM MASA", "TAK SEDIA", "ESOK SAJA", "JANGAN", "TAKUT", "NANTI DULU", "BAHAYA"]
FONT_WIND = skia.Font(skia.Typeface.MakeFromFile(FONT_DIR + "Montserrat-Black.ttf"), 64)


def b_pilih(c, lt, dur, T):
    T0 = BY["pilih"]["mula"] - 0.15
    t_pilih = word_t("pilih", "pilih") - T0
    rnd = random.Random(3)
    for i in range(12):
        word = WORDS_WIND[i % len(WORDS_WIND)]
        y0 = rnd.uniform(360, 1120)
        speed = rnd.uniform(380, 700)
        size = rnd.uniform(0.55, 1.25)
        x = 1250 - ((lt * speed + rnd.uniform(0, 1600)) % 1700)
        y = y0 + 40 * math.sin(x / 160 + i)
        a = rnd.uniform(0.2, 0.55)
        c.save()
        c.translate(x, y)
        c.scale(size, size)
        if abs(x - 520) < 160 and abs(y - 900) < 330:  # lari mengelilingi watak
            c.translate(0, 120 if y > 900 else -120)
        c.drawString(word, 0, 0, FONT_WIND, pen(WHITE, 0, a, fill=True) if i % 3 else pen(WHITE, 2, a))
        c.restore()
    wind = skia.Path()
    for i in range(10):
        y = 420 + i * 90
        x = 1200 - ((lt * 900 + i * 230) % 1500)
        wind.addPath(curve([(x, y), (x + 120, y - 15), (x + 260, y)]))
    c.drawPath(wind, pen(WHITE, 2, 0.35))
    k = ease(prog(lt, t_pilih - 0.1, t_pilih + 0.6))
    line(c, poly([(600, 1250), (1150, 1250)]), k, 6)
    line(c, poly([(-50, 1250), (600, 1250)]), 1, 2.5, 0.4, glow=False)
    pose = walk_pose(lt * 5.5, 0.85, 18)
    person(c, 520, 1250, 560, pose, facing=1, col=WHITE, hat=False, kid="bag")


def b_berani(c, lt, dur, T):
    T0 = BY["berani"]["mula"] - 0.15
    t_zoom = word_t("berani", "bukannya") - T0
    z = ease(prog(lt, t_zoom - 0.3, t_zoom + 0.4))
    camera(c, lerp(1.0, 2.3, z), lerp(540, 552, z), lerp(860, 650, z))
    mt = curve([(-100, 1350), (150, 1050), (300, 1000), (420, 820), (540, 705), (640, 790), (760, 900), (900, 1080), (1200, 1300)])
    line(c, mt, ease(prog(lt, 0, 0.8)), 4)
    line(c, curve([(380, 900), (450, 880), (500, 960)]), ease(prog(lt, 0.3, 1.0)), 2, 0.5, glow=False)
    line(c, curve([(620, 820), (700, 900), (680, 980)]), ease(prog(lt, 0.3, 1.0)), 2, 0.5, glow=False)
    pole = poly([(610, 705), (610, 470)])
    line(c, pole, ease(prog(lt, 0.4, 0.9)), 4)
    flag = [(610, 470)] + [(610 + i * 30, 485 + 18 * math.sin(lt * 6 - i * 0.7) + i * 2) for i in range(1, 6)] + \
           [(610 + i * 30, 575 + 18 * math.sin(lt * 6 - i * 0.7)) for i in range(5, 0, -1)] + [(610, 560)]
    if lt > 0.7:
        line(c, curve(flag), ease(prog(lt, 0.7, 1.1)), 3.5)
    pose = dict(POSE["stand"])
    pose["aF"] = (150, 0)
    person(c, 545, 712, 220, pose, facing=1, col=WHITE, hat=False, kid="bag")
    if z > 0:
        beat = 1 + 0.18 * max(0, math.sin(lt * 14)) ** 6
        h = heart_pts(560, 600, 1.0 * beat, 120)
        c.saveLayerAlpha(None, int(255 * z))
        line(c, pts_path(h), 1, 2.4)
        c.restore()
    if z > 0:
        c.save()
        c.resetMatrix()
        y = 1150
        pts = []
        for i in range(70):
            x = i * 16
            ph = (x / 1080 * 3 - lt * 2.2) % 1
            spike = 0
            if 0.40 < ph < 0.43:
                spike = -170
            elif 0.43 < ph < 0.46:
                spike = 110
            elif 0.46 < ph < 0.48:
                spike = -40
            pts.append((x, y + spike))
        line(c, poly(pts), z, 3)
        c.restore()


def b_esok(c, lt, dur, T):
    camera(c, lerp(1.0, 1.06, lt / dur), 540, 860)
    win = rrect(560, 380, 380, 420, 6)
    win.addPath(poly([(750, 380), (750, 800)]))
    win.addPath(poly([(560, 590), (940, 590)]))
    line(c, win, ease(prog(lt, 0, 0.6)), 4)
    c.save()
    c.clipRect(skia.Rect.MakeXYWH(560, 380, 380, 420))
    sy = lerp(860, 700, ease(lt / dur))
    c.drawCircle(750, sy, 80, pen(WHITE, 0, 0.9, fill=True))
    c.drawCircle(750, sy, 160, pen(WHITE, 0, 0.18, glow=40, fill=True))
    c.restore()
    bed = rrect(120, 1000, 720, 120, 20)
    bed.addPath(poly([(120, 1120), (120, 1220)]))
    bed.addPath(poly([(840, 1120), (840, 1220)]))
    bed.addPath(poly([(120, 880), (120, 1120)]))
    line(c, bed, ease(prog(lt, 0.1, 0.7)), 4)
    blanket = curve([(300, 1000), (360, 930), (520, 910), (700, 940), (830, 1000)])
    line(c, blanket, ease(prog(lt, 0.2, 0.8)), 3.5)
    line(c, ellipse(220, 970, 70, 32), ease(prog(lt, 0.2, 0.8)), 3)
    line(c, circle_path(270, 935, 46), ease(prog(lt, 0.3, 0.9)), 3.5)
    zz = skia.Path()
    for i in range(3):
        k = (lt * 0.8 + i * 0.33) % 1
        x, y, s = 330 + k * 90, 860 - k * 160, 18 + 14 * k
        zz.addPath(poly([(x, y), (x + s, y), (x, y + s), (x + s, y + s)]))
    c.drawPath(zz, pen(WHITE, 3, 0.6))
    shake = 7 * math.sin(lt * 60) * (lt % 0.8 < 0.45)
    cx, cy = 960, 1010
    line(c, rrect(cx - 75 + shake, cy - 150, 150, 150, 16), 1, 4)
    line(c, circle_path(cx + shake, cy - 75, 48), 1, 3)
    line(c, poly([(cx + shake, cy - 75), (cx + shake, cy - 108)]), 1, 3)
    line(c, poly([(cx + shake, cy - 75), (cx + 22 + shake, cy - 75)]), 1, 3)
    if lt % 0.8 < 0.45:
        for s_ in (-1, 1):
            for j in range(2):
                r = 115 + j * 30
                arc = skia.Path()
                arc.addArc(skia.Rect.MakeXYWH(cx - r, cy - 75 - r, 2 * r, 2 * r), -90 + s_ * 35 - 15, 30)
                line(c, arc, 1, 3, 0.7)


def b_pergi(c, lt, dur, T):
    T0 = BY["pergi"]["mula"] - 0.15
    t_go = word_t("pergi", "pergi") - T0
    flash_t = t_go + 0.55
    if lt > flash_t + 0.15:
        end_scene(c, lt - flash_t - 0.15, T)
        f = 1 - prog(lt, flash_t + 0.15, flash_t + 0.9)
        if f > 0:
            c.drawRect(skia.Rect.MakeWH(W, H), pen(WHITE, 0, f, fill=True))
        return
    open_ = ease(prog(lt, 0.1, t_go))
    dx0, dy0, dw, dh = 380, 520, 320, 640
    light = poly([(dx0, dy0), (dx0 + dw, dy0), (dx0 + dw + 520, 1920), (dx0 - 520, 1920)], closed=True)
    c.drawPath(light, pen(WHITE, 0, 0.06 * open_, glow=60, fill=True))
    c.drawRect(skia.Rect.MakeXYWH(dx0, dy0, dw, dh), pen(WHITE, 0, 0.92 * open_, fill=True))
    door_w = dw * (1 - 0.85 * open_)
    door = poly([(dx0, dy0), (dx0 + door_w, dy0 + 30 * open_), (dx0 + door_w, dy0 + dh - 30 * open_), (dx0, dy0 + dh)], closed=True)
    fill(c, door, BG)
    line(c, door, 1, 4)
    line(c, rrect(dx0 - 30, dy0 - 30, dw + 60, dh + 30, 4), 1, 4)
    line(c, poly([(-50, 1160), (1130, 1160)]), 1, 2.5, 0.4, glow=False)
    run = prog(lt, t_go - 0.3, flash_t)
    x = lerp(260, 540, ease(run))
    ground = lerp(1500, 1160, ease(run))
    s = lerp(620, 300, ease(run))
    if run > 0:
        streaks = skia.Path()
        for i in range(14):
            y = 300 + i * 110
            xx = (i * 173 + lt * 2600) % 1400 - 200
            streaks.addPath(poly([(xx, y), (xx - 260, y)]))
        c.drawPath(streaks, pen(WHITE, 3, 0.35 * run))
        pose = walk_pose(lt * 14, 1.4, 24)
    else:
        pose = dict(POSE["stand"])
    person(c, x, ground, s, pose, facing=1, col=WHITE, hat=False, kid="bag")
    fl = prog(lt, flash_t - 0.2, flash_t + 0.15)
    if fl > 0:
        c.drawRect(skia.Rect.MakeWH(W, H), pen(WHITE, 0, ease(fl), fill=True))


FONT_END = skia.Font(skia.Typeface.MakeFromFile(FONT_DIR + "Montserrat-Black.ttf"), 120)
FONT_SUB = skia.Font(skia.Typeface.MakeFromFile(FONT_DIR + "Montserrat-SemiBold.ttf"), 40)


def petal(cx, cy, ang, L, wdt):
    p = skia.Path()
    p.moveTo(0, 0)
    p.cubicTo(wdt, -L * 0.3, wdt * 0.8, -L * 0.85, 0, -L)
    p.cubicTo(-wdt * 0.8, -L * 0.85, -wdt, -L * 0.3, 0, 0)
    m = skia.Matrix()
    m.setRotate(ang)
    m.postTranslate(cx, cy)
    p.transform(m)
    return p


def end_scene(c, lt, T):
    """Benih -> batang -> daun -> bunga mekar + teks penutup."""
    gx, gy = 540, 1100
    line(c, poly([(200, gy), (880, gy)]), ease(prog(lt, 0, 0.5)), 2.5, 0.5, glow=False)
    c.drawPath(ellipse(gx, gy - 6, 14, 9), pen(WHITE, 0, 1 - prog(lt, 0.6, 1.0), fill=True))
    stem = skia.Path()
    stem.moveTo(gx, gy)
    stem.cubicTo(gx - 60, gy - 150, gx + 70, gy - 260, gx, gy - 420)
    line(c, stem, ease(prog(lt, 0.3, 1.2)), 5)
    for side, t0, yy in ((-1, 0.8, gy - 140), (1, 1.0, gy - 250)):
        k = ease_out(prog(lt, t0, t0 + 0.5))
        if k > 0:
            leaf = petal(gx + side * 8, yy, side * 62, 150 * k, 50 * k)
            line(c, leaf, 1, 3.5)
    cx, cy = gx, gy - 420
    for ring, (n, L, wdt, t0, rot) in enumerate(((8, 170, 62, 1.25, 0), (8, 120, 48, 1.5, 22.5))):
        for i in range(n):
            k = ease_out(prog(lt, t0 + i * 0.04, t0 + 0.6 + i * 0.04))
            if k <= 0:
                continue
            a = rot + i * 360 / n + 4 * math.sin(T * 1.5 + i)
            p = petal(cx, cy, a, L * k, wdt * k)
            if ring == 1:
                fill(c, p, BG)
            line(c, p, 1, 3.5 if ring == 0 else 3)
    k = ease_out(prog(lt, 1.8, 2.2))
    if k > 0:
        c.drawCircle(cx, cy, 160 * k, pen(WHITE, 0, 0.12, glow=50, fill=True))
        c.drawCircle(cx, cy, 34 * k, pen(WHITE, 0, 1, fill=True))
    # debunga naik
    rnd = random.Random(1)
    for i in range(26):
        st = 2.0 + rnd.uniform(0, 1.5)
        if lt < st:
            continue
        s = lt - st
        x = cx + rnd.uniform(-60, 60) + 80 * math.sin(s * 1.3 + i) + rnd.uniform(-1, 1) * s * 90
        y = cy - s * rnd.uniform(90, 220)
        c.drawCircle(x, y, rnd.uniform(2, 5), pen(WHITE, 0, max(0, 0.8 - s * 0.25), fill=True))
    for i, (txt, font, y, t0) in enumerate((("MULA", FONT_END, 1300, 1.6), ("HARI INI.", FONT_END, 1430, 1.8),
                                          ("Kongsi dengan seseorang yang perlu dengar ini.", FONT_SUB, 1560, 2.6))):
        k = ease_out(prog(lt, t0, t0 + 0.45))
        if k <= 0:
            continue
        wd = font.measureText(txt)
        c.save()
        c.translate(W / 2, y)
        sc = lerp(1.25, 1.0, k)
        c.scale(sc, sc)
        if i < 2:
            c.drawString(txt, -wd / 2, 0, font, pen(WHITE, 0, 0.3 * k, glow=16, fill=True))
        c.drawString(txt, -wd / 2, 0, font, pen(WHITE, 0, k * (1 if i < 2 else 0.7), fill=True))
        c.restore()


SCENES = {"hook": b_hook, "keputusan": b_keputusan, "tunggu": b_tunggu, "takdatang": b_takdatang, "bukan": b_bukan,
          "gementar": b_gementar, "menyusul": b_menyusul, "pilih": b_pilih, "berani": b_berani, "esok": b_esok,
          "pergi": b_pergi}
# kedudukan teks kinetik bagi setiap babak
CAP_Y = {"takdatang": 1330, "pergi": 1420}
STARTS = [0.0] + [b["mula"] - 0.15 for b in BARIS[1:]]
ENDS = STARTS[1:] + [JUMLAH]
XFADE = 0.38
SHAKES = [word_t("hook", "bersedia"), word_t("keputusan", "keputusan"), word_t("takdatang", "datang"),
          word_t("pergi", "pergi")]


def draw_scene(c, k, t):
    c.save()
    SCENES[BARIS[k]["babak"]](c, t - STARTS[k], ENDS[k] - STARTS[k], t)
    c.restore()


def wave_clip(u, T, vertical):
    """Kawasan berbentuk gelombang untuk peralihan 'mengalir'."""
    pts = []
    if vertical:
        X = lerp(-150, W + 150, u)
        for i in range(41):
            y = i * H / 40
            pts.append((X + 70 * math.sin(y / 170 + T * 5), y))
        pts += [(-10, H), (-10, 0)]
    else:
        Y = lerp(-150, H + 150, u)
        for i in range(41):
            x = i * W / 40
            pts.append((x, Y + 70 * math.sin(x / 150 + T * 5)))
        pts += [(W, -10), (0, -10)]
    return pts


# ------------------------------------------------------------------ tipografi kinetik
TF_BLACK = skia.Typeface.MakeFromFile(FONT_DIR + "Montserrat-Black.ttf")
TF_BOLD = skia.Typeface.MakeFromFile(FONT_DIR + "Montserrat-SemiBold.ttf")
KEY = {"bersedia", "keputusan", "perasaan", "sempurna", "takut", "yakin", "datang", "kerja", "perbualan", "perjalanan",
       "gementar", "izin", "melangkah", "menyusul", "sendiri", "pilih", "tunggu", "berani", "berhenti", "esok", "pergi",
       "senyap", "takkan", "susah"}
SIZE_KEY, SIZE_STD, MAXW = 132, 62, 960


def clean(w):
    return w.strip(".,!?…").replace("...", "")


def is_key(w):
    return clean(w).lower() in KEY


def word_style(w, n_key, babak=""):
    key = is_key(w)
    text = clean(w).upper() if key else clean(w).lower()
    size = SIZE_KEY if key else SIZE_STD
    if babak == "pergi" and clean(w).lower() == "pergi":
        size = 230
    font = skia.Font(TF_BLACK if key else TF_BOLD, size)
    wd = font.measureText(text)
    if wd > MAXW:
        size *= MAXW / wd
        font = skia.Font(TF_BLACK if key else TF_BOLD, size)
        wd = font.measureText(text)
    return dict(text=text, font=font, size=size, w=wd, key=key, outline=key and n_key % 2 == 1)


def build_pages():
    pages = []
    for b in BARIS:
        cur, nk = [], 0
        for w in b["kata"]:
            cur.append(w)
            nk += is_key(w["k"])
            if w["k"][-1] in ".,?!" or len(cur) == 4 or nk == 2:
                pages.append((b["babak"], cur))
                cur, nk = [], 0
        if cur:
            pages.append((b["babak"], cur))
    out = []
    n_key = 0
    for i, (babak, words) in enumerate(pages):
        styled = []
        for w in words:
            st = word_style(w["k"], n_key, babak)
            n_key += st["key"]
            st.update(mula=w["mula"], tamat=w["tamat"])
            styled.append(st)
        # susun baris
        lines, cur, cw = [], [], 0
        for st in styled:
            gap = 22 if cur else 0
            if cur and cw + gap + st["w"] > MAXW:
                lines.append(cur)
                cur, cw, gap = [], 0, 0
            cur.append(st)
            cw += gap + st["w"]
        lines.append(cur)
        start = words[0]["mula"] - 0.05
        nxt = pages[i + 1][1][0]["mula"] - 0.16 if i + 1 < len(pages) else JUMLAH
        end = min(nxt, words[-1]["tamat"] + 0.9)
        if babak == "pergi" and i == len(pages) - 1:
            end = words[-1]["tamat"] + 0.35
        out.append(dict(babak=babak, start=start, end=end, lines=lines))
    return out


PAGES = build_pages()


def kinetic(c, t):
    for pg in PAGES:
        if not (pg["start"] <= t < pg["end"] + 0.1):
            continue
        out = prog(t, pg["end"], pg["end"] + 0.1)
        heights = [max(st["size"] for st in ln) * 1.05 + 8 for ln in pg["lines"]]
        total = sum(heights)
        y = CAP_Y.get(pg["babak"], 1450) - total / 2
        for ln, hgt in zip(pg["lines"], heights):
            y += hgt
            lw = sum(st["w"] for st in ln) + 22 * (len(ln) - 1)
            x = W / 2 - lw / 2
            for st in ln:
                k = prog(t, st["mula"] - 0.04, st["mula"] + 0.2)
                if k > 0:
                    e = ease_out(k)
                    sc = (1 + (0.7 if st["key"] else 0.3) * (1 - e)) * (1 - 0.1 * out)
                    a = e * (1 - out)
                    speaking = st["mula"] - 0.04 <= t < st["tamat"] + 0.1
                    c.save()
                    cx = x + st["w"] / 2
                    c.translate(cx, y - st["size"] * 0.35 + 30 * (1 - e) - 40 * out)
                    c.scale(sc, sc)
                    c.translate(-cx, -(y - st["size"] * 0.35))
                    if st["key"]:
                        c.drawString(st["text"], x, y, st["font"], pen(WHITE, 0, 0.35 * a, glow=18, fill=True))
                    c.drawString(st["text"], x, y + 6, st["font"], pen((0, 0, 0), 0, 0.8 * a, glow=8, fill=True))
                    if st["outline"]:
                        c.drawString(st["text"], x, y, st["font"], pen(BG, 0, a, fill=True))
                        c.drawString(st["text"], x, y, st["font"], pen(WHITE, 3.2, a))
                    else:
                        col = WHITE if (st["key"] or speaking) else (175, 175, 175)
                        c.drawString(st["text"], x, y, st["font"], pen(col, 0, a, fill=True))
                    if st["key"]:
                        ul = ease(prog(t, st["mula"] + 0.08, st["mula"] + 0.4))
                        c.drawPath(poly([(x, y + 22), (x + st["w"] * ul, y + 22)]), pen(WHITE, 5, a))
                    c.restore()
                x += st["w"] + 22


# ------------------------------------------------------------------ bingkai
VIGNETTE = skia.Paint(Shader=skia.GradientShader.MakeRadial(
    (W / 2, H / 2), H * 0.75, [skia.ColorSetARGB(0, 0, 0, 0), skia.ColorSetARGB(0, 0, 0, 0), skia.ColorSetARGB(220, 0, 0, 0)], [0.0, 0.5, 1.0]))


def render_frame(t, buf=None):
    if buf is None:
        buf = np.zeros((H, W, 4), np.uint8)
    surf = skia.Surface(buf)
    c = surf.getCanvas()
    c.clear(skia.ColorSetARGB(255, *BG))
    shake = sum(math.exp(-(t - s) * 9) * (t >= s) for s in SHAKES)
    if shake > 0.01:
        c.translate(14 * shake * math.sin(t * 90), 10 * shake * math.cos(t * 77))
    flow(c, t, 0.9)
    k = max(i for i, s in enumerate(STARTS) if s <= t)
    if k > 0 and t - STARTS[k] < XFADE:
        u = ease((t - STARTS[k]) / XFADE)
        vertical = k % 2 == 1
        pts = wave_clip(u, t, vertical)
        new_area = poly(pts, closed=True)
        old_area = skia.Op(poly([(-50, -50), (W + 50, -50), (W + 50, H + 50), (-50, H + 50)], closed=True), new_area,
                           skia.PathOp.kDifference_PathOp)
        c.save()
        c.clipPath(old_area, doAntiAlias=True)
        draw_scene(c, k - 1, t)
        c.restore()
        c.save()
        c.clipPath(new_area, doAntiAlias=True)
        c.clear(skia.ColorSetARGB(255, *BG))
        flow(c, t, 0.9)
        draw_scene(c, k, t)
        c.restore()
        edge = poly(pts[:41])
        line(c, edge, 1, 4, 0.9)
    else:
        draw_scene(c, k, t)
    c.resetMatrix()
    c.drawRect(skia.Rect.MakeWH(W, H), VIGNETTE)
    kinetic(c, t)
    # sedikit butiran filem
    return buf


def render_chunk(args):
    i0, i1, path = args
    proc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS),
         "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", str(path)],
        stdin=subprocess.PIPE)
    buf = np.zeros((H, W, 4), np.uint8)
    for i in range(i0, i1):
        proc.stdin.write(render_frame(i / FPS, buf).tobytes())
    proc.stdin.close()
    proc.wait()
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--still", type=float, nargs="*")
    ap.add_argument("--sheet", action="store_true")
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    BUILD.mkdir(exist_ok=True)
    OUT.mkdir(exist_ok=True)
    from PIL import Image
    if a.still:
        for t in a.still:
            Image.fromarray(render_frame(t)[:, :, :3]).save(BUILD / f"still_{t:05.2f}.png")
        return
    if a.sheet:
        times = [STARTS[k] + (ENDS[k] - STARTS[k]) * f for k in range(len(BARIS)) for f in (0.35, 0.85)]
        times = times[:20]
        sheet = Image.new("RGB", (216 * 5, 384 * 4))
        for i, t in enumerate(times):
            sheet.paste(Image.fromarray(render_frame(t)[:, :, :3]).resize((216, 384)), ((i % 5) * 216, (i // 5) * 384))
        sheet.save(BUILD / "sheet.png")
        return
    n = int(JUMLAH * FPS)
    jobs = a.jobs
    bounds = [round(n * j / jobs) for j in range(jobs + 1)]
    chunks = [(bounds[j], bounds[j + 1], BUILD / f"part{j}.mp4") for j in range(jobs)]
    with Pool(jobs) as pool:
        for p in pool.imap(render_chunk, chunks):
            print("siap", p, flush=True)
    (BUILD / "parts.txt").write_text("".join(f"file '{p.name}'\n" for _, _, p in chunks))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(BUILD / "parts.txt"),
                    "-c", "copy", str(BUILD / "video_bisu.mp4")], check=True)
    audio = BUILD / "audio.wav"
    if not audio.exists():
        sys.exit("Jalankan muzik.py dahulu untuk menghasilkan build/audio.wav")
    out = OUT / "bersedia.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(BUILD / "video_bisu.mp4"), "-i", str(audio),
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out)], check=True)
    print("Output:", out)


if __name__ == "__main__":
    main()
