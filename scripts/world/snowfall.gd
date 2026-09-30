extends Node2D
## Light snow drifting across the view (the Starfall Range): flakes live in screen
## space round the camera, fall slowly with a little sideways sway, and wrap round the
## edges, so the snow never runs out wherever you walk. Bigger flakes are nearer:
## they fall faster and brighter.

@export var count := 90
@export var wind := 14.0

var _flakes: Array[Vector4] = []   # x, y (0..1 of the view), depth (0.4..1), phase


func _ready() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 11
	for i in count:
		_flakes.append(Vector4(rng.randf(), rng.randf(), rng.randf_range(0.4, 1.0), rng.randf() * TAU))


func _process(delta: float) -> void:
	var size := get_viewport_rect().size
	for i in _flakes.size():
		var f := _flakes[i]
		f.y += delta * (14.0 + 26.0 * f.z) / size.y
		f.x += delta * (wind * f.z + sin(f.w + f.y * 12.0) * 6.0) / size.x
		if f.y > 1.02:
			f.y -= 1.04
		f.x = fposmod(f.x, 1.0)
		_flakes[i] = f
	queue_redraw()


func _draw() -> void:
	var canvas := get_canvas_transform()
	var size := get_viewport_rect().size
	var origin := canvas.affine_inverse() * Vector2.ZERO
	var scale_px := 1.0 / canvas.get_scale().x
	for f in _flakes:
		var p := origin + Vector2(f.x * size.x, f.y * size.y) * scale_px
		var r := (0.6 + f.z * 0.9)
		draw_circle(to_local(p), r, Color(1, 1, 1, 0.35 + 0.5 * f.z))
