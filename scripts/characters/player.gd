class_name Player
extends CharacterBody2D
## Top-down 8-directional player: move, dash, sword swing, pistol shot, quick-cast
## spell, and stealth steals (interact next to a rival).
## Going down to 0 HP wakes you in the nearest town. A rival who beat you takes a
## loose/exposed card; monsters make you drop a loose card where you fell.
## Animations are named "<action>_<direction>", e.g. "run_south_east".

signal health_changed(current: int, maximum: int)
signal died

enum State { MOVE, DASH, SWORD, SHOOT, DEAD }

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
## How long the fall lasts before waking in town.
@export var down_time := 1.2
@export_group("Stealth")
@export var steal_cooldown := 1.0

var facing := Vector2.DOWN
var health := 0

var _state := State.MOVE
var _state_time := 0.0
var _dash_cd := 0.0
var _pistol_cd := 0.0
var _dash_dir := Vector2.ZERO
var _steal_cd := 0.0
var _slash := Node2D.new()

@onready var sprite: AnimatedSprite2D = $AnimatedSprite2D
@onready var sword_pivot: Node2D = $SwordPivot
@onready var sword_hitbox: Hitbox = $SwordPivot/SwordHitbox
@onready var sword_shape: CollisionShape2D = $SwordPivot/SwordHitbox/CollisionShape2D
@onready var hurtbox: Hurtbox = $Hurtbox


func _ready() -> void:
	add_to_group(&"player")
	add_to_group(&"collectors")
	health = max_health
	sword_hitbox.damage = sword_damage
	sword_hitbox.source_id = collector_id
	sword_shape.disabled = true
	hurtbox.owner_id = collector_id
	hurtbox.hurt.connect(_on_hurt)
	_slash.z_index = 1
	sword_pivot.add_child(_slash)
	_slash.draw.connect(_draw_slash)
	health_changed.emit(health, max_health)


func _physics_process(delta: float) -> void:
	_state_time += delta
	_dash_cd -= delta
	_pistol_cd -= delta
	_steal_cd -= delta

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
			_slash.queue_redraw()
		State.SHOOT:
			velocity = Vector2.ZERO
			if _state_time >= 0.18:
				_enter(State.MOVE)
		State.DEAD:
			velocity = velocity.move_toward(Vector2.ZERO, 400.0 * delta)

	move_and_slide()
	_update_animation()


func _process_move() -> void:
	if GameState.menus_open > 0:
		velocity = Vector2.ZERO
		return
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
	elif Input.is_action_just_pressed(&"spell"):
		CardSpells.cast_pickpocket(self)
	elif Input.is_action_just_pressed(&"interact") and _steal_cd <= 0.0:
		_try_stealth_steal()


func _try_stealth_steal() -> void:
	var target := stealth_target()
	if target == null:
		return  # Nothing to lift here; interact belongs to whatever else is nearby.
	_steal_cd = steal_cooldown
	var result := Stealth.attempt(self, target)
	if not result.ok and result.reason != "Caught":
		EventBus.notify.emit(result.reason)


## Nearest rival within stealth range, or null.
func stealth_target() -> Node2D:
	for node in CardSpells.collectors_in_range(self, Stealth.STEAL_RANGE):
		if node is Rival:
			return node
	return null


## How loud the player is, for rival awareness: still < running < dashing.
func noise() -> float:
	match _state:
		State.DEAD:
			return 0.0
		State.DASH:
			return 1.8
		State.SWORD:
			return 1.5
	return 1.0 if velocity.length() > 1.0 else 0.4


func _fire_pistol() -> void:
	if projectile_scene == null:
		return
	_pistol_cd = pistol_cooldown
	var shot := projectile_scene.instantiate() as Projectile
	shot.direction = facing
	shot.damage = pistol_damage
	shot.source_id = collector_id
	var zone := Zone.current(get_tree())
	shot.level = zone.level_at(global_position) if zone else -1
	shot.global_position = global_position + Vector2(0, -18) + facing * 10.0
	get_parent().add_child(shot)
	_enter(State.SHOOT)


func _enter(state: State) -> void:
	_state = state
	_state_time = 0.0
	if state != State.SWORD:
		_slash.queue_redraw()


func _on_hurt(hitbox: Hitbox) -> void:
	if _state == State.DEAD:
		return
	health = maxi(health - hitbox.damage, 0)
	health_changed.emit(health, max_health)
	Combat.pop_number(get_parent(), global_position, hitbox.damage, Color(1, 0.45, 0.4))
	velocity = hitbox.global_position.direction_to(global_position) * hitbox.knockback
	if health == 0:
		_die(hitbox.source_id)
		return
	sprite.modulate = Color(1, 0.5, 0.5)
	await _set_invulnerable_for(hurt_invulnerability)
	sprite.modulate = Color.WHITE


