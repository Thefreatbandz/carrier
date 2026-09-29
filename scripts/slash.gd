extends Area2D
## Sword slash hitbox. Lives 0.18s, damages infected once each.

var damage := 1
var _life := 0.18
var _hit := {}

func _ready() -> void:
	$Sprite.texture = load("res://assets/slash_thick.png")
	$Sprite.scale = Vector2(0.45, 0.45)
	body_entered.connect(_on_body)

func _physics_process(delta: float) -> void:
	_life -= delta
	$Sprite.rotation += 6.0 * delta
	if _life <= 0.0:
		queue_free()

func _on_body(body: Node2D) -> void:
	if _hit.has(body.get_instance_id()):
		return
	if body.is_in_group("infected") and body.has_method("take_damage"):
		_hit[body.get_instance_id()] = true
		body.take_damage(damage)
