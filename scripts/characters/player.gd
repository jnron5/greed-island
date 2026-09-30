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

## Passive buff cards (worn in the loadout, GameState.equipped).
const HOLLOWPOINT := &"hollowpoint_charm"
const TIDEWALKER := &"tidewalker_anklet"
const MOSSHEART := &"mossheart_charm"
const EMBERBURST := &"emberburst_rounds"
const STONESONG := &"stonesong_charm"
const STONESONG_HEARTS := 2
const CHARGE_TIME := 0.7            # hold the pistol this long for an Emberburst round
const BURST_DAMAGE := 3
const MOSSHEART_CALM := 8.0        # seconds without a hit before it starts
const MOSSHEART_EVERY := 5.0       # then a heart every this many seconds
var _calm_time := 0.0
@export var move_speed := 145.0
@export_group("Dash")
@export var dash_speed := 340.0
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
## Hearts; a Stonesong Charm adds STONESONG_HEARTS while worn.
@export var max_health := 6:
	get:
		return max_health + (STONESONG_HEARTS if GameState.is_equipped(STONESONG) else 0)
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
## Seconds the pistol has been held with Emberburst worn; -1 = not charging.
var _charge := -1.0
var _charge_ring := Node2D.new()
var _dash_dir := Vector2.ZERO
var _steal_cd := 0.0
var _slash := Node2D.new()

@onready var sprite: AnimatedSprite2D = $AnimatedSprite2D
@onready var sword_pivot: Node2D = $SwordPivot
@onready var sword_hitbox: Hitbox = $SwordPivot/SwordHitbox
@onready var sword_shape: CollisionShape2D = $SwordPivot/SwordHitbox/CollisionShape2D
@onready var hurtbox: Hurtbox = $Hurtbox


func _ready() -> void:
	# A faint cool glow round the wanderer after dark (the glyph band), so you can
	# always see yourself on an unlit street.
	var glow := LampLight.new()
	glow.max_energy = 0.55
	glow.tint = Color(0.75, 0.85, 1.0)
	glow.flicker = 0.0
	glow.texture_scale = 0.55
	glow.position = Vector2(0, -10)
	add_child(glow)
	add_to_group(&"player")
	add_to_group(&"collectors")
	health = max_health
	EventBus.loadout_changed.connect(func() -> void:
		health = mini(health, max_health)
		health_changed.emit(health, max_health))
	sword_hitbox.damage = sword_damage
	sword_hitbox.source_id = collector_id
	sword_shape.disabled = true
	hurtbox.owner_id = collector_id
	hurtbox.hurt.connect(_on_hurt)
	_slash.z_index = 1
	sword_pivot.add_child(_slash)
	_slash.draw.connect(_draw_slash)
	_charge_ring.z_index = 2
	_charge_ring.position = Vector2(0, -12)
	add_child(_charge_ring)
	_charge_ring.draw.connect(_draw_charge)
	# A blow that lands kicks the camera and stops the world for a heartbeat.
	for hitbox: Hitbox in find_children("*", "Hitbox", true, false):
		hitbox.hit_landed.connect(func(_h: Hurtbox) -> void:
			Combat.shake(get_tree(), 2.0, 3)
			Combat.hit_stop(get_tree(), 0.04))
	health_changed.emit(health, max_health)


func _physics_process(delta: float) -> void:
	_state_time += delta
	_dash_cd -= delta
	_pistol_cd -= delta
	_steal_cd -= delta
	_mossheart(delta)

	match _state:
		State.MOVE:
			_process_move()
		State.DASH:
			velocity = _dash_dir * dash_speed
			_leave_afterimage()
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
	if _charge >= 0.0:
		_process_charge(input)
		return
	if input != Vector2.ZERO:
		facing = input.normalized()

	if Input.is_action_just_pressed(&"dash") and _dash_cd <= 0.0:
		_dash_dir = facing if input == Vector2.ZERO else input.normalized()
		_dash_cd = dash_cooldown * (0.5 if GameState.is_equipped(TIDEWALKER) else 1.0)
		hurtbox.invulnerable = true
		_enter(State.DASH)
		Sfx.play(&"dash")
	elif Input.is_action_just_pressed(&"sword"):
		sword_pivot.rotation = facing.angle()
		sword_shape.set_deferred(&"disabled", false)
		_enter(State.SWORD)
		Sfx.play(&"sword")
	elif Input.is_action_just_pressed(&"pistol") and _pistol_cd <= 0.0:
		if GameState.is_equipped(EMBERBURST):
			_charge = 0.0  # fires on release: a tap is a normal shot, a hold a burst
		else:
			_fire_pistol()
	elif Input.is_action_just_pressed(&"spell"):
		CardSpells.cast_pickpocket(self)
	elif Input.is_action_just_pressed(&"quick_heal"):
		if Items.quick_heal() == null:
			EventBus.notify.emit("Nothing to heal with." if health < max_health else "You're at full health.")
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


