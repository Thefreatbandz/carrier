#!/usr/bin/env python3
"""CARRIER character art v3 — bigger, higher-contrast, stronger silhouettes.
Same filenames as the live build (drop-in replacement). Run from carrier root:
    python3 assets-src/char_factory_v3.py
"""
from PIL import Image, ImageDraw, ImageFilter
import math, random

W, H = 192, 256
ASSETS = "assets"
random.seed(7)

# ---------------- palette ----------------
INK      = (8, 10, 18)
CLOAK_T  = (48, 62, 104)
CLOAK_M  = (36, 48, 88)
CLOAK_B  = (24, 32, 60)
FOLD     = (14, 18, 38)
RIM      = (150, 245, 255)
RIM_DIM  = (70, 140, 175)
STEEL    = (228, 238, 255)
STEEL_D  = (130, 150, 195)
EDGE_G   = (57, 255, 106)
EYE_G    = (140, 255, 160)
SKIN     = (216, 198, 180)
SKIN_D   = (160, 140, 125)
VEIN     = (57, 255, 106)
LEATHER  = (104, 72, 48)
LEATHER_D= (66, 44, 30)
VIAL     = (57, 255, 106)
BLOOD_D  = (120, 30, 30)

ROT_SKIN   = (126, 158, 110)
ROT_SKIN_D = (80, 104, 70)
ROT_CLOTH  = (74, 78, 66)
ROT_CLOTH_D= (46, 48, 42)
GLOW_INF   = (57, 255, 106)

RUN_SKIN   = (150, 130, 105)
RUN_SKIN_D = (100, 84, 66)
RUN_MUS    = (168, 84, 72)
RUN_MUS_D  = (110, 52, 46)

BR_PLATE   = (96, 92, 88)
BR_PLATE_D = (58, 55, 52)
BR_RUST    = (140, 84, 44)
BR_CRACK   = (255, 150, 60)

# ---------------- core helpers ----------------
def new():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))

def save(im, name):
    p = f"{ASSETS}/{name}"
    im.save(p)

def _vgrad(w, h, c_top, c_bot):
    g = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(g)
    for y in range(h):
        t = y / max(1, h - 1)
        d.line([(0, y), (w, y)], fill=tuple(int(c_top[i] + (c_bot[i] - c_top[i]) * t) for i in range(3)) + (255,))
    return g

def part(mask, bbox, c_top, c_bot):
    """Fill bbox with vertical gradient, masked."""
    x0, y0, x1, y1 = [int(v) for v in bbox]
    w, h = max(1, x1 - x0), max(1, y1 - y0)
    g = _vgrad(w, h, c_top, c_bot)
    m = mask.crop((x0, y0, x1, y1)).convert("L")
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.paste(g, (x0, y0), m)
    return out

def poly_mask(pts):
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    return m

def ell_mask(cx, cy, rx, ry):
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=255)
    return m

def add_glow(im, x, y, r, color, alpha=90):
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(g)
    for i in range(r, 0, -2):
        a = int(alpha * (1 - i / r) ** 1.6)
        d.ellipse([x - i, y - i, x + i, y + i], fill=color + (a,))
    im.alpha_composite(g)

def grain(im, bbox, amt=14):
    x0, y0, x1, y1 = [int(v) for v in bbox]
    n = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
    px = n.load()
    for y in range(y1 - y0):
        for x in range(x1 - x0):
            v = random.randint(-amt, amt)
            px[x, y] = (v, v, v, 26)
    im.alpha_composite(n, (x0, y0))

def rim_stroke(im, pts, color=RIM, width=3, alpha=200):
    d = ImageDraw.Draw(im)
    d.line(pts, fill=color + (alpha,), width=width, joint="curve")

def blade_shape(d, x0, y0, x1, y1, wdt=10):
    """Draw a blade as a thick line + tip + glowing edge."""
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    d.line([(x0, y0), (x1, y1)], fill=STEEL_D + (255,), width=wdt + 4)
    d.line([(x0, y0), (x1, y1)], fill=STEEL + (255,), width=wdt)
    # glowing edge on one side
    d.line([(x0 + nx * wdt * 0.45, y0 + ny * wdt * 0.45),
            (x1 + nx * wdt * 0.45, y1 + ny * wdt * 0.45)], fill=EDGE_G + (230,), width=3)
    # tip
    tx, ty = x1 + dx / L * 14, y1 + dy / L * 14
    d.polygon([(x1 + nx * wdt / 2, y1 + ny * wdt / 2),
               (x1 - nx * wdt / 2, y1 - ny * wdt / 2), (tx, ty)], fill=STEEL + (255,))

