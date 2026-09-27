class_name GullFlock
extends Node2D
## Seagulls circling over the water: each gull flies its own wide, lazy loop around
## the flock's position, flapping (a PixelLab-animated strip, drawn side-on), facing
## the way it flies, with a faint shadow on the water below to show its height.
## Purely ambient: no collision.

@export var strip: Texture2D
@export var frame_count := 6
@export var count := 3
@export var radius := Vector2(150, 70)
@export var height := 46.0                  # shadow offset below the bird
@export var seed := 1

var _gulls: Array[Dictionary] = []
var _shadows: Node2D


func _ready() -> void:
	z_index = 20
	z_as_relative = false
	_shadows = Node2D.new()          # on the water, under everything that stands
	_shadows.z_index = -8
	_shadows.z_as_relative = false
	_shadows.draw.connect(_draw_shadows)
	add_child(_shadows)
	var frames := SpriteFrames.new()
	frames.set_animation_speed(&"default", 9.0)
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
		sprite.speed_scale = rng.randf_range(0.8, 1.2)
		add_child(sprite)
		_gulls.append({
			"sprite": sprite,
			"angle": rng.randf() * TAU,
			"speed": rng.randf_range(0.18, 0.3) * (1.0 if rng.randf() < 0.7 else -1.0),
			"radius": radius * rng.randf_range(0.6, 1.1),
			"offset": Vector2(rng.randf_range(-40, 40), rng.randf_range(-24, 24)),
			"wobble": rng.randf() * TAU,
		})


func _process(delta: float) -> void:
	for g in _gulls:
		g.angle += g.speed * delta
		g.wobble += delta * 0.7
		var r: Vector2 = g.radius * (1.0 + 0.12 * sin(g.wobble))
		var pos: Vector2 = g.offset + Vector2(cos(g.angle) * r.x, sin(g.angle) * r.y)
		var heading := Vector2(-sin(g.angle) * r.x, cos(g.angle) * r.y) * signf(g.speed)
		var sprite: AnimatedSprite2D = g.sprite
		sprite.position = pos.round()
		# Drawn side-on, flying right: face the way it's flying.
		sprite.flip_h = heading.x < 0.0
	_shadows.queue_redraw()


func _draw_shadows() -> void:
	for g in _gulls:
		var at: Vector2 = (g.sprite as AnimatedSprite2D).position + Vector2(10, height)
		_shadows.draw_rect(Rect2(at - Vector2(5, 1), Vector2(10, 2)), Color(0, 0.05, 0.1, 0.18))
		_shadows.draw_rect(Rect2(at - Vector2(3, 2), Vector2(6, 4)), Color(0, 0.05, 0.1, 0.12))
