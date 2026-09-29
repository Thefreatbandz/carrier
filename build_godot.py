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
# fix export path
p = os.path.join(ROOT, "export_presets.cfg")
s = open(p).read().replace(
    "/home/hatch/workspace/last-shift/build/web/index.html",
    "/home/hatch/workspace/godot-rpg/carrier/build/web/index.html")
open(p, "w").write(s)
print("export_presets.cfg copied + repathed")

# ================= icon.svg =================
W("icon.svg", """<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128"><rect width="128" height="128" rx="24" fill="#0a0c10"/><circle cx="64" cy="64" r="34" fill="none" stroke="#39ff6a" stroke-width="8"/><circle cx="64" cy="64" r="12" fill="#39ff6a"/></svg>
""")
print("PART1 done")

# ================= scenes =================
W("scenes/title.tscn", """[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/title.gd" id="1"]

[node name="Title" type="Node2D"]
script = ExtResource("1")
""")

W("scenes/main.tscn", """[gd_scene load_steps=2 format=3]

[ext_resource type="Script" path="res://scripts/main.gd" id="1"]

[node name="Main" type="Node2D"]
script = ExtResource("1")
""")

W("scenes/player.tscn", """[gd_scene load_steps=3 format=3]

[ext_resource type="Script" path="res://scripts/player.gd" id="1"]

[sub_resource type="RectangleShape2D" id="body"]
size = Vector2(96, 110)

[node name="Player" type="CharacterBody2D"]
script = ExtResource("1")

[node name="Body" type="CollisionShape2D" parent="."]
position = Vector2(0, 90)
shape = SubResource("body")

[node name="Sprite" type="AnimatedSprite2D" parent="."]

[node name="Camera" type="Camera2D" parent="."]
position_smoothing_enabled = true
position_smoothing_speed = 8.0
zoom = Vector2(1.15, 1.15)
""")