def slash_arc(im, cx, cy, r0, r1, a0, a1, color=(200, 255, 210), alpha=150):
    """Crescent slash trail — smooth band, brightest mid-radius."""
    d = ImageDraw.Draw(im)
    band = r1 - r0
    for i in range(6):
        t = i / 5.0
        r = r0 + band * t
        a = int(alpha * (0.3 + 0.7 * math.sin(math.pi * t)))
        d.arc([cx - r, cy - r, cx + r, cy + r], start=a0, end=a1,
              fill=color + (a,), width=max(3, band // 6 + 2))

# =====================================================================
# PLAYER — The Carrier v3
# =====================================================================
def _cloak(im, cx, top_y, hem_y, hem_w, sway=0, back=0):
    """Big flared cloak with folds + rim light. Fills most of frame."""
    pts = [(cx - 34 + back, top_y), (cx + 36 + back, top_y - 4),
           (cx + hem_w + sway, hem_y), (cx - hem_w + sway * 0.6, hem_y + 4)]
    im.alpha_composite(part(poly_mask(pts), (cx - hem_w - 8, top_y - 8, cx + hem_w + 8, hem_y + 8),
                            CLOAK_T, CLOAK_B))
    d = ImageDraw.Draw(im)
    # fold shadows
    for fx, fw in ((-30, 9), (-8, 12), (16, 10), (36, 8)):
        x = cx + fx + sway * 0.4 + back
        d.polygon([(x - fw, top_y + 10), (x + fw, top_y + 10),
                   (x + fw * 1.7 + sway * 0.5, hem_y), (x - fw * 1.7 + sway * 0.5, hem_y)],
                  fill=FOLD + (170,))
    # ragged hem
    for i in range(7):
        hx = cx - hem_w + i * (2 * hem_w / 6) + sway * 0.5
        d.polygon([(hx, hem_y - 2), (hx + 9, hem_y - 2), (hx + 5, hem_y + 12 + (i % 3) * 5)],
                  fill=CLOAK_B + (255,))
    grain(im, (cx - hem_w, top_y, cx + hem_w, hem_y), 12)
    # rim light along right edge + faint fill on left so it never goes pitch black
    rim_stroke(im, [(cx + 36 + back, top_y), (cx + hem_w * 0.92 + sway, hem_y - 30)], RIM, 3, 210)
    rim_stroke(im, [(cx + hem_w * 0.92 + sway, hem_y - 30), (cx + hem_w * 0.8 + sway, hem_y - 6)], RIM_DIM, 2, 150)
    rim_stroke(im, [(cx - 34 + back, top_y + 6), (cx - hem_w * 0.9 + sway * 0.6, hem_y - 34)], RIM_DIM, 2, 80)

def _hood_side(im, cx, cy, facing_right=True, eye_boost=0):
    """Big hood, deep face shadow, large glowing eyes."""
    s = 1 if facing_right else -1
    # hood mass
    im.alpha_composite(part(ell_mask(cx, cy, 42, 44), (cx - 46, cy - 48, cx + 46, cy + 48), CLOAK_T, CLOAK_M))
    d = ImageDraw.Draw(im)
    # peak
    d.polygon([(cx - 10 * s, cy - 40), (cx + 44 * s, cy - 34), (cx + 20 * s, cy - 8)], fill=CLOAK_T + (255,))
    # face shadow (front-right)
    fx = cx + 16 * s
    im.alpha_composite(part(ell_mask(fx, cy + 6, 24, 28), (fx - 28, cy - 26, fx + 28, cy + 38), (4, 6, 12), (10, 14, 24)))
    # glowing eyes — big
    for ex, ey, ew, eh in ((fx - 8, cy + 2, 10, 13), (fx + 9, cy + 3, 9, 12)):
        d.ellipse([ex - ew / 2, ey - eh / 2, ex + ew / 2, ey + eh / 2], fill=(6, 20, 10, 255))
        d.ellipse([ex - ew / 2 + 2, ey - eh / 2 + 2, ex + ew / 2 - 2, ey + eh / 2 - 2], fill=EYE_G + (255,))
    add_glow(im, fx, cy + 4, 26, (57, 255, 106), 60 + eye_boost)
    # vein cracks on hood edge
    d.line([(fx - 20, cy + 22), (fx - 10, cy + 28), (fx - 14, cy + 34)], fill=VEIN + (160,), width=2)
    # rim on hood
    rim_stroke(im, [(cx + 40 * s, cy - 30), (cx + 44 * s, cy + 10)], RIM, 3, 220)
    rim_stroke(im, [(cx + 44 * s, cy - 34), (cx + 20 * s, cy - 44)], RIM_DIM, 2, 160)

def _baldric(im, cx, y0, y1, flip=False):
    d = ImageDraw.Draw(im)
    s = -1 if flip else 1
    d.line([(cx - 30, y0), (cx + 28 * s, y1)], fill=LEATHER_D + (255,), width=16)
    d.line([(cx - 30, y0), (cx + 28 * s, y1)], fill=LEATHER + (255,), width=11)
    # vials
    for i, t in enumerate((0.35, 0.55, 0.75)):
        vx = cx - 30 + (58 * s) * t
        vy = y0 + (y1 - y0) * t
        d.rectangle([vx - 6, vy - 9, vx + 6, vy + 9], fill=(20, 40, 30, 255), outline=STEEL_D + (255,), width=2)
        d.rectangle([vx - 4, vy - 2, vx + 4, vy + 7], fill=VIAL + (255,))
    add_glow(im, cx - 30 + 58 * s * 0.55, y0 + (y1 - y0) * 0.55, 18, VIAL, 50)

def _boot(d, x, y, step=0, wdt=20):
    d.ellipse([x - wdt / 2, y - 26 + step, x + wdt / 2, y + step], fill=(24, 20, 28, 255))
    d.rectangle([x - wdt / 2, y - 30 + step, x + wdt / 2, y - 8 + step], fill=(34, 30, 40, 255))

def draw_player_side(im, ph, mode="idle"):
    """Facing right. ph: 0..3 walk phase / idle variant."""
    cx, d = 96, ImageDraw.Draw(im)
    bob = [0, -5, 0, -5][ph] if mode == "walk" else 0
    sway = [0, 7, 0, -7][ph] if mode == "walk" else (3 if mode == "idle" else 0)
    lunge = 16 if mode == "attack1" else (8 if mode == "attack2" else 0)
    back = -12 if mode == "hurt" else 0
    top_y, hem_y = 74 + bob, 232
    # boots
    if mode in ("death0", "death1"):
        pass
    elif mode == "walk":
        _boot(d, cx - 14 + [0, 14, 0, -14][ph], hem_y - 6, [0, -10, 0, -10][ph])
        _boot(d, cx + 16 + [0, -14, 0, 14][ph], hem_y - 4, [0, -10, 0, -10][(ph + 2) % 4])
    else:
        _boot(d, cx - 12, hem_y - 6); _boot(d, cx + 18, hem_y - 4)
    # cloak
    _cloak(im, cx, top_y, hem_y, 56, sway, back)
    # baldric
    _baldric(im, cx + back, 108 + bob, 168 + bob)
    # hood + face
    _hood_side(im, cx + back, 52 + bob, True, eye_boost=40 if mode.startswith("attack") else 0)
    # blade per pose
    hx, hy = cx + 30 + back + lunge, 150 + bob
    if mode == "idle":
        blade_shape(d, hx, hy, hx + 10, hy + 78, 9)
        d.line([(hx - 14, hy + 2), (hx + 14, hy + 2)], fill=STEEL_D + (255,), width=6)  # guard
    elif mode == "walk":
        blade_shape(d, hx, hy, hx + 12, hy + 76, 9)
        d.line([(hx - 14, hy + 2), (hx + 14, hy + 2)], fill=STEEL_D + (255,), width=6)
    elif mode == "attack0":   # windup: blade up-back, body coiled
        blade_shape(d, hx - 6, hy - 10, hx - 52, hy - 78, 10)
        add_glow(im, hx - 40, hy - 60, 30, (57, 255, 106), 60)
    elif mode == "attack1":   # slash: blade swept forward + big arc
        blade_shape(d, hx - 30, hy - 20, hx + 78, hy - 34, 11)
        slash_arc(im, hx + 10, hy - 10, 60, 108, -70, 40, (190, 255, 200), 170)
        slash_arc(im, hx + 10, hy - 10, 40, 66, -60, 30, (57, 255, 106), 130)
        add_glow(im, hx + 40, hy - 30, 44, (200, 255, 210), 80)
    elif mode == "attack2":   # recover: blade low forward
        blade_shape(d, hx + 6, hy + 6, hx + 52, hy + 52, 9)
    elif mode == "hurt":
        blade_shape(d, hx - 8, hy, hx + 2, hy + 70, 9)
        rim_stroke(im, [(cx - 34 + back, top_y), (cx - 52 + back, hem_y - 40)], (255, 90, 90), 4, 220)
    # left clawed hand (visible in attacks)
    if mode in ("attack0", "attack1"):
        gx, gy = cx - 34 + back, 150 + bob
        d.ellipse([gx - 9, gy - 11, gx + 9, gy + 11], fill=SKIN + (255,))
        for i in range(3):
            d.line([(gx - 4 + i * 5, gy + 8), (gx - 6 + i * 5, gy + 20)], fill=SKIN_D + (255,), width=3)
        d.line([(gx - 6, gy - 6), (gx + 2, gy + 2)], fill=VEIN + (200,), width=2)
        add_glow(im, gx, gy, 16, VEIN, 40)
    return im

def draw_player_down(im, ph, mode="idle"):
    """Facing viewer."""
    cx, d = 96, ImageDraw.Draw(im)
    bob = [0, -5, 0, -5][ph] if mode == "walk" else 0
    sway = [0, 5, 0, -5][ph] if mode == "walk" else 0
    top_y, hem_y = 76 + bob, 234
    if mode == "walk":
        _boot(d, cx - 16, hem_y - 6, [0, -10, 0, -10][ph])
        _boot(d, cx + 16, hem_y - 4, [0, -10, 0, -10][(ph + 2) % 4])
    else:
        _boot(d, cx - 14, hem_y - 6); _boot(d, cx + 16, hem_y - 4)
    _cloak(im, cx, top_y, hem_y, 54, sway)
    _baldric(im, cx, 110 + bob, 170 + bob)
    # hood front
    im.alpha_composite(part(ell_mask(cx, 54 + bob, 42, 44), (cx - 46, 6 + bob, cx + 46, 102 + bob), CLOAK_T, CLOAK_M))
    d.polygon([(cx - 12, 12 + bob), (cx + 12, 12 + bob), (cx, 34 + bob)], fill=CLOAK_T + (255,))
    im.alpha_composite(part(ell_mask(cx, 62 + bob, 26, 28), (cx - 30, 30 + bob, cx + 30, 94 + bob), (4, 6, 12), (12, 16, 26)))
    for ex in (cx - 11, cx + 11):
        d.ellipse([ex - 6, 54 + bob, ex + 6, 68 + bob], fill=(6, 20, 10, 255))
        d.ellipse([ex - 4, 56 + bob, ex + 4, 66 + bob], fill=EYE_G + (255,))
    add_glow(im, cx, 62 + bob, 30, (57, 255, 106), 65)
    d.line([(cx - 18, 78 + bob), (cx - 8, 84 + bob)], fill=VEIN + (170,), width=2)
    rim_stroke(im, [(cx + 40, 24 + bob), (cx + 44, 70 + bob)], RIM, 3, 210)
    # blade held right
    hx = cx + 52
    blade_shape(d, hx, 140 + bob, hx + 8, 222, 9)
    d.line([(hx - 13, 142 + bob), (hx + 13, 142 + bob)], fill=STEEL_D + (255,), width=6)
    return im

def draw_player_up(im, ph, mode="idle"):
    """Back view."""
    cx, d = 96, ImageDraw.Draw(im)
    bob = [0, -5, 0, -5][ph] if mode == "walk" else 0
    sway = [0, 5, 0, -5][ph] if mode == "walk" else 0
    top_y, hem_y = 76 + bob, 234
    if mode == "walk":
        _boot(d, cx - 16, hem_y - 6, [0, -10, 0, -10][ph])
        _boot(d, cx + 16, hem_y - 4, [0, -10, 0, -10][(ph + 2) % 4])
    else:
        _boot(d, cx - 14, hem_y - 6); _boot(d, cx + 16, hem_y - 4)
    _cloak(im, cx, top_y, hem_y, 54, sway)
    # hood back with seam
    im.alpha_composite(part(ell_mask(cx, 54 + bob, 42, 44), (cx - 46, 6 + bob, cx + 46, 102 + bob), CLOAK_M, CLOAK_B))
    d.line([(cx, 14 + bob), (cx, 96 + bob)], fill=FOLD + (200,), width=4)
    d.polygon([(cx - 12, 12 + bob), (cx + 12, 12 + bob), (cx, 34 + bob)], fill=CLOAK_M + (255,))
    rim_stroke(im, [(cx + 40, 24 + bob), (cx + 44, 70 + bob)], RIM, 3, 210)
    # infection veins crawling on back
    d.line([(cx - 20, 120 + bob), (cx - 8, 140 + bob), (cx - 14, 160 + bob)], fill=VEIN + (150,), width=2)
    add_glow(im, cx - 12, 140 + bob, 14, VEIN, 40)
    hx = cx + 52
    blade_shape(d, hx, 140 + bob, hx + 8, 222, 9)
    d.line([(hx - 13, 142 + bob), (hx + 13, 142 + bob)], fill=STEEL_D + (255,), width=6)
    return im

def draw_player_death(im, stage):
    cx, d = 96, ImageDraw.Draw(im)
    if stage == 0:
        # kneeling, head bowed, blade dropped
        _cloak(im, cx, 120, 236, 58, 0)
        im.alpha_composite(part(ell_mask(cx, 96, 36, 34), (cx - 40, 60, cx + 40, 132), CLOAK_T, CLOAK_M))
        d.ellipse([cx - 20, 84, cx + 20, 116], fill=(4, 6, 12, 255))
        blade_shape(d, cx + 66, 200, cx + 96, 236, 8)  # dropped blade
        add_glow(im, cx, 150, 40, (57, 255, 106), 50)
    else:
        # collapsed + infection pool
        d.ellipse([cx - 70, 210, cx + 70, 250], fill=(20, 60, 30, 200))
        d.ellipse([cx - 46, 218, cx + 46, 244], fill=(40, 140, 70, 200))
        add_glow(im, cx, 230, 60, (57, 255, 106), 90)
        im.alpha_composite(part(poly_mask([(cx - 60, 236), (cx - 40, 190), (cx + 60, 196), (cx + 70, 236)]),
                                (cx - 74, 186, cx + 74, 240), CLOAK_B, (10, 12, 24)))
        im.alpha_composite(part(ell_mask(cx - 44, 210, 24, 20), (cx - 72, 188, cx - 16, 232), CLOAK_M, CLOAK_B))
        # fading eye
        d.ellipse([cx - 50, 204, cx - 38, 214], fill=(30, 80, 40, 255))
    return im

# =====================================================================
# SHAMBLER v3 — "Rotwalker": bulky, exposed glowing ribcage, one huge arm
# =====================================================================
def _shambler_body(im, cx, lurch=0, rear=0, slam=0, glow_boost=0):
    d = ImageDraw.Draw(im)
    base_y = 236
    # legs (short, bowed)
    for lx, bent in ((-24, 1), (22, -1)):
        x = cx + lx + lurch
        d.rectangle([x - 13, base_y - 70, x + 13, base_y - 6], fill=ROT_CLOTH_D + (255,))
        d.ellipse([x - 15, base_y - 22, x + 15, base_y + 2], fill=(40, 44, 38, 255))
    # torso: massive, hunched
    ty = 150 - rear * 26 + slam * 10
    torso = [(cx - 52 + lurch, ty - 62), (cx + 54 + lurch, ty - 66),
             (cx + 48 + lurch, ty + 62), (cx - 56 + lurch, ty + 58)]
    im.alpha_composite(part(poly_mask(torso), (cx - 60, ty - 70, cx + 60, ty + 66), ROT_SKIN, ROT_SKIN_D))
    # torn shirt strips
    for sx, sw in ((-38, 16), (-8, 20), (24, 14)):
        d.polygon([(cx + sx + lurch, ty - 64), (cx + sx + sw + lurch, ty - 64),
                   (cx + sx + sw * 0.7 + lurch, ty + 40), (cx + sx * 0.7 + lurch, ty + 40)],
                  fill=ROT_CLOTH + (255,))
        d.polygon([(cx + sx * 0.7 + lurch, ty + 40), (cx + sx + sw * 0.7 + lurch, ty + 40),
                   (cx + sx + sw * 0.4 + lurch, ty + 62), (cx + sx * 0.4 + lurch, ty + 62)],
                  fill=ROT_CLOTH_D + (255,))
    # EXPOSED RIBCAGE — glowing green ribs
    rib_cx, rib_cy = cx + 6 + lurch, ty + 2
    for i in range(4):
        ry = rib_cy - 24 + i * 15
        d.arc([rib_cx - 30, ry - 10, rib_cx + 30, ry + 10], start=200, end=340, fill=(30, 40, 30, 255), width=9)
        d.arc([rib_cx - 30, ry - 10, rib_cx + 30, ry + 10], start=200, end=340, fill=GLOW_INF + (255,), width=4)
    add_glow(im, rib_cx, rib_cy, 46, GLOW_INF, 70 + glow_boost)
    # head: unhinged jaw, inner glow
    hx, hy = cx + 10 + lurch, ty - 92 - rear * 10
    im.alpha_composite(part(ell_mask(hx, hy, 26, 28), (hx - 30, hy - 32, hx + 30, hy + 32), ROT_SKIN, ROT_SKIN_D))
    d.ellipse([hx - 2, hy - 2, hx + 22, hy + 26], fill=(10, 8, 8, 255))  # maw
    add_glow(im, hx + 10, hy + 12, 22, GLOW_INF, 80 + glow_boost)
    for ex in (hx - 12, hx + 2):
        d.ellipse([ex - 5, hy - 14, ex + 5, hy - 4], fill=(8, 16, 8, 255))
        d.ellipse([ex - 3, hy - 12, ex + 3, hy - 6], fill=EYE_G + (255,))
    # jaw bone
    d.polygon([(hx + 2, hy + 18), (hx + 22, hy + 20), (hx + 14, hy + 34), (hx, hy + 30)], fill=ROT_SKIN_D + (255,))
    # veins on skull
    d.line([(hx - 20, hy - 20), (hx - 10, hy - 8)], fill=VEIN + (180,), width=2)
    # rim light right side
    rim_stroke(im, [(cx + 54 + lurch, ty - 60), (cx + 50 + lurch, ty + 50)], (170, 255, 170), 3, 160)
    return ty

def draw_shambler(im, ph, mode="walk"):
    cx = 96
    d = ImageDraw.Draw(im)
    lurch = [0, 10, 0, -10][ph] if mode == "walk" else 0
    if mode == "attack0":      # telegraph: rearing up, cracks flaring
        ty = _shambler_body(im, cx, rear=1, glow_boost=60)
        # both arms raised high
        for ax in (-46, 50):
            d.line([(cx + ax * 0.6, ty - 40), (cx + ax, ty - 130)], fill=ROT_SKIN_D + (255,), width=26)
            d.ellipse([cx + ax - 16, ty - 146, cx + ax + 16, ty - 114], fill=ROT_SKIN + (255,))
        add_glow(im, cx, ty - 120, 60, GLOW_INF, 70)
    elif mode == "attack1":    # slam: arms down, shockwave + dust
        ty = _shambler_body(im, cx, slam=1)
        for ax in (-48, 52):
            d.line([(cx + ax * 0.6, ty - 40), (cx + ax, ty + 66)], fill=ROT_SKIN_D + (255,), width=30)
            d.ellipse([cx + ax - 20, ty + 52, cx + ax + 20, ty + 86], fill=ROT_SKIN + (255,))
            for i in range(4):  # claws
                d.line([(cx + ax - 12 + i * 8, ty + 78), (cx + ax - 14 + i * 8, ty + 96)], fill=(220, 220, 210, 255), width=4)
        for r, a in ((80, 110), (110, 70), (140, 40)):
            d.ellipse([cx - r, 236 - r * 0.35, cx + r, 236 + r * 0.35], outline=GLOW_INF + (a,), width=6)
        add_glow(im, cx, 226, 70, GLOW_INF, 90)
    else:                      # walk: lurching, one huge arm dragging
        ty = _shambler_body(im, cx, lurch=lurch)
        bob = [0, -4, 0, -4][ph]
        # huge right arm dragging with claws
        ax = cx + 58 + lurch
        d.line([(cx + 34, ty - 30 + bob), (ax, ty + 70)], fill=ROT_SKIN_D + (255,), width=30)
        d.ellipse([ax - 19, ty + 56, ax + 19, ty + 90], fill=ROT_SKIN + (255,))
        for i in range(4):
            d.line([(ax - 12 + i * 8, ty + 82), (ax - 15 + i * 8, ty + 102)], fill=(220, 220, 210, 255), width=5)
        # withered left arm
        d.line([(cx - 40, ty - 30 + bob), (cx - 62 + lurch, ty + 30)], fill=ROT_SKIN_D + (255,), width=15)
    grain(im, (cx - 60, 60, cx + 60, 236), 10)
    return im

def draw_shambler_death(im, stage):
    cx, d = 96, ImageDraw.Draw(im)
    if stage == 0:
        # crumpling forward
        im.alpha_composite(part(poly_mask([(cx - 56, 236), (cx - 40, 150), (cx + 50, 156), (cx + 60, 236)]),
                                (cx - 60, 146, cx + 64, 240), ROT_SKIN_D, (50, 62, 44)))
        im.alpha_composite(part(ell_mask(cx + 8, 140, 24, 22), (cx - 20, 116, cx + 36, 164), ROT_SKIN, ROT_SKIN_D))
        add_glow(im, cx, 200, 50, GLOW_INF, 60)
    else:
        # dissolved into glowing rot pool
        d.ellipse([cx - 64, 214, cx + 64, 250], fill=(24, 54, 32, 210))
        d.ellipse([cx - 40, 222, cx + 40, 246], fill=(52, 150, 76, 210))
        add_glow(im, cx, 232, 56, GLOW_INF, 100)
        for i in range(5):  # bone bits
            bx, by = cx - 40 + i * 18, 226 + (i % 2) * 8
            d.line([(bx, by), (bx + 10, by - 6)], fill=(200, 200, 190, 220), width=4)
    return im

# =====================================================================
# RUNNER v3 — "Skitter": tall, emaciated, glowing spine, long claws
# =====================================================================
def _runner_body(im, cx, lean=0, coil=0, air=0, glow_boost=0):
    d = ImageDraw.Draw(im)
    base_y = 238 - air
    hip_y = base_y - 110 + coil * 30
    sh_y = hip_y - 78 + coil * 10
    # long legs
    for lx, fwd in ((-16, 1), (16, -1)):
        kx = cx + lx + lean * 0.4 + fwd * 14
        d.line([(cx + lx, hip_y), (kx, base_y - 44)], fill=RUN_SKIN_D + (255,), width=14)
        d.line([(kx, base_y - 44), (kx + fwd * 10, base_y - 4)], fill=RUN_SKIN_D + (255,), width=11)
        d.ellipse([kx + fwd * 10 - 9, base_y - 14, kx + fwd * 10 + 9, base_y + 4], fill=RUN_SKIN + (255,))
    # emaciated torso
    im.alpha_composite(part(poly_mask([(cx - 22 + lean * 0.5, sh_y), (cx + 24 + lean * 0.5, sh_y + 6),
                                       (cx + 16, hip_y), (cx - 18, hip_y)]),
                            (cx - 26, sh_y - 6, cx + 28, hip_y + 6), RUN_SKIN, RUN_SKIN_D))
    # EXPOSED SPINE — glowing dots down the back
    for i in range(6):
        sy = sh_y + 8 + i * 12
        sx = cx - 20 + lean * 0.5 - i * 1.5
        d.ellipse([sx - 5, sy - 5, sx + 5, sy + 5], fill=GLOW_INF + (255,))
    add_glow(im, cx - 22, sh_y + 40, 34, GLOW_INF, 60 + glow_boost)
    # ribs hint
    for i in range(3):
        ry = sh_y + 22 + i * 13
        d.arc([cx - 20 + lean * 0.5, ry - 8, cx + 22 + lean * 0.5, ry + 8], start=190, end=350,
              fill=RUN_SKIN_D + (255,), width=3)
    # long arms with claws
    for ax, fwd in ((-1, -1), (1, 1)):
        sx = cx + ax * 24 + lean * 0.5
        ex = sx + fwd * 26 + lean * 0.6
        hx2 = ex + fwd * 22
        hy2 = sh_y + 66 - coil * 20
        d.line([(sx, sh_y + 10), (ex, sh_y + 44)], fill=RUN_MUS_D + (255,), width=16)
        d.line([(ex, sh_y + 44), (hx2, hy2)], fill=RUN_SKIN_D + (255,), width=11)
        for i in range(4):  # long claws
            d.line([(hx2 - 8 + i * 6, hy2), (hx2 - 12 + i * 6 + fwd * 8, hy2 + 22)], fill=(230, 230, 220, 255), width=4)
    # head tilted
    hx, hy = cx + 10 + lean * 0.7, sh_y - 26
    im.alpha_composite(part(ell_mask(hx, hy, 20, 24), (hx - 24, hy - 28, hx + 24, hy + 28), RUN_SKIN, RUN_SKIN_D))
    tilt = -0.35
    for ex, ey in ((hx - 8, hy - 6), (hx + 8, hy - 2)):
        d.ellipse([ex - 6, ey - 7, ex + 6, ey + 7], fill=(10, 18, 8, 255))
        d.ellipse([ex - 4, ey - 5, ex + 4, ey + 5], fill=(255, 220, 90, 255))  # amber eyes
    add_glow(im, hx, hy - 4, 20, (255, 220, 90), 50)
    d.line([(hx - 14, hy + 12), (hx + 10, hy + 18)], fill=(60, 20, 20, 255), width=5)  # gash mouth
    # muscle striations glowing faintly
    d.line([(cx - 6, sh_y + 30), (cx + 4, sh_y + 52)], fill=RUN_MUS + (170,), width=3)
    rim_stroke(im, [(cx + 24 + lean * 0.5, sh_y), (cx + 18, hip_y)], (255, 240, 170), 2, 150)
    return sh_y

def draw_runner(im, ph, mode="walk"):
    cx = 96
    d = ImageDraw.Draw(im)
    if mode == "attack0":      # coil
        _runner_body(im, cx, coil=1, glow_boost=40)
    elif mode == "attack1":    # leaping scratch + claw trails
        _runner_body(im, cx, lean=26, air=34, glow_boost=30)
        for off in (-30, -6, 18):
            d.line([(cx + 40, 120 + off), (cx + 110, 150 + off)], fill=(255, 240, 180, 200), width=5)
            d.line([(cx + 40, 120 + off), (cx + 110, 150 + off)], fill=(255, 255, 255, 230), width=2)
        add_glow(im, cx + 70, 140, 40, (255, 240, 180), 60)
    else:                      # bounding run
        lean = [0, 12, 4, 14][ph]
        air = [0, 16, 0, 10][ph]
        _runner_body(im, cx, lean=lean, air=air)
    grain(im, (cx - 40, 40, cx + 50, 240), 10)
    return im

def draw_runner_death(im, stage):
    cx, d = 96, ImageDraw.Draw(im)
    if stage == 0:
        im.alpha_composite(part(poly_mask([(cx - 30, 236), (cx - 20, 150), (cx + 26, 156), (cx + 34, 236)]),
                                (cx - 34, 146, cx + 38, 240), RUN_SKIN_D, (70, 60, 50)))
        im.alpha_composite(part(ell_mask(cx + 6, 132, 18, 20), (cx - 16, 110, cx + 28, 156), RUN_SKIN, RUN_SKIN_D))
    else:
        d.ellipse([cx - 52, 218, cx + 52, 250], fill=(30, 44, 30, 210))
        add_glow(im, cx, 234, 46, GLOW_INF, 90)
        for i in range(4):
            bx = cx - 36 + i * 22
            d.line([(bx, 232), (bx + 8, 214)], fill=(210, 200, 190, 220), width=4)
    return im

# =====================================================================
# BRUTE v3 — "Bulwark": rusted plate armor, glowing cracks, tiny head
# =====================================================================
def _brute_body(im, cx, stomp=0, raise_f=0, glow_boost=0):
    d = ImageDraw.Draw(im)
    base_y = 240
    # dark gap between legs first (separation)
    d.rectangle([cx - 9, base_y - 96, cx + 9, base_y - 8], fill=(18, 16, 14, 255))
    # tree-trunk legs in armor
    for lx in (-30, 30):
        x = cx + lx
        d.rectangle([x - 20, base_y - 96, x + 20, base_y - 8], fill=BR_PLATE_D + (255,))
        d.rectangle([x - 20, base_y - 96, x + 20, base_y - 70], fill=BR_PLATE + (255,))
        d.ellipse([x - 22, base_y - 24, x + 22, base_y + 2], fill=(46, 42, 40, 255))
    # massive torso — darker hide between the plates
    ty = 150 - raise_f * 14 + stomp * 6
    im.alpha_composite(part(poly_mask([(cx - 64, ty - 70), (cx + 64, ty - 70), (cx + 56, ty + 70), (cx - 58, ty + 70)]),
                            (cx - 68, ty - 74, cx + 68, ty + 74), (62, 54, 48), (34, 30, 28)))
    # chest plate — lighter, clearly a separate plate
    im.alpha_composite(part(poly_mask([(cx - 46, ty - 52), (cx + 46, ty - 52), (cx + 40, ty + 30), (cx - 42, ty + 30)]),
                            (cx - 50, ty - 56, cx + 50, ty + 34), (128, 122, 116), (86, 82, 78)))
    d.rectangle([cx - 46, ty - 52, cx + 46, ty - 46], fill=(150, 144, 138, 255))  # plate top edge catch-light
    # glowing cracks between plates
    for crx, cry, cl in ((-30, ty - 20, 26), (24, ty + 6, 30), (-6, ty - 44, 22), (38, ty - 34, 18)):
        d.line([(crx - 12, cry), (crx + 12, cry + 6)], fill=BR_CRACK + (255,), width=6)
        d.line([(crx, cry - 8), (crx + 4, cry + 12)], fill=(255, 220, 160, 255), width=3)
    add_glow(im, cx, ty - 10, 60, BR_CRACK, 55 + glow_boost)
    # pauldrons
    for px in (-62, 62):
        im.alpha_composite(part(ell_mask(cx + px, ty - 62, 30, 26), (cx + px - 34, ty - 92, cx + px + 34, ty - 32),
                                BR_PLATE, BR_PLATE_D))
        d.arc([cx + px - 30, ty - 88, cx + px + 30, ty - 36], start=200, end=340, fill=BR_RUST + (255,), width=5)
    # rust streaks
    for i in range(6):
        rx = cx - 50 + i * 20
        d.line([(rx, ty - 50), (rx + 3, ty + 20)], fill=BR_RUST + (130,), width=4)
    # head sunk low between pauldrons, joined by a neck shadow
    hx, hy = cx + 6, ty - 86
    d.rectangle([hx - 15, hy + 8, hx + 15, ty - 66], fill=(16, 14, 12, 255))
    im.alpha_composite(part(ell_mask(hx, hy, 22, 23), (hx - 26, hy - 27, hx + 26, hy + 27), ROT_SKIN, ROT_SKIN_D))
    for ex in (hx - 9, hx + 9):
        d.ellipse([ex - 6, hy - 8, ex + 6, hy + 4], fill=(12, 8, 4, 255))
        d.ellipse([ex - 4, hy - 6, ex + 4, hy + 2], fill=(255, 120, 40, 255))
    add_glow(im, hx, hy - 2, 26, (255, 120, 40), 70)
    d.line([(hx - 11, hy + 13), (hx + 13, hy + 13)], fill=(40, 16, 12, 255), width=5)
    rim_stroke(im, [(cx + 64, ty - 66), (cx + 58, ty + 60)], (255, 220, 170), 3, 170)
    return ty

def draw_brute(im, ph, mode="walk"):
    cx = 96
    d = ImageDraw.Draw(im)
    if mode == "attack0":      # fists raised high, cracks flaring
        ty = _brute_body(im, cx, raise_f=1, glow_boost=70)
        for ax in (-70, 70):
            d.line([(cx + ax * 0.7, ty - 50), (cx + ax, ty - 150)], fill=(60, 54, 50, 255), width=40)
            d.rectangle([cx + ax - 26, ty - 178, cx + ax + 26, ty - 132], fill=BR_PLATE + (255,),
                        outline=BR_PLATE_D + (255,), width=4)
            d.line([(cx + ax - 20, ty - 155), (cx + ax + 20, ty - 150)], fill=BR_CRACK + (255,), width=5)
        add_glow(im, cx, ty - 140, 70, BR_CRACK, 80)
    elif mode == "attack1":    # ground slam + shockwave + debris
        ty = _brute_body(im, cx, stomp=1)
        for ax in (-72, 72):
            d.line([(cx + ax * 0.7, ty - 50), (cx + ax, ty + 78)], fill=(60, 54, 50, 255), width=44)
            d.rectangle([cx + ax - 28, ty + 48, cx + ax + 28, ty + 100], fill=BR_PLATE_D + (255,),
                        outline=BR_PLATE + (255,), width=4)
        for r, a in ((90, 120), (125, 80), (160, 45)):
            d.ellipse([cx - r, 240 - r * 0.32, cx + r, 240 + r * 0.32], outline=BR_CRACK + (a,), width=7)
        for i in range(8):  # debris chunks
            dx2 = cx - 90 + i * 26
            dy2 = 200 - (i * 37 % 60)
            d.polygon([(dx2, dy2), (dx2 + 12, dy2 + 4), (dx2 + 4, dy2 + 14)], fill=(90, 84, 78, 255))
        add_glow(im, cx, 225, 80, BR_CRACK, 100)
    else:                      # heavy stomp walk
        rock = [0, 6, 0, -6][ph]
        ty = _brute_body(im, cx)
        for ax, fwd in ((-66, 1), (66, -1)):
            sw = [0, 14, 0, -14][ph] * fwd
            d.line([(cx + ax * 0.75, ty - 40), (cx + ax + sw, ty + 60)], fill=(60, 54, 50, 255), width=38)
            d.rectangle([cx + ax + sw - 24, ty + 34, cx + ax + sw + 24, ty + 82], fill=BR_PLATE_D + (255,))
        # dust at feet
        for i in range(4):
            dx2 = cx - 60 + i * 40 + rock
            d.ellipse([dx2 - 14, 226, dx2 + 14, 246], fill=(120, 115, 105, 90))
    grain(im, (cx - 70, 40, cx + 70, 242), 10)
    return im

def draw_brute_death(im, stage):
    cx, d = 96, ImageDraw.Draw(im)
    if stage == 0:
        # kneeling, plates cracked wide
        im.alpha_composite(part(poly_mask([(cx - 58, 236), (cx - 48, 130), (cx + 52, 134), (cx + 60, 236)]),
                                (cx - 62, 126, cx + 64, 240), (60, 54, 50), (40, 36, 34)))
        im.alpha_composite(part(ell_mask(cx + 6, 104, 22, 23), (cx - 20, 78, cx + 32, 130), ROT_SKIN, ROT_SKIN_D))
        d.line([(cx - 30, 160), (cx + 30, 170)], fill=BR_CRACK + (255,), width=5)
        add_glow(im, cx, 165, 44, BR_CRACK, 70)
    else:
        # toppled, armor scattered
        im.alpha_composite(part(poly_mask([(cx - 80, 236), (cx - 60, 190), (cx + 70, 196), (cx + 80, 236)]),
                                (cx - 84, 186, cx + 84, 240), (48, 44, 42), (32, 30, 28)))
        for i in range(3):
            px2 = cx - 50 + i * 48
            d.rectangle([px2 - 16, 200 + (i % 2) * 10, px2 + 16, 224 + (i % 2) * 10], fill=BR_PLATE_D + (255,))
        add_glow(im, cx, 220, 56, BR_CRACK, 80)
    return im

# =====================================================================
# FX assets
# =====================================================================
def fx_assets():
    # soft drop shadow
    sh = Image.new("RGBA", (96, 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(sh)
    for i in range(20, 0, -1):
        a = int(110 * (1 - i / 20))
        d.ellipse([48 - i * 2.2, 20 - i, 48 + i * 2.2, 20 + i], fill=(0, 0, 0, a))
    save(sh.filter(ImageFilter.GaussianBlur(2)), "shadow.png")
    # spark
    sp = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(sp)
    d.rectangle([4, 4, 12, 12], fill=(255, 255, 255, 255))
    d.rectangle([6, 6, 10, 10], fill=(255, 255, 255, 255))
    save(sp, "spark.png")
    # dust puff
    du = Image.new("RGBA", (48, 48), (0, 0, 0, 0))
    d = ImageDraw.Draw(du)
    for i in range(22, 0, -2):
        a = int(90 * (1 - i / 22))
        d.ellipse([24 - i, 24 - i, 24 + i, 24 + i], fill=(200, 195, 185, a))
    save(du.filter(ImageFilter.GaussianBlur(1)), "dust.png")
    # slash trail crescent
    tr = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(tr)
    for r, a in ((118, 40), (100, 80), (82, 130), (64, 90)):
        d.arc([128 - r, 128 - r, 128 + r, 128 + r], start=-75, end=45, fill=(190, 255, 200, a), width=16)
    for r, a in ((100, 60), (82, 110)):
        d.arc([128 - r, 128 - r, 128 + r, 128 + r], start=-70, end=40, fill=(255, 255, 255, a), width=6)
    save(tr, "trail_arc.png")
    print("fx assets written")

# ================= GENERATE =================
def breathe(im, dy=2):
    out = new()
    out.alpha_composite(im, (0, dy))
    return out

def gen():
    n = 0
    # ---- player (24) ----
    for dname, fn in (("down", draw_player_down), ("up", draw_player_up), ("side", draw_player_side)):
        for v in (0, 1):
            im = new(); fn(im, 0, "idle"); save(breathe(im, 2 * v), f"p_{dname}_idle_{v}.png"); n += 1
        for ph in range(4):
            im = new(); fn(im, ph, "walk"); save(im, f"p_{dname}_walk_{ph}.png"); n += 1
    for i, m in enumerate(("attack0", "attack1", "attack2")):
        im = new(); draw_player_side(im, 0, m); save(im, f"p_attack_{i}.png"); n += 1
    im = new(); draw_player_side(im, 0, "hurt"); save(im, "p_hurt_0.png"); n += 1
    for s in (0, 1):
        im = new(); draw_player_death(im, s); save(im, f"p_death_{s}.png"); n += 1
    # ---- infected (24) ----
    for tname, wfn, dfn in (("shambler", draw_shambler, draw_shambler_death),
                            ("runner", draw_runner, draw_runner_death),
                            ("brute", draw_brute, draw_brute_death)):
        for ph in range(4):
            im = new(); wfn(im, ph, "walk"); save(im, f"e_{tname}_walk_{ph}.png"); n += 1
        for i, m in enumerate(("attack0", "attack1")):
            im = new(); wfn(im, 0, m); save(im, f"e_{tname}_attack_{i}.png"); n += 1
        for s in (0, 1):
            im = new(); dfn(im, s); save(im, f"e_{tname}_death_{s}.png"); n += 1
    fx_assets()
    print(f"generated {n} v3 frames")

if __name__ == "__main__":
    gen()
