class_name Boss
extends CharacterBody2D
## Zone boss fight (the Canopy Warden is the first). Loop:
##   DORMANT  hidden in the canopy until a collector enters the arena
##   CANOPY   invulnerable, only a shadow on the ground, drifting after its target
##   DROP     a red ring marks where it will land, then SLAM (area damage)
##   GROUNDED vulnerable; SWIPE (close) or LASH (a long vine line) 2x, 3x when enraged
##   RECOVER  winded and vulnerable, then CLIMB back into the canopy
## Enraged below half health: shorter telegraphs, one extra attack per landing.
## Drops one of each of its cards on death; GameState tracks kills and the
## gate-based respawn (it only comes back when a respawn gate opens).
## 4-directional animations: "idle_<dir>", "walk_<dir>", "attack_<dir>".

enum State { DORMANT, CANOPY, DROP, SLAM, GROUNDED, SWIPE_WINDUP, SWIPE, LASH_WINDUP, LASH, RECOVER, CLIMB, DEAD }

const DIRECTIONS_4: Array[String] = ["east", "south", "west", "north"]

@export var boss_id: StringName = &"canopy_warden"
@export var sprite_frames: SpriteFrames
@export var max_health := 36
## Wakes when a collector comes this close to its lair.
@export var wake_radius := 230.0
## Loses interest (and heals) when nobody is within this of its lair.
@export var arena_radius := 420.0
@export var canopy_speed := 120.0
@export var ground_speed := 45.0
@export var canopy_time := 2.2
@export var drop_time := 0.9
@export var swipe_windup := 0.55
@export var lash_windup := 0.75
@export var lash_length := 170.0
@export var recover_time := 1.3
@export var attack_damage := 2
@export var pickup_scene: PackedScene = preload("res://scenes/systems/card_pickup.tscn")

var health := 0
var facing := Vector2.DOWN
## Set when a collector strikes another mid-fight: the shared fight is off.
var truce_broken := false
## Collectors who have landed a blow on it this fight.
var _fighters: Dictionary = {}

var _state := State.DORMANT
var _state_time := 0.0
var _lair := Vector2.ZERO
var _target: Node2D
var _attacks_left := 0
var _aim := Vector2.DOWN
var _killer: StringName = &""
var _flash := 0.0
var _alone_time := 0.0
## Death show; killed if the boss returns before it finishes.
var _death_tween: Tween
var _dying := false
var _base_scale := Vector2.ONE
## Draws the death show's light (over the boss, whatever its own _draw does).
var _fx := Node2D.new()
var _dying_time := 0.0
## 1 at the moment it breaks apart, fading to 0: the flash and rising motes.
var _burst := 0.0

@onready var sprite: AnimatedSprite2D = $AnimatedSprite2D
@onready var body_shape: CollisionShape2D = $CollisionShape2D
@onready var hurtbox: Hurtbox = $Hurtbox
@onready var slam_shape: CollisionShape2D = $SlamHitbox/CollisionShape2D
@onready var swipe_hitbox: Hitbox = $SwipeHitbox
@onready var swipe_shape: CollisionShape2D = $SwipeHitbox/CollisionShape2D
@onready var lash_hitbox: Hitbox = $LashHitbox
@onready var lash_shape: CollisionShape2D = $LashHitbox/CollisionShape2D


func _ready() -> void:
	add_to_group(&"bosses")
	if sprite_frames:
		sprite.sprite_frames = sprite_frames
	_base_scale = sprite.scale
	_fx.z_index = 3
	add_child(_fx)
	_fx.draw.connect(_draw_death_fx)
	_lair = global_position
	hurtbox.owner_id = Combat.MONSTER
	hurtbox.hurt.connect(_on_hurt)
	hurtbox.hurt.connect(_note_fighter)
	for hitbox: Hitbox in [$SlamHitbox, swipe_hitbox, lash_hitbox]:
		hitbox.source_id = Combat.MONSTER
		hitbox.damage = attack_damage
	for shape in [slam_shape, swipe_shape, lash_shape]:
		shape.disabled = true
	health = max_health
	EventBus.boss_returned.connect(_on_boss_returned)
	if GameState.is_boss_alive(boss_id):
		_hide_in_canopy()
		_enter(State.DORMANT)
	else:
		_go_quiet()


