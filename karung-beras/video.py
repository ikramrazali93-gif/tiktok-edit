"""Render video 'Karung Beras' (9:16, 30fps) dengan sari kata perkataan demi perkataan.

  python3 video.py               # render penuh -> output/karung-beras.mp4
  python3 video.py --still 12.5  # simpan satu bingkai (PNG) pada saat tertentu
  python3 video.py --sheet       # helaian kenalan satu bingkai setiap babak
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

from lukis import (BG, GOLD, H, POSE, W, WHITE, bird, car, cash, clamp, coin, curve, dim, ease, ease_out, ellipse,
                   fill, glow_dot, gold_bar, grain_layout, grains, grass, house, house_card, ink, lerp, moon, neon,
                   pen, person, poly, prog, sack, stars, tree, truck_back, walk_pose)

ROOT = Path(__file__).parent
BUILD = ROOT / "build"
OUT = ROOT / "output"
FPS = 30
KAD_AKHIR = 2.6  # saat kad penutup selepas narasi
FONT = "/usr/share/fonts/truetype/montserrat/Montserrat-ExtraBold.ttf"

MASA = json.loads((BUILD / "masa.json").read_text())
BARIS = MASA["baris"]
JUMLAH = MASA["jumlah"] + KAD_AKHIR

# ------------------------------------------------------------------ dunia jalan raya
HY = 700  # garis ufuk


def persp(y):
    return max(0.0, (y - HY) / 1220)


def depth_y(d):
    return HY + 1220 / d


def edge_x(y, top, bottom):
    return lerp(top, bottom, (y - HY) / 1220)


SACK = (860, 1420)
SACK_S = persp(SACK[1]) * 1.0
GRAINS = grain_layout()
_r = random.Random(11)
GRASS = []
for _ in range(120):
    y = HY + 1220 * _r.random() ** 1.6 + 8
    side = _r.random()
    if side < 0.7:
        x = _r.uniform(edge_x(y, 446, 800) + 20, 1100)
    else:
        x = _r.uniform(-60, edge_x(y, 395, -520) - 20)
    GRASS.append((x, y, persp(y) * 1.5 + 0.15))
GRASS.sort(key=lambda g: g[1])


def road_world(c, T, sack_on=True, grains_alive=None, spread=1.0, torn=1.0, sack_pos=None, sack_rot=0.0):
    stars(c, 3, 80, 0, HY - 40, T)
    moon(c, 870, 250, 44)
    # barisan pokok di ufuk
    rnd = random.Random(5)
    pts = [(-60, HY)]
    x = -60
    while x < 1140:
        x += rnd.uniform(30, 70)
        pts.append((x, HY - rnd.uniform(12, 60)))
    dim(c, curve(pts), 2.0, 0.28)
    for tx, ts, sd in ((980, 0.55, 2), (690, 0.35, 4), (120, 0.4, 6)):
        tree(c, tx, HY + 4, ts, 0.3, sd)
    # sawah
    fr = random.Random(8)
    for d in (1.5, 2.3, 3.4, 5.0, 7.5, 11.0):
        y = depth_y(d)
        x0 = edge_x(y, 446, 800) + 40 + fr.uniform(0, 120)
        x1 = x0 + fr.uniform(180, 520)
        dim(c, curve([(x0, y), ((x0 + x1) / 2, y + fr.uniform(-6, 6)), (x1, y + 10 / d)]), 1.4, 0.13)
    # tiang elektrik
    tops = []
    for d in (1.15, 1.6, 2.3, 3.4, 5.0, 7.5, 11.5):
        y = depth_y(d)
        x = edge_x(y, 330, -260)
        h = 1000 * persp(y)
        p = poly([(x, y), (x, y - h)])
        p.addPath(poly([(x - 60 * persp(y), y - h * 0.92), (x + 60 * persp(y), y - h * 0.92)]))
        dim(c, p, max(1.4, 5 * persp(y)), 0.4)
        tops.append((x, y - h * 0.92))
    wires = skia.Path()
    for (x0, y0), (x1, y1) in zip(tops, tops[1:]):
        wires.moveTo(x0, y0)
        wires.quadTo((x0 + x1) / 2, (y0 + y1) / 2 + 30 * persp(y0), x1, y1)
    dim(c, wires, 1.6, 0.3)
    # jalan
    road = poly([(400, HY), (440, HY), (800, 1925), (-520, 1925)], closed=True)
    fill(c, road, (14, 14, 16))
    edges = poly([(400, HY), (-520, 1920)])
    edges.addPath(poly([(440, HY), (800, 1920)]))
    ink(c, edges, 3, 0.55)
    ink(c, poly([(434, HY), (735, 1920)]), 5, 0.7)
    dashes = skia.Path()
    for d in np.geomspace(1.05, 25, 18):
        y0, y1 = depth_y(d), depth_y(d * 1.18)
        dashes.addPath(poly([(edge_x(y0, 420, 140), y0), (edge_x(y1, 420, 140), y1)]))
    ink(c, dashes, 6, 0.7)
    for gx, gy, gs in GRASS:
        grass(c, gx, gy, gs, 0.4)
    if sack_on:
        sx, sy = sack_pos or SACK
        if sack_pos:
            c.save()
            c.translate(sx, sy)
            c.rotate(sack_rot)
            sack(c, 0, 0, SACK_S, torn=0)
            c.restore()
        else:
            sack(c, sx, sy, SACK_S, torn=torn)
    if grains_alive is not None:
        grains(c, SACK[0], SACK[1], SACK_S, GRAINS, grains_alive, spread)


def truck_at(c, T):
    d = 1.05 + 1.25 * T
    y = depth_y(d)
    a = clamp(1 - (d - 10) / 6)
    if a <= 0:
        return
    x = lerp(edge_x(y, 420, 140), edge_x(y, 440, 800), 0.5)
    c.saveLayerAlpha(None, int(255 * a))
    truck_back(c, x, y, 1.15 / d)
    c.restore()
    return x, y, 1.15 / d


def bird_spot(i):
    return [(690, 1452), (575, 1440), (790, 1495)][i]


def bird_scale(y):
    return persp(y) * 1.75


def bird_track(lt, spot, t_land, t_leave, start, end, fly=1.2):
    if lt < t_land:
        u = ease_out(prog(lt, t_land - fly, t_land))
        x = lerp(start[0], spot[0], u)
        y = lerp(start[1], spot[1], u) - math.sin(u * math.pi) * 60
        return dict(x=x, y=y, pose="fly", phase=lt * 20, peck=0, grain=False, facing=1 if spot[0] > start[0] else -1)
    if lt < t_leave:
        k = lt - t_land
        peck = max(0.0, math.sin(k * 6.5)) ** 2
        return dict(x=spot[0], y=spot[1], pose="stand", phase=0, peck=peck, grain=k > 1.0 and peck < 0.3, facing=None)
    u = prog(lt, t_leave, t_leave + fly) ** 1.6
    x = lerp(spot[0], end[0], u)
    y = lerp(spot[1], end[1], u)
    return dict(x=x, y=y, pose="fly", phase=lt * 20, peck=0, grain=True, facing=1 if end[0] > spot[0] else -1)


def draw_bird(c, kind, b, face_default=1):
    s = bird_scale(b["y"] if b["pose"] != "fly" else max(b["y"], 1300))
    bird(c, b["x"], b["y"], s, kind, b["pose"], b["facing"] or face_default, b["phase"], b["peck"], b["grain"])


def camera(c, z, cx, cy):
    c.translate(W / 2, H / 2)
    c.scale(z, z)
    c.translate(-cx, -cy)


# ------------------------------------------------------------------ babak
ALL = [1.0] * len(GRAINS)


def b_lori(c, lt, dur, T):
    camera(c, lerp(1.0, 1.06, lt / dur), 540, lerp(1120, 1160, lt / dur))
    t_drop, t_land = 0.5, 1.2
    info = None
    if lt < t_drop:
        road_world(c, T, sack_on=False)
        info = truck_at(c, T)
        return
    land_u = prog(lt, t_drop, t_land)
    road_world(c, T, sack_on=land_u >= 1,
               grains_alive=[ease_out(prog(lt, t_land + i * 0.002, t_land + 0.4 + i * 0.002)) for i in range(len(GRAINS))] if land_u >= 1 else None,
               spread=lerp(0.3, 1.0, ease_out(prog(lt, t_land, t_land + 0.8))),
               torn=ease(prog(lt, t_land, t_land + 0.3)))
    tx, ty, ts = truck_at(c, T)
    if land_u < 1:
        x0, y0 = tx + 180 * ts, ty - 520 * ts
        x = lerp(x0, SACK[0], land_u)
        y = lerp(y0, SACK[1], land_u ** 2) - math.sin(land_u * math.pi) * 90
        c.save()
        c.translate(x, y)
        c.rotate(land_u * 160)
        sack(c, 0, 0, lerp(ts, SACK_S, land_u), torn=0)
        c.restore()
    else:
        puff = prog(lt, t_land, t_land + 0.9)
        if puff < 1:
            for i in range(6):
                ang = math.pi + i * math.pi / 5
                r = 30 + puff * 140
                c.drawCircle(SACK[0] + math.cos(ang) * r, SACK[1] + math.sin(ang) * r * 0.25 - 20, 18 + puff * 30,
                             pen(WHITE, 0, 0.25 * (1 - puff), glow=12, fill=True))


def b_koyak(c, lt, dur, T):
    u = ease(lt / dur)
    camera(c, lerp(1.15, 1.6, u), lerp(620, 740, u), lerp(1060, 1300, u))
    road_world(c, T, grains_alive=ALL)
    truck_at(c, T)


def birds_scene(c, lt, dur, T, plan, z0, z1, center):
    u = ease(lt / dur)
    camera(c, lerp(z0, z1, u), center[0], center[1])
    road_world(c, T, grains_alive=ALL)
    tracks = []
    for kind, spot, t_land, t_leave, start, end in plan:
        tracks.append((kind, bird_track(lt, spot, t_land, t_leave, start, end)))
    for kind, b in sorted(tracks, key=lambda kb: kb[1]["y"]):
        draw_bird(c, kind, b, face_default=-1 if b["x"] > 700 else 1)


def b_pipit(c, lt, dur, T):
    plan = [("pipit", bird_spot(0), 1.2, dur - 1.1, (1100, 900), (300, 850))]
    birds_scene(c, lt, dur, T, plan, 1.9, 2.0, (700, 1360))


def b_gagak(c, lt, dur, T):
    plan = [("gagak", bird_spot(1), 1.0, dur - 0.9, (300, 900), (1150, 950))]
    birds_scene(c, lt, dur, T, plan, 1.95, 2.0, (680, 1360))


def b_merpati(c, lt, dur, T):
    plan = [("merpati", bird_spot(2), 1.0, dur - 0.7, (1200, 1000), (1200, 850))]
    birds_scene(c, lt, dur, T, plan, 1.9, 1.98, (740, 1370))


def b_cukup(c, lt, dur, T):
    plan = [
        ("pipit", bird_spot(0), 0.0, dur - 1.6, (700, 1450), (250, 900)),
        ("gagak", bird_spot(1), 0.0, dur - 1.1, (600, 1440), (150, 1000)),
        ("merpati", bird_spot(2), 0.0, dur - 0.6, (775, 1480), (1200, 900)),
    ]
    birds_scene(c, lt, dur, T, plan, 1.8, 1.6, (690, 1350))


def b_lelaki(c, lt, dur, T):
    camera(c, lerp(1.12, 1.18, lt / dur), 720, 1160)
    road_world(c, T, grains_alive=ALL)
    t_arrive = 1.7
    plan = [
        ("pipit", bird_spot(0), -1, t_arrive + 0.1, (0, 0), (200, 800)),
        ("gagak", bird_spot(1), -1, t_arrive + 0.25, (0, 0), (120, 1000)),
        ("merpati", bird_spot(2), -1, t_arrive + 0.05, (0, 0), (1150, 820)),
    ]
    for kind, spot, a, b, s0, e in plan:
        draw_bird(c, kind, bird_track(lt, spot, a, b, s0, e, fly=1.0))
    ground = 1560
    s = persp(ground) * 880
    if lt < t_arrive:
        x = lerp(1250, 960, ease_out(lt / t_arrive))
        person(c, x, ground, s, walk_pose(lt * 8, 1.0, 8), facing=-1)
    else:
        k = lt - t_arrive
        pose = dict(POSE["shoo"])
        pose["aF"] = (150 + 20 * math.sin(k * 10), 20)
        pose["aB"] = (118 + 20 * math.sin(k * 10 + 2), 30)
        person(c, 960 - 20 * ease_out(k), ground, s, pose, facing=-1)


def b_kaut(c, lt, dur, T):
    u = ease(lt / dur)
    camera(c, lerp(1.3, 1.45, u), lerp(690, 700, u), lerp(1250, 1290, u))
    order = sorted(range(len(GRAINS)), key=lambda i: GRAINS[i][0])
    alive = [1.0] * len(GRAINS)
    gone = prog(lt, 0.3, dur - 0.4)
    for rank, i in enumerate(order):
        alive[i] = 1 - ease(prog(gone * len(order), rank - 4, rank))
    road_world(c, T, grains_alive=alive)
    ground = 1500
    s = persp(ground) * 880
    pose = dict(POSE["kneel"])
    k = math.sin(lt * 7)
    pose["aF"] = (68 + 18 * k, 10 - 10 * k)
    pose["aB"] = (55 - 14 * k, 20)
    x = lerp(470, 560, ease(gone))
    person(c, x, ground, s, pose, facing=1)
    # butir dalam genggaman
    if gone < 1:
        for i in range(5):
            glow_dot(c, x + 0.36 * s + i * 6, ground - 0.17 * s - (i % 2) * 6, 4, GOLD, 0.9, 2.5)


def b_fikir(c, lt, dur, T):
    u = ease(lt / dur)
    camera(c, lerp(1.08, 1.0, u), 540, 960)
    stars(c, 9, 120, 0, 1500, T)
    moon(c, 560, 640, 120)
    wire = skia.Path()
    wire.moveTo(-60, 990)
    wire.quadTo(540, 1110, 1140, 990)
    ink(c, wire, 3, 0.6)
    w2 = skia.Path()
    w2.moveTo(-60, 1060)
    w2.quadTo(540, 1180, 1140, 1060)
    dim(c, w2, 2, 0.3)
    ink(c, poly([(1010, 2000), (1010, 960)]), 10, 0.5)
    ink(c, poly([(930, 990), (1090, 990)]), 6, 0.5)
    rnd = random.Random(2)
    pts = [(-60, 1640)]
    x = -60
    while x < 1140:
        x += rnd.uniform(40, 90)
        pts.append((x, 1640 - rnd.uniform(20, 120)))
    dim(c, curve(pts), 2.2, 0.35)
    for gx in range(-40, 1120, 55):
        grass(c, gx, 1760 + rnd.uniform(-30, 30), 1.2, 0.3, random.Random(gx))
    for i, (kind, bx) in enumerate((("pipit", 300), ("gagak", 545), ("merpati", 790))):
        by = 990 + (1 - ((bx - 540) / 600) ** 2) * 60 + 2 + math.sin(T * 2 + i) * 2
        bird(c, bx, by, 2.1, kind, "stand", -1 if i == 2 else 1, peck=0.0, grain=True)


def b_esok(c, lt, dur, T):
    u = lt / dur
    camera(c, 1.0, lerp(600, 470, u), 960)
    stars(c, 4, 90, 0, 1100, T)
    cloud_x = lerp(1250, 700, u)
    moon(c, 820, 330, 50, a=lerp(1, 0.35, prog(u, 0.45, 0.8)))
    cl = curve([(cloud_x - 200, 380), (cloud_x - 150, 320), (cloud_x - 60, 300), (cloud_x + 20, 270), (cloud_x + 120, 300), (cloud_x + 200, 360), (cloud_x - 200, 380)])
    fill(c, cl, (12, 12, 14))
    dim(c, cl, 2.4, 0.4)
    house(c, 1040, 1180, 0.8, 0.35)
    tree(c, 150, 1300, 1.6, 0.45, 8)
    path = poly([(-400, 1500), (1400, 1450), (1400, 1650), (-400, 1720)], closed=True)
    fill(c, path, (14, 14, 16))
    dim(c, curve([(-400, 1500), (300, 1475), (900, 1460), (1400, 1450)]), 2.4, 0.5)
    dim(c, curve([(-400, 1720), (300, 1690), (900, 1665), (1400, 1650)]), 2.4, 0.5)
    fence = skia.Path()
    for fx in range(-300, 1400, 90):
        fence.moveTo(fx, 1440)
        fence.lineTo(fx, 1360)
    fence.moveTo(-300, 1380)
    fence.lineTo(1400, 1380)
    dim(c, fence, 2.4, 0.35)
    for gx in range(-300, 1400, 70):
        grass(c, gx, 1760 + (gx * 37 % 40), 1.3, 0.35)
    x = lerp(820, 520, u)
    person(c, x, 1590, 620, walk_pose(lt * 4.6, 0.7, 14, carry=True), facing=-1, extra="sack_shoulder", sweat=lt)


ITEMS = [
    ("coin", 360, 1640, 1.2), ("cash", 760, 1650, 1.2), ("coin", 300, 1560, 1.0), ("gold", 640, 1700, 1.2),
    ("car", 860, 1470, 1.1), ("coin", 450, 1700, 1.1), ("house", 220, 1480, 1.1), ("cash", 900, 1700, 1.0),
    ("gold", 520, 1610, 1.0), ("coin", 820, 1580, 1.0), ("cash", 240, 1700, 1.1), ("coin", 960, 1600, 0.9),
    ("gold", 380, 1760, 1.1), ("coin", 700, 1770, 1.0), ("cash", 560, 1790, 1.1), ("coin", 160, 1620, 0.9),
]


def item(c, kind, x, y, s, a=1.0):
    if kind == "coin":
        for i in range(3):
            coin(c, x + (i - 1) * 26 * s, y - i * 6 * s, 24 * s, a)
    elif kind == "cash":
        cash(c, x, y, s, a)
    elif kind == "gold":
        gold_bar(c, x, y, s, a)
        gold_bar(c, x + 40 * s, y - 40 * s, s * 0.9, a)
    elif kind == "car":
        car(c, x, y, s, a)
    elif kind == "house":
        house_card(c, x, y, s, a)


def b_harta(c, lt, dur, T):
    u = ease(lt / dur)
    camera(c, lerp(1.25, 1.0, u), 540, lerp(1250, 1100, u))
    stars(c, 6, 70, 0, 900, T)
    moon(c, 880, 260, 44)
    house(c, 200, 1200, 0.9, 0.35)
    tree(c, 960, 1250, 1.2, 0.35, 3)
    dim(c, poly([(-200, 1250), (1300, 1250)]), 2.0, 0.3)
    n = len(ITEMS)
    for i, (kind, x, y, s) in enumerate(ITEMS):
        t0 = (i / n) ** 0.8 * (dur - 0.8)
        k = prog(lt, t0, t0 + 0.35)
        if k <= 0:
            continue
        pop = 1 + 0.25 * math.sin(k * math.pi) if k < 1 else 1
        item(c, kind, x, y, s * pop * ease_out(k))
    pose = dict(POSE["grab"])
    k = math.sin(lt * 9)
    pose["aF"] = (80 + 40 * k, -10)
    pose["aB"] = (40 - 30 * k, 60)
    person(c, 580, 1560, 560, pose, facing=-1 if int(lt * 1.2) % 2 else 1, sweat=lt)


def b_kafan(c, lt, dur, T):
    u = ease(lt / dur)
    camera(c, lerp(1.0, 1.12, u), 540, lerp(1000, 1080, u))
    # dinding & tingkap
    dim(c, poly([(-100, 1380), (1180, 1380)]), 2.4, 0.45)
    win = skia.Rect.MakeXYWH(640, 640, 260, 340)
    c.drawRect(win, pen(WHITE, 2.4, 0.4))
    c.save()
    c.clipRect(win)
    stars(c, 12, 25, 640, 980, T)
    moon(c, 820, 730, 34, 0.8)
    c.restore()
    dim(c, poly([(770, 640), (770, 980)]), 2.0, 0.35)
    dim(c, poly([(640, 810), (900, 810)]), 2.0, 0.35)
    for i in range(9):
        dim(c, poly([(-100 + i * 150, 1380), (-300 + i * 190, 1920)]), 1.6, 0.18)
    # pelita
    fl = 1 + 0.08 * math.sin(T * 13) + 0.05 * math.sin(T * 7.3)
    c.drawCircle(160, 1130, 180 * fl, pen((255, 190, 90), 0, 0.10, glow=80, fill=True))
    ink(c, poly([(130, 1240), (190, 1240), (175, 1170), (145, 1170)], closed=True), 2.6, 0.7)
    flame = skia.Path()
    flame.moveTo(160, 1165)
    flame.quadTo(178 * 1, 1140, 160, 1110 - 6 * fl)
    flame.quadTo(142, 1140, 160, 1165)
    neon(c, flame, 2, fill=True)
    # usungan & jenazah berkafan
    bed = skia.Rect.MakeLTRB(230, 1250, 870, 1280)
    c.drawRect(bed, pen(BG, 0, 1, fill=True))
    ink(c, poly([(230, 1250), (870, 1250), (870, 1280), (230, 1280)], closed=True), 2.6, 0.7)
    ink(c, poly([(260, 1280), (260, 1340)]), 3, 0.6)
    ink(c, poly([(840, 1280), (840, 1340)]), 3, 0.6)
    body = curve([(280, 1250), (282, 1200), (318, 1172), (358, 1182), (378, 1196), (420, 1168), (560, 1158),
                  (700, 1172), (780, 1190), (830, 1212), (845, 1250)])
    body.close()
    c.drawPath(body, pen((240, 240, 240), 0, 0.18, glow=30, fill=True))
    fill(c, body, (210, 210, 212))
    ink(c, body, 3, 0.95)
    ties = skia.Path()
    for tx in (330, 560, 800):
        ties.moveTo(tx, 1250)
        ties.quadTo(tx - 6, 1200, tx + 2, 1160)
        ties.moveTo(tx, 1160)
        ties.lineTo(tx - 14, 1140)
        ties.moveTo(tx, 1160)
        ties.lineTo(tx + 14, 1140)
    c.drawPath(ties, pen((60, 60, 64), 3, 0.9))
    folds = skia.Path()
    for fx in (420, 480, 650, 720):
        folds.moveTo(fx, 1170)
        folds.quadTo(fx + 15, 1210, fx + 5, 1245)
    c.drawPath(folds, pen((120, 120, 124), 2, 0.8))
    # harta ditinggalkan - hilang sinar
    a = lerp(0.9, 0.35, prog(lt, 0.5, dur))
    c.saveLayerAlpha(None, int(255 * a))
    for kind, x, y, s in (("cash", 960, 1440, 0.9), ("coin", 1000, 1500, 0.8), ("gold", 900, 1520, 0.8), ("coin", 820, 1480, 0.7)):
        item(c, kind, x, y, s)
    c.restore()
    for mx in (380, 540):
        person(c, mx, 1130, 330, POSE["stand"], facing=1, col=(160, 160, 165), hat=False, glow=False)


def b_anak(c, lt, dur, T):
    u = ease(lt / dur)
    camera(c, lerp(1.05, 1.0, u), 540, 1020)
    stars(c, 21, 80, 0, 820, T)
    moon(c, 900, 260, 44)
    house(c, 230, 1200, 1.05, 0.45)
    tree(c, 960, 1200, 1.1, 0.35, 9)
    # simpang jalan
    pa = skia.Path()
    pa.moveTo(380, 1920)
    pa.cubicTo(450, 1600, 520, 1400, 300, 1210)
    pa.moveTo(760, 1920)
    pa.cubicTo(700, 1600, 640, 1450, 620, 1220)
    pa.moveTo(700, 1500)
    pa.cubicTo(800, 1400, 900, 1300, 1000, 1220)
    dim(c, pa, 2.4, 0.45)
    split = BARIS[12]["kata"]
    t_go = next((w["mula"] for w in split[1:] if w["k"].lower().startswith("kita")), BARIS[12]["mula"] + dur * 0.5) - BARIS[12]["mula"]
    go = ease(prog(lt, t_go, dur))
    kids = (((620, 1600), (612, 1240), 380, "bag"), ((770, 1610), (960, 1240), 340, "hair"))
    for i, ((x0, y0), (x1, y1), s, style) in enumerate(kids):
        g = clamp(go * 1.1 - i * 0.1)
        x, y = lerp(x0, x1, g), lerp(y0, y1, g)
        sc = s * lerp(1, 0.35, g)
        pose = walk_pose(lt * 7 + i, 0.8, 4) if 0 < g < 1 else POSE["stand"]
        person(c, x, y, sc, pose, facing=1 if x1 > x0 + 50 else -1, col=WHITE, hat=False, glow=False, kid=style)
    pose = dict(POSE["hold"]) if go < 0.05 else dict(POSE["arms_open"] if go < 0.6 else POSE["stand"])
    person(c, 420, 1640, 600, pose, facing=1)


def b_jalan(c, lt, dur, T):
    u = ease(lt / dur)
    camera(c, 1.0, 540, lerp(1060, 960, u))
    sun_y = lerp(1080, 1010, u)
    c.drawCircle(540, sun_y, 520, pen((255, 190, 70), 0, 0.16, glow=160, fill=True))
    c.drawCircle(540, sun_y, 95, pen((255, 214, 120), 0, 1, fill=True))
    c.drawCircle(540, sun_y, 95, pen(GOLD, 0, 0.6, glow=30, fill=True))
    for i in range(14):
        a = math.radians(180 + i * 180 / 13)
        r0, r1 = 140, 230 + 40 * (i % 2)
        c.drawLine(540 + math.cos(a) * r0, sun_y + math.sin(a) * r0, 540 + math.cos(a) * r1, sun_y + math.sin(a) * r1, pen(GOLD, 3, 0.35))
    fill(c, poly([(-200, 1080), (1300, 1080), (1300, 2000), (-200, 2000)], closed=True), BG)
    for k, (yb, amp, a) in enumerate(((1080, 70, 0.55), (1180, 110, 0.4), (1300, 90, 0.3))):
        rnd = random.Random(k + 30)
        pts = [(-100 + i * 140, yb - rnd.uniform(0, amp)) for i in range(10)]
        ink(c, curve(pts), 2.4, a)
    road = skia.Path()
    road.moveTo(380, 1920)
    road.cubicTo(500, 1600, 760, 1450, 560, 1260)
    road.cubicTo(450, 1170, 520, 1120, 540, 1085)
    road.moveTo(740, 1920)
    road.cubicTo(800, 1600, 880, 1450, 640, 1260)
    road.cubicTo(530, 1170, 560, 1120, 548, 1085)
    ink(c, road, 3, 0.6)
    for i in range(6):
        y = 1500 + i * 70
        dim(c, poly([(-100, y), (lerp(340, 300, i / 5), y - 20)]), 1.8, 0.25)
        dim(c, poly([(lerp(800, 860, i / 5), y - 20), (1180, y)]), 1.8, 0.25)
    for i in range(5):
        bx = lerp(-100, 1200, (lt * 0.12 + i * 0.17) % 1)
        by = 700 + i * 45 + math.sin(lt * 2 + i) * 10
        f = math.sin(lt * 9 + i)
        w = skia.Path()
        w.moveTo(bx - 22, by - 10 * f)
        w.quadTo(bx - 8, by - 8, bx, by)
        w.quadTo(bx + 8, by - 8, bx + 22, by - 10 * f)
        ink(c, w, 2.6, 0.8)
    person(c, 300, 1800, 520, POSE["stand"], facing=1)


def b_akhir(c, lt, dur, T):
    u = ease(lt / dur)
    camera(c, lerp(1.0, 1.1, u), 540, lerp(1000, 960, u))
    c.drawCircle(540, 900, 600, pen((255, 190, 70), 0, 0.18, glow=180, fill=True))
    c.drawCircle(540, 900, 105, pen((255, 214, 120), 0, 1, fill=True))
    c.drawCircle(540, 900, 105, pen(GOLD, 0, 0.6, glow=30, fill=True))
    fill(c, poly([(-200, 960), (1300, 960), (1300, 2100), (-200, 2100)], closed=True), BG)
    for k, (yb, amp, a) in enumerate(((960, 60, 0.55), (1050, 90, 0.35))):
        rnd = random.Random(k + 40)
        ink(c, curve([(-100 + i * 140, yb - rnd.uniform(0, amp)) for i in range(10)]), 2.4, a)
    road = poly([(520, 965), (560, 965), (900, 2000), (180, 2000)], closed=True)
    fill(c, road, (16, 16, 18))
    ink(c, poly([(520, 965), (180, 2000)]), 3, 0.6)
    ink(c, poly([(560, 965), (900, 2000)]), 3, 0.6)
    for gx in range(-100, 1200, 60):
        if 150 < gx < 920:
            continue
        grass(c, gx, 1700 + (gx * 31 % 200), 1.3, 0.35)
    # karung ditinggalkan untuk burung
    sack(c, 960, 1600, 0.6, torn=1)
    grains(c, 960, 1600, 0.6, GRAINS[:70], [1.0] * 70)
    for i, (kind, bx, by) in enumerate((("pipit", 780, 1640), ("merpati", 860, 1680))):
        bird(c, bx, by, 0.75, kind, "stand", 1, peck=max(0, math.sin(T * 6 + i * 2)) ** 2)
    # lelaki berjalan ke arah matahari
    y = lerp(1850, 1150, ease(prog(lt, 0, dur + 2)))
    s = lerp(520, 140, ease(prog(lt, 0, dur + 2)))
    person(c, lerp(470, 540, u), y, s, walk_pose(lt * 6, 0.9, 0), facing=1)


SCENES = {
    "lori": b_lori, "koyak": b_koyak, "pipit": b_pipit, "gagak": b_gagak, "merpati": b_merpati,
    "cukup": b_cukup, "lelaki": b_lelaki, "kaut": b_kaut, "fikir": b_fikir, "esok": b_esok,
    "harta": b_harta, "kafan": b_kafan, "anak": b_anak, "jalan": b_jalan, "akhir": b_akhir,
}

# jadual babak: setiap babak bermula sedikit sebelum barisnya diucap
STARTS = [0.0] + [b["mula"] - 0.15 for b in BARIS[1:]]
ENDS = STARTS[1:] + [JUMLAH]
XFADE = 0.35


def draw_scene(c, k, t):
    lt = t - STARTS[k]
    dur = ENDS[k] - STARTS[k]
    c.save()
    SCENES[BARIS[k]["babak"]](c, lt, dur, t)
    c.restore()


# ------------------------------------------------------------------ sari kata
TF = skia.Typeface.MakeFromFile(FONT)
FONT_CAP = skia.Font(TF, 74)
FONT_END = skia.Font(TF, 68)


def build_pages():
    pages = []
    for b in BARIS:
        cur = []
        for w in b["kata"]:
            if cur and FONT_CAP.measureText(" ".join(x["k"] for x in cur + [w])) > 900:
                pages.append(cur)
                cur = []
            cur.append(w)
            if w["k"][-1] in ".,?!" or len(cur) == 3:
                pages.append(cur)
                cur = []
        if cur:
            pages.append(cur)
    out = []
    for i, p in enumerate(pages):
        start = p[0]["mula"] - 0.05
        end = min(pages[i + 1][0]["mula"] - 0.05 if i + 1 < len(pages) else p[-1]["tamat"] + 0.6, p[-1]["tamat"] + 0.7)
        out.append((start, end, p))
    return out


PAGES = build_pages()


def captions(c, t):
    for start, end, words in PAGES:
        if not (start <= t < end):
            continue
        pop = ease_out(prog(t, start, start + 0.12))
        widths = [FONT_CAP.measureText(w["k"]) for w in words]
        space = FONT_CAP.measureText(" ")
        total = sum(widths) + space * (len(words) - 1)
        x = W / 2 - total / 2
        y = 1390
        c.save()
        c.translate(W / 2, y)
        c.scale(lerp(0.88, 1.0, pop), lerp(0.88, 1.0, pop))
        c.translate(-W / 2, -y)
        stroke = pen((0, 0, 0), 14, 0.95)
        shadow = pen((0, 0, 0), 0, 0.6, glow=14, fill=True)
        for w, wd in zip(words, widths):
            active = w["mula"] - 0.04 <= t
            col = GOLD if (active and t < w["tamat"] + 0.15) else WHITE
            lift = -6 * (1 - prog(t, w["mula"], w["mula"] + 0.12)) if active else 0
            c.drawString(w["k"], x, y + 10 + lift, FONT_CAP, shadow)
            c.drawString(w["k"], x, y + lift, FONT_CAP, stroke)
            c.drawString(w["k"], x, y + lift, FONT_CAP, pen(col, 0, 1.0 if active else 0.92, fill=True))
            x += wd + space
        c.restore()


def end_card(c, t):
    t0 = MASA["jumlah"] - 0.6
    a = ease(prog(t, t0, t0 + 0.8))
    if a <= 0:
        return
    c.drawRect(skia.Rect.MakeWH(W, H), pen(BG, 0, a * 0.85, fill=True))
    for i, (line, col) in enumerate((("Ambil secukupnya.", WHITE), ("Nikmati perjalanan.", GOLD))):
        k = ease_out(prog(t, t0 + 0.2 + i * 0.5, t0 + 0.9 + i * 0.5))
        if k <= 0:
            continue
        wd = FONT_END.measureText(line)
        y = 930 + i * 110 + 20 * (1 - k)
        if col == GOLD:
            c.drawString(line, W / 2 - wd / 2, y, FONT_END, pen(GOLD, 0, 0.5 * k, glow=14, fill=True))
        c.drawString(line, W / 2 - wd / 2, y, FONT_END, pen(col, 0, k, fill=True))


VIGNETTE = skia.Paint(Shader=skia.GradientShader.MakeRadial(
    (W / 2, H / 2), H * 0.72, [skia.ColorSetARGB(0, 0, 0, 0), skia.ColorSetARGB(0, 0, 0, 0), skia.ColorSetARGB(200, 0, 0, 0)], [0.0, 0.55, 1.0]))


def render_frame(t, buf=None):
    if buf is None:
        buf = np.zeros((H, W, 4), np.uint8)
    surf = skia.Surface(buf)
    c = surf.getCanvas()
    c.clear(skia.ColorSetARGB(255, *BG))
    k = max(i for i, s in enumerate(STARTS) if s <= t)
    if k > 0 and t - STARTS[k] < XFADE:
        draw_scene(c, k - 1, t)
        c.saveLayerAlpha(None, int(255 * ease((t - STARTS[k]) / XFADE)))
        c.clear(skia.ColorSetARGB(255, *BG))
        draw_scene(c, k, t)
        c.restore()
    else:
        draw_scene(c, k, t)
    c.drawRect(skia.Rect.MakeWH(W, H), VIGNETTE)
    captions(c, t)
    end_card(c, t)
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


def save_png(t, path):
    from PIL import Image
    Image.fromarray(render_frame(t)[:, :, :3]).save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--still", type=float, nargs="*")
    ap.add_argument("--sheet", action="store_true")
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    BUILD.mkdir(exist_ok=True)
    OUT.mkdir(exist_ok=True)
    if a.still:
        for t in a.still:
            save_png(t, BUILD / f"still_{t:05.1f}.png")
        return
    if a.sheet:
        from PIL import Image
        tiles = []
        for k in range(len(BARIS)):
            t = STARTS[k] + (ENDS[k] - STARTS[k]) * 0.6
            tiles.append(Image.fromarray(render_frame(t)[:, :, :3]).resize((270, 480)))
        sheet = Image.new("RGB", (270 * 5, 480 * 3))
        for i, im in enumerate(tiles):
            sheet.paste(im, ((i % 5) * 270, (i // 5) * 480))
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
    out = OUT / "karung-beras.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(BUILD / "video_bisu.mp4"), "-i", str(audio),
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out)], check=True)
    print("Output:", out)


if __name__ == "__main__":
    main()
