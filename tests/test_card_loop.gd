extends Node
## Headless end-to-end test of the spell-steal loop:
## buy -> cast -> steal loose only -> bound safe -> lockbox blocks -> sell removes supply.
## Run: godot --headless --path . res://tests/test_card_loop.tscn
## (A scene rather than a -s script so the autoloads exist.)

const P := &"player"
const R := &"runner"

var _failures := 0


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	var gs := GameState
	var root := get_tree().root
	gs.new_game(gs.DEFAULT_RIVALS)
	var player: Node2D = load("res://scenes/characters/player.tscn").instantiate()
	var runner: Node2D = load("res://scenes/characters/rival.tscn").instantiate()
	runner.set(&"collector_id", R)
	root.add_child(player)
	root.add_child(runner)
	player.global_position = Vector2.ZERO
	runner.global_position = Vector2(60, 0)
	await get_tree().process_frame
	runner.set_physics_process(false)  # Hold the runner still for the test.

	_check("starting gold", gs.currency == gs.STARTING_GOLD)
	_check("buy whisper", gs.buy_card(P, CardSpells.PICKPOCKET) and gs.currency == gs.STARTING_GOLD - 30)

	gs.add_loose_card(R, &"harbor_lantern")
	gs.add_loose_card(R, &"sea_glass")
	gs.bind_card(R, &"sea_glass")
	_check("tracker before", gs.tracker_counts()[R] == 2 and gs.tracker_counts()[P] == 0)

	var stolen: StringName = CardSpells.cast_pickpocket(player)
	_check("whisper steals the loose card", stolen == &"harbor_lantern")
	_check("thief holds it loose", gs.collection(P).count(&"harbor_lantern", CardCollection.State.LOOSE) == 1)
	_check("victim lost it", gs.collection(R).count(&"harbor_lantern") == 0)
	_check("whisper consumed", gs.collection(P).count(CardSpells.PICKPOCKET) == 0)
	_check("tracker after", gs.tracker_counts()[R] == 1 and gs.tracker_counts()[P] == 1)
	_check("no whisper, no cast", CardSpells.cast_pickpocket(player) == &"")

	_check("victim is in grace", gs.grace_left(R) > 0.0)
	gs.clear_grace(R)
	gs.add_loose_card(P, CardSpells.PICKPOCKET)
	_check("bound cards can't be pickpocketed", CardSpells.cast_pickpocket(player) == &"")
	_check("failed cast keeps the whisper", gs.collection(P).count(CardSpells.PICKPOCKET) == 1)

	gs.add_loose_card(R, &"tide_bell")
	gs.add_loose_card(R, CardSpells.LOCKBOX)
	_check("lockbox locks", CardSpells.use_lockbox(R, &"tide_bell"))
	_check("locked card can't be pickpocketed", CardSpells.cast_pickpocket(player) == &"")

	runner.global_position = Vector2(500, 0)
	gs.add_loose_card(R, &"coral_coin")
	_check("out of range", CardSpells.cast_pickpocket(player) == &"")

	var supply: int = gs.world_supply[&"harbor_lantern"]
	var gold: int = gs.currency
	gs.sell_card(P, &"harbor_lantern")
	_check("selling removes world supply", gs.world_supply[&"harbor_lantern"] == supply - 1)
	_check("selling pays", gs.currency == gold + 10)

	gs.add_loose_card(P, &"gull_feather")
	gs.bind_card(P, &"gull_feather")
	_check("bound card resists direct steal", not gs.steal_card(R, P, &"gull_feather", &"combat"))
	gs.expose_card(P, &"gull_feather")
	_check("exposed card can be stolen", gs.steal_card(R, P, &"gull_feather", &"combat"))

	print("PASS" if _failures == 0 else "FAILED: %d check(s)" % _failures)
	get_tree().quit(1 if _failures else 0)


func _check(label: String, ok: bool) -> void:
	print("  %s  %s" % ["ok  " if ok else "FAIL", label])
	if not ok:
		_failures += 1
