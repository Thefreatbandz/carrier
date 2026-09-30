#!/usr/bin/env python3
"""CARRIER character art v6 — player hero pass (Tbandz: "make the character
look way more better but so choppy").

Player-only upgrades over v5 (enemies reuse v5 frames 1:1):
- 6-phase walk cycle with sinusoidal leg/bob/sway -> visibly smoother motion.
- Richer suit: highlight panel, deeper fold shadows, belt pouch.
- Better boots: tread lines + ankle cuff rings.
- Gloves with wrist cuffs + knuckle seams.
- Mask: visor scanline, stronger rim light, strap buckles.
- Backpack canister: valve cap + hose to the shoulder.

Generates the same 48 filenames as v5 PLUS 6 new walk frames
(p_{down,up,side}_walk_4/5.png) = 54 total. Run from carrier root:
    python3 assets-src/char_factory_v6.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
import char_factory_v5 as V5
from char_factory_v3 import (new, save, part, poly_mask, ell_mask, add_glow,
                             grain, rim_stroke, blade_shape, slash_arc, breathe)
from PIL import Image, ImageDraw
import math

# ---- palette (from v5) ----
HAZ_Y, HAZ_YM, HAZ_YD, HAZ_OL = V5.HAZ_Y, V5.HAZ_YM, V5.HAZ_YD, V5.HAZ_OL
PATCH, PATCH_D = V5.PATCH, V5.PATCH_D
RUBBER, RUBBER_D = V5.RUBBER, V5.RUBBER_D
SEAM = V5.SEAM
STRAP, STRAP_D = V5.STRAP, V5.STRAP_D
VISOR_D = V5.VISOR_D
GRIME = V5.GRIME
EYE_G, VEIN = V5.EYE_G, V5.VEIN
VIAL = V5.VIAL
RIM, RIM_DIM = V5.RIM, V5.RIM_DIM
HAZ_HL = (233, 197, 82)   # v6: suit highlight

CX = 96


def _walk6(ph):
    """Smooth 6-phase walk cycle -> (swing_l, lift_l, swing_r, lift_r, bob, sway).

    Legs stride forward/back in X (reads as walking at phone size) and lift
    as they pass through; the body dips twice per cycle with no snap."""
    a = 2.0 * math.pi * ph / 6.0
    swing_l = 11.0 * math.cos(a)
    swing_r = 11.0 * math.cos(a + math.pi)
    lift_l = -9.0 * max(0.0, math.sin(a))
    lift_r = -9.0 * max(0.0, math.sin(a + math.pi))
    bob = -2.5 * abs(math.sin(a))
    sway = 6.0 * math.sin(a)
    return swing_l, lift_l, swing_r, lift_r, bob, sway


def _hood_mask(d, im, cx, cy, facing=1, glow_boost=0):
    """Small suit hood + rubber gas mask with ONE glowing visor (v6 polish)."""
    im.alpha_composite(part(ell_mask(cx, cy, 27, 29), (cx - 31, cy - 33, cx + 31, cy + 33), HAZ_Y, HAZ_YM))
    d.polygon([(cx - 8 * facing, cy - 26), (cx + 28 * facing, cy - 20), (cx + 12 * facing, cy - 4)],
              fill=HAZ_YM + (255,))
    # hood top highlight
    d.arc([cx - 24, cy - 30, cx + 24, cy + 18], 200, 320, fill=HAZ_HL + (150,), width=4)
    mx = cx + 10 * facing
    im.alpha_composite(part(ell_mask(mx, cy + 8, 17, 20), (mx - 20, cy - 14, mx + 20, cy + 30), RUBBER, RUBBER_D))
    # mask cheek highlight
    d.arc([mx - 15, cy - 8, mx + 15, cy + 26], 300, 60, fill=(90, 86, 80, 160), width=3)
    vx0, vy0, vx1, vy1 = mx - 13, cy - 2, mx + 13, cy + 12
    d.rounded_rectangle([vx0, vy0, vx1, vy1], radius=6, fill=VISOR_D + (255,))
    d.rounded_rectangle([vx0 + 3, vy0 + 3, vx1 - 3, vy1 - 3], radius=4, fill=EYE_G + (255,))
    # visor scanline: sells the glass
    d.line([(vx0 + 4, (vy0 + vy1) / 2), (vx1 - 4, (vy0 + vy1) / 2)], fill=(8, 38, 20, 255), width=2)
    # visor top glint
    d.line([(vx0 + 6, vy0 + 5), (vx1 - 8, vy0 + 5)], fill=(220, 255, 225, 200), width=2)
    add_glow(im, (vx0 + vx1) / 2, (vy0 + vy1) / 2, 24, EYE_G, 90 + glow_boost)
    # filter canister on cheek
    d.ellipse([mx + 6 * facing - 7, cy + 14, mx + 6 * facing + 7, cy + 28],
              fill=RUBBER_D + (255,), outline=(88, 86, 80, 255), width=2)
    d.line([(mx + 6 * facing - 3, cy + 18), (mx + 6 * facing + 3, cy + 18)], fill=(88, 86, 80, 255), width=2)
    # mask straps + buckles
    d.line([(cx - 22 * facing, cy - 10), (mx - 14, cy - 4)], fill=STRAP_D + (255,), width=4)
    d.line([(cx - 22 * facing, cy + 18), (mx - 14, cy + 14)], fill=STRAP_D + (255,), width=4)
    d.ellipse([mx - 17, cy - 7, mx - 11, cy - 1], fill=(120, 116, 108, 255,))
    d.ellipse([mx - 17, cy + 11, mx - 11, cy + 17], fill=(120, 116, 108, 255,))
    # stronger rim light on hood
    rim_stroke(im, [(cx + 24 * facing, cy - 20), (cx + 27 * facing, cy + 8)], RIM, 4, 235)


def _suit_torso(im, d, cx, top_y, hip_y, half_w, sway=0, back=0, lean=0):
    """Tapered torso: highlight panel, fold shading, seam, belt + pouch."""
    pts = [(cx - half_w + back, top_y), (cx + half_w + back, top_y),
           (cx + half_w * 0.82 + sway, hip_y), (cx - half_w * 0.82 + sway, hip_y)]
    im.alpha_composite(part(poly_mask(pts), (cx - half_w - 8, top_y - 6, cx + half_w + 8, hip_y + 6),
                            HAZ_Y, HAZ_YD))
    # v6: light-side highlight panel
    d.polygon([(cx - half_w + 8 + back, top_y + 10), (cx - half_w * 0.28 + back, top_y + 10),
               (cx - half_w * 0.24 + sway * 0.4 + back, hip_y - 14),
               (cx - half_w + 12 + sway * 0.4 + back, hip_y - 14)],
              fill=HAZ_HL + (85,))
    # fold shadows (deeper than v5)
    for fx, fw in ((-half_w * 0.55, 7), (0, 8), (half_w * 0.55, 7)):
        x = cx + fx + sway * 0.4 + back
        d.polygon([(x - fw, top_y + 10), (x + fw, top_y + 10),
                   (x + fw * 1.4 + sway * 0.4, hip_y), (x - fw * 1.4 + sway * 0.4, hip_y)],
                  fill=HAZ_OL + (165,))
    # center zipper seam
    d.line([(cx + back, top_y + 8), (cx + back + sway * 0.4, hip_y - 4)], fill=SEAM + (220,), width=3)
    # belt + buckle + pouch
    d.rectangle([cx - half_w * 0.86 + sway * 0.5, hip_y - 10, cx + half_w * 0.86 + sway * 0.5, hip_y + 2],
                fill=STRAP_D + (255,))
    d.rectangle([cx - 8, hip_y - 10, cx + 8, hip_y + 2], fill=(120, 116, 108, 255))  # buckle
    px = cx + half_w * 0.5 + sway * 0.5
    d.rounded_rectangle([px - 11, hip_y - 26, px + 11, hip_y - 8], radius=3,
                        fill=STRAP + (255,), outline=STRAP_D + (255,), width=2)
    d.line([(px, hip_y - 26), (px, hip_y - 8)], fill=STRAP_D + (255,), width=2)
    # grime blotch
    d.ellipse([cx - half_w * 0.5, hip_y - 34, cx - half_w * 0.5 + 18, hip_y - 16], fill=GRIME + (70,))
    rim_stroke(im, [(cx + half_w + back, top_y + 4), (cx + half_w * 0.8 + sway, hip_y - 12)], RIM, 4, 225)


def _vial_band(im, d, cx, y, wdt=46):
    """Horizontal chest band with 2 small vials."""
    d.rectangle([cx - wdt / 2, y - 7, cx + wdt / 2, y + 7], fill=STRAP + (255,),
                outline=STRAP_D + (255,), width=2)
    for vx in (cx - 13, cx + 13):
        d.rectangle([vx - 5, y - 13, vx + 5, y + 5], fill=(18, 36, 26, 255),
                    outline=(80, 78, 72, 255), width=2)
        d.rectangle([vx - 3, y - 6, vx + 3, y + 3], fill=VIAL + (255,))
        d.line([(vx - 3, y - 4), (vx + 3, y - 4)], fill=(220, 255, 225, 200), width=1)
    add_glow(im, cx, y, 18, VIAL, 55)


def _leg(d, x, hip_y, foot_y, step=0, xoff=0):
    x += xoff
    d.rectangle([x - 11, hip_y, x + 11, foot_y + step], fill=HAZ_YM + (255,),
                outline=HAZ_YD + (255,), width=2)
    # thigh highlight
    d.line([(x - 6, hip_y + 8), (x - 6, foot_y - 24 + step)], fill=HAZ_HL + (110,), width=4)
    # ankle cuff ring
    d.rectangle([x - 12, foot_y - 22 + step, x + 12, foot_y - 13 + step],
                fill=STRAP + (255,), outline=STRAP_D + (255,), width=1)
    # boot + tread
    d.rectangle([x - 12, foot_y - 14 + step, x + 12, foot_y + step], fill=RUBBER + (255,))
    d.ellipse([x - 12, foot_y - 8 + step, x + 12, foot_y + 4 + step], fill=RUBBER_D + (255,))
    for ty in (foot_y - 5 + step, foot_y + 1 + step):
        d.line([(x - 10, ty), (x + 10, ty)], fill=(74, 70, 64, 255), width=2)


def _arm_to(d, im, shx, shy, hx, hy, wdt=15):
    d.line([(shx, shy), ((shx + hx) / 2, (shy + hy) / 2 + 3), (hx, hy)], fill=HAZ_YM + (255,), width=wdt + 5)
    d.line([(shx, shy), ((shx + hx) / 2, (shy + hy) / 2 + 3), (hx, hy)], fill=HAZ_Y + (255,), width=wdt)
    # sleeve highlight
    d.line([(shx - 3, shy + 2), ((shx + hx) / 2 - 3, (shy + hy) / 2 + 4)], fill=HAZ_HL + (100,), width=3)
    # wrist cuff + glove + knuckle seams
    d.ellipse([hx - 10, hy - 12, hx + 10, hy - 4], fill=STRAP + (255,), outline=STRAP_D + (255,), width=1)
    d.ellipse([hx - 9, hy - 7, hx + 9, hy + 9], fill=RUBBER + (255,))
    d.line([(hx - 5, hy - 1), (hx + 5, hy - 1)], fill=(74, 70, 64, 255), width=2)


def draw_player_side(im, ph, mode="idle"):
    cx, d = CX, ImageDraw.Draw(im)
    swing_l, lift_l, swing_r, lift_r, bob, sway = _walk6(ph) if mode == "walk" else (0, 0, 0, 0, 0, 0)
    lunge = 18 if mode == "attack1" else (8 if mode == "attack2" else 0)
    back = -10 if mode == "hurt" else 0
    if mode in ("death0", "death1"):
        return draw_player_death(im, 0 if mode == "death0" else 1)
    top_y, hip_y, foot_y = 84 + bob, 168 + bob, 238
    if mode == "walk":
        _leg(d, cx - 15, hip_y, foot_y, lift_l, swing_l)
        _leg(d, cx + 15, hip_y, foot_y, lift_r, swing_r)
    else:
        _leg(d, cx - 15, hip_y, foot_y); _leg(d, cx + 15, hip_y, foot_y)
    _suit_torso(im, d, cx, top_y, hip_y, 34, sway, back)
    _vial_band(im, d, cx + back, 118 + bob)
    # backpack canister + valve + hose to shoulder
    d.rectangle([cx - 46 + back, 96 + bob, cx - 32 + back, 142 + bob], fill=RUBBER_D + (255,),
                outline=(80, 78, 72, 255), width=2)
    d.ellipse([cx - 45 + back, 88 + bob, cx - 33 + back, 100 + bob], fill=(88, 86, 80, 255))
    d.arc([cx - 56 + back, 92 + bob, cx - 22 + back, 126 + bob], 100, 260,
          fill=RUBBER_D + (255,), width=5)
    d.line([(cx - 39 + back, 96 + bob), (cx - 39 + back, 88 + bob)], fill=(80, 78, 72, 255), width=4)
    _hood_mask(d, im, cx + back, 50 + bob, 1, glow_boost=60 if mode.startswith("attack") else 0)
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
    swing_l, lift_l, swing_r, lift_r, bob, sway = _walk6(ph) if mode == "walk" else (0, 0, 0, 0, 0, 0)
    if mode in ("death0", "death1"):
        return draw_player_death(im, 0 if mode == "death0" else 1)
    top_y, hip_y, foot_y = 86 + bob, 170 + bob, 238
    if mode == "walk":
        _leg(d, cx - 15, hip_y, foot_y, lift_l, swing_l)
        _leg(d, cx + 15, hip_y, foot_y, lift_r, swing_r)
    else:
        _leg(d, cx - 15, hip_y, foot_y); _leg(d, cx + 15, hip_y, foot_y)
    _suit_torso(im, d, cx, top_y, hip_y, 36, 0, 0)
    _vial_band(im, d, cx, 120 + bob)
    # front-facing hood: hood ring + mask centered
    im.alpha_composite(part(ell_mask(cx, 50 + bob, 30, 32), (cx - 34, 14 + bob, cx + 34, 86 + bob), HAZ_Y, HAZ_YM))
    d.arc([cx - 26, 22 + bob, cx + 26, 78 + bob], 200, 320, fill=HAZ_HL + (140,), width=4)
    im.alpha_composite(part(ell_mask(cx, 54 + bob, 18, 21), (cx - 21, 30 + bob, cx + 21, 79 + bob), RUBBER, RUBBER_D))
    d.rounded_rectangle([cx - 13, 44 + bob, cx + 13, 58 + bob], radius=6, fill=VISOR_D + (255,))
    d.rounded_rectangle([cx - 10, 47 + bob, cx + 10, 55 + bob], radius=4, fill=EYE_G + (255,))
    d.line([(cx - 9, 51 + bob), (cx + 9, 51 + bob)], fill=(8, 38, 20, 255), width=2)
    add_glow(im, cx, 52 + bob, 24, EYE_G, 90)
    d.rounded_rectangle([cx - 7, 62 + bob, cx + 7, 74 + bob], radius=3, fill=RUBBER_D + (255,),
                        outline=(88, 86, 80, 255), width=2)
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
    swing_l, lift_l, swing_r, lift_r, bob, sway = _walk6(ph) if mode == "walk" else (0, 0, 0, 0, 0, 0)
    if mode in ("death0", "death1"):
        return draw_player_death(im, 0 if mode == "death0" else 1)
    top_y, hip_y, foot_y = 86 + bob, 170 + bob, 238
    if mode == "walk":
        _leg(d, cx - 15, hip_y, foot_y, lift_l, swing_l)
        _leg(d, cx + 15, hip_y, foot_y, lift_r, swing_r)
    else:
        _leg(d, cx - 15, hip_y, foot_y); _leg(d, cx + 15, hip_y, foot_y)
    _suit_torso(im, d, cx, top_y, hip_y, 36, 0, 0)
    # backpack canister center-back with valve
    d.rounded_rectangle([cx - 14, 92 + bob, cx + 14, 150 + bob], radius=6, fill=RUBBER_D + (255,),
                        outline=(80, 78, 72, 255), width=2)
    d.ellipse([cx - 12, 84 + bob, cx + 12, 96 + bob], fill=(88, 86, 80, 255))
    d.line([(cx, 92 + bob), (cx, 84 + bob)], fill=(80, 78, 72, 255), width=4)
    # back of hood
    im.alpha_composite(part(ell_mask(cx, 50 + bob, 30, 32), (cx - 34, 14 + bob, cx + 34, 86 + bob), HAZ_Y, HAZ_YM))
    d.arc([cx - 26, 22 + bob, cx + 26, 78 + bob], 200, 320, fill=HAZ_HL + (140,), width=4)
    d.polygon([(cx - 20, 30 + bob), (cx + 20, 30 + bob), (cx, 62 + bob)], fill=HAZ_YD + (255,))
    d.arc([cx - 24, 26 + bob, cx + 24, 74 + bob], 200, 340, fill=SEAM + (200,), width=2)
    _arm_to(d, im, cx - 26, 108 + bob, cx - 32, 152 + bob)
    _arm_to(d, im, cx + 26, 108 + bob, cx + 34, 150 + bob)
    blade_shape(d, cx + 34, 152 + bob, cx + 38, 216 + bob, 10)
    grain(im, (cx - 52, top_y, cx + 52, foot_y), 10)
    return im


def draw_player_death(im, stage):
    return V5.draw_player_death(im, stage)


def gen():
    n = 0
    for dname, fn in (("down", draw_player_down), ("up", draw_player_up), ("side", draw_player_side)):
        for v in (0, 1):
            im = new(); fn(im, 0, "idle"); save(breathe(im, 2 * v), f"p_{dname}_idle_{v}.png"); n += 1
        for ph in range(6):
            im = new(); fn(im, ph, "walk"); save(im, f"p_{dname}_walk_{ph}.png"); n += 1
    for i, m in enumerate(("attack0", "attack1", "attack2")):
        im = new(); draw_player_side(im, 0, m); save(im, f"p_attack_{i}.png"); n += 1
    im = new(); draw_player_side(im, 0, "hurt"); save(im, "p_hurt_0.png"); n += 1
    for s in (0, 1):
        im = new(); draw_player_death(im, s); save(im, f"p_death_{s}.png"); n += 1
    # enemies: v5 frames reused 1:1
    for tname, wfn, dfn in (("shambler", V5.draw_rotwalker, V5.draw_rotwalker_death),
                            ("runner", V5.draw_skitter, V5.draw_skitter_death),
                            ("brute", V5.draw_bulwark, V5.draw_bulwark_death)):
        for ph in range(4):
            im = new(); wfn(im, ph, "walk"); save(im, f"e_{tname}_walk_{ph}.png"); n += 1
        for i, m in enumerate(("attack0", "attack1")):
            im = new(); wfn(im, 0, m); save(im, f"e_{tname}_attack_{i}.png"); n += 1
        for s in (0, 1):
            im = new(); dfn(im, s); save(im, f"e_{tname}_death_{s}.png"); n += 1
    print(f"generated {n} v6 frames")


if __name__ == "__main__":
    gen()
