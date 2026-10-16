"""Primitif lukisan gaya 'line-art' gelap + neon emas (Skia)."""
import math
import random

import skia

W, H = 1080, 1920
BG = (6, 6, 8)
GOLD = (255, 196, 58)
WHITE = (236, 236, 236)
GREY = (150, 150, 155)


def rgba(c, a=1.0):
    return skia.ColorSetARGB(int(255 * max(0.0, min(1.0, a))), *c)


_blur = {}


def blur(sigma):
    if sigma not in _blur:
        _blur[sigma] = skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, sigma)
    return _blur[sigma]


def pen(c=WHITE, w=3.0, a=1.0, glow=0, fill=False):
    p = skia.Paint(
        AntiAlias=True,
        Color=rgba(c, a),
        StrokeWidth=w,
        Style=skia.Paint.kFill_Style if fill else skia.Paint.kStroke_Style,
        StrokeCap=skia.Paint.kRound_Cap,
        StrokeJoin=skia.Paint.kRound_Join,
    )
    if glow:
        p.setMaskFilter(blur(glow))
    return p


def lerp(a, b, t):
    return a + (b - a) * t


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_out(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def prog(t, t0, t1):
    return clamp((t - t0) / (t1 - t0)) if t1 > t0 else float(t >= t0)


# ---------------------------------------------------------------- laluan

def poly(pts, closed=False):
    p = skia.Path()
    p.moveTo(*pts[0])
    for q in pts[1:]:
        p.lineTo(*q)
    if closed:
        p.close()
    return p


def curve(pts, closed=False, tension=0.5):
    """Spline Catmull-Rom melalui semua titik."""
    p = skia.Path()
    n = len(pts)
    if n < 3:
        return poly(pts, closed)
    pts2 = list(pts) + ([pts[0], pts[1], pts[2]] if closed else [])
    p.moveTo(*pts2[0])
    rng = range(len(pts2) - 3) if closed else range(n - 1)
    for i in rng:
        p0 = pts2[i - 1] if (i > 0 or closed) else pts2[i]
        p1, p2 = pts2[i], pts2[i + 1]
        p3 = pts2[i + 2] if i + 2 < len(pts2) else p2
        k = tension / 3 * 2
        c1 = (p1[0] + (p2[0] - p0[0]) * k / 2, p1[1] + (p2[1] - p0[1]) * k / 2)
        c2 = (p2[0] - (p3[0] - p1[0]) * k / 2, p2[1] - (p3[1] - p1[1]) * k / 2)
        p.cubicTo(*c1, *c2, *p2)
    if closed:
        p.close()
    return p


def ellipse(cx, cy, rx, ry):
    p = skia.Path()
    p.addOval(skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry))
    return p


def moved(path, x=0, y=0, sx=1, sy=None, rot=0):
    m = skia.Matrix()
    m.setScale(sx, sx if sy is None else sy)
    m.postRotate(rot)
    m.postTranslate(x, y)
    q = skia.Path(path)
    q.transform(m)
    return q


# ---------------------------------------------------------------- gaya

def dim(c, path, w=2.0, a=0.32):
    c.drawPath(path, pen(WHITE, w, a))


def ink(c, path, w=3.0, a=0.85, col=WHITE):
    c.drawPath(path, pen(col, w, a))


def neon(c, path, w=4.0, col=GOLD, a=1.0, fill=False):
    c.drawPath(path, pen(col, w * 4, 0.28 * a, glow=16))
    c.drawPath(path, pen(col, w * 1.8, 0.55 * a, glow=4))
    c.drawPath(path, pen(col, w, a, fill=fill))


def fill(c, path, col=BG, a=1.0):
    c.drawPath(path, pen(col, 0, a, fill=True))


def glow_dot(c, x, y, r, col=GOLD, a=1.0, halo=3.0):
    c.drawCircle(x, y, r * halo, pen(col, 0, 0.25 * a, glow=r * 2, fill=True))
    c.drawCircle(x, y, r, pen(col, 0, a, fill=True))


# ---------------------------------------------------------------- latar

def stars(c, seed=3, n=70, top=0, bottom=760, t=0.0):
    rnd = random.Random(seed)
    for _ in range(n):
        x, y = rnd.uniform(0, W), rnd.uniform(top, bottom)
        r = rnd.uniform(0.8, 2.2)
        tw = 0.5 + 0.5 * math.sin(t * rnd.uniform(1, 3) + rnd.uniform(0, 6))
        c.drawCircle(x, y, r, pen(WHITE, 0, 0.15 + 0.35 * tw, fill=True))