func _physics_process(delta: float) -> void:
	_state_time += delta
	if _flash > 0.0:
		_flash -= delta
		sprite.modulate = Color(3, 3, 3) if _flash > 0.0 else Color.WHITE
	var rate := 0.75 if enraged() else 1.0
	if _state not in [State.DORMANT, State.DEAD]:
		_track_target(delta)

	match _state:
		State.DORMANT:
			velocity = Vector2.ZERO
			_target = _find_target(wake_radius)
			if _target:
				EventBus.notify.emit("The canopy stirs... the %s!" % _display_name())
				_show_bar(true)
				_enter(State.CANOPY)
		State.CANOPY:
			velocity = global_position.direction_to(_target.global_position) * canopy_speed if _target else Vector2.ZERO
			if _state_time >= canopy_time * rate and _target:
				velocity = Vector2.ZERO
				_enter(State.DROP)
		State.DROP:
			velocity = Vector2.ZERO
			if _state_time >= drop_time * rate:
				_land()
		State.SLAM:
			if _state_time >= 0.15:
				slam_shape.set_deferred(&"disabled", true)
				_attacks_left = 3 if enraged() else 2
				_enter(State.GROUNDED)
		State.GROUNDED:
			velocity = global_position.direction_to(_target.global_position) * ground_speed if _target else Vector2.ZERO
			if _state_time >= 0.5 and _target:
				velocity = Vector2.ZERO
				_aim = global_position.direction_to(_target.global_position)
				facing = _aim
				var close := global_position.distance_to(_target.global_position) < 60.0
				_enter(State.SWIPE_WINDUP if close else State.LASH_WINDUP)
		State.SWIPE_WINDUP:
			velocity = Vector2.ZERO
			if _state_time >= swipe_windup * rate:
				swipe_hitbox.position = _aim * 26.0 + Vector2(0, -14)
				swipe_shape.set_deferred(&"disabled", false)
				_enter(State.SWIPE)
		State.LASH_WINDUP:
			velocity = Vector2.ZERO
			if _state_time >= lash_windup * rate:
				lash_hitbox.rotation = _aim.angle()
				lash_hitbox.position = Vector2(0, -14)
				lash_shape.position = Vector2(lash_length / 2.0, 0)
				lash_shape.set_deferred(&"disabled", false)
				_enter(State.LASH)
		State.SWIPE, State.LASH:
			velocity = Vector2.ZERO
			if _state_time >= 0.18:
				swipe_shape.set_deferred(&"disabled", true)
				lash_shape.set_deferred(&"disabled", true)
				_attacks_left -= 1
				_enter(State.GROUNDED if _attacks_left > 0 else State.RECOVER)
		State.RECOVER:
			velocity = Vector2.ZERO
			if _state_time >= recover_time:
				_climb()
		State.CLIMB:
			velocity = Vector2.ZERO
		State.DEAD:
			velocity = Vector2.ZERO

	move_and_slide()
	_update_animation()
	queue_redraw()


func enraged() -> bool:
	return health <= max_health / 2


func is_vulnerable() -> bool:
	return _state in [State.SLAM, State.GROUNDED, State.SWIPE_WINDUP, State.SWIPE,
		State.LASH_WINDUP, State.LASH, State.RECOVER]


func is_dead() -> bool:
	return _state == State.DEAD


## Keeps a target while anyone fights in the arena; resets when everyone leaves.
func _track_target(delta: float) -> void:
	if not _valid_target(_target, arena_radius):
		_target = _find_target(arena_radius)
	if _target:
		_alone_time = 0.0
		return
	_alone_time += delta
	if _alone_time > 4.0 and _state == State.CANOPY:
		# Nobody left to fight: heal up and wait.
		health = max_health
		_show_bar(false)
		global_position = _lair
		_enter(State.DORMANT)


