extends Node
## Headless test of stealth: awareness meter, success chances, forced rolls,
## grace period, and rivals lifting from the player.
## Run: godot --headless --path . res://tests/test_stealth.tscn

const P := &"player"
const R := &"runner"

var _failures := 0


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	GameState.new_game(GameState.DEFAULT_RIVALS)
	var player: Player = load("res://scenes/characters/player.tscn").instantiate()
	var runner: Rival = load("res://scenes/characters/rival.tscn").instantiate()
	runner.collector_id = R
	add_child(player)
	add_child(runner)
	await get_tree().process_frame
	runner.set_physics_process(false)
	player.set_physics_process(false)
	var aw := runner.awareness

	# Runner at the origin facing south (down); player north of it = behind.
	runner.global_position = Vector2.ZERO
	runner.facing = Vector2.DOWN
	aw.facing = Vector2.DOWN
	player.facing = Vector2.DOWN

	player.global_position = Vector2(0, -100)
	_tick(aw, player, 5.0)
	_check("unseen and unheard behind at 100px stays unaware", aw.level == Awareness.Level.UNAWARE and aw.value == 0.0)

	player.global_position = Vector2(0, 60)
	_tick(aw, player, 0.5)
	_check("seen in the cone: rises", aw.value > 0.0)
	_tick(aw, player, 10.0)
	_check("keeps watching: alert", aw.level == Awareness.Level.ALERT)

	player.global_position = Vector2(0, -100)
	_tick(aw, player, 2.0)
	_check("out of sight: still alert briefly (hysteresis)", aw.level == Awareness.Level.ALERT)
	_tick(aw, player, 10.0)
	_check("out of sight long enough: calms to unaware", aw.level == Awareness.Level.UNAWARE)

	player.global_position = Vector2(0, -20)  # Right behind it.
	_check("unaware + behind = 95%", is_equal_approx(Stealth.success_chance(player, runner), 0.95))
	_check("no loose cards: blocked", Stealth.blocker(player, runner) != "")

	GameState.add_loose_card(R, &"harbor_lantern")
	GameState.add_loose_card(R, &"coral_coin")
	GameState.add_loose_card(R, &"sea_glass")
	GameState.bind_card(R, &"sea_glass")
	var result := Stealth.attempt(player, runner, 0.0)
	_check("forced success lifts a loose card", result.ok and result.card_id in [&"harbor_lantern", &"coral_coin"])
	_check("bound card untouched", GameState.collection(R).count(&"sea_glass") == 1)
	_check("lift makes the runner uneasy", aw.value >= Stealth.SUCCESS_BUMP)
	_check("grace blocks a second try", Stealth.attempt(player, runner, 0.0).reason == "They were just robbed")

	GameState.clear_grace(R)
	result = Stealth.attempt(player, runner, 0.99)
	_check("forced failure is caught", not result.ok and result.reason == "Caught")
	_check("caught: runner alert and wary", aw.level == Awareness.Level.ALERT and aw.is_wary())
	_check("alert + wary chance is low", Stealth.success_chance(player, runner) < 0.15)

	# Runner lifts from the player: behind is easier than face to face.
	GameState.add_loose_card(P, &"gull_feather")
	player.global_position = Vector2.ZERO
	runner.global_position = Vector2(0, -15)
	player.facing = Vector2.DOWN
	_check("player robbed from behind: 60%", is_equal_approx(Stealth.success_chance(runner, player), Stealth.PLAYER_BEHIND))
	player.facing = Vector2.UP
	_check("player facing the thief: 12%", is_equal_approx(Stealth.success_chance(runner, player), Stealth.PLAYER_FACING))
	result = Stealth.attempt(runner, player, 0.0)
	_check("runner lifts from player", result.ok and GameState.collection(R).count(&"gull_feather") == 1)

	print("PASS" if _failures == 0 else "FAILED: %d check(s)" % _failures)
	get_tree().quit(1 if _failures else 0)


func _tick(aw: Awareness, target: Node2D, seconds: float) -> void:
	var steps := int(seconds * 60.0)
	for i in steps:
		aw.update(1.0 / 60.0, target)


func _check(label: String, ok: bool) -> void:
	print("  %s  %s" % ["ok  " if ok else "FAIL", label])
	if not ok:
		_failures += 1
