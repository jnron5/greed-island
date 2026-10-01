extends Node
## The Cairn Colossus (Aurewind Plains): a heap of stones until a collector comes
## close; its stone turns most blows while it walks; hurls boulders at marked spots;
## sinks out of reach while pillars burst up under its target; surfaces open (full
## damage); pounds the ground up close; drops the Cairn Heart.
## Run: godot --headless --path . res://tests/test_colossus.tscn

const BOSS := &"cairn_colossus"
const P := &"player"

var _failures := 0


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	RivalDirector.enabled = false
	GameState.new_game(GameState.DEFAULT_RIVALS)
	_check("starts alive with 3 kills", GameState.is_boss_alive(BOSS) and GameState.boss_kills_left(BOSS) == 3)
	var boss: CairnColossus = load("res://scenes/characters/cairn_colossus.tscn").instantiate()
	add_child(boss)
	var player: Player = load("res://scenes/characters/player.tscn").instantiate()
	add_child(player)
	player.global_position = Vector2(-1000, 0)
	await _frames(3)
	player.set_physics_process(false)
	boss._on_hurt(_hit(10))
	_check("a quiet heap of stones: can't be hurt", boss.health == boss.max_health)

	player.global_position = Vector2(-160, 0)
	await _frames(3)
	_check("stands up when a collector comes close", boss._state == Boss.State.CANOPY)
	boss._on_hurt(_hit(3))
	_check("its stone turns most of a blow while it walks", boss.health == boss.max_health - 1)

	boss._state_time = 99.0
	await _frames(2)
	_check("at range it hurls boulders", boss._state == Boss.State.DROP)
	boss._state_time = 99.0
	await _frames(2)
	var impacts := get_children().filter(func(c: Node) -> bool: return c is GroundImpact)
	_check("three marked spots, round the target", impacts.size() == 3)

	boss._state_time = 99.0
	await _frames(2)
	_check("then it sinks into the earth", boss._state == Boss.State.LASH_WINDUP)
	boss._state_time = 99.0
	await _frames(2)
	_check("out of reach underground", boss._state == Boss.State.LASH and not boss.is_vulnerable())
	for i in 400:
		if boss._state != Boss.State.LASH:
			break
		await get_tree().physics_frame
	_check("pillars burst up under its target", get_children().filter(func(c: Node) -> bool: return c is GroundImpact).size() >= 1
		or boss._state == Boss.State.RECOVER)
	_check("and it surfaces open", boss._state == Boss.State.RECOVER and boss.global_position.distance_to(boss._lair) <= 181.0)
	var before := boss.health
	boss._on_hurt(_hit(4))
	_check("open, every blow lands in full", boss.health == before - 4)

	boss._enter(Boss.State.CANOPY)
	player.global_position = boss.global_position + Vector2(30, 0)
	await _frames(3)
	_check("up close it pounds the ground", boss._state in [Boss.State.SWIPE_WINDUP, Boss.State.SWIPE])

	var had := GameState.collection(P).count(&"cairn_heart")
	boss._enter(Boss.State.RECOVER)
	boss._on_hurt(_hit(999))
	await _frames(3)
	await get_tree().create_timer(1.0).timeout
	_check("falls and leaves its heart on the ground", boss.is_dead() and _on_ground(&"cairn_heart") == 1
		and GameState.collection(P).count(&"cairn_heart") == had and GameState.boss_kills_left(BOSS) == 2)

	var check := SoftLockCheck.run()
	var warnings := Array(check.warnings).filter(func(w: String) -> bool: return "cairn" in w.to_lower())
	_check("validator: the heart's supply and respawn gates add up", check.errors.is_empty() and warnings.is_empty())
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
