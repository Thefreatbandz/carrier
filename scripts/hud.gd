extends CanvasLayer
## HUD: HP + infection bars, scrap, floor, power buttons, joystick, channel, draft, death.

var player: CharacterBody2D
var room_size := Vector2(2100, 2100)
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
var joy_base: Sprite2D
var joy_knob: Sprite2D
var channel_bar: ProgressBar
var channel_label: Label
var draft_panel: PanelContainer
var death_panel: PanelContainer
var minimap: Minimap
var _t := 0.0
var _toast_t := 0.0

class Minimap extends Control:
	var room := Vector2(2100, 2100)
	func _process(_d: float) -> void:
		queue_redraw()
	func _draw() -> void:
		var r := Rect2(Vector2.ZERO, size)
		draw_rect(r, Color(0, 0, 0, 0.55))
		draw_rect(r, Color(0.3, 1.0, 0.5, 0.8), false, 2.0)
		var s := size.x / room.x
		var w2m := func(wpos: Vector2) -> Vector2: return (wpos + room / 2.0) * s
		for pd in get_tree().get_nodes_in_group("extract_pad"):
			var c: Vector2 = w2m.call((pd as Node2D).global_position)
			var pulse := 5.0 + 2.0 * sin(Time.get_ticks_msec() / 300.0)
			draw_circle(c, pulse, Color(0.3, 1.0, 0.5, 0.9))
		for pk in get_tree().get_nodes_in_group("pickups"):
			draw_circle(w2m.call((pk as Node2D).global_position), 2.5, Color(1.0, 0.85, 0.2, 0.9))
		for e in get_tree().get_nodes_in_group("infected"):
			if not (e as Node).get("dead"):
				draw_circle(w2m.call((e as Node2D).global_position), 3.0, Color(1.0, 0.25, 0.25, 0.9))
		var pl := get_tree().get_first_node_in_group("player")
		if pl:
			draw_circle(w2m.call((pl as Node2D).global_position), 4.5, Color.WHITE)

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
	hp_bar = _bar(Vector2(24, 24), Vector2(300, 28), Color(0.85, 0.2, 0.2))
	inf_bar = _bar(Vector2(24, 60), Vector2(300, 28), Color(0.25, 1.0, 0.42))
	inf_label = _label(Vector2(24, 92), 22, "INFECTION 0%")
	inf_label.add_theme_color_override("font_color", Color(0.35, 1.0, 0.5))
	scrap_label = _label(Vector2(24, 124), 24, "SCRAP 0")
	lvl_label = _label(Vector2(24, 156), 22, "LV 1")
	xp_bar = _bar(Vector2(92, 160), Vector2(232, 18), Color(0.6, 0.4, 1.0))
	floor_label = _label(Vector2(340, 24), 30, "DEPTH 1")
	toast_label = _label(Vector2(110, 120), 34, "")
	toast_label.visible = false
	minimap = Minimap.new()
	minimap.position = Vector2(528, 24)
	minimap.size = Vector2(168, 168)
	add_child(minimap)
	surge_btn = _power_btn(Vector2(430, 870), "SURGE", Color(0.2, 0.7, 1.0), Vector2(140, 100))
	frenzy_btn = _power_btn(Vector2(430, 985), "FRENZY", Color(1.0, 0.45, 0.2), Vector2(140, 100))
	sense_btn = _power_btn(Vector2(430, 1100), "SENSE", Color(0.3, 1.0, 1.0), Vector2(140, 100))
	atk_btn = _power_btn(Vector2(585, 990), "ATTACK", Color(1.0, 0.85, 0.2), Vector2(125, 175))
	surge_btn.pressed.connect(func(): if player: player.try_surge())
	frenzy_btn.pressed.connect(func(): if player: player.try_frenzy())
	sense_btn.pressed.connect(func(): if player: player.try_sense())
	atk_btn.pressed.connect(func(): if player and not player.dead: player.attack())
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

func _power_btn(pos: Vector2, text: String, color: Color, bsize := Vector2(150, 110)) -> Button:
	var b := Button.new()
	b.position = pos
	b.size = bsize
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
	floor_label.text = "DEPTH %d" % n

func set_room(r: Vector2) -> void:
	room_size = r
	minimap.room = r

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
	if _toast_t > 0.0:
		_toast_t -= delta
		toast_label.modulate.a = clampf(_toast_t, 0.0, 1.0)
		if _toast_t <= 0.0:
			toast_label.visible = false
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
	lvl_label.text = "LV %d" % player.level
	xp_bar.max_value = player.xp_next
	xp_bar.value = player.xp
	_upd_btn(surge_btn, "SURGE", player.surge_cost, player.surge_cd, player.infection)
	_upd_btn(frenzy_btn, "FRENZY", player.frenzy_cost, player.frenzy_cd, player.infection)
	_upd_btn(sense_btn, "SENSE", player.sense_cost, player.sense_cd, player.infection)

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
