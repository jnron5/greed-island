@tool
extends StaticBody2D
## Placeholder Thornveil tree until the forest tileset exists: trunk collision
## with a drawn canopy.

@export var radius := 18.0:
	set(value):
		radius = value
		queue_redraw()
@export var tint := Color(0.2, 0.42, 0.22)


func _draw() -> void:
	draw_circle(Vector2(0, 4), radius * 0.8, Color(0, 0, 0, 0.2))
	draw_rect(Rect2(-3, -10, 6, 12), Color(0.35, 0.24, 0.14))
	draw_circle(Vector2(0, -radius - 6), radius, tint.darkened(0.25))
	draw_circle(Vector2(-radius * 0.3, -radius - 10), radius * 0.7, tint)
	draw_circle(Vector2(radius * 0.35, -radius - 4), radius * 0.55, tint.lightened(0.1))