func _find_target(radius: float) -> Node2D:
	var best: Node2D = null
	var best_dist := INF
	for node in get_tree().get_nodes_in_group(&"collectors"):
		if not _valid_target(node, radius):
			continue
		var d := global_position.distance_to(node.global_position)
		if d < best_dist:
			best = node
			best_dist = d
	return best


## Untyped on purpose: the target may have been freed (rivals leave zones).
func _valid_target(n: Variant, radius: float) -> bool:
	if not is_instance_valid(n) or not (n is Node2D) or not n.is_inside_tree():
		return false
	var id: Variant = n.get(&"collector_id")
	if not (id is StringName) or GameState.is_in_safe_zone(id):
		return false
	if not Zone.same_level(get_tree(), global_position, n.global_position):
		return false
	if n.has_method(&"can_pick_up") and not n.can_pick_up():
		return false  # Down/dead collectors aren't worth attacking.
	return _lair.distance_to(n.global_position) <= radius


func _land() -> void:
	sprite.visible = true
	sprite.modulate.a = 1.0
	sprite.position.y = -120.0
	var tween := create_tween()
	tween.tween_property(sprite, "position:y", 0.0, 0.12).set_ease(Tween.EASE_IN)
	body_shape.set_deferred(&"disabled", false)
	hurtbox.set_deferred(&"monitoring", true)
	slam_shape.set_deferred(&"disabled", false)
	_shake_camera(6.0)
	_enter(State.SLAM)


func _climb() -> void:
	_enter(State.CLIMB)
	hurtbox.set_deferred(&"monitoring", false)
	body_shape.set_deferred(&"disabled", true)
	var tween := create_tween()
	tween.tween_property(sprite, "position:y", -120.0, 0.45).set_ease(Tween.EASE_OUT)
	tween.parallel().tween_property(sprite, "modulate:a", 0.0, 0.45)
	tween.tween_callback(_finish_climb)


func _finish_climb() -> void:
	_hide_in_canopy()
	_enter(State.CANOPY)


func _hide_in_canopy() -> void:
	sprite.visible = false
	sprite.position.y = 0.0
	body_shape.set_deferred(&"disabled", true)
	hurtbox.set_deferred(&"monitoring", false)


func _on_hurt(hitbox: Hitbox) -> void:
	if not is_vulnerable():
		return
	health = maxi(health - hitbox.damage, 0)
	_killer = hitbox.source_id
	_flash = 0.08
	Combat.pop_number(get_parent(), global_position, hitbox.damage)
	_show_bar(true)
	if health == 0:
		_die()


func _note_fighter(hitbox: Hitbox) -> void:
	if Combat.is_collector(hitbox.source_id) and is_vulnerable():
		_fighters[hitbox.source_id] = true


func _die() -> void:
	# Brought down by more than one collector with the truce kept: a shared win.
	var members := _fighters.keys()
	if members.size() >= 2 and not truce_broken:
		EventBus.boss_shared_win.emit(boss_id, members)
	_fighters.clear()
	truce_broken = false
	_enter(State.DEAD)
	for shape in [slam_shape, swipe_shape, lash_shape]:
		shape.set_deferred(&"disabled", true)
	body_shape.set_deferred(&"disabled", true)
	hurtbox.set_deferred(&"monitoring", false)
	GameState.kill_boss(boss_id, _killer)
	_show_bar(false)
	EventBus.notify.emit("The %s falls!" % _display_name())
	_dramatic_death()


