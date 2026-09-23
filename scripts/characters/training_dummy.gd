class_name TrainingDummy
extends StaticBody2D
## Stand-in for a regular monster until real ones exist: takes sword/pistol
## hits, drops a common card when broken, and respawns after a cooldown.

@export var max_health := 4
@export var respawn_time := 6.0
@export var drop_card_ids: Array[StringName] = [&"thorn_sprig", &"moss_lantern", &"hollow_acorn"]
@export var pickup_scene: PackedScene

var health := 0
var _flash := 0.0

@onready var hurtbox: Hurtbox = $Hurtbox
@onready var body_shape: CollisionShape2D = $CollisionShape2D


func _ready() -> void:
	hurtbox.hurt.connect(_on_hurt)
	_respawn()


func _process(delta: float) -> void:
	if _flash > 0.0:
		_flash -= delta
		queue_redraw()


func _on_hurt(hitbox: Hitbox) -> void:
	if health <= 0:
		return
	health -= hitbox.damage
	_flash = 0.1
	queue_redraw()
	if health <= 0:
		_break()


func _break() -> void:
	visible = false
	body_shape.set_deferred(&"disabled", true)
	hurtbox.set_deferred(&"monitoring", false)
	if pickup_scene and not drop_card_ids.is_empty():
		var pickup := pickup_scene.instantiate() as CardPickup
		pickup.card_id = drop_card_ids.pick_random()
		pickup.position = position + Vector2(randf_range(-12, 12), 14)
		get_parent().add_child.call_deferred(pickup)
	get_tree().create_timer(respawn_time).timeout.connect(_respawn)


func _respawn() -> void:
	health = max_health
	visible = true
	body_shape.set_deferred(&"disabled", false)
	hurtbox.set_deferred(&"monitoring", true)
	queue_redraw()


func _draw() -> void:
	var wood := Color.WHITE if _flash > 0.0 else Color(0.55, 0.38, 0.22)
	draw_rect(Rect2(-6, 4, 12, 3), Color(0, 0, 0, 0.25))
	draw_rect(Rect2(-2, -6, 4, 12), wood.darkened(0.2))
	draw_rect(Rect2(-8, -8, 16, 4), wood)
	draw_circle(Vector2(0, -13), 5.0, Color.WHITE if _flash > 0.0 else Color(0.85, 0.75, 0.55))
