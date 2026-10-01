class_name CairnColossus
extends Boss
## The Aurewind Plains' boss: a giant of standing stones on Kestrel Rise, the
## crown rune of the circles glowing on its brow. Slow, heavy, and only hurt where
## its stone is open. Loop:
##   DORMANT       a quiet heap of stones; wakes when a collector comes close
##   CANOPY        (lumbering) walks after its target; its armour turns most blows
##   SWIPE_WINDUP / SWIPE   close by: raises its fists and pounds the ground
##   DROP          at range: hurls boulders at marked spots round its target
##   LASH_WINDUP / LASH     sinks into the earth (untouchable) while stone pillars
##                 burst up under its target, one after another
##   RECOVER       surfaces with its rune core glowing and open: hit it now
## Enraged below half health: more boulders and pillars, shorter wind-ups.

const ARMOUR := 0.34   # share of a blow that gets through while it walks

@export var walk_time := 2.0
@export var pound_windup := 0.7
@export var boulder_texture: Texture2D
@export var pillar_texture: Texture2D
## What it looks like asleep: a heap of tumbled stones.
@export var dormant_texture: Texture2D

var _pillars_left := 0
var _pillar_timer := 0.0
var _chip := 0.0


func _physics_process(delta: float) -> void:
	_state_time += delta
	if _flash > 0.0:
		_flash -= delta
		sprite.modulate = Color(3, 3, 3) if _flash > 0.0 else _tint()
	else:
		sprite.modulate = _tint()
	var rate := 0.75 if enraged() else 1.0
	if _state not in [State.DORMANT, State.DEAD]:
		_track(delta)

	match _state:
		State.DORMANT:
			velocity = Vector2.ZERO
			_target = _find_target(wake_radius)
			if _target:
				sprite.visible = true
				EventBus.notify.emit("The stones of Kestrel Rise stand up... the %s!" % _display_name())
				_shake_camera(5.0)
				_show_bar(true)
				_enter(State.CANOPY)
		State.CANOPY:
			if _target == null:
				velocity = Vector2.ZERO
			else:
				var to := _target.global_position - global_position
				facing = to.normalized()
				velocity = facing * ground_speed
				if to.length() < 64.0:
					velocity = Vector2.ZERO
					_aim = facing
					_enter(State.SWIPE_WINDUP)
				elif _state_time >= walk_time * rate:
					velocity = Vector2.ZERO
					_enter(State.LASH_WINDUP if _attacks_left % 2 == 1 else State.DROP)
					_attacks_left += 1
		State.SWIPE_WINDUP:
			velocity = Vector2.ZERO
			if _state_time >= pound_windup * rate:
				slam_shape.set_deferred(&"disabled", false)
				_shake_camera(6.0)
				_enter(State.SWIPE)
		State.SWIPE:
			velocity = Vector2.ZERO
			if _state_time >= 0.18:
				slam_shape.set_deferred(&"disabled", true)
				_enter(State.RECOVER)
		State.DROP:
			velocity = Vector2.ZERO
			if _state_time >= 0.5 * rate:
				_throw_boulders(5 if enraged() else 3)
				_enter(State.CANOPY)
		State.LASH_WINDUP:
			# Sinking into the earth.
			velocity = Vector2.ZERO
			if _state_time >= 0.6:
				_sink(true)
				_pillars_left = 6 if enraged() else 4
				_pillar_timer = 0.0
				_enter(State.LASH)
		State.LASH:
			velocity = Vector2.ZERO
			_pillar_timer -= delta
			if _pillars_left > 0 and _pillar_timer <= 0.0 and _target:
				_pillar_timer = 0.55 * rate
				_pillars_left -= 1
				_spawn_impact(_target.global_position, 0.8 * rate, 26.0, pillar_texture)
			if _pillars_left == 0 and _pillar_timer <= -0.6:
				if _target:
					# Comes up near you, but never off its own rise.
					var up := _target.global_position + Vector2(0, -90)
					global_position = _lair + (up - _lair).limit_length(180.0)
				_sink(false)
				_shake_camera(5.0)
				_enter(State.RECOVER)
		State.RECOVER:
			velocity = Vector2.ZERO
			if _state_time >= recover_time:
				_enter(State.CANOPY)
		_:
			velocity = Vector2.ZERO

	move_and_slide()
	_update_animation()
	queue_redraw()


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
		sprite.visible = dormant_texture == null
		_enter(State.DORMANT)


