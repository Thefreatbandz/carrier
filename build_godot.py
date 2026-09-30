#!/usr/bin/env python3
"""Builds the CARRIER Godot project: scenes, scripts, config."""
import os, shutil

ROOT = "/home/hatch/workspace/godot-rpg/carrier"
for d in ["scenes", "scripts", "assets", "build/web"]:
    os.makedirs(os.path.join(ROOT, d), exist_ok=True)

def W(path, content):
    p = os.path.join(ROOT, path)
    with open(p, "w") as f:
        f.write(content)
    print("wrote", path, len(content), "bytes")

# ================= project.godot =================
W("project.godot", """; Engine configuration file.
config_version=5

[application]

config/name="CARRIER"
config/description="Infection-meter tower extraction RPG. Ride the infection or turn."
run/main_scene="res://scenes/title.tscn"
config/features=PackedStringArray("4.7", "GL Compatibility")

[autoload]

Sfx="*res://scripts/sfx.gd"

[display]

window/size/viewport_width=720
window/size/viewport_height=1280
window/stretch/mode="canvas_items"
window/stretch/aspect="expand"

[rendering]

renderer/rendering_method="gl_compatibility"
renderer/rendering_method.mobile="gl_compatibility"
textures/canvas_textures/default_texture_filter=0
environment/defaults/default_clear_color=Color(0.03, 0.035, 0.05, 1)
""")

# ================= export_presets.cfg =================
shutil.copy("/home/hatch/workspace/last-shift/export_presets.cfg",
            os.path.join(ROOT, "export_presets.cfg"))
# fix export path + keep CARRIER's pck exclusions (shots/concepts/sources)
p = os.path.join(ROOT, "export_presets.cfg")
s = open(p).read().replace(
    "/home/hatch/workspace/last-shift/build/web/index.html",
    "/home/hatch/workspace/godot-rpg/carrier/build/web/index.html")
if "concepts/*" not in s:
    s = s.replace('exclude_filter="', 'exclude_filter="shots/*,concepts/*,assets-src/*,')
open(p, "w").write(s)
print("export_presets.cfg copied + repathed")

# ================= icon.svg =================
W("icon.svg", """<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128"><rect width="128" height="128" rx="24" fill="#0a0c10"/><circle cx="64" cy="64" r="34" fill="none" stroke="#39ff6a" stroke-width="8"/><circle cx="64" cy="64" r="12" fill="#39ff6a"/></svg>
""")
print("PART1 done")

# ================= scenes =================
W("scenes/infected.tscn", """[gd_scene load_steps=3 format=3]

[ext_resource type="Script" path="res://scripts/infected.gd" id="1"]

[sub_resource type="RectangleShape2D" id="body"]
size = Vector2(56, 60)

[node name="Infected" type="CharacterBody2D"]
collision_layer = 2
collision_mask = 1
script = ExtResource("1")

[node name="CollisionShape2D" type="CollisionShape2D" parent="."]
position = Vector2(0, 16)
shape = SubResource("body")

[node name="Sprite" type="AnimatedSprite2D" parent="."]
""")

W("scenes/slash.tscn", """[gd_scene load_steps=3 format=3]

[ext_resource type="Script" path="res://scripts/slash.gd" id="1"]

[sub_resource type="RectangleShape2D" id="hitbox"]
size = Vector2(200, 160)

[node name="Slash" type="Area2D"]
collision_layer = 4
collision_mask = 2
script = ExtResource("1")

[node name="Sprite" type="Sprite2D" parent="."]

[node name="Hitbox" type="CollisionShape2D" parent="."]
shape = SubResource("hitbox")
""")

W("scenes/pickup.tscn", """[gd_scene load_steps=3 format=3]

[ext_resource type="Script" path="res://scripts/pickup.gd" id="1"]

[sub_resource type="CircleShape2D" id="grab"]
radius = 60.0

[node name="Pickup" type="Area2D"]
collision_layer = 8
collision_mask = 1
script = ExtResource("1")

[node name="Sprite" type="Sprite2D" parent="."]

[node name="Grab" type="CollisionShape2D" parent="."]
shape = SubResource("grab")
""")
print("PART2 scenes done")

