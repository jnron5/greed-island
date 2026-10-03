extends Node
## Return cards: each town's card shop sells its own (Sable for Kalmora, the stalls in
## Sorenda, Verdana and Frisalle, Fennick at Seabright), dear; used from anywhere, the
## card is spent and you arrive in that town's square; refused (and kept) when you're
## already there.
## Run: godot --headless --path . res://tests/test_return.tscn

var _failures := 0


func _ready() -> void:
	get_tree().current_scene = null
	_run.call_deferred()


func _run() -> void:
	RivalDirector.enabled = false
	TimeOfDay.paused = true
	GameState.new_game(GameState.DEFAULT_RIVALS)
	var P := GameState.PLAYER
	var col := GameState.collection(P)
	for id: StringName in CardSpells.RETURN_CARDS:
		var card := CardDatabase.get_card(id)
		_check("%s: a one-use card, and not cheap" % id, card != null and card.category == CardData.Category.BUFF_TEMP
			and card.shop_price >= 100 and not card.is_final_set_member)
	# Who sells which.
	for town: String in [WorldMap.SORENDA, WorldMap.VERDANA, WorldMap.FRISALLE]:
		var zone := await _load(town)
		var stall := zone.find_children("*", "Merchant", true, false)
		var home := CardSpells.return_card_for(town)
		_check("%s's stall sells %s" % [zone.name, home], stall.size() > 0 and (stall[0] as Merchant).stock.has(home))
	for room: Array in [[WorldMap.KALMORA_CARD_SHOP, &"sable", &"kalmora_return"], [WorldMap.SEABRIGHT_HOTEL, &"fennick", &"seabright_return"]]:
		var zone := await _load(room[0])
		var keeper := zone.get_node_or_null("Npc_%s" % room[1]) as Npc
		_check("%s sells %s" % [room[1], room[2]], keeper != null and keeper.shop_stock.has(room[2]))

	# One resident per town gives the first one free, once.
	_check("every town's return card has a giver", CardSpells.RETURN_CARDS.keys().all(func(id: StringName) -> bool:
		return Quests.WELCOME_GIFTS.values().has(id)))
	_check("Jobelle has something for you", Quests.marker_for(&"jobelle") == "!" and not Quests.dialogue_for(&"jobelle").is_empty())
	Quests.talked_to(&"jobelle")
	_check("a free Kalmora Return", col.count(&"kalmora_return") == 1 and Quests.marker_for(&"jobelle") == "")
	Quests.talked_to(&"jobelle")
	_check("only the once", col.count(&"kalmora_return") == 1 and Quests.dialogue_for(&"jobelle").is_empty())
	GameState.consume_card(P, &"kalmora_return", &"buff")

	# Buy one in Verdana; it won't take you where you already are.
	var verdana := await _load(WorldMap.VERDANA)
	GameState.currency = 200
	_check("buying a Verdana Return costs its price", GameState.buy_card(P, &"verdana_return")
		and col.count(&"verdana_return") == 1 and GameState.currency == 200 - CardDatabase.get_card(&"verdana_return").shop_price)
	var player := verdana.get_tree().get_first_node_in_group(&"player") as Player
	_check("not from Verdana itself (the card is kept)", not CardSpells.use_return(player, &"verdana_return")
		and col.count(&"verdana_return") == 1)

	# From up at Lake Serin it takes you home, and is gone.
	var lake := await _load(WorldMap.LAKE_SERIN)
	player = lake.get_tree().get_first_node_in_group(&"player") as Player
	_check("used at Lake Serin", CardSpells.use_return(player, &"verdana_return") and col.count(&"verdana_return") == 0)
	var back := await _wait_for(WorldMap.VERDANA)
	player = back.get_tree().get_first_node_in_group(&"player") as Player if back else null
	var marker := back.get_node_or_null("Spawns/%s" % WorldMap.town_spawn(WorldMap.VERDANA)) as Node2D if back else null
	_check("and you arrive in Verdana's square", back != null and player != null and marker != null
		and player.global_position.distance_to(marker.global_position) < 40.0)
	print("PASS" if _failures == 0 else "FAILED: %d check(s)" % _failures)
	get_tree().quit(1 if _failures else 0)


func _load(path: String) -> Zone:
	get_tree().change_scene_to_file(path)
	return await _wait_for(path)


func _wait_for(path: String) -> Zone:
	for i in 300:
		await get_tree().process_frame
		if get_tree().current_scene != null and get_tree().current_scene.scene_file_path == path:
			await get_tree().physics_frame
			await get_tree().physics_frame
			return get_tree().current_scene as Zone
	return null


func _check(label: String, ok: bool) -> void:
	if not ok:
		_failures += 1
		print("  FAIL  ", label)
