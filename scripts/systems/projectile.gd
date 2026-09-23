class_name Projectile
extends Hitbox
## Pistol shot. Flies straight, stops at the first hurtbox or wall.

@export var speed := 320.0
@export var lifetime := 0.8

var direction := Vector2.RIGHT


func _ready() -> void:
	rotation = direction.angle()
	hit_landed.connect(func(_h: Hurtbox) -> void: queue_free())
	body_entered.connect(func(_b: Node2D) -> void: queue_free())
	get_tree().create_timer(lifetime).timeout.connect(queue_free)


func _physics_process(delta: float) -> void:
	position += direction * speed * delta


func _draw() -> void:
	draw_rect(Rect2(-3, -1, 6, 2), Color(1.0, 0.9, 0.5))
	draw_rect(Rect2(-5, -1, 2, 2), Color(1.0, 0.6, 0.2, 0.6))
