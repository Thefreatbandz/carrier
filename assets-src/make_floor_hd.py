#!/usr/bin/env python3
"""CARRIER HD floor tiles. 240x240, scaled to 120 in-game. Fine stone detail."""
from PIL import Image, ImageDraw, ImageFilter
import os, random, math

OUT = os.path.join(os.path.dirname(__file__), "..", "assets")
S = 240

def save(im, name):
    im.save(os.path.join(OUT, name))

def stone_base(seed, tint=(96, 94, 100)):
    rnd = random.Random(seed)
    im = Image.new("RGB", (S, S))
    d = ImageDraw.Draw(im)
    # large soft mottling (subtle, heavily blurred)
    mottle = Image.new("RGB", (S, S), tint)
    md = ImageDraw.Draw(mottle)
    for _ in range(30):
        x, y = rnd.randint(0, S), rnd.randint(0, S)
        r = rnd.randint(30, 85)
        v = rnd.randint(-10, 10)
        c = tuple(max(0, min(255, tint[i] + v)) for i in range(3))
        md.ellipse([x - r, y - r, x + r, y + r], fill=c)
    mottle = mottle.filter(ImageFilter.GaussianBlur(6))
    im = Image.blend(im, mottle, 0.55)
    # fine grain
    for _ in range(900):
        x, y = rnd.randint(0, S - 1), rnd.randint(0, S - 1)
        v = rnd.randint(-22, 22)
        c = tuple(max(0, min(255, tint[i] + v)) for i in range(3))
        d.point((x, y), fill=c)
    # speckles
    for _ in range(60):
        x, y = rnd.randint(0, S), rnd.randint(0, S)
        r = rnd.randint(1, 3)
        v = rnd.choice([-34, 30])
        c = tuple(max(0, min(255, tint[i] + v)) for i in range(3))
        d.ellipse([x - r, y - r, x + r, y + r], fill=c)
    im = im.filter(ImageFilter.GaussianBlur(0.7))
    return im, ImageDraw.Draw(im)

def bevel(d):
    # inner edge highlight top-left, shadow bottom-right
    d.rectangle([2, 2, S - 3, 6], fill=(150, 148, 155))
    d.rectangle([2, 2, 6, S - 3], fill=(140, 138, 145))
    d.rectangle([2, S - 7, S - 3, S - 3], fill=(52, 50, 56))
    d.rectangle([S - 7, 2, S - 3, S - 3], fill=(58, 56, 62))
    d.rectangle([0, 0, S - 1, S - 1], outline=(28, 27, 32), width=3)

def crack(d, rnd, x0, y0, segs=9):
    x, y = x0, y0
    pts = [(x, y)]
    ang = rnd.uniform(0, math.pi * 2)
    for _ in range(segs):
        ang += rnd.uniform(-0.7, 0.7)
        L = rnd.randint(10, 26)
        x += math.cos(ang) * L
        y += math.sin(ang) * L
        pts.append((x, y))
    # depth shadow then dark core then faint highlight
    d.line(pts, fill=(40, 38, 44), width=7)
    d.line(pts, fill=(22, 21, 26), width=4)
    off = [(x + 3, y + 3) for x, y in pts]
    d.line(off, fill=(130, 128, 135), width=1)

def grime_patch(im, d, rnd, n=7):
    for _ in range(n):
        x, y = rnd.randint(20, S - 20), rnd.randint(20, S - 20)
        r = rnd.randint(18, 46)
        for rr in range(r, 0, -4):
            a = int(70 * (1 - rr / r))
            d.ellipse([x - rr, y - rr, x + rr, y + rr],
                      fill=(30, 28, 26, a))
    # a few dark drips
    for _ in range(4):
        x = rnd.randint(10, S - 10)
        d.line([(x, rnd.randint(0, 60)), (x + rnd.randint(-8, 8), rnd.randint(120, S))],
               fill=(34, 32, 30, 90), width=rnd.randint(3, 7))

def moss_patch(d, rnd, n=6):
    for _ in range(n):
        x, y = rnd.randint(24, S - 24), rnd.randint(24, S - 24)
        r = rnd.randint(16, 34)
        # base
        d.ellipse([x - r, y - r, x + r, y + r], fill=(34, 74, 36))
        # fronds
        for _ in range(40):
            a = rnd.uniform(0, math.pi * 2)
            rr = rnd.uniform(r * 0.2, r)
            fx, fy = x + math.cos(a) * rr, y + math.sin(a) * rr
            g = rnd.randint(70, 130)
            d.line([(fx, fy), (fx + rnd.randint(-4, 4), fy - rnd.randint(2, 7))],
                   fill=(36, g, 40), width=2)
        # infection glow flecks
        for _ in range(6):
            fx = x + rnd.randint(-r, r)
            fy = y + rnd.randint(-r, r)
            d.ellipse([fx - 2, fy - 2, fx + 2, fy + 2], fill=(57, 255, 112))

def make_tiles():
    # base
    im, d = stone_base(11)
    bevel(d)
    save(im, "floor_a.png")
    # crack
    im, d = stone_base(23)
    rnd = random.Random(23)
    crack(d, rnd, 30, 20)
    crack(d, rnd, 200, 210)
    bevel(d)
    save(im, "floor_crack.png")
    # grime
    im, d = stone_base(37)
    rnd = random.Random(37)
    ov = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    grime_patch(ov, ImageDraw.Draw(ov), rnd)
    im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
    d = ImageDraw.Draw(im)
    bevel(d)
    save(im, "floor_grime.png")
    # moss
    im, d = stone_base(51, tint=(88, 92, 88))
    rnd = random.Random(51)
    moss_patch(d, rnd)
    bevel(d)
    save(im, "floor_moss.png")
    print("HD floor tiles done")

if __name__ == "__main__":
    make_tiles()