W("scenes/infected.tscn", """[gd_scene load_steps=3 format=3]

[ext_resource type="Script" path="res://scripts/infected.gd" id="1"]

[sub_resource type="RectangleShape2D" id="body"]
size = Vector2(120, 100)

[node name="Infected" type="CharacterBody2D"]
collision_layer = 2
collision_mask = 1
script = ExtResource("1")

[node name="Body" type="CollisionShape2D" parent="."]
position = Vector2(0, 60)
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

const BASE_SPEED := 300.0
const PASSIVE_INFECTION := 0.35   # per second
const HIT_INFECTION := 6.0
var surge_cost := 15.0
var frenzy_cost := 20.0

var max_hp := 100.0
var hp := 100.0
var infection := 0.0
var damage := 1
var move_mult := 1.0
var scrap := 0

var facing := Vector2.DOWN
var joystick := Vector2.ZERO     # set by HUD touch controls
var attack_cd := 0.0
var hurt_cd := 0.0
var surge_t := 0.0               # active power timers
var frenzy_t := 0.0
var surge_cd := 0.0
var frenzy_cd := 0.0
var dead := false
var extract_cleanse := false     # standing on pad

var slash_scene := preload("res://scenes/slash.tscn")

func _ready() -> void:
	add_to_group("player")
	var sf := SpriteFrames.new()
	_add_anim(sf, "down", ["hero_down_idle", "hero_down_walk"])
	_add_anim(sf, "up", ["hero_up_idle", "hero_up_walk"])
	_add_anim(sf, "side", ["hero_sideL_idle", "hero_sideL_walk"])
	$Sprite.frames = sf
	$Sprite.play("down")
	$Sprite.scale = Vector2(0.35, 0.35)

func _add_anim(sf: SpriteFrames, name: String, files: Array) -> void:
	sf.add_animation(name)
	sf.set_animation_speed(name, 6.0)
	sf.set_animation_loop(name, true)
	for f in files:
		var tex := load("res://assets/%s.png" % f) as Texture2D
		sf.add_frame(name, tex)

func _physics_process(delta: float) -> void:
	if dead:
		return
	# --- timers ---
	attack_cd = maxf(0.0, attack_cd - delta)
	hurt_cd = maxf(0.0, hurt_cd - delta)
	surge_cd = maxf(0.0, surge_cd - delta)
	frenzy_cd = maxf(0.0, frenzy_cd - delta)
	surge_t = maxf(0.0, surge_t - delta)
	frenzy_t = maxf(0.0, frenzy_t - delta)
	# --- infection drift ---
	add_infection(PASSIVE_INFECTION * delta, true)
	if extract_cleanse:
		add_infection(-5.0 * delta, true)
	# --- movement ---
	var iv := Input.get_vector("mv_left", "mv_right", "mv_up", "mv_down")
	var mv := iv + joystick
	if mv.length() > 1.0:
		mv = mv.normalized()
	var spd := BASE_SPEED * move_mult
	if surge_t > 0.0:
		spd *= 1.8
	velocity = mv * spd
	move_and_slide()
	if mv.length() > 0.15:
		_face(mv)
		if not $Sprite.is_playing():
			$Sprite.play(_anim_name())
	else:
		$Sprite.stop()
		$Sprite.frame = 0
	emit_signal("changed")

func _face(mv: Vector2) -> void:
	facing = mv.normalized()
	$Sprite.flip_h = facing.x < -0.1
	$Sprite.play(_anim_name())

func _anim_name() -> String:
	if absf(facing.x) > 0.5:
		return "side"
	return "up" if facing.y < -0.1 else "down"

func attack() -> void:
	if dead or attack_cd > 0.0:
		return
	attack_cd = 0.42
	var s := slash_scene.instantiate()
	s.global_position = global_position + facing * 110.0
	s.rotation = facing.angle()
	s.damage = damage * (2 if frenzy_t > 0.0 else 1)
	get_parent().add_child(s)

func try_surge() -> void:
	if dead or surge_cd > 0.0 or infection + surge_cost >= 100.0:
		return
	add_infection(surge_cost)
	surge_t = 3.0
	surge_cd = 8.0
	emit_signal("changed")

func try_frenzy() -> void:
	if dead or frenzy_cd > 0.0 or infection + frenzy_cost >= 100.0:
		return
	add_infection(frenzy_cost)
	frenzy_t = 5.0
	frenzy_cd = 12.0
	emit_signal("changed")

func take_hit(amount: float) -> void:
	if dead or hurt_cd > 0.0:
		return
	hurt_cd = 0.6
	hp -= amount
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

func _die() -> void:
	dead = true
	emit_signal("died")

func _turn() -> void:
	dead = true
	infection = 100.0
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
var room := Vector2(2100, 2100)
var pad: Area2D
var channeling := false
var channel_t := 0.0
const CHANNEL_NEED := 3.0
var joy_id := -1
var joy_origin := Vector2.ZERO

const UPGRADES := [
	{"name": "MAX HP +20", "desc": "Sturdier body"},
	{"name": "DAMAGE +1", "desc": "Heavier swings"},
	{"name": "SPEED +10%", "desc": "Lighter feet"},
	{"name": "CHEAP POWERS", "desc": "Powers cost 25% less"},
]

func _ready() -> void:
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
	_add("surge", [KEY_Q])
	_add("frenzy", [KEY_E])

func _add(action: String, keys: Array) -> void:
	if not InputMap.has_action(action):
		InputMap.add_action(action)
	for k in keys:
		var ev := InputEventKey.new()
		ev.physical_keycode = k
		if not InputMap.action_has_event(action, ev):
			InputMap.action_add_event(action, ev)

func start_run() -> void:
	floor_num = 1
	room = Vector2(2100, 2100)
	build_floor()

func build_floor() -> void:
	# clear old floor (deferred; new one tracked via floor_node)
	if floor_node and is_instance_valid(floor_node):
		floor_node.queue_free()
	channeling = false
	channel_t = 0.0
	var f := Node2D.new()
	f.name = "Floor"
	add_child(f)
	floor_node = f
	# tiles
	var tile_tex := load("res://assets/floor_tile.png") as Texture2D
	var n := int(room.x / 640.0) + 1
	for ix in range(n):
		for iy in range(n):
			var sp := Sprite2D.new()
			sp.texture = tile_tex
			sp.scale = Vector2(640.0, 640.0) / tile_tex.get_size()
			sp.position = Vector2(ix * 640.0 + 320.0, iy * 640.0 + 320.0) - room / 2.0
			sp.modulate = Color(0.55, 0.58, 0.62)
			f.add_child(sp)
	# border walls
	_wall(f, Vector2(0, -room.y / 2), Vector2(room.x + 200, 100))
	_wall(f, Vector2(0, room.y / 2), Vector2(room.x + 200, 100))
	_wall(f, Vector2(-room.x / 2, 0), Vector2(100, room.y + 200))
	_wall(f, Vector2(room.x / 2, 0), Vector2(100, room.y + 200))
	# interior obstacles
	var wall_tex := load("res://assets/wall_block.png") as Texture2D
	var rub_tex := load("res://assets/rubble.png") as Texture2D
	var door_tex := load("res://assets/door.png") as Texture2D
	for i in range(4 + floor_num):
		var p := _open_spot(f, 300.0)
		if i % 3 == 0:
			_wall(f, p, Vector2(420, 420), wall_tex)
		else:
			var d := Sprite2D.new()
			d.texture = rub_tex if i % 2 == 0 else door_tex
			d.position = p
			d.scale = Vector2(0.7, 0.7)
			f.add_child(d)
	# player
	player = player_scene.instantiate()
	player.position = Vector2(-room.x / 2 + 260, room.y / 2 - 260)
	f.add_child(player)
	player.died.connect(_on_player_died.bind(false))
	player.turned.connect(_on_player_died.bind(true))
	hud.bind(player)
	# extraction pad far corner
	pad = Area2D.new()
	pad.collision_layer = 16
	pad.collision_mask = 1
	pad.position = Vector2(room.x / 2 - 320, -room.y / 2 + 320)
	var ps := Sprite2D.new()
	ps.texture = load("res://assets/extract_pad.png")
	ps.scale = Vector2(0.6, 0.6)
	pad.add_child(ps)
	var shape := CollisionShape2D.new()
	var circ := CircleShape2D.new()
	circ.radius = 190.0
	shape.shape = circ
	pad.add_child(shape)
	f.add_child(pad)
	pad.body_entered.connect(_on_pad_enter)
	pad.body_exited.connect(_on_pad_exit)
	# infected
	for i in range(mini(3 + floor_num, 9)):
		spawn_infected(_open_spot(f, 500.0))
	# loot
	for i in range(5):
		spawn_pickup("scrap", _open_spot(f, 200.0))
	for i in range(2):
		spawn_pickup("suppressant", _open_spot(f, 200.0))
	spawn_pickup("medkit", _open_spot(f, 200.0))
	# spawner timer
	var t := Timer.new()
	t.name = "Spawner"
	t.wait_time = 7.0
	t.autostart = true
	t.timeout.connect(_on_spawn_tick)
	f.add_child(t)
	hud.set_floor(floor_num)

func _wall(parent: Node, pos: Vector2, size: Vector2, tex: Texture2D = null) -> void:
	var sb := StaticBody2D.new()
	sb.position = pos
	var cs := CollisionShape2D.new()
	var rect := RectangleShape2D.new()
	rect.size = size
	cs.shape = rect
	sb.add_child(cs)
	if tex:
		var sp := Sprite2D.new()
		sp.texture = tex
		sp.scale = size / tex.get_size()
		sb.add_child(sp)
	parent.add_child(sb)

func _open_spot(f: Node, margin: float) -> Vector2:
	for tries in range(40):
		var p := Vector2(
			rng.randf_range(-room.x / 2 + margin, room.x / 2 - margin),
			rng.randf_range(-room.y / 2 + margin, room.y / 2 - margin))
		if player and p.distance_to(player.position) < 380.0:
			continue
		return p
	return Vector2.ZERO

func spawn_infected(pos: Vector2) -> void:
	var f := floor_node
	var e: CharacterBody2D = infected_scene.instantiate()
	e.position = pos
	e.max_hp = 3 + floor_num / 2
	e.hp = e.max_hp
	e.speed = 95.0 + floor_num * 6.0
	e.touch_damage = 12.0 + floor_num
	f.add_child(e)

func spawn_pickup(kind: String, pos: Vector2) -> void:
	var f := floor_node
	var p: Area2D = pickup_scene.instantiate()
	p.kind = kind
	p.position = pos
	f.add_child(p)

func on_infected_killed(pos: Vector2) -> void:
	var r := rng.randf()
	if r < 0.55:
		spawn_pickup("scrap", pos)
	elif r < 0.70:
		spawn_pickup("suppressant", pos)
	elif r < 0.78:
		spawn_pickup("medkit", pos)

func _on_spawn_tick() -> void:
	var count := get_tree().get_nodes_in_group("infected").size()
	if count < mini(4 + floor_num, 10) and player and not player.dead:
		var ang := rng.randf_range(0.0, TAU)
		var pos: Vector2 = player.position + Vector2(cos(ang), sin(ang)) * 800.0
		pos.x = clampf(pos.x, -room.x / 2 + 150, room.x / 2 - 150)
		pos.y = clampf(pos.y, -room.y / 2 + 150, room.y / 2 - 150)
		spawn_infected(pos)

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
	if channeling and player and not player.dead:
		channel_t += delta
		hud.set_channel(channel_t / CHANNEL_NEED)
		if channel_t >= CHANNEL_NEED:
			channeling = false
			player.extract_cleanse = false
			floor_cleared()

func floor_cleared() -> void:
	get_tree().paused = true
	var picks := UPGRADES.duplicate()
	picks.shuffle()
	hud.show_draft(picks.slice(0, 3), _on_upgrade)

func _on_upgrade(u: Dictionary) -> void:
	get_tree().paused = false
	match u["name"]:
		"MAX HP +20":
			player.max_hp += 20.0
			player.heal(20.0)
		"DAMAGE +1":
			player.damage += 1
		"SPEED +10%":
			player.move_mult *= 1.1
		"CHEAP POWERS":
			player.surge_cost = 11.0
			player.frenzy_cost = 15.0
	floor_num += 1
	room += Vector2(120, 120)
	build_floor()

func _on_player_died(turned: bool) -> void:
	get_tree().paused = true
	hud.show_death(turned, floor_num, player.scrap)

func _on_power_btn(pos: Vector2) -> bool:
	if hud.surge_btn.get_global_rect().has_point(pos):
		return true
	if hud.frenzy_btn.get_global_rect().has_point(pos):
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
	if event is InputEventScreenTouch:
		var t := event as InputEventScreenTouch
		var vp := get_viewport().get_visible_rect().size
		if t.pressed:
			if t.position.x < vp.x * 0.5 and joy_id == -1:
				joy_id = t.index
				joy_origin = t.position
				hud.show_joystick(t.position)
			elif t.position.x >= vp.x * 0.5 and not _on_power_btn(t.position):
				if player and not player.dead:
					player.attack()
		else:
			if t.index == joy_id:
				joy_id = -1
				if player:
					player.joystick = Vector2.ZERO
				hud.hide_joystick()
	elif event is InputEventScreenDrag:
		var d := event as InputEventScreenDrag
		if d.index == joy_id and player:
			var v := (d.position - joy_origin) / 110.0
			if v.length() > 1.0:
				v = v.normalized()
			player.joystick = v
			hud.move_knob(joy_origin + v * 110.0)
""")
print("PART5 main done")

