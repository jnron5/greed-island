class_name RimeStag
extends Boss
## The Starfall Range's boss: an icy stag on the high snowfield under the pass.
## It never hides like the Warden; it fights in the open. Loop:
##   DORMANT       stands at its lair; wakes when a collector comes close
##   CANOPY        (stalking) circles its target at a distance, head low
##   LASH_WINDUP   paws the snow; a line shows where it will charge
##   LASH          (charging) gallops down that line; the antlers hit hard
##   RECOVER       skids to a stop, winded: the best time to strike
##   SWIPE_WINDUP / SWIPE   an antler sweep when you crowd it
##   DROP / SLAM   (enraged only) rears up, stamps: a ring of ice shards flies out
## Reuses the Boss machinery (target, bar, damage, drops, kill cap, respawns);
## the scene's LashHitbox rides on its chest while it charges.

const SHARDS := 10

@export var stalk_time := 1.6
@export var stalk_distance := 130.0
@export var stalk_speed := 70.0
@export var charge_windup := 0.8
@export var charge_speed := 340.0
@export var charge_length := 300.0
@export var rear_time := 0.8
@export var shard_damage := 1

var _charged := 0.0
var _circle := 1.0
var _charges := 0
var _projectile: PackedScene = preload("res://scenes/systems/projectile.tscn")


func _physics_process(delta: float) -> void:
	_state_time += delta
	if _flash > 0.0:
		_flash -= delta
		sprite.modulate = Color(3, 3, 3) if _flash > 0.0 else Color.WHITE
	var rate := 0.75 if enraged() else 1.0
	if _state not in [State.DORMANT, State.DEAD]:
		_track(delta)

	match _state:
		State.DORMANT:
			velocity = Vector2.ZERO
			_target = _find_target(wake_radius)
			if _target:
				EventBus.notify.emit("The air goes still and cold... the %s!" % _display_name())
				_show_bar(true)
				_enter(State.CANOPY)
		State.CANOPY:
			if _target == null:
				velocity = Vector2.ZERO
			else:
				var to := _target.global_position - global_position
				var d := to.length()
				var dir := to / maxf(d, 1.0)
				var side := dir.orthogonal() * _circle
				var push := (d - stalk_distance) / 60.0
				velocity = (side + dir * clampf(push, -1.0, 1.0)).normalized() * stalk_speed
				facing = dir
				if d < 50.0:
					_aim = dir
					velocity = Vector2.ZERO
					_enter(State.SWIPE_WINDUP)
				elif _state_time >= stalk_time * rate:
					velocity = Vector2.ZERO
					_aim = dir
					facing = dir
					if enraged() and _charges >= 2:
						_charges = 0
						_enter(State.DROP)
					else:
						_enter(State.LASH_WINDUP)
		State.LASH_WINDUP:
			velocity = Vector2.ZERO
			if _target and _state_time < charge_windup * rate * 0.6:
				_aim = global_position.direction_to(_target.global_position)   # tracks you, then locks
				facing = _aim
			if _state_time >= charge_windup * rate:
				lash_hitbox.rotation = _aim.angle()
				lash_hitbox.position = _aim * 20.0 + Vector2(0, -20)
				lash_shape.position = Vector2.ZERO
				lash_shape.set_deferred(&"disabled", false)
				_charged = 0.0
				_charges += 1
				_enter(State.LASH)
		State.LASH:
			velocity = _aim * charge_speed
			_charged += charge_speed * delta
			if _charged >= charge_length or (_state_time > 0.1 and get_slide_collision_count() > 0):
				lash_shape.set_deferred(&"disabled", true)
				velocity = Vector2.ZERO
				if get_slide_collision_count() > 0:
					_shake_camera(5.0)
				_circle = -_circle
				_enter(State.RECOVER)
		State.SWIPE_WINDUP:
			velocity = Vector2.ZERO
			if _state_time >= swipe_windup * rate:
				swipe_hitbox.position = _aim * 28.0 + Vector2(0, -16)
				swipe_shape.set_deferred(&"disabled", false)
				_enter(State.SWIPE)
		State.SWIPE:
			velocity = Vector2.ZERO
			if _state_time >= 0.18:
				swipe_shape.set_deferred(&"disabled", true)
				_enter(State.CANOPY)
		State.DROP:
			velocity = Vector2.ZERO
			if _state_time >= rear_time * rate:
				slam_shape.set_deferred(&"disabled", false)
				_shake_camera(6.0)
				_throw_shards()
				_enter(State.SLAM)
		State.SLAM:
			if _state_time >= 0.15:
				slam_shape.set_deferred(&"disabled", true)
				_enter(State.RECOVER)
		State.RECOVER:
			velocity = velocity.move_toward(Vector2.ZERO, 900.0 * delta)
			if _state_time >= recover_time:
				_enter(State.CANOPY)
		State.DEAD, State.CLIMB, State.GROUNDED, State.SWIPE, State.LASH_WINDUP:
			velocity = Vector2.ZERO

	move_and_slide()
	_update_animation()
	queue_redraw()


