class_name DustDevilFx
extends Node2D
## The Dust Devil card's whirl of sand: rings of grit spinning outward from where it
## was cast, fading over a second and a half.

const LIFE := 1.5

var _age := 0.0


func _process(delta: float) -> void:
	_age += delta
	if _age >= LIFE:
		queue_free()
	queue_redraw()


func _draw() -> void:
	var t := _age / LIFE
	var sand := Color(0.86, 0.68, 0.4, 1.0 - t)
	var r := 20.0 + t * CardSpells.DUST_DEVIL_RANGE
	draw_set_transform(Vector2(0, -8), 0.0, Vector2(1.0, 0.5))
	draw_arc(Vector2.ZERO, r, 0, TAU, 40, sand, 3.0)
	draw_arc(Vector2.ZERO, r * 0.7, 0, TAU, 32, Color(sand, sand.a * 0.6), 2.0)
	draw_set_transform(Vector2.ZERO)
	for i in 24:
		var a := TAU * i / 24.0 + _age * 9.0
		var d := r * (0.4 + 0.6 * fmod(i * 0.37, 1.0))
		draw_circle(Vector2(cos(a) * d, sin(a) * d * 0.5 - 8.0 - t * 30.0 * fmod(i * 0.61, 1.0)), 1.5, sand)