# ================= scripts/infected.gd =================
W("scripts/infected.gd", """extends CharacterBody2D
## Infected crawler. Chases the carrier, hits raise infection.

var max_hp := 3
var hp := 3
var speed := 95.0
var touch_damage := 12.0
var dead := false
var _hit_flash := 0.0

func _ready() -> void:
	add_to_group("infected")
	var sf := SpriteFrames.new()
	sf.add_animation("chase")
	sf.set_animation_speed("chase", 5.0)
	sf.set_animation_loop("chase", true)
	for f in ["slime_idle", "slime_hop"]:
		sf.add_frame("chase", load("res://assets/%s.png" % f) as Texture2D)
	$Sprite.frames = sf
	$Sprite.play("chase")
	$Sprite.scale = Vector2(0.4, 0.4)

func _physics_process(delta: float) -> void:
	if dead:
		return
	_hit_flash = maxf(0.0, _hit_flash - delta)
	$Sprite.modulate = Color(1.6, 0.7, 0.7) if _hit_flash > 0.0 else Color.WHITE
	var player := get_tree().get_first_node_in_group("player")
	if player == null or player.dead:
		velocity = Vector2.ZERO
		move_and_slide()
		return
	var to_p: Vector2 = player.global_position - global_position
	var dist := to_p.length()
	if dist < 460.0:
		velocity = to_p.normalized() * speed
	else:
		velocity = velocity.lerp(Vector2.ZERO, 4.0 * delta)
	for o in get_tree().get_nodes_in_group("infected"):
		if o == self or o.dead:
			continue
		var d: Vector2 = global_position - o.global_position
		var l := d.length()
		if l > 1.0 and l < 90.0:
			velocity += d.normalized() * 60.0
	move_and_slide()
	if dist < 95.0:
		player.take_hit(touch_damage)

func take_damage(amount: int) -> void:
	if dead:
		return
	hp -= amount
	_hit_flash = 0.12
	if hp <= 0:
		dead = true
		var main := get_tree().current_scene
		if main != null and main.has_method("on_infected_killed"):
			main.on_infected_killed(global_position)
		queue_free()
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
## Loot pickup: scrap / suppressant / medkit.

@export var kind := "scrap"
var _t := 0.0
var _base_y := 0.0

const TEX := {
	"scrap": "coin_full",
	"suppressant": "suppressant",
	"medkit": "heart",
}

func _ready() -> void:
	$Sprite.texture = load("res://assets/%s.png" % TEX.get(kind, "coin_full"))
	$Sprite.scale = Vector2(0.5, 0.5)
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
	queue_free()
""")
print("pickup ok")