def moon(c, x, y, r=46, a=1.0):
    c.drawCircle(x, y, r * 2.6, pen((255, 240, 200), 0, 0.10 * a, glow=r, fill=True))
    p = skia.Path()
    p.addCircle(x, y, r)
    cut = skia.Path()
    cut.addCircle(x + r * 0.45, y - r * 0.3, r * 0.9)
    crescent = skia.Op(p, cut, skia.PathOp.kDifference_PathOp)
    c.drawPath(crescent, pen((255, 244, 214), 0, a, fill=True))


def grass(c, x, y, s=1.0, a=0.45, rnd=None):
    rnd = rnd or random.Random(int(x * 7 + y))
    p = skia.Path()
    for _ in range(rnd.randint(4, 7)):
        dx = rnd.uniform(-26, 26) * s
        h = rnd.uniform(30, 70) * s
        bx = x + rnd.uniform(-10, 10) * s
        p.moveTo(bx, y)
        p.quadTo(bx + dx * 0.2, y - h * 0.6, bx + dx, y - h)
    c.drawPath(p, pen(WHITE, max(1.2, 2.2 * s), a))


def tree(c, x, y, s=1.0, a=0.4, seed=1):
    rnd = random.Random(seed)
    pts = []
    n = 11
    for i in range(n):
        ang = math.pi * (1.0 + i / (n - 1))
        rr = rnd.uniform(0.85, 1.15)
        pts.append((x + math.cos(ang) * 120 * s * rr, y - 210 * s + math.sin(ang) * 110 * s * rr))
    pts.append((x + 120 * s, y - 170 * s))
    pts.insert(0, (x - 120 * s, y - 170 * s))
    canopy = curve(pts)
    canopy.quadTo(x, y - 130 * s, x - 120 * s, y - 170 * s)
    c.drawPath(canopy, pen(WHITE, 2.4 * s + 0.6, a))
    trunk = skia.Path()
    trunk.moveTo(x - 12 * s, y)
    trunk.quadTo(x - 6 * s, y - 70 * s, x - 18 * s, y - 145 * s)
    trunk.moveTo(x + 12 * s, y)
    trunk.quadTo(x + 6 * s, y - 70 * s, x + 16 * s, y - 145 * s)
    trunk.moveTo(x, y - 100 * s)
    trunk.lineTo(x + 40 * s, y - 150 * s)
    c.drawPath(trunk, pen(WHITE, 2.4 * s + 0.6, a))


def house(c, x, y, s=1.0, a=0.5, lit=True):
    """Rumah kampung bertiang. (x,y) = tengah bawah tiang."""
    L = lambda pts: poly([(x + px * s, y + py * s) for px, py in pts])
    p = skia.Path()
    for px in (-150, -50, 50, 150):
        p.addPath(L([(px, 0), (px, -70)]))
    p.addPath(L([(-170, -70), (170, -70), (170, -220), (-170, -220)], ))
    p.addPath(L([(-170, -70), (-170, -220)]))
    p.addPath(L([(-200, -215), (0, -330), (200, -215)]))
    p.addPath(L([(-20, -345), (20, -315)]))
    p.addPath(L([(20, -345), (-20, -315)]))
    p.addPath(L([(-190, -70), (-235, 0)]))
    p.addPath(L([(-170, -70), (-215, 0)]))
    for i in range(1, 4):
        p.addPath(L([(-170 - i * 11, -70 + i * 17.5), (-190 - i * 11, -70 + i * 17.5)]))
    c.drawPath(p, pen(WHITE, 2.4, a))
    for wx in (-110, 60):
        r = skia.Rect.MakeXYWH(x + wx * s, y - 185 * s, 55 * s, 75 * s)
        if lit:
            c.drawRect(r, pen((255, 200, 110), 0, 0.35 * a, glow=10, fill=True))
        c.drawRect(r, pen(WHITE, 2.0, a))


# ---------------------------------------------------------------- objek

def sack_path(open_amt=1.0):
    """Karung terbaring, mulut koyak di kiri. Koordinat tempatan ~ lebar 420."""
    pts = [(-150, -10), (-120, -120), (-20, -170), (110, -160), (200, -110),
           (220, -20), (170, 40), (40, 55), (-90, 45), (-150, 25)]
    return curve(pts, closed=True)


