#!/usr/bin/env python3
"""CARRIER HD items: sword pickup (160x160), chests (192x144)."""
from PIL import Image, ImageDraw, ImageFilter
import os, math, random

OUT = os.path.join(os.path.dirname(__file__), "..", "assets")
INFECT = (57, 255, 112)

def save(im, name):
    im.save(os.path.join(OUT, name))

def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c[:3])

def make_sword():
    S = 160
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rnd = random.Random(5)
    cx = S // 2
    # shadow
    d.ellipse([cx - 40, 128, cx + 40, 148], fill=(0, 0, 0, 90))
    # blade: diagonal from lower-left hilt to upper-right tip
    bx, by, tx, ty = 62, 104, 128, 30
    # fuller + gradient: draw thick dark, then lighter core, then edge
    d.line([(bx, by), (tx, ty)], fill=(104, 112, 130, 255), width=17)
    d.line([(bx, by), (tx, ty)], fill=(160, 170, 188, 255), width=11)
    d.line([(bx, by), (tx, ty)], fill=(205, 214, 230, 255), width=5)
    # tip
    d.polygon([(tx, ty), (tx - 14, ty + 2), (tx - 4, ty + 14)], fill=(205, 214, 230, 255))
    # edge highlight
    mx, my = tx - bx, ty - by
    L = math.hypot(mx, my)
    nx, ny = -my / L * 3, mx / L * 3
    d.line([(bx + nx, by + ny), (tx + nx, ty + ny)], fill=(240, 246, 255, 255), width=2)
    # guard
    gx, gy = bx, by
    d.line([(gx - 22, gy + 10), (gx + 10, gy - 22)], fill=(88, 74, 52, 255), width=10)
    d.line([(gx - 22, gy + 10), (gx + 10, gy - 22)], fill=(140, 118, 84, 255), width=5)
    # grip
    d.line([(gx, gy), (gx - 20, gy + 20)], fill=(46, 34, 26, 255), width=12)
    for i in range(3):
        t = (i + 1) / 4
        wx, wy = gx + (gx - 20 - gx) * t, gy + (gy + 20 - gy) * t
        d.line([(wx - 6, wy - 6), (wx + 6, wy + 6)], fill=(90, 70, 50, 255), width=2)
    # pommel gem (infection)
    px, py = gx - 22, gy + 22
    d.ellipse([px - 8, py - 8, px + 8, py + 8], fill=(120, 100, 70, 255))
    d.ellipse([px - 5, py - 5, px + 5, py + 5], fill=INFECT + (255,))
    # glow on gem
    ov = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for r in range(20, 0, -4):
        od.ellipse([px - r, py - r, px + r, py + r], fill=INFECT + (int(50 * (1 - r / 22)),))
    im.alpha_composite(ov)
    # nicks on blade
    for _ in range(4):
        t = rnd.uniform(0.2, 0.8)
        nx2, ny2 = bx + mx * t, by + my * t
        d.line([(nx2 - 3, ny2 + 2), (nx2 + 3, ny2 - 2)], fill=(70, 76, 90, 255), width=2)
    save(im, "sword.png")
    print("HD sword done")

def make_chest(opened):
    W2, H2 = 192, 144
    im = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rnd = random.Random(9 if not opened else 10)
    # shadow
    d.ellipse([30, 118, 162, 138], fill=(0, 0, 0, 100))
    # body
    for y in range(52, 122):
        t = (y - 52) / 70
        v = int(96 + (58 - 96) * t)
        d.line([(28, y), (164, y)], fill=(v, int(v * 0.72), int(v * 0.5)))
    # wood planks
    for px in (62, 96, 130):
        d.line([(px, 54), (px, 120)], fill=(52, 38, 27, 255), width=2)
    # wood grain
    for _ in range(40):
        x, y = rnd.randint(32, 160), rnd.randint(56, 118)
        d.line([(x, y), (x + rnd.randint(6, 18), y)], fill=(70, 52, 36, 255), width=1)
    # metal bands
    for bx in (40, 152):
        d.rectangle([bx - 7, 50, bx + 7, 122], fill=(52, 56, 66))
        d.rectangle([bx - 7, 50, bx + 7, 122], outline=(150, 158, 172), width=2)
        for ry in (66, 106):
            d.ellipse([bx - 3, ry - 3, bx + 3, ry + 3], fill=(160, 168, 182))
    # lid
    if not opened:
        for y in range(18, 54):
            t = (y - 18) / 36
            v = int(110 + (70 - 110) * t)
            d.line([(24, y), (168, y)], fill=(v, int(v * 0.72), int(v * 0.5)))
        d.rectangle([22, 16, 170, 54], outline=(150, 158, 172), width=3)
        # lock plate
        d.rounded_rectangle([84, 40, 108, 66], radius=4, fill=(60, 64, 74))
        d.rounded_rectangle([84, 40, 108, 66], radius=4, outline=(160, 168, 182), width=2)
        d.ellipse([93, 48, 99, 54], fill=(20, 20, 24))
        d.rectangle([94, 52, 98, 60], fill=(20, 20, 24))
    else:
        # lid flipped open behind
        for y in range(2, 30):
            v = int(70 + y)
            d.line([(30, y), (162, y)], fill=(v, int(v * 0.7), int(v * 0.48)))
        d.rectangle([28, 0, 164, 32], outline=(150, 158, 172), width=3)
        # glowing contents
        for y in range(52, 70):
            d.line([(34, y), (158, y)], fill=(20, 40, 26))
        ov = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        for r in range(46, 0, -5):
            od.ellipse([96 - r, 62 - r * 0.6, 96 + r, 62 + r * 0.6],
                       fill=INFECT + (int(80 * (1 - r / 50)),))
        im.alpha_composite(ov)
        # gold bits
        for _ in range(8):
            x, y = rnd.randint(50, 142), rnd.randint(54, 66)
            d.ellipse([x - 3, y - 2, x + 3, y + 2], fill=(230, 200, 110, 255))
    # base trim
    d.rectangle([26, 112, 166, 124], outline=(40, 30, 22, 255), width=3)
    save(im, "chest_closed.png" if not opened else "chest_open.png")
    print("HD chest (%s) done" % ("closed" if not opened else "open"))

if __name__ == "__main__":
    make_sword()
    make_chest(False)
    make_chest(True)
