class_name LighthouseBeam
extends Node2D
## The lighthouse's lamp after dark: a long beam sweeping round from the lantern
## room (a flat circle seen at the game's slant, so it squashes as it swings toward or
## away from you), a glow on the lantern glass that flares when the beam faces you,
## and nothing at all by day. Drawn additive and unshaded so the night tint doesn't
## dim it. Sits at the lantern glass.

@export var length := 520.0
@export var spread := 0.1          # half-width of the beam, radians
@export var turn_seconds := 9.0    # one full sweep
@export var slant := 0.42          # how flat the beam's circle looks from above

const WARM := Color(1.0, 0.9, 0.62)

var _angle := 0.0


func _ready() -> void:
	z_index = 60
	var mat := CanvasItemMaterial.new()
	mat.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	material = mat


func _process(delta: float) -> void:
	_angle = fmod(_angle + delta * TAU / turn_seconds, TAU)
	var night := TimeOfDay.night_factor()
	visible = night > 0.02
	modulate.a = night
	if visible:
		queue_redraw()


func _draw() -> void:
	# Two beams, back to back, like a real rotating lens.
	for k in 2:
		var a := _angle + k * PI
		_beam(a)
	# The glass: brightest while a beam points down the screen toward the viewer.
	var facing := maxf(sin(_angle), sin(_angle + PI))
	var flare := 0.35 + 0.65 * pow(facing, 6.0)
	draw_circle(Vector2.ZERO, 22.0, Color(WARM, 0.12 * flare))
	draw_circle(Vector2.ZERO, 11.0, Color(WARM, 0.3 * flare))
	draw_circle(Vector2.ZERO, 5.0, Color(1, 1, 0.92, 0.7 * flare))


func _beam(a: float) -> void:
	var dir := func(t: float) -> Vector2: return Vector2(cos(t), sin(t) * slant)
	# A beam pointing away (up the screen) is further off and fainter.
	var strength := 0.55 + 0.45 * (sin(a) * 0.5 + 0.5)
	var steps := 5
	for i in steps:
		var near := maxf(length * float(i) / steps, 4.0)
		var far := length * float(i + 1) / steps
		var fade_near := (1.0 - float(i) / steps) * 0.22 * strength
		var fade_far := (1.0 - float(i + 1) / steps) * 0.22 * strength
		var pts := PackedVector2Array([
			dir.call(a - spread) * near, dir.call(a + spread) * near,
			dir.call(a + spread) * far, dir.call(a - spread) * far,
		])
		var cols := PackedColorArray([Color(WARM, fade_near), Color(WARM, fade_near),
			Color(WARM, fade_far), Color(WARM, fade_far)])
		draw_polygon(pts, cols)
	# A brighter core down the middle.
	draw_line(Vector2.ZERO, dir.call(a) * length * 0.6, Color(WARM, 0.12 * strength), 3.0)