## A boss doesn't just vanish. The world slows; it convulses, flashing white and red
## as the ground shakes; it sinks and crumples; it breaks apart in a burst of light
## and rising motes; and only then do its cards (and a purse of gold) spill out
## across the ground for whoever is quickest.
func _dramatic_death() -> void:
	var headless := DisplayServer.get_name() == "headless"
	var t := 0.05 if headless else 1.0
	_dying = true
	_dying_time = 0.0
	Sfx.play(&"roar")
	if not headless:
		Engine.time_scale = 0.3
		get_tree().create_timer(0.9, true, false, true).timeout.connect(func() -> void: Engine.time_scale = 1.0)
	_death_tween = create_tween()
	# 1. Convulsing: white and blood-red flashes, each with a jolt of the camera.
	for i in 8:
		_death_tween.tween_callback(func() -> void:
			sprite.modulate = Color(3, 3, 3) if i % 2 == 0 else Color(1.4, 0.35, 0.3)
			sprite.position.x = (2.0 if i % 2 == 0 else -2.0)
			_shake_camera(3.0 + i * 0.6))
		_death_tween.tween_interval(0.2 * t)
	_death_tween.tween_callback(func() -> void:
		sprite.position.x = 0.0
		sprite.modulate = Color(1.2, 0.8, 0.75))
	# 2. Collapsing: it sags and sinks into itself.
	_death_tween.tween_property(sprite, "scale", Vector2(1.08, 0.72) * sprite.scale, 0.9 * t).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	_death_tween.parallel().tween_property(sprite, "position:y", 10.0, 0.9 * t)
	_death_tween.parallel().tween_property(sprite, "modulate", Color(0.75, 0.7, 0.75), 0.9 * t)
	_death_tween.tween_callback(_collapsed)
	# 3. Breaking apart in light.
	_death_tween.tween_callback(func() -> void:
		_burst = 1.0
		_shake_camera(8.0)
		Sfx.play(&"explosion"))
	_death_tween.tween_property(sprite, "modulate:a", 0.0, 1.0 * t)
	_death_tween.parallel().tween_property(self, "_burst", 0.0, 1.0 * t)
	# 4. The prize.
	_death_tween.tween_callback(_spill_drops)
	_death_tween.tween_interval(1.2 * t)
	_death_tween.tween_callback(_go_quiet)


func _process(delta: float) -> void:
	if _dying or _burst > 0.0:
		_dying_time += delta
		_fx.queue_redraw()


## Motes of light rising off the dying boss, and the flash when it breaks apart.
func _draw_death_fx() -> void:
	if not _dying and _burst <= 0.0:
		return
	for i in 16:
		var phase := fmod(_dying_time * 0.6 + i / 16.0, 1.0)
		var x := sin(i * 2.4 + _dying_time * 2.0) * (14.0 + (i % 5) * 6.0)
		var p := Vector2(x, -10.0 - phase * 90.0)
		_fx.draw_circle(p, 1.5 if i % 3 else 2.2, Color(1.0, 0.93, 0.7, (1.0 - phase) * 0.85))
	if _burst > 0.0:
		var r := 20.0 + (1.0 - _burst) * 90.0
		_fx.draw_set_transform(Vector2(0, -30), 0.0, Vector2(1.0, 0.7))
		_fx.draw_circle(Vector2.ZERO, r, Color(1.0, 0.97, 0.85, _burst * 0.45))
		_fx.draw_arc(Vector2.ZERO, r + 6.0, 0, TAU, 40, Color(1.0, 0.85, 0.5, _burst), 3.0)
		_fx.draw_set_transform(Vector2.ZERO)


## Hook for a boss that leaves something behind when it collapses (the Colossus's rubble).
func _collapsed() -> void:
	pass


func _spill_drops() -> void:
	_dying = false
	var data := GameState.boss_data(boss_id)
	if data:
		for card_id in data.drop_card_ids:
			Combat.drop_loot(get_tree(), position, card_id, 0, &"", 40.0)
	Combat.drop_loot(get_tree(), position, &"", randi_range(30, 60), &"", 40.0)


## Dead (or not back yet): gone from the grove until a respawn gate opens.
func _go_quiet() -> void:
	_enter(State.DEAD)
	visible = false
	body_shape.set_deferred(&"disabled", true)
	hurtbox.set_deferred(&"monitoring", false)


