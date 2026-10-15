extends Node
## Hollowmaw, the sand serpent (the Siroth Dunes' boss, in the Bone Hollow): buried
## and out of reach until a collector comes close; burrows after its target (still out
## of reach); the sand caves in a marked ring and it bursts up there; reared up, it
## spits a fan of sand at range and bites up close; slumped and winded after, every
## blow hurts more; it sinks back under; drops the Hollowmaw Scale.
## Run: godot --headless --path . res://tests/test_serpent.tscn

const BOSS := &"sand_serpent"
const P := &"player"

var _failures := 0


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	RivalDirector.enabled = false
	GameState.new_game(GameState.DEFAULT_RIVALS)
	_check("starts alive with 3 kills", GameState.is_boss_alive(BOSS) and GameState.boss_kills_left(BOSS) == 3)
	var boss: SandSerpent = load("res://scenes/characters/sand_serpent.tscn").instantiate()
	add_child(boss)
	var player: Player = load("res://scenes/characters/player.tscn").instantiate()
	add_child(player)
	player.global_position = Vector2(-1000, 0)
	await _frames(3)
	player.set_physics_process(false)
	boss._on_hurt(_hit(10))
	_check("buried under the sand: can't be hurt", boss.health == boss.max_health and not boss.sprite.visible)

	player.global_position = Vector2(-150, 0)
	await _frames(3)
	_check("wakes and burrows when a collector comes close", boss._state == Boss.State.CANOPY and not boss.is_vulnerable())
	var start := boss.global_position.distance_to(player.global_position)
	await _frames(20)
	_check("the mound slides after its target", boss.global_position.distance_to(player.global_position) < start - 20.0)

	boss._state_time = 99.0
	await _frames(2)
	_check("the sand caves in a marked ring", boss._state == Boss.State.DROP)
	boss._state_time = 99.0
	await _frames(2)
	_check("it bursts up out of the sand", boss._state in [Boss.State.SLAM, Boss.State.GROUNDED] and boss.is_vulnerable())
	await _frames(30)
	_check("reared up and visible", boss.sprite.visible and boss._rise > 0.5)

	player.global_position = boss.global_position + Vector2(-180, 0)
	boss._enter(Boss.State.GROUNDED)
	boss._state_time = 99.0
	await _frames(2)
	_check("at range it gathers itself to spit", boss._state == Boss.State.LASH_WINDUP)
	boss._state_time = 99.0
	await _frames(2)
	var spit := get_children().filter(func(c: Node) -> bool: return c is Projectile and c.sand)
	_check("a fan of sand flies at its target", spit.size() >= 5)

	player.global_position = boss.global_position + Vector2(40, 0)
	boss._attacks_left = 2
	boss._enter(Boss.State.GROUNDED)
	boss._state_time = 99.0
	await _frames(2)
	_check("up close it bites", boss._state in [Boss.State.SWIPE_WINDUP, Boss.State.SWIPE])

	boss._enter(Boss.State.RECOVER)
	var before := boss.health
	boss._on_hurt(_hit(3))
	_check("slumped and winded, a blow hurts more", boss.health == before - 4)
	boss._state_time = 99.0
	await _frames(2)
	_check("then it sinks back under the sand", boss._state == Boss.State.CLIMB and not boss.is_vulnerable())
	await get_tree().create_timer(0.8).timeout
	_check("and hunts again from below", boss._state == Boss.State.CANOPY and not boss.sprite.visible)

	var had := GameState.collection(P).count(&"hollowmaw_scale")
	# Stand clear: the scale is flung out of the body and the player would pick it up.
	player.global_position = boss.global_position + Vector2(300, 0)
	boss._land()
	await _frames(2)
	boss._on_hurt(_hit(999))
	await _frames(3)
	await get_tree().create_timer(1.0).timeout
	_check("falls and leaves its scale on the ground", boss.is_dead() and _on_ground(&"hollowmaw_scale") == 1
		and GameState.collection(P).count(&"hollowmaw_scale") == had and GameState.boss_kills_left(BOSS) == 2)

	var check := SoftLockCheck.run()
	var warnings := Array(check.warnings).filter(func(w: String) -> bool: return "serpent" in w.to_lower() or "hollowmaw" in w.to_lower())
	_check("validator: the scale's supply and respawn gates add up", check.errors.is_empty() and warnings.is_empty())
	print("PASS" if _failures == 0 else "FAILED: %d check(s)" % _failures)
	get_tree().quit(1 if _failures else 0)


func _hit(damage: int) -> Hitbox:
	var hitbox := Hitbox.new()
	hitbox.source_id = P
	hitbox.damage = damage
	hitbox.knockback = 0.0
	add_child(hitbox)
	return hitbox


func _frames(n: int) -> void:
	for i in n:
		await get_tree().physics_frame


func _check(label: String, ok: bool) -> void:
	print("  %s  %s" % ["ok  " if ok else "FAIL", label])
	if not ok:
		_failures += 1


## Card pickups lying in the test scene for `card_id`.
func _on_ground(card_id: StringName) -> int:
	return get_children().filter(func(c: Node) -> bool: return c is CardPickup and c.card_id == card_id).size()
