extends Node
## The Rime Stag (Starfall Range): stands in the open until a collector comes close,
## stalks, telegraphs and runs a charge, skids winded (hits hurt more then), throws
## a ring of ice shards when enraged, drops its antler, and comes back through its
## respawn gates (a gate opened while it lives is owed, not wasted).
## Run: godot --headless --path . res://tests/test_stag.tscn

const STAG := &"rime_stag"
const P := &"player"

var _failures := 0


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	RivalDirector.enabled = false
	GameState.new_game(GameState.DEFAULT_RIVALS)
	_check("starts alive with 3 kills", GameState.is_boss_alive(STAG) and GameState.boss_kills_left(STAG) == 3)

	var stag: RimeStag = load("res://scenes/characters/rime_stag.tscn").instantiate()
	add_child(stag)
	var player: Player = load("res://scenes/characters/player.tscn").instantiate()
	add_child(player)
	player.global_position = Vector2(-1000, 0)
	await _frames(3)
	player.set_physics_process(false)
	_check("stands in the open, not hidden", stag.sprite.visible)
	stag._on_hurt(_hit(10))
	_check("asleep on its feet: can't be hurt yet", stag.health == stag.max_health)

	player.global_position = Vector2(-150, 0)
	await _frames(3)
	_check("wakes and stalks when a collector comes close", stag._state == Boss.State.CANOPY)
	stag._state_time = 99.0
	await _frames(2)
	_check("then paws the snow, picking a line", stag._state == Boss.State.LASH_WINDUP)
	var start := stag.global_position
	stag._state_time = 99.0
	await _frames(2)
	_check("and charges down it", stag._state == Boss.State.LASH and not stag.lash_shape.disabled)
	for i in 120:
		if stag._state != Boss.State.LASH:
			break
		await get_tree().physics_frame
	_check("the charge covers ground, then it skids winded", stag._state == Boss.State.RECOVER
		and stag.global_position.distance_to(start) > 100.0)
	var before := stag.health
	stag._on_hurt(_hit(2))
	_check("a hit while winded hurts more", stag.health == before - 3)

	stag.health = stag.max_health / 2
	stag._charges = 2
	stag._enter(Boss.State.CANOPY)
	stag._state_time = 99.0
	await _frames(2)
	_check("enraged, it rears instead of charging", stag._state == Boss.State.DROP)
	stag._state_time = 99.0
	await _frames(2)
	var shards := get_children().filter(func(c: Node) -> bool: return c is Projectile and c.ice)
	_check("and stamps out a ring of ice shards", shards.size() == RimeStag.SHARDS)

	var loose := GameState.collection(P).count(&"rime_antler")
	stag._enter(Boss.State.RECOVER)
	stag._on_hurt(_hit(999))
	await _frames(3)
	await get_tree().create_timer(1.0).timeout
	_check("dies and leaves its antler on the ground", stag.is_dead() and _on_ground(&"rime_antler") == 1
		and GameState.collection(P).count(&"rime_antler") == loose and GameState.boss_kills_left(STAG) == 2)

	# Rivals in the arena team up: a truce, the Raider goes for the stag, and when it
	# falls with the truce kept they take their prize and go in peace.
	GameState.new_game(GameState.DEFAULT_RIVALS)
	var stag2: RimeStag = load("res://scenes/characters/rime_stag.tscn").instantiate()
	stag2.position = Vector2(600, 0)
	add_child(stag2)
	var raider: Rival = load("res://scenes/characters/rival.tscn").instantiate()
	raider.apply_profile(GameState.rival_profile(&"raider"))
	raider.position = Vector2(600, 120)
	add_child(raider)
	player.global_position = Vector2(480, 60)
	await _frames(3)
	_check("the stag wakes for the two of them", stag2._state != Boss.State.DORMANT)
	raider._update_boss_fight(0.1)
	_check("the Raider calls a truce and goes for the boss", raider._boss_fight == stag2 and raider._foe == stag2)
	_check("in a truce, a rival won't hurt the player", not Combat.can_damage(&"raider", P))
	_check("but the player can still strike (and break it)", Combat.can_damage(P, &"raider"))
	stag2._note_fighter(_hit(1))
	var by_raider := _hit(1)
	by_raider.source_id = &"raider"
	stag2._enter(Boss.State.RECOVER)
	stag2._note_fighter(by_raider)
	stag2._on_hurt(_hit(999))
	await _frames(2)
	_check("a shared kill: the Raider takes its prize and will leave in peace",
		raider._leave_after_prize and raider._peaceful())
	raider.queue_free()
	stag2.queue_free()
	await _frames(2)
	var with_hoarder: Array[StringName] = [&"raider", &"hoarder"]
	GameState.new_game(with_hoarder)
	var stag3: RimeStag = load("res://scenes/characters/rime_stag.tscn").instantiate()
	stag3.position = Vector2(600, 0)
	add_child(stag3)
	var hoarder: Rival = load("res://scenes/characters/rival.tscn").instantiate()
	hoarder.apply_profile(GameState.rival_profile(&"hoarder"))
	hoarder.position = Vector2(600, 120)
	add_child(hoarder)
	await _frames(3)
	hoarder._update_boss_fight(0.1)
	var betrayal := _hit(1)
	hoarder._on_hurt(betrayal)
	_check("striking a rival mid-fight breaks the truce", stag3.truce_broken and hoarder._speech != "")
	_check("and it fights back", hoarder._foe == player or hoarder._state == Rival.State.HUNT)
	hoarder.queue_free()
	stag3.queue_free()

	# The west gate (usually opened long before) is owed to it: it comes back.
	GameState.new_game(GameState.DEFAULT_RIVALS)
	GameState.add_loose_card(P, &"verdant_crest")
	GameState.open_gate(&"kalmora_west_gate", P)
	GameState.kill_boss(STAG, P)
	_check("a gate opened before the first kill still brings it back", GameState.is_boss_alive(STAG))

	var check := SoftLockCheck.run()
	var warnings := Array(check.warnings).filter(func(w: String) -> bool: return "rime" in w.to_lower())
	_check("validator: the antler's supply and respawn gates add up", check.errors.is_empty() and warnings.is_empty())
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
