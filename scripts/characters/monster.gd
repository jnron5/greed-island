class_name Monster
extends CharacterBody2D
## Regular zone monster: wanders near its spawn, chases the nearest collector
## (player or rival) that comes close, telegraphs and lunges, drops a common
## card on death, and respawns after a cooldown. 4-directional animations:
## "idle_<dir>", "walk_<dir>", "attack_<dir>" with dir in south/east/north/west.
## After dark (TimeOfDay.is_night(), outdoors) every monster turns savage: tougher
## (NIGHT_HEALTH), harder-hitting, quicker to strike, faster and keener-eyed, with a
## red glow about it; and it carries more: a full purse, often food, every other time
## a second card.

enum State { WANDER, CHASE, WINDUP, LUNGE, RECOVER, STAGGER, DEAD }

const DIRECTIONS_4: Array[String] = ["east", "south", "west", "north"]
const NIGHT_HEALTH := 2.0
const NIGHT_DAMAGE := 1
const NIGHT_SPEED := 1.25
const NIGHT_AGGRO := 1.5
## Night beasts wind up quicker (less time to dodge) and recover sooner.
const NIGHT_QUICKNESS := 0.75
const NIGHT_TINT := Color(1.18, 0.82, 0.86)
const NIGHT_FOOD: Array[StringName] = [&"bread", &"smoked_fish", &"healers_tonic"]

@export var sprite_frames: SpriteFrames
@export var max_health := 5
@export var wander_speed := 35.0
@export var chase_speed := 85.0
@export var aggro_radius := 120.0
## Gives up the chase beyond this distance from its spawn point.
@export var leash_radius := 260.0
@export_group("Attack")
@export var attack_range := 34.0
@export var attack_damage := 1
@export var windup_time := 0.45
@export var lunge_speed := 230.0
@export var lunge_time := 0.18
@export var recover_time := 0.7
@export_group("Drops")
@export var drop_card_ids: Array[StringName] = [&"thorn_sprig", &"moss_lantern", &"veyra_reed", &"hollow_acorn"]
@export var pickup_scene: PackedScene = preload("res://scenes/systems/card_pickup.tscn")

var _last_hitter: StringName
@export var respawn_time := 25.0
## Big beasts roar (and the ground shakes) when they notice you.
@export var roar := false

var health := 0
var facing := Vector2.DOWN

var _state := State.WANDER
## Seconds left frozen solid (a Frostfang sword hit): no moving, no attacking.
var _frozen := 0.0
var _state_time := 0.0
var _spawn_point := Vector2.ZERO
var _wander_target := Vector2.ZERO
var _target: Node2D
var _lunge_dir := Vector2.ZERO
var _flash := 0.0
## Savage after dark (outdoors only; caves keep their own dark).
var night := false
var _base := {}
var _night_check := 0.0
var _night_light: PointLight2D

@onready var sprite: AnimatedSprite2D = $AnimatedSprite2D
@onready var body_shape: CollisionShape2D = $CollisionShape2D
@onready var hurtbox: Hurtbox = $Hurtbox
@onready var attack_hitbox: Hitbox = $AttackHitbox
@onready var attack_shape: CollisionShape2D = $AttackHitbox/CollisionShape2D


func _ready() -> void:
	add_to_group(&"monsters")
	if sprite_frames:
		sprite.sprite_frames = sprite_frames
	_spawn_point = global_position
	_wander_target = global_position
	hurtbox.owner_id = Combat.MONSTER
	hurtbox.hurt.connect(_on_hurt)
	attack_hitbox.source_id = Combat.MONSTER
	attack_hitbox.damage = attack_damage
	attack_shape.disabled = true
	_base = { "health": max_health, "damage": attack_damage, "chase": chase_speed, "aggro": aggro_radius,
		"windup": windup_time, "recover": recover_time }
	health = max_health
	_update_night()


## Turns savage at dusk and back at dawn (health scaled with it, so a wounded beast
## stays wounded).
func _update_night() -> void:
	var zone := Zone.current(get_tree()) if is_inside_tree() else null
	var want := TimeOfDay.is_night() and not (zone != null and zone.underground)
	if want == night or _base.is_empty():
		return
	night = want
	var old_max := max_health
	max_health = ceili(_base.health * NIGHT_HEALTH) if night else int(_base.health)
	attack_damage = int(_base.damage) + (NIGHT_DAMAGE if night else 0)
	windup_time = float(_base.windup) * (NIGHT_QUICKNESS if night else 1.0)
	recover_time = float(_base.recover) * (NIGHT_QUICKNESS if night else 1.0)
	chase_speed = float(_base.chase) * (NIGHT_SPEED if night else 1.0)
	aggro_radius = float(_base.aggro) * (NIGHT_AGGRO if night else 1.0)
	attack_hitbox.damage = attack_damage
	if health > 0:
		health = clampi(ceili(float(health) * max_health / old_max), 1, max_health)
	sprite.self_modulate = NIGHT_TINT if night else Color.WHITE
	# A red glow about it that the dark can't swallow (a light, like the lamps).
	if night and _night_light == null:
		_night_light = PointLight2D.new()
		_night_light.texture = LampLight.glow_texture()
		_night_light.color = Color(1.0, 0.22, 0.12)
		_night_light.energy = 1.1
		_night_light.texture_scale = 0.75
		_night_light.position = Vector2(0, -10)
		add_child(_night_light)
	if _night_light:
		_night_light.enabled = night and _state != State.DEAD


