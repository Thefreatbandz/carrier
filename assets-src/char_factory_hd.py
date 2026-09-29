#!/usr/bin/env python3
"""CARRIER HD character sprite factory.
192x256 canvas, gradient-shaded parts, rim light, glows. Same filenames as before
so no game code changes are needed.
"""
from PIL import Image, ImageDraw, ImageFilter
import os, math

OUT = os.path.join(os.path.dirname(__file__), "..", "assets")
W, H = 192, 256

# ---------- palette ----------
INFECT = (57, 255, 112)        # infection green
INFECT_DIM = (24, 140, 62)
EYE_CORE = (220, 255, 230)

def new():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))

def save(im, name):
    p = os.path.join(OUT, name)
    im.save(p)

def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c[:3])

def lerp3(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def part(fn, box, c_top, c_bot, blur=0):
    """Draw silhouette fn(d) on a mask, fill with vertical gradient, return RGBA."""
    m = Image.new("L", (W, H), 0)
    fn(ImageDraw.Draw(m))
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    x0, y0, x1, y1 = [int(v) for v in box]
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(W, x1), min(H, y1)
    for y in range(y0, y1):
        t = (y - y0) / max(1, y1 - y0 - 1)
        c = lerp3(c_top, c_bot, t) + (255,)
        gd.line([(x0, y), (x1, y)], fill=c)
    g.putalpha(m)
    if blur:
        g = g.filter(ImageFilter.GaussianBlur(blur))
    return g

def ellipse_fn(cx, cy, rx, ry):
    return lambda d: d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=255)

def poly_fn(pts):
    return lambda d: d.polygon(pts, fill=255)

def rrect_fn(box, r=8):
    return lambda d: d.rounded_rectangle(box, radius=r, fill=255)

def add_glow(im, cx, cy, r, color, alpha=110):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    steps = max(2, r // 6)
    for i in range(steps, 0, -1):
        rr = r * i / steps
        a = int(alpha * (1 - i / (steps + 1)) ** 1.5)
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=color + (a,))
    im.alpha_composite(ov)