def sack(c, x, y, s=1.0, torn=1.0, upright=0.0, fullness=1.0):
    """Karung guni. torn: 0..1 koyak; upright: 0 baring, 1 tegak."""
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    if upright > 0:
        _sack_upright(c, upright, fullness)
        c.restore()
        return
    body = sack_path()
    fill(c, body, (32, 32, 34))
    # tekstur guni
    tex = skia.Path()
    for i in range(-5, 7):
        tex.moveTo(-120 + i * 32, -150)
        tex.quadTo(-100 + i * 32, -60, -125 + i * 34, 40)
    c.save()
    c.clipPath(body, doAntiAlias=True)
    c.drawPath(tex, pen(WHITE, 1.4, 0.13))
    c.restore()
    ink(c, body, 3.2, 0.9)
    folds = skia.Path()
    folds.moveTo(60, -150)
    folds.quadTo(40, -80, 90, 20)
    folds.moveTo(140, -130)
    folds.quadTo(120, -60, 150, 10)
    c.drawPath(folds, pen(WHITE, 2.2, 0.5))
    if torn > 0:
        mouth = curve([(-150, -10), (-185 - 25 * torn, -60), (-175, -115), (-205 - 20 * torn, -150), (-120, -120)])
        fill(c, curve([(-150, -10), (-185 - 25 * torn, -60), (-175, -115), (-205 - 20 * torn, -150), (-120, -120), (-140, -60)], closed=True), (18, 18, 20))
        ink(c, mouth, 3.0, 0.9)
        teeth = skia.Path()
        for i in range(5):
            yy = -20 - i * 24
            teeth.moveTo(-160 - 6 * i, yy)
            teeth.lineTo(-180 - 8 * torn - 6 * i, yy - 8)
        c.drawPath(teeth, pen(WHITE, 1.8, 0.6))
    c.restore()


def _sack_upright(c, up, fullness):
    h = 240 * (0.55 + 0.45 * fullness)
    pts = [(-110, 0), (-125, -h * 0.5), (-95, -h), (-30, -h - 30), (40, -h - 20), (100, -h), (125, -h * 0.5), (110, 0)]
    body = curve(pts, closed=True)
    fill(c, body, (32, 32, 34))
    ink(c, body, 3.2, 0.9)
    if fullness > 0.05:
        top = ellipse(0, -h - 10, 80, 18)
        c.drawPath(top, pen(GOLD, 0, 0.8, fill=True))
        neon(c, top, 2.0)


def grain_layout(n=170, seed=7):
    """Taburan butir beras di sekitar mulut karung (koordinat tempatan karung)."""
    rnd = random.Random(seed)
    out = []
    for i in range(n):
        if i < n * 0.55:  # timbunan rapat dekat mulut
            ang = rnd.uniform(math.radians(150), math.radians(250))
            r = rnd.uniform(0, 120) ** 1.0
            x, y = -190 + math.cos(ang) * r * 1.1, 20 + math.sin(ang) * r * 0.35
        else:  # bertaburan
            x, y = rnd.uniform(-470, -150), rnd.uniform(-10, 70)
            x += rnd.uniform(-30, 30)
        out.append((x, y, rnd.uniform(5.5, 8.5), rnd.uniform(0, 180)))
    return out


def grains(c, x, y, s, layout, alive, spread=1.0):
    """Lukis butir. alive: senarai bool / float 0..1 (skala)."""
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    glow = skia.Path()
    for (gx, gy, r, rot), al in zip(layout, alive):
        if al <= 0:
            continue
        gx2 = -190 + (gx + 190) * spread
        glow.addOval(skia.Rect.MakeXYWH(gx2 - r * al, gy - r * 0.6 * al, 2 * r * al, 1.2 * r * al))
    c.drawPath(glow, pen(GOLD, 0, 0.35, glow=14, fill=True))
    c.drawPath(glow, pen((255, 214, 96), 0, 1.0, fill=True))
    c.drawPath(glow, pen((150, 100, 20), 1.0, 0.8))
    c.restore()