func _physics_process(delta: float) -> void:
	_state_time += delta
	_night_check -= delta
	if _night_check <= 0.0:
		_night_check = 2.0
		_update_night()
	if night:
		queue_redraw()
	if _flash > 0.0:
		_flash -= delta
		sprite.modulate = Color(3, 3, 3) if _flash > 0.0 else Color.WHITE
	if _frozen > 0.0 and _state != State.DEAD:
		_frozen -= delta
		velocity = Vector2.ZERO
		sprite.modulate = Color(0.6, 0.85, 1.4) if _frozen > 0.0 else Color.WHITE
		sprite.speed_scale = 0.0 if _frozen > 0.0 else 1.0
		move_and_slide()
		queue_redraw()
		return
	match _state:
		State.WANDER:
			_process_wander()
		State.CHASE:
			_process_chase()
		State.WINDUP:
			velocity = Vector2.ZERO
			# Telegraph: shake in place before the lunge.
			sprite.offset.x = sin(_state_time * 60.0) * 1.0
			if _state_time >= windup_time:
				sprite.offset.x = 0.0
				attack_shape.set_deferred(&"disabled", false)
				_enter(State.LUNGE)
		State.LUNGE:
			velocity = _lunge_dir * lunge_speed
			if _state_time >= lunge_time:
				attack_shape.set_deferred(&"disabled", true)
				_enter(State.RECOVER)
		State.RECOVER, State.STAGGER:
			velocity = velocity.move_toward(Vector2.ZERO, 600.0 * delta)
			var wait := recover_time if _state == State.RECOVER else 0.25
			if _state_time >= wait:
				_enter(State.CHASE if _valid_target(_target) else State.WANDER)
		State.DEAD:
			velocity = Vector2.ZERO
	move_and_slide()
	_update_animation()
	queue_redraw()


func _process_wander() -> void:
	_target = _find_target()
	if _target:
		if roar and _target.is_in_group(&"player"):
			Sfx.play(&"roar")
			Combat.shake(get_tree(), 5.0, 8)
		_enter(State.CHASE)
		return
	if global_position.distance_to(_wander_target) < 4.0 or _state_time > 4.0:
		_wander_target = _spawn_point + Vector2.from_angle(randf() * TAU) * randf_range(10.0, 60.0)
		_state_time = 0.0
	velocity = global_position.direction_to(_wander_target) * wander_speed


func _process_chase() -> void:
	if not _valid_target(_target) or global_position.distance_to(_spawn_point) > leash_radius:
		_target = null
		_wander_target = _spawn_point
		_enter(State.WANDER)
		return
	var dist := global_position.distance_to(_target.global_position)
	if dist <= attack_range:
		_lunge_dir = global_position.direction_to(_target.global_position)
		facing = _lunge_dir
		_enter(State.WINDUP)
		return
	velocity = global_position.direction_to(_target.global_position) * chase_speed


## Nearest collector in aggro range that isn't safe in town.
func _find_target() -> Node2D:
	var best: Node2D = null
	var best_dist := aggro_radius
	for node in get_tree().get_nodes_in_group(&"collectors"):
		var n := node as Node2D
		if not _valid_target(n):
			continue
		var d := global_position.distance_to(n.global_position)
		if d < best_dist:
			best = n
			best_dist = d
	return best


## Untyped on purpose: the target may have been freed (e.g. a rival that left the zone).
func _valid_target(n: Variant) -> bool:
	if not is_instance_valid(n) or not (n is Node2D) or not n.is_inside_tree():
		return false
	var id: Variant = n.get(&"collector_id")
	if not (id is StringName) or GameState.is_in_safe_zone(id):
		return false
	if not Zone.same_level(get_tree(), global_position, n.global_position):
		return false
	return global_position.distance_to(n.global_position) <= aggro_radius * 1.6


func _on_hurt(hitbox: Hitbox) -> void:
	if _state == State.DEAD:
		return
	health -= hitbox.damage
	_last_hitter = hitbox.source_id
	Sfx.play(&"hit")
	_flash = 0.08
	Combat.pop_number(get_parent(), global_position, hitbox.damage)
	velocity = hitbox.global_position.direction_to(global_position) * hitbox.knockback
	# Getting hit draws aggro onto whoever hit us.
	for node in get_tree().get_nodes_in_group(&"collectors"):
		if node.get(&"collector_id") == hitbox.source_id:
			_target = node
	if hitbox.freeze > 0.0 and health > 0:
		_frozen = maxf(_frozen, hitbox.freeze)
		attack_shape.set_deferred(&"disabled", true)
		sprite.offset.x = 0.0
		_enter(State.STAGGER)
	if health <= 0:
		_frozen = 0.0
		sprite.speed_scale = 1.0
		_die()
	elif _state != State.LUNGE:
		attack_shape.set_deferred(&"disabled", true)
		sprite.offset.x = 0.0
		_enter(State.STAGGER)


