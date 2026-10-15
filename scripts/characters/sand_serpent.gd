class_name SandSerpent
extends Boss
## The Siroth Dunes' boss: Hollowmaw, a horned sand serpent that lives under the Bone
## Hollow, beside the skeleton of its mate. It hunts from under the sand. Loop:
##   DORMANT       buried at its lair, the sand slowly turning over it
##   CANOPY        (burrowing) out of reach under the sand: a moving mound and a
##                 wake of thrown sand slide after its target
##   DROP          stops under its target; the sand caves in a marked ring
##   SLAM          bursts up out of the sand (area damage); enraged, a ring of sand
##                 spines flies out as well
##   GROUNDED      reared up and turning to face its target: bites what's close
##                 (SWIPE), spits a fan of sand at what isn't (LASH), 2x, 3x enraged
##   RECOVER       slumps, its jaw in the sand: open to every blow (they hurt more)
##   CLIMB         sinks back under the sand, and the hunt begins again
## Reuses the Boss machinery (targets, bar, truce, kill cap, gate respawns, death show).

const SPINES := 12

@export var burrow_speed := 125.0
@export var burrow_time := 2.0
@export var spit_count := 5
@export var spit_speed := 190.0
@export var spit_damage := 1

## Where the mound has been lately (for the wake of thrown sand).
var _trail: Array[Vector2] = []
var _trail_time := 0.0
## 0..1: how far it has risen out of the sand (the sprite squashes into the ground).
var _rise := 0.0
var _projectile: PackedScene = preload("res://scenes/systems/projectile.tscn")


func _physics_process(delta: float) -> void:
	_state_time += delta
	if _flash > 0.0:
		_flash -= delta
		sprite.modulate = Color(3, 3, 3) if _flash > 0.0 else _tint()
	elif _state != State.DEAD:
		sprite.modulate = _tint()
	var rate := 0.75 if enraged() else 1.0
	if _state not in [State.DORMANT, State.DEAD]:
		_track(delta)
	_trail_time -= delta
	if _trail_time <= 0.0:
		_trail_time = 0.08
		_trail.push_front(global_position)
		if _trail.size() > 12:
			_trail.pop_back()

	match _state:
		State.DORMANT:
			velocity = Vector2.ZERO
			_target = _find_target(wake_radius)
			if _target:
				EventBus.notify.emit("The sand of the Bone Hollow heaves... %s!" % _display_name())
				_shake_camera(5.0)
				_show_bar(true)
				_enter(State.CANOPY)
		State.CANOPY:
			if _target == null:
				velocity = Vector2.ZERO
			else:
				var to := _target.global_position - global_position
				velocity = to.normalized() * burrow_speed if to.length() > 6.0 else Vector2.ZERO
				# Never leaves its hollow, nor tunnels up into the mesas round it.
				var next := global_position + velocity * delta * 6.0
				var zone := Zone.current(get_tree())
				if next.distance_to(_lair) > arena_radius * 0.8 \
						or (zone and zone.level_at(next) != zone.level_at(_lair)):
					velocity = Vector2.ZERO
				if _state_time >= burrow_time * rate:
					velocity = Vector2.ZERO
					_enter(State.DROP)
		State.DROP:
			velocity = Vector2.ZERO
			if _state_time >= drop_time * rate:
				_land()
		State.SLAM:
			velocity = Vector2.ZERO
			if _state_time >= 0.15:
				slam_shape.set_deferred(&"disabled", true)
				_attacks_left = 3 if enraged() else 2
				_enter(State.GROUNDED)
		State.GROUNDED:
			velocity = Vector2.ZERO
			if _target:
				facing = global_position.direction_to(_target.global_position)
			if _state_time >= 0.55 * rate and _target:
				_aim = global_position.direction_to(_target.global_position)
				facing = _aim
				var close := global_position.distance_to(_target.global_position) < 76.0
				_enter(State.SWIPE_WINDUP if close else State.LASH_WINDUP)
		State.SWIPE_WINDUP:
			velocity = Vector2.ZERO
			if _state_time >= swipe_windup * rate:
				swipe_hitbox.position = _aim * 40.0 + Vector2(0, -20)
				swipe_shape.set_deferred(&"disabled", false)
				_enter(State.SWIPE)
		State.LASH_WINDUP:
			velocity = Vector2.ZERO
			if _target and _state_time < lash_windup * rate * 0.6:
				_aim = global_position.direction_to(_target.global_position)   # tracks you, then locks
				facing = _aim
			if _state_time >= lash_windup * rate:
				_spit()
				_enter(State.LASH)
		State.SWIPE, State.LASH:
			velocity = Vector2.ZERO
			if _state_time >= 0.25:
				swipe_shape.set_deferred(&"disabled", true)
				_attacks_left -= 1
				_enter(State.GROUNDED if _attacks_left > 0 else State.RECOVER)
		State.RECOVER:
			velocity = Vector2.ZERO
			if _state_time >= recover_time:
				_climb()
		_:
			velocity = Vector2.ZERO

	move_and_slide()
	_update_animation()
	queue_redraw()


