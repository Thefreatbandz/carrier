#!/usr/bin/env python3
"""CARRIER character art v4 — HAZMAT restyle (Tbandz pick).

Player: patched yellow hazmat suit, suit hood, cracked gas mask with glowing
green visor, chest strap with infection vials, scavenged blade.
Creatures: same v3 bodies/silhouettes, restyled in the hazmat design language
(torn containment suits, respirator masks, straps, yellowed plates).

Same 48 filenames as the live build (drop-in replacement). Run from carrier root:
    python3 assets-src/char_factory_v4.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
import char_factory_v3 as V3
from PIL import Image, ImageDraw
import math

new = V3.new; save = V3.save; part = V3.part
poly_mask = V3.poly_mask; ell_mask = V3.ell_mask
add_glow = V3.add_glow; grain = V3.grain; rim_stroke = V3.rim_stroke
blade_shape = V3.blade_shape; slash_arc = V3.slash_arc; breathe = V3.breathe

RIM, RIM_DIM = V3.RIM, V3.RIM_DIM
EYE_G, GLOW_INF, VEIN = V3.EYE_G, V3.GLOW_INF, V3.VEIN
STEEL, STEEL_D, EDGE_G = V3.STEEL, V3.STEEL_D, V3.EDGE_G
VIAL = V3.VIAL

# ---------------- hazmat palette ----------------
HAZ_Y   = (198, 160, 46)    # suit yellow
HAZ_YM  = (162, 128, 36)    # mid
HAZ_YD  = (118, 92, 26)     # dark / folds
HAZ_OL  = (88, 70, 20)      # deep shadow olive
PATCH   = (76, 68, 54)      # repair patches
PATCH_D = (54, 48, 38)
RUBBER  = (38, 36, 34)      # mask / gloves / boots
RUBBER_D= (22, 20, 18)
SEAM    = (96, 76, 24)      # stitched seams
STRAP   = (64, 56, 40)      # straps / webbing
STRAP_D = (44, 38, 28)
VISOR_D = (10, 26, 14)      # visor socket
GRIME   = (60, 54, 34)

def _patch(d, x, y, w, h, rot=0):
    """Stitched repair patch."""
    d.rectangle([x - w / 2, y - h / 2, x + w / 2, y + h / 2], fill=PATCH + (255,))
    d.rectangle([x - w / 2, y - h / 2, x + w / 2, y + h / 2], outline=PATCH_D + (255,), width=2)
    for sx in (-w / 2 + 4, w / 2 - 4):
        d.line([(x + sx, y - h / 2 + 3), (x + sx, y + h / 2 - 3)], fill=SEAM + (200,), width=2)

def _suit_body(im, cx, top_y, hem_y, hem_w, sway=0, back=0, tear_boost=0):
    """Tapered hazmat suit torso with patches, seams, straps, folds."""
    pts = [(cx - 30 + back, top_y), (cx + 32 + back, top_y - 4),
           (cx + hem_w + sway, hem_y), (cx - hem_w + sway * 0.6, hem_y + 4)]
    im.alpha_composite(part(poly_mask(pts), (cx - hem_w - 8, top_y - 8, cx + hem_w + 8, hem_y + 8),
                            HAZ_Y, HAZ_YD))
    d = ImageDraw.Draw(im)
    # fold shadows
    for fx, fw in ((-24, 8), (-4, 10), (18, 9)):
        x = cx + fx + sway * 0.4 + back
        d.polygon([(x - fw, top_y + 12), (x + fw, top_y + 12),
                   (x + fw * 1.5 + sway * 0.5, hem_y), (x - fw * 1.5 + sway * 0.5, hem_y)],
                  fill=HAZ_OL + (150,))
    # center zipper seam
    d.line([(cx + back + sway * 0.3, top_y + 8), (cx + back + sway * 0.5, hem_y - 6)],
           fill=SEAM + (220,), width=3)
    # stitched side seams
    for s in (-1, 1):
        d.line([(cx + s * 30 + back, top_y + 14), (cx + s * (hem_w - 8) + sway * 0.6, hem_y - 4)],
               fill=SEAM + (160,), width=2)
    # repair patches
    _patch(d, cx - 22 + back, top_y + 66, 26, 20)
    _patch(d, cx + 24 + back + sway * 0.4, top_y + 108, 22, 26)
    if tear_boost:
        _patch(d, cx - 6 + back, hem_y - 34, 30, 18)
    # grime blotches
    for gx, gy, gr in ((cx - 30, hem_y - 50, 12), (cx + 26, top_y + 40, 9), (cx + 8, hem_y - 90, 11)):
        d.ellipse([gx - gr, gy - gr, gx + gr, gy + gr], fill=GRIME + (90,))
    grain(im, (cx - hem_w, top_y, cx + hem_w, hem_y), 12)
    # rim light along right edge
    rim_stroke(im, [(cx + 32 + back, top_y), (cx + hem_w * 0.92 + sway, hem_y - 30)], RIM, 3, 200)
    rim_stroke(im, [(cx - 30 + back, top_y + 6), (cx - hem_w * 0.9 + sway * 0.6, hem_y - 34)], RIM_DIM, 2, 80)

def _mask_side(im, cx, cy, facing_right=True, visor_boost=0, cracked=True):
    """Suit hood + cracked gas mask, big glowing green visor lenses."""
    s = 1 if facing_right else -1
    # hood mass (suit fabric)
    im.alpha_composite(part(ell_mask(cx, cy, 42, 44), (cx - 46, cy - 48, cx + 46, cy + 48), HAZ_Y, HAZ_YM))
    d = ImageDraw.Draw(im)
    d.polygon([(cx - 10 * s, cy - 40), (cx + 44 * s, cy - 34), (cx + 20 * s, cy - 8)], fill=HAZ_Y + (255,))
    _patch(d, cx - 24 * s, cy - 26, 20, 14)
    # mask body (front-right)
    fx = cx + 16 * s
    im.alpha_composite(part(ell_mask(fx, cy + 8, 26, 30), (fx - 30, cy - 26, fx + 30, cy + 42), RUBBER, RUBBER_D))
    # filter canister on cheek
    d.ellipse([fx + 8 * s - 9, cy + 16, fx + 8 * s + 9, cy + 34], fill=RUBBER_D + (255,),
              outline=(70, 68, 64, 255), width=2)
    # VISOR — big round glowing green lenses
    for ex, ew, eh in ((fx - 7, 13, 15), (fx + 11, 11, 13)):
        d.ellipse([ex - ew / 2, cy - 2, ex + ew / 2, cy - 2 + eh], fill=VISOR_D + (255,))
        d.ellipse([ex - ew / 2 + 2, cy, ex + ew / 2 - 2, cy + eh - 2], fill=EYE_G + (255,))
    add_glow(im, fx + 2, cy + 6, 28, (57, 255, 106), 70 + visor_boost)
    # cracks across the mask
    if cracked:
        d.line([(fx - 18, cy - 12), (fx - 6, cy - 2), (fx - 12, cy + 8)], fill=(120, 118, 112, 255), width=2)
        d.line([(fx + 16, cy - 8), (fx + 8, cy + 2)], fill=(120, 118, 112, 255), width=2)
    # straps around hood
    d.line([(cx - 30 * s, cy - 18), (fx - 20, cy - 6)], fill=STRAP_D + (255,), width=5)
    d.line([(cx - 28 * s, cy + 22), (fx - 22, cy + 18)], fill=STRAP_D + (255,), width=5)
    # infection seep at hood seam
    d.line([(fx - 22, cy + 26), (fx - 12, cy + 32), (fx - 16, cy + 38)], fill=VEIN + (170,), width=2)
    add_glow(im, fx - 14, cy + 32, 12, VEIN, 40)
    rim_stroke(im, [(cx + 40 * s, cy - 30), (cx + 44 * s, cy + 10)], RIM, 3, 210)

def _chest_strap(im, cx, y0, y1, flip=False):
    """Webbing strap across chest with glowing infection vials."""
    d = ImageDraw.Draw(im)
    s = -1 if flip else 1
    d.line([(cx - 28, y0), (cx + 26 * s, y1)], fill=STRAP_D + (255,), width=17)
    d.line([(cx - 28, y0), (cx + 26 * s, y1)], fill=STRAP + (255,), width=12)
    d.rectangle([cx - 34, y0 - 10, cx - 22, y0 + 10], fill=(80, 78, 72, 255))  # buckle
    for i, t in enumerate((0.35, 0.55, 0.75)):
        vx = cx - 28 + (54 * s) * t
        vy = y0 + (y1 - y0) * t
        d.rectangle([vx - 6, vy - 9, vx + 6, vy + 9], fill=(20, 40, 30, 255), outline=(70, 68, 64, 255), width=2)
        d.rectangle([vx - 4, vy - 2, vx + 4, vy + 7], fill=VIAL + (255,))
    add_glow(im, cx - 28 + 54 * s * 0.55, y0 + (y1 - y0) * 0.55, 18, VIAL, 50)

def _boot_haz(d, x, y, step=0, wdt=22):
    d.ellipse([x - wdt / 2, y - 24 + step, x + wdt / 2, y + step], fill=RUBBER_D + (255,))
    d.rectangle([x - wdt / 2, y - 30 + step, x + wdt / 2, y - 8 + step], fill=RUBBER + (255,))
    d.line([(x - wdt / 2, y - 14 + step), (x + wdt / 2, y - 14 + step)], fill=SEAM + (180,), width=2)

def _glove(d, x, y, wdt=16):
    d.ellipse([x - wdt / 2, y - wdt / 2, x + wdt / 2, y + wdt / 2], fill=RUBBER + (255,))
    d.rectangle([x - wdt / 2, y - wdt, x + wdt / 2, y], fill=HAZ_YM + (255,))

# =====================================================================
# PLAYER v4 — Hazmat Carrier (same poses/anchors as v3)
# =====================================================================
def draw_player_side(im, ph, mode="idle"):
    cx, d = 96, ImageDraw.Draw(im)
    bob = [0, -5, 0, -5][ph] if mode == "walk" else 0
    sway = [0, 7, 0, -7][ph] if mode == "walk" else (3 if mode == "idle" else 0)
    lunge = 16 if mode == "attack1" else (8 if mode == "attack2" else 0)
    back = -12 if mode == "hurt" else 0
    top_y, hem_y = 74 + bob, 232
    if mode == "walk":
        _boot_haz(d, cx - 14 + [0, 14, 0, -14][ph], hem_y - 6, [0, -10, 0, -10][ph])
        _boot_haz(d, cx + 16 + [0, -14, 0, 14][ph], hem_y - 4, [0, -10, 0, -10][(ph + 2) % 4])
    elif mode not in ("death0", "death1"):
        _boot_haz(d, cx - 12, hem_y - 6); _boot_haz(d, cx + 18, hem_y - 4)
    if mode in ("death0", "death1"):
        return draw_player_death(im, 0 if mode == "death0" else 1)
    _suit_body(im, cx, top_y, hem_y, 54, sway, back)
    _chest_strap(im, cx + back, 108 + bob, 168 + bob)
    # backpack canister peeking behind shoulder
    d.rectangle([cx - 44 + back, 92 + bob, cx - 28 + back, 140 + bob], fill=RUBBER_D + (255,),
                outline=(70, 68, 64, 255), width=2)
    d.line([(cx - 36 + back, 92 + bob), (cx - 36 + back, 84 + bob)], fill=(70, 68, 64, 255), width=4)
    _mask_side(im, cx + back, 52 + bob, True, visor_boost=50 if mode.startswith("attack") else 0)
    # right arm: suit sleeve from shoulder to glove (tracks blade hand)
    hx, hy = cx + 30 + back + lunge, 150 + bob
    shx, shy = cx + 10 + back, 118 + bob
    d.line([(shx, shy), ((shx + hx) / 2 + 4, (shy + hy) / 2), (hx, hy)], fill=HAZ_YM + (255,), width=17)
    d.line([(shx, shy), ((shx + hx) / 2 + 4, (shy + hy) / 2), (hx, hy)], fill=HAZ_Y + (255,), width=11)
    _patch(d, (shx + hx) / 2 + 2, (shy + hy) / 2, 16, 12)  # elbow patch
    # scavenged blade per pose
    if mode == "idle":
        blade_shape(d, hx, hy, hx + 10, hy + 78, 9)
        _glove(d, hx, hy + 4)
    elif mode == "walk":
        blade_shape(d, hx, hy, hx + 12, hy + 76, 9)
        _glove(d, hx, hy + 4)
    elif mode == "attack0":
        blade_shape(d, hx - 6, hy - 10, hx - 52, hy - 78, 10)
        _glove(d, hx - 6, hy - 8)
        add_glow(im, hx - 40, hy - 60, 30, (57, 255, 106), 60)
    elif mode == "attack1":
        blade_shape(d, hx - 30, hy - 20, hx + 78, hy - 34, 11)
        _glove(d, hx - 28, hy - 18)
        slash_arc(im, hx + 10, hy - 10, 60, 108, -70, 40, (190, 255, 200), 170)
        slash_arc(im, hx + 10, hy - 10, 40, 66, -60, 30, (57, 255, 106), 130)
        add_glow(im, hx + 40, hy - 30, 44, (200, 255, 210), 80)
    elif mode == "attack2":
        blade_shape(d, hx + 6, hy + 6, hx + 52, hy + 52, 9)
        _glove(d, hx + 8, hy + 8)
    elif mode == "hurt":
        blade_shape(d, hx - 8, hy, hx + 2, hy + 70, 9)
        _glove(d, hx - 6, hy + 2)
        rim_stroke(im, [(cx - 34 + back, top_y), (cx - 52 + back, hem_y - 40)], (255, 90, 90), 4, 220)
    return im

def draw_player_down(im, ph, mode="idle"):
    cx, d = 96, ImageDraw.Draw(im)
    bob = [0, -5, 0, -5][ph] if mode == "walk" else 0
    sway = [0, 5, 0, -5][ph] if mode == "walk" else 0
    top_y, hem_y = 76 + bob, 234
    if mode == "walk":
        _boot_haz(d, cx - 16, hem_y - 6, [0, -10, 0, -10][ph])
        _boot_haz(d, cx + 16, hem_y - 4, [0, -10, 0, -10][(ph + 2) % 4])
    else:
        _boot_haz(d, cx - 14, hem_y - 6); _boot_haz(d, cx + 16, hem_y - 4)
    _suit_body(im, cx, top_y, hem_y, 52, sway)
    _chest_strap(im, cx, 110 + bob, 170 + bob)
    # hood + mask front
    im.alpha_composite(part(ell_mask(cx, 54 + bob, 42, 44), (cx - 46, 6 + bob, cx + 46, 102 + bob), HAZ_Y, HAZ_YM))
    d = ImageDraw.Draw(im)
    _patch(d, cx - 22, 30 + bob, 20, 14)
    im.alpha_composite(part(ell_mask(cx, 62 + bob, 28, 30), (cx - 32, 28 + bob, cx + 32, 96 + bob), RUBBER, RUBBER_D))
    for ex, ew in ((cx - 13, 14), (cx + 13, 12)):
        d.ellipse([ex - ew / 2, 52 + bob, ex + ew / 2, 68 + bob], fill=(10, 26, 14, 255))
        d.ellipse([ex - ew / 2 + 2, 54 + bob, ex + ew / 2 - 2, 66 + bob], fill=EYE_G + (255,))
    add_glow(im, cx, 60 + bob, 32, (57, 255, 106), 70)
    d.line([(cx - 20, 40 + bob), (cx - 8, 48 + bob)], fill=(120, 118, 112, 255), width=2)  # crack
    d.ellipse([cx - 4, 74 + bob, cx + 14, 90 + bob], fill=RUBBER_D + (255,), outline=(70, 68, 64, 255), width=2)
    rim_stroke(im, [(cx + 40, 24 + bob), (cx + 44, 70 + bob)], RIM, 3, 200)
    hx = cx + 52
    blade_shape(d, hx, 140 + bob, hx + 8, 222, 9)
    _glove(d, hx + 2, 144 + bob)
    return im

def draw_player_up(im, ph, mode="idle"):
    cx, d = 96, ImageDraw.Draw(im)
    bob = [0, -5, 0, -5][ph] if mode == "walk" else 0
    sway = [0, 5, 0, -5][ph] if mode == "walk" else 0
    top_y, hem_y = 76 + bob, 234
    if mode == "walk":
        _boot_haz(d, cx - 16, hem_y - 6, [0, -10, 0, -10][ph])
        _boot_haz(d, cx + 16, hem_y - 4, [0, -10, 0, -10][(ph + 2) % 4])
    else:
        _boot_haz(d, cx - 14, hem_y - 6); _boot_haz(d, cx + 16, hem_y - 4)
    _suit_body(im, cx, top_y, hem_y, 52, sway)
    # backpack rig on back
    d.rectangle([cx - 26, 96 + bob, cx + 26, 168 + bob], fill=RUBBER_D + (255,), outline=STRAP_D + (255,), width=3)
    d.rectangle([cx - 18, 76 + bob, cx + 18, 100 + bob], fill=(70, 68, 64, 255), outline=RUBBER_D + (255,), width=2)
    d.line([(cx - 26, 110 + bob), (cx + 26, 110 + bob)], fill=STRAP + (255,), width=5)
    d.line([(cx - 26, 140 + bob), (cx + 26, 140 + bob)], fill=STRAP + (255,), width=5)
    add_glow(im, cx, 88 + bob, 14, (57, 255, 106), 40)  # gauge light
    # hood back with seam
    im.alpha_composite(part(ell_mask(cx, 54 + bob, 42, 44), (cx - 46, 6 + bob, cx + 46, 102 + bob), HAZ_YM, HAZ_YD))
    d = ImageDraw.Draw(im)
    d.line([(cx, 14 + bob), (cx, 96 + bob)], fill=SEAM + (220,), width=4)
    _patch(d, cx + 20, 40 + bob, 18, 14)
    rim_stroke(im, [(cx + 40, 24 + bob), (cx + 44, 70 + bob)], RIM, 3, 200)
    hx = cx + 52
    blade_shape(d, hx, 140 + bob, hx + 8, 222, 9)
    _glove(d, hx + 2, 144 + bob)
    return im

def draw_player_death(im, stage):
    cx, d = 96, ImageDraw.Draw(im)
    if stage == 0:
        # crumpling: suit folds, visor flickers
        im.alpha_composite(part(poly_mask([(cx - 52, 236), (cx - 38, 150), (cx + 48, 156), (cx + 56, 236)]),
                                (cx - 56, 146, cx + 60, 240), HAZ_YM, HAZ_OL))
        im.alpha_composite(part(ell_mask(cx + 8, 140, 24, 22), (cx - 20, 116, cx + 36, 164), RUBBER, RUBBER_D))
        d.ellipse([cx - 2, 132, cx + 18, 148], fill=(10, 26, 14, 255))
        d.ellipse([cx + 1, 135, cx + 15, 145], fill=(90, 160, 100, 255))  # dying visor
        add_glow(im, cx + 8, 140, 30, (57, 255, 106), 50)
    else:
        # suit slumped, vials spilled glowing
        d.ellipse([cx - 60, 216, cx + 60, 248], fill=HAZ_OL + (230,))
        im.alpha_composite(part(ell_mask(cx, 228, 34, 12), (cx - 38, 214, cx + 38, 244), HAZ_YD, HAZ_OL))
        for i in range(3):
            vx = cx - 30 + i * 28
            d.rectangle([vx - 5, 218, vx + 5, 234], fill=VIAL + (220,))
        add_glow(im, cx, 228, 50, VIAL, 90)
        d.ellipse([cx - 50, 208, cx - 30, 224], fill=RUBBER_D + (255,))  # dropped mask
    return im

# ---------------- enemy hazmat palette ----------------
ESUIT   = (172, 140, 42)     # torn containment suit
ESUIT_D = (112, 90, 28)
ESUIT_T = (72, 62, 32)       # shredded dark bits
EMASK   = (44, 42, 40)
EMASK_D = (26, 24, 22)
EPLATE  = (158, 132, 58)     # yellowed containment armor
EPLATE_D= (100, 84, 36)
ERUST   = (140, 84, 44)
ECRACK  = (255, 150, 60)

def _suit_strip(d, cx, sx, sw, ty, lurch=0):
    """Hanging shredded suit strip."""
    d.polygon([(cx + sx + lurch, ty - 64), (cx + sx + sw + lurch, ty - 64),
               (cx + sx + sw * 0.7 + lurch, ty + 40), (cx + sx * 0.7 + lurch, ty + 40)],
              fill=ESUIT + (255,))
    d.polygon([(cx + sx * 0.7 + lurch, ty + 40), (cx + sx + sw * 0.7 + lurch, ty + 40),
               (cx + sx + sw * 0.4 + lurch, ty + 62), (cx + sx * 0.4 + lurch, ty + 62)],
              fill=ESUIT_D + (255,))

def _visor_eyes(d, hx, hy, color, w=5, h=9, spread=14):
    """Cracked-mask glowing visor eyes."""
    for ex in (hx - spread / 2, hx + spread / 2):
        d.ellipse([ex - w, hy - h / 2, ex + w, hy + h / 2], fill=(8, 16, 8, 255))
        d.ellipse([ex - w + 2, hy - h / 2 + 2, ex + w - 2, hy + h / 2 - 2], fill=color + (255,))

# =====================================================================
# ROTWALKER v4 — same bulk/ribcage body, burst containment suit + respirator
# =====================================================================
def _rotwalker_body(im, cx, lurch=0, rear=0, slam=0, glow_boost=0):
    d = ImageDraw.Draw(im)
    base_y = 236
    # legs: torn suit, heavy boots
    for lx, bent in ((-24, 1), (22, -1)):
        x = cx + lx + lurch
        d.rectangle([x - 13, base_y - 70, x + 13, base_y - 6], fill=ESUIT_D + (255,))
        d.ellipse([x - 15, base_y - 22, x + 15, base_y + 2], fill=EMASK_D + (255,))
    # torso: burst suit stretched over bulk
    ty = 150 - rear * 26 + slam * 10
    torso = [(cx - 52 + lurch, ty - 62), (cx + 54 + lurch, ty - 66),
             (cx + 48 + lurch, ty + 62), (cx - 56 + lurch, ty + 58)]
    im.alpha_composite(part(poly_mask(torso), (cx - 60, ty - 70, cx + 60, ty + 66), ESUIT, ESUIT_D))
    # suit burst open at chest — glowing interior
    d.ellipse([cx - 34 + lurch, ty - 30, cx + 40 + lurch, ty + 44], fill=(16, 40, 20, 255))
    add_glow(im, cx + 4 + lurch, ty + 6, 40, GLOW_INF, 60 + glow_boost)
    # shredded suit strips hanging
    for sx, sw in ((-38, 16), (-8, 20), (24, 14)):
        _suit_strip(d, cx, sx, sw, ty, lurch)
    # straps dangling
    for sx in (-46, 40):
        d.line([(cx + sx + lurch, ty - 50), (cx + sx + lurch * 1.2, ty + 30)], fill=STRAP_D + (255,), width=6)
    # EXPOSED RIBCAGE — glowing green ribs (signature kept)
    rib_cx, rib_cy = cx + 6 + lurch, ty + 2
    for i in range(4):
        ry = rib_cy - 24 + i * 15
        d.arc([rib_cx - 30, ry - 10, rib_cx + 30, ry + 10], start=200, end=340, fill=(30, 40, 30, 255), width=9)
        d.arc([rib_cx - 30, ry - 10, rib_cx + 30, ry + 10], start=200, end=340, fill=GLOW_INF + (255,), width=4)
    add_glow(im, rib_cx, rib_cy, 46, GLOW_INF, 70 + glow_boost)
    # head: cracked respirator, visor eyes, shattered lower mask with glowing maw
    hx, hy = cx + 10 + lurch, ty - 92 - rear * 10
    im.alpha_composite(part(ell_mask(hx, hy, 26, 28), (hx - 30, hy - 32, hx + 30, hy + 32), EMASK, EMASK_D))
    d.line([(hx - 22, hy - 18), (hx - 8, hy - 4), (hx - 16, hy + 6)], fill=(120, 118, 112, 255), width=2)
    _visor_eyes(d, hx - 4, hy - 8, (140, 255, 160))
    add_glow(im, hx - 4, hy - 8, 20, GLOW_INF, 60 + glow_boost)
    d.ellipse([hx - 2, hy + 2, hx + 22, hy + 28], fill=(10, 8, 8, 255))  # shattered maw
    add_glow(im, hx + 10, hy + 14, 22, GLOW_INF, 80 + glow_boost)
    d.polygon([(hx + 2, hy + 20), (hx + 22, hy + 22), (hx + 14, hy + 36), (hx, hy + 32)], fill=EMASK_D + (255,))
    # filter canister on jaw
    d.ellipse([hx - 26, hy + 8, hx - 10, hy + 26], fill=EMASK_D + (255,), outline=(70, 68, 64, 255), width=2)
    rim_stroke(im, [(cx + 54 + lurch, ty - 60), (cx + 50 + lurch, ty + 50)], (170, 255, 170), 3, 160)
    return ty

def draw_rotwalker(im, ph, mode="walk"):
    cx = 96
    d = ImageDraw.Draw(im)
    lurch = [0, 10, 0, -10][ph] if mode == "walk" else 0
    if mode == "attack0":
        ty = _rotwalker_body(im, cx, rear=1, glow_boost=60)
        for ax in (-46, 50):
            d.line([(cx + ax * 0.6, ty - 40), (cx + ax, ty - 130)], fill=ESUIT_D + (255,), width=26)
            d.ellipse([cx + ax - 16, ty - 146, cx + ax + 16, ty - 114], fill=ESUIT + (255,))
            _glove_d(d, cx + ax, ty - 130)
        add_glow(im, cx, ty - 120, 60, GLOW_INF, 70)
    elif mode == "attack1":
        ty = _rotwalker_body(im, cx, slam=1)
        for ax in (-48, 52):
            d.line([(cx + ax * 0.6, ty - 40), (cx + ax, ty + 66)], fill=ESUIT_D + (255,), width=30)
            d.ellipse([cx + ax - 20, ty + 52, cx + ax + 20, ty + 86], fill=ESUIT + (255,))
            _glove_d(d, cx + ax, ty + 70)
            for i in range(4):
                d.line([(cx + ax - 12 + i * 8, ty + 78), (cx + ax - 14 + i * 8, ty + 96)], fill=(220, 220, 210, 255), width=4)
        for r, a in ((80, 110), (110, 70), (140, 40)):
            d.ellipse([cx - r, 236 - r * 0.35, cx + r, 236 + r * 0.35], outline=GLOW_INF + (a,), width=6)
        add_glow(im, cx, 226, 70, GLOW_INF, 90)
    else:
        ty = _rotwalker_body(im, cx, lurch=lurch)
        bob = [0, -4, 0, -4][ph]
        ax = cx + 58 + lurch
        d.line([(cx + 34, ty - 30 + bob), (ax, ty + 70)], fill=ESUIT_D + (255,), width=30)
        d.ellipse([ax - 19, ty + 56, ax + 19, ty + 90], fill=ESUIT + (255,))
        _glove_d(d, ax, ty + 72)
        for i in range(4):
            d.line([(ax - 12 + i * 8, ty + 82), (ax - 15 + i * 8, ty + 102)], fill=(220, 220, 210, 255), width=5)
        d.line([(cx - 40, ty - 30 + bob), (cx - 62 + lurch, ty + 30)], fill=ESUIT_D + (255,), width=15)
    grain(im, (cx - 60, 60, cx + 60, 236), 10)
    return im

def _glove_d(d, x, y):
    d.ellipse([x - 14, y - 12, x + 14, y + 14], fill=EMASK + (255,))

def draw_rotwalker_death(im, stage):
    cx, d = 96, ImageDraw.Draw(im)
    if stage == 0:
        im.alpha_composite(part(poly_mask([(cx - 56, 236), (cx - 40, 150), (cx + 50, 156), (cx + 60, 236)]),
                                (cx - 60, 146, cx + 64, 240), ESUIT_D, (60, 52, 24)))
        im.alpha_composite(part(ell_mask(cx + 8, 140, 24, 22), (cx - 20, 116, cx + 36, 164), EMASK, EMASK_D))
        d.ellipse([cx - 2, 132, cx + 18, 148], fill=(10, 26, 14, 255))
        add_glow(im, cx, 200, 50, GLOW_INF, 60)
    else:
        d.ellipse([cx - 64, 214, cx + 64, 250], fill=(24, 54, 32, 210))
        d.ellipse([cx - 40, 222, cx + 40, 246], fill=(52, 150, 76, 210))
        add_glow(im, cx, 232, 56, GLOW_INF, 100)
        for i in range(5):
            bx, by = cx - 40 + i * 18, 226 + (i % 2) * 8
            d.line([(bx, by), (bx + 10, by - 6)], fill=(200, 200, 190, 220), width=4)
    return im

# =====================================================================
# SKITTER v4 — same emaciated body/spine, shredded suit + cracked mask
# =====================================================================
def _skitter_body(im, cx, lean=0, coil=0, air=0, glow_boost=0):
    d = ImageDraw.Draw(im)
    base_y = 238 - air
    hip_y = base_y - 110 + coil * 30
    sh_y = hip_y - 78 + coil * 10
    # long legs in shredded suit
    for lx, fwd in ((-16, 1), (16, -1)):
        kx = cx + lx + lean * 0.4 + fwd * 14
        d.line([(cx + lx, hip_y), (kx, base_y - 44)], fill=ESUIT_D + (255,), width=14)
        d.line([(kx, base_y - 44), (kx + fwd * 10, base_y - 4)], fill=ESUIT_D + (255,), width=11)
        d.ellipse([kx + fwd * 10 - 9, base_y - 14, kx + fwd * 10 + 9, base_y + 4], fill=EMASK_D + (255,))
    # emaciated torso, suit hanging loose + torn open at back
    im.alpha_composite(part(poly_mask([(cx - 22 + lean * 0.5, sh_y), (cx + 24 + lean * 0.5, sh_y + 6),
                                       (cx + 16, hip_y), (cx - 18, hip_y)]),
                            (cx - 26, sh_y - 6, cx + 28, hip_y + 6), ESUIT, ESUIT_D))
    # fluttering suit shreds
    for i, (sx, sl) in enumerate(((-24, 26), (-8, 34), (10, 24))):
        d.polygon([(cx + sx + lean * 0.5, hip_y - 6), (cx + sx + 10 + lean * 0.5, hip_y - 6),
                   (cx + sx + 6 + lean * 0.7, hip_y + sl)], fill=ESUIT_T + (255,))
    # EXPOSED SPINE — glowing dots down the torn-open back
    for i in range(6):
        sy = sh_y + 8 + i * 12
        sx = cx - 20 + lean * 0.5 - i * 1.5
        d.ellipse([sx - 5, sy - 5, sx + 5, sy + 5], fill=GLOW_INF + (255,))
    add_glow(im, cx - 22, sh_y + 40, 34, GLOW_INF, 60 + glow_boost)
    for i in range(3):
        ry = sh_y + 22 + i * 13
        d.arc([cx - 20 + lean * 0.5, ry - 8, cx + 22 + lean * 0.5, ry + 8], start=190, end=350,
              fill=ESUIT_D + (255,), width=3)
    # long arms with claws
    for ax, fwd in ((-1, -1), (1, 1)):
        sx = cx + ax * 24 + lean * 0.5
        ex = sx + fwd * 26 + lean * 0.6
        hx2 = ex + fwd * 22
        hy2 = sh_y + 66 - coil * 20
        d.line([(sx, sh_y + 10), (ex, sh_y + 44)], fill=ESUIT_D + (255,), width=16)
        d.line([(ex, sh_y + 44), (hx2, hy2)], fill=EMASK_D + (255,), width=11)
        for i in range(4):
            d.line([(hx2 - 8 + i * 6, hy2), (hx2 - 12 + i * 6 + fwd * 8, hy2 + 22)], fill=(230, 230, 220, 255), width=4)
    # head: cracked mask, AMBER visor (differentiates from green player)
    hx, hy = cx + 10 + lean * 0.7, sh_y - 26
    im.alpha_composite(part(ell_mask(hx, hy, 20, 24), (hx - 24, hy - 28, hx + 24, hy + 28), EMASK, EMASK_D))
    d.line([(hx - 14, hy - 16), (hx - 4, hy - 4)], fill=(120, 118, 112, 255), width=2)
    _visor_eyes(d, hx, hy - 4, (255, 200, 90), w=6, h=13, spread=16)
    add_glow(im, hx, hy - 4, 20, (255, 200, 90), 50)
    d.line([(hx - 14, hy + 12), (hx + 10, hy + 18)], fill=(60, 20, 20, 255), width=5)
    # torn suit collar
    d.polygon([(hx - 18, hy + 20), (hx + 18, hy + 20), (hx + 10, hy + 36), (hx - 12, hy + 36)], fill=ESUIT_T + (255,))
    rim_stroke(im, [(cx + 24 + lean * 0.5, sh_y), (cx + 18, hip_y)], (255, 240, 170), 2, 150)
    return sh_y

def draw_skitter(im, ph, mode="walk"):
    cx = 96
    d = ImageDraw.Draw(im)
    if mode == "attack0":
        _skitter_body(im, cx, coil=1, glow_boost=40)
    elif mode == "attack1":
        _skitter_body(im, cx, lean=26, air=34, glow_boost=30)
        for off in (-30, -6, 18):
            d.line([(cx + 40, 120 + off), (cx + 110, 150 + off)], fill=(255, 240, 180, 200), width=5)
            d.line([(cx + 40, 120 + off), (cx + 110, 150 + off)], fill=(255, 255, 255, 230), width=2)
        add_glow(im, cx + 70, 140, 40, (255, 240, 180), 60)
    else:
        lean = [0, 12, 4, 14][ph]
        air = [0, 16, 0, 10][ph]
        _skitter_body(im, cx, lean=lean, air=air)
    grain(im, (cx - 40, 40, cx + 50, 240), 10)
    return im

def draw_skitter_death(im, stage):
    cx, d = 96, ImageDraw.Draw(im)
    if stage == 0:
        im.alpha_composite(part(poly_mask([(cx - 30, 236), (cx - 20, 150), (cx + 26, 156), (cx + 34, 236)]),
                                (cx - 34, 146, cx + 38, 240), ESUIT_D, (80, 64, 30)))
        im.alpha_composite(part(ell_mask(cx + 6, 132, 18, 20), (cx - 16, 110, cx + 28, 156), EMASK, EMASK_D))
    else:
        d.ellipse([cx - 52, 218, cx + 52, 250], fill=(30, 44, 30, 210))
        add_glow(im, cx, 234, 46, GLOW_INF, 90)
        for i in range(4):
            bx = cx - 36 + i * 22
            d.line([(bx, 232), (bx + 8, 214)], fill=(210, 200, 190, 220), width=4)
    return im

# =====================================================================
# BULWARK v4 — same plated brute, yellowed containment armor + visor slit
# =====================================================================
def _bulwark_body(im, cx, stomp=0, raise_f=0, glow_boost=0):
    d = ImageDraw.Draw(im)
    base_y = 240
    # dark gap between legs first (separation)
    d.rectangle([cx - 9, base_y - 96, cx + 9, base_y - 8], fill=(18, 16, 14, 255))
    # tree-trunk legs in yellowed armor
    for lx in (-30, 30):
        x = cx + lx
        d.rectangle([x - 20, base_y - 96, x + 20, base_y - 8], fill=EPLATE_D + (255,))
        d.rectangle([x - 20, base_y - 96, x + 20, base_y - 70], fill=EPLATE + (255,))
        d.ellipse([x - 22, base_y - 24, x + 22, base_y + 2], fill=(52, 46, 30, 255))
        d.line([(x - 20, base_y - 60), (x + 20, base_y - 60)], fill=SEAM + (200,), width=2)
    # massive torso — dark suit between the plates
    ty = 150 - raise_f * 14 + stomp * 6
    im.alpha_composite(part(poly_mask([(cx - 64, ty - 70), (cx + 64, ty - 70), (cx + 56, ty + 70), (cx - 58, ty + 70)]),
                            (cx - 68, ty - 74, cx + 68, ty + 74), (70, 60, 30), (44, 38, 22)))
    # chest plate — yellowed, separate plate with bolts
    im.alpha_composite(part(poly_mask([(cx - 46, ty - 52), (cx + 46, ty - 52), (cx + 40, ty + 30), (cx - 42, ty + 30)]),
                            (cx - 50, ty - 56, cx + 50, ty + 34), EPLATE, EPLATE_D))
    d.rectangle([cx - 46, ty - 52, cx + 46, ty - 46], fill=(190, 164, 80, 255))
    for bx, by in ((-38, ty - 40), (38, ty - 40), (-34, ty + 18), (34, ty + 18)):
        d.ellipse([bx - 4, by - 4, bx + 4, by + 4], fill=(60, 54, 40, 255))
    # glowing cracks between plates
    for crx, cry, cl in ((-30, ty - 20, 26), (24, ty + 6, 30), (-6, ty - 44, 22), (38, ty - 34, 18)):
        d.line([(crx - 12, cry), (crx + 12, cry + 6)], fill=ECRACK + (255,), width=6)
        d.line([(crx, cry - 8), (crx + 4, cry + 12)], fill=(255, 220, 160, 255), width=3)
    add_glow(im, cx, ty - 10, 60, ECRACK, 55 + glow_boost)
    # pauldrons — big yellowed domes
    for px in (-62, 62):
        im.alpha_composite(part(ell_mask(cx + px, ty - 62, 30, 26), (cx + px - 34, ty - 92, cx + px + 34, ty - 32),
                                EPLATE, EPLATE_D))
        d.arc([cx + px - 30, ty - 88, cx + px + 30, ty - 36], start=200, end=340, fill=ERUST + (255,), width=5)
        d.ellipse([cx + px - 5, ty - 72, cx + px + 5, ty - 62], fill=(60, 54, 40, 255))
    # rust + grime streaks
    for i in range(6):
        rx = cx - 50 + i * 20
        d.line([(rx, ty - 50), (rx + 3, ty + 20)], fill=ERUST + (130,), width=4)
    # head sunk between pauldrons: heavy mask with glowing VISOR SLIT
    hx, hy = cx + 6, ty - 86
    d.rectangle([hx - 15, hy + 8, hx + 15, ty - 66], fill=(16, 14, 12, 255))
    im.alpha_composite(part(ell_mask(hx, hy, 22, 23), (hx - 26, hy - 27, hx + 26, hy + 27), EMASK, EMASK_D))
    d.rectangle([hx - 14, hy - 6, hx + 14, hy + 6], fill=(8, 14, 8, 255))  # visor slit
    d.rectangle([hx - 12, hy - 4, hx + 12, hy + 4], fill=(255, 150, 60, 255))
    add_glow(im, hx, hy, 26, (255, 150, 60), 70)
    d.line([(hx - 18, hy - 18), (hx - 8, hy - 10)], fill=(120, 118, 112, 255), width=2)
    rim_stroke(im, [(cx + 64, ty - 66), (cx + 58, ty + 60)], (255, 220, 170), 3, 170)
    return ty

def draw_bulwark(im, ph, mode="walk"):
    cx = 96
    d = ImageDraw.Draw(im)
    if mode == "attack0":
        ty = _bulwark_body(im, cx, raise_f=1, glow_boost=70)
        for ax in (-70, 70):
            d.line([(cx + ax * 0.7, ty - 50), (cx + ax, ty - 150)], fill=(70, 60, 34, 255), width=40)
            d.rectangle([cx + ax - 26, ty - 178, cx + ax + 26, ty - 132], fill=EPLATE + (255,),
                        outline=EPLATE_D + (255,), width=4)
            d.line([(cx + ax - 20, ty - 155), (cx + ax + 20, ty - 150)], fill=ECRACK + (255,), width=5)
        add_glow(im, cx, ty - 140, 70, ECRACK, 80)
    elif mode == "attack1":
        ty = _bulwark_body(im, cx, stomp=1)
        for ax in (-72, 72):
            d.line([(cx + ax * 0.7, ty - 50), (cx + ax, ty + 78)], fill=(70, 60, 34, 255), width=44)
            d.rectangle([cx + ax - 28, ty + 48, cx + ax + 28, ty + 100], fill=EPLATE_D + (255,),
                        outline=EPLATE + (255,), width=4)
        for r, a in ((90, 120), (125, 80), (160, 45)):
            d.ellipse([cx - r, 240 - r * 0.32, cx + r, 240 + r * 0.32], outline=ECRACK + (a,), width=7)
        for i in range(8):
            dx2 = cx - 90 + i * 26
            dy2 = 200 - (i * 37 % 60)
            d.polygon([(dx2, dy2), (dx2 + 12, dy2 + 4), (dx2 + 4, dy2 + 14)], fill=(110, 96, 52, 255))
        add_glow(im, cx, 225, 80, ECRACK, 100)
    else:
        rock = [0, 6, 0, -6][ph]
        ty = _bulwark_body(im, cx)
        for ax, fwd in ((-66, 1), (66, -1)):
            sw = [0, 14, 0, -14][ph] * fwd
            d.line([(cx + ax * 0.75, ty - 40), (cx + ax + sw, ty + 60)], fill=(70, 60, 34, 255), width=38)
            d.rectangle([cx + ax + sw - 24, ty + 34, cx + ax + sw + 24, ty + 82], fill=EPLATE_D + (255,))
        for i in range(4):
            dx2 = cx - 60 + i * 40 + rock
            d.ellipse([dx2 - 14, 226, dx2 + 14, 246], fill=(120, 115, 105, 90))
    grain(im, (cx - 70, 40, cx + 70, 242), 10)
    return im

def draw_bulwark_death(im, stage):
    cx, d = 96, ImageDraw.Draw(im)
    if stage == 0:
        im.alpha_composite(part(poly_mask([(cx - 58, 236), (cx - 48, 130), (cx + 52, 134), (cx + 60, 236)]),
                                (cx - 62, 126, cx + 64, 240), (70, 62, 34), (48, 42, 24)))
        im.alpha_composite(part(ell_mask(cx + 6, 104, 22, 23), (cx - 20, 78, cx + 32, 130), EMASK, EMASK_D))
        d.rectangle([cx - 6, 98, cx + 18, 108], fill=(60, 30, 10, 255))  # dead visor
        d.line([(cx - 30, 160), (cx + 30, 170)], fill=ECRACK + (255,), width=5)
        add_glow(im, cx, 165, 44, ECRACK, 70)
    else:
        im.alpha_composite(part(poly_mask([(cx - 80, 236), (cx - 60, 190), (cx + 70, 196), (cx + 80, 236)]),
                                (cx - 84, 186, cx + 84, 240), (56, 50, 28), (36, 32, 20)))
        for i in range(3):
            px2 = cx - 50 + i * 48
            d.rectangle([px2 - 16, 200 + (i % 2) * 10, px2 + 16, 224 + (i % 2) * 10], fill=EPLATE_D + (255,))
        add_glow(im, cx, 220, 56, ECRACK, 80)
    return im

# ================= GENERATE (same 48 filenames) =================
def gen():
    n = 0
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
    for tname, wfn, dfn in (("shambler", draw_rotwalker, draw_rotwalker_death),
                            ("runner", draw_skitter, draw_skitter_death),
                            ("brute", draw_bulwark, draw_bulwark_death)):
        for ph in range(4):
            im = new(); wfn(im, ph, "walk"); save(im, f"e_{tname}_walk_{ph}.png"); n += 1
        for i, m in enumerate(("attack0", "attack1")):
            im = new(); wfn(im, 0, m); save(im, f"e_{tname}_attack_{i}.png"); n += 1
        for s in (0, 1):
            im = new(); dfn(im, s); save(im, f"e_{tname}_death_{s}.png"); n += 1
    print(f"generated {n} v4 frames")

if __name__ == "__main__":
    gen()