def rim_light(im, mask_fn, side, color, alpha=90, width=7):
    """Paint a rim-light strip along one side of a silhouette."""
    m = Image.new("L", (W, H), 0)
    mask_fn(ImageDraw.Draw(m))
    edge = m.filter(ImageFilter.FIND_EDGES)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    px = edge.load()
    for y in range(H):
        for x in range(W):
            if px[x, y] > 40:
                ok = (side == "right" and x > W // 2) or (side == "left" and x < W // 2) \
                     or (side == "top" and y < H // 2)
                if ok:
                    od.ellipse([x - width, y - width, x + width, y + width],
                               fill=color + (alpha,))
    im.alpha_composite(ov)

def fold_lines(d, x, y0, y1, n, spread, color, width=3):
    for i in range(n):
        fx = x + (i - (n - 1) / 2) * spread
        d.line([(fx, y0), (fx + spread * 0.3, y1)], fill=color, width=width)

def boot_lace(*a, **k):
    pass

# ================= PLAYER (hooded carrier) =================
CLOAK_T, CLOAK_B = (48, 56, 76), (15, 18, 26)
CLOAK_DK = (9, 11, 17)
HOOD_T, HOOD_B = (56, 64, 86), (20, 24, 34)
LEATHER_T, LEATHER_B = (74, 56, 40), (38, 29, 21)
STEEL_T, STEEL_B = (168, 178, 196), (96, 104, 122)
STEEL_EDGE = (232, 240, 250)

def draw_blade(im, bx, by, tx, ty, w=9):
    d = ImageDraw.Draw(im)
    d.line([(bx, by), (tx, ty)], fill=STEEL_B + (255,), width=w + 3)
    d.line([(bx, by), (tx, ty)], fill=STEEL_T + (255,), width=w)
    # bright cutting edge offset
    mx, my = (tx - bx), (ty - by)
    L = math.hypot(mx, my) or 1
    nx, ny = -my / L * 2.5, mx / L * 2.5
    d.line([(bx + nx, by + ny), (tx + nx, ty + ny)], fill=STEEL_EDGE + (255,), width=2)
    # hilt
    d.line([(bx, by), (bx - mx / L * 14, by - my / L * 14)], fill=(30, 22, 16, 255), width=w + 1)
    d.ellipse([bx - 7, by - 7, bx + 7, by + 7], fill=(52, 40, 28, 255))

def draw_player_side(im, ph, mode="idle"):
    """Facing right. ph: walk phase 0..3 / idle variant. mode: idle,walk,attack0..2,hurt,death0,death1."""
    d = ImageDraw.Draw(im)
    cx = 96
    bob = 0
    lean = 0
    if mode == "walk":
        bob = [0, -4, 0, -4][ph]
        lean = 3
    lunge = 14 if mode == "attack1" else (6 if mode == "attack2" else 0)
    back = -10 if mode == "hurt" else 0
    cx += lunge + back
    # ---- legs ----
    if mode in ("death0", "death1"):
        pass  # drawn later as collapsed
    else:
        if mode == "walk":
            feet = [(-18, 0), (6, -14), (18, 0), (-6, -14)][ph]
            feet2 = [(18, 0), (-6, -14), (-18, 0), (6, -14)][ph]
        else:
            feet = (-10, 0); feet2 = (12, 0)
        for fx, lift in (feet2, feet):  # back leg first
            dark = fx == feet2[0]
            c1 = (36, 30, 26) if not dark else (26, 22, 19)
            c2 = (18, 15, 12) if not dark else (14, 12, 10)
            im.alpha_composite(part(poly_fn([
                (cx + fx - 11, 158 + bob), (cx + fx + 11, 158 + bob),
                (cx + fx + 9, 226 + lift), (cx + fx - 9, 226 + lift)]),
                (cx - 30, 150, cx + 30, 240), c1, c2))
            # boot
            im.alpha_composite(part(rrect_fn(
                (cx + fx - 10, 218 + lift, cx + fx + 14, 236 + lift), 5),
                (cx - 30, 210, cx + 30, 240), (30, 24, 20), (14, 11, 9)))
    # ---- cloak (behind torso, flares) ----
    sway = [0, 5, 0, -5][ph] if mode == "walk" else 0
    if mode == "attack1":
        sway = -12
    flare = 16 if mode in ("attack0", "attack1") else 0
    cloak_pts = [(cx - 34, 92 + bob), (cx + 40, 92 + bob),
                 (cx + 52 + sway + flare, 220), (cx - 52 + sway - flare * 0.4, 220)]
    cloak_mask = poly_fn(cloak_pts)
    im.alpha_composite(part(cloak_mask, (cx - 70, 85, cx + 70, 225), CLOAK_T, CLOAK_B))
    rim_light(im, cloak_mask, "right", INFECT, 50, 5)
    # cloak folds
    fold_lines(d, cx + 6 + sway * 0.5, 110 + bob, 214, 4, 20, CLOAK_DK + (255,), 4)
    # tattered hem
    for i, hx in enumerate(range(int(cx - 48 + sway), int(cx + 50 + sway), 18)):
        hh = 220 + (i % 3) * 5
        d.polygon([(hx, 214), (hx + 9, 214), (hx + 5, hh)], fill=CLOAK_DK + (255,))
    # ---- torso / chest strap ----
    im.alpha_composite(part(rrect_fn((cx - 30, 96 + bob, cx + 34, 162 + bob), 12),
                            (cx - 34, 92, cx + 38, 166), (40, 46, 62), (22, 26, 36)))
    d.line([(cx - 28, 118 + bob), (cx + 32, 132 + bob)], fill=LEATHER_B + (255,), width=10)
    d.line([(cx - 28, 118 + bob), (cx + 32, 132 + bob)], fill=LEATHER_T + (255,), width=5)
    d.ellipse([cx - 4, 120 + bob, cx + 8, 132 + bob], fill=(120, 130, 150, 255))  # buckle
    # pauldron (right shoulder)
    im.alpha_composite(part(ellipse_fn(cx + 24, 100 + bob, 20, 15),
                            (cx, 80, cx + 48, 120), (70, 76, 92), (34, 38, 50)))
    d.arc([cx + 8, 88 + bob, cx + 40, 112 + bob], 200, 340, fill=STEEL_EDGE + (255,), width=2)
    # ---- head / hood ----
    hy = 58 + bob + (-6 if mode == "hurt" else 0)
    hood_mask = ellipse_fn(cx + 6, hy, 37, 40)
    im.alpha_composite(part(hood_mask, (cx - 34, hy - 42, cx + 46, hy + 42), HOOD_T, HOOD_B))
    rim_light(im, hood_mask, "right", INFECT, 60, 5)
    # face shadow (profile facing right)
    d.ellipse([cx - 6, hy - 20, cx + 30, hy + 22], fill=(16, 18, 24, 255))
    # glowing eye
    ex, ey = cx + 14, hy - 2
    add_glow(im, ex, ey, 12, INFECT, 130)
    d.ellipse([ex - 5, ey - 4, ex + 5, ey + 4], fill=EYE_CORE + (255,))
    d.ellipse([ex - 2, ey - 2, ex + 2, ey + 2], fill=INFECT + (255,))
    # hood folds + peak
    d.arc([cx - 28, hy - 38, cx + 38, hy + 26], 300, 60, fill=CLOAK_DK + (255,), width=5)
    # ---- arm + blade ----
    if mode == "attack0":      # windup: blade raised back
        hx, hyy = cx + 44, 40 + bob
        d.line([(cx + 20, 108 + bob), (hx, hyy)], fill=(44, 50, 66, 255), width=16)
        draw_blade(im, hx, hyy, hx + 34, hyy - 44, 9)
    elif mode == "attack1":    # slash: blade swept forward + arc trail
        hx, hyy = cx + 52, 108 + bob
        d.line([(cx + 20, 108 + bob), (hx, hyy)], fill=(44, 50, 66, 255), width=16)
        draw_blade(im, hx, hyy, hx + 58, hyy - 6, 9)
        add_glow(im, cx + 70, hyy - 10, 40, INFECT, 90)
        d.arc([cx - 10, hyy - 58, cx + 130, hyy + 42], 290, 30,
              fill=INFECT + (200,), width=7)
    elif mode == "attack2":    # recover: blade low forward
        hx, hyy = cx + 46, 140 + bob
        d.line([(cx + 20, 108 + bob), (hx, hyy)], fill=(44, 50, 66, 255), width=16)
        draw_blade(im, hx, hyy, hx + 44, hyy + 18, 9)
    else:
        hx, hyy = cx + 26, 152 + bob
        d.line([(cx + 20, 108 + bob), (hx, hyy)], fill=(40, 46, 60, 255), width=15)
        d.ellipse([hx - 8, hyy - 8, hx + 8, hyy + 8], fill=(52, 40, 30, 255))  # glove
        draw_blade(im, hx, hyy, hx + 10, hyy + 52, 8)
    # left arm (behind, darker)
    d.line([(cx - 16, 108 + bob), (cx - 26, 148 + bob)], fill=(30, 34, 46, 255), width=13)
    if mode in ("death0",):
        # kneeling handled by lowering whole body: redraw simpler
        pass
    return im

def draw_player_down(im, ph, mode="idle"):
    """Facing viewer."""
    d = ImageDraw.Draw(im)
    cx = 96
    bob = [0, -4, 0, -4][ph] if mode == "walk" else 0
    if mode == "walk":
        feet = [(-20, 0), (-8, -14), (20, 0), (8, -14)][ph]
        feet2 = [(20, 0), (8, -14), (-20, 0), (-8, -14)][ph]
    else:
        feet, feet2 = (-12, 0), (12, 0)
    for fx, lift in (feet2, feet):
        im.alpha_composite(part(poly_fn([
            (cx + fx - 11, 158 + bob), (cx + fx + 11, 158 + bob),
            (cx + fx + 9, 226 + lift), (cx + fx - 9, 226 + lift)]),
            (cx - 40, 150, cx + 40, 240), (36, 30, 26), (16, 13, 11)))
        im.alpha_composite(part(rrect_fn(
            (cx + fx - 11, 218 + lift, cx + fx + 11, 236 + lift), 5),
            (cx - 40, 210, cx + 40, 240), (30, 24, 20), (14, 11, 9)))
    sway = [0, 4, 0, -4][ph] if mode == "walk" else 0
    cloak_pts = [(cx - 36, 92 + bob), (cx + 36, 92 + bob),
                 (cx + 52 + sway, 220), (cx - 52 + sway, 220)]
    cloak_mask = poly_fn(cloak_pts)
    im.alpha_composite(part(cloak_mask, (cx - 56, 85, cx + 56, 225), CLOAK_T, CLOAK_B))
    fold_lines(d, cx + sway * 0.5, 112 + bob, 212, 5, 20, CLOAK_DK + (255,), 4)
    for i, hx in enumerate(range(cx - 48, cx + 50, 18)):
        hh = 220 + (i % 3) * 5
        d.polygon([(hx, 214), (hx + 9, 214), (hx + 5, hh)], fill=CLOAK_DK + (255,))
    # chest clasp + straps
    d.line([(cx - 30, 116 + bob), (cx + 30, 116 + bob)], fill=LEATHER_B + (255,), width=9)
    d.ellipse([cx - 9, 108 + bob, cx + 9, 126 + bob], fill=(120, 130, 150, 255))
    d.ellipse([cx - 5, 112 + bob, cx + 5, 122 + bob], fill=INFECT_DIM + (255,))
    # hood + face
    hy = 56 + bob
    hood_mask = ellipse_fn(cx, hy, 38, 41)
    im.alpha_composite(part(hood_mask, (cx - 40, hy - 43, cx + 40, hy + 43), HOOD_T, HOOD_B))
    rim_light(im, hood_mask, "top", INFECT, 45, 4)
    d.ellipse([cx - 24, hy - 22, cx + 24, hy + 24], fill=(15, 17, 23, 255))
    for ex in (cx - 11, cx + 11):
        add_glow(im, ex, hy - 2, 13, INFECT, 140)
        d.ellipse([ex - 6, hy - 6, ex + 6, hy + 2], fill=EYE_CORE + (255,))
        d.ellipse([ex - 2, hy - 4, ex + 2, hy], fill=INFECT + (255,))
    d.arc([cx - 30, hy - 36, cx + 30, hy + 28], 300, 60, fill=CLOAK_DK + (255,), width=5)
    # arms at sides, blade in right hand
    for sgn, col in ((-1, (30, 34, 46)), (1, (42, 48, 64))):
        d.line([(cx + sgn * 30, 106 + bob), (cx + sgn * 36, 150 + bob)],
               fill=col + (255,), width=15)
        d.ellipse([cx + sgn * 36 - 8, 142 + bob, cx + sgn * 36 + 8, 158 + bob],
                  fill=(52, 40, 30, 255))
    draw_blade(im, cx + 36, 152 + bob, cx + 44, 206 + bob, 8)
    return im

def draw_player_up(im, ph, mode="idle"):
    """Back view."""
    d = ImageDraw.Draw(im)
    cx = 96
    bob = [0, -4, 0, -4][ph] if mode == "walk" else 0
    if mode == "walk":
        feet = [(-20, 0), (-8, -14), (20, 0), (8, -14)][ph]
        feet2 = [(20, 0), (8, -14), (-20, 0), (-8, -14)][ph]
    else:
        feet, feet2 = (-12, 0), (12, 0)
    for fx, lift in (feet2, feet):
        im.alpha_composite(part(poly_fn([
            (cx + fx - 11, 158 + bob), (cx + fx + 11, 158 + bob),
            (cx + fx + 9, 226 + lift), (cx + fx - 9, 226 + lift)]),
            (cx - 40, 150, cx + 40, 240), (30, 26, 22), (14, 12, 10)))
    sway = [0, 4, 0, -4][ph] if mode == "walk" else 0
    cloak_pts = [(cx - 38, 92 + bob), (cx + 38, 92 + bob),
                 (cx + 54 + sway, 222), (cx - 54 + sway, 222)]
    cloak_mask = poly_fn(cloak_pts)
    im.alpha_composite(part(cloak_mask, (cx - 58, 85, cx + 58, 227), CLOAK_T, CLOAK_B))
    rim_light(im, cloak_mask, "right", INFECT, 50, 5)
    fold_lines(d, cx + sway * 0.5, 120 + bob, 214, 5, 21, CLOAK_DK + (255,), 4)
    # sheathed blade diagonal on back
    draw_blade(im, cx - 26, 190 + bob, cx + 30, 96 + bob, 8)
    d.line([(cx - 28, 130 + bob), (cx + 28, 170 + bob)], fill=LEATHER_B + (255,), width=8)
    # back of hood (no face)
    hy = 56 + bob
    hood_mask = ellipse_fn(cx, hy, 38, 41)
    im.alpha_composite(part(hood_mask, (cx - 40, hy - 43, cx + 40, hy + 43), HOOD_T, HOOD_B))
    rim_light(im, hood_mask, "top", INFECT, 45, 4)
    d.arc([cx - 24, hy - 30, cx + 24, hy + 18], 200, 340, fill=CLOAK_DK + (255,), width=5)
    fold_lines(d, cx, hy - 34, hy + 30, 3, 14, CLOAK_DK + (200,), 3)
    return im

def draw_player_death(im, stage):
    d = ImageDraw.Draw(im)
    cx = 96
    if stage == 0:
        # kneeling, head bowed, blade dropped
        im.alpha_composite(part(poly_fn([
            (cx - 40, 130), (cx + 40, 130), (cx + 56, 236), (cx - 56, 236)]),
            (cx - 60, 125, cx + 60, 240), (30, 36, 50), (12, 14, 20)))
        hood_mask = ellipse_fn(cx + 8, 108, 34, 36)
        im.alpha_composite(part(hood_mask, (cx - 30, 70, cx + 46, 146), HOOD_T, CLOAK_B))
        d.ellipse([cx - 8, 96, cx + 28, 130], fill=(14, 16, 22, 255))
        draw_blade(im, cx + 66, 200, cx + 104, 226, 8)
        add_glow(im, cx + 4, 106, 10, INFECT, 60)  # fading eyes
    else:
        # collapsed mound
        mound = poly_fn([(cx - 70, 236), (cx - 52, 180), (cx + 30, 172),
                         (cx + 70, 236)])
        im.alpha_composite(part(mound, (cx - 74, 168, cx + 74, 240),
                                (26, 32, 46), (10, 12, 18)))
        hood_mask = ellipse_fn(cx + 52, 208, 26, 24)
        im.alpha_composite(part(hood_mask, (cx + 24, 182, cx + 80, 234), HOOD_T, CLOAK_B))
        fold_lines(d, cx - 10, 190, 232, 4, 22, CLOAK_DK + (255,), 4)
        draw_blade(im, cx - 80, 220, cx - 44, 238, 8)
    return im

# ================= SHAMBLER =================
SH_T, SH_B = (122, 138, 92), (58, 68, 44)      # sickly skin
SH_CLOTH_T, SH_CLOTH_B = (74, 62, 52), (36, 30, 25)

def shambler_cracks(d, pts_list):
    for pts in pts_list:
        d.line(pts, fill=INFECT + (255,), width=3)
        d.line(pts, fill=EYE_CORE + (255,), width=1)

def draw_shambler(im, ph, mode="walk"):
    d = ImageDraw.Draw(im)
    cx = 96
    sway = [0, 6, 0, -6][ph] if mode == "walk" else 0
    bob = [0, -3, 0, -3][ph] if mode == "walk" else 0
    hunch = 8
    # ---- legs (tattered pants) ----
    if mode == "walk":
        feet = [(-16, 0), (4, -10), (16, 0), (-4, -10)][ph]
        feet2 = [(16, 0), (-4, -10), (-16, 0), (4, -10)][ph]
    else:
        feet, feet2 = (-10, 0), (10, 0)
    for fx, lift in (feet2, feet):
        im.alpha_composite(part(poly_fn([
            (cx + fx - 12, 158), (cx + fx + 12, 158),
            (cx + fx + 9, 228 + lift), (cx + fx - 9, 228 + lift)]),
            (cx - 34, 150, cx + 34, 240), SH_CLOTH_T, SH_CLOTH_B))
    # ---- torso (hunched, shirt) ----
    torso_pts = [(cx - 30 + sway, 100 + hunch + bob), (cx + 26 + sway, 104 + hunch + bob),
                 (cx + 20 + sway, 168), (cx - 34 + sway, 164)]
    torso_mask = poly_fn(torso_pts)
    im.alpha_composite(part(torso_mask, (cx - 38, 95, cx + 32, 172), SH_CLOTH_T, SH_CLOTH_B))
    # torn shirt hem
    for i, hx in enumerate(range(cx - 32, cx + 22, 14)):
        d.polygon([(hx + sway, 158), (hx + 8 + sway, 158), (hx + 4 + sway, 170 + (i % 2) * 6)],
                  fill=SH_CLOTH_B + (255,))
    # exposed skin + glowing cracks on torso
    d.ellipse([cx - 12 + sway, 108 + hunch + bob, cx + 14 + sway, 140 + hunch + bob],
              fill=SH_B + (255,))
    shambler_cracks(d, [[(cx - 8 + sway, 112 + hunch + bob), (cx + 2 + sway, 128 + hunch + bob),
                         (cx - 4 + sway, 140 + hunch + bob)]])
    # ---- head (lolling forward, facing right) ----
    hx, hy = cx + 30 + sway, 78 + hunch + bob
    head_mask = ellipse_fn(hx, hy, 27, 29)
    im.alpha_composite(part(head_mask, (hx - 29, hy - 31, hx + 29, hy + 31), SH_T, SH_B))
    rim_light(im, head_mask, "right", INFECT, 55, 4)
    # sunken glowing eyes
    for ex, ey in ((hx + 8, hy - 6), (hx + 18, hy - 2)):
        d.ellipse([ex - 7, ey - 5, ex + 7, ey + 5], fill=(30, 36, 24, 255))
        add_glow(im, ex, ey, 9, INFECT, 120)
        d.ellipse([ex - 3, ey - 3, ex + 3, ey + 3], fill=INFECT + (255,))
    # slack jaw
    d.ellipse([hx + 6, hy + 10, hx + 26, hy + 26], fill=(28, 30, 22, 255))
    # cracks on head
    shambler_cracks(d, [[(hx - 14, hy - 18), (hx - 6, hy - 6), (hx - 12, hy + 4)]])
    # ---- arms (long, clawed) ----
    if mode == "attack0":
        arm_targets = [(cx + 44, 40), (cx + 20, 36)]   # raised
    elif mode == "attack1":
        arm_targets = [(cx + 66, 130), (cx + 52, 118)]  # swiped forward
    else:
        sw = [0, 10, 0, -10][ph] if mode == "walk" else 0
        arm_targets = [(cx + 34 + sw, 168), (cx + 22 - sw, 162)]
    for i, (tx, ty) in enumerate(arm_targets):
        col = (SH_T if i == 0 else shade(SH_T, 0.85))
        d.line([(cx + 6 + sway, 116 + hunch + bob), (tx, ty)], fill=col + (255,), width=17)
        d.line([(cx + 6 + sway, 116 + hunch + bob), (tx, ty)], fill=shade(col, 1.15) + (255,), width=8)
        # claws
        for c in range(3):
            a = math.radians(200 + c * 25)
            d.line([(tx, ty), (tx + math.cos(a) * 14, ty + math.sin(a) * 14)],
                   fill=(210, 215, 200, 255), width=3)
    if mode == "attack1":
        add_glow(im, cx + 70, 128, 34, INFECT, 80)
        for k in range(3):
            d.arc([cx + 10, 84 + k * 14, cx + 110, 164 + k * 14], 300, 20,
                  fill=INFECT + (170,), width=4)
    return im

def draw_shambler_death(im, stage):
    d = ImageDraw.Draw(im)
    cx = 96
    if stage == 0:
        im.alpha_composite(part(poly_fn([
            (cx - 44, 150), (cx + 40, 150), (cx + 52, 236), (cx - 52, 236)]),
            (cx - 56, 145, cx + 56, 240), SH_CLOTH_T, (30, 34, 24)))
        hm = ellipse_fn(cx + 20, 128, 26, 27)
        im.alpha_composite(part(hm, (cx - 8, 99, cx + 48, 157), SH_T, SH_B))
    else:
        mound = poly_fn([(cx - 64, 236), (cx - 40, 196), (cx + 44, 192), (cx + 64, 236)])
        im.alpha_composite(part(mound, (cx - 68, 188, cx + 68, 240), SH_CLOTH_T, (28, 32, 22)))
        hm = ellipse_fn(cx + 44, 210, 24, 22)
        im.alpha_composite(part(hm, (cx + 18, 186, cx + 70, 234), SH_T, SH_B))
        shambler_cracks(d, [[(cx - 30, 206), (cx - 10, 218), (cx - 22, 230)]])
    return im

# ================= RUNNER =================
RN_T, RN_B = (146, 88, 66), (70, 40, 30)      # lean reddish muscle
RN_DK = (46, 26, 20)

def draw_runner(im, ph, mode="walk"):
    d = ImageDraw.Draw(im)
    cx = 96
    lean = 14 if mode == "walk" else (20 if mode == "attack1" else 6)
    bob = [0, -6, 0, -6][ph] if mode == "walk" else 0
    cx += lean
    # ---- digitigrade legs ----
    if mode == "walk":
        legdefs = [[(-26, 0), (20, -18)], [(-6, -20), (26, 0)],
                   [(20, 0), (-26, -18)], [(26, -18), (-6, -20)]][ph]
    else:
        legdefs = [(-14, 0), (14, 0)]
    for i, leg in enumerate(legdefs):
        fx, lift = leg
        c1 = RN_DK if i == 1 else RN_T
        # thigh
        d.line([(cx, 150 + bob), (cx + fx * 0.6, 190 + lift * 0.5 + bob)],
               fill=c1 + (255,), width=20)
        # shin back down
        d.line([(cx + fx * 0.6, 190 + lift * 0.5 + bob), (cx + fx, 232 + lift + bob)],
               fill=shade(c1, 0.8) + (255,), width=13)
        # clawed foot
        d.polygon([(cx + fx - 8, 228 + lift + bob), (cx + fx + 16, 228 + lift + bob),
                   (cx + fx + 10, 238 + lift + bob)], fill=(200, 205, 190, 255))
    # ---- torso (sprinter lean) ----
    torso_mask = poly_fn([(cx - 24, 96 + bob), (cx + 22, 92 + bob),
                          (cx + 14, 158 + bob), (cx - 28, 158 + bob)])
    im.alpha_composite(part(torso_mask, (cx - 28, 88, cx + 26, 162), RN_T, RN_B))
    # ab definition
    for i in range(3):
        y = 112 + i * 14 + bob
        d.line([(cx - 12, y), (cx + 10, y)], fill=RN_DK + (255,), width=3)
    # spine spikes
    for i, sx in enumerate(range(-16, 20, 10)):
        d.polygon([(cx + sx, 94 + bob), (cx + sx + 5, 94 + bob), (cx + sx + 2, 80 + bob - (i % 2) * 5)],
                  fill=(60, 64, 70, 255))
    rim_light(im, torso_mask, "right", INFECT, 55, 5)
    # ---- head (thrust forward, jaw open) ----
    hx, hy = cx + 26, 66 + bob
    head_mask = ellipse_fn(hx, hy, 24, 22)
    im.alpha_composite(part(head_mask, (hx - 26, hy - 24, hx + 26, hy + 24), RN_T, RN_B))
    # open jaw with teeth
    d.polygon([(hx + 2, hy + 8), (hx + 30, hy + 4), (hx + 26, hy + 22), (hx + 4, hy + 24)],
              fill=(30, 18, 16, 255))
    for t in range(4):
        tx = hx + 8 + t * 6
        d.polygon([(tx, hy + 9), (tx + 3, hy + 9), (tx + 1.5, hy + 15)], fill=(220, 225, 210, 255))
    # eyes
    ex, ey = hx + 6, hy - 8
    add_glow(im, ex, ey, 10, (255, 210, 80), 120)
    d.ellipse([ex - 4, ey - 3, ex + 4, ey + 3], fill=(255, 230, 150, 255))
    # ---- arms pumping ----
    if mode == "walk":
        arms = [(30, 150), (-24, 120)] if ph % 2 == 0 else [(-24, 120), (30, 150)]
    elif mode == "attack0":
        arms = [(-10, 90), (-16, 84)]
    elif mode == "attack1":
        arms = [(52, 110), (48, 104)]
    else:
        arms = [(16, 148), (-14, 132)]
    for tx, ty in arms:
        d.line([(cx + 2, 108 + bob), (cx + tx, ty + bob)], fill=RN_T + (255,), width=15)
        for c in range(3):
            a = math.radians(160 + c * 22)
            d.line([(cx + tx, ty + bob),
                    (cx + tx + math.cos(a) * 13, ty + bob + math.sin(a) * 13)],
                   fill=(210, 215, 200, 255), width=3)
    if mode == "attack1":
        add_glow(im, cx + 52, 110, 30, INFECT, 70)
    return im

def draw_runner_death(im, stage):
    d = ImageDraw.Draw(im)
    cx = 96
    if stage == 0:
        im.alpha_composite(part(poly_fn([
            (cx - 40, 160), (cx + 36, 150), (cx + 48, 236), (cx - 44, 236)]),
            (cx - 48, 145, cx + 52, 240), RN_T, RN_DK))
        hm = ellipse_fn(cx + 30, 132, 22, 20)
        im.alpha_composite(part(hm, (cx + 6, 110, cx + 54, 154), RN_T, RN_B))
    else:
        im.alpha_composite(part(poly_fn([
            (cx - 66, 236), (cx - 30, 204), (cx + 50, 206), (cx + 66, 236)]),
            (cx - 70, 200, cx + 70, 240), RN_B, RN_DK))
        d.line([(cx - 40, 214), (cx + 40, 220)], fill=INFECT_DIM + (255,), width=4)
    return im

# ================= BRUTE =================
BR_T, BR_B = (104, 98, 88), (48, 44, 38)      # thick hide
BR_PLATE_T, BR_PLATE_B = (88, 94, 108), (40, 44, 54)

def draw_brute(im, ph, mode="walk"):
    d = ImageDraw.Draw(im)
    cx = 96
    rock = [0, 4, 0, -4][ph] if mode == "walk" else 0
    bob = [0, -3, 0, -3][ph] if mode == "walk" else 0
    # ---- tree-trunk legs ----
    if mode == "walk":
        feet = [(-18, 0), (14, -8)][ph % 2]
        feet2 = [(18, 0), (-14, -8)][(ph + 1) % 2]
    else:
        feet, feet2 = (-16, 0), (16, 0)
    for fx, lift in (feet2, feet):
        im.alpha_composite(part(poly_fn([
            (cx + fx - 16, 156), (cx + fx + 16, 156),
            (cx + fx + 13, 230 + lift), (cx + fx - 13, 230 + lift)]),
            (cx - 40, 150, cx + 40, 242), BR_T, BR_B))
        im.alpha_composite(part(rrect_fn(
            (cx + fx - 15, 222 + lift, cx + fx + 15, 240 + lift), 6),
            (cx - 40, 216, cx + 40, 244), (36, 32, 28), (18, 16, 14)))
    # ---- massive torso ----
    torso_pts = [(cx - 44 + rock, 84 + bob), (cx + 44 + rock, 84 + bob),
                 (cx + 38 + rock, 170), (cx - 38 + rock, 170)]
    torso_mask = poly_fn(torso_pts)
    im.alpha_composite(part(torso_mask, (cx - 48, 80, cx + 48, 174), BR_T, BR_B))
    rim_light(im, torso_mask, "right", INFECT, 60, 6)
    # glowing cracks across torso
    for cr in [[(cx - 30 + rock, 100 + bob), (cx - 10 + rock, 120 + bob), (cx - 24 + rock, 145 + bob)],
               [(cx + 28 + rock, 96 + bob), (cx + 12 + rock, 130 + bob)]]:
        d.line(cr, fill=INFECT + (255,), width=4)
        d.line(cr, fill=EYE_CORE + (255,), width=2)
        for px, py in cr:
            add_glow(im, px, py, 12, INFECT, 70)
    # ---- armor plates: shoulders + back ----
    for sgn in (-1, 1):
        px = cx + sgn * 40 + rock
        plate = poly_fn([(px - 26, 78 + bob), (px + 26, 78 + bob),
                         (px + 18, 116 + bob), (px - 18, 116 + bob)])
        im.alpha_composite(part(plate, (px - 30, 74, px + 30, 120), BR_PLATE_T, BR_PLATE_B))
        d.line([(px - 20, 86 + bob), (px + 20, 86 + bob)], fill=STEEL_EDGE + (255,), width=2)
        for r in range(3):  # rivets
            d.ellipse([px - 12 + r * 12 - 3, 98 + bob, px - 12 + r * 12 + 3, 104 + bob],
                      fill=(150, 158, 172, 255))
    # ---- small head, heavy brow ----
    hx, hy = cx + 10 + rock, 52 + bob
    head_mask = ellipse_fn(hx, hy, 22, 24)
    im.alpha_composite(part(head_mask, (hx - 24, hy - 26, hx + 24, hy + 26), BR_T, BR_B))
    d.rectangle([hx - 18, hy - 14, hx + 20, hy - 4], fill=(34, 30, 26, 255))  # brow
    for ex in (hx + 2, hx + 12):
        add_glow(im, ex, hy - 2, 9, INFECT, 130)
        d.ellipse([ex - 3, hy - 5, ex + 3, hy + 1], fill=INFECT + (255,))
    d.line([(hx - 2, hy + 12), (hx + 18, hy + 12)], fill=(26, 22, 20, 255), width=4)  # grim mouth
    # ---- huge arms ----
    if mode == "attack0":
        arm_l = (cx - 52 + rock, 20 + bob); arm_r = (cx + 56 + rock, 24 + bob)
    elif mode == "attack1":
        arm_l = (cx - 40 + rock, 190); arm_r = (cx + 60 + rock, 190)
    else:
        sw = [0, 8, 0, -8][ph] if mode == "walk" else 0
        arm_l = (cx - 56 + rock, 150 + sw); arm_r = (cx + 60 + rock, 150 - sw)
    for ax, ay in (arm_l, arm_r):
        sx = cx - 40 + rock if (ax, ay) == arm_l else cx + 40 + rock
        d.line([(sx, 100 + bob), (ax, ay)], fill=BR_T + (255,), width=30)
        d.line([(sx, 100 + bob), (ax, ay)], fill=shade(BR_T, 1.12) + (255,), width=16)
        # fist
        fist = ellipse_fn(ax, ay, 20, 17)
        im.alpha_composite(part(fist, (ax - 22, ay - 19, ax + 22, ay + 19),
                                shade(BR_T, 1.1), BR_B))
    if mode == "attack1":
        # shockwave ring
        for r, a in ((70, 90), (95, 55), (120, 28)):
            d.ellipse([cx + 10 - r, 200 - r * 0.4, cx + 10 + r, 200 + r * 0.4],
                      outline=INFECT + (a,), width=5)
        add_glow(im, cx + 10, 200, 60, INFECT, 80)
    return im

def draw_brute_death(im, stage):
    d = ImageDraw.Draw(im)
    cx = 96
    if stage == 0:
        # kneeling
        im.alpha_composite(part(poly_fn([
            (cx - 48, 130), (cx + 48, 130), (cx + 54, 236), (cx - 54, 236)]),
            (cx - 58, 125, cx + 58, 240), BR_T, (34, 30, 26)))
        hm = ellipse_fn(cx + 6, 104, 22, 23)
        im.alpha_composite(part(hm, (cx - 18, 79, cx + 30, 129), BR_T, BR_B))
    else:
        # toppled
        im.alpha_composite(part(poly_fn([
            (cx - 80, 236), (cx - 60, 190), (cx + 70, 196), (cx + 80, 236)]),
            (cx - 84, 186, cx + 84, 240), BR_B, (30, 27, 24)))
        hm = ellipse_fn(cx + 58, 214, 22, 20)
        im.alpha_composite(part(hm, (cx + 34, 192, cx + 82, 236), BR_T, BR_B))
    return im

# ================= GENERATE =================
def breathe(im, dy=2):
    out = new()
    out.alpha_composite(im, (0, dy))
    return out

def gen():
    n = 0
    # ---- player ----
    for dname, fn in (("down", draw_player_down), ("up", draw_player_up), ("side", draw_player_side)):
        for v in (0, 1):
            im = new(); fn(im, 0, "idle"); save(breathe(im, 2 * v), f"p_{dname}_idle_{v}.png"); n += 1
        for ph in range(4):
            im = new(); fn(im, ph, "walk"); save(im, f"p_{dname}_walk_{ph}.png"); n += 1
    for i, m in enumerate(("attack0", "attack1", "attack2")):
        im = new(); draw_player_side(im, 0, m); save(im, f"p_side_attack_{i}.png"); n += 1
    im = new(); draw_player_side(im, 0, "hurt"); save(im, "p_hurt.png"); n += 1
    for s in (0, 1):
        im = new(); draw_player_death(im, s); save(im, f"p_death_{s}.png"); n += 1
    # ---- infected ----
    for tname, wfn, dfn in (("shambler", draw_shambler, draw_shambler_death),
                            ("runner", draw_runner, draw_runner_death),
                            ("brute", draw_brute, draw_brute_death)):
        for ph in range(4):
            im = new(); wfn(im, ph, "walk"); save(im, f"e_{tname}_walk_{ph}.png"); n += 1
        for i, m in enumerate(("attack0", "attack1")):
            im = new(); wfn(im, 0, m); save(im, f"e_{tname}_attack_{i}.png"); n += 1
        for s in (0, 1):
            im = new(); dfn(im, s); save(im, f"e_{tname}_death_{s}.png"); n += 1
    print(f"generated {n} HD frames")

if __name__ == "__main__":
    gen()
