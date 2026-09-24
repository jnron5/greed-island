class_name LampLight
extends PointLight2D
## Warm light for lamp posts, lanterns and windows. Brightens as night falls
## (TimeOfDay.night_factor) with a gentle candle flicker; `always_on` lights
## (interiors, fires) ignore the clock.

@export var max_energy := 1.1
@export var always_on := false
@export var flicker := 0.08

var _t := randf() * 10.0


func _ready() -> void:
	if texture == null:
		texture = LampLight.glow_texture()
	color = Color(1.0, 0.78, 0.45)
	texture_scale = 1.0


func _process(delta: float) -> void:
	_t += delta
	var base := 1.0 if always_on else TimeOfDay.night_factor()
	energy = max_energy * base * (1.0 + sin(_t * 9.0) * flicker * 0.5 + sin(_t * 23.0) * flicker * 0.5)
	enabled = energy > 0.01


static var _glow: Texture2D


## A soft radial falloff, shared by every lamp.
static func glow_texture() -> Texture2D:
	if _glow == null:
		var gradient := Gradient.new()
		gradient.set_color(0, Color(1, 1, 1, 1))
		gradient.set_color(1, Color(1, 1, 1, 0))
		gradient.add_point(0.35, Color(1, 1, 1, 0.55))
		var tex := GradientTexture2D.new()
		tex.gradient = gradient
		tex.fill = GradientTexture2D.FILL_RADIAL
		tex.fill_from = Vector2(0.5, 0.5)
		tex.fill_to = Vector2(1.0, 0.5)
		tex.width = 128
		tex.height = 128
		_glow = tex
	return _glow