# ================= scripts/hud.gd =================
W("scripts/hud.gd", """extends CanvasLayer
## HUD: HP + infection bars, scrap, floor, power buttons, joystick, channel, draft, death.

var player: CharacterBody2D
var hp_bar: ProgressBar
var inf_bar: ProgressBar
var inf_label: Label
var scrap_label: Label
var floor_label: Label
var surge_btn: Button
var frenzy_btn: Button
var joy_base: Sprite2D
var joy_knob: Sprite2D
var atk_hint: Sprite2D
var channel_bar: ProgressBar
var channel_label: Label
var draft_panel: PanelContainer
var death_panel: PanelContainer
var _t := 0.0

func _ready() -> void:
	hp_bar = _bar(Vector2(24, 24), Vector2(300, 28), Color(0.85, 0.2, 0.2))
	inf_bar = _bar(Vector2(24, 60), Vector2(300, 28), Color(0.25, 1.0, 0.42))
	inf_label = _label(Vector2(24, 92), 22, "INFECTION 0%")
	inf_label.add_theme_color_override("font_color", Color(0.35, 1.0, 0.5))
	scrap_label = _label(Vector2(24, 124), 24, "SCRAP 0")
	floor_label = _label(Vector2(400, 24), 30, "FLOOR 1")
	surge_btn = _power_btn(Vector2(470, 1010), "SURGE", Color(0.2, 0.7, 1.0))
	frenzy_btn = _power_btn(Vector2(470, 1140), "FRENZY", Color(1.0, 0.45, 0.2))
	surge_btn.pressed.connect(func(): if player: player.try_surge())
	frenzy_btn.pressed.connect(func(): if player: player.try_frenzy())
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
	atk_hint = Sprite2D.new()
	atk_hint.texture = load("res://assets/attack_btn.png")
	atk_hint.position = Vector2(610, 1140)
	atk_hint.modulate.a = 0.5
	atk_hint.scale = Vector2(0.8, 0.8)
	add_child(atk_hint)
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
	bg.set_corner_radius_all(6)
	var fg := StyleBoxFlat.new()
	fg.bg_color = fill
	fg.set_corner_radius_all(6)
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

func _power_btn(pos: Vector2, text: String, color: Color) -> Button:
	var b := Button.new()
	b.position = pos
	b.size = Vector2(150, 110)
	b.text = text
	b.add_theme_font_size_override("font_size", 24)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0, 0, 0, 0.55)
	sb.border_color = color
	sb.set_border_width_all(3)
	sb.set_corner_radius_all(14)
	b.add_theme_stylebox_override("normal", sb)
	var sb2 := sb.duplicate() as StyleBoxFlat
	sb2.bg_color = Color(color.r * 0.3, color.g * 0.3, color.b * 0.3, 0.7)
	b.add_theme_stylebox_override("pressed", sb2)
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
	floor_label.text = "FLOOR %d" % n

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
	rb.pressed.connect(func(): get_tree().paused = false; get_tree().reload_current_scene())
	vb.add_child(rb)
	death_panel.visible = true
	await get_tree().process_frame
	death_panel.set_anchors_preset(Control.PRESET_CENTER)

func _process(delta: float) -> void:
	_t += delta
	atk_hint.modulate.a = 0.35 + 0.2 * sin(_t * 4.0)
	if player == null or not is_instance_valid(player):
		return
	hp_bar.max_value = player.max_hp
	hp_bar.value = player.hp
	inf_bar.value = player.infection
	inf_label.text = "INFECTION %d%%" % int(player.infection)
	if player.infection > 75.0:
		inf_label.add_theme_color_override("font_color", Color(1.0, 0.35, 0.35))
	else:
		inf_label.add_theme_color_override("font_color", Color(0.35, 1.0, 0.5))
	scrap_label.text = "SCRAP %d" % player.scrap
	_upd_btn(surge_btn, "SURGE", player.surge_cost, player.surge_cd, player.infection)
	_upd_btn(frenzy_btn, "FRENZY", player.frenzy_cost, player.frenzy_cd, player.infection)

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
	var tile_tex := load("res://assets/floor_tile.png") as Texture2D
	for ix in range(3):
		for iy in range(3):
			var sp := Sprite2D.new()
			sp.texture = tile_tex
			sp.position = Vector2(360 + ix * 300, 420 + iy * 300) - Vector2(300, 300)
			sp.modulate = Color(0.4, 0.42, 0.46)
			add_child(sp)
	var hero := Sprite2D.new()
	hero.texture = load("res://assets/hero_down_idle.png")
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

Original tower-extraction RPG. LAST SHIFT outbreak universe.
Core mechanic (Tbandz picked 2026-09-29): the INFECTION METER.

## The loop
1. Drop onto a tower floor (top-down 2D pixel art).
2. Fight infected, grab loot (scrap / suppressant / medkit).
3. Reach the glowing extraction pad, channel 3s to descend.
4. Draft 1 of 3 upgrades between floors.
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
- More infected types, boss floors, Sense power (loot radar)
- Proper infected art (replace slime stand-in)
- Sound, more tower biomes, daily seeded tower
""")
print("BUILD COMPLETE")
