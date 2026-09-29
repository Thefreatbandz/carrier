#!/usr/bin/env python3
"""Gate post art for CARRIER doorways: a chunky dungeon stone pillar."""
from PIL import Image, ImageDraw
import random

random.seed(7)

W, H = 64, 128
img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# Pillar body: dark blue-grey stone
d.rectangle([10, 8, 53, 119], fill=(58, 63, 78, 255))
# Left highlight / right shadow for roundness
d.rectangle([10, 8, 18, 119], fill=(86, 93, 112, 255))
d.rectangle([45, 8, 53, 119], fill=(34, 38, 50, 255))
# Stone block seams
for y in (38, 68, 98):
    d.line([10, y, 53, y], fill=(30, 33, 44, 255), width=2)
    d.line([10, y - 2, 53, y - 2], fill=(80, 86, 104, 255), width=1)
# Cap stone (wider top)
d.rectangle([4, 0, 59, 12], fill=(70, 76, 94, 255))
d.rectangle([4, 0, 12, 12], fill=(98, 105, 126, 255))
d.rectangle([51, 0, 59, 12], fill=(40, 44, 58, 255))
# Base stone (wider bottom)
d.rectangle([4, 112, 59, 127], fill=(48, 52, 66, 255))
d.rectangle([4, 112, 12, 127], fill=(74, 80, 100, 255))
# Cracks + moss speckle
for _ in range(26):
    x = random.randint(12, 51)
    y = random.randint(14, 110)
    d.point((x, y), fill=(28, 30, 40, 255))
for _ in range(10):
    x = random.randint(12, 50)
    y = random.randint(60, 118)
    d.point((x, y), fill=(52, 84, 52, 255))
# Iron band with rivets
d.rectangle([10, 52, 53, 60], fill=(38, 40, 48, 255))
d.rectangle([10, 52, 53, 54], fill=(70, 72, 84, 255))
for x in (16, 31, 47):
    d.ellipse([x - 2, 53, x + 2, 57], fill=(110, 112, 128, 255))
# Green infection glow rune carved near top
d.rectangle([27, 20, 36, 30], fill=(20, 40, 26, 255))
d.rectangle([29, 22, 34, 28], fill=(90, 230, 130, 255))

img.save("/home/hatch/workspace/godot-rpg/carrier/assets-src/gate_post.png")
print("wrote gate_post.png", img.size)
