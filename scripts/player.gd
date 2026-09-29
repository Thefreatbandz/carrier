extends CharacterBody2D
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
var joystick := Vector2.ZERO     # set by HUD touch controls
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

var slash_scene := preload("res://scenes/slash.tscn")

func _ready() -> void:
	add_to_group("player")
	var sf := SpriteFrames.new()
	for dir in ["down", "up", "side"]:
		_add_frames(sf, dir + "_idle",
			["p_%s_idle_0" % dir, "p_%s_idle_1" % dir], 4.0, true)
		_add_frames(sf, dir + "_walk",
			["p_%s_walk_0" % dir, "p_%s_walk_1" % dir,
			 "p_%s_walk_2" % dir, "p_%s_walk_3" % dir], 10.0, true)
	_add_frames(sf, "attack", ["p_attack_0", "p_attack_1", "p_attack_2"], 16.0, false)
	_add_frames(sf, "hurt", ["p_hurt_0"], 8.0, false)
	_add_frames(sf, "death", ["p_death_0", "p_death_1"], 6.0, false)
	$Sprite.frames = sf
	$Sprite.scale = Vector2(0.5, 0.5)  # HD art is 2x, keep on-screen size
	$Sprite.play("down_idle")

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
	surge_t = maxf(0.0, surge_t - delta)
	frenzy_t = maxf(0.0, frenzy_t - delta)
	sense_t = maxf(0.0, sense_t - delta)
	_flash = maxf(0.0, _flash - delta)
	_attack_t = maxf(0.0, _attack_t - delta)
	_hurt_t = maxf(0.0, _hurt_t - delta)
	_lunge = _lunge.lerp(Vector2.ZERO, 14.0 * delta)
	$Sprite.modulate = Color(1.8, 0.45, 0.45) if _flash > 0.0 else Color.WHITE
	# --- infection drift ---
	add_infection(PASSIVE_INFECTION * delta, true)
	if extract_cleanse:
		add_infection(-5.0 * delta, true)
	# --- movement (accel/decel, knockback decays) ---
	var iv := Input.get_vector("mv_left", "mv_right", "mv_up", "mv_down")
	var mv := iv + joystick
	if mv.length() > 1.0:
		mv = mv.normalized()
	var spd := BASE_SPEED * move_mult
	if surge_t > 0.0:
		spd *= 1.8
	var accel := 2400.0 if mv.length() > 0.1 else 2000.0
	velocity = velocity.move_toward(mv * spd, accel * delta)
	velocity += _kb
	_kb = _kb.move_toward(Vector2.ZERO, 2200.0 * delta)
	move_and_slide()
	var moving := mv.length() > 0.15
	if moving:
		_face(mv)
		_bob_t += delta * 11.0
	# --- animation state machine (attack/hurt lock, then locomotion) ---
	var want := ""
	if _attack_t > 0.0:
		want = "attack"
	elif _hurt_t > 0.0:
		want = "hurt"
	elif moving:
		want = _anim_name() + "_walk"
	else:
		want = _anim_name() + "_idle"
	if $Sprite.animation != want or not $Sprite.is_playing():
		$Sprite.play(want)
	$Sprite.position = Vector2(0, sin(_bob_t) * 5.0 if moving else 0.0) + _lunge
	emit_signal("changed")

func _face(mv: Vector2) -> void:
	facing = mv.normalized()
	$Sprite.flip_h = facing.x < -0.1

func _anim_name() -> String:
	if absf(facing.x) > 0.5:
		return "side"
	return "up" if facing.y < -0.1 else "down"

func attack() -> void:
	if dead or attack_cd > 0.0:
		return
	attack_cd = 0.42
	_attack_t = 0.32
	_lunge = facing * 30.0
	Sfx.play("swing")
	var s := slash_scene.instantiate()
	s.global_position = global_position + facing * 110.0
	s.rotation = facing.angle()
	s.damage = damage * (2 if frenzy_t > 0.0 else 1)
	get_parent().add_child(s)
	var m := _main()
	if m:
		m.hitstop(0.05)

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
	hp -= amount
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