# ================= scripts/player.gd =================
W("scripts/player.gd", """extends CharacterBody2D
## The carrier. Infection meter is the core: spend it on powers, hits and time raise it, 100% = turn.

signal died
signal turned
signal changed
signal leveled_up(level: int)
signal sensed

const BASE_SPEED := 300.0
const PASSIVE_INFECTION := 0.35   # per second
const HIT_INFECTION := 6.0
var surge_cost := 15.0
var frenzy_cost := 20.0
var sense_cost := 10.0

var max_hp := 100.0
var hp := 100.0
var infection := 0.0
var damage := 1
var move_mult := 1.0
var scrap := 0
var level := 1
var xp := 0
var xp_next := 45

var facing := Vector2.DOWN
var joystick := Vector2.ZERO     # target set by HUD touch controls
var _joy_sm := Vector2.ZERO      # smoothed joystick (kills thumb jitter/chop)
var attack_cd := 0.0
var hurt_cd := 0.0
var surge_t := 0.0               # active power timers
var frenzy_t := 0.0
var sense_t := 0.0
var surge_cd := 0.0
var frenzy_cd := 0.0
var sense_cd := 0.0
var dead := false
var extract_cleanse := false     # standing on pad
var _flash := 0.0                # hurt flash timer
var _bob_t := 0.0                # walk bob phase
var _lunge := Vector2.ZERO       # attack lunge offset
var _kb := Vector2.ZERO          # knockback velocity (decays)
var _attack_t := 0.0             # attack anim lock timer
var _hurt_t := 0.0               # hurt anim lock timer
# --- dodge roll ---
var dodge_cd := 0.0
var dodge_t := 0.0
var dodge_dir := Vector2.DOWN
var dodge_cd_max := 1.1
var last_move_dir := Vector2.DOWN
var _ghost_t := 0.0
# --- charged heavy attack (hold attack) ---
var touch_atk_held := false
var heavy_mult := 2.5
var _hold_t := 0.0
var _heavy_armed := true
# --- juice ---
var _dust_t := 0.0
var _squash_t := 0.0
var _squash := Vector2.ONE
var _base_scale := Vector2(0.62, 0.62)  # v3 art is bigger, reads on phone

var slash_scene := preload("res://scenes/slash.tscn")

func _ready() -> void:
	add_to_group("player")
	var sf := SpriteFrames.new()
	for dir in ["down", "up", "side"]:
		_add_frames(sf, dir + "_idle",
			["p_%s_idle_0" % dir, "p_%s_idle_1" % dir], 4.0, true)
		_add_frames(sf, dir + "_walk",
			["p_%s_walk_0" % dir, "p_%s_walk_1" % dir,
			 "p_%s_walk_2" % dir, "p_%s_walk_3" % dir,
			 "p_%s_walk_4" % dir, "p_%s_walk_5" % dir], 15.0, true)
	_add_frames(sf, "attack", ["p_attack_0", "p_attack_1", "p_attack_2"], 20.0, false)
	_add_frames(sf, "hurt", ["p_hurt_0"], 8.0, false)
	_add_frames(sf, "death", ["p_death_0", "p_death_1"], 6.0, false)
	$Sprite.frames = sf
	$Sprite.scale = _base_scale
	$Sprite.play("down_idle")
	var sh := Sprite2D.new()
	sh.texture = load("res://assets/shadow.png")
	sh.position = Vector2(0, 86)
	add_child(sh)
	move_child(sh, 0)

func _add_frames(sf: SpriteFrames, name: String, files: Array, fps: float, loop: bool) -> void:
	sf.add_animation(name)
	sf.set_animation_speed(name, fps)
	sf.set_animation_loop(name, loop)
	for f in files:
		var tex := load("res://assets/%s.png" % f) as Texture2D
		sf.add_frame(name, tex)

func _main() -> Node:
	# walk up to the Main node (has hitstop/shake); null-safe for tests
	var n: Node = self
	while n:
		if n.has_method("hitstop"):
			return n
		n = n.get_parent()
	return null

func _physics_process(delta: float) -> void:
	if dead:
		return
	# --- timers ---
	attack_cd = maxf(0.0, attack_cd - delta)
	hurt_cd = maxf(0.0, hurt_cd - delta)
	surge_cd = maxf(0.0, surge_cd - delta)
	frenzy_cd = maxf(0.0, frenzy_cd - delta)
	sense_cd = maxf(0.0, sense_cd - delta)
	dodge_cd = maxf(0.0, dodge_cd - delta)
	dodge_t = maxf(0.0, dodge_t - delta)
	surge_t = maxf(0.0, surge_t - delta)
	frenzy_t = maxf(0.0, frenzy_t - delta)
	sense_t = maxf(0.0, sense_t - delta)
	_flash = maxf(0.0, _flash - delta)
	_attack_t = maxf(0.0, _attack_t - delta)
	_hurt_t = maxf(0.0, _hurt_t - delta)
	_squash_t = maxf(0.0, _squash_t - delta)
	_lunge = _lunge.lerp(Vector2.ZERO, 14.0 * delta)
	$Sprite.modulate = Color(1.8, 0.45, 0.45) if _flash > 0.0 else Color.WHITE
	# --- infection drift ---
	add_infection(PASSIVE_INFECTION * delta, true)
	if extract_cleanse:
		add_infection(-5.0 * delta, true)
	# --- hold attack to charge a heavy ---
	var held := Input.is_action_pressed("atk") or touch_atk_held
	if held and dodge_t <= 0.0:
		_hold_t += delta
		if _hold_t >= 0.45 and _heavy_armed and attack_cd <= 0.05:
			_heavy_armed = false
			attack_heavy()
		elif _hold_t >= 0.25 and _flash <= 0.0:
			var pulse := 1.0 + 0.12 * sin(_hold_t * 30.0)
			$Sprite.modulate = Color(1.1 * pulse, 1.5 * pulse, 1.1 * pulse)
	else:
		_hold_t = 0.0
		_heavy_armed = true
	# --- movement (accel/decel, knockback decays, dodge burst) ---
	var iv := Input.get_vector("mv_left", "mv_right", "mv_up", "mv_down")
	# smooth the thumbstick so velocity glides instead of snapping (no chop)
	_joy_sm = _joy_sm.lerp(joystick, 1.0 - exp(-16.0 * delta))
	var mv := iv + _joy_sm
	if mv.length() > 1.0:
		mv = mv.normalized()
	if dodge_t > 0.0:
		velocity = dodge_dir * BASE_SPEED * 3.4
		_ghost_t -= delta
		if _ghost_t <= 0.0:
			_ghost_t = 0.06
			var m0 := _main()
			if m0:
				m0.fx_ghost(self)
	else:
		var spd := BASE_SPEED * move_mult
		if surge_t > 0.0:
			spd *= 1.8
		if infection >= 70.0:
			spd *= 1.08  # infection frenzy: faster, but fragile
		var accel := 2400.0 if mv.length() > 0.1 else 2000.0
		velocity = velocity.move_toward(mv * spd, accel * delta)
	velocity += _kb
	_kb = _kb.move_toward(Vector2.ZERO, 2200.0 * delta)
	move_and_slide()
	var moving := mv.length() > 0.15
	if moving:
		_face(mv)
		last_move_dir = mv.normalized()
		_bob_t += delta * 11.0
		_dust_t -= delta
		if _dust_t <= 0.0 and dodge_t <= 0.0:
			_dust_t = 0.24
			var m1 := _main()
			if m1:
				m1.fx_dust(global_position + Vector2(0, 66), 1)
	# --- squash & stretch ---
	if dodge_t > 0.0:
		$Sprite.scale = _base_scale * Vector2(1.18, 0.82)
	elif _squash_t > 0.0:
		var k := 1.0 - _squash_t / 0.16
		$Sprite.scale = _base_scale * _squash.lerp(Vector2.ONE, clampf(k, 0.0, 1.0))
	else:
		$Sprite.scale = _base_scale
	# --- animation state machine (attack/hurt lock, then locomotion) ---
	var want := ""
	if _attack_t > 0.0:
		want = "attack"
	elif _hurt_t > 0.0:
		want = "hurt"
	elif moving or dodge_t > 0.0:
		want = _anim_name() + "_walk"
	else:
		want = _anim_name() + "_idle"
	$Sprite.speed_scale = 2.2 if dodge_t > 0.0 else 1.0
	if $Sprite.animation != want or not $Sprite.is_playing():
		$Sprite.play(want)
	$Sprite.position = Vector2(0, sin(_bob_t) * 3.5 if moving else 0.0) + _lunge
	emit_signal("changed")

func _face(mv: Vector2) -> void:
	facing = mv.normalized()
	$Sprite.flip_h = facing.x < -0.1

func _anim_name() -> String:
	if absf(facing.x) > 0.5:
		return "side"
	return "up" if facing.y < -0.1 else "down"

func attack() -> void:
	if dead or attack_cd > 0.0 or dodge_t > 0.0:
		return
	attack_cd = 0.42
	_attack_t = 0.32
	_lunge = facing * 30.0
	_squash = Vector2(1.12, 0.88)
	_squash_t = 0.16
	Sfx.play("swing")
	var s := slash_scene.instantiate()
	s.global_position = global_position + facing * 110.0
	s.rotation = facing.angle()
	s.damage = _out_damage(1.0)
	get_parent().add_child(s)
	var m := _main()
	if m:
		m.hitstop(0.05)
		m.fx_trail(global_position + facing * 70.0, facing.angle(), false)

func attack_heavy() -> void:
	# charged heavy: hold attack 0.45s. Big arc, big damage, costs infection.
	if dead or dodge_t > 0.0:
		return
	attack_cd = 0.6
	_attack_t = 0.4
	_lunge = facing * 46.0
	_squash = Vector2(1.22, 0.78)
	_squash_t = 0.16
	Sfx.play("swing")
	add_infection(4.0, true)
	var s := slash_scene.instantiate()
	s.global_position = global_position + facing * 120.0
	s.rotation = facing.angle()
	s.scale = Vector2(1.7, 1.7)
	s.damage = _out_damage(heavy_mult)
	get_parent().add_child(s)
	var m := _main()
	if m:
		m.hitstop(0.09)
		m.shake(0.5)
		m.fx_trail(global_position + facing * 80.0, facing.angle(), true)
		m.fx_dust(global_position, 4)

func _out_damage(mult: float) -> int:
	# infection risk/reward: riding it high hits harder
	return int(round(damage * mult * (2.0 if frenzy_t > 0.0 else 1.0) * (1.0 + infection / 200.0)))

func try_dodge(dir: Vector2) -> void:
	if dead or dodge_cd > 0.0 or dodge_t > 0.0 or _attack_t > 0.0:
		return
	if dir.length() < 0.1:
		dir = facing
	dodge_dir = dir.normalized()
	dodge_t = 0.32
	dodge_cd = dodge_cd_max
	hurt_cd = maxf(hurt_cd, 0.34)  # i-frames
	_ghost_t = 0.0
	Sfx.play("surge")
	var m := _main()
	if m:
		m.fx_dust(global_position, 6)
		m.shake(0.12)

func try_surge() -> void:
	if dead or surge_cd > 0.0 or infection + surge_cost >= 100.0:
		return
	add_infection(surge_cost)
	surge_t = 3.0
	surge_cd = 8.0
	Sfx.play("surge")
	emit_signal("changed")

func try_frenzy() -> void:
	if dead or frenzy_cd > 0.0 or infection + frenzy_cost >= 100.0:
		return
	add_infection(frenzy_cost)
	frenzy_t = 5.0
	frenzy_cd = 12.0
	Sfx.play("frenzy")
	emit_signal("changed")

func try_sense() -> void:
	if dead or sense_cd > 0.0 or infection + sense_cost >= 100.0:
		return
	add_infection(sense_cost)
	sense_t = 4.0
	sense_cd = 10.0
	Sfx.play("sense")
	emit_signal("sensed")
	emit_signal("changed")

func take_hit(amount: float, from_pos: Vector2 = Vector2.ZERO) -> void:
	if dead or hurt_cd > 0.0:
		return
	hurt_cd = 0.6
	_flash = 0.18
	_hurt_t = 0.25
	_squash = Vector2(1.18, 0.82)
	_squash_t = 0.16
	hp -= amount * (1.0 + infection / 200.0)  # infection risk: fragile when riding high
	Sfx.play("hurt")
	var m := _main()
	if m:
		m.shake(0.35)
	if from_pos != Vector2.ZERO:
		var d := global_position - from_pos
		if d.length() > 1.0:
			_kb = d.normalized() * 420.0
	add_infection(HIT_INFECTION, true)
	if hp <= 0.0:
		hp = 0.0
		_die()
	emit_signal("changed")

func take_damage(amount: int) -> void:
	pass  # player is not damaged via slash

func heal(amount: float) -> void:
	hp = minf(max_hp, hp + amount)
	emit_signal("changed")

func add_infection(amount: float, silent := false) -> void:
	if dead:
		return
	infection = clampf(infection + amount, 0.0, 100.0)
	if infection >= 100.0:
		_turn()
	elif not silent:
		emit_signal("changed")

func add_scrap(n: int) -> void:
	scrap += n
	emit_signal("changed")

func add_xp(n: int) -> void:
	if dead:
		return
	xp += n
	while xp >= xp_next:
		xp -= xp_next
		level += 1
		xp_next = int(45.0 * pow(level, 1.35))
		max_hp += 12.0
		heal(max_hp * 0.3)
		if level % 2 == 0:
			damage += 1
		Sfx.play("levelup")
		emit_signal("leveled_up", level)
	emit_signal("changed")

func _die() -> void:
	dead = true
	$Sprite.play("death")
	emit_signal("died")

func _turn() -> void:
	dead = true
	infection = 100.0
	$Sprite.play("death")
	emit_signal("turned")
""")
print("PART3 player done")

