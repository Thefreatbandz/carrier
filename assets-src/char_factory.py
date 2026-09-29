#!/usr/bin/env python3
"""CARRIER character factory: chunky pixel-art frame sets for the player and
the three infected types. Every frame is drawn from a parametric skeleton so
walk/attack/death are real animation, not static swaps.

Output: assets/<name>.png frames, 96x128 (brute 128x160).
"""
from PIL import Image, ImageDraw
import math, os

OUT = "/home/hatch/workspace/godot-rpg/carrier/assets"
W, H = 96, 128
CX = 48

# ---------------------------------------------------------------- helpers
def new_canvas(w=W, h=H):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))

def limb(d, x, y, ang_deg, length, width, color):
    """Thick limb from (x,y); 0deg = down, positive = clockwise (toward right)."""
    r = math.radians(ang_deg)
    x2 = x + math.sin(r) * length
    y2 = y + math.cos(r) * length
    d.line([x, y, x2, y2], fill=color, width=int(width))
    cr = int(width // 2)
    d.ellipse([x - cr, y - cr, x + cr, y + cr], fill=color)
    d.ellipse([x2 - cr, y2 - cr, x2 + cr, y2 + cr], fill=color)
    return x2, y2

def circle(d, x, y, r, color):
    d.ellipse([x - r, y - r, x + r, y + r], fill=color)

def rect(d, x0, y0, x1, y1, color):
    d.rectangle([x0, y0, x1, y1], fill=color)

def shade(rgb, f):
    return tuple(max(0, min(255, int(c * f))) for c in rgb)

# ---------------------------------------------------------------- palettes
PLAYER = dict(
    skin=(216, 184, 154), skin_d=(180, 148, 122),
    hood=(44, 56, 70), hood_d=(29, 37, 48), hood_l=(66, 80, 98),
    cloak=(37, 45, 57),
    wrap=(107, 74, 47), wrap_d=(82, 56, 35),
    pants=(52, 49, 47), pants_d=(38, 36, 34),
    boots=(34, 29, 26),
    eye=(110, 255, 140), belt=(30, 26, 24),
    blade=(188, 198, 208), blade_d=(140, 150, 162), edge=(110, 255, 140),
    bulk=1.0, name="p",
)
SHAMBLER = dict(
    skin=(134, 156, 118), skin_d=(104, 126, 94),
    shirt=(76, 58, 90), shirt_d=(58, 44, 70),
    pants=(52, 50, 62), pants_d=(40, 38, 48),
    eye=(255, 220, 90), dead_eye=(60, 60, 66),
    bulk=1.08, name="e_shambler",
)
RUNNER = dict(
    skin=(190, 178, 128), skin_d=(158, 146, 104),
    shirt=(128, 44, 44), shirt_d=(100, 34, 34),
    pants=(44, 44, 52), pants_d=(34, 34, 42),
    eye=(255, 120, 80),
    bulk=0.85, name="e_runner",
)
BRUTE = dict(
    skin=(152, 128, 152), skin_d=(122, 102, 124),
    shirt=(62, 72, 112), shirt_d=(48, 56, 88),
    pants=(44, 40, 52), pants_d=(34, 30, 42),
    eye=(255, 90, 90),
    bulk=1.55, name="e_brute",
)

# ---------------------------------------------------------------- player draw
def draw_player(view, pose, frame):
    """view: down/up/side. pose dict carries walk phase / attack stage / etc."""
    img = new_canvas()
    d = ImageDraw.Draw(img)
    P = PLAYER
    cx = CX
    # shadow
    d.ellipse([cx - 22, 112, cx + 22, 122], fill=(0, 0, 0, 100))

    bob = pose.get("bob", 0)
    lean = pose.get("lean", 0)          # degrees, + = forward(right in side view)
    hip_y = 80 + bob
    sh_y = 52 + bob

    if view == "up":
        # ---- back view: big cloak, hood covers head
        rect(d, cx - 20, sh_y - 6, cx + 20, hip_y + 8, P["cloak"])
        rect(d, cx - 20, sh_y - 6, cx - 12, hip_y + 8, shade(P["cloak"], 1.25))
        _legs(d, P, cx, hip_y, pose, view)
        rect(d, cx - 14, sh_y + 2, cx + 14, hip_y - 4, P["wrap"])       # torso strap
        rect(d, cx - 14, hip_y - 8, cx + 14, hip_y - 2, P["belt"])      # belt
        circle(d, cx, sh_y - 14, 15, P["hood"])                        # hood ball
        circle(d, cx, sh_y - 12, 10, P["hood_d"])                      # hood hollow
        # bedroll on back
        rect(d, cx - 12, sh_y + 8, cx + 12, sh_y + 18, P["wrap_d"])
        rect(d, cx - 12, sh_y + 8, cx + 12, sh_y + 10, P["wrap"])
        _arms_back(d, P, cx, sh_y, pose)
        return img

    if view == "side":
        # ---- profile facing right
        _legs(d, P, cx, hip_y, pose, view)
        x0 = cx + lean * 0.25
        limb(d, x0, hip_y, lean, sh_y - hip_y if False else 30, 30, P["wrap"])  # torso
        torso_top = (x0 + math.sin(math.radians(lean)) * 30, hip_y - math.cos(math.radians(lean)) * 30)
        rect(d, x0 - 13, hip_y - 8, x0 + 13, hip_y - 2, P["belt"])
        # cloak trailing behind (left side)
        tx, ty = torso_top
        d.polygon([(tx - 8, ty + 4), (tx - 26, hip_y + 10), (tx - 10, hip_y + 6)], fill=P["cloak"])
        # head profile
        hx, hy = tx + 4, ty - 12
        circle(d, hx, hy, 13, P["skin"])
        d.arc([hx - 16, hy - 18, hx + 14, hy + 12], 200, 20, fill=P["hood"], width=7)  # hood rim back
        d.pieslice([hx - 16, hy - 20, hx + 16, hy + 12], 230, 330, fill=P["hood"])       # hood top
        circle(d, hx + 6, hy + 1, 3, P["eye"])                                          # one glowing eye
        # near arm (swings, holds blade)
        shx, shy = tx + 2, ty + 6
        arm_a = pose.get("arm_r", 10)
        ex, ey = limb(d, shx, shy, arm_a, 24, 11, P["wrap"])
        hx2, hy2 = limb(d, ex, ey, arm_a + pose.get("elbow_r", 12), 20, 9, P["skin"])
        if pose.get("blade", True):
            bx, by = limb(d, hx2, hy2, arm_a + pose.get("blade_a", -70), 36, 7, P["blade"])
            d.line([hx2, hy2, bx, by], fill=P["edge"], width=2)
        # far arm (darker, behind)
        arm_a2 = pose.get("arm_l", -8)
        ex2, ey2 = limb(d, tx - 6, ty + 6, arm_a2, 22, 10, shade(P["wrap"], 0.7))
        limb(d, ex2, ey2, arm_a2 + 14, 18, 8, shade(P["skin"], 0.7))
        return img

    # ---- down view (facing viewer)
    # cloak back panel
    rect(d, cx - 19, sh_y - 4, cx + 19, hip_y + 10, P["cloak"])
    rect(d, cx - 19, sh_y - 4, cx - 11, hip_y + 10, shade(P["cloak"], 1.3))
    _legs(d, P, cx, hip_y, pose, view)
    # torso
    limb(d, cx, hip_y, lean, 32, 32, P["wrap"])
    rect(d, cx - 14, hip_y - 8, cx + 14, hip_y - 2, P["belt"])
    # straps across chest
    d.line([cx - 12, sh_y + 6, cx + 12, sh_y + 20], fill=P["wrap_d"], width=4)
    # arms behind head area first (far arm = left viewer's right? keep simple)
    sh_l, sh_r = (cx - 17, sh_y + 4), (cx + 17, sh_y + 4)
    a_l = pose.get("arm_l", 14)
    a_r = pose.get("arm_r", -14)
    # left arm (viewer-left)
    ex, ey = limb(d, *sh_l, a_l, 22, 11, P["wrap"])
    hx_, hy_ = limb(d, ex, ey, a_l + pose.get("elbow_l", 10), 18, 9, P["skin"])
    # right arm holds blade
    ex2, ey2 = limb(d, *sh_r, a_r, 22, 11, P["wrap"])
    hx2, hy2 = limb(d, ex2, ey2, a_r + pose.get("elbow_r", 10), 18, 9, P["skin"])
    if pose.get("blade", True):
        bx, by = limb(d, hx2, hy2, a_r + pose.get("blade_a", -60), 34, 7, P["blade"])
        d.line([hx2, hy2, bx, by], fill=P["edge"], width=2)
        circle(d, hx2, hy2, 5, P["wrap_d"])  # grip
    # head + hood
    hy = sh_y - 16 + pose.get("head_bob", 0)
    circle(d, cx, hy, 14, P["hood"])
    # hood peak
    d.polygon([(cx - 10, hy - 10), (cx + 10, hy - 10), (cx, hy - 24)], fill=P["hood"])
    circle(d, cx, hy + 2, 10, P["skin"])          # face opening
    circle(d, cx, hy + 2, 10, None) if False else None
    # glowing eyes
    ew = pose.get("eye_w", 3)
    circle(d, cx - 5, hy + 1, ew, P["eye"])
    circle(d, cx + 5, hy + 1, ew, P["eye"])
    if pose.get("mouth_open", False):
        rect(d, cx - 3, hy + 7, cx + 3, hy + 10, (40, 20, 20))
    return img

def _legs(d, P, cx, hip_y, pose, view):
    ph = pose.get("phase", 0.0)
    swing = pose.get("swing", 26)
    if view == "side":
        offs = [6, -6]
        cols = [P["pants"], shade(P["pants"], 0.65)]
        bcols = [P["boots"], shade(P["boots"], 0.7)]
    else:
        offs = [-9, 9]
        cols = [P["pants"], P["pants"]]
        bcols = [P["boots"], P["boots"]]
    for i, off in enumerate(offs):
        p = ph + (math.pi if i == 1 else 0)
        hip_a = math.sin(p) * swing
        knee_bend = 14 + 30 * max(0.0, math.cos(p))
        kx, ky = limb(d, cx + off, hip_y, hip_a, 22, 13, cols[i])
        fx, fy = limb(d, kx, ky, hip_a + knee_bend, 20, 11, cols[i])
        rect(d, fx - 8, fy - 4, fx + 8, fy + 6, bcols[i])  # boot

def _arms_back(d, P, cx, sh_y, pose):
    for sgn, key in ((-1, "arm_l"), (1, "arm_r")):
        a = pose.get(key, 12)
        ex, ey = limb(d, cx + sgn * 16, sh_y + 4, a * sgn, 22, 11, shade(P["wrap"], 0.75))
        limb(d, ex, ey, a * sgn + 12, 18, 9, shade(P["skin"], 0.75))

# ---------------------------------------------------------------- enemy draw
def draw_enemy(cfg, pose):
    big = cfg["bulk"] > 1.3
    w, h = (128, 160) if big else (W, H)
    img = new_canvas(w, h)
    d = ImageDraw.Draw(img)
    cx = w // 2
    b = cfg["bulk"]
    d.ellipse([cx - 22 * b, h - 16, cx + 22 * b, h - 6], fill=(0, 0, 0, 100))  # shadow

    bob = pose.get("bob", 0)
    lean = pose.get("lean", 10)
    hip_y = (h - 52) * (1.0 if not big else 1.0) + bob
    hip_y = h - 56 + bob
    sh_y = hip_y - int(34 * b)
    # legs
    ph = pose.get("phase", 0.0)
    swing = pose.get("swing", 30)
    for i, off in enumerate([-10 * b, 10 * b]):
        p = ph + (math.pi if i == 1 else 0)
        hip_a = math.sin(p) * swing + pose.get("leg_bias", 0)
        knee = 16 + 34 * max(0.0, math.cos(p)) * pose.get("knee_mult", 1.0)
        kx, ky = limb(d, cx + off, hip_y, hip_a, 24, int(13 * b), cfg["pants"])
        fx, fy = limb(d, kx, ky, hip_a + knee, 22, int(11 * b), shade(cfg["pants"], 0.8))
    # torso (bloated for brute)
    limb(d, cx, hip_y, lean, int(34 * b), int(30 * b), cfg["shirt"])
    if big:
        circle(d, cx + 4, hip_y - 18, int(20 * b * 0.7), cfg["shirt"])  # gut
    # tatters
    for tx in (-12, 2, 14):
        d.line([cx + tx, sh_y + 14, cx + tx - 4, hip_y + 6], fill=cfg["shirt_d"], width=3)
    # arms: zombie reach
    for sgn, key in ((-1, "arm_l"), (1, "arm_r")):
        a = pose.get(key, 34)
        ex, ey = limb(d, cx + sgn * 15 * b, sh_y + 6, a * sgn, int(24 * b), int(12 * b), cfg["shirt"])
        limb(d, ex, ey, a * sgn + pose.get("elbow", 8), int(20 * b), int(9 * b), cfg["skin"])
    # head
    tilt = pose.get("tilt", 8)
    hx = cx + int(math.sin(math.radians(tilt)) * 10) + pose.get("head_fwd", 0)
    hy = sh_y - int(16 * b) + pose.get("head_bob", 0)
    hr = int(13 * (0.75 if big else 1.0) * (b if not big else 1.0))
    circle(d, hx, hy, hr, cfg["skin"])
    circle(d, hx - hr // 2, hy - hr // 2, hr // 2, shade(cfg["skin"], 0.85))  # rot patch
    # eyes
    ew = 3
    circle(d, hx - 5, hy - 1, ew, cfg["eye"])
    if pose.get("dead_eye", True):
        circle(d, hx + 5, hy - 1, ew, cfg.get("dead_eye", (60, 60, 66)))
    else:
        circle(d, hx + 5, hy - 1, ew, cfg["eye"])
    # mouth
    if pose.get("mouth_open", False):
        rect(d, hx - 5, hy + 5, hx + 5, hy + 11, (30, 12, 12))
        for tx in (-3, 0, 3):
            d.line([hx + tx, hy + 5, hx + tx, hy + 8], fill=(200, 190, 170), width=1)
    else:
        d.line([hx - 5, hy + 6, hx + 5, hy + 6], fill=shade(cfg["skin"], 0.6), width=2)
    return img

def draw_downed(cfg, blood_r, player=False):
    """Death frame: body flat on the ground with blood pool."""
    big = cfg["bulk"] > 1.3
    w, h = (128, 160) if big else (W, H)
    img = new_canvas(w, h)
    d = ImageDraw.Draw(img)
    cx = w // 2
    gy = h - 30
    d.ellipse([cx - blood_r, gy - 10, cx + blood_r, gy + 10], fill=(120, 18, 18, 220))  # blood
    d.ellipse([cx - blood_r + 8, gy - 6, cx + blood_r - 8, gy + 6], fill=(150, 26, 26, 220))
    b = cfg["bulk"]
    # torso horizontal
    x0, x1 = cx - 30 * b, cx + 18 * b
    limb(d, x0, gy - 6, 84, int(44 * b), int(26 * b), cfg["shirt"] if not player else PLAYER["wrap"])
    # head with X eyes
    hx, hy = x1 + 14, gy - 8
    sk = cfg["skin"] if not player else PLAYER["skin"]
    circle(d, hx, hy, 12, sk)
    for s in (-4, 4):
        d.line([hx + s - 3, hy - 4, hx + s + 3, hy + 2], fill=(20, 20, 20), width=2)
        d.line([hx + s - 3, hy + 2, hx + s + 3, hy - 4], fill=(20, 20, 20), width=2)
    # sprawled limbs
    lc = cfg["pants"] if not player else PLAYER["pants"]
    limb(d, x0 + 6, gy - 4, 100, 26, 11, lc)
    limb(d, x0 + 6, gy - 4, 70, 24, 11, shade(lc, 0.8))
    ac = cfg["skin"] if not player else PLAYER["wrap"]
    limb(d, x1 - 8, gy - 10, 55, 24, 10, ac)
    limb(d, x1 - 8, gy - 10, 120, 22, 10, shade(ac, 0.8))
    return img

# ---------------------------------------------------------------- pose sets
def player_poses():
    P = {}
    for v in ("down", "up", "side"):
        idles = []
        for i in range(2):
            idles.append(dict(bob=-1.5 * i, arm_l=14 + 2 * i, arm_r=-14 - 2 * i,
                              elbow_l=10, elbow_r=10, head_bob=-1 * i, blade_a=-60))
        walks = []
        for i in range(4):
            p = math.radians(i * 90)
            walks.append(dict(phase=p, bob=-3 * abs(math.cos(p)), lean=5,
                              arm_l=-math.sin(p) * 22, arm_r=math.sin(p) * 22,
                              elbow_l=12, elbow_r=12, blade_a=-60, head_bob=0))
        P[v] = (idles, walks)
    atk = [dict(lean=-12, arm_r=-128, elbow_r=6, blade_a=-30, arm_l=30, bob=0, phase=0),
           dict(lean=16, arm_r=72, elbow_r=4, blade_a=-8, arm_l=-20, bob=-2, phase=0),
           dict(lean=2, arm_r=18, elbow_r=10, blade_a=-60, arm_l=10, bob=0, phase=0)]
    hurt = dict(lean=-16, arm_l=44, arm_r=-48, elbow_l=6, elbow_r=6, blade_a=-90,
                head_bob=-3, eye_w=5, mouth_open=True, bob=0)
    return P, atk, hurt

def enemy_walk_poses(cfg):
    frames = []
    n = 4
    for i in range(n):
        p = math.radians(i * 90)
        f = dict(
            phase=p,
            bob=-4 * abs(math.cos(p)),
            lean=12,
            arm_l=34 - math.sin(p) * 10,
            arm_r=34 + math.sin(p) * 10,
            elbow=10,
            tilt=10 + math.sin(p) * 6,
            head_bob=-2 * abs(math.sin(p)),
            mouth_open=(i == 2),
        )
        if cfg is RUNNER:
            f.update(dict(swing=48, lean=22, bob=-5 * abs(math.cos(p)),
                          arm_l=60 - math.sin(p) * 30, arm_r=60 + math.sin(p) * 30,
                          elbow=55, knee_mult=1.4, mouth_open=True))
        if cfg is SHAMBLER:
            f.update(dict(swing=24, lean=14, leg_bias=6, knee_mult=0.5,
                          arm_l=44, arm_r=30, tilt=16))
        if cfg is BRUTE:
            f.update(dict(swing=20, lean=18, bob=-6 * abs(math.cos(p)),
                          arm_l=50, arm_r=50, elbow=20, tilt=4))
        frames.append(f)
    return frames

def enemy_attack_poses(cfg):
    a0 = dict(phase=0, bob=2, lean=-8, arm_l=-95, arm_r=-95, elbow=14,
              tilt=-6, head_bob=-3, mouth_open=False, swing=10)
    a1 = dict(phase=0, bob=-3, lean=26, arm_l=78, arm_r=78, elbow=6,
              tilt=10, head_bob=3, head_fwd=8, mouth_open=True, swing=10)
    return [a0, a1]

# ---------------------------------------------------------------- build
def save(img, name):
    img.save(os.path.join(OUT, name + ".png"))

def build():
    poses, atk, hurt = player_poses()
    # player: down/up/side idle+walk, attack, hurt, death
    for v in ("down", "up", "side"):
        idles, walks = poses[v]
        for i, po in enumerate(idles):
            save(draw_player(v, po, i), f"p_{v}_idle_{i}")
        for i, po in enumerate(walks):
            save(draw_player(v, po, i), f"p_{v}_walk_{i}")
    for i, po in enumerate(atk):
        save(draw_player("side", po, i), f"p_attack_{i}")
    save(draw_player("down", hurt, 0), "p_hurt_0")
    save(draw_downed(PLAYER, 30, player=True), "p_death_0")
    save(draw_downed(PLAYER, 40, player=True), "p_death_1")

    for cfg in (SHAMBLER, RUNNER, BRUTE):
        for i, po in enumerate(enemy_walk_poses(cfg)):
            save(draw_enemy(cfg, po), f"{cfg['name']}_walk_{i}")
        for i, po in enumerate(enemy_attack_poses(cfg)):
            save(draw_enemy(cfg, po), f"{cfg['name']}_attack_{i}")
        save(draw_downed(cfg, 28), f"{cfg['name']}_death_0")
        save(draw_downed(cfg, 38), f"{cfg['name']}_death_1")
    print("frames built")

if __name__ == "__main__":
    build()
