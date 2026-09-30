extends Node2D

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
