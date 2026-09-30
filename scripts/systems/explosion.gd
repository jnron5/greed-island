class_name Explosion
extends Hitbox
## The burst of an Emberburst round: one frame of area damage round the point of
## impact (every hurtbox inside, same level only, never its owner), then a flash
## and a ring of embers that fade.

const RADIUS := 40.0
const LIFE := 0.45

var _age := 0.0
var _embers: Array[Vector2] = []


func _init() -> void:
	collision_layer = 64
	collision_mask = 0
	monitoring = false
	knockback = 220.0
	var shape := CollisionShape2D.new()
	var circle := CircleShape2D.new()
	circle.radius = RADIUS
	shape.shape = circle
	add_child(shape)
	z_index = 5
	for i in 14:
		_embers.append(Vector2.from_angle(TAU * i / 14.0 + randf() * 0.4) * randf_range(0.5, 1.0))


func _ready() -> void:
	Sfx.play(&"explosion")
	Combat.shake(get_tree(), 4.0, 6)
	var light := LampLight.new()
	light.always_on = true
	light.max_energy = 1.4
	light.tint = Color(1.0, 0.7, 0.35)
	light.flicker = 0.0
	light.texture_scale = 1.1
	add_child(light)
	create_tween().tween_property(light, "max_energy", 0.0, LIFE)
	# Damage lands on the first physics frame only; the rest is the show.
	get_tree().create_timer(0.08, false, true).timeout.connect(func() -> void:
		for child in get_children():
			if child is CollisionShape2D:
				child.set_deferred(&"disabled", true))


func _process(delta: float) -> void:
	_age += delta
	if _age >= LIFE:
		queue_free()
	queue_redraw()


func _draw() -> void:
	var t := _age / LIFE
	var r := RADIUS * (0.35 + 0.65 * sqrt(t))
	var fade := 1.0 - t
	draw_circle(Vector2.ZERO, r * 0.8, Color(1.0, 0.85, 0.45, 0.45 * fade * fade))
	draw_circle(Vector2.ZERO, r * 0.45 * (1.0 - t), Color(1.0, 1.0, 0.85, 0.9 * fade))
	draw_arc(Vector2.ZERO, r, 0, TAU, 32, Color(1.0, 0.55, 0.2, 0.8 * fade), 2.0)
	for e in _embers:
		var p := e * r * 1.1
		draw_rect(Rect2(p - Vector2.ONE, Vector2(2, 2)), Color(1.0, 0.6 + 0.3 * e.x, 0.2, fade))
