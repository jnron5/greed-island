class_name StringLights
extends Node2D
## A string of little lanterns slung overhead between two points (across a market lane,
## round a square). By day it's a sagging cord with small paper lanterns; after dusk the
## lanterns glow (additive, unshaded, so the night tint doesn't dim them) and each one
## throws a little warm light. `to` is relative to this node.

@export var to := Vector2(100, 0)
@export var sag := 14.0
@export var count := 7
## Lantern colours, cycled along the string.
@export var colors: PackedColorArray = [Color(1.0, 0.78, 0.4), Color(1.0, 0.55, 0.35), Color(0.95, 0.9, 0.55)]

const CORD := Color(0.22, 0.14, 0.1)

var _glow: Node2D
var _t := randf() * 10.0


func _ready() -> void:
	z_index = 40
	# The glowing halos draw on a child with its own additive material.
	_glow = Node2D.new()
	var mat := CanvasItemMaterial.new()
	mat.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	_glow.material = mat
	_glow.draw.connect(_draw_glow)
	add_child(_glow)
	# A few real lights along the string so the lane below is lit too.
	for i in 3:
		var light := LampLight.new()
		light.position = _point((i + 1) / 4.0) + Vector2(0, 26)
		light.texture_scale = 0.8
		light.max_energy = 0.7
		add_child(light)


func _process(delta: float) -> void:
	_t += delta
	var night := TimeOfDay.night_factor()
	_glow.visible = night > 0.02
	_glow.modulate.a = night
	if _glow.visible:
		_glow.queue_redraw()


func _point(t: float) -> Vector2:
	return to * t + Vector2(0, sag * 4.0 * t * (1.0 - t))


func _draw() -> void:
	var prev := Vector2.ZERO
	for i in range(1, 13):
		var p := _point(i / 12.0)
		draw_line(prev.round(), p.round(), CORD, 1.0)
		prev = p
	for i in count:
		var p := _point((i + 0.5) / count).round()
		var c := colors[i % colors.size()]
		draw_line(p, p + Vector2(0, 2), CORD, 1.0)
		draw_rect(Rect2(p + Vector2(-2, 2), Vector2(4, 5)), c.darkened(0.25))
		draw_rect(Rect2(p + Vector2(-1, 3), Vector2(2, 3)), c)


func _draw_glow() -> void:
	for i in count:
		var p := _point((i + 0.5) / count).round() + Vector2(0, 4.5)
		var c := colors[i % colors.size()]
		var flick := 0.85 + 0.15 * sin(_t * 5.0 + i * 1.7)
		_glow.draw_circle(p, 9.0, Color(c, 0.12 * flick))
		_glow.draw_circle(p, 4.5, Color(c, 0.35 * flick))
		_glow.draw_rect(Rect2(p + Vector2(-1, -1.5), Vector2(2, 3)), Color(1, 0.95, 0.8, 0.9 * flick))