# ================= scripts/main.gd =================
W("scripts/main.gd", """extends Node2D
## CARRIER run manager: floors, extraction, spawner, upgrades, touch input.

var player_scene := preload("res://scenes/player.tscn")
var infected_scene := preload("res://scenes/infected.tscn")
var pickup_scene := preload("res://scenes/pickup.tscn")

var player: CharacterBody2D
var hud: CanvasLayer
var floor_node: Node2D
var floor_num := 1
var rng := RandomNumberGenerator.new()
var channeling := false
var channel_t := 0.0
var _tick_t := 0.0
const CHANNEL_NEED := 3.0
const CELL := 720.0
const DOOR_GAP := 280.0
var dungeon_rooms: Array = []
var boss: Node = null
const WEAPON_NAMES := ["WORN SHIV", "RUSTY BLADE", "HUNTER'S EDGE", "PLAGUEBANE"]
var pad: Area2D
var joy_id := -1
var joy_origin := Vector2.ZERO
const JOY_DEADZONE := 0.22   # thumb rest zone: no drift, no jitter
var cam: Camera2D                       # cached player camera (shake)
var pad_glow: Sprite2D = null
var _hitstop := 0.0                     # hit-stop timer (unscaled)
var _trauma := 0.0                      # screen-shake trauma 0..1
var _glow_t := 0.0
var run := {}                           # run state: survives floor rebuilds
var atk_touch_id := -1                  # right-half tap holding attack
var last_tap_msec := 0                  # (unused since dodge got its own button)

const UPGRADES := [
	{"name": "MAX HP +20", "desc": "Sturdier body"},
	{"name": "DAMAGE +1", "desc": "Heavier swings"},
	{"name": "SPEED +10%", "desc": "Lighter feet"},
	{"name": "CHEAP POWERS", "desc": "Powers cost 25% less"},
	{"name": "SWIFT DODGE", "desc": "Dodge recharges 30% faster"},
	{"name": "HEAVY HITTER", "desc": "Charged heavies hit 40% harder"},
]

class SenseMarker extends Node2D:
	var life := 4.0
	var _t := 0.0
	func _process(d: float) -> void:
		_t += d
		life -= d
		queue_redraw()
		if life <= 0.0:
			queue_free()
	func _draw() -> void:
		var a := 0.35 + 0.3 * sin(_t * 8.0)
		draw_arc(Vector2.ZERO, 36.0, 0.0, TAU, 24, Color(0.3, 1.0, 1.0, a), 7.0)
		draw_circle(Vector2.ZERO, 6.0, Color(0.3, 1.0, 1.0, a))

func _ready() -> void:
	add_to_group("game_main")
	_ensure_input()
	rng.seed = randi()
	hud = preload("res://scripts/hud.gd").new()
	hud.name = "HUD"
	hud.process_mode = Node.PROCESS_MODE_ALWAYS
	add_child(hud)
	start_run()

func _ensure_input() -> void:
	_add("mv_left", [KEY_A, KEY_LEFT])
	_add("mv_right", [KEY_D, KEY_RIGHT])
	_add("mv_up", [KEY_W, KEY_UP])
	_add("mv_down", [KEY_S, KEY_DOWN])
	_add("atk", [KEY_SPACE])
	_add("dodge", [KEY_SHIFT])
	_add("surge", [KEY_Q])
	_add("frenzy", [KEY_E])
	_add("sense", [KEY_F])

func _add(action: String, keys: Array) -> void:
	if not InputMap.has_action(action):
		InputMap.add_action(action)
	for k in keys:
		var ev := InputEventKey.new()
		ev.physical_keycode = k
		if not InputMap.action_has_event(action, ev):
			InputMap.action_add_event(action, ev)

func _to_canvas(p: Vector2) -> Vector2:
	# screen pixels -> canvas units (they only match on desktop; phones scale)
	return get_viewport().get_canvas_transform().affine_inverse() * p

func start_run() -> void:
	Engine.time_scale = 1.0
	floor_num = 1
	run = _default_run()
	build_floor()

func _default_run() -> Dictionary:
	return {
		"max_hp": 100.0, "hp": 100.0, "damage": 1, "move_mult": 1.0,
		"surge_cost": 15.0, "frenzy_cost": 20.0, "scrap": 0,
		"level": 1, "xp": 0, "xp_next": 45, "infection": 0.0,
		"dodge_cd_max": 1.1, "heavy_mult": 2.5,
	}

func _snapshot_run() -> void:
	# copy the living player's state before the floor (and player) is rebuilt
	if player == null or not is_instance_valid(player):
		return
	run["max_hp"] = player.max_hp
	run["hp"] = player.hp
	run["damage"] = player.damage
	run["move_mult"] = player.move_mult
	run["surge_cost"] = player.surge_cost
	run["frenzy_cost"] = player.frenzy_cost
	run["scrap"] = player.scrap
	run["level"] = player.level
	run["xp"] = player.xp
	run["xp_next"] = player.xp_next
	run["infection"] = player.infection
	run["dodge_cd_max"] = player.dodge_cd_max
	run["heavy_mult"] = player.heavy_mult

func _apply_run(p: Node) -> void:
	p.max_hp = float(run["max_hp"])
	p.hp = float(run["hp"])
	p.damage = int(run["damage"])
	p.move_mult = float(run["move_mult"])
	p.surge_cost = float(run["surge_cost"])
	p.frenzy_cost = float(run["frenzy_cost"])
	p.scrap = int(run["scrap"])
	p.level = int(run["level"])
	p.xp = int(run["xp"])
	p.xp_next = int(run["xp_next"])
	p.infection = float(run["infection"])
	p.dodge_cd_max = float(run["dodge_cd_max"])
	p.heavy_mult = float(run["heavy_mult"])

func build_floor() -> void:
	# clear old floor (deferred; new one tracked via floor_node)
	if floor_node and is_instance_valid(floor_node):
		floor_node.queue_free()
	channeling = false
	channel_t = 0.0
	boss = null
	hud.set_boss(null)
	var f := Node2D.new()
	f.name = "Floor"
	add_child(f)
	floor_node = f
	_gen_dungeon()
	var floor_texs: Array = [
		load("res://assets/floor_a.png") as Texture2D,
		load("res://assets/floor_crack.png") as Texture2D,
		load("res://assets/floor_grime.png") as Texture2D,
		load("res://assets/floor_moss.png") as Texture2D,
	]
	var floor_w := [0.60, 0.15, 0.15, 0.10]
	var wall_tex := load("res://assets/wall_block.png") as Texture2D
	var door_tex := load("res://assets/gate_post.png") as Texture2D
	var glow_tex := load("res://assets/glow_green.png") as Texture2D
	for r in dungeon_rooms:
		var c: Vector2 = r["center"]
		# 6x6 varied floor tiles per room (seeded)
		for tx in range(6):
			for ty in range(6):
				var roll := rng.randf()
				var acc := 0.0
				var ti := 0
				for i in range(floor_w.size()):
					acc += float(floor_w[i])
					if roll <= acc:
						ti = i
						break
				var sp := Sprite2D.new()
				sp.texture = floor_texs[ti]
				sp.scale = Vector2(120, 120) / (floor_texs[ti] as Texture2D).get_size()
				sp.position = c + Vector2((tx - 2.5) * 120.0, (ty - 2.5) * 120.0)
				sp.modulate = Color(0.55, 0.57, 0.62)
				f.add_child(sp)
		_build_room_walls(f, r, wall_tex, door_tex, glow_tex)
	# player in entrance room
	var entrance: Dictionary = _room_by_type("entrance")
	player = player_scene.instantiate()
	_apply_run(player)  # upgrades/scrap/xp/infection survive the descent
	player.position = entrance["center"]
	f.add_child(player)
	cam = player.get_node("Camera") as Camera2D
	player.died.connect(_on_player_died.bind(false))
	player.turned.connect(_on_player_died.bind(true))
	player.sensed.connect(func(): reveal_pickups(4.0))
	player.leveled_up.connect(func(lv: int): hud.show_toast("LEVEL %d" % lv))
	hud.bind(player)
	# extraction pad in farthest room
	var ext: Dictionary = _room_by_type("extraction")
	pad = Area2D.new()
	pad.add_to_group("extract_pad")
	pad.collision_layer = 16
	pad.collision_mask = 1
	pad.position = ext["center"]
	var ps := Sprite2D.new()
	ps.texture = load("res://assets/extract_pad.png")
	ps.scale = Vector2(0.6, 0.6)
	pad.add_child(ps)
	var pg := Sprite2D.new()
	pg.texture = glow_tex
	pg.scale = Vector2(2.2, 2.2)
	pg.modulate = Color(1, 1, 1, 0.5)
	pad.add_child(pg)
	pad_glow = pg
	var shape := CollisionShape2D.new()
	var circ := CircleShape2D.new()
	circ.radius = 190.0
	shape.shape = circ
	pad.add_child(shape)
	f.add_child(pad)
	pad.body_entered.connect(_on_pad_enter)
	pad.body_exited.connect(_on_pad_exit)
	# infected in combat rooms
	for r in dungeon_rooms:
		if r["type"] == "combat":
			var n := 1 + mini(floor_num / 2, 3)
			for i in range(n):
				spawn_infected(_room_spot(r, 180.0))
	# treasure chest
	var tr: Dictionary = _room_by_type("treasure")
	if not tr.is_empty():
		_spawn_chest(tr["center"])
	# scatter loot
	for i in range(5):
		spawn_pickup("scrap", _any_spot(200.0))
	for i in range(2):
		spawn_pickup("suppressant", _any_spot(200.0))
	spawn_pickup("medkit", _any_spot(200.0))
	# boss every 3rd depth guards the pad
	if floor_num % 3 == 0:
		_spawn_boss(ext["center"] + Vector2(0, -170))
	# spawner timer
	var t := Timer.new()
	t.name = "Spawner"
	t.wait_time = 7.0
	t.autostart = true
	t.timeout.connect(_on_spawn_tick)
	f.add_child(t)
	hud.set_floor(floor_num)
	hud.set_dungeon(dungeon_rooms)

func _gen_dungeon() -> void:
	dungeon_rooms.clear()
	var gw := 3 if floor_num < 3 else 4
	var gh := 3
	var target := mini(5 + floor_num, gw * gh)
	var dirs := [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]
	var cell_to_idx := {}
	var door_map := {}
	var cur := Vector2i(0, 0)
	cell_to_idx[cur] = 0
	door_map[cur] = []
	var guard := 0
	while cell_to_idx.size() < target and guard < 300:
		guard += 1
		var d: Vector2i = dirs[rng.randi() % 4]
		var nxt := Vector2i(cur.x + d.x, cur.y + d.y)
		if nxt.x < 0 or nxt.y < 0 or nxt.x >= gw or nxt.y >= gh:
			continue
		if not cell_to_idx.has(nxt):
			cell_to_idx[nxt] = cell_to_idx.size()
			door_map[nxt] = []
		if not (door_map[cur] as Array).has(d):
			(door_map[cur] as Array).append(d)
			(door_map[nxt] as Array).append(Vector2i(-d.x, -d.y))
		cur = nxt
	for cell in cell_to_idx.keys():
		var wx := (float(cell.x) - float(gw - 1) / 2.0) * CELL
		var wy := (float(cell.y) - float(gh - 1) / 2.0) * CELL
		dungeon_rooms.append({
			"cell": cell, "center": Vector2(wx, wy),
			"type": "combat", "doors": door_map[cell],
		})
	dungeon_rooms.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
		return (cell_to_idx[a["cell"]] as int) < (cell_to_idx[b["cell"]] as int))
	dungeon_rooms[0]["type"] = "entrance"
	# BFS from entrance: farthest room holds the extraction pad
	var dist := {Vector2i(0, 0): 0}
	var queue: Array = [Vector2i(0, 0)]
	while not queue.is_empty():
		var c: Vector2i = queue.pop_front()
		var ri: int = cell_to_idx[c]
		for d in dungeon_rooms[ri]["doors"]:
			var nc := Vector2i(c.x + d.x, c.y + d.y)
			if not dist.has(nc):
				dist[nc] = (dist[c] as int) + 1
				queue.append(nc)
	var far_cell := Vector2i(0, 0)
	for c in dist.keys():
		if (dist[c] as int) > (dist[far_cell] as int):
			far_cell = c
	dungeon_rooms[cell_to_idx[far_cell]]["type"] = "extraction"
	var cands: Array = []
	for i in range(dungeon_rooms.size()):
		if (dungeon_rooms[i] as Dictionary)["type"] == "combat":
			cands.append(i)
	if not cands.is_empty():
		(dungeon_rooms[cands[rng.randi() % cands.size()]] as Dictionary)["type"] = "treasure"

func _build_room_walls(f: Node, r: Dictionary, wall_tex: Texture2D, door_tex: Texture2D, glow_tex: Texture2D) -> void:
	var c: Vector2 = r["center"]
	var dirs := [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]
	for d in dirs:
		var has_door: bool = (r["doors"] as Array).has(d)
		var n := Vector2(d)
		var tang := Vector2(-n.y, n.x)
		var edge := c + n * (CELL / 2.0)
		if has_door:
			var seg_len := (CELL - DOOR_GAP) / 2.0
			var off := seg_len / 2.0 + DOOR_GAP / 2.0
			_tiled_wall(f, edge + tang * off, tang, seg_len, wall_tex)
			_tiled_wall(f, edge - tang * off, tang, seg_len, wall_tex)
			# Gate: two stone posts flanking the opening, middle stays CLEAR.
			for sgn in [-1.0, 1.0]:
				var gp := Sprite2D.new()
				gp.texture = door_tex  # now the gate post texture
				gp.position = edge + tang * sgn * (DOOR_GAP / 2.0 + 34.0)
				gp.rotation = PI / 2.0 if n.y != 0.0 else 0.0
				f.add_child(gp)
			# soft infection glow marking the gate
			var gl := Sprite2D.new()
			gl.texture = glow_tex
			gl.position = edge
			gl.scale = Vector2(1.6, 1.6)
			gl.modulate = Color(1, 1, 1, 0.35)
			f.add_child(gl)
		else:
			_tiled_wall(f, edge, tang, CELL, wall_tex)

func _tiled_wall(f: Node, center: Vector2, tang: Vector2, length: float, tex: Texture2D) -> void:
	var sb := StaticBody2D.new()
	sb.position = center
	var cs := CollisionShape2D.new()
	var rect := RectangleShape2D.new()
	if absf(tang.x) > 0.5:
		rect.size = Vector2(length, 60.0)
	else:
		rect.size = Vector2(60.0, length)
	cs.shape = rect
	sb.add_child(cs)
	f.add_child(sb)
	var block := 120.0
	var n := maxi(1, int(length / block))
	for i in range(n):
		var tt := (float(i) + 0.5) / float(n) - 0.5
		var sp := Sprite2D.new()
		sp.texture = tex
		sp.scale = Vector2(block, block) / tex.get_size()
		sp.position = center + tang * (tt * length)
		sp.modulate = Color(0.5, 0.5, 0.55)
		f.add_child(sp)

func _room_by_type(t: String) -> Dictionary:
	for r in dungeon_rooms:
		if (r as Dictionary)["type"] == t:
			return r
	return {}

func _room_spot(r: Dictionary, margin: float) -> Vector2:
	var c: Vector2 = r["center"]
	for tries in range(30):
		var p := c + Vector2(rng.randf_range(-1.0, 1.0), rng.randf_range(-1.0, 1.0)) * (CELL / 2.0 - margin)
		if player and p.distance_to(player.position) < 380.0:
			continue
		return p
	return c

func _any_spot(margin: float) -> Vector2:
	if dungeon_rooms.is_empty():
		return Vector2.ZERO
	return _room_spot(dungeon_rooms[rng.randi() % dungeon_rooms.size()], margin)

func _spawn_chest(pos: Vector2) -> void:
	var f := floor_node
	var ch := Area2D.new()
	ch.name = "Chest"
	ch.add_to_group("chests")
	ch.collision_layer = 0
	ch.collision_mask = 1
	ch.position = pos
	ch.set_meta("opened", false)
	var sp := Sprite2D.new()
	sp.name = "Sprite"
	sp.texture = load("res://assets/chest_closed.png")
	sp.scale = Vector2(0.7, 0.7)
	ch.add_child(sp)
	var shape := CollisionShape2D.new()
	var circ := CircleShape2D.new()
	circ.radius = 90.0
	shape.shape = circ
	ch.add_child(shape)
	f.add_child(ch)
	ch.body_entered.connect(_on_chest_open.bind(ch))

func _on_chest_open(body: Node2D, ch: Area2D) -> void:
	if not body.is_in_group("player"):
		return
	if ch.get_meta("opened") as bool:
		return
	ch.set_meta("opened", true)
	(ch.get_node("Sprite") as Sprite2D).texture = load("res://assets/chest_open.png")
	Sfx.play("upgrade")
	hud.show_toast("CHEST LOOTED")
	var base: Vector2 = ch.global_position
	var kinds := ["scrap", "scrap", "suppressant", "medkit", "weapon"]
	for i in range(3):
		var k: String = kinds[rng.randi() % kinds.size()]
		spawn_pickup(k, base + Vector2(rng.randf_range(-90.0, 90.0), rng.randf_range(-90.0, 90.0)))

func _spawn_boss(pos: Vector2) -> void:
	var f := floor_node
	var e: CharacterBody2D = infected_scene.instantiate()
	e.position = pos
	e.setup("brute", floor_num)
	e.set("is_boss", true)
	var bhp: int = int(e.get("max_hp")) * 6
	e.set("max_hp", bhp)
	e.set("hp", bhp)
	e.set("touch_damage", float(e.get("touch_damage")) * 1.5)
	e.set("xp", 150)
	f.add_child(e)
	var spr := e.get_node("Sprite") as Node2D
	spr.scale = spr.scale * 1.5
	boss = e
	hud.set_boss(boss)
	hud.show_toast("THE WARDEN STIRS")

func on_weapon_pickup() -> void:
	if player and not player.dead:
		player.damage += 1
		var nm: String = WEAPON_NAMES[mini(floor_num / 2, 3)]
		hud.show_toast(nm + "  DMG +1")

func _pick_type() -> String:
	var r := rng.randf()
	if floor_num <= 1:
		return "shambler"
	if floor_num == 2:
		return "runner" if r < 0.35 else "shambler"
	return "brute" if r < 0.2 else ("runner" if r < 0.5 else "shambler")

func spawn_infected(pos: Vector2) -> void:
	var f := floor_node
	var e: CharacterBody2D = infected_scene.instantiate()
	e.position = pos
	e.setup(_pick_type(), floor_num)
	f.add_child(e)

func reveal_pickups(dur: float) -> void:
	for p in get_tree().get_nodes_in_group("pickups"):
		var m := SenseMarker.new()
		m.life = dur
		(p as Node2D).add_child(m)
	for ch in get_tree().get_nodes_in_group("chests"):
		var m2 := SenseMarker.new()
		m2.life = dur
		(ch as Node2D).add_child(m2)
	if pad and is_instance_valid(pad):
		var m3 := SenseMarker.new()
		m3.life = dur
		pad.add_child(m3)

func spawn_pickup(kind: String, pos: Vector2) -> void:
	var f := floor_node
	var p: Area2D = pickup_scene.instantiate()
	p.kind = kind
	p.position = pos
	f.add_child(p)

func on_infected_killed(pos: Vector2, xp: int, was_boss: bool = false) -> void:
	if player and not player.dead:
		player.add_xp(xp)
	if was_boss:
		hud.show_toast("WARDEN SLAIN")
		spawn_pickup("weapon", pos + Vector2(-60, 0))
		spawn_pickup("medkit", pos + Vector2(60, 0))
		spawn_pickup("suppressant", pos + Vector2(0, 60))
		for i in range(3):
			spawn_pickup("scrap", pos + Vector2(rng.randf_range(-100, 100), rng.randf_range(-100, 100)))
		return
	var r := rng.randf()
	if r < 0.55:
		spawn_pickup("scrap", pos)
	elif r < 0.70:
		spawn_pickup("suppressant", pos)
	elif r < 0.78:
		spawn_pickup("medkit", pos)
	if xp >= 30 and rng.randf() < 0.12:
		spawn_pickup("weapon", pos + Vector2(40, 0))

func _on_spawn_tick() -> void:
	var count := get_tree().get_nodes_in_group("infected").size()
	if count < mini(4 + floor_num, 10) and player and not player.dead:
		spawn_infected(_any_spot(200.0))

func _on_pad_enter(body: Node2D) -> void:
	if body.is_in_group("player"):
		channeling = true
		channel_t = 0.0
		player.extract_cleanse = true

func _on_pad_exit(body: Node2D) -> void:
	if body.is_in_group("player"):
		channeling = false
		channel_t = 0.0
		player.extract_cleanse = false
		hud.set_channel(-1.0)

func _process(delta: float) -> void:
	# hit-stop (unscaled: divide out time_scale so 0.09s really is 0.09s)
	if _hitstop > 0.0:
		_hitstop -= delta / maxf(Engine.time_scale, 0.001)
		if _hitstop <= 0.0:
			Engine.time_scale = 1.0
	# screen shake
	if _trauma > 0.0:
		_trauma = maxf(0.0, _trauma - delta * 1.8)
		if cam:
			var s := _trauma * _trauma * 26.0
			cam.offset = Vector2(randf_range(-s, s), randf_range(-s, s))
	elif cam and cam.offset != Vector2.ZERO:
		cam.offset = Vector2.ZERO
	# extraction pad glow pulse
	if pad_glow and is_instance_valid(pad_glow):
		_glow_t += delta
		pad_glow.modulate.a = 0.38 + 0.18 * sin(_glow_t * 3.0)
	if channeling and player and not player.dead:
		channel_t += delta
		_tick_t += delta
		if _tick_t >= 0.5:
			_tick_t = 0.0
			Sfx.play("extract_tick")
		hud.set_channel(channel_t / CHANNEL_NEED)
		if channel_t >= CHANNEL_NEED:
			channeling = false
			player.extract_cleanse = false
			floor_cleared()

func floor_cleared() -> void:
	Engine.time_scale = 1.0
	get_tree().paused = true
	var picks := UPGRADES.duplicate()
	picks.shuffle()
	hud.show_draft(picks.slice(0, 3), _on_upgrade)

func _on_upgrade(u: Dictionary) -> void:
	get_tree().paused = false
	Sfx.play("upgrade")
	_snapshot_run()
	match u["name"]:
		"MAX HP +20":
			run["max_hp"] = float(run["max_hp"]) + 20.0
			run["hp"] = minf(float(run["max_hp"]), float(run["hp"]) + 20.0)
		"DAMAGE +1":
			run["damage"] = int(run["damage"]) + 1
		"SPEED +10%":
			run["move_mult"] = float(run["move_mult"]) * 1.1
		"CHEAP POWERS":
			run["surge_cost"] = 11.0
			run["frenzy_cost"] = 15.0
		"SWIFT DODGE":
			run["dodge_cd_max"] = float(run["dodge_cd_max"]) * 0.7
		"HEAVY HITTER":
			run["heavy_mult"] = float(run["heavy_mult"]) * 1.4
	# descend: catch your breath (+25% HP), but the infection comes with you
	run["hp"] = minf(float(run["max_hp"]), float(run["hp"]) + float(run["max_hp"]) * 0.25)
	floor_num += 1
	build_floor()
	hud.show_toast("DEPTH %d — upgrades kept" % floor_num)

func hitstop(dur: float) -> void:
	Engine.time_scale = 0.05
	_hitstop = dur

func shake(amount: float) -> void:
	_trauma = minf(1.0, _trauma + amount)

# ---------------- juice: ghosts, sparks, dust, trails ----------------
func fx_ghost(p: Node2D) -> void:
	if floor_node == null or not is_instance_valid(floor_node):
		return
	var spr := p.get_node_or_null("Sprite") as AnimatedSprite2D
	if spr == null:
		return
	var g := Sprite2D.new()
	g.texture = spr.sprite_frames.get_frame_texture(spr.animation, spr.frame)
	g.global_position = p.global_position
	g.scale = spr.global_scale
	g.flip_h = spr.flip_h
	g.modulate = Color(0.45, 1.0, 0.55, 0.55)
	g.z_index = 1  # above floor tiles, trails behind the dodging player
	floor_node.add_child(g)
	var tw := create_tween()
	tw.tween_property(g, "modulate:a", 0.0, 0.3)
	tw.tween_callback(g.queue_free)

func fx_sparks(pos: Vector2, color: Color = Color(1, 1, 1)) -> void:
	if floor_node == null or not is_instance_valid(floor_node):
		return
	var tex := load("res://assets/spark.png") as Texture2D
	for i in range(8):
		var s := Sprite2D.new()
		s.texture = tex
		s.position = pos
		s.modulate = color
		var a := rng.randf() * TAU
		var d := Vector2(cos(a), sin(a)) * rng.randf_range(120.0, 320.0)
		floor_node.add_child(s)
		var tw := create_tween().set_parallel()
		tw.tween_property(s, "position", pos + d, 0.35).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
		tw.tween_property(s, "modulate:a", 0.0, 0.35)
		tw.chain().tween_callback(s.queue_free)

func fx_dust(pos: Vector2, n: int = 3) -> void:
	if floor_node == null or not is_instance_valid(floor_node):
		return
	var tex := load("res://assets/dust.png") as Texture2D
	for i in range(n):
		var s := Sprite2D.new()
		s.texture = tex
		s.position = pos + Vector2(rng.randf_range(-24, 24), rng.randf_range(-8, 8))
		s.modulate = Color(0.8, 0.78, 0.75, 0.5)
		var sc := rng.randf_range(0.7, 1.4) * 0.5
		s.scale = Vector2(sc, sc)
		floor_node.add_child(s)
		var tw := create_tween().set_parallel()
		tw.tween_property(s, "scale", s.scale * 2.2, 0.4)
		tw.tween_property(s, "modulate:a", 0.0, 0.4)
		tw.chain().tween_callback(s.queue_free)

func fx_trail(pos: Vector2, angle: float, big: bool) -> void:
	if floor_node == null or not is_instance_valid(floor_node):
		return
	var s := Sprite2D.new()
	s.texture = load("res://assets/trail_arc.png")
	s.position = pos
	s.rotation = angle
	var sc := 1.1 if big else 0.8
	s.scale = Vector2(sc, sc)
	s.modulate = Color(0.7, 1.0, 0.75, 0.85)
	floor_node.add_child(s)
	var tw := create_tween().set_parallel()
	tw.tween_property(s, "rotation", angle + 1.2, 0.18)
	tw.tween_property(s, "modulate:a", 0.0, 0.18)
	tw.chain().tween_callback(s.queue_free)

func _on_player_died(turned: bool) -> void:
	Engine.time_scale = 1.0
	get_tree().paused = true
	Sfx.play("turn" if turned else "hurt")
	hud.show_death(turned, floor_num, player.scrap)

func _on_power_btn(pos: Vector2) -> bool:
	for b in [hud.surge_btn, hud.frenzy_btn, hud.sense_btn, hud.atk_btn, hud.dodge_btn]:
		if b and b.get_global_rect().has_point(pos):
			return true
	return false

func _input(event: InputEvent) -> void:
	if event.is_action_pressed("atk"):
		if player and not player.dead:
			player.attack()
	if event.is_action_pressed("surge"):
		if player:
			player.try_surge()
	if event.is_action_pressed("frenzy"):
		if player:
			player.try_frenzy()
	if event.is_action_pressed("sense"):
		if player:
			player.try_sense()
	if event.is_action_pressed("dodge"):
		if player:
			player.try_dodge(player.last_move_dir)
	if event is InputEventScreenTouch:
		var t := event as InputEventScreenTouch
		var cpos := _to_canvas(t.position)
		if t.pressed:
			if cpos.x < 360.0:
				# left half = floating joystick. Dodge has its own button now:
				# double-tap kept firing accidental rolls while repositioning
				# the thumb, which is what made movement feel broken.
				if joy_id == -1:
					joy_id = t.index
					joy_origin = cpos
					hud.show_joystick(cpos)
			elif cpos.x >= 360.0 and not _on_power_btn(cpos):
				if player and not player.dead:
					atk_touch_id = t.index
					player.touch_atk_held = true
					player.attack()
		else:
			if t.index == joy_id:
				joy_id = -1
				if player:
					player.joystick = Vector2.ZERO
				hud.hide_joystick()
			if t.index == atk_touch_id:
				atk_touch_id = -1
				if player:
					player.touch_atk_held = false
	elif event is InputEventScreenDrag:
		var d := event as InputEventScreenDrag
		if d.index == joy_id and player:
			var raw := (_to_canvas(d.position) - joy_origin) / 110.0
			var rl := raw.length()
			var v := Vector2.ZERO
			if rl > JOY_DEADZONE:
				# smoothstep response: gentle near center, full throw at the rim
				var t := clampf((rl - JOY_DEADZONE) / (1.0 - JOY_DEADZONE), 0.0, 1.0)
				t = t * t * (3.0 - 2.0 * t)
				v = raw / rl * t
			player.joystick = v
			hud.move_knob(joy_origin + v * 110.0)
""")
print("PART5 main done")