def truck_back(c, x, y, s, t=0.0):
    """Lori dari belakang; (x,y) = tengah bawah tayar."""
    c.save()
    c.translate(x, y)
    c.scale(s, s)
    box = skia.Rect.MakeLTRB(-240, -460, 240, -110)
    c.drawRect(box, pen(BG, 0, 1, fill=True))
    c.drawRect(box, pen(WHITE, 4, 0.9))
    bars = skia.Path()
    bars.moveTo(0, -460)
    bars.lineTo(0, -110)
    for yy in (-380, -300, -220):
        bars.moveTo(-240, yy)
        bars.lineTo(240, yy)
    c.drawPath(bars, pen(WHITE, 2.4, 0.55))
    # muatan guni
    for i in range(6):
        cx = -200 + i * 80
        p = curve([(cx - 45, -460), (cx - 40, -520), (cx, -540), (cx + 40, -520), (cx + 45, -460)])
        c.drawPath(p, pen(WHITE, 3, 0.8))
    chassis = skia.Rect.MakeLTRB(-250, -110, 250, -80)
    c.drawRect(chassis, pen(WHITE, 3, 0.8))
    for wx in (-230, 140):
        r = skia.Rect.MakeXYWH(wx, -95, 90, 95)
        c.drawRoundRect(r, 14, 14, pen((10, 10, 10), 0, 1, fill=True))
        c.drawRoundRect(r, 14, 14, pen(WHITE, 3, 0.8))
    for lx in (-215, 215):
        glow_dot(c, lx, -95, 11, (255, 60, 50), 0.95, halo=3.5)
    c.restore()


def coin(c, x, y, r=26, a=1.0):
    c.drawCircle(x, y, r * 1.8, pen(GOLD, 0, 0.18 * a, glow=r, fill=True))
    c.drawPath(ellipse(x, y, r, r * 0.92), pen((40, 30, 8), 0, a, fill=True))
    c.drawPath(ellipse(x, y, r, r * 0.92), pen(GOLD, 3, a))
    c.drawPath(ellipse(x, y, r * 0.65, r * 0.6), pen(GOLD, 2, 0.8 * a))


def cash(c, x, y, s=1.0, a=1.0):
    for i in range(4):
        r = skia.Rect.MakeXYWH(x - 70 * s, y - 18 * s - i * 16 * s, 140 * s, 30 * s)
        c.drawRect(r, pen(BG, 0, a, fill=True))
        c.drawRect(r, pen(WHITE, 2.4, 0.85 * a))
    c.drawCircle(x, y - 51 * s, 9 * s, pen(WHITE, 2, 0.7 * a))


def gold_bar(c, x, y, s=1.0, a=1.0):
    p = poly([(x - 60 * s, y), (x + 60 * s, y), (x + 42 * s, y - 40 * s), (x - 42 * s, y - 40 * s)], closed=True)
    fill(c, p, (60, 42, 6), a)
    neon(c, p, 2.6, a=a)


def car(c, x, y, s=1.0, a=1.0):
    L = lambda pts: [(x + px * s, y + py * s) for px, py in pts]
    body = curve(L([(-160, -30), (-150, -70), (-80, -80), (-40, -130), (60, -130), (110, -80), (160, -70), (165, -30)]))
    body.lineTo(x - 160 * s, y - 30 * s)
    fill(c, body, BG, a)
    c.drawPath(body, pen(WHITE, 2.6, 0.85 * a))
    win = poly(L([(-30, -120), (50, -120), (90, -82), (-62, -82)]), closed=True)
    c.drawPath(win, pen(WHITE, 2, 0.6 * a))
    for wx in (-90, 95):
        c.drawCircle(x + wx * s, y - 28 * s, 30 * s, pen(BG, 0, a, fill=True))
        c.drawCircle(x + wx * s, y - 28 * s, 30 * s, pen(WHITE, 2.6, 0.85 * a))
        c.drawCircle(x + wx * s, y - 28 * s, 12 * s, pen(WHITE, 2, 0.6 * a))


def house_card(c, x, y, s=1.0, a=1.0):
    r = skia.Rect.MakeXYWH(x - 70 * s, y - 120 * s, 140 * s, 120 * s)
    c.drawRect(r, pen(BG, 0, a, fill=True))
    c.drawRect(r, pen(WHITE, 2.6, 0.85 * a))
    p = poly([(x - 40 * s, y - 25 * s), (x - 40 * s, y - 65 * s), (x, y - 95 * s), (x + 40 * s, y - 65 * s), (x + 40 * s, y - 25 * s)], closed=True)
    c.drawPath(p, pen(WHITE, 2.4, 0.85 * a))


# ---------------------------------------------------------------- burung

