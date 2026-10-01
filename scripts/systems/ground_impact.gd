class_name GroundImpact
extends Hitbox
## A boss attack that lands on a marked spot: a ring on the ground fills for
## `delay` seconds (step out of it), then the blow lands for one moment (a hurled
## boulder, a stone pillar bursting up) and its rubble fades. Monster-owned.

@export var delay := 1.0
@export var radius := 30.0
## Drawn where it lands (a boulder, a pillar); optional.
@export var texture: Texture2D

const LINGER := 0.7

var _age := 0.0
var _shape := CollisionShape2D.new()


func _init() -> void:
	collision_layer = 128
	collision_mask = 0
	monitoring = false
	knockback = 200.0
	source_id = Combat.MONSTER
	z_index = 1


func _ready() -> void:
	var circle := CircleShape2D.new()
	circle.radius = radius
	_shape.shape = circle
	_shape.disabled = true
	add_child(_shape)


func _physics_process(delta: float) -> void:
	_age += delta
	if _age >= delay and _shape.disabled and _age < delay + 0.15:
		_shape.set_deferred(&"disabled", false)
		Combat.shake(get_tree(), 3.0, 4)
		Sfx.play(&"explosion")
	elif _age >= delay + 0.15 and not _shape.disabled:
		_shape.set_deferred(&"disabled", true)
	if _age >= delay + LINGER:
		queue_free()
	queue_redraw()


func _draw() -> void:
	if _age < delay:
		var t := _age / delay
		draw_set_transform(Vector2.ZERO, 0.0, Vector2(1.0, 0.5))
		draw_circle(Vector2.ZERO, radius * t, Color(1.0, 0.75, 0.3, 0.25))
		draw_arc(Vector2.ZERO, radius, 0, TAU, 28, Color(1.0, 0.8, 0.35, 0.9), 2.0)
		draw_set_transform(Vector2.ZERO)
		return
	var fade := 1.0 - clampf((_age - delay) / LINGER, 0.0, 1.0)
	if texture:
		var size := texture.get_size()
		draw_texture(texture, Vector2(-size.x / 2.0, -size.y + 4), Color(1, 1, 1, fade))
	else:
		draw_set_transform(Vector2.ZERO, 0.0, Vector2(1.0, 0.5))
		draw_circle(Vector2.ZERO, radius, Color(0.45, 0.4, 0.35, 0.6 * fade))
		draw_set_transform(Vector2.ZERO)
