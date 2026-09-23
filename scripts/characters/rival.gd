class_name Rival
extends CharacterBody2D
## AI collector racing the player. First-slice state machine:
## find card -> carry -> return home -> bind, plus stealth: an Awareness meter
## watching the player, fleeing home when alerted, and sneaking up behind the
## player to lift a loose card. (Hunt boss comes later.)
## Carried cards stay Loose until bound at home, and that is the window the player exploits.

enum State { IDLE, SEEK, RETURN, BIND, SNEAK }

@export var collector_id: StringName = &"runner"
@export var sprite_frames: SpriteFrames
@export var move_speed := 95.0
## Head home to bind once carrying this many loose cards.
@export var carry_limit := 2
@export var search_radius := 700.0
@export var idle_time := 2.5
## Where this rival binds its haul. Should sit inside a safe zone.
@export var home: Marker2D
@export_group("Stealth")
## Chance, each time the player is nearby with loose cards, that this rival tries to lift one.
@export var steal_urge := 0.35
@export var steal_cooldown := 20.0
@export var sneak_notice_radius := 110.0
@export var sneak_timeout := 5.0
@export var flee_speed_multiplier := 1.3

var facing := Vector2.DOWN

var _state := State.IDLE
var _state_time := 0.0
var _target: CardPickup
var _stuck_time := 0.0
var _detour_time := 0.0
var _detour_dir := Vector2.ZERO
var _last_position := Vector2.ZERO
var _sneak_cd := 5.0
var _fleeing := false
## Draws the sight cone on the ground layer, under every character.
var _cone := Node2D.new()

@onready var sprite: AnimatedSprite2D = $AnimatedSprite2D
@onready var awareness: Awareness = $Awareness


func _ready() -> void:
	if collector_id not in GameState.active_rivals:
		_cone.free()
		queue_free()  # Not one of the 2 rivals racing this playthrough.
		return
	add_to_group(&"collectors")
	add_to_group(&"rivals")
	if sprite_frames:
		sprite.sprite_frames = sprite_frames
	_last_position = global_position
	_cone.z_index = -5
	add_child(_cone)
	_cone.draw.connect(_draw_sight_cone)
	awareness.level_changed.connect(_on_awareness_changed)
	EventBus.stealth_failed.connect(_on_stealth_failed)


func _physics_process(delta: float) -> void:
	_state_time += delta
	_sneak_cd -= delta
	var player := _player()
	awareness.facing = facing
	awareness.update(delta, player)

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
				_fleeing = false
				_enter(State.BIND)
			else:
				_steer_toward(home_pos, delta)
		State.BIND:
			velocity = Vector2.ZERO
			_process_bind()
		State.SNEAK:
			_process_sneak(player, delta)

	if _state in [State.IDLE, State.SEEK]:
		_consider_sneaking(player)
	if _fleeing:
		velocity *= flee_speed_multiplier
	elif awareness.level == Awareness.Level.SUSPICIOUS and _state != State.SNEAK:
		velocity *= 0.4  # Slows down to look around.
	move_and_slide()
	_update_facing(player, delta)
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


## Occasionally decide to lift a card off a nearby player carrying loose cards.
func _consider_sneaking(player: Node2D) -> void:
	if player == null or _sneak_cd > 0.0 or awareness.level == Awareness.Level.ALERT:
		return
	if global_position.distance_to(player.global_position) > sneak_notice_radius:
		return
	if GameState.grace_left(GameState.PLAYER) > 0.0 \
			or GameState.stealable_card_ids(GameState.PLAYER, CardCollection.LOOSE_ONLY).is_empty():
		return
	_sneak_cd = steal_cooldown
	if randf() < steal_urge:
		_enter(State.SNEAK)


## Circle in behind the player, then try the lift.
func _process_sneak(player: Node2D, delta: float) -> void:
	if player == null or _state_time > sneak_timeout:
		_enter(State.SEEK)
		return
	var behind: Vector2 = player.global_position - (player.get(&"facing") as Vector2).normalized() * 14.0
	if global_position.distance_to(player.global_position) <= Stealth.STEAL_RANGE - 4.0:
		var result := Stealth.attempt(self, player)
		if not result.ok:
			_fleeing = result.reason == "Caught"
		_enter(State.RETURN if carried_count() > 0 or _fleeing else State.SEEK)
		return
	_steer_toward(behind, delta)


