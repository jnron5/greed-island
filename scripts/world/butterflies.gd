class_name Butterflies
extends Node2D
## A few butterflies fluttering over a meadow or clearing: each wanders on its own
## drifting path around the group's position (never far), flapping (a PixelLab
## wing-beat strip), bobbing a little and turning to face where it drifts, with a
## small shadow on the grass. Purely ambient: no collision. They keep to daytime.

@export var strip: Texture2D = preload("res://assets/sprites/ambient/butterfly.png")
@export var frame_count := 8
@export var count := 3
@export var radius := 70.0
@export var tint := Color.WHITE
@export var seed := 1

var _flies: Array[Dictionary] = []


func _ready() -> void:
	z_index = 15
	var frames := SpriteFrames.new()
	frames.set_animation_speed(&"default", 16.0)
	var image := strip.get_image()
	var w := image.get_width() / frame_count
	for k in frame_count:
		var atlas := AtlasTexture.new()
		atlas.atlas = strip
		atlas.region = Rect2(k * w, 0, w, image.get_height())
		frames.add_frame(&"default", atlas)
	var rng := RandomNumberGenerator.new()
	rng.seed = seed
	for i in count:
		var sprite := AnimatedSprite2D.new()
		sprite.sprite_frames = frames
		sprite.play(&"default")
		sprite.frame = rng.randi_range(0, frame_count - 1)
		sprite.speed_scale = rng.randf_range(0.8, 1.25)
		sprite.scale = Vector2.ONE * 0.45
		sprite.modulate = tint.lerp(Color(rng.randf_range(0.8, 1.2), rng.randf_range(0.8, 1.1), rng.randf_range(0.7, 1.3)), 0.35)
		add_child(sprite)
		_flies.append({
			"sprite": sprite,
			"pos": Vector2(rng.randf_range(-radius, radius), rng.randf_range(-radius, radius) * 0.6),
			"heading": rng.randf() * TAU,
			"speed": rng.randf_range(16, 28),
			"t": rng.randf() * TAU,
		})


func _process(delta: float) -> void:
	var day := 1.0 - TimeOfDay.night_factor()
	modulate.a = clampf(day * 1.5 - 0.3, 0.0, 1.0)
	for f in _flies:
		f.t += delta
		# Wander: the heading drifts, and pulls back home when a fly strays too far.
		f.heading += sin(f.t * 1.7) * 2.2 * delta + randf_range(-1.5, 1.5) * delta
		var pos: Vector2 = f.pos
		if pos.length() > radius:
			f.heading = lerp_angle(f.heading, (-pos).angle(), 2.0 * delta)
		f.pos = pos + Vector2.from_angle(f.heading) * f.speed * delta
		var sprite: AnimatedSprite2D = f.sprite
		sprite.position = f.pos + Vector2(0, -18 + sin(f.t * 5.0) * 3.0)
		sprite.rotation = lerp_angle(sprite.rotation, f.heading + PI / 2.0, 4.0 * delta)
	queue_redraw()


func _draw() -> void:
	for f in _flies:
		draw_circle(f.pos, 2.0, Color(0, 0, 0, 0.18 * modulate.a))
