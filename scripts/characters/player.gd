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
const FROSTFANG := &"frostfang_charm"
const FROSTFANG_FREEZE := 1.2      # seconds a sword hit freezes a monster
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
var health := 0:
	set(value):
		health = value
		if is_inside_tree():
			GameState.player_health = value

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
## The sword and pistol, drawn in code over the body animation: one sprite each,
## swung and aimed to the exact facing, so they look the same in all 8 directions
## (PixelLab couldn't keep a weapon consistent frame to frame). The slash trail and
## muzzle flash are drawn here too.
var _gear := Node2D.new()
var _swing_side := 1.0
const SWORD_TEX := preload("res://assets/sprites/player/fx/sword_h.png")
const PISTOL_TEX := preload("res://assets/sprites/player/fx/pistol.png")
const SLASH_TEX := preload("res://assets/sprites/player/fx/slash.png")
const FLASH_TEX := preload("res://assets/sprites/player/fx/flash.png")
## Hand height on the cloak, and how far the weapon sits out from the body.
const HAND := Vector2(0, -21)
## How far out to the side the weapon hand is held.
const HAND_REACH := 9.0
## The sword art's own tilt (its blade points this far up), and where its grip is.
const SWORD_TILT := 0.42
const SWORD_GRIP := Vector2(-6, -17)
## Weapon art is drawn a little smaller than its file, to suit the 85%-scale cloak.
const SWORD_SCALE := 0.65
const PISTOL_SCALE := 0.8

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
	health = max_health if GameState.player_health < 0 else clampi(GameState.player_health, 1, max_health)
	EventBus.loadout_changed.connect(func() -> void:
		health = mini(health, max_health)
		health_changed.emit(health, max_health)
		sword_hitbox.freeze = FROSTFANG_FREEZE if GameState.is_equipped(FROSTFANG) else 0.0)
	sword_hitbox.freeze = FROSTFANG_FREEZE if GameState.is_equipped(FROSTFANG) else 0.0
	sword_hitbox.damage = sword_damage
	sword_hitbox.source_id = collector_id
	sword_shape.disabled = true
	hurtbox.owner_id = collector_id
	hurtbox.hurt.connect(_on_hurt)
	_slash.z_index = 1
	sword_pivot.add_child(_slash)
	_slash.draw.connect(_draw_slash)
	_gear.position = HAND
	add_child(_gear)
	_gear.draw.connect(_draw_gear)
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
	if GameState.waking:
		GameState.waking = false
		_wake_up.call_deferred()


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
	if _state in [State.SWORD, State.SHOOT] or _charge >= 0.0 or _gear_was_drawn:
		_gear.queue_redraw()


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
		_swing_side = -_swing_side   # alternate forehand and backhand cuts
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


## Out of the fight, to a rival or a monster alike: you drop one card where you
## fell (anyone can pick it up, the winner included), the world slows, you crumple,
## the screen fades to white, and you come round at the inn of the nearest town.
func _die(killer_id: StringName) -> void:
	_enter(State.DEAD)
	died.emit()
	velocity = Vector2.ZERO
	_charge = -1.0
	sword_shape.set_deferred(&"disabled", true)
	hurtbox.invulnerable = true
	var zone := Zone.current(get_tree())
	var town := WorldMap.nearest_town(zone.scene_file_path if zone else "", position)
	var lost := Combat.resolve_defeat(killer_id, collector_id, get_tree(), position)
	var outcome := "You fainted"
	if Combat.is_collector(killer_id):
		var profile := GameState.rival_profile(killer_id)
		outcome = "The %s beat you" % (profile.display_name if profile else "rival")
	else:
		EventBus.player_fainted.emit(lost)
	if lost != &"":
		outcome += " and you dropped your %s where you fell" % CardDatabase.get_card(lost).display_name
	GameState.pending_notice = "%s. You came round in %s." % [outcome, WorldMap.town_name(town)]
	GameState.pending_lost_card = lost
	_death_sequence(town)


## A moment of slow motion, a red flash, the cloak crumpling to the ground while
## the camera leans in, a still beat, then the white fade.
func _death_sequence(town: String) -> void:
	Sfx.play(&"hurt")
	Combat.shake(get_tree(), 5.0, 8)
	var headless := DisplayServer.get_name() == "headless"
	if not headless:
		Engine.time_scale = 0.35
		await get_tree().create_timer(0.7, true, false, true).timeout
		Engine.time_scale = 1.0
	var camera := get_node_or_null(^"Camera2D") as Camera2D
	var t := 0.05 if headless else 1.0
	var tween := create_tween()
	tween.tween_property(sprite, "modulate", Color(1.0, 0.5, 0.45), 0.12 * t)
	tween.tween_property(sprite, "rotation", PI / 2.0, 0.9 * t).set_trans(Tween.TRANS_BOUNCE).set_ease(Tween.EASE_OUT)
	tween.parallel().tween_property(sprite, "modulate", Color(0.65, 0.62, 0.7), 0.9 * t)
	if camera:
		tween.parallel().tween_property(camera, "zoom", camera.zoom * 1.25, 1.6 * t).set_trans(Tween.TRANS_SINE)
	tween.tween_interval(1.2 * t)
	tween.tween_callback(_wake_in.bind(town))


## Comes round at the inn of `town` (or the town itself if it has none).
func _wake_in(town: String) -> void:
	GameState.player_health = -1
	var inn := WorldMap.inn_of(town)
	GameState.waking = true
	if inn != "":
		GameState.pending_spawn = &"door"
		Transition.faint_to(inn)
	else:
		GameState.pending_spawn = WorldMap.town_spawn(town)
		Transition.faint_to(town)


