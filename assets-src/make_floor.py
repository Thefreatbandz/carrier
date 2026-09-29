#!/usr/bin/env python3
"""Floor tile variants + gate glow for CARRIER graphics cleanup."""
from PIL import Image, ImageDraw
import random

random.seed(31)
OUT = "/home/hatch/workspace/godot-rpg/carrier/assets"
S = 120

def base():
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, S - 1, S - 1], fill=(16, 18, 24, 255))
    # per-tile vignette (subtle)
    for i in range(8):
        inset = i * 2
        a = 26 - i * 3
        d.rectangle([inset, inset, S - 1 - inset, S - 1 - inset],
                    outline=(0, 0, 0, max(0, a)))
    # noise speckle
    for _ in range(90):
        x, y = random.randint(0, S - 1), random.randint(0, S - 1)
        v = random.randint(10, 30)
        d.point((x, y), fill=(v, v + 2, v + 6, 255))
    # grout border
    d.rectangle([0, 0, S - 1, S - 1], outline=(6, 7, 10, 255), width=2)
    d.rectangle([1, 1, S - 2, S - 2], outline=(30, 33, 40, 255), width=1)
    return img, d

img, d = base()
img.save(f"{OUT}/floor_a.png")

img, d = base()
# cracks
for _ in range(3):
    x, y = random.randint(20, 100), random.randint(20, 100)
    for _ in range(7):
        nx, ny = x + random.randint(-16, 16), y + random.randint(-16, 16)
        d.line([x, y, nx, ny], fill=(4, 5, 7, 255), width=2)
        x, y = nx, ny
img.save(f"{OUT}/floor_crack.png")

img, d = base()
# grime blotches
for _ in range(7):
    x, y = random.randint(10, 110), random.randint(10, 110)
    r = random.randint(8, 22)
    d.ellipse([x - r, y - r, x + r, y + r], fill=(8, 9, 12, 255))
img.save(f"{OUT}/floor_grime.png")

img, d = base()
# faint infection veins (green)
for _ in range(4):
    x, y = random.randint(20, 100), random.randint(20, 100)
    for _ in range(6):
        nx, ny = x + random.randint(-18, 18), y + random.randint(-18, 18)
        d.line([x, y, nx, ny], fill=(34, 90, 52, 255), width=2)
        d.line([x, y, nx, ny], fill=(70, 170, 100, 255), width=1)
        x, y = nx, ny
img.save(f"{OUT}/floor_moss.png")

# soft radial glow (gates, extraction pad)
G = 256
glow = Image.new("RGBA", (G, G), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
for r in range(G // 2, 0, -1):
    a = int(90 * (1 - r / (G / 2)) ** 2)
    gd.ellipse([G // 2 - r, G // 2 - r, G // 2 + r, G // 2 + r],
               fill=(70, 255, 140, a))
glow.save(f"{OUT}/glow_green.png")
print("floor variants + glow written")