func _on_awareness_changed(level: Awareness.Level) -> void:
	# Alerted while carrying: run home and bind before anyone gets another try.
	if level == Awareness.Level.ALERT and carried_count() > 0 and _state != State.BIND:
		_fleeing = true
		_enter(State.RETURN)


func _on_stealth_failed(thief: StringName, _victim: StringName) -> void:
	if thief == collector_id:
		_fleeing = true  # Caught red-handed: bolt.
		_enter(State.RETURN)


func carried_count() -> int:
	var col := GameState.collection(collector_id)
	var n := 0
	for id in col.card_ids():
		n += col.count(id, CardCollection.State.LOOSE)
	return n


func _player() -> Node2D:
	return get_tree().get_first_node_in_group(&"player") as Node2D


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


## Face where we're going; when suspicious and stopped, turn toward the noise.
func _update_facing(player: Node2D, delta: float) -> void:
	if awareness.level == Awareness.Level.SUSPICIOUS and player and awareness.value > 55.0:
		var to_player := global_position.direction_to(player.global_position)
		facing = Vector2.from_angle(rotate_toward(facing.angle(), to_player.angle(), 1.5 * delta))
	elif velocity.length() > 1.0:
		facing = velocity.normalized()


func _update_animation() -> void:
	if sprite.sprite_frames == null:
		return
	var dir := Player.direction_name(facing)
	var action := "run" if velocity.length() > 1.0 else "idle"
	for candidate in [action, "idle"]:
		var anim := StringName("%s_%s" % [candidate, dir])
		if sprite.sprite_frames.has_animation(anim):
			if sprite.animation != anim:
				sprite.play(anim)
			return


func _draw() -> void:
	_cone.queue_redraw()
	# Carried (loose, stealable) cards fan out above the hood.
	var n := carried_count()
	for i in n:
		var x := (i - (n - 1) / 2.0) * 7.0
		draw_rect(Rect2(x - 3, -66, 6, 8), Color(0.1, 0.08, 0.06))
		draw_rect(Rect2(x - 2, -65, 4, 6), Color(0.95, 0.85, 0.45))
	_draw_awareness_marker()
	_draw_steal_prompt()


func _draw_sight_cone() -> void:
	var colors := {
		Awareness.Level.UNAWARE: Color(1, 1, 1, 0.07),
		Awareness.Level.SUSPICIOUS: Color(1, 0.85, 0.2, 0.12),
		Awareness.Level.ALERT: Color(1, 0.25, 0.2, 0.16),
	}
	var points := PackedVector2Array([Vector2.ZERO])
	var half := deg_to_rad(awareness.sight_half_angle_deg)
	for i in 13:
		var a := facing.angle() - half + (2.0 * half) * i / 12.0
		points.append(Vector2.from_angle(a) * awareness.sight_radius)
	_cone.draw_colored_polygon(points, colors[awareness.level])


func _draw_awareness_marker() -> void:
	if awareness.level == Awareness.Level.UNAWARE and awareness.value < 5.0:
		return
	var font := ThemeDB.fallback_font
	var color := Color(1, 0.3, 0.25) if awareness.level == Awareness.Level.ALERT else Color(1, 0.85, 0.2)
	if awareness.level != Awareness.Level.UNAWARE:
		var mark := "!" if awareness.level == Awareness.Level.ALERT else "?"
		draw_string_outline(font, Vector2(-3, -72), mark, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, 3, Color.BLACK)
		draw_string(font, Vector2(-3, -72), mark, HORIZONTAL_ALIGNMENT_LEFT, -1, 12, color)
	# Meter under the marker.
	draw_rect(Rect2(-9, -70, 18, 3), Color(0, 0, 0, 0.6))
	draw_rect(Rect2(-8, -69, 16.0 * awareness.value / 100.0, 1), color)


func _draw_steal_prompt() -> void:
	var player := _player()
	if player == null or global_position.distance_to(player.global_position) > Stealth.STEAL_RANGE:
		return
	var text := Stealth.blocker(player, self)
	if text == "":
		text = "E: Steal %d%%" % roundi(Stealth.success_chance(player, self) * 100.0)
	var font := ThemeDB.fallback_font
	draw_string_outline(font, Vector2(-24, -84), text, HORIZONTAL_ALIGNMENT_LEFT, -1, 8, 3, Color.BLACK)
	draw_string(font, Vector2(-24, -84), text, HORIZONTAL_ALIGNMENT_LEFT, -1, 8, Color.WHITE)
