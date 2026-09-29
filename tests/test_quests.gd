extends Node
## Headless test of Sorenda's "What the Trees Remember": Pell starts it, reading the
## satchel at the far end of the Hollow (the cave past the moss gate, where the hollow
## bear has its den) moves it on, Elder Moss finishes it with gold, tonics and the star
## map; and the residents' favours (Errands) hand over their cards.
## Run: godot --headless --path . res://tests/test_quests.tscn

var _failures := 0


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	RivalDirector.enabled = false
	GameState.new_game(GameState.DEFAULT_RIVALS)
	var cave: Node = load(WorldMap.SORENDA_HOLLOW).instantiate()
	var satchel := false
	var bear := false
	for node in cave.get_children():
		if node is Readable and node.title == Quests.SATCHEL_TITLE:
			satchel = true
		if node is Monster:
			bear = true
	cave.free()
	_check("the satchel is in the Hollow", satchel)
	_check("something lives in the Hollow", bear)
	var edge := WorldMap.edges_from(WorldMap.SORENDA).filter(func(e: Dictionary) -> bool: return e.to == WorldMap.SORENDA_HOLLOW)
	_check("the Hollow is past Sorenda's moss gate", edge.size() == 1 and edge[0].gate == &"sorenda_hollow")
	_check("Pell has something to ask", Quests.marker_for(&"pell") == "!")
	Quests.talked_to(&"pell")
	_check("talking to Pell starts it", Quests.stage(&"trees_remember") == 1 and "Hollow" in Quests.tracker_text())
	Quests.read("A letter somewhere else")
	_check("other reading doesn't count", Quests.stage(&"trees_remember") == 1)
	Quests.read(Quests.SATCHEL_TITLE)
	_check("reading the satchel: take it to Moss", Quests.stage(&"trees_remember") == 2 and Quests.marker_for(&"moss") == "?")
	var gold := GameState.currency
	var tonics := GameState.item_count(&"healers_tonic")
	Quests.talked_to(&"moss")
	_check("Moss completes it", Quests.stage(&"trees_remember") == Quests.DONE)
	_check("reward: gold, two tonics and the star map", GameState.currency == gold + Quests.TREES_REWARD_GOLD
		and GameState.item_count(&"healers_tonic") == tonics + 2
		and GameState.collection(GameState.PLAYER).count(Quests.TREES_REWARD_CARD) == 1)
	_check("nothing left to track", not "Trees" in Quests.tracker_text())

	# Favours. A chat: Luca gives his feather the first time you talk.
	var col := GameState.collection(GameState.PLAYER)
	_check("Luca has something for you", Errands.marker_for(&"sailor") == "!")
	Errands.talked_to(&"sailor")
	_check("talking to Luca: a gull feather", col.count(&"gull_feather") == 1 and Errands.state(&"luca_feather") == Errands.DONE)
	Errands.talked_to(&"sailor")
	_check("only once", col.count(&"gull_feather") == 1)
	# An item: Nonna wants a smoked fish. Asked first, then handed in.
	Errands.talked_to(&"nonna")
	_check("Nonna asks for a fish", Errands.state(&"nonna_fish") == Errands.ASKED and col.count(&"terracotta_tile") == 0)
	GameState.add_item(&"smoked_fish")
	_check("with a fish, she's ready", Errands.marker_for(&"nonna") == "?")
	Errands.talked_to(&"nonna")
	_check("the fish for the tile", col.count(&"terracotta_tile") == 1 and GameState.item_count(&"smoked_fish") == 0)
	# Kills: Tomas counts briar hounds the player puts down.
	Errands.talked_to(&"tomas")
	for i in 2:
		EventBus.monster_defeated.emit(&"briar_hound", GameState.PLAYER)
	EventBus.monster_defeated.emit(&"briar_hound", &"raider")          # somebody else's kill doesn't count
	_check("two hounds aren't three", not Errands.is_met(&"tomas_hounds"))
	EventBus.monster_defeated.emit(&"briar_hound", GameState.PLAYER)
	Errands.talked_to(&"tomas")
	_check("three hounds: the tide bell", col.count(&"tide_bell") == 1)
	# Rivals can do the favours too, off screen: the favour is listed with the zone's pickups.
	var in_kalmora := WorldMap.remaining_pickups(WorldMap.KALMORA, &"runner").map(func(p: Dictionary) -> String: return p.key)
	_check("rivals can still get Luca's feather", "errand:luca_feather" in in_kalmora)
	# "A Boat for Wen": three parts round the harbor, then back to Wen.
	var kalmora: Node = load(WorldMap.KALMORA).instantiate()
	var parts := 0
	for node in kalmora.get_children():
		if node is ClueObject and node.clue_id in Quests.BOAT_PARTS:
			parts += 1
	kalmora.free()
	_check("the boat parts are in Kalmora", parts == 3)
	_check("Wen has something to ask", Quests.marker_for(&"wen") == "!")
	Quests.talked_to(&"wen")
	_check("talking to Wen starts it", Quests.stage(&"wens_boat") == 1)
	for part in Quests.BOAT_PARTS:
		Quests.inspect(part)
	_check("all three found: back to Wen", Quests.stage(&"wens_boat") == 2 and Quests.marker_for(&"wen") == "?")
	var seals := col.count(&"lockbox_seal")
	Quests.talked_to(&"wen")
	_check("Wen's thanks", Quests.stage(&"wens_boat") == Quests.DONE and col.count(&"lockbox_seal") == seals + 1)
	print("PASS" if _failures == 0 else "FAILED: %d check(s)" % _failures)
	get_tree().quit(1 if _failures else 0)


func _check(label: String, ok: bool) -> void:
	if not ok:
		_failures += 1
		print("  FAIL  ", label)
