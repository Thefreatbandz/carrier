extends CharacterBody2D
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
			_bob_t += delta * 4.0  # synced to 4-frame/8fps walk (2 steps per 0.5s cycle)
			$Sprite.position.y = sin(_bob_t * TAU) * 4.0
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
		main.fx_wisp(global_position + Vector2(0, -20))
		main.call("on_infected_killed", global_position, xp, is_boss)
	var tw := create_tween()
	tw.tween_interval(0.5)          # death pose reads clearly
	tw.tween_property($Sprite, "modulate:a", 0.0, 0.3)
	tw.tween_callback(queue_free)