func is_vulnerable() -> bool:
	return _state not in [State.DORMANT, State.DEAD, State.LASH]


## Its stone turns most of a blow (a third gets through, in chips) until it
## surfaces from the earth with its core open; then every blow lands in full.
func _on_hurt(hitbox: Hitbox) -> void:
	if not is_vulnerable():
		return
	if _state in [State.RECOVER, State.SWIPE]:
		super._on_hurt(hitbox)
		return
	_chip += hitbox.damage * ARMOUR
	var through := floori(_chip)
	_chip -= through
	_flash = 0.05
	if through > 0:
		health = maxi(health - through, 0)
		_killer = hitbox.source_id
		Combat.pop_number(get_parent(), global_position, through)
		_show_bar(true)
		if health == 0:
			_die()


func _hide_in_canopy() -> void:
	_sink(false)
	sprite.visible = dormant_texture == null


func _sink(under: bool) -> void:
	sprite.visible = not under
	sprite.modulate.a = 1.0
	sprite.position = Vector2.ZERO
	body_shape.set_deferred(&"disabled", under)
	hurtbox.set_deferred(&"monitoring", not under)


func _throw_boulders(count: int) -> void:
	if _target == null:
		return
	for i in count:
		var off := Vector2.ZERO if i == 0 else Vector2.from_angle(TAU * i / (count - 1) + randf()) * 70.0
		_spawn_impact(_target.global_position + off, 1.0 + 0.12 * i, 30.0, boulder_texture)


func _spawn_impact(at: Vector2, delay: float, radius: float, texture: Texture2D) -> void:
	var impact := GroundImpact.new()
	impact.delay = delay
	impact.radius = radius
	impact.damage = attack_damage
	impact.texture = texture
	var zone := Zone.current(get_tree())
	impact.level = zone.level_at(global_position if _state != State.LASH else at) if zone else -1
	impact.global_position = at
	get_parent().add_child(impact)


func _tint() -> Color:
	# The rune core glows while it's open.
	return Color(1.25, 1.15, 0.85) if _state == State.RECOVER else Color.WHITE


func _update_animation() -> void:
	if sprite.sprite_frames == null or not sprite.visible:
		return
	if velocity.length() > 1.0:
		facing = velocity.normalized()
	var dir := DIRECTIONS_4[wrapi(roundi(facing.angle() / (PI / 2.0)), 0, 4)]
	var action := "idle"
	match _state:
		State.CANOPY:
			action = "walk" if velocity.length() > 1.0 else "idle"
		State.SWIPE_WINDUP, State.SWIPE, State.DROP:
			action = "attack"
	for candidate in [action, "walk", "idle"]:
		var anim := StringName("%s_%s" % [candidate, dir])
		if sprite.sprite_frames.has_animation(anim):
			if sprite.animation != anim:
				sprite.play(anim)
			return


func _draw() -> void:
	if _state == State.DORMANT and dormant_texture and not sprite.visible:
		var size := dormant_texture.get_size()
		draw_texture(dormant_texture, Vector2(-size.x / 2.0, -size.y + 6))
		return
	match _state:
		State.SWIPE_WINDUP:
			var t := clampf(_state_time / (pound_windup * (0.75 if enraged() else 1.0)), 0.0, 1.0)
			draw_set_transform(Vector2.ZERO, 0.0, Vector2(1.0, 0.5))
			draw_circle(Vector2.ZERO, 46.0 * t, Color(1.0, 0.75, 0.3, 0.25))
			draw_arc(Vector2.ZERO, 46.0, 0, TAU, 32, Color(1.0, 0.8, 0.35, 0.9), 2.0)
			draw_set_transform(Vector2.ZERO)
		State.LASH:
			# The ground heaves where it went under.
			draw_set_transform(Vector2.ZERO, 0.0, Vector2(1.0, 0.45))
			draw_circle(Vector2.ZERO, 26.0, Color(0.3, 0.24, 0.16, 0.5))
			draw_set_transform(Vector2.ZERO)
		State.RECOVER:
			var font := ThemeDB.fallback_font
			draw_string_outline(font, Vector2(-16, -120), "open!", HORIZONTAL_ALIGNMENT_LEFT, -1, 8, 3, Color.BLACK)
			draw_string(font, Vector2(-16, -120), "open!", HORIZONTAL_ALIGNMENT_LEFT, -1, 8, Color(1.0, 0.85, 0.4))
