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
	# Emberburst: a charged round bursts where it lands and hurts everything round it.
	GameState.add_loose_card(P, &"emberburst_rounds")
	GameState.unequip(&"mossheart_charm")
	_check("wear Emberburst Rounds", GameState.equip(&"emberburst_rounds"))
	var hounds: Array[Monster] = []
	for x in [300.0, 330.0]:
		var hound: Monster = load("res://scenes/characters/briar_hound.tscn").instantiate()
		hound.position = Vector2(x, 200)
		add_child(hound)
		hounds.append(hound)
	await get_tree().physics_frame
	var full := [hounds[0].health, hounds[1].health]
	var burst := Explosion.new()
	burst.damage = 1
	burst.source_id = P
	burst.position = Vector2(315, 190)
	add_child(burst)
	for i in 4:
		await get_tree().physics_frame
	_check("a burst hurts every monster round it", hounds[0].health < full[0] and hounds[1].health < full[1])
	player.global_position = Vector2(-400, 0)
	var shot: Projectile = load("res://scenes/systems/projectile.tscn").instantiate()
	shot.explosive = true
	shot.source_id = P
	shot.lifetime = 0.05
	add_child(shot)
	await get_tree().create_timer(0.15).timeout
	_check("a charged round bursts where it stops", get_children().any(func(c: Node) -> bool: return c is Explosion))
	# Frostfang: worn, the sword freezes what it hits.
	GameState.add_loose_card(P, &"frostfang_charm")
	GameState.unequip(&"emberburst_rounds")
	_check("wear the Frostfang Charm", GameState.equip(&"frostfang_charm") and player.sword_hitbox.freeze > 0.0)
	var cold := Hitbox.new()
	cold.damage = 0
	cold.freeze = player.sword_hitbox.freeze
	cold.source_id = P
	hounds[0].health = 5
	hounds[0]._on_hurt(cold)
	var at := hounds[0].global_position
	await get_tree().create_timer(0.5).timeout
	_check("a Frostfang hit freezes a monster in place", hounds[0]._frozen > 0.0 and hounds[0].global_position.distance_to(at) < 1.0)
	cold.free()
	GameState.unequip(&"frostfang_charm")
	_check("taking it off thaws the sword", player.sword_hitbox.freeze == 0.0)
	for hound in hounds:
		hound.queue_free()
	# The rebuy shelf: a card spent on a gate can be bought back, at a price.
	GameState.add_loose_card(P, &"salt_compass")
	GameState.open_gate(&"kalmora_north_gate", P)
	_check("a gate card spent is remembered", GameState.spent_on_gates.get(&"salt_compass", 0) == 1)
	GameState.currency = 0
	_check("can't buy it back broke", not GameState.rebuy_card(&"salt_compass"))
	GameState.currency = 1000
	var price := GameState.rebuy_price(&"salt_compass")
	_check("buying it back", GameState.rebuy_card(&"salt_compass") and col.count(&"salt_compass") == 1
		and GameState.currency == 1000 - price and not GameState.spent_on_gates.has(&"salt_compass"))
	# The game stands still while the binder is open.
	var binder: Node = load("res://scenes/ui/binder.tscn").instantiate()
	add_child(binder)
	binder.open()
	_check("opening the binder pauses the game", get_tree().paused and binder.can_process())
	binder.close()
	_check("closing it lets the game run again", not get_tree().paused)
	binder.queue_free()
	print("PASS" if _failures == 0 else "FAILED: %d check(s)" % _failures)
	get_tree().quit(1 if _failures else 0)


func _check(label: String, ok: bool) -> void:
	print("  %s  %s" % ["ok  " if ok else "FAIL", label])
	if not ok:
		_failures += 1
