extends CharacterBody2D
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
