extends CharacterBody2D
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