BIRD = {
    "pipit": dict(fill=(86, 72, 58), belly=(170, 160, 140), beak=10, size=0.85),
    "gagak": dict(fill=(16, 16, 18), belly=(30, 30, 32), beak=22, size=1.2),
    "merpati": dict(fill=(120, 122, 130), belly=(165, 165, 172), beak=11, size=1.05),
}


def bird(c, x, y, s, kind="pipit", pose="stand", facing=1, phase=0.0, peck=0.0, grain=False):
    """(x,y) = titik kaki di tanah. peck: 0..1 kepala menunduk."""
    k = BIRD[kind]
    s = s * k["size"]
    lw = 2.6 / s
    c.save()
    c.translate(x, y)
    c.scale(facing * s, s)
    c.translate(0, -40)
    tilt = 28 * peck if pose != "fly" else -8
    c.rotate(tilt)
    outline = pen(WHITE, lw, 0.9)
    if pose == "fly":
        flap = math.sin(phase)
        back = _wing(-flap)
        fill(c, back, tuple(int(v * 0.7) for v in k["fill"]))
        c.drawPath(back, pen(WHITE, lw, 0.6))
    else:
        legs = skia.Path()
        for lx in (-4, 7):
            legs.moveTo(lx, 18)
            legs.lineTo(lx - 2, 40)
            legs.lineTo(lx + 8, 40)
        c.save()
        c.rotate(-tilt)
        c.drawPath(legs, pen((210, 170, 120), lw, 0.9))
        c.restore()
    tail = poly([(-26, -6), (-64, -18), (-60, 6), (-24, 10)], closed=True)
    fill(c, tail, k["fill"])
    c.drawPath(tail, outline)
    body = ellipse(0, 0, 34, 22)
    fill(c, body, k["fill"])
    belly = ellipse(6, 9, 24, 11)
    c.save()
    c.clipPath(body, doAntiAlias=True)
    fill(c, belly, k["belly"])
    c.restore()
    c.drawPath(body, outline)
    hx, hy = (27, -20)
    head = ellipse(hx, hy, 15, 14)
    fill(c, head, k["fill"])
    c.drawPath(head, outline)
    bl = k["beak"]
    beak = poly([(hx + 12, hy - 4), (hx + 14 + bl, hy + 1), (hx + 12, hy + 5)], closed=True)
    fill(c, beak, (200, 170, 90))
    c.drawPath(beak, pen(WHITE, lw * 0.8, 0.9))
    c.drawCircle(hx + 5, hy - 4, 2.8, pen(WHITE, 0, 1, fill=True))
    if grain:
        c.drawPath(ellipse(hx + 16 + bl, hy + 2, 5, 3), pen(GOLD, 0, 1, fill=True))
        c.drawPath(ellipse(hx + 16 + bl, hy + 2, 5, 3), pen(GOLD, 0, 0.5, glow=6, fill=True))
    if pose == "fly":
        front = _wing(math.sin(phase))
        fill(c, front, k["fill"])
        c.drawPath(front, outline)
    else:
        wing = curve([(18, -10), (-2, -20), (-30, -12), (-44, 4), (-16, 8), (12, 2)], closed=True)
        fill(c, wing, tuple(min(255, int(v * 1.25 + 8)) for v in k["fill"]))
        c.drawPath(wing, outline)
        feather = skia.Path()
        for i in range(3):
            feather.moveTo(-10 - i * 10, -6)
            feather.lineTo(-22 - i * 10, 4)
        c.drawPath(feather, pen(WHITE, lw * 0.7, 0.5))
    c.restore()


def _wing(f):
    """Sayap terbuka; f=+1 ke atas, -1 ke bawah."""
    tip_y = -10 - 70 * f
    return curve([(14, -8), (-4, -10 + (tip_y + 10) * 0.6), (-38, tip_y), (-30, tip_y * 0.6 + 4), (-16, -2)], closed=True)


# ---------------------------------------------------------------- manusia