# ================= scripts/infected.gd =================
W("scripts/infected.gd", """extends CharacterBody2D
## Infected. Chases the carrier; attacks have a telegraph + lunge.

var max_hp := 3
var hp := 3
var speed := 95.0
var touch_damage := 12.0
var dead := false
var is_boss := false
var itype := "shambler"
var xp := 10
var _base := "e_shambler"
var _spr_scale := 1.0
var _hbox := Vector2.ONE
var _hit_flash := 0.0
var _knockback := Vector2.ZERO
var _bob_t := 0.0
var _atk_cd := 0.0
var _windup := 0.0       # attack telegraph timer
var _dead_t := 0.0

func setup(t: String, floor_num: int) -> void:
	itype = t
	match t:
		"runner":
			max_hp = 2 + floor_num / 2
			speed = 155.0 + floor_num * 4.0
			touch_damage = 10.0 + floor_num
			xp = 14
			_base = "e_runner"
			_spr_scale = 0.55
			_hbox = Vector2(0.85, 0.85)
		"brute":
			max_hp = 9 + floor_num
			speed = 62.0
			touch_damage = 22.0 + floor_num
			xp = 30
			_base = "e_brute"
			_spr_scale = 0.9
			_hbox = Vector2(1.6, 1.5)
		_:  # shambler
			max_hp = 3 + floor_num / 2
			speed = 95.0 + floor_num * 6.0
			touch_damage = 12.0 + floor_num
			xp = 10
			_base = "e_shambler"
			_spr_scale = 0.6
			_hbox = Vector2.ONE
	hp = max_hp

func _main() -> Node:
	var n: Node = self
	while n:
		if n.has_method("hitstop"):
			return n
		n = n.get_parent()
	return null

func _ready() -> void:
	add_to_group("infected")
	var sf := SpriteFrames.new()
	_add_frames(sf, "walk",
		[_base + "_walk_0", _base + "_walk_1", _base + "_walk_2", _base + "_walk_3"],
		8.0, true)
	_add_frames(sf, "attack", [_base + "_attack_0", _base + "_attack_1"], 10.0, false)
	_add_frames(sf, "death", [_base + "_death_0", _base + "_death_1"], 6.0, false)
	$Sprite.frames = sf
	$Sprite.play("walk")
	$Sprite.scale = Vector2(_spr_scale, _spr_scale)
	$CollisionShape2D.scale = _hbox
	var sh := Sprite2D.new()
	sh.texture = load("res://assets/shadow.png")
	sh.position = Vector2(0, 128.0 * _spr_scale + 4.0)
	add_child(sh)
	move_child(sh, 0)

func _add_frames(sf: SpriteFrames, name: String, files: Array, fps: float, loop: bool) -> void:
	sf.add_animation(name)
	sf.set_animation_speed(name, fps)
	sf.set_animation_loop(name, loop)
	for f in files:
		sf.add_frame(name, load("res://assets/%s.png" % f) as Texture2D)

func _physics_process(delta: float) -> void:
	if dead:
		return
	_hit_flash = maxf(0.0, _hit_flash - delta)
	_atk_cd = maxf(0.0, _atk_cd - delta)
	_knockback = _knockback.move_toward(Vector2.ZERO, 1400.0 * delta)
	var player := get_tree().get_first_node_in_group("player")
	if player == null or player.dead:
		velocity = velocity.move_toward(_knockback, 1200.0 * delta)
		move_and_slide()
		return
	var to_p: Vector2 = player.global_position - global_position
	var dist := to_p.length()
	# --- attack: telegraph, then lunge + damage ---
	if _windup > 0.0:
		_windup -= delta
		velocity = velocity.move_toward(Vector2.ZERO, 1500.0 * delta)
		$Sprite.modulate = Color(1.9, 0.5, 0.5)  # telegraph flash
		if $Sprite.animation != "attack":
			$Sprite.play("attack")
		if _windup <= 0.0:
			_atk_cd = 1.1
			_knockback = to_p.normalized() * 300.0
			Sfx.play("hit")
			if dist < 150.0:
				player.take_hit(touch_damage, global_position)
	elif dist < 120.0 and _atk_cd <= 0.0:
		_windup = 0.35
	else:
		$Sprite.modulate = Color(1.6, 0.7, 0.7) if _hit_flash > 0.0 else Color.WHITE
		if $Sprite.animation != "walk" or not $Sprite.is_playing():
			$Sprite.play("walk")
	# --- steering ---
	if _windup <= 0.0:
		if dist < 460.0:
			velocity = velocity.move_toward(to_p.normalized() * speed, 900.0 * delta)
			_bob_t += delta * 8.0
			$Sprite.position.y = sin(_bob_t) * 6.0
			$Sprite.flip_h = to_p.x < 0.0
		else:
			velocity = velocity.move_toward(Vector2.ZERO, 700.0 * delta)
			$Sprite.position.y = 0.0
	# --- separation (distance-weighted, anti-stack) ---
	for o in get_tree().get_nodes_in_group("infected"):
		if o == self or (o as Node2D).get("dead"):
			continue
		var d: Vector2 = global_position - (o as Node2D).global_position
		var l := d.length()
		if l > 1.0 and l < 110.0:
			velocity += d.normalized() * (150.0 * (1.0 - l / 110.0))
	velocity += _knockback
	move_and_slide()
	velocity -= _knockback

func take_damage(amount: int) -> void:
	if dead:
		return
	hp -= amount
	_hit_flash = 0.12
	var p := get_tree().get_first_node_in_group("player")
	if p:
		var away: Vector2 = global_position - (p as Node2D).global_position
		if away.length() > 1.0:
			_knockback = away.normalized() * 300.0
	Sfx.play("hit")
	var main := _main()
	if main:
		main.fx_sparks(global_position + Vector2(0, -30), Color(0.6, 1.0, 0.6))
	if hp <= 0:
		_die()

func _die() -> void:
	dead = true
	collision_layer = 0
	collision_mask = 0
	Sfx.play("die")
	$Sprite.play("death")
	$Sprite.modulate = Color.WHITE
	var main := _main()
	if main:
		main.hitstop(0.09)
		main.shake(0.3)
		main.fx_sparks(global_position + Vector2(0, -40), Color(0.4, 1.0, 0.5))
		main.fx_dust(global_position + Vector2(0, 40), 4)
		main.call("on_infected_killed", global_position, xp, is_boss)
	var tw := create_tween()
	tw.tween_interval(0.5)          # death pose reads clearly
	tw.tween_property($Sprite, "modulate:a", 0.0, 0.3)
	tw.tween_callback(queue_free)
""")
print("infected ok")

