class_name Rival
extends CharacterBody2D
## AI collector racing the player. First-slice state machine:
## find card -> carry -> return home -> bind (hunt boss comes later).
## Carried cards stay Loose until bound at home, and that is the window a
## Pickpocket's Whisper exploits. Floating cards above the head show how many are carried.

enum State { IDLE, SEEK, RETURN, BIND }

@export var collector_id: StringName = &"runner"
@export var sprite_frames: SpriteFrames
@export var move_speed := 95.0
## Head home to bind once carrying this many loose cards.
@export var carry_limit := 2
@export var search_radius := 700.0
@export var idle_time := 2.5
## Where this rival binds its haul. Should sit inside a safe zone.
@export var home: Marker2D

var facing := Vector2.DOWN

var _state := State.IDLE
var _state_time := 0.0
var _target: CardPickup
var _stuck_time := 0.0
var _detour_time := 0.0
var _detour_dir := Vector2.ZERO
var _last_position := Vector2.ZERO

@onready var sprite: AnimatedSprite2D = $AnimatedSprite2D


func _ready() -> void:
	if collector_id not in GameState.active_rivals:
		queue_free()  # Not one of the 2 rivals racing this playthrough.
		return
	add_to_group(&"collectors")
	add_to_group(&"rivals")
	if sprite_frames:
		sprite.sprite_frames = sprite_frames
	_last_position = global_position


func _physics_process(delta: float) -> void:
	_state_time += delta
	match _state:
		State.IDLE:
			velocity = Vector2.ZERO
			if _state_time >= idle_time:
				_enter(State.SEEK)
		State.SEEK:
			_process_seek()
		State.RETURN:
			var home_pos := home.global_position if home else global_position
			if global_position.distance_to(home_pos) < 6.0:
				_enter(State.BIND)
			else:
				_steer_toward(home_pos, delta)
		State.BIND:
			velocity = Vector2.ZERO
			_process_bind()
	move_and_slide()
	_update_animation()
	queue_redraw()


func _process_seek() -> void:
	if not is_instance_valid(_target) or _target.is_queued_for_deletion():
		_target = null
		if carried_count() >= carry_limit:
			_enter(State.RETURN)
			return
		_target = _find_nearest_pickup()
		if _target == null:
			_enter(State.RETURN if carried_count() > 0 else State.IDLE)
			return
	_steer_toward(_target.global_position, get_physics_process_delta_time())


## Binds one loose card per bind_time; instant when home is in a safe zone.
func _process_bind() -> void:
	if _state_time < GameState.bind_time(collector_id):
		return
	var col := GameState.collection(collector_id)
	for id in col.card_ids():
		if col.count(id, CardCollection.State.LOOSE) > 0:
			GameState.bind_card(collector_id, id)
			_state_time = 0.0
			if GameState.bind_time(collector_id) > 0.0:
				return
	_enter(State.IDLE)


func carried_count() -> int:
	var col := GameState.collection(collector_id)
	var n := 0
	for id in col.card_ids():
		n += col.count(id, CardCollection.State.LOOSE)
	return n


func _find_nearest_pickup() -> CardPickup:
	var best: CardPickup = null
	var best_dist := search_radius
	for node in get_tree().get_nodes_in_group(&"card_pickups"):
		var pickup := node as CardPickup
		if pickup == null or pickup.is_queued_for_deletion():
			continue
		var d := global_position.distance_to(pickup.global_position)
		if d < best_dist:
			best = pickup
			best_dist = d
	return best


## Straight-line steering with a sidestep when blocked (no navmesh yet).
func _steer_toward(point: Vector2, delta: float) -> void:
	var dir := global_position.direction_to(point)
	if _detour_time > 0.0:
		_detour_time -= delta
		dir = (dir + _detour_dir * 1.5).normalized()
	velocity = dir * move_speed
	if global_position.distance_to(_last_position) < move_speed * delta * 0.25:
		_stuck_time += delta
		if _stuck_time > 0.3:
			_detour_dir = dir.orthogonal() * (1.0 if randf() < 0.5 else -1.0)
			_detour_time = 0.5
			_stuck_time = 0.0
	else:
		_stuck_time = 0.0
	_last_position = global_position


func _enter(state: State) -> void:
	_state = state
	_state_time = 0.0


func _update_animation() -> void:
	if sprite.sprite_frames == null:
		return
	if velocity.length() > 1.0:
		facing = velocity.normalized()
	var dir := Player.direction_name(facing)
	var action := "run" if velocity.length() > 1.0 else "idle"
	for candidate in [action, "idle"]:
		var anim := StringName("%s_%s" % [candidate, dir])
		if sprite.sprite_frames.has_animation(anim):
			if sprite.animation != anim:
				sprite.play(anim)
			return


func _draw() -> void:
	# Carried (loose, stealable) cards fan out above the hood.
	var n := carried_count()
	for i in n:
		var x := (i - (n - 1) / 2.0) * 7.0
		draw_rect(Rect2(x - 3, -66, 6, 8), Color(0.1, 0.08, 0.06))
		draw_rect(Rect2(x - 2, -65, 4, 6), Color(0.95, 0.85, 0.45))
