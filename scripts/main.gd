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
	var sc := 1.35 if big else 1.0
	s.scale = Vector2(sc, sc)
	# additive glow: brighter, more visible slash arc
	s.modulate = Color(0.85, 1.0, 0.8, 0.95)
	floor_node.add_child(s)
	var tw := create_tween().set_parallel()
	tw.tween_property(s, "rotation", angle + 1.4, 0.22).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tw.tween_property(s, "scale", Vector2(sc * 1.25, sc * 1.25), 0.22)
	tw.tween_property(s, "modulate:a", 0.0, 0.22)
	tw.chain().tween_callback(s.queue_free)

func fx_wisp(pos: Vector2) -> void:
	# infection wisp rises from a slain enemy (cheap, atmospheric)
	if floor_node == null or not is_instance_valid(floor_node):
		return
	var s := Sprite2D.new()
	s.texture = load("res://assets/dust.png")
	s.position = pos
	s.modulate = Color(0.45, 1.0, 0.55, 0.7)
	s.scale = Vector2(0.8, 0.8)
	floor_node.add_child(s)
	var tw := create_tween().set_parallel()
	tw.tween_property(s, "position", pos + Vector2(rng.randf_range(-20, 20), -90), 0.8).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tw.tween_property(s, "scale", Vector2(1.6, 1.6), 0.8)
	tw.tween_property(s, "modulate:a", 0.0, 0.8)
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
		# NOTE: on web Godot delivers touch positions ALREADY in canvas units;
		# converting again via the canvas transform double-converts into garbage
		# (this was the invisible-joystick bug: cpos went negative off-screen).
		var cpos := t.position
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
			var raw := (d.position - joy_origin) / 110.0
			var rl := raw.length()
			var v := Vector2.ZERO
			if rl > JOY_DEADZONE:
				# smoothstep response: gentle near center, full throw at the rim
				var t := clampf((rl - JOY_DEADZONE) / (1.0 - JOY_DEADZONE), 0.0, 1.0)
				t = t * t * (3.0 - 2.0 * t)
				v = raw / rl * t
			player.joystick = v
			hud.move_knob(joy_origin + v * 110.0)