func _on_boss_returned(id: StringName, _gate_id: StringName) -> void:
	if id != boss_id:
		return
	if _death_tween:
		_death_tween.kill()
	_dying = false
	_burst = 0.0
	sprite.scale = _base_scale
	sprite.position = Vector2.ZERO
	sprite.modulate = Color.WHITE
	health = max_health
	truce_broken = false
	_fighters.clear()
	visible = true
	global_position = _lair
	_hide_in_canopy()
	_enter(State.DORMANT)


func _enter(state: State) -> void:
	_state = state
	_state_time = 0.0


func _show_bar(shown: bool) -> void:
	EventBus.boss_bar.emit(_display_name(), health, max_health, shown)


func _display_name() -> String:
	var data := GameState.boss_data(boss_id)
	return data.display_name if data else String(boss_id)


func _shake_camera(strength: float) -> void:
	var camera := get_viewport().get_camera_2d()
	if camera == null:
		return
	var tween := create_tween()
	for i in 6:
		tween.tween_property(camera, "offset", Vector2(randf_range(-1, 1), randf_range(-1, 1)) * strength, 0.03)
	tween.tween_property(camera, "offset", Vector2.ZERO, 0.03)


func _update_animation() -> void:
	if sprite.sprite_frames == null or not sprite.visible:
		return
	if velocity.length() > 1.0:
		facing = velocity.normalized()
	var dir := DIRECTIONS_4[wrapi(roundi(facing.angle() / (PI / 2.0)), 0, 4)]
	var action := "idle"
	match _state:
		State.SWIPE_WINDUP, State.SWIPE, State.LASH_WINDUP, State.LASH, State.SLAM:
			action = "attack"
		State.GROUNDED:
			action = "walk" if velocity.length() > 1.0 else "idle"
	for candidate in [action, "walk", "idle"]:
		var anim := StringName("%s_%s" % [candidate, dir])
		if sprite.sprite_frames.has_animation(anim):
			if sprite.animation != anim:
				sprite.play(anim)
			return


func _draw() -> void:
	match _state:
		State.CANOPY, State.DORMANT:
			if _state == State.CANOPY:
				draw_set_transform(Vector2.ZERO, 0.0, Vector2(1.0, 0.45))
				draw_circle(Vector2.ZERO, 30.0, Color(0, 0, 0, 0.3))
				draw_set_transform(Vector2.ZERO)
		State.DROP:
			var t := clampf(_state_time / (drop_time * (0.75 if enraged() else 1.0)), 0.0, 1.0)
			draw_set_transform(Vector2.ZERO, 0.0, Vector2(1.0, 0.5))
			draw_circle(Vector2.ZERO, 42.0 * t, Color(1, 0.25, 0.2, 0.25))
			draw_arc(Vector2.ZERO, 42.0, 0, TAU, 32, Color(1, 0.3, 0.2, 0.8), 2.0)
			draw_circle(Vector2.ZERO, 30.0, Color(0, 0, 0, 0.3 + 0.3 * t))
			draw_set_transform(Vector2.ZERO)
		State.SWIPE_WINDUP:
			var center := Vector2(0, -14)
			draw_arc(center, 40.0, _aim.angle() - 1.1, _aim.angle() + 1.1, 16, Color(1, 0.3, 0.2, 0.8), 3.0)
		State.LASH_WINDUP:
			var start := Vector2(0, -14)
			draw_line(start, start + _aim * lash_length, Color(1, 0.3, 0.2, 0.35), 14.0)
			draw_line(start, start + _aim * lash_length, Color(1, 0.3, 0.2, 0.9), 2.0)
		State.RECOVER:
			var font := ThemeDB.fallback_font
			draw_string_outline(font, Vector2(-14, -100), "winded", HORIZONTAL_ALIGNMENT_LEFT, -1, 8, 3, Color.BLACK)
			draw_string(font, Vector2(-14, -100), "winded", HORIZONTAL_ALIGNMENT_LEFT, -1, 8, Color(1, 0.9, 0.5))