## Like Boss._track_target, but it goes back under its lair when everyone has left.
func _track(delta: float) -> void:
	if not _valid_target(_target, arena_radius):
		_target = _find_target(arena_radius)
	if _target:
		_alone_time = 0.0
		return
	_alone_time += delta
	if _alone_time > 4.0 and _state in [State.CANOPY, State.GROUNDED, State.RECOVER]:
		health = max_health
		_show_bar(false)
		global_position = _lair
		_hide_in_canopy()
		_enter(State.DORMANT)


## Took a hit while slumped in the sand: it hurts more.
func _on_hurt(hitbox: Hitbox) -> void:
	if not is_vulnerable():
		return
	super._on_hurt(hitbox)
	if _state == State.RECOVER and health > 0 and hitbox.damage > 0:
		health = maxi(health - 1, 1)
		_show_bar(true)


## Bursts up out of the sand where the ring was.
func _land() -> void:
	sprite.visible = true
	sprite.position = Vector2.ZERO
	_rise = 0.0
	var tween := create_tween()
	tween.tween_property(self, "_rise", 1.0, 0.16).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_BACK)
	body_shape.set_deferred(&"disabled", false)
	hurtbox.set_deferred(&"monitoring", true)
	slam_shape.set_deferred(&"disabled", false)
	_shake_camera(7.0)
	Sfx.play(&"roar")
	if enraged():
		_throw_spines()
	_enter(State.SLAM)


## Sinks back under the sand.
func _climb() -> void:
	_enter(State.CLIMB)
	hurtbox.set_deferred(&"monitoring", false)
	var tween := create_tween()
	tween.tween_property(self, "_rise", 0.0, 0.5).set_ease(Tween.EASE_IN)
	tween.tween_callback(_finish_climb)


func _hide_in_canopy() -> void:
	_rise = 0.0
	sprite.visible = false
	sprite.position = Vector2.ZERO
	body_shape.set_deferred(&"disabled", true)
	hurtbox.set_deferred(&"monitoring", false)


func _spit() -> void:
	var zone := Zone.current(get_tree())
	var n := spit_count + (2 if enraged() else 0)
	var spread := 0.9
	for i in n:
		var a := _aim.angle() + spread * (float(i) / (n - 1) - 0.5)
		_shoot(Vector2.from_angle(a), spit_speed, 1.3, zone)


func _throw_spines() -> void:
	var zone := Zone.current(get_tree())
	for i in SPINES:
		_shoot(Vector2.from_angle(TAU * i / SPINES + _state_time), 160.0, 1.2, zone)


func _shoot(dir: Vector2, speed: float, life: float, zone: Zone) -> void:
	var shot: Projectile = _projectile.instantiate()
	shot.collision_layer = 128
	shot.direction = dir
	shot.damage = spit_damage
	shot.source_id = Combat.MONSTER
	shot.speed = speed
	shot.lifetime = life
	shot.sand = true
	shot.level = zone.level_at(global_position) if zone else -1
	shot.global_position = global_position + Vector2(0, -30) + dir * 26.0
	get_parent().add_child(shot)


func _tint() -> Color:
	# Slumped and winded: its scales dull.
	return Color(0.85, 0.82, 0.78) if _state == State.RECOVER else Color.WHITE


func _process(delta: float) -> void:
	super._process(delta)
	# Rising out of the sand / sinking back in: squashed into the ground at its base.
	if _state != State.DEAD:
		sprite.scale = Vector2(_base_scale.x, _base_scale.y * maxf(_rise, 0.02))
		sprite.visible = _rise > 0.02