# ================= scripts/slash.gd =================
W("scripts/slash.gd", """extends Area2D
## Sword slash hitbox. Lives 0.18s, damages infected once each.

var damage := 1
var _life := 0.18
var _hit := {}

func _ready() -> void:
	$Sprite.texture = load("res://assets/slash_thick.png")
	$Sprite.scale = Vector2(0.45, 0.45)
	body_entered.connect(_on_body)

func _physics_process(delta: float) -> void:
	_life -= delta
	$Sprite.rotation += 6.0 * delta
	if _life <= 0.0:
		queue_free()

func _on_body(body: Node2D) -> void:
	if _hit.has(body.get_instance_id()):
		return
	if body.is_in_group("infected") and body.has_method("take_damage"):
		_hit[body.get_instance_id()] = true
		body.take_damage(damage)
""")
print("slash ok")

# ================= scripts/pickup.gd =================
W("scripts/pickup.gd", """extends Area2D
## Loot pickup: scrap / suppressant / medkit / weapon.

@export var kind := "scrap"
var _t := 0.0
var _base_y := 0.0

const TEX := {
	"scrap": "coin_full",
	"suppressant": "suppressant",
	"medkit": "heart",
	"weapon": "sword",
}

# on-screen target ~52px; source assets are oversized
const PICKUP_SCALE := {
	"scrap": 0.16,
	"suppressant": 0.26,
	"medkit": 0.15,
	"weapon": 0.32,
}

func _ready() -> void:
	add_to_group("pickups")
	$Sprite.texture = load("res://assets/%s.png" % TEX.get(kind, "coin_full"))
	var sc: float = PICKUP_SCALE.get(kind, 0.2)
	$Sprite.scale = Vector2(sc, sc)
	_base_y = $Sprite.position.y
	body_entered.connect(_on_body)

func _process(delta: float) -> void:
	_t += delta
	$Sprite.position.y = _base_y + sin(_t * 3.0) * 10.0

func _on_body(body: Node2D) -> void:
	if not body.is_in_group("player") or body.dead:
		return
	match kind:
		"scrap":
			body.add_scrap(1)
		"suppressant":
			body.add_infection(-30.0)
		"medkit":
			body.heal(30.0)
		"weapon":
			var main := get_tree().get_first_node_in_group("game_main")
			if main and main.has_method("on_weapon_pickup"):
				main.on_weapon_pickup()
	Sfx.play("pickup")
	queue_free()
""")

