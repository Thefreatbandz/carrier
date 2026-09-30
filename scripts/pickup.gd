extends Area2D
## Loot pickup: scrap / suppressant / medkit / weapon.

@export var kind := "scrap"
var _t := 0.0
var _base_y := 0.0

const TEX := {
	"scrap": "coin_full",
	"suppressant": "suppressant",
	"medkit": "heart",
	"weapon": "sword",
}

# on-screen target ~52px; source assets are oversized
const PICKUP_SCALE := {
	"scrap": 0.16,
	"suppressant": 0.26,
	"medkit": 0.15,
	"weapon": 0.32,
}

func _ready() -> void:
	add_to_group("pickups")
	$Sprite.texture = load("res://assets/%s.png" % TEX.get(kind, "coin_full"))
	var sc: float = PICKUP_SCALE.get(kind, 0.2)
	$Sprite.scale = Vector2(sc, sc)
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
		"weapon":
			var main := get_tree().get_first_node_in_group("game_main")
			if main and main.has_method("on_weapon_pickup"):
				main.on_weapon_pickup()
	Sfx.play("pickup")
	queue_free()
