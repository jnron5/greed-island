extends Node
## Headless test of combat rules: who can hurt whom, towns, combat steals,
## monster death drops, rival and player defeats (respawning in the nearest town),
## dropping cards, card gates.
## Run: godot --headless --path . res://tests/test_combat.tscn

const P := &"player"
const R := &"runner"
const RAIDER := &"raider"

var _failures := 0


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	RivalDirector.enabled = false  # Keep rivals where the test puts them.
	GameState.new_game(GameState.DEFAULT_RIVALS)

	_check("monster hits player", Combat.can_damage(Combat.MONSTER, P))
	_check("monsters don't hit monsters", not Combat.can_damage(Combat.MONSTER, Combat.MONSTER))
	_check("nobody hits themselves", not Combat.can_damage(P, P))
	_check("collectors fight in the field", Combat.can_damage(P, R))
	GameState.set_in_safe_zone(R, true)
	_check("no fights in town", not Combat.can_damage(P, R) and not Combat.can_damage(R, P))
	_check("monster damage is allowed by the rules (monsters never enter towns)", Combat.can_damage(Combat.MONSTER, R))
	GameState.set_in_safe_zone(R, false)

	# Combat steal.
	GameState.add_loose_card(R, &"coral_coin")
	GameState.add_loose_card(R, &"sea_glass")
	GameState.bind_card(R, &"sea_glass")
	_check("winner takes the loose card", Combat.resolve_defeat(P, R) == &"coral_coin")
	_check("bound card stays", GameState.collection(R).count(&"sea_glass") == 1)
	GameState.add_loose_card(R, &"tide_bell")
	_check("grace protects a just-beaten loser", Combat.resolve_defeat(P, R) == &"")
	GameState.clear_grace(R)

	# Monster: dies, drops a card, stays down until respawn.
	var hound: Monster = load("res://scenes/characters/briar_hound.tscn").instantiate()
	hound.max_health = 3
	add_child(hound)
	await get_tree().process_frame
	var pickups_before := get_tree().get_nodes_in_group(&"card_pickups").size()
	hound._on_hurt(_hit(P, 2))
	_check("monster takes damage", hound.health == 1 and not hound.is_dead())
	hound._on_hurt(_hit(P, 2))
	_check("monster dies", hound.is_dead())
	await get_tree().process_frame
	await get_tree().process_frame
	_check("monster drops a card", get_tree().get_nodes_in_group(&"card_pickups").size() == pickups_before + 1)

	# Rival: beaten by the player, loses a card, goes down.
	var runner: Rival = load("res://scenes/characters/rival.tscn").instantiate()
	runner.collector_id = R
	add_child(runner)
	await get_tree().process_frame
	runner.set_physics_process(false)
	var tide_before := GameState.collection(P).count(&"tide_bell")
	for i in 5:
		runner._on_hurt(_hit(P, 1))
	_check("beaten rival hands over a card", GameState.collection(P).count(&"tide_bell") == tide_before + 1)
	_check("beaten rival is down and untouchable", runner.hurtbox.invulnerable)

	# Beaten rivals wake in the nearest town. Deep in Thornveil that's Sorenda,
	# near its south edge it's Kalmora; either way the rival leaves this zone.
	_check("nearest town from deep Thornveil is Sorenda",
		WorldMap.nearest_town(WorldMap.THORNVEIL, Vector2(0, -700)) == WorldMap.SORENDA)
	_check("nearest town from Thornveil's south edge is Kalmora",
		WorldMap.nearest_town(WorldMap.THORNVEIL, Vector2(0, 60)) == WorldMap.KALMORA)
	GameState.move_rival(R, WorldMap.THORNVEIL, Vector2(0, -600))
	runner.position = Vector2(0, -600)
	runner.respawn_in_nearest_town()
	await get_tree().process_frame
	var loc: Dictionary = GameState.rival_locations[R]
	_check("rival relocated to Sorenda", loc.zone == WorldMap.SORENDA and loc.position == null)
	_check("rival left the zone it fell in", not is_instance_valid(runner))

	# Player: beaten by the Raider, loses a card, heads for the nearest town.
	var player: Player = load("res://scenes/characters/player.tscn").instantiate()
	add_child(player)
	await get_tree().process_frame
	player.set_physics_process(false)
	GameState.add_loose_card(P, &"gull_feather")
	player._on_hurt(_hit(RAIDER, 99))
	_check("raider took a card from the player", GameState.collection(RAIDER).card_ids().size() == 1)
	_check("player is down", player.health == 0 and player.hurtbox.invulnerable)
	_check("player will wake in Kalmora", "The Raider beat you" in GameState.pending_notice
		and "woke in Kalmora" in GameState.pending_notice)

	# Dropping a card doesn't touch world supply (it's still out there).
	GameState.add_loose_card(P, &"harbor_lantern")
	var supply: int = GameState.world_supply[&"harbor_lantern"]
	_check("drop removes from hand", GameState.drop_card(P, &"harbor_lantern")
		and GameState.collection(P).count(&"harbor_lantern") == 0)
	_check("drop keeps world supply", GameState.world_supply[&"harbor_lantern"] == supply)

	# Card gate: spends the cost card, stays open.
	_check("gate refuses without the card", not GameState.open_gate(&"kalmora_north_gate", P))
	GameState.add_loose_card(P, &"salt_compass")
	var compass_supply: int = GameState.world_supply[&"salt_compass"]
	_check("gate opens with the card", GameState.open_gate(&"kalmora_north_gate", P))
	_check("gate card consumed", GameState.collection(P).count(&"salt_compass") == 0
		and GameState.world_supply[&"salt_compass"] == compass_supply - 1)
	_check("gate stays open", GameState.opened_gates.has(&"kalmora_north_gate"))

	print("PASS" if _failures == 0 else "FAILED: %d check(s)" % _failures)
	get_tree().quit(1 if _failures else 0)


func _hit(source: StringName, damage: int) -> Hitbox:
	var hitbox := Hitbox.new()
	hitbox.source_id = source
	hitbox.damage = damage
	hitbox.knockback = 0.0
	add_child(hitbox)
	return hitbox


func _check(label: String, ok: bool) -> void:
	print("  %s  %s" % ["ok  " if ok else "FAIL", label])
	if not ok:
		_failures += 1