## Out of the fight. A rival who beat you takes a loose/exposed card; monsters
## make you drop a loose card where you fell. Either way you wake in the nearest town.
func _die(killer_id: StringName) -> void:
	_enter(State.DEAD)
	died.emit()
	sprite.rotation = PI / 2.0
	sword_shape.set_deferred(&"disabled", true)
	hurtbox.invulnerable = true
	var zone := Zone.current(get_tree())
	var town := WorldMap.nearest_town(zone.scene_file_path if zone else "", position)
	var outcome := ""
	if Combat.is_collector(killer_id):
		var taken := Combat.resolve_defeat(killer_id, collector_id)
		var profile := GameState.rival_profile(killer_id)
		var who := profile.display_name if profile else "rival"
		outcome = "The %s beat you" % who
		if taken != &"":
			outcome += " and took your %s" % CardDatabase.get_card(taken).display_name
	else:
		outcome = "You fainted"
		var dropped := _drop_a_loose_card(zone)
		if dropped != &"":
			outcome += " and dropped %s where you fell" % CardDatabase.get_card(dropped).display_name
		EventBus.player_fainted.emit(dropped)
	GameState.pending_notice = "%s. You woke in %s." % [outcome, WorldMap.town_name(town)]
	var tween := create_tween()
	tween.tween_interval(down_time * 0.4)
	tween.tween_property(sprite, "modulate:a", 0.0, down_time * 0.6)
	tween.tween_callback(_wake_in.bind(town))


## Leaves one random loose card on the ground here (it stays in this zone).
func _drop_a_loose_card(zone: Zone) -> StringName:
	var loose := GameState.stealable_card_ids(collector_id, CardCollection.LOOSE_ONLY)
	if loose.is_empty() or zone == null:
		return &""
	var card_id: StringName = loose.pick_random()
	if not GameState.drop_card(collector_id, card_id):
		return &""
	zone.drop_card(card_id, position)
	return card_id


func _wake_in(town: String) -> void:
	GameState.pending_spawn = WorldMap.town_spawn(town)
	get_tree().change_scene_to_file(town)


func _set_invulnerable_for(seconds: float) -> void:
	hurtbox.invulnerable = true
	await get_tree().create_timer(seconds).timeout
	if _state != State.DASH and is_inside_tree():
		hurtbox.invulnerable = false


## Down players don't grab cards (including the one they just dropped).
func can_pick_up() -> bool:
	return _state != State.DEAD


func heal(amount: int) -> void:
	health = mini(health + amount, max_health)
	health_changed.emit(health, max_health)


func facing_name() -> String:
	return direction_name(facing)


## 8-way animation suffix for a direction vector ("south_east", ...).
static func direction_name(dir: Vector2) -> String:
	return DIRECTIONS[wrapi(roundi(dir.angle() / (PI / 4.0)), 0, 8)]


## Picks "<action>_<dir>" from `frames`, falling back to the nearest cardinal
## direction (for actions only drawn in 4 directions), then to `fallback` actions.
## Returns &"" if nothing fits.
static func pick_animation(frames: SpriteFrames, action: String, dir: Vector2, fallback: Array[String]) -> StringName:
	var name := direction_name(dir)
	var cardinals: Array[String] = [name]
	if "_" in name:
		# Diagonal: try the closer of its two cardinal halves first.
		var halves := name.split("_")
		cardinals.append_array([halves[1], halves[0]] if absf(dir.x) > absf(dir.y) else [halves[0], halves[1]])
	for candidate: String in [action] + fallback:
		for d in cardinals:
			var anim := StringName("%s_%s" % [candidate, d])
			if frames.has_animation(anim):
				return anim
	return &""


func _update_animation() -> void:
	var action := "idle"
	match _state:
		State.MOVE:
			action = "run" if velocity.length() > 1.0 else "idle"
		State.DASH:
			action = "dash"
		State.SWORD:
			action = "sword"
		State.SHOOT:
			action = "pistol"
		State.DEAD:
			action = "idle"
	_play(action)


## Plays "<action>_<facing>", falling back to run/idle while art is missing.
func _play(action: String) -> void:
	if sprite.sprite_frames == null:
		return
	var fallback: Array[String] = ["run" if action == "dash" else "idle", "idle"]
	var anim := pick_animation(sprite.sprite_frames, action, facing, fallback)
	if anim != &"" and sprite.animation != anim:
		sprite.play(anim)


## Sword arc effect while the swing is active.
func _draw_slash() -> void:
	if _state != State.SWORD or _state_time > sword_active_time + 0.05:
		return
	var t := clampf(_state_time / sword_active_time, 0.0, 1.0)
	var sweep := lerpf(-1.1, 1.1, t)
	_slash.draw_arc(Vector2.ZERO, 20.0, -1.1, sweep, 12, Color(1, 1, 0.9, 0.9), 3.0)
	_slash.draw_arc(Vector2.ZERO, 16.0, -1.1, sweep, 12, Color(1, 0.95, 0.7, 0.4), 2.0)