def figure_points(x, ground, s, pose, facing=1):
    """Kira kedudukan sendi. pose: dict sudut (darjah). Pulangkan dict titik."""
    P = dict(lean=0, head=0, aB=(8, 10), aF=(8, 10), lB=(0, 0), lF=(0, 0), bob=0)
    P.update(pose)

    def go(o, ang, L):
        a = math.radians(ang)
        return (o[0] + facing * math.sin(a) * L * s, o[1] + math.cos(a) * L * s)

    hip = (0.0, 0.0)
    knees, feet = {}, {}
    for side in ("lB", "lF"):
        ha, kb = P[side]
        knees[side] = go(hip, ha, 0.23)
        feet[side] = go(knees[side], ha + kb, 0.23)
    low = max(feet["lB"][1], feet["lF"][1])
    off = (x, ground - low - P["bob"] * s)

    def T(p):
        return (p[0] + off[0], p[1] + off[1])

    lean = math.radians(P["lean"])
    neck = (facing * math.sin(lean) * 0.30 * s, -math.cos(lean) * 0.30 * s)
    shoulder = (neck[0] * 0.9, neck[1] * 0.9)
    hl = lean + math.radians(P["head"])
    head = (neck[0] + facing * math.sin(hl) * 0.11 * s, neck[1] - math.cos(hl) * 0.11 * s)
    pts = dict(hip=T(hip), neck=T(neck), head=T(head), sh=T(shoulder), lean=P["lean"] + P["head"])
    for side, key in (("aB", "B"), ("aF", "F")):
        sa, eb = P[side]
        el = go(shoulder, sa, 0.15)
        hand = go(el, sa + eb, 0.15)
        pts["el" + key], pts["hand" + key] = T(el), T(hand)
    for side, key in (("lB", "B"), ("lF", "F")):
        pts["knee" + key], pts["foot" + key] = T(knees[side]), T(feet[side])
        ha, kb = P[side]
        pts["toe" + key] = (pts["foot" + key][0] + facing * 0.055 * s, pts["foot" + key][1])
    return pts


def _outlined(c, groups, col, lw, glow=True, interior=BG):
    """groups: senarai kumpulan bentuk; setiap kumpulan dilukis dengan garis luar bersatu."""
    for gi, shapes in enumerate(groups):
        for pass_ in ("glow", "line", "fill"):
            if pass_ == "glow" and not glow:
                continue
            for kind, data, wdt in shapes:
                if pass_ == "glow":
                    pt = pen(col, wdt + lw * 6, 0.22, glow=14)
                elif pass_ == "line":
                    pt = pen(col, wdt + lw * 2, 1.0)
                else:
                    pt = pen(interior, wdt, 1.0)
                if kind == "line":
                    c.drawPath(data, pt)
                elif kind == "shape":
                    if pass_ == "fill":
                        c.drawPath(data, pen(interior, 0, 1, fill=True))
                    else:
                        pt.setStrokeWidth(lw * (6 if pass_ == "glow" else 2))
                        c.drawPath(data, pt)
                        if pass_ == "line":
                            c.drawPath(data, pen(col, 0, 1, fill=True))


