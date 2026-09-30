#!/usr/bin/env python3
"""CARRIER character art v5 — CLEAN HAZMAT redesign (Tbandz: "they looking kinda crazy").

Fixes vs v4:
- Real proportions: head ~1/4 of body height (v4 hood was a giant pumpkin).
- Player mask: ONE glowing visor (welding-visor style) + filter canister.
  No more ghost-face two-eyes look.
- Vial band is horizontal across the chest with 2 small vials, not diagonal
  green teeth.
- Suit has LEGS + boots, not a dress triangle.
- Enemies: same containment design language, cleaner silhouettes, smaller
  claws, readable visor slits, less noise.

Same 48 filenames as the live build (drop-in replacement). Run from carrier root:
    python3 assets-src/char_factory_v5.py
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
STEEL, STEEL_D = V3.STEEL, V3.STEEL_D
VIAL = V3.VIAL

# ---------------- palette ----------------
HAZ_Y   = (205, 168, 52)    # suit yellow
HAZ_YM  = (168, 134, 40)    # mid
HAZ_YD  = (122, 96, 30)     # dark folds
HAZ_OL  = (90, 72, 24)      # deep shadow
PATCH   = (96, 88, 66)      # repair patch
PATCH_D = (66, 60, 44)
RUBBER  = (40, 38, 36)      # mask / gloves / boots
RUBBER_D= (24, 22, 20)
SEAM    = (110, 88, 30)     # stitched seams
STRAP   = (70, 62, 44)      # webbing
STRAP_D = (48, 42, 30)
VISOR_D = (8, 22, 12)       # visor socket
GRIME   = (70, 62, 40)
# enemy tints
ESUIT   = (150, 124, 44)    # corrupted containment yellow
ESUIT_D = (104, 84, 30)
EFLESH  = (52, 60, 40)      # exposed under-suit
AMBER   = (255, 170, 60)    # runner visor
ORANGE  = (255, 120, 40)    # brute visor
RUST    = (120, 66, 30)

CX = 96

# =====================================================================
# PLAYER — clean hazmat carrier
# =====================================================================
def _hood_mask(d, im, cx, cy, facing=1, glow_boost=0):
    """Small suit hood + rubber gas mask with ONE glowing visor."""
    # hood (modest size)
    im.alpha_composite(part(ell_mask(cx, cy, 27, 29), (cx - 31, cy - 33, cx + 31, cy + 33), HAZ_Y, HAZ_YM))
    # hood back point
    d.polygon([(cx - 8 * facing, cy - 26), (cx + 28 * facing, cy - 20), (cx + 12 * facing, cy - 4)],
              fill=HAZ_YM + (255,))
    # mask body (front)
    mx = cx + 10 * facing
    im.alpha_composite(part(ell_mask(mx, cy + 8, 17, 20), (mx - 20, cy - 14, mx + 20, cy + 30), RUBBER, RUBBER_D))
    # SINGLE visor: wide rounded rectangle, glowing green
    vx0, vy0, vx1, vy1 = mx - 13, cy - 2, mx + 13, cy + 12
    d.rounded_rectangle([vx0, vy0, vx1, vy1], radius=6, fill=VISOR_D + (255,))
    d.rounded_rectangle([vx0 + 3, vy0 + 3, vx1 - 3, vy1 - 3], radius=4, fill=EYE_G + (255,))
    add_glow(im, (vx0 + vx1) / 2, (vy0 + vy1) / 2, 22, EYE_G, 80 + glow_boost)
    # filter canister on cheek
    d.ellipse([mx + 6 * facing - 7, cy + 14, mx + 6 * facing + 7, cy + 28],
              fill=RUBBER_D + (255,), outline=(88, 86, 80, 255), width=2)
    # mask straps
    d.line([(cx - 22 * facing, cy - 10), (mx - 14, cy - 4)], fill=STRAP_D + (255,), width=4)
    d.line([(cx - 22 * facing, cy + 18), (mx - 14, cy + 14)], fill=STRAP_D + (255,), width=4)
    # rim light on hood
    rim_stroke(im, [(cx + 24 * facing, cy - 20), (cx + 27 * facing, cy + 8)], RIM, 3, 210)


def _suit_torso(im, d, cx, top_y, hip_y, half_w, sway=0, back=0, lean=0):
    """Tapered torso with center seam, belt, fold shading."""
    pts = [(cx - half_w + back, top_y), (cx + half_w + back, top_y),
           (cx + half_w * 0.82 + sway, hip_y), (cx - half_w * 0.82 + sway, hip_y)]
    im.alpha_composite(part(poly_mask(pts), (cx - half_w - 8, top_y - 6, cx + half_w + 8, hip_y + 6),
                            HAZ_Y, HAZ_YD))
    # fold shadows
    for fx, fw in ((-half_w * 0.55, 7), (0, 8), (half_w * 0.55, 7)):
        x = cx + fx + sway * 0.4 + back
        d.polygon([(x - fw, top_y + 10), (x + fw, top_y + 10),
                   (x + fw * 1.4 + sway * 0.4, hip_y), (x - fw * 1.4 + sway * 0.4, hip_y)],
                  fill=HAZ_OL + (140,))
    # center zipper seam
    d.line([(cx + back, top_y + 8), (cx + back + sway * 0.4, hip_y - 4)], fill=SEAM + (220,), width=3)
    # belt
    d.rectangle([cx - half_w * 0.86 + sway * 0.5, hip_y - 10, cx + half_w * 0.86 + sway * 0.5, hip_y + 2],
                fill=STRAP_D + (255,))
    d.rectangle([cx - 8, hip_y - 10, cx + 8, hip_y + 2], fill=(90, 88, 82, 255))  # buckle
    # one subtle grime blotch
    d.ellipse([cx - half_w * 0.5, hip_y - 34, cx - half_w * 0.5 + 18, hip_y - 16], fill=GRIME + (70,))
    rim_stroke(im, [(cx + half_w + back, top_y + 4), (cx + half_w * 0.8 + sway, hip_y - 12)], RIM, 3, 200)


def _vial_band(im, d, cx, y, wdt=46):
    """Horizontal chest band with 2 small vials (not diagonal teeth)."""
    d.rectangle([cx - wdt / 2, y - 7, cx + wdt / 2, y + 7], fill=STRAP + (255,),
                outline=STRAP_D + (255,), width=2)
    for vx in (cx - 13, cx + 13):
        d.rectangle([vx - 5, y - 13, vx + 5, y + 5], fill=(18, 36, 26, 255),
                    outline=(80, 78, 72, 255), width=2)
        d.rectangle([vx - 3, y - 6, vx + 3, y + 3], fill=VIAL + (255,))
    add_glow(im, cx, y, 16, VIAL, 45)


def _leg(d, x, hip_y, foot_y, step=0):
    d.rectangle([x - 11, hip_y, x + 11, foot_y + step], fill=HAZ_YM + (255,),
                outline=HAZ_YD + (255,), width=2)
    # boot
    d.rectangle([x - 12, foot_y - 14 + step, x + 12, foot_y + step], fill=RUBBER + (255,))
    d.ellipse([x - 12, foot_y - 8 + step, x + 12, foot_y + 4 + step], fill=RUBBER_D + (255,))


def _arm_to(d, im, shx, shy, hx, hy, wdt=15):
    d.line([(shx, shy), ((shx + hx) / 2, (shy + hy) / 2 + 3), (hx, hy)], fill=HAZ_YM + (255,), width=wdt + 5)
    d.line([(shx, shy), ((shx + hx) / 2, (shy + hy) / 2 + 3), (hx, hy)], fill=HAZ_Y + (255,), width=wdt)
    # glove
    d.ellipse([hx - 9, hy - 7, hx + 9, hy + 9], fill=RUBBER + (255,))


def draw_player_side(im, ph, mode="idle"):
    cx, d = CX, ImageDraw.Draw(im)
    bob = [0, -5, 0, -5][ph] if mode == "walk" else 0
    sway = [0, 6, 0, -6][ph] if mode == "walk" else 0
    lunge = 18 if mode == "attack1" else (8 if mode == "attack2" else 0)
    back = -10 if mode == "hurt" else 0
    if mode in ("death0", "death1"):
        return draw_player_death(im, 0 if mode == "death0" else 1)
    top_y, hip_y, foot_y = 84 + bob, 168 + bob, 238
    # legs (walk cycle)
    if mode == "walk":
        _leg(d, cx - 15, hip_y, foot_y, [0, -12, 0, -12][ph])
        _leg(d, cx + 15, hip_y, foot_y, [0, -12, 0, -12][(ph + 2) % 4])
    else:
        _leg(d, cx - 15, hip_y, foot_y); _leg(d, cx + 15, hip_y, foot_y)
    _suit_torso(im, d, cx, top_y, hip_y, 34, sway, back)
    _vial_band(im, d, cx + back, 118 + bob)
    # backpack canister behind shoulder
    d.rectangle([cx - 46 + back, 96 + bob, cx - 32 + back, 142 + bob], fill=RUBBER_D + (255,),
                outline=(80, 78, 72, 255), width=2)
    d.line([(cx - 39 + back, 96 + bob), (cx - 39 + back, 88 + bob)], fill=(80, 78, 72, 255), width=4)
    _hood_mask(d, im, cx + back, 50 + bob, 1, glow_boost=60 if mode.startswith("attack") else 0)
    # right arm -> blade hand
    hx, hy = cx + 34 + back + lunge, 148 + bob
    _arm_to(d, im, cx + 12 + back, 108 + bob, hx, hy)
    gb = 60 if mode == "attack1" else 0
    if mode == "idle":
        blade_shape(d, hx, hy, hx + 8, hy + 72, 10)
    elif mode == "walk":
        blade_shape(d, hx, hy, hx + 10, hy + 70, 10)
    elif mode == "attack0":
        blade_shape(d, hx - 4, hy - 8, hx - 46, hy - 70, 11)
        add_glow(im, hx - 34, hy - 52, 28, EYE_G, 60)
    elif mode == "attack1":
        blade_shape(d, hx - 24, hy - 16, hx + 74, hy - 30, 12)
        slash_arc(im, hx + 12, hy - 8, 58, 104, -70, 40, (190, 255, 200), 170)
        slash_arc(im, hx + 12, hy - 8, 38, 64, -60, 30, EYE_G, 130)
        add_glow(im, hx + 40, hy - 26, 42, (200, 255, 210), 80)
    elif mode == "attack2":
        blade_shape(d, hx + 4, hy + 4, hx + 48, hy + 48, 10)
    elif mode == "hurt":
        blade_shape(d, hx - 6, hy, hx + 2, hy + 64, 10)
        rim_stroke(im, [(cx - 34 + back, top_y), (cx - 50 + back, hip_y)], (255, 90, 90), 4, 220)
    grain(im, (cx - 50, top_y, cx + 50, foot_y), 10)
    return im


def draw_player_down(im, ph, mode="idle"):
    cx, d = CX, ImageDraw.Draw(im)
    bob = [0, -5, 0, -5][ph] if mode == "walk" else 0
    if mode in ("death0", "death1"):
        return draw_player_death(im, 0 if mode == "death0" else 1)
    top_y, hip_y, foot_y = 86 + bob, 170 + bob, 238
    if mode == "walk":
        _leg(d, cx - 15, hip_y, foot_y, [0, -12, 0, -12][ph])
        _leg(d, cx + 15, hip_y, foot_y, [0, -12, 0, -12][(ph + 2) % 4])
    else:
        _leg(d, cx - 15, hip_y, foot_y); _leg(d, cx + 15, hip_y, foot_y)
    _suit_torso(im, d, cx, top_y, hip_y, 36, 0, 0)
    _vial_band(im, d, cx, 120 + bob)
    # front-facing hood: hood ring + mask centered
    im.alpha_composite(part(ell_mask(cx, 50 + bob, 30, 32), (cx - 34, 14 + bob, cx + 34, 86 + bob), HAZ_Y, HAZ_YM))
    im.alpha_composite(part(ell_mask(cx, 54 + bob, 18, 21), (cx - 21, 30 + bob, cx + 21, 79 + bob), RUBBER, RUBBER_D))
    d.rounded_rectangle([cx - 13, 44 + bob, cx + 13, 58 + bob], radius=6, fill=VISOR_D + (255,))
    d.rounded_rectangle([cx - 10, 47 + bob, cx + 10, 55 + bob], radius=4, fill=EYE_G + (255,))
    add_glow(im, cx, 52 + bob, 22, EYE_G, 80)
    # filter canister below visor
    d.rounded_rectangle([cx - 7, 62 + bob, cx + 7, 74 + bob], radius=3, fill=RUBBER_D + (255,),
                        outline=(88, 86, 80, 255), width=2)
    # arms at sides, blade in right hand
    _arm_to(d, im, cx - 26, 108 + bob, cx - 32, 152 + bob)
    _arm_to(d, im, cx + 26, 108 + bob, cx + 34, 150 + bob)
    if mode == "walk":
        blade_shape(d, cx + 34, 152 + bob, cx + 40, 218 + bob, 10)
    else:
        blade_shape(d, cx + 34, 152 + bob, cx + 38, 216 + bob, 10)
    grain(im, (cx - 52, top_y, cx + 52, foot_y), 10)
    return im


def draw_player_up(im, ph, mode="idle"):
    cx, d = CX, ImageDraw.Draw(im)
    bob = [0, -5, 0, -5][ph] if mode == "walk" else 0
    if mode in ("death0", "death1"):
        return draw_player_death(im, 0 if mode == "death0" else 1)
    top_y, hip_y, foot_y = 86 + bob, 170 + bob, 238
    if mode == "walk":
        _leg(d, cx - 15, hip_y, foot_y, [0, -12, 0, -12][ph])
        _leg(d, cx + 15, hip_y, foot_y, [0, -12, 0, -12][(ph + 2) % 4])
    else:
        _leg(d, cx - 15, hip_y, foot_y); _leg(d, cx + 15, hip_y, foot_y)
    _suit_torso(im, d, cx, top_y, hip_y, 36, 0, 0)
    # backpack canister center-back (seen from behind)
    d.rounded_rectangle([cx - 14, 92 + bob, cx + 14, 150 + bob], radius=6, fill=RUBBER_D + (255,),
                        outline=(80, 78, 72, 255), width=2)
    d.line([(cx, 92 + bob), (cx, 84 + bob)], fill=(80, 78, 72, 255), width=4)
    # back of hood: plain hood, no mask
    im.alpha_composite(part(ell_mask(cx, 50 + bob, 30, 32), (cx - 34, 14 + bob, cx + 34, 86 + bob), HAZ_Y, HAZ_YM))
    d.polygon([(cx - 20, 30 + bob), (cx + 20, 30 + bob), (cx, 62 + bob)], fill=HAZ_YD + (255,))
    # hood seam
    d.arc([cx - 24, 26 + bob, cx + 24, 74 + bob], 200, 340, fill=SEAM + (200,), width=2)
    _arm_to(d, im, cx - 26, 108 + bob, cx - 32, 152 + bob)
    _arm_to(d, im, cx + 26, 108 + bob, cx + 34, 150 + bob)
    blade_shape(d, cx + 34, 152 + bob, cx + 38, 216 + bob, 10)
    grain(im, (cx - 52, top_y, cx + 52, foot_y), 10)
    return im


def draw_player_death(im, stage):
    cx, d = CX, ImageDraw.Draw(im)
    if stage == 0:
        # crumpled to knees
        im.alpha_composite(part(poly_mask([(cx - 40, 238), (cx - 30, 150), (cx + 34, 152), (cx + 42, 238)]),
                                (cx - 44, 146, cx + 46, 242), HAZ_YM, HAZ_YD))
        im.alpha_composite(part(ell_mask(cx + 4, 128, 26, 28), (cx - 24, 98, cx + 34, 158), HAZ_Y, HAZ_YM))
        d.rounded_rectangle([cx - 6, 120, cx + 18, 132], radius=5, fill=VISOR_D + (255,))
        d.rounded_rectangle([cx - 3, 123, cx + 15, 129], radius=3, fill=(40, 90, 60, 255))  # visor dimming
        blade_shape(d, cx + 40, 190, cx + 78, 226, 10)
    else:
        # flat on ground, fading
        im.alpha_composite(part(poly_mask([(cx - 78, 238), (cx - 60, 196), (cx + 70, 200), (cx + 78, 238)]),
                                (cx - 82, 192, cx + 82, 242), HAZ_YD, (60, 48, 20)))
        im.alpha_composite(part(ell_mask(cx - 58, 214, 24, 18), (cx - 84, 194, cx - 32, 236), HAZ_YM, HAZ_YD))
        add_glow(im, cx, 220, 60, VEIN, 70)
    return im


# =====================================================================
# ENEMIES — clean containment-corrupted designs
# =====================================================================
def _resp_snout(d, im, hx, hy, facing=1):
    """Respirator snout: cylinder + filter disc."""
    sx = hx + 14 * facing
    d.rectangle([hx, hy - 8, sx, hy + 8], fill=RUBBER + (255,))
    d.ellipse([sx - 8, hy - 10, sx + 8, hy + 10], fill=RUBBER_D + (255,),
              outline=(88, 86, 80, 255), width=2)


def draw_rotwalker(im, ph, mode="walk"):
    """Shambler: slumped burst containment suit, respirator snout, glowing ribs."""
    cx, d = CX, ImageDraw.Draw(im)
    lurch = [0, 8, 0, -8][ph] if mode == "walk" else 0
    lunge = 14 if mode.startswith("attack") else 0
    if mode.startswith("death"):
        return draw_rotwalker_death(im, 0 if mode == "death0" else 1)
    head_cy, hip_y, foot_y = 84, 170, 238
    # legs: wide stance
    d.rectangle([cx - 34 + lurch * 0.3, hip_y, cx - 12 + lurch * 0.3, foot_y], fill=ESUIT_D + (255,))
    d.rectangle([cx + 12 + lurch * 0.3, hip_y, cx + 34 + lurch * 0.3, foot_y], fill=ESUIT_D + (255,))
    d.ellipse([cx - 34 + lurch * 0.3, foot_y - 10, cx - 8 + lurch * 0.3, foot_y + 4], fill=RUBBER_D + (255,))
    d.ellipse([cx + 8 + lurch * 0.3, foot_y - 10, cx + 34 + lurch * 0.3, foot_y + 4], fill=RUBBER_D + (255,))
    # torso: burst suit, jagged hem
    pts = [(cx - 34, 100), (cx + 36, 100), (cx + 44 + lurch, hip_y), (cx - 40 + lurch, hip_y)]
    im.alpha_composite(part(poly_mask(pts), (cx - 48, 96, cx + 48, hip_y + 4), ESUIT, ESUIT_D))
    # torn hem strips
    for tx, tl in ((-30, 12), (-8, 18), (16, 10), (34, 15)):
        d.polygon([(cx + tx, hip_y - 4), (cx + tx + 10, hip_y - 4),
                   (cx + tx + 5, hip_y + tl)], fill=ESUIT_D + (255,))
    # burst chest: dark opening with glowing rib slats
    d.rounded_rectangle([cx - 20 + lurch * 0.5, 112, cx + 22 + lurch * 0.5, 160], radius=8,
                        fill=(16, 20, 14, 255))
    for i, ry in enumerate((120, 132, 144, 155)):
        d.rounded_rectangle([cx - 16 + lurch * 0.5, ry, cx + 18 + lurch * 0.5, ry + 5], radius=2,
                            fill=EYE_G + (255,))
    add_glow(im, cx + lurch * 0.5, 138, 30, EYE_G, 90)
    # head: dark rubber mask, small green visor lenses, respirator snout
    im.alpha_composite(part(ell_mask(cx + lurch * 0.4, head_cy, 21, 23),
                            (cx - 25, head_cy - 27, cx + 25, head_cy + 27), RUBBER, RUBBER_D))
    for ex in (cx - 7, cx + 9):
        d.ellipse([ex - 5, head_cy - 8, ex + 5, head_cy + 2], fill=VISOR_D + (255,))
        d.ellipse([ex - 3, head_cy - 6, ex + 3, head_cy], fill=EYE_G + (255,))
    add_glow(im, cx + lurch * 0.4, head_cy - 4, 18, EYE_G, 60)
    _resp_snout(d, im, cx + 12 + lurch * 0.4, head_cy + 12)
    # hanging arms with small claws
    for s in (-1, 1):
        ax = cx + s * 38 + lurch * 0.5
        d.line([(ax, 110), (ax + s * 4, 168)], fill=ESUIT_D + (255,), width=13)
        d.line([(ax, 110), (ax + s * 4, 168)], fill=ESUIT + (255,), width=8)
        hx2, hy2 = ax + s * 4, 176
        d.ellipse([hx2 - 8, hy2 - 6, hx2 + 8, hy2 + 8], fill=RUBBER + (255,))
        for ci in range(3):
            d.line([(hx2 - 5 + ci * 5, hy2 + 6), (hx2 - 7 + ci * 5 + lunge * 0.3, hy2 + 20)],
                   fill=STEEL + (255,), width=3)
    if mode.startswith("attack"):
        slash_arc(im, cx + 52 + lunge, 150, 30, 52, -40, 60, (190, 255, 200), 120)
    grain(im, (cx - 48, 96, cx + 48, foot_y), 10)
    rim_stroke(im, [(cx + 36, 104), (cx + 44 + lurch, hip_y - 10)], RIM_DIM, 3, 140)
    return im


def draw_rotwalker_death(im, stage):
    cx, d = CX, ImageDraw.Draw(im)
    if stage == 0:
        im.alpha_composite(part(poly_mask([(cx - 50, 238), (cx - 40, 150), (cx + 44, 154), (cx + 52, 238)]),
                                (cx - 54, 146, cx + 56, 242), ESUIT_D, (60, 48, 22)))
        im.alpha_composite(part(ell_mask(cx, 132, 20, 22), (cx - 24, 108, cx + 24, 156), RUBBER, RUBBER_D))
        d.rectangle([cx - 12, 126, cx + 12, 134], fill=(40, 90, 60, 255))
    else:
        im.alpha_composite(part(poly_mask([(cx - 74, 238), (cx - 56, 200), (cx + 66, 204), (cx + 74, 238)]),
                                (cx - 78, 196, cx + 78, 242), (56, 48, 26), (36, 32, 20)))
        add_glow(im, cx, 220, 50, EYE_G, 60)
    return im


def draw_skitter(im, ph, mode="walk"):
    """Runner: lean shredded containment suit, amber visor slit, spine glow."""
    cx, d = CX, ImageDraw.Draw(im)
    lean = [0, 10, 0, 10][ph] if mode == "walk" else 0
    coil = [0, -8, 0, 8][ph] if mode == "walk" else 0
    lunge = 16 if mode.startswith("attack") else 0
    if mode.startswith("death"):
        return draw_skitter_death(im, 0 if mode == "death0" else 1)
    head_cy, hip_y, foot_y = 76 + coil, 168, 238
    # bent legs (crouched runner)
    for s in (-1, 1):
        lx = cx + s * 16
        d.line([(lx, hip_y), (lx + s * 10, 204), (lx - s * 4 + lean * 0.4, foot_y)], fill=ESUIT_D + (255,), width=13)
        d.ellipse([lx - s * 4 + lean * 0.4 - 9, foot_y - 8, lx - s * 4 + lean * 0.4 + 9, foot_y + 4],
                  fill=RUBBER_D + (255,))
    # slim torso leaning forward
    pts = [(cx - 22, 96 + coil), (cx + 24, 96 + coil),
           (cx + 30 + lean, hip_y), (cx - 26 + lean, hip_y)]
    im.alpha_composite(part(poly_mask(pts), (cx - 34, 92, cx + 36, hip_y + 4), ESUIT, ESUIT_D))
    # shredded strips at hem
    for tx, tl in ((-20, 16), (-2, 22), (16, 14)):
        d.polygon([(cx + tx + lean, hip_y - 2), (cx + tx + 8 + lean, hip_y - 2),
                   (cx + tx + 4 + lean, hip_y + tl)], fill=ESUIT_D + (255,))
    # spine glow dots down the back
    for i, sy in enumerate((104, 120, 136, 152)):
        d.ellipse([cx - 24 + lean * 0.6 - 4, sy + coil * 0.5 - 4, cx - 24 + lean * 0.6 + 4, sy + coil * 0.5 + 4],
                  fill=EYE_G + (255,))
    add_glow(im, cx - 24 + lean * 0.6, 128 + coil * 0.5, 20, EYE_G, 60)
    # head: torn hood, amber visor SLIT
    im.alpha_composite(part(ell_mask(cx + lean * 0.5, head_cy, 18, 20),
                            (cx - 22, head_cy - 24, cx + 22, head_cy + 24), ESUIT_D, (80, 64, 26)))
    d.rounded_rectangle([cx + lean * 0.5 - 12, head_cy - 5, cx + lean * 0.5 + 12, head_cy + 5],
                        radius=4, fill=VISOR_D + (255,))
    d.rounded_rectangle([cx + lean * 0.5 - 9, head_cy - 2, cx + lean * 0.5 + 9, head_cy + 2],
                        radius=2, fill=AMBER + (255,))
    add_glow(im, cx + lean * 0.5, head_cy, 16, AMBER, 70)
    _resp_snout(d, im, cx + 8 + lean * 0.5, head_cy + 12)
    # long arms, small dark claws
    for s in (-1, 1):
        ax = cx + s * 26 + lean * 0.5
        d.line([(ax, 104 + coil), (ax + s * 8 + lunge * 0.4, 168)], fill=ESUIT_D + (255,), width=11)
        hx2, hy2 = ax + s * 8 + lunge * 0.4, 174
        d.ellipse([hx2 - 7, hy2 - 5, hx2 + 7, hy2 + 7], fill=RUBBER + (255,))
        for ci in range(3):
            d.line([(hx2 - 4 + ci * 4, hy2 + 5), (hx2 - 6 + ci * 4, hy2 + 17)], fill=(70, 68, 64, 255), width=3)
    if mode.startswith("attack"):
        slash_arc(im, cx + 44 + lunge, 150, 28, 50, -50, 50, (255, 220, 150), 120)
    grain(im, (cx - 36, 92, cx + 40, foot_y), 10)
    rim_stroke(im, [(cx + 24, 100 + coil), (cx + 30 + lean, hip_y - 8)], RIM_DIM, 3, 140)
    return im


def draw_skitter_death(im, stage):
    cx, d = CX, ImageDraw.Draw(im)
    if stage == 0:
        im.alpha_composite(part(poly_mask([(cx - 44, 238), (cx - 34, 160), (cx + 38, 164), (cx + 46, 238)]),
                                (cx - 48, 156, cx + 50, 242), ESUIT_D, (60, 48, 22)))
        im.alpha_composite(part(ell_mask(cx, 142, 17, 19), (cx - 21, 121, cx + 21, 163), ESUIT_D, (80, 64, 26)))
        d.rectangle([cx - 9, 138, cx + 9, 143], fill=(90, 60, 30, 255))
    else:
        im.alpha_composite(part(poly_mask([(cx - 68, 238), (cx - 50, 206), (cx + 60, 210), (cx + 68, 238)]),
                                (cx - 72, 202, cx + 72, 242), (56, 48, 26), (36, 32, 20)))
        add_glow(im, cx, 222, 44, EYE_G, 50)
    return im


def _armor_plate(d, x0, y0, x1, y1):
    d.rounded_rectangle([x0, y0, x1, y1], radius=5, fill=(168, 140, 60, 255),
                        outline=(110, 88, 40, 255), width=2)
    for rx, ry in ((x0 + 6, y0 + 6), (x1 - 6, y0 + 6), (x0 + 6, y1 - 6), (x1 - 6, y1 - 6)):
        d.ellipse([rx - 2, ry - 2, rx + 2, ry + 2], fill=(90, 72, 34, 255))
    # rust streak
    d.line([(x0 + (x1 - x0) * 0.6, y0 + 4), (x0 + (x1 - x0) * 0.55, y1 - 4)], fill=RUST + (160,), width=3)


def draw_bulwark(im, ph, mode="walk"):
    """Brute: yellowed containment armor, orange visor slit, plated fists."""
    cx, d = CX, ImageDraw.Draw(im)
    rock = [0, 6, 0, -6][ph] if mode == "walk" else 0
    slam = 12 if mode.startswith("attack") else 0
    if mode.startswith("death"):
        return draw_bulwark_death(im, 0 if mode == "death0" else 1)
    head_cy, hip_y, foot_y = 62, 176, 240
    # legs: thick armored
    for s in (-1, 1):
        lx = cx + s * 30
        d.rectangle([lx - 16, hip_y, lx + 16, foot_y], fill=(110, 92, 44, 255),
                    outline=(80, 66, 32, 255), width=2)
        d.rectangle([lx - 17, foot_y - 14, lx + 17, foot_y], fill=RUBBER + (255,))
    # wide torso
    pts = [(cx - 52, 92), (cx + 52, 92), (cx + 56 + rock, hip_y), (cx - 56 + rock, hip_y)]
    im.alpha_composite(part(poly_mask(pts), (cx - 60, 88, cx + 60, hip_y + 4), ESUIT, ESUIT_D))
    # chest armor plates
    for i, py in enumerate((104, 132, 160)):
        _armor_plate(d, cx - 34 + rock * 0.4, py, cx + 34 + rock * 0.4, py + 22)
    # faint infection crack on one plate (subtle)
    d.line([(cx - 20 + rock * 0.4, 108), (cx - 8 + rock * 0.4, 122)], fill=VEIN + (110,), width=2)
    add_glow(im, cx - 14 + rock * 0.4, 115, 12, VEIN, 30)
    # big shoulder pauldrons
    for s in (-1, 1):
        px = cx + s * 52 + rock * 0.5
        im.alpha_composite(part(ell_mask(px, 100, 24, 22), (px - 28, 74, px + 28, 126),
                                (168, 140, 60), (110, 88, 40)))
        d.arc([px - 20, 82, px + 20, 118], 180, 360, fill=(200, 170, 90, 120), width=2)
    # head: armored collar, dark faceplate, ORANGE visor slit
    im.alpha_composite(part(ell_mask(cx, head_cy, 22, 24), (cx - 26, head_cy - 28, cx + 26, head_cy + 28),
                            (120, 100, 48), (84, 70, 34)))
    d.rounded_rectangle([cx - 15, head_cy - 6, cx + 15, head_cy + 6], radius=5, fill=VISOR_D + (255,))
    d.rounded_rectangle([cx - 12, head_cy - 3, cx + 12, head_cy + 3], radius=3, fill=ORANGE + (255,))
    add_glow(im, cx, head_cy, 20, ORANGE, 80)
    # plated arms with fists
    for s in (-1, 1):
        ax = cx + s * 62 + rock * 0.6
        d.line([(ax, 116), (ax + s * 6, 190 + slam)], fill=(110, 92, 44, 255), width=30)
        d.line([(ax, 116), (ax + s * 6, 190 + slam)], fill=(140, 116, 56, 255), width=20)
        d.rectangle([ax + s * 6 - 15, 186 + slam, ax + s * 6 + 15, 214 + slam], fill=RUBBER_D + (255,),
                    outline=(80, 78, 72, 255), width=2)
    grain(im, (cx - 70, 40, cx + 70, foot_y), 10)
    return im


def draw_bulwark_death(im, stage):
    cx, d = CX, ImageDraw.Draw(im)
    if stage == 0:
        im.alpha_composite(part(poly_mask([(cx - 56, 238), (cx - 46, 140), (cx + 50, 144), (cx + 58, 238)]),
                                (cx - 60, 136, cx + 62, 242), (100, 84, 40), (60, 52, 28)))
        im.alpha_composite(part(ell_mask(cx, 118, 20, 22), (cx - 24, 94, cx + 24, 142), (120, 100, 48), (84, 70, 34)))
        d.rectangle([cx - 12, 114, cx + 12, 120], fill=(80, 40, 20, 255))  # dead visor
    else:
        im.alpha_composite(part(poly_mask([(cx - 78, 238), (cx - 58, 196), (cx + 68, 200), (cx + 78, 238)]),
                                (cx - 82, 192, cx + 82, 242), (56, 50, 28), (36, 32, 20)))
        for i in range(3):
            px2 = cx - 48 + i * 46
            d.rectangle([px2 - 15, 204 + (i % 2) * 8, px2 + 15, 226 + (i % 2) * 8], fill=(84, 70, 34, 255,))
        add_glow(im, cx, 220, 52, VEIN, 60)
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
    print(f"generated {n} v5 frames")


if __name__ == "__main__":
    gen()
