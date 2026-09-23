class_name Player
extends CharacterBody2D
## Top-down 8-directional player: move, dash, sword swing, pistol shot.
## Animations are named "<action>_<direction>", e.g. "run_south_east".

signal health_changed(current: int, maximum: int)
signal died

enum State { MOVE, DASH, SWORD, DEAD }

## Indexed by facing angle in 45° steps, starting at east and turning clockwise.
const DIRECTIONS: Array[String] = [
	"east", "south_east", "south", "south_west", "west", "north_west", "north", "north_east",
]

@export var collector_id: StringName = &"player"
@export var move_speed := 110.0
@export_group("Dash")
@export var dash_speed := 260.0
@export var dash_duration := 0.15
@export var dash_cooldown := 0.5
@export_group("Sword")
@export var sword_damage := 2
@export var sword_active_time := 0.12
@export var sword_recovery := 0.14
@export_group("Pistol")
@export var projectile_scene: PackedScene
@export var pistol_damage := 1
@export var pistol_cooldown := 0.35
@export_group("Health")
@export var max_health := 6
@export var hurt_invulnerability := 0.6

var facing := Vector2.DOWN
var health := 0

var _state := State.MOVE
var _state_time := 0.0
var _dash_cd := 0.0
var _pistol_cd := 0.0
var _dash_dir := Vector2.ZERO

@onready var sprite: AnimatedSprite2D = $AnimatedSprite2D
@onready var sword_pivot: Node2D = $SwordPivot
@onready var sword_hitbox: Hitbox = $SwordPivot/SwordHitbox
@onready var sword_shape: CollisionShape2D = $SwordPivot/SwordHitbox/CollisionShape2D
@onready var hurtbox: Hurtbox = $Hurtbox


func _ready() -> void:
	add_to_group(&"player")
	health = max_health
	sword_hitbox.damage = sword_damage
	sword_hitbox.source_id = collector_id
	sword_shape.disabled = true
	hurtbox.hurt.connect(_on_hurt)
	health_changed.emit(health, max_health)


func _physics_process(delta: float) -> void:
	_state_time += delta
	_dash_cd -= delta
	_pistol_cd -= delta

	match _state:
		State.MOVE:
			_process_move()
		State.DASH:
			velocity = _dash_dir * dash_speed
			if _state_time >= dash_duration:
				hurtbox.invulnerable = false
				_enter(State.MOVE)
		State.SWORD:
			velocity = velocity.move_toward(Vector2.ZERO, move_speed * 8.0 * delta)
			if _state_time >= sword_active_time:
				sword_shape.set_deferred(&"disabled", true)
			if _state_time >= sword_active_time + sword_recovery:
				_enter(State.MOVE)
		State.DEAD:
			velocity = Vector2.ZERO

	move_and_slide()
	_update_animation()


func _process_move() -> void:
	var input := Input.get_vector(&"move_left", &"move_right", &"move_up", &"move_down")
	velocity = input * move_speed
	if input != Vector2.ZERO:
		facing = input.normalized()

	if Input.is_action_just_pressed(&"dash") and _dash_cd <= 0.0:
		_dash_dir = facing if input == Vector2.ZERO else input.normalized()
		_dash_cd = dash_cooldown
		hurtbox.invulnerable = true
		_enter(State.DASH)
	elif Input.is_action_just_pressed(&"sword"):
		sword_pivot.rotation = facing.angle()
		sword_shape.set_deferred(&"disabled", false)
		_enter(State.SWORD)
	elif Input.is_action_just_pressed(&"pistol") and _pistol_cd <= 0.0:
		_fire_pistol()


func _fire_pistol() -> void:
	if projectile_scene == null:
		return
	_pistol_cd = pistol_cooldown
	var shot := projectile_scene.instantiate() as Projectile
	shot.direction = facing
	shot.damage = pistol_damage
	shot.source_id = collector_id
	shot.global_position = global_position + Vector2(0, -18) + facing * 10.0
	get_parent().add_child(shot)


func _enter(state: State) -> void:
	_state = state
	_state_time = 0.0


func _on_hurt(hitbox: Hitbox) -> void:
	if _state == State.DEAD:
		return
	health = maxi(health - hitbox.damage, 0)
	health_changed.emit(health, max_health)
	velocity = (global_position - hitbox.global_position).normalized() * hitbox.knockback
	if health == 0:
		_enter(State.DEAD)
		died.emit()
		return
	hurtbox.invulnerable = true
	sprite.modulate = Color(1, 0.5, 0.5)
	await get_tree().create_timer(hurt_invulnerability).timeout
	sprite.modulate = Color.WHITE
	if _state != State.DASH:
		hurtbox.invulnerable = false


func heal(amount: int) -> void:
	health = mini(health + amount, max_health)
	health_changed.emit(health, max_health)


func facing_name() -> String:
	return DIRECTIONS[wrapi(roundi(facing.angle() / (PI / 4.0)), 0, 8)]


func _update_animation() -> void:
	var action := "idle"
	match _state:
		State.MOVE:
			action = "run" if velocity.length() > 1.0 else "idle"
		State.DASH:
			action = "dash"
		State.SWORD:
			action = "sword"
	_play(action)


## Plays "<action>_<facing>", falling back to run/idle while art is missing.
func _play(action: String) -> void:
	if sprite.sprite_frames == null:
		return
	var dir := facing_name()
	for candidate in [action, "run" if action == "dash" else "idle"]:
		var anim := StringName("%s_%s" % [candidate, dir])
		if sprite.sprite_frames.has_animation(anim):
			if sprite.animation != anim:
				sprite.play(anim)
			return