def person(c, x, ground, s, pose, facing=1, col=GOLD, hat=True, glow=True, extra=None, kid=None, sweat=0.0):
    """Lukis watak garis luar (neon). s ~ tinggi dalam piksel."""
    p = figure_points(x, ground, s, pose, facing)
    limb = 0.058 * s
    lw = max(2.0, 0.0085 * s)

    def seg(*pts):
        return ("line", poly(pts), limb)

    back = [seg(p["sh"], p["elB"], p["handB"]), seg(p["hip"], p["kneeB"], p["footB"], p["toeB"])]
    torso = ("line", poly([p["hip"], p["neck"]]), 0.155 * s)
    head = ("shape", ellipse(p["head"][0], p["head"][1], 0.074 * s, 0.078 * s), 0)
    body = [torso, seg(p["hip"], p["kneeF"], p["footF"], p["toeF"])]
    front = [seg(p["sh"], p["elF"], p["handF"])]
    groups = []
    if kid == "bag":
        bx, by = p["neck"][0] - facing * 0.09 * s, p["neck"][1] + 0.12 * s
        groups.append([("shape", moved(skia.Path().addRoundRect(skia.Rect.MakeXYWH(-0.06 * s, -0.09 * s, 0.12 * s, 0.18 * s), 10, 10), bx, by), 0)])
    groups += [back, body]
    hd = [head]
    if kid == "hair":
        hd.append(("shape", ellipse(p["head"][0] - facing * 0.07 * s, p["head"][1] + 0.01 * s, 0.03 * s, 0.03 * s), 0))
    groups.append(hd)
    if extra == "sack_shoulder":
        sx, sy = p["sh"][0] - facing * 0.06 * s, p["sh"][1] - 0.13 * s
        sk = curve([(sx - 0.17 * s, sy + 0.08 * s), (sx - 0.15 * s, sy - 0.07 * s), (sx, sy - 0.12 * s), (sx + 0.16 * s, sy - 0.06 * s), (sx + 0.17 * s, sy + 0.08 * s), (sx, sy + 0.12 * s)], closed=True)
        groups.append([("shape", sk, 0)])
    groups.append(front)
    _outlined(c, groups, col, lw, glow=glow)
    if extra == "sack_shoulder":
        sx, sy = p["sh"][0] - facing * 0.06 * s, p["sh"][1] - 0.13 * s
        for i in range(7):
            gx = sx + (i - 3) * 0.035 * s
            c.drawPath(ellipse(gx, sy - 0.1 * s + abs(i - 3) * 0.012 * s, 0.012 * s, 0.008 * s), pen(GOLD, 0, 1, fill=True))
    if hat:
        _hat(c, p, s, facing, col, lw)
    # mata
    ex = p["head"][0] + facing * 0.03 * s
    c.drawCircle(ex, p["head"][1] - 0.005 * s, 0.008 * s, pen(col, 0, 1, fill=True))
    if sweat > 0:
        for i, (dx, dy) in enumerate(((-0.1, -0.06), (0.1, -0.1), (0.13, -0.02))):
            ph = (sweat * 2 + i * 0.33) % 1
            d = skia.Path()
            cx, cy = p["head"][0] + dx * s * facing, p["head"][1] + dy * s + ph * 0.05 * s
            d.moveTo(cx, cy - 0.025 * s)
            d.quadTo(cx + 0.015 * s, cy, cx, cy + 0.01 * s)
            d.quadTo(cx - 0.015 * s, cy, cx, cy - 0.025 * s)
            c.drawPath(d, pen(col, lw * 0.8, 1 - ph))
    return p


def _hat(c, p, s, facing, col, lw):
    hx, hy = p["head"]
    c.save()
    c.translate(hx, hy)
    c.rotate(facing * p["lean"])
    brim = ellipse(0, -0.045 * s, 0.135 * s, 0.022 * s)
    crown = skia.Path()
    crown.moveTo(-0.065 * s, -0.05 * s)
    crown.cubicTo(-0.065 * s, -0.13 * s, 0.065 * s, -0.13 * s, 0.065 * s, -0.05 * s)
    crown.close()
    for path in (crown, brim):
        c.drawPath(path, pen(col, lw * 6, 0.22, glow=14))
        c.drawPath(path, pen(BG, 0, 1, fill=True))
        c.drawPath(path, pen(col, lw * 2, 1))
    band = skia.Path()
    band.moveTo(-0.062 * s, -0.068 * s)
    band.quadTo(0, -0.058 * s, 0.062 * s, -0.068 * s)
    c.drawPath(band, pen(col, lw * 1.4, 1))
    c.restore()


def walk_pose(ph, amp=1.0, lean=4, carry=False):
    sn = math.sin(ph)
    pose = dict(
        lean=lean,
        lF=(26 * sn * amp, -8 - 30 * max(0, -math.cos(ph)) * amp),
        lB=(-26 * sn * amp, -8 - 30 * max(0, math.cos(ph)) * amp),
        aF=(-22 * sn * amp, 18),
        aB=(22 * sn * amp, 18),
        bob=0.012 * abs(math.cos(ph)),
    )
    if carry:
        pose["aF"] = (130, 95)
    return pose


POSE = {
    "stand": dict(lean=0, aF=(6, 8), aB=(-6, 8), lF=(4, -2), lB=(-4, -2)),
    "shoo": dict(lean=-4, head=-6, aF=(150, 20), aB=(118, 30), lF=(22, -6), lB=(-20, -4)),
    "kneel": dict(lean=52, head=10, aF=(72, 10), aB=(55, 20), lF=(85, -95), lB=(10, -120)),
    "sit": dict(lean=6, aF=(30, 40), aB=(25, 40), lF=(88, -88), lB=(82, -92)),
    "grab": dict(lean=28, head=6, aF=(80, -10), aB=(40, 60), lF=(30, -30), lB=(-15, -10)),
    "hold": dict(lean=0, aF=(34, 6), aB=(-8, 8), lF=(4, -2), lB=(-4, -2)),
    "arms_open": dict(lean=-6, head=-14, aF=(118, 8), aB=(112, 8), lF=(6, -2), lB=(-6, -2)),
}
