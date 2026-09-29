extends Area2D
## Loot pickup: scrap / suppressant / medkit.

@export var kind := "scrap"
var _t := 0.0
var _base_y := 0.0

const TEX := {
	"scrap": "coin_full",
	"suppressant": "suppressant",
	"medkit": "heart",
}

func _ready() -> void:
	$Sprite.texture = load("res://assets/%s.png" % TEX.get(kind, "coin_full"))
	$Sprite.scale = Vector2(0.5, 0.5)
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
	queue_free()