# ================= scripts/sfx.gd =================
W("scripts/sfx.gd", """extends Node
## Sfx: pooled one-shot sound effects, callable anywhere as Sfx.play("hit").

var _players: Array[AudioStreamPlayer] = []
var _streams: Dictionary = {}
var _idx := 0

const NAMES := ["swing", "hit", "die", "pickup", "surge", "frenzy", "sense",
	"extract_tick", "upgrade", "hurt", "turn", "levelup", "click"]

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	for n in NAMES:
		_streams[n] = load("res://assets/audio/%s.wav" % n) as AudioStream
	for i in range(10):
		var p := AudioStreamPlayer.new()
		add_child(p)
		_players.append(p)

func play(n: String, pitch := 1.0) -> void:
	if not _streams.has(n) or _streams[n] == null:
		return
	var p := _players[_idx]
	_idx = (_idx + 1) % _players.size()
	p.stream = _streams[n]
	p.pitch_scale = pitch * randf_range(0.94, 1.06)
	p.play()
""")
print("pickup ok")

# ================= scripts/hud.gd =================
W("scripts/hud.gd", """extends CanvasLayer
## HUD: HP + infection bars, scrap, floor, power buttons, joystick, channel, draft, death.

var player: CharacterBody2D
var boss_ref: Node = null
var boss_bar: ProgressBar
var boss_label: Label
var hp_bar: ProgressBar
var inf_bar: ProgressBar
var inf_label: Label
var scrap_label: Label
var lvl_label: Label
var xp_bar: ProgressBar
var floor_label: Label
var toast_label: Label
var surge_btn: Button
var frenzy_btn: Button
var sense_btn: Button
var atk_btn: Button
var dodge_btn: Button
var joy_base: Sprite2D
var joy_knob: Sprite2D
var channel_bar: ProgressBar
var channel_label: Label
var hp_num: Label
var hp_fill: StyleBoxFlat
var draft_panel: PanelContainer
var death_panel: PanelContainer
var minimap: Minimap
var corrupt: ColorRect
var _crit_warned := false
var _t := 0.0
var _toast_t := 0.0

class Minimap extends Control:
	var rooms: Array = []
	var world_rect := Rect2(-1080, -1080, 2160, 2160)
	func _process(_d: float) -> void:
		queue_redraw()
	func _w2m(wpos: Vector2) -> Vector2:
		var k := minf(size.x / world_rect.size.x, size.y / world_rect.size.y)
		var org := (size - world_rect.size * k) / 2.0
		return org + (wpos - world_rect.position) * k
	func _draw() -> void:
		var r := Rect2(Vector2.ZERO, size)
		draw_rect(r, Color(0, 0, 0, 0.55))
		var k := minf(size.x / world_rect.size.x, size.y / world_rect.size.y)
		for rm in rooms:
			var c: Vector2 = (rm as Dictionary)["center"]
			var rr := Rect2(_w2m(c - Vector2(360, 360)), Vector2(720, 720) * k)
			draw_rect(rr, Color(0.12, 0.14, 0.16, 0.9))
			draw_rect(rr, Color(0.3, 1.0, 0.5, 0.3), false, 1.0)
		draw_rect(r, Color(0.3, 1.0, 0.5, 0.8), false, 2.0)
		for pd in get_tree().get_nodes_in_group("extract_pad"):
			var c: Vector2 = _w2m((pd as Node2D).global_position)
			var pulse := 5.0 + 2.0 * sin(Time.get_ticks_msec() / 300.0)
			draw_circle(c, pulse, Color(0.3, 1.0, 0.5, 0.9))
		for ck in get_tree().get_nodes_in_group("chests"):
			if not ((ck as Node).get_meta("opened") as bool):
				draw_circle(_w2m((ck as Node2D).global_position), 3.0, Color(1.0, 0.75, 0.2, 0.9))
		for pk in get_tree().get_nodes_in_group("pickups"):
			draw_circle(_w2m((pk as Node2D).global_position), 2.5, Color(1.0, 0.85, 0.2, 0.9))
		for e in get_tree().get_nodes_in_group("infected"):
			if not (e as Node).get("dead"):
				var col := Color(1.0, 0.25, 0.25, 0.9)
				if (e as Node).get("is_boss") as bool:
					col = Color(1.0, 0.0, 0.0, 1.0)
				draw_circle(_w2m((e as Node2D).global_position), 3.0, col)
		var pl := get_tree().get_first_node_in_group("player")
		if pl:
			draw_circle(_w2m((pl as Node2D).global_position), 4.5, Color.WHITE)

func _ready() -> void:
	# dungeon vignette (drawn behind everything)
	var grad := Gradient.new()
	grad.set_color(0, Color(0, 0, 0, 0))
	grad.set_color(1, Color(0, 0, 0, 0.5))
	var gtex := GradientTexture2D.new()
	gtex.gradient = grad
	gtex.fill = GradientTexture2D.FILL_RADIAL
	gtex.fill_from = Vector2(0.5, 0.5)
	gtex.fill_to = Vector2(1.0, 0.5)
	gtex.width = 720
	gtex.height = 1280
	var vig := TextureRect.new()
	vig.set_anchors_preset(Control.PRESET_FULL_RECT)
	vig.texture = gtex
	vig.stretch_mode = TextureRect.STRETCH_SCALE
	vig.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(vig)
	# corruption vignette: the screen rots as infection climbs (under the buttons)
	corrupt = ColorRect.new()
	corrupt.set_anchors_preset(Control.PRESET_FULL_RECT)
	corrupt.color = Color(0.45, 0.06, 0.1)
	corrupt.modulate.a = 0.0
	corrupt.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(corrupt)
	# joystick visuals first so buttons always draw on top of them
	joy_base = Sprite2D.new()
	joy_base.texture = load("res://assets/joy_base.png")
	joy_base.modulate.a = 0.55
	joy_base.visible = false
	add_child(joy_base)
	joy_knob = Sprite2D.new()
	joy_knob.texture = load("res://assets/joy_knob.png")
	joy_knob.modulate.a = 0.8
	joy_knob.visible = false
	add_child(joy_knob)
	hp_bar = _bar(Vector2(24, 24), Vector2(300, 28), Color(0.85, 0.2, 0.2))
	hp_fill = hp_bar.get_theme_stylebox("fill") as StyleBoxFlat
	hp_num = _label(Vector2(30, 26), 20, "100")
	inf_bar = _bar(Vector2(24, 60), Vector2(300, 28), Color(0.25, 1.0, 0.42))
	inf_label = _label(Vector2(24, 92), 22, "INFECTION 0%")
	inf_label.add_theme_color_override("font_color", Color(0.35, 1.0, 0.5))
	scrap_label = _label(Vector2(24, 124), 24, "SCRAP 0")
	lvl_label = _label(Vector2(24, 156), 22, "LV 1")
	xp_bar = _bar(Vector2(92, 160), Vector2(232, 18), Color(0.6, 0.4, 1.0))
	floor_label = _label(Vector2(340, 24), 30, "DEPTH 1")
	boss_label = _label(Vector2(295, 66), 24, "THE WARDEN")
	boss_label.add_theme_color_override("font_color", Color(1.0, 0.3, 0.3))
	boss_label.visible = false
	boss_bar = _bar(Vector2(210, 100), Vector2(300, 22), Color(0.75, 0.12, 0.12))
	boss_bar.visible = false
	toast_label = _label(Vector2(110, 240), 34, "")
	toast_label.visible = false
	minimap = Minimap.new()
	minimap.position = Vector2(528, 24)
	minimap.size = Vector2(168, 168)
	add_child(minimap)
	surge_btn = _power_btn(Vector2(430, 870), "SURGE", Color(0.2, 0.7, 1.0), Vector2(140, 100), 16)
	frenzy_btn = _power_btn(Vector2(430, 985), "FRENZY", Color(1.0, 0.45, 0.2), Vector2(140, 100), 16)
	sense_btn = _power_btn(Vector2(430, 1100), "SENSE", Color(0.3, 1.0, 1.0), Vector2(140, 100), 16)
	atk_btn = _power_btn(Vector2(585, 990), "ATTACK", Color(1.0, 0.85, 0.2), Vector2(125, 175), 60)
	atk_btn.add_theme_font_size_override("font_size", 28)
	# DODGE: its own button above ATTACK. Double-tap on the joystick kept
	# firing accidental rolls; a real button is precise.
	dodge_btn = _power_btn(Vector2(585, 862), "DODGE", Color(0.55, 0.85, 1.0), Vector2(125, 110), 60)
	dodge_btn.add_theme_font_size_override("font_size", 24)
	dodge_btn.pressed.connect(func():
		if player and not player.dead:
			var d: Vector2 = player.joystick
			if d.length() < 0.1:
				d = player.facing
			player.try_dodge(d))
	surge_btn.pressed.connect(func(): if player: player.try_surge())
	frenzy_btn.pressed.connect(func(): if player: player.try_frenzy())
	sense_btn.pressed.connect(func(): if player: player.try_sense())
	atk_btn.button_down.connect(func():
		if player and not player.dead:
			player.touch_atk_held = true
			player.attack())
	atk_btn.button_up.connect(func():
		if player:
			player.touch_atk_held = false)
	channel_label = _label(Vector2(210, 180), 26, "EXTRACTING...")
	channel_label.add_theme_color_override("font_color", Color(0.35, 1.0, 0.5))
	channel_label.visible = false
	channel_bar = _bar(Vector2(210, 214), Vector2(300, 22), Color(0.25, 1.0, 0.42))
	channel_bar.visible = false
	draft_panel = _panel()
	death_panel = _panel()

func _bar(pos: Vector2, size: Vector2, fill: Color) -> ProgressBar:
	var b := ProgressBar.new()
	b.position = pos
	b.size = size
	b.min_value = 0
	b.max_value = 100
	b.value = 100
	b.show_percentage = false
	var bg := StyleBoxFlat.new()
	bg.bg_color = Color(0, 0, 0, 0.6)
	bg.border_color = Color(1, 1, 1, 0.22)
	bg.set_border_width_all(2)
	bg.set_corner_radius_all(6)
	var fg := StyleBoxFlat.new()
	fg.bg_color = fill
	fg.set_corner_radius_all(5)
	fg.content_margin_left = 2
	fg.content_margin_right = 2
	fg.content_margin_top = 2
	fg.content_margin_bottom = 2
	b.add_theme_stylebox_override("background", bg)
	b.add_theme_stylebox_override("fill", fg)
	add_child(b)
	return b

func _label(pos: Vector2, fsize: int, text: String) -> Label:
	var l := Label.new()
	l.position = pos
	l.add_theme_font_size_override("font_size", fsize)
	l.add_theme_color_override("font_color", Color.WHITE)
	l.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.9))
	l.add_theme_constant_override("shadow_offset_x", 2)
	l.add_theme_constant_override("shadow_offset_y", 2)
	l.text = text
	add_child(l)
	return l

func _btn_style(color: Color, radius: int) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = Color(0.04, 0.05, 0.07, 0.88)
	s.border_color = color
	s.set_border_width_all(3)
	s.set_corner_radius_all(radius)
	return s

func _power_btn(pos: Vector2, text: String, color: Color, bsize := Vector2(150, 110), radius := 14) -> Button:
	var b := Button.new()
	b.position = pos
	b.size = bsize
	b.text = text
	b.add_theme_font_size_override("font_size", 24)
	b.add_theme_color_override("font_color", Color(0.95, 0.95, 0.95))
	b.add_theme_color_override("font_pressed_color", Color.WHITE)
	b.add_theme_color_override("font_disabled_color", Color(0.5, 0.5, 0.5))
	b.add_theme_stylebox_override("normal", _btn_style(color, radius))
	b.add_theme_stylebox_override("hover", _btn_style(color, radius))
	var pr := _btn_style(color, radius)
	pr.bg_color = Color(color.r * 0.4, color.g * 0.4, color.b * 0.4, 0.95)
	b.add_theme_stylebox_override("pressed", pr)
	var dis := _btn_style(Color(0.35, 0.35, 0.35), radius)
	b.add_theme_stylebox_override("disabled", dis)
	b.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	add_child(b)
	return b

func _panel() -> PanelContainer:
	var p := PanelContainer.new()
	p.set_anchors_preset(Control.PRESET_CENTER)
	p.visible = false
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.02, 0.03, 0.04, 0.94)
	sb.border_color = Color(0.25, 1.0, 0.42)
	sb.set_border_width_all(3)
	sb.set_corner_radius_all(16)
	sb.content_margin_left = 36
	sb.content_margin_right = 36
	sb.content_margin_top = 28
	sb.content_margin_bottom = 28
	p.add_theme_stylebox_override("panel", sb)
	add_child(p)
	return p

func bind(p: CharacterBody2D) -> void:
	player = p

func set_floor(n: int) -> void:
	floor_label.text = "DEPTH %d" % n

func set_dungeon(rooms: Array) -> void:
	minimap.rooms = rooms
	var mn := Vector2(INF, INF)
	var mx := Vector2(-INF, -INF)
	for r in rooms:
		var c: Vector2 = (r as Dictionary)["center"]
		mn = mn.min(c - Vector2(360, 360))
		mx = mx.max(c + Vector2(360, 360))
	minimap.world_rect = Rect2(mn, mx - mn)

func set_boss(b: Node) -> void:
	boss_ref = b
	boss_bar.visible = b != null
	boss_label.visible = b != null

func show_toast(t: String) -> void:
	toast_label.text = t
	toast_label.visible = true
	toast_label.modulate.a = 1.0
	_toast_t = 1.8

func set_channel(frac: float) -> void:
	if frac < 0.0:
		channel_bar.visible = false
		channel_label.visible = false
	else:
		channel_bar.visible = true
		channel_label.visible = true
		channel_bar.value = frac * 100.0

func show_joystick(pos: Vector2) -> void:
	joy_base.position = pos
	joy_knob.position = pos
	joy_base.visible = true
	joy_knob.visible = true

func move_knob(pos: Vector2) -> void:
	joy_knob.position = pos

func hide_joystick() -> void:
	joy_base.visible = false
	joy_knob.visible = false

func show_draft(picks: Array, cb: Callable) -> void:
	for c in draft_panel.get_children():
		c.queue_free()
	var vb := VBoxContainer.new()
	vb.add_theme_constant_override("separation", 14)
	draft_panel.add_child(vb)
	var title := Label.new()
	title.text = "FLOOR CLEARED - CHOOSE"
	title.add_theme_font_size_override("font_size", 30)
	title.add_theme_color_override("font_color", Color(0.35, 1.0, 0.5))
	vb.add_child(title)
	for u in picks:
		var b := Button.new()
		b.text = "%s: %s" % [u["name"], u["desc"]]
		b.custom_minimum_size = Vector2(420, 96)
		b.add_theme_font_size_override("font_size", 26)
		b.add_theme_color_override("font_color", Color(0.95, 0.95, 0.95))
		b.add_theme_stylebox_override("normal", _btn_style(Color(0.25, 1.0, 0.42), 12))
		b.add_theme_stylebox_override("hover", _btn_style(Color(0.25, 1.0, 0.42), 12))
		b.add_theme_stylebox_override("pressed", _btn_style(Color(0.1, 0.6, 0.25), 12))
		b.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
		var uu: Dictionary = u
		b.pressed.connect(func(): draft_panel.visible = false; cb.call(uu))
		vb.add_child(b)
	draft_panel.visible = true
	await get_tree().process_frame
	draft_panel.set_anchors_preset(Control.PRESET_CENTER)

func show_death(turned: bool, floor: int, scrap: int) -> void:
	for c in death_panel.get_children():
		c.queue_free()
	var vb := VBoxContainer.new()
	vb.add_theme_constant_override("separation", 14)
	death_panel.add_child(vb)
	var title := Label.new()
	title.text = "YOU TURNED" if turned else "YOU DIED"
	title.add_theme_font_size_override("font_size", 44)
	title.add_theme_color_override("font_color", Color(0.6, 1.0, 0.4) if turned else Color(1.0, 0.3, 0.3))
	vb.add_child(title)
	var stats := Label.new()
	stats.text = "Reached floor %d - Scrap: %d" % [floor, scrap]
	stats.add_theme_font_size_override("font_size", 26)
	vb.add_child(stats)
	var rb := Button.new()
	rb.text = "RUN IT BACK"
	rb.custom_minimum_size = Vector2(420, 96)
	rb.add_theme_font_size_override("font_size", 30)
	rb.add_theme_color_override("font_color", Color(0.95, 0.95, 0.95))
	rb.add_theme_stylebox_override("normal", _btn_style(Color(0.25, 1.0, 0.42), 12))
	rb.add_theme_stylebox_override("hover", _btn_style(Color(0.25, 1.0, 0.42), 12))
	rb.add_theme_stylebox_override("pressed", _btn_style(Color(0.1, 0.6, 0.25), 12))
	rb.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	rb.pressed.connect(func(): get_tree().paused = false; get_tree().reload_current_scene())
	vb.add_child(rb)
	death_panel.visible = true
	await get_tree().process_frame
	death_panel.set_anchors_preset(Control.PRESET_CENTER)

func _process(delta: float) -> void:
	_t += delta
	if _toast_t > 0.0:
		_toast_t -= delta
		toast_label.modulate.a = clampf(_toast_t, 0.0, 1.0)
		if _toast_t <= 0.0:
			toast_label.visible = false
	if player == null or not is_instance_valid(player):
		return
	# corruption vignette: screen rots as infection climbs, pulses hard past 70
	var inf := float(player.infection)
	var target := 0.0
	if inf >= 55.0:
		var rate := 9.0 if inf >= 70.0 else 4.0
		target = (inf - 55.0) / 45.0 * 0.30 * (0.75 + 0.25 * sin(_t * rate))
	corrupt.modulate.a = lerpf(corrupt.modulate.a, target, clampf(8.0 * delta, 0.0, 1.0))
	if inf >= 70.0 and not _crit_warned:
		_crit_warned = true
		show_toast("INFECTION CRITICAL — power surges, body fails")
	elif inf < 55.0:
		_crit_warned = false
	hp_bar.max_value = player.max_hp
	hp_bar.value = player.hp
	hp_num.text = "%d" % int(ceil(player.hp))
	var frac: float = float(player.hp) / maxf(float(player.max_hp), 1.0)
	if frac > 0.5:
		hp_fill.bg_color = Color(0.85, 0.2, 0.2)
	elif frac > 0.25:
		hp_fill.bg_color = Color(0.9, 0.65, 0.15)
	else:
		var pulse := 0.75 + 0.25 * sin(_t * 8.0)
		hp_fill.bg_color = Color(1.0 * pulse, 0.15, 0.15)
	inf_bar.value = player.infection
	inf_label.text = "INFECTION %d%%" % int(player.infection)
	if boss_ref != null:
		if not is_instance_valid(boss_ref) or (boss_ref.get("dead") as bool):
			set_boss(null)
		else:
			boss_bar.max_value = float(boss_ref.get("max_hp"))
			boss_bar.value = float(boss_ref.get("hp"))
	if player.infection > 75.0:
		inf_label.add_theme_color_override("font_color", Color(1.0, 0.35, 0.35))
	else:
		inf_label.add_theme_color_override("font_color", Color(0.35, 1.0, 0.5))
	scrap_label.text = "SCRAP %d" % player.scrap
	lvl_label.text = "LV %d" % player.level
	xp_bar.max_value = player.xp_next
	xp_bar.value = player.xp
	_upd_btn(surge_btn, "SURGE", player.surge_cost, player.surge_cd, player.infection)
	_upd_btn(frenzy_btn, "FRENZY", player.frenzy_cost, player.frenzy_cd, player.infection)
	_upd_btn(sense_btn, "SENSE", player.sense_cost, player.sense_cd, player.infection)
	if player.dodge_cd > 0.0:
		dodge_btn.text = "DODGE %ds" % int(ceil(player.dodge_cd))
		dodge_btn.disabled = true
	else:
		dodge_btn.text = "DODGE"
		dodge_btn.disabled = false

func _upd_btn(b: Button, name: String, cost: float, cd: float, inf: float) -> void:
	if cd > 0.0:
		b.text = "%s %ds" % [name, int(ceil(cd))]
		b.disabled = true
	elif inf + cost >= 100.0:
		b.text = "%s RISK" % name
		b.disabled = true
	else:
		b.text = "%s -%d" % [name, int(cost)]
		b.disabled = false
""")
print("hud ok")