func _update_animation() -> void:
	if sprite.sprite_frames == null or not sprite.visible:
		return
	var dir := DIRECTIONS_4[wrapi(roundi(facing.angle() / (PI / 2.0)), 0, 4)]
	var action := "idle"
	match _state:
		State.SWIPE_WINDUP, State.SWIPE, State.LASH_WINDUP, State.LASH, State.SLAM:
			action = "attack"
	for candidate in [action, "idle"]:
		var anim := StringName("%s_%s" % [candidate, dir])
		if sprite.sprite_frames.has_animation(anim):
			if sprite.animation != anim:
				sprite.play(anim)
			return


func _draw() -> void:
	var sand := Color(0.78, 0.6, 0.36)
	match _state:
		State.DORMANT:
			# The sand slowly turning over where it sleeps.
			var t := Time.get_ticks_msec() / 1000.0
			draw_set_transform(Vector2.ZERO, 0.0, Vector2(1.0, 0.45))
			for i in 3:
				var r := 18.0 + fmod(t * 6.0 + i * 12.0, 36.0)
				draw_arc(Vector2.ZERO, r, 0, TAU, 28, Color(sand, 0.5 * (1.0 - r / 54.0)), 2.0)
			draw_set_transform(Vector2.ZERO)
		State.CANOPY:
			# The wake: thrown sand along the way it came, and the mound over it.
			for k in _trail.size():
				var p := to_local(_trail[k])
				var fade := 1.0 - float(k) / _trail.size()
				draw_set_transform(p, 0.0, Vector2(1.0, 0.5))
				draw_circle(Vector2.ZERO, 14.0 * fade + 4.0, Color(sand.darkened(0.25), 0.35 * fade))
				draw_set_transform(Vector2.ZERO)
			draw_set_transform(Vector2.ZERO, 0.0, Vector2(1.0, 0.5))
			draw_circle(Vector2.ZERO, 26.0, Color(sand.darkened(0.3), 0.55))
			draw_circle(Vector2(0, -6), 18.0, Color(sand.lightened(0.15), 0.85))
			draw_set_transform(Vector2.ZERO)
			var wob := sin(Time.get_ticks_msec() / 60.0)
			for i in 5:
				var a := TAU * i / 5.0 + wob * 0.3
				draw_circle(Vector2(cos(a) * 20.0, sin(a) * 9.0 - 6.0 - absf(wob) * 4.0), 2.0, Color(sand.lightened(0.3), 0.9))
		State.DROP:
			# The sand caves in: a marked ring where it will burst up.
			var t := clampf(_state_time / (drop_time * (0.75 if enraged() else 1.0)), 0.0, 1.0)
			draw_set_transform(Vector2.ZERO, 0.0, Vector2(1.0, 0.5))
			draw_circle(Vector2.ZERO, 44.0, Color(sand.darkened(0.4), 0.25 + 0.35 * t))
			draw_circle(Vector2.ZERO, 44.0 * t, Color(1, 0.4, 0.2, 0.25))
			draw_arc(Vector2.ZERO, 44.0, 0, TAU, 32, Color(1, 0.45, 0.25, 0.9), 2.0)
			draw_set_transform(Vector2.ZERO)
		State.SLAM, State.GROUNDED, State.SWIPE_WINDUP, State.SWIPE, State.LASH_WINDUP, State.LASH, State.RECOVER, State.CLIMB:
			# The churned sand round its body.
			draw_set_transform(Vector2.ZERO, 0.0, Vector2(1.0, 0.45))
			draw_circle(Vector2.ZERO, 30.0, Color(sand.darkened(0.35), 0.45))
			draw_arc(Vector2.ZERO, 30.0, 0, TAU, 24, Color(sand.lightened(0.2), 0.7), 2.0)
			draw_set_transform(Vector2.ZERO)
			if _state == State.SWIPE_WINDUP:
				draw_arc(Vector2(0, -20), 52.0, _aim.angle() - 0.9, _aim.angle() + 0.9, 16, Color(1, 0.4, 0.2, 0.85), 3.0)
			elif _state == State.LASH_WINDUP:
				var start := Vector2(0, -30)
				for s in [-0.45, 0.0, 0.45]:
					draw_line(start, start + Vector2.from_angle(_aim.angle() + s) * 120.0, Color(1, 0.45, 0.2, 0.35), 3.0)
			elif _state == State.RECOVER:
				var font := ThemeDB.fallback_font
				draw_string_outline(font, Vector2(-14, -110), "winded", HORIZONTAL_ALIGNMENT_LEFT, -1, 8, 3, Color.BLACK)
				draw_string(font, Vector2(-14, -110), "winded", HORIZONTAL_ALIGNMENT_LEFT, -1, 8, Color(1, 0.85, 0.5))
