extends Node
## Canopy Warden: invulnerable in the canopy, wakes for nearby collectors,
## vulnerable once landed, drops its three cards, kill cap + gate-based respawn,
## and rivals hunting it only for cards they still need.
## Run: godot --headless --path . res://tests/test_boss.tscn

const WARDEN := &"canopy_warden"
const P := &"player"
const RAIDER := &"raider"

var _failures := 0
var _defeated_by: StringName = &""


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	RivalDirector.enabled = false
	GameState.new_game(GameState.DEFAULT_RIVALS)
	EventBus.boss_defeated.connect(func(_id: StringName, killer: StringName) -> void: _defeated_by = killer)

	_check("starts alive with 4 kills available", GameState.is_boss_alive(WARDEN) and GameState.boss_kills_left(WARDEN) == 4)

	var boss: Boss = load("res://scenes/characters/canopy_warden.tscn").instantiate()
	add_child(boss)
	var player: Player = load("res://scenes/characters/player.tscn").instantiate()
	add_child(player)
	player.global_position = Vector2(-1000, 0)
	await _frames(3)
	player.set_physics_process(false)

	boss._on_hurt(_hit(P, 10))
	_check("dormant in the canopy: can't be hurt", boss.health == boss.max_health and not boss.is_vulnerable())

	player.global_position = Vector2(-120, 0)
	await _frames(3)
	_check("wakes when a collector comes close", boss._state == Boss.State.CANOPY)
	boss._on_hurt(_hit(P, 10))
	_check("still untouchable up in the canopy", boss.health == boss.max_health)

	boss._land()
	_check("vulnerable once it lands", boss.is_vulnerable())
	var pickups_before := get_tree().get_nodes_in_group(&"card_pickups").size()
	boss._on_hurt(_hit(P, boss.max_health))
	await _frames(3)
	_check("dies at 0 HP", boss.is_dead())
	_check("drops its three cards", get_tree().get_nodes_in_group(&"card_pickups").size() == pickups_before + 3)
	_check("kill recorded, credited to the player", not GameState.is_boss_alive(WARDEN)
		and GameState.boss_kills_left(WARDEN) == 3 and _defeated_by == P)

	# Gate-based respawn.
	GameState.add_loose_card(P, &"hollow_acorn")
	GameState.open_gate(&"sorenda_hollow", P)
	await _frames(2)
	# (With the player standing nearby it wakes straight back up into the canopy.)
	_check("opening a respawn gate brings it back", GameState.is_boss_alive(WARDEN)
		and boss._state in [Boss.State.DORMANT, Boss.State.CANOPY] and boss.health == boss.max_health)
	await get_tree().create_timer(1.5).timeout
	_check("the old death fade doesn't hide the returned boss", boss.visible and not boss.is_dead())

	# Kill cap: 4 kills total, then it's gone for good.
	var respawn_gates := [[&"thornveil_moss_bridge", &"moss_lantern"], [&"elder_grove_seal", &"veyra_pearl"]]
	for pair in respawn_gates:
		GameState.kill_boss(WARDEN, P)
		GameState.add_loose_card(P, pair[1])
		GameState.open_gate(pair[0], P)
	GameState.kill_boss(WARDEN, P)
	_check("four kills used up", GameState.boss_kills_left(WARDEN) == 0 and not GameState.is_boss_alive(WARDEN))
	GameState._respawn_boss(WARDEN, &"any_gate")
	_check("won't respawn past the kill cap", not GameState.is_boss_alive(WARDEN))

	# Rivals: hunters go for it only while they still need its cards.
	GameState.new_game(GameState.DEFAULT_RIVALS)
	_check("Raider wants the Warden", RivalDirector.wanted_boss(RAIDER, WorldMap.THORNVEIL) != null)
	_check("so it heads for the grove", RivalDirector.choose_destination(RAIDER, WorldMap.THORNVEIL) == WorldMap.WARDENS_GROVE)
	_check("the Runner (no weapon) never hunts bosses", RivalDirector.wanted_boss(&"runner", WorldMap.KALMORA) == null)
	for card in [&"warden_mask", &"canopy_eye", &"verdant_crest"]:
		GameState.add_loose_card(RAIDER, card)
	_check("no denial play: holding every drop, it leaves the boss alone",
		RivalDirector.wanted_boss(RAIDER, WorldMap.THORNVEIL) == null)

	GameState.new_game(GameState.DEFAULT_RIVALS)
	var data := GameState.boss_data(WARDEN)
	_check("off-screen win takes the drops", RivalDirector.fight_boss_offscreen(RAIDER, data, 0.0)
		and GameState.collection(RAIDER).count(&"canopy_eye") == 1 and not GameState.is_boss_alive(WARDEN))
	GameState.new_game(GameState.DEFAULT_RIVALS)
	RivalDirector.fight_boss_offscreen(RAIDER, data, 0.99)
	_check("off-screen loss wakes it in the nearest town (Sorenda)",
		GameState.rival_locations[RAIDER].zone == WorldMap.SORENDA and GameState.is_boss_alive(WARDEN))

	var check := SoftLockCheck.run()
	var boss_warnings := Array(check.warnings).filter(func(w: String) -> bool: return "Boss" in w)
	_check("validator: kill cap reachable via respawn gates", check.errors.is_empty() and boss_warnings.is_empty())

	print("PASS" if _failures == 0 else "FAILED: %d check(s)" % _failures)
	get_tree().quit(1 if _failures else 0)


func _hit(source: StringName, damage: int) -> Hitbox:
	var hitbox := Hitbox.new()
	hitbox.source_id = source
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
