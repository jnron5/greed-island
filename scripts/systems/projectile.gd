class_name Projectile
extends Hitbox
## Pistol shot. Flies straight, stops at the first hurtbox or wall. A charged
## (Emberburst) shot is bigger and slower and bursts where it stops.

@export var speed := 320.0
@export var lifetime := 0.8

var direction := Vector2.RIGHT
## Set before adding: bursts into an Explosion of this damage where it stops.
var explosive := false
var burst_damage := 3
## An ice shard (the Rime Stag's stamp) rather than a bullet: drawn pale blue.
var ice := false

var _done := false


func _ready() -> void:
	rotation = direction.angle()
	if explosive:
		speed *= 0.8
		var light := LampLight.new()
		light.always_on = true
		light.max_energy = 0.8
		light.tint = Color(1.0, 0.6, 0.3)
		light.flicker = 0.0
		light.texture_scale = 0.4
		add_child(light)
	hit_landed.connect(func(_h: Hurtbox) -> void:
		if source_id == GameState.PLAYER:
			Combat.shake(get_tree(), 1.5, 2)
		_finish())
	body_entered.connect(func(_b: Node2D) -> void: _finish())
	get_tree().create_timer(lifetime).timeout.connect(_finish)


func _finish() -> void:
	if _done:
		return
	_done = true
	if explosive and is_inside_tree():
		var burst := Explosion.new()
		burst.damage = burst_damage
		burst.source_id = source_id
		burst.level = level
		burst.position = position
		get_parent().add_child.call_deferred(burst)
	queue_free()


func _physics_process(delta: float) -> void:
	position += direction * speed * delta


func _draw() -> void:
	if ice:
		draw_colored_polygon(PackedVector2Array([Vector2(6, 0), Vector2(-2, -3), Vector2(-6, 0), Vector2(-2, 3)]), Color(0.75, 0.92, 1.0))
		draw_line(Vector2(-5, 0), Vector2(5, 0), Color(1, 1, 1, 0.9), 1.0)
		return
	if explosive:
		draw_circle(Vector2.ZERO, 4.0, Color(1.0, 0.55, 0.2, 0.5))
		draw_circle(Vector2.ZERO, 2.5, Color(1.0, 0.9, 0.55))
		draw_rect(Rect2(-9, -1.5, 5, 3), Color(1.0, 0.5, 0.15, 0.5))
		return
	draw_rect(Rect2(-3, -1, 6, 2), Color(1.0, 0.9, 0.5))
	draw_rect(Rect2(-5, -1, 2, 2), Color(1.0, 0.6, 0.2, 0.6))
