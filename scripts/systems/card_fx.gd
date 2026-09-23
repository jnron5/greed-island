class_name CardFx
extends Node2D
## A card that arcs from one collector to another, for steals.

const DURATION := 0.4


static func fly(from: Node2D, to: Node2D) -> void:
	var fx := CardFx.new()
	fx.z_index = 20
	from.get_parent().add_child(fx)
	fx.global_position = from.global_position + Vector2(0, -24)
	var end := to.global_position + Vector2(0, -24)
	var start := fx.global_position
	var apex := (start + end) / 2.0 + Vector2(0, -30)
	# Quadratic bezier arc from start over the apex to end.
	var arc := func(t: float) -> void:
		fx.global_position = start.lerp(apex, t).lerp(apex.lerp(end, t), t)
		fx.rotation = sin(t * PI * 2.0) * 0.4
	var tween := fx.create_tween()
	tween.tween_method(arc, 0.0, 1.0, DURATION)
	tween.tween_callback(fx.queue_free)


func _draw() -> void:
	draw_rect(Rect2(-5, -7, 10, 14), Color(0.1, 0.08, 0.06))
	draw_rect(Rect2(-4, -6, 8, 12), Color(0.95, 0.85, 0.45))
	draw_rect(Rect2(-2, -4, 4, 4), Color(0.8, 0.3, 0.2))
