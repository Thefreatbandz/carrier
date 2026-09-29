#!/usr/bin/env python3
"""CARRIER HD wall block (240x240, scaled to 120 in game) and gate post (64x256 native)."""
from PIL import Image, ImageDraw, ImageFilter
import os, random, math

OUT = os.path.join(os.path.dirname(__file__), "..", "assets")
S = 240

def save(im, name):
    im.save(os.path.join(OUT, name))

def make_wall():
    rnd = random.Random(77)
    im = Image.new("RGB", (S, S), (64, 62, 70))
    d = ImageDraw.Draw(im)
    # courses of stone blocks: 3 rows
    rows = [(0, 78), (78, 160), (160, 240)]
    for ri, (y0, y1) in enumerate(rows):
        off = (ri % 2) * 60
        for bx in range(-60, S + 60, 120):
            x0, x1 = bx + off, bx + off + 116
            # block face with vertical gradient
            for y in range(y0 + 3, y1 - 3):
                t = (y - y0) / max(1, y1 - y0)
                c = tuple(int(96 + (58 - 96) * t + rnd.randint(-6, 6)) for _ in range(3))
                c = (c[0], c[1], c[2] + 6)
                d.line([(max(0, x0 + 3), y), (min(S, x1 - 3), y)], fill=c)
            # top bevel highlight, bottom shadow
            d.line([(x0 + 3, y0 + 4), (x1 - 3, y0 + 4)], fill=(150, 148, 156), width=3)
            d.line([(x0 + 3, y1 - 5), (x1 - 3, y1 - 5)], fill=(36, 34, 40), width=4)
            # side shading
            d.line([(x0 + 4, y0 + 4), (x0 + 4, y1 - 4)], fill=(120, 118, 126), width=2)
            # per-block mottling
            for _ in range(26):
                x, y = rnd.randint(int(x0), int(x1)), rnd.randint(y0, y1)
                r = rnd.randint(4, 16)
                v = rnd.randint(-12, 12)
                cc = (84 + v, 82 + v, 90 + v)
                d.ellipse([x - r, y - r, x + r, y + r], fill=cc)
    # mortar lines
    for y0, y1 in rows:
        d.line([(0, y0), (S, y0)], fill=(30, 28, 34), width=4)
    for ri, (y0, y1) in enumerate(rows):
        off = (ri % 2) * 60
        for bx in range(-60, S + 60, 120):
            d.line([(bx + off, y0), (bx + off, y1)], fill=(30, 28, 34), width=4)
    # cracks + moss in crevices
    for _ in range(3):
        x, y = rnd.randint(0, S), rnd.randint(0, S)
        pts = [(x, y)]
        ang = rnd.uniform(0, math.pi * 2)
        for _ in range(6):
            ang += rnd.uniform(-0.6, 0.6)
            x += math.cos(ang) * rnd.randint(8, 18)
            y += math.sin(ang) * rnd.randint(8, 18)
            pts.append((x, y))
        d.line(pts, fill=(24, 22, 28), width=3)
    for _ in range(10):
        x = rnd.randint(0, S)
        y = rnd.choice([78, 160])
        for _ in range(14):
            fx, fy = x + rnd.randint(-16, 16), y + rnd.randint(-6, 6)
            g = rnd.randint(60, 110)
            d.ellipse([fx - 2, fy - 2, fx + 2, fy + 2], fill=(36, g, 40))
    im = im.filter(ImageFilter.GaussianBlur(0.6))
    save(im, "wall_block.png")
    print("HD wall done")

def make_gate():
    W2, H2 = 96, 288
    rnd = random.Random(99)
    im = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # stacked stones
    y = 8
    while y < H2 - 20:
        h = rnd.randint(34, 52)
        y1 = min(H2 - 8, y + h)
        for yy in range(y + 2, y1 - 2):
            t = (yy - y) / max(1, h)
            v = int(92 + (52 - 92) * t)
            d.line([(6, yy), (W2 - 6, yy)], fill=(v, v - 2, v + 6))
        # bevels
        d.line([(6, y + 3), (W2 - 6, y + 3)], fill=(150, 148, 156), width=2)
        d.line([(6, y1 - 3), (W2 - 6, y1 - 3)], fill=(34, 32, 38), width=3)
        d.line([(8, y), (8, y1)], fill=(118, 116, 124), width=2)
        # mortar
        d.line([(4, y1), (W2 - 4, y1)], fill=(26, 24, 30), width=3)
        # stone texture
        for _ in range(20):
            x, yy = rnd.randint(10, W2 - 10), rnd.randint(y + 4, y1 - 4)
            r = rnd.randint(2, 6)
            vv = rnd.randint(-14, 14)
            d.ellipse([x - r, yy - r, x + r, yy + r], fill=(80 + vv, 78 + vv, 86 + vv))
        y = y1
    # carved band with glowing runes
    d.rectangle([4, 120, W2 - 4, 168], fill=(44, 42, 50))
    d.rectangle([4, 120, W2 - 4, 168], outline=(140, 138, 146), width=2)
    for i, rx in enumerate(range(16, W2 - 12, 18)):
        # rune: angular glyph
        pts = [(rx, 128), (rx + 8, 136), (rx, 144), (rx + 8, 152), (rx, 160)]
        d.line(pts, fill=(57, 255, 112), width=3)
    # glow over runes
    ov = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    od.rectangle([4, 120, W2 - 4, 168], fill=(57, 255, 112, 40))
    im.alpha_composite(ov)
    # moss patches
    for _ in range(24):
        x, yy = rnd.randint(4, W2 - 4), rnd.randint(0, H2)
        g = rnd.randint(60, 110)
        d.ellipse([x - 3, yy - 3, x + 3, yy + 3], fill=(36, g, 40, 255))
    # pointed cap
    d.polygon([(2, 26), (W2 - 2, 26), (W2 // 2, 2)], fill=(70, 68, 76))
    d.polygon([(2, 26), (W2 - 2, 26), (W2 // 2, 2)], outline=(140, 138, 146))
    d.line([(W2 // 2 - 14, 18), (W2 // 2 + 14, 18)], fill=(150, 148, 156), width=2)
    # base shadow
    d.rectangle([0, H2 - 8, W2, H2], fill=(20, 18, 24))
    save(im, "gate_post.png")
    print("HD gate post done")

if __name__ == "__main__":
    make_wall()
    make_gate()
