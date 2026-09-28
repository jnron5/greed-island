class_name Fireflies
extends Node2D
## Fireflies over a glade after dusk: small warm-green motes that drift on slow
## looping paths near home and pulse on and off, each with a faint halo. They fade in
## as night falls (TimeOfDay.night_factor) and are gone by day. Purely ambient.

@export var count := 8
@export var radius := 90.0
@export var seed := 1

const GLOW := Color(0.85, 1.0, 0.45)

var _flies: Array[Dictionary] = []


func _ready() -> void:
	z_index = 16
	# They make their own light: the night tint (CanvasModulate) doesn't dim them.
	var glow := CanvasItemMaterial.new()
	glow.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	glow.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	material = glow
	var rng := RandomNumberGenerator.new()
	rng.seed = seed
	for i in count:
		_flies.append({
			"home": Vector2(rng.randf_range(-radius, radius), rng.randf_range(-radius, radius) * 0.6),
			"loop": Vector2(rng.randf_range(10, 26), rng.randf_range(6, 16)),
			"speed": rng.randf_range(0.4, 0.9),
			"phase": rng.randf() * TAU,
			"blink": rng.randf_range(0.8, 1.6),
			"t": rng.randf() * 10.0,
		})


func _process(delta: float) -> void:
	modulate.a = clampf(TimeOfDay.night_factor() * 1.4 - 0.15, 0.0, 1.0)
	visible = modulate.a > 0.01
	if not visible:
		return
	for f in _flies:
		f.t += delta
	queue_redraw()


func _draw() -> void:
	for f in _flies:
		var t: float = f.t
		var p: Vector2 = f.home + Vector2(cos(t * f.speed + f.phase) * f.loop.x,
			sin(t * f.speed * 1.3 + f.phase) * f.loop.y - 14.0)
		var on := clampf(sin(t * f.blink + f.phase) * 1.6, 0.0, 1.0)
		if on <= 0.02:
			continue
		p = p.round()
		draw_circle(p, 6.0, Color(GLOW, 0.1 * on))
		draw_circle(p, 3.0, Color(GLOW, 0.3 * on))
		draw_rect(Rect2(p - Vector2(1, 1), Vector2(2, 2)), Color(1.0, 1.0, 0.8, on))
