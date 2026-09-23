class_name SafeZone
extends Area2D
## Town area: binding cards is instant here, and (later) combat steals are off.


func _ready() -> void:
	body_entered.connect(func(body: Node2D) -> void: _set_inside(body, true))
	body_exited.connect(func(body: Node2D) -> void: _set_inside(body, false))


func _set_inside(body: Node2D, inside: bool) -> void:
	var collector: Variant = body.get(&"collector_id")
	if collector is StringName:
		GameState.set_in_safe_zone(collector, inside)
