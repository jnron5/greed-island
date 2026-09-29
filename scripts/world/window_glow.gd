class_name WindowGlow
extends Sprite2D
## A building's windows lit from inside at night: an overlay of just the window glass,
## repainted warm (made by the builder from hand-marked window rects, see WINDOWS in
## build_kalmora.py). Fades in with TimeOfDay.night_factor(), unshaded so the night
## tint doesn't dim it, with a faint candle flicker. Each building puts its lamps out
## at its own hour in the small hours and lights them again before dawn.

@export var lights_out := 2.0

var _t := randf() * 10.0


func _ready() -> void:
	var mat := CanvasItemMaterial.new()
	mat.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	material = mat


func _process(delta: float) -> void:
	_t += delta
	var night := TimeOfDay.night_factor()
	var h := TimeOfDay.hour
	if h >= lights_out and h < 5.0:
		night = 0.0
	modulate.a = night * (0.92 + sin(_t * 7.0) * 0.04 + sin(_t * 17.0) * 0.04)
	visible = modulate.a > 0.01