## Like Boss._track_target, but it goes back to its lair (not the canopy) when
## everyone has left.
func _track(delta: float) -> void:
	if not _valid_target(_target, arena_radius):
		_target = _find_target(arena_radius)
	if _target:
		_alone_time = 0.0
		return
	_alone_time += delta
	if _alone_time > 4.0 and _state in [State.CANOPY, State.RECOVER]:
		health = max_health
		_show_bar(false)
		global_position = _lair
		_enter(State.DORMANT)


func is_vulnerable() -> bool:
	return _state not in [State.DORMANT, State.DEAD]


## Took a hit while winded: it hurts more (the opening the fight is built round).
func _on_hurt(hitbox: Hitbox) -> void:
	if _state == State.DORMANT:
		return
	super._on_hurt(hitbox)
	if _state == State.RECOVER and health > 0 and hitbox.damage > 0:
		health = maxi(health - 1, 1)
		_show_bar(true)


## The stag never hides: "back in the canopy" is just standing at its lair.
func _hide_in_canopy() -> void:
	sprite.visible = true
	sprite.modulate.a = 1.0
	sprite.position = Vector2.ZERO
	body_shape.set_deferred(&"disabled", false)
	hurtbox.set_deferred(&"monitoring", true)


func _throw_shards() -> void:
	var zone := Zone.current(get_tree())
	for i in SHARDS:
		var shard: Projectile = _projectile.instantiate()
		shard.collision_layer = 128
		shard.direction = Vector2.from_angle(TAU * i / SHARDS + _state_time)
		shard.damage = shard_damage
		shard.source_id = Combat.MONSTER
		shard.speed = 170.0
		shard.lifetime = 1.4
		shard.ice = true
		shard.level = zone.level_at(global_position) if zone else -1
		shard.global_position = global_position + Vector2(0, -16) + shard.direction * 20.0
		get_parent().add_child(shard)


func _update_animation() -> void:
	if sprite.sprite_frames == null:
		return
	if velocity.length() > 1.0 and _state != State.RECOVER:
		facing = velocity.normalized()
	var dir := DIRECTIONS_4[wrapi(roundi(facing.angle() / (PI / 2.0)), 0, 4)]
	var action := "idle"
	match _state:
		State.LASH:
			action = "run"
		State.CANOPY:
			action = "walk" if velocity.length() > 1.0 else "idle"
		State.SWIPE_WINDUP, State.SWIPE, State.DROP, State.SLAM:
			action = "attack"
	sprite.speed_scale = 1.6 if _state == State.LASH else 1.0
	for candidate in [action, "walk", "idle"]:
		var anim := StringName("%s_%s" % [candidate, dir])
		if sprite.sprite_frames.has_animation(anim):
			if sprite.animation != anim:
				sprite.play(anim)
			return


func _draw() -> void:
	match _state:
		State.LASH_WINDUP:
			var start := Vector2(0, -10)
			var t := clampf(_state_time / (charge_windup * (0.75 if enraged() else 1.0)), 0.0, 1.0)
			draw_line(start, start + _aim * charge_length, Color(0.6, 0.85, 1.0, 0.25), 26.0)
			draw_line(start, start + _aim * charge_length * t, Color(0.75, 0.92, 1.0, 0.9), 2.0)
		State.SWIPE_WINDUP:
			draw_arc(Vector2(0, -16), 44.0, _aim.angle() - 1.1, _aim.angle() + 1.1, 16, Color(0.6, 0.85, 1.0, 0.9), 3.0)
		State.DROP:
			var t := clampf(_state_time / (rear_time * (0.75 if enraged() else 1.0)), 0.0, 1.0)
			draw_set_transform(Vector2.ZERO, 0.0, Vector2(1.0, 0.5))
			draw_circle(Vector2.ZERO, 46.0 * t, Color(0.6, 0.85, 1.0, 0.25))
			draw_arc(Vector2.ZERO, 46.0, 0, TAU, 32, Color(0.7, 0.9, 1.0, 0.9), 2.0)
			draw_set_transform(Vector2.ZERO)
		State.RECOVER:
			var font := ThemeDB.fallback_font
			draw_string_outline(font, Vector2(-14, -96), "winded", HORIZONTAL_ALIGNMENT_LEFT, -1, 8, 3, Color.BLACK)
			draw_string(font, Vector2(-14, -96), "winded", HORIZONTAL_ALIGNMENT_LEFT, -1, 8, Color(0.75, 0.92, 1.0))