# ================= scripts/title.gd =================
W("scripts/title.gd", """extends Node2D

var _t := 0.0
var prompt: Label

func _ready() -> void:
	var bg := ColorRect.new()
	bg.color = Color(0.03, 0.035, 0.05)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	var tile_tex := load("res://assets/floor_a.png") as Texture2D
	for ix in range(3):
		for iy in range(3):
			var sp := Sprite2D.new()
			sp.texture = tile_tex
			sp.position = Vector2(360 + ix * 300, 420 + iy * 300) - Vector2(300, 300)
			sp.modulate = Color(0.4, 0.42, 0.46)
			add_child(sp)
	var hero := Sprite2D.new()
	hero.texture = load("res://assets/p_down_idle_0.png")
	hero.scale = Vector2(0.5, 0.5)
	hero.position = Vector2(360, 500)
	add_child(hero)
	var title := Label.new()
	title.text = "CARRIER"
	title.add_theme_font_size_override("font_size", 130)
	title.add_theme_color_override("font_color", Color(0.25, 1.0, 0.42))
	title.position = Vector2(110, 700)
	add_child(title)
	var sub := Label.new()
	sub.text = "ride the infection. extract alive."
	sub.add_theme_font_size_override("font_size", 34)
	sub.add_theme_color_override("font_color", Color(0.7, 0.75, 0.8))
	sub.position = Vector2(110, 870)
	add_child(sub)
	prompt = Label.new()
	prompt.text = "TAP TO START"
	prompt.add_theme_font_size_override("font_size", 44)
	prompt.add_theme_color_override("font_color", Color.WHITE)
	prompt.position = Vector2(190, 1050)
	add_child(prompt)
	var ver := Label.new()
	ver.text = "v0.8"
	ver.add_theme_font_size_override("font_size", 24)
	ver.add_theme_color_override("font_color", Color(0.45, 0.5, 0.55))
	ver.position = Vector2(330, 1210)
	add_child(ver)

func _process(delta: float) -> void:
	_t += delta
	prompt.modulate.a = 0.5 + 0.5 * sin(_t * 4.0)

func _input(event: InputEvent) -> void:
	if event is InputEventScreenTouch and event.pressed:
		_go()
	elif event is InputEventMouseButton and event.pressed:
		_go()
	elif event is InputEventKey and event.pressed and not event.echo:
		_go()

func _go() -> void:
	get_tree().change_scene_to_file("res://scenes/main.tscn")
""")
print("title ok")