func _die() -> void:
	_enter(State.DEAD)
	if _night_light:
		_night_light.enabled = false
	attack_shape.set_deferred(&"disabled", true)
	body_shape.set_deferred(&"disabled", true)
	hurtbox.set_deferred(&"monitoring", false)
	EventBus.monster_defeated.emit(StringName(scene_file_path.get_file().get_basename()), _last_hitter)
	# What it leaves on the ground, flung out of the body: its card, often a few
	# coins, now and then something to eat.
	var card: StringName = drop_card_ids.pick_random() if not drop_card_ids.is_empty() else &""
	var gold := randi_range(1, 4) if randf() < 0.6 else 0
	var item: StringName = &"bread" if randf() < 0.08 else &""
	if night:
		# A night beast carries more: a fuller purse, often food, now and then a
		# second card.
		gold = randi_range(8, 18)
		item = NIGHT_FOOD.pick_random() if randf() < 0.45 else &""
		if randf() < 0.5 and not drop_card_ids.is_empty():
			Combat.drop_loot(get_tree(), position, drop_card_ids.pick_random())
	Combat.drop_loot(get_tree(), position, card, gold, item)
	# Down it goes: a white flash, knocked over, a beat on the ground, then it fades.
	var headless := DisplayServer.get_name() == "headless"
	var t := 0.1 if headless else 1.0
	var side := -1.0 if facing.x < 0.0 else 1.0
	sprite.modulate = Color(3, 3, 3)
	var tween := create_tween()
	tween.tween_property(sprite, "modulate", Color(1.0, 0.6, 0.6), 0.15 * t)
	tween.tween_property(sprite, "rotation", side * PI / 2.0, 0.4 * t).set_trans(Tween.TRANS_BOUNCE).set_ease(Tween.EASE_OUT)
	tween.tween_interval(0.6 * t)
	tween.tween_property(sprite, "modulate:a", 0.0, 0.7 * t)
	tween.tween_callback(func() -> void: visible = false)
	get_tree().create_timer(respawn_time).timeout.connect(_respawn)


func _respawn() -> void:
	if not is_inside_tree():
		return
	global_position = _spawn_point
	health = max_health
	visible = true
	sprite.modulate = Color.WHITE
	sprite.rotation = 0.0
	body_shape.set_deferred(&"disabled", false)
	hurtbox.set_deferred(&"monitoring", true)
	_target = null
	_enter(State.WANDER)
	if _night_light:
		_night_light.enabled = night


func _enter(state: State) -> void:
	_state = state
	_state_time = 0.0


func is_dead() -> bool:
	return _state == State.DEAD


func _update_animation() -> void:
	if sprite.sprite_frames == null or _state == State.DEAD:
		return
	if velocity.length() > 1.0 and _state != State.LUNGE:
		facing = velocity.normalized()
	var dir := DIRECTIONS_4[wrapi(roundi(facing.angle() / (PI / 2.0)), 0, 4)]
	var action := "walk"
	match _state:
		State.WINDUP, State.LUNGE:
			action = "attack"
		_:
			action = "walk" if velocity.length() > 1.0 else "idle"
	for candidate in [action, "walk", "idle"]:
		var anim := StringName("%s_%s" % [candidate, dir])
		if sprite.sprite_frames.has_animation(anim):
			if sprite.animation != anim:
				sprite.play(anim)
			return


func _draw() -> void:
	if _state == State.DEAD:
		return
	if night:
		# A savage red glow about its feet.
		var pulse := 0.5 + 0.5 * sin(Time.get_ticks_msec() / 260.0)
		# (bright and warm, so the night grade leaves it its colour)
		draw_set_transform(Vector2(0, 2), 0.0, Vector2(1.0, 0.45))
		draw_circle(Vector2.ZERO, 18.0, Color(1.0, 0.25, 0.1, 0.22 + 0.12 * pulse))
		draw_arc(Vector2.ZERO, 18.0, 0.0, TAU, 28, Color(1.0, 0.45, 0.2, 0.75 + 0.25 * pulse), 2.0)
		draw_set_transform(Vector2.ZERO)
	if _state == State.WINDUP:
		# Red warning ring where the lunge will land.
		draw_arc(_lunge_dir * attack_range * 0.8, 10.0, 0, TAU, 16, Color(1, 0.3, 0.2, 0.7), 1.5)
	if health < max_health:
		draw_rect(Rect2(-10, -40, 20, 3), Color(0, 0, 0, 0.6))
		draw_rect(Rect2(-9, -39, 18.0 * health / max_health, 1), Color(0.9, 0.3, 0.25))
