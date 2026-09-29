extends CharacterBody2D
## Infected crawler. Chases the carrier, hits raise infection.

var max_hp := 3
var hp := 3
var speed := 95.0
var touch_damage := 12.0
var dead := false
var itype := "shambler"
var xp := 10
var _frames := ["slime_idle", "slime_hop"]
var _scale := 0.4
var _hit_flash := 0.0
var _knockback := Vector2.ZERO
var _bob_t := 0.0

func setup(t: String, floor_num: int) -> void:
	itype = t
	match t:
		"runner":
			max_hp = 2 + floor_num / 2
			speed = 155.0 + floor_num * 4.0
			touch_damage = 10.0 + floor_num
			xp = 14
			_frames = ["inf_runner_0", "inf_runner_1"]
			_scale = 0.45
		"brute":
			max_hp = 9 + floor_num
			speed = 62.0
			touch_damage = 22.0 + floor_num
			xp = 30
			_frames = ["inf_brute_0", "inf_brute_1"]
			_scale = 0.62
		_:  # shambler
			max_hp = 3 + floor_num / 2
			speed = 95.0 + floor_num * 6.0
			touch_damage = 12.0 + floor_num
			xp = 10
			_frames = ["inf_shambler_0", "inf_shambler_1"]
			_scale = 0.5
	hp = max_hp

func _ready() -> void:
	add_to_group("infected")
	var sf := SpriteFrames.new()
	sf.add_animation("chase")
	sf.set_animation_speed("chase", 5.0)
	sf.set_animation_loop("chase", true)
	for f in _frames:
		sf.add_frame("chase", load("res://assets/%s.png" % f) as Texture2D)
	$Sprite.frames = sf
	$Sprite.play("chase")
	$Sprite.scale = Vector2(_scale, _scale)

func _physics_process(delta: float) -> void:
	if dead:
		return
	_hit_flash = maxf(0.0, _hit_flash - delta)
	$Sprite.modulate = Color(1.6, 0.7, 0.7) if _hit_flash > 0.0 else Color.WHITE
	_knockback = _knockback.lerp(Vector2.ZERO, 10.0 * delta)
	var player := get_tree().get_first_node_in_group("player")
	if player == null or player.dead:
		velocity = _knockback
		move_and_slide()
		return
	var to_p: Vector2 = player.global_position - global_position
	var dist := to_p.length()
	if dist < 460.0:
		velocity = to_p.normalized() * speed + _knockback
		_bob_t += delta * 8.0
		$Sprite.position.y = sin(_bob_t) * 6.0
	else:
		velocity = velocity.lerp(Vector2.ZERO, 4.0 * delta) + _knockback
		$Sprite.position.y = 0.0
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
	var p := get_tree().get_first_node_in_group("player")
	if p:
		var away: Vector2 = global_position - (p as Node2D).global_position
		if away.length() > 1.0:
			_knockback = away.normalized() * 300.0
	Sfx.play("hit")
	if hp <= 0:
		dead = true
		collision_layer = 0
		collision_mask = 0
		Sfx.play("die")
		var main: Node = get_tree().current_scene
		if main == null or not main.has_method("on_infected_killed"):
			main = get_tree().get_first_node_in_group("game_main")
		if main != null:
			main.call("on_infected_killed", global_position, xp)
		var tw := create_tween()
		tw.set_parallel(true)
		tw.tween_property($Sprite, "scale", Vector2(0.05, 0.05), 0.28)
		tw.tween_property($Sprite, "modulate:a", 0.0, 0.28)
		tw.chain().tween_callback(queue_free)