# ================= DESIGN.md =================
W("DESIGN.md", """# CARRIER - design doc (working title, not final)

Original dungeon-descent extraction RPG. LAST SHIFT outbreak universe.
Core mechanic (Tbandz picked 2026-09-29): the INFECTION METER.
Direction call 2026-09-29: it's a DUNGEON game - descend the depths, fight
dungeon creatures (the infected), extract down. "FLOOR" renamed "DEPTH",
darker dungeon mood (vignette, dim tiles).

## The loop
1. Drop into a dungeon depth (top-down 2D pixel art).
2. Fight infected (shamblers, runners, brutes), grab loot (scrap / suppressant / medkit).
3. Reach the glowing extraction pad, channel 3s to descend.
4. Draft 1 of 3 upgrades between depths.
5. Die (HP 0) or TURN (infection 100%) = run over. Run it back.

## The infection meter (0-100%)
- Rises: +0.35/s passive, +6 per hit taken, powers cost chunks.
- Spend it: SURGE (3s +80% speed, 15%), FRENZY (5s 2x damage, 20%).
- Lowers: suppressant pickup -30%, extraction pad -5%/s while channeling.
- 100% = you turn. Run over.

## Risk/reward (the longevity engine)
Push deeper for better loot or extract and bank it. Harder floors scale
infected HP/speed/damage + spawn rate. Upgrade draft compounds builds.

## Phase 1 (shipped scope)
- Procedural floors (seeded), border + interior walls, rubble/door decor
- 1 infected type (crawler), spawner, touch damage
- Melee swing, 2 powers, suppressant/medkit/scrap
- Extraction pad + channel + floor progression
- 4-upgrade draft pool, death/turn screens, retry
- Touch: floating joystick (left), tap right = attack, power buttons
- Desktop: WASD/arrows, Space, Q/E

## Later phases
- Meta progression: XP, skill tree, base upgrades (persist across runs)
- More infected types, boss floors
- More dungeon biomes, daily seeded dungeon

## Phase 2 (shipped 2026-09-29)
- 3 infected types with real art: SHAMBLER (slow, tanky, floor 1), RUNNER
  (fast, fragile, floor 2+), BRUTE (big, heavy hitter, floor 3+)
- 13 synthesized sound effects (swing/hit/die/pickup/powers/level/death/extract ticks)
- SENSE power (10% infection, 4s loot+pad markers, 10s cd, key F)
- XP/levels: kills grant XP, level-ups heal 30%, +12 max HP, +1 dmg every 2nd level
- Big ATTACK button (kept tap-right attack); SENSE joins SURGE/FRENZY buttons
- Minimap: player/pad/pickups/infected dots, pulsing extraction marker
- Animation: attack lunge, walk bob, hit knockback + flash, shrink-out death
- Dungeon reframe: DEPTH label, darker tiles, vignette
- QA: 22/22 integration tests green (1 real bug found + fixed: kill rewards
  skipped when main wasn't current_scene - group fallback added)

## Phase 3 (shipped 2026-09-29) - DUNGEON DEPTHS
- Seeded multi-room dungeons replace the single open floor: entrance /
  combat / treasure / extraction room types, door gaps between connected
  rooms, tiled wall blocks, extraction pad in the farthest room (BFS)
- Chests: touch to open, 3-pickup loot shower, gold marker on minimap
- Weapons as loot: WORN SHIV -> RUSTY BLADE -> HUNTER'S EDGE -> PLAGUEBANE
  (tier by depth), each +1 damage with a toast; drop from brutes (12%),
  chests, and the boss (guaranteed)
- Boss every 3rd depth: THE WARDEN (brute, 6x HP, 1.5x damage, 1.5x size),
  red boss HP bar under the DEPTH label, guards the extraction pad,
  drops weapon + medkit + suppressant + 3 scrap, 150 XP
- Minimap draws the actual room layout (rects), chest + boss markers
- Touch fixes: screen->canvas coordinate conversion (fixed button taps
  double-firing attacks + joystick misplacement), left-half joystick zone,
  tactile styled buttons (normal/pressed/disabled states), joystick drawn
  under buttons, v0.3 build label on title
- QA: 27/27 phase-3 integration tests (connectivity, chest, weapon, boss,
  drops, minimap, depth-2 rebuild), 22/22 phase-2 regression green
- Deploy fix: root URL was serving the stale phase-1 index.* while the new
  build sat at carrier.html - now exports as index.* (root) and mirrors to
  carrier.* so both URLs serve the current build

## Phase 4 (shipped 2026-09-29) - GATE / ART / ANIMATION / PHYSICS / UI POLISH
- First-room exit fixed and rebuilt as a real GATE: DOOR_GAP widened
  180 -> 280, player collision shrunk to 52x64, doorway center has NO
  collision - two stone gatepost sprites flank the opening with a soft
  infection glow. Physics walk-through test proves traversal.
- New character art (48 generated frames): hooded outbreak carrier
  (glowing infection eyes, blade), SHAMBLER / RUNNER / BRUTE redesigns.
- Full animation contract: player idle/walk (3 directions, 4-frame walk),
  attack (3 frames), hurt, death; infected walk (4) / attack (2) / death (2).
  Attack + hurt anim locks; death pose reads 0.5s then fades.
- Combat physics: accel/decel movement, knockback with decay, enemy
  steering smoothing, distance-weighted separation (anti-stack), attack
  telegraph (0.35s windup) + lunge + cooldown, hit-stop on slash/kill,
  screen shake (trauma-based) on player hit/kill. Engine.time_scale always
  reset on death/draft/scene load.
- UI cleanup: bordered bars, HP number + green/yellow/red states with
  low-HP pulse, styled draft/death buttons, infection emphasis kept.
- Graphics: 4 floor tile variants (base/crack/grime/infection moss) in
  seeded 6x6 per-room mix, gate glows, pulsing extraction pad glow.
- Run-state persistence across depths still unproven (known issue).
- QA: walk-through PASS, 22/22 phase-2, 27/27 phase-3, zero script errors.

## Phase 5 (shipped 2026-09-29) - HD SPRITE PASS
- All 48 character frames redrawn at 2x (192x256) with gradient shading,
  rim light, glowing eyes/cracks, detailed cloth/armor/blade work.
- HD environment: 4 floor tiles (240px, fine grain + bevels), wall blocks
  (stone courses, mortar, moss), gate posts (carved stones, glowing runes),
  HD sword pickup + chests (open chest glows).
- Sprite scales halved to keep on-screen sizes; collisions unchanged.
- QA: walk-through PASS, 22/22 phase-2, 27/27 phase-3, zero script errors.

## RPG roadmap (Tbandz's blueprint, staged)
Loop: Explore -> Fight -> Loot -> Upgrade -> Discover -> Boss -> New
Dungeon -> Repeat. Infection meter stays the signature mechanic.
- Phase 4: inventory UI + equippable weapons/armor, loot rarity tiers,
  gold economy, elite infected, miniboss on depth 2 of each cycle
- Phase 5: combat depth - combos, dodge roll, block, crits, status effects
  (bleed/burn), elemental damage types, active skills beyond the 3 powers
- Phase 6: town/hub between cycles - NPCs, merchants, quests, crafting,
  multiple dungeon biomes, save data, achievements
- Phase 7: endgame - New Game+, endless dungeon, boss rush, challenge
  modifiers, daily seeded dungeon
Rules: classes optional (identity via equipment); hand-designed room
archetypes with randomized order; no duplicate systems; $0-first;
iPhone 12 smooth; every build gets a bug-check pass; Tbandz is final QA.
""")
print("BUILD COMPLETE")