## Lying where the keeper put you, then sitting up and getting to your feet. The
## keeper says welcome back, and the card you lost shows on screen.
func _wake_up() -> void:
	_enter(State.DEAD)
	hurtbox.invulnerable = true
	sprite.rotation = PI / 2.0
	sprite.modulate = Color(0.7, 0.68, 0.78)
	var headless := DisplayServer.get_name() == "headless"
	await get_tree().create_timer(0.05 if headless else 1.6).timeout
	var tween := create_tween()
	tween.tween_property(sprite, "rotation", 0.0, 0.05 if headless else 0.6).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tween.parallel().tween_property(sprite, "modulate", Color.WHITE, 0.05 if headless else 0.6)
	await tween.finished
	_enter(State.MOVE)
	hurtbox.invulnerable = false
	var lost := GameState.pending_lost_card
	GameState.pending_lost_card = &""
	var keeper: Npc = null
	for npc in get_tree().get_nodes_in_group(&"npcs"):
		if npc is Npc and npc.inn_rooms:
			keeper = npc
			break
	if keeper:
		keeper.welcome_back(func() -> void: CardReveal.show_lost(lost))
	else:
		CardReveal.show_lost(lost)


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
	pass   # the swing is drawn by _draw_gear


var _gear_was_drawn := false


## Sword: the blade sweeps through a wide arc in front (alternating sides), a
## crescent of light trailing it, then it's put away. Pistol: drawn and aimed,
## kicked back by the shot with a flash at the muzzle; held out while charging.
## Behind the body when facing away from the camera.
func _draw_gear() -> void:
	_gear_was_drawn = false
	var aim := facing.angle()
	var flip := Vector2(1, -1 if facing.x < -0.01 else 1)
	var hand := _hand_offset()
	# The weapon hand is on the far side of the body when facing away or when the
	# right side is turned from the camera (facing west): drawn behind the cloak.
	_gear.z_index = -1 if facing.y < -0.35 or hand.y < -2.0 else 1
	if _state == State.SWORD:
		var t := clampf(_state_time / (sword_active_time + 0.05), 0.0, 1.0)
		var eased := 1.0 - pow(1.0 - t, 3.0)
		var angle := aim + lerpf(-1.5, 1.5, eased) * _swing_side
		var fade := clampf(1.0 - (_state_time - sword_active_time - 0.04) / sword_recovery, 0.0, 1.0)
		# The arm reaches out into the cut and draws back after it.
		var grip := hand + facing * 4.0 * sin(eased * PI)
		if t > 0.1 and t < 0.95:
			var trail := clampf(1.0 - absf(t - 0.5) * 2.0, 0.0, 1.0)
			_gear.draw_set_transform(grip + Vector2.from_angle(aim) * 10.0, aim + PI, Vector2(0.55, 0.65 * _swing_side))
			var ss := SLASH_TEX.get_size()
			_gear.draw_texture(SLASH_TEX, -ss / 2.0, Color(1, 1, 1, 0.85 * trail))
		# The art's blade points 24 degrees up: level it, mirror it for the backhand,
		# then turn it to the swing angle, held by its grip in the hand.
		var level := Transform2D(SWORD_TILT, Vector2.ZERO)
		var mirror := Transform2D(Vector2(SWORD_SCALE, 0), Vector2(0, SWORD_SCALE * _swing_side * flip.y), Vector2.ZERO)
		_gear.draw_set_transform_matrix(Transform2D(angle, grip) * mirror * level)
		_gear.draw_texture(SWORD_TEX, SWORD_GRIP, Color(1, 1, 1, fade))
		_gear.draw_set_transform(Vector2.ZERO)
		_draw_fist(grip, fade)
		_gear_was_drawn = fade > 0.0
		return
	var aiming := _charge >= 0.0
	if _state == State.SHOOT or aiming:
		var kick := 0.0 if aiming else clampf(1.0 - _state_time / 0.1, 0.0, 1.0) * 3.0
		# Held out at arm's length from the shoulder, pointing where you aim.
		var base := hand + Vector2.from_angle(aim) * (5.0 - kick)
		_gear.draw_set_transform(base, aim, flip * PISTOL_SCALE)
		var ps := PISTOL_TEX.get_size()
		_gear.draw_texture(PISTOL_TEX, Vector2(-4.0, -ps.y / 2.0))
		if not aiming and _state_time < 0.07:
			var fs := FLASH_TEX.get_size()
			_gear.draw_texture_rect(FLASH_TEX, Rect2(Vector2(ps.x - 7.0, -fs.y * 0.45), fs * 0.9), false)
		_gear.draw_set_transform(Vector2.ZERO)
		_draw_fist(base, 1.0)
		_gear_was_drawn = true


## The gloved fist closed round the grip (the cloak hides the arm), so the weapon
## is held, not floating.
func _draw_fist(at: Vector2, alpha: float) -> void:
	if alpha <= 0.0:
		return
	_gear.draw_circle(at, 2.6, Color(0.12, 0.08, 0.06, alpha))
	_gear.draw_circle(at, 1.8, Color(0.42, 0.27, 0.17, alpha))
	_gear.draw_circle(at + Vector2(-0.5, -0.6), 0.8, Color(0.62, 0.44, 0.3, alpha))


## Where the weapon hand is, from the chest: out at the wanderer's right side
## (screen left when facing the camera, nearer the camera when facing east, behind
## the body when facing west), squashed vertically for the top-down view.
func _hand_offset() -> Vector2:
	var right := facing.normalized().rotated(PI / 2.0)
	return Vector2(right.x * HAND_REACH, right.y * HAND_REACH * 0.55 + 2.0)


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
