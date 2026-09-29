extends Node
## Passive buff cards (charms): worn in two slots, held Exposed while worn (so they
## can be stolen, and a stolen charm comes off), taken off back into the binder; only
## passive cards can be worn; and the player's shots hit harder with a Hollowpoint.
## Run: godot --headless --path . res://tests/test_loadout.tscn

var _failures := 0


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	RivalDirector.enabled = false
	GameState.new_game(GameState.DEFAULT_RIVALS)
	var P := GameState.PLAYER
	var col := GameState.collection(P)
	for id in [&"hollowpoint_charm", &"tidewalker_anklet", &"mossheart_charm", &"tide_bell"]:
		GameState.add_loose_card(P, id)
	_check("a set card can't be worn", not GameState.equip(&"tide_bell"))
	_check("wear a Hollowpoint", GameState.equip(&"hollowpoint_charm")
		and col.count(&"hollowpoint_charm", CardCollection.State.EXPOSED) == 1)
	_check("and an Anklet", GameState.equip(&"tidewalker_anklet"))
	_check("but only two at once", not GameState.equip(&"mossheart_charm") and GameState.equipped.size() == 2)
	_check("taking one off binds it", GameState.unequip(&"tidewalker_anklet")
		and col.count(&"tidewalker_anklet", CardCollection.State.BOUND) == 1 and not GameState.is_equipped(&"tidewalker_anklet"))
	_check("a bound charm can be worn again", GameState.equip(&"tidewalker_anklet"))
	# A worn charm is Exposed: a rival can take it, and then it's no longer worn.
	_check("a worn charm can be stolen", GameState.steal_card(&"runner", P, &"hollowpoint_charm", &"combat"))
	_check("and it comes off", not GameState.is_equipped(&"hollowpoint_charm"))

	var player: Player = load("res://scenes/characters/player.tscn").instantiate()
	add_child(player)
	await get_tree().process_frame
	GameState.add_loose_card(P, &"hollowpoint_charm")
	var plain := player.pistol_damage + (1 if GameState.is_equipped(Player.HOLLOWPOINT) else 0)
	GameState.equip(&"mossheart_charm") if GameState.equipped.size() < 2 else null
	GameState.unequip(&"tidewalker_anklet")
	GameState.equip(&"hollowpoint_charm")
	var charmed := player.pistol_damage + (1 if GameState.is_equipped(Player.HOLLOWPOINT) else 0)
	_check("a Hollowpoint adds to a shot", charmed == plain + 1)
	# Mossheart heals a hurt wanderer who keeps out of trouble.
	player.health = 2
	GameState.unequip(&"hollowpoint_charm")
	GameState.equip(&"mossheart_charm")
	for i in 60 * 14:
		player._mossheart(1.0 / 60.0)
	_check("a Mossheart closes wounds out of danger", player.health >= 3)
	print("PASS" if _failures == 0 else "FAILED: %d check(s)" % _failures)
	get_tree().quit(1 if _failures else 0)


func _check(label: String, ok: bool) -> void:
	print("  %s  %s" % ["ok  " if ok else "FAIL", label])
	if not ok:
		_failures += 1