## Emberburst: aim while holding (half speed), release to fire. Held long enough,
## the round bursts where it lands; let go early and it's an ordinary shot.
func _process_charge(input: Vector2) -> void:
	velocity *= 0.5
	_charge += get_physics_process_delta_time()
	_charge_ring.queue_redraw()
	if _charge >= CHARGE_TIME and _charge - get_physics_process_delta_time() < CHARGE_TIME:
		Sfx.play(&"charged")
	if not GameState.is_equipped(EMBERBURST):
		_charge = -1.0
	elif not Input.is_action_pressed(&"pistol"):
		var full := _charge >= CHARGE_TIME
		_charge = -1.0
		_charge_ring.queue_redraw()
		_fire_pistol(full)
	elif Input.is_action_just_pressed(&"dash"):
		_charge = -1.0  # dodging lets the charge go
		_charge_ring.queue_redraw()
	if input != Vector2.ZERO:
		facing = input.normalized()


func _draw_charge() -> void:
	if _charge < 0.0:
		return
	var t := minf(_charge / CHARGE_TIME, 1.0)
	var full := t >= 1.0
	var col := Color(1.0, 0.85, 0.4, 0.9) if full else Color(1.0, 0.6, 0.25, 0.6)
	_charge_ring.draw_arc(Vector2.ZERO, 14.0, -PI / 2, -PI / 2 + TAU * t, 24, col, 1.5)
	if full:
		var pulse := 0.5 + 0.5 * sin(_charge * 18.0)
		_charge_ring.draw_circle(facing * 12.0, 2.5 + pulse, Color(1.0, 0.8, 0.4, 0.8))


func _fire_pistol(burst := false) -> void:
	if projectile_scene == null:
		return
	_pistol_cd = pistol_cooldown * (2.0 if burst else 1.0)
	Sfx.play(&"pistol")
	var shot := projectile_scene.instantiate() as Projectile
	shot.direction = facing
	shot.damage = pistol_damage + (1 if GameState.is_equipped(HOLLOWPOINT) else 0)
	shot.explosive = burst
	shot.burst_damage = BURST_DAMAGE
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
	_calm_time = 0.0
	health_changed.emit(health, max_health)
	Combat.pop_number(get_parent(), global_position, hitbox.damage, Color(1, 0.45, 0.4))
	velocity = hitbox.global_position.direction_to(global_position) * hitbox.knockback
	if health == 0:
		_die(hitbox.source_id)
		return
	sprite.modulate = Color(1, 0.5, 0.5)
	Combat.shake(get_tree(), 4.0)
	Sfx.play(&"hurt")
	Combat.hit_stop(get_tree(), 0.07)
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
	Transition.go(town)


func _set_invulnerable_for(seconds: float) -> void:
	hurtbox.invulnerable = true
	await get_tree().create_timer(seconds).timeout
	if _state != State.DASH and is_inside_tree():
		hurtbox.invulnerable = false


## Down players don't grab cards (including the one they just dropped).
func can_pick_up() -> bool:
	return _state != State.DEAD


## Mossheart Charm: out of danger for a while, one heart grows back every few seconds.
func _mossheart(delta: float) -> void:
	_calm_time += delta
	if not GameState.is_equipped(MOSSHEART) or health >= max_health or _state == State.DEAD:
		return
	if _calm_time >= MOSSHEART_CALM:
		_calm_time = MOSSHEART_CALM - MOSSHEART_EVERY
		heal(1)


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


## Soft footsteps while running, two alternating sounds.
var _step_time := 0.0
var _step_k := 0


func _footsteps(delta: float) -> void:
	if _state != State.MOVE or velocity.length() < 10.0:
		_step_time = 0.0
		return
	_step_time -= delta
	if _step_time <= 0.0:
		_step_time = 0.27
		_step_k = 1 - _step_k
		Sfx.play(&"step1" if _step_k == 0 else &"step2", -4.0, 0.12)


func _update_animation() -> void:
	_footsteps(get_physics_process_delta_time())
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
	# The run cycle was drawn for a 110 px/s stride: keep the feet in step at other speeds.
	sprite.speed_scale = move_speed / 110.0 if action == "run" else 1.0
	if anim != &"" and sprite.animation != anim:
		sprite.play(anim)


## Sword arc effect while the swing is active.
func _draw_slash() -> void:
	if _state != State.SWORD or _state_time > sword_active_time + 0.05:
		return
	var t := clampf(_state_time / sword_active_time, 0.0, 1.0)
	var sweep := lerpf(-1.1, 1.1, t)
	# The sword animation draws its own swing; this is just a faint reach marker.
	_slash.draw_arc(Vector2.ZERO, 20.0, -1.1, sweep, 12, Color(1, 1, 0.9, 0.25), 2.0)


## A fading copy of the current frame left behind while dashing (every other physics
## frame), tinted like the cloak's wind, so the dash reads as a burst of speed.
func _leave_afterimage() -> void:
	if Engine.get_physics_frames() % 2 or DisplayServer.get_name() == "headless":
		return
	var ghost := Sprite2D.new()
	ghost.texture = sprite.sprite_frames.get_frame_texture(sprite.animation, sprite.frame)
	ghost.global_position = sprite.global_position
	ghost.offset = sprite.offset
	ghost.scale = sprite.scale
	ghost.flip_h = sprite.flip_h
	ghost.modulate = Color(1.0, 0.85, 0.6, 0.45)
	ghost.z_index = -1
	get_parent().add_child(ghost)
	var tween := ghost.create_tween()
	tween.tween_property(ghost, "modulate:a", 0.0, 0.22)
	tween.tween_callback(ghost.queue_free)
