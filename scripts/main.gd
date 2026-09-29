extends Node2D
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
var _tick_t := 0.0
const CHANNEL_NEED := 3.0
var joy_id := -1
var joy_origin := Vector2.ZERO

const UPGRADES := [
	{"name": "MAX HP +20", "desc": "Sturdier body"},
	{"name": "DAMAGE +1", "desc": "Heavier swings"},
	{"name": "SPEED +10%", "desc": "Lighter feet"},
	{"name": "CHEAP POWERS", "desc": "Powers cost 25% less"},
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
			sp.modulate = Color(0.42, 0.44, 0.48)
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
	player.sensed.connect(func(): reveal_pickups(4.0))
	player.leveled_up.connect(func(lv: int): hud.show_toast("LEVEL %d" % lv))
	hud.bind(player)
	# extraction pad far corner
	pad = Area2D.new()
	pad.add_to_group("extract_pad")
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
	hud.set_room(room)

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
	if pad and is_instance_valid(pad):
		var m2 := SenseMarker.new()
		m2.life = dur
		pad.add_child(m2)

func spawn_pickup(kind: String, pos: Vector2) -> void:
	var f := floor_node
	var p: Area2D = pickup_scene.instantiate()
	p.kind = kind
	p.position = pos
	f.add_child(p)

func on_infected_killed(pos: Vector2, xp: int) -> void:
	if player and not player.dead:
		player.add_xp(xp)
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
	get_tree().paused = true
	var picks := UPGRADES.duplicate()
	picks.shuffle()
	hud.show_draft(picks.slice(0, 3), _on_upgrade)

func _on_upgrade(u: Dictionary) -> void:
	get_tree().paused = false
	Sfx.play("upgrade")
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
	Sfx.play("turn" if turned else "hurt")
	hud.show_death(turned, floor_num, player.scrap)

func _on_power_btn(pos: Vector2) -> bool:
	for b in [hud.surge_btn, hud.frenzy_btn, hud.sense_btn, hud.atk_btn]:
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
