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
	_check("then Pell has something for you", Quests.marker_for(&"pell") == "!")
	Quests.talked_to(&"pell")
	_check("Pell gives Emberburst Rounds, once", GameState.collection(GameState.PLAYER).count(&"emberburst_rounds") == 1
		and Quests.marker_for(&"pell") == "")
	Quests.talked_to(&"pell")
	_check("and only once", GameState.collection(GameState.PLAYER).count(&"emberburst_rounds") == 1)
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
	# Paid favours never take your gold on the first chat, even when you could afford it.
	var purse := GameState.currency
	Errands.talked_to(&"brannoc")
	_check("Brannoc asks before he takes your gold", GameState.currency == purse and col.count(&"net_mender") == 0)
	Errands.talked_to(&"brannoc")
	_check("and sells it the next time", GameState.currency == purse - 30 and col.count(&"net_mender") == 1)
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

	# "Stones That Remember": each stone is a Readable in its own zone; read all three,
	# then back to Aldous in Verdana.
	for title: String in Quests.STONES:
		var zone: Node = load(Quests.STONES[title]).instantiate()
		_check("'%s' stands in %s" % [title, zone.name],
			zone.get_children().any(func(n: Node) -> bool: return n is Readable and n.title == title))
		zone.free()
	_check("Aldous has something to ask", Quests.marker_for(&"aldous") == "!")
	Quests.read("The Aurewind circle")     # read before being asked: it still counts
	Quests.talked_to(&"aldous")
	_check("talking to Aldous starts it, one stone already read", Quests.stage(&"stones_remember") == 1
		and "(1/3)" in Quests.tracker_text())
	_check("the unread stones' zones show on the map", WorldMap.LAKE_SERIN in Quests.map_goals()
		and WorldMap.STARFALL in Quests.map_goals() and not WorldMap.AUREWIND in Quests.map_goals())
	Quests.read("The stone on Stone Point")
	Quests.read("The Starfall stone")
	_check("all three read: back to Aldous", Quests.stage(&"stones_remember") == 2 and Quests.marker_for(&"aldous") == "?")
	gold = GameState.currency
	Quests.talked_to(&"aldous")
	_check("Aldous's reward: gold and the Stonesong Charm", Quests.stage(&"stones_remember") == Quests.DONE
		and col.count(&"stonesong_charm") == 1 and GameState.currency == gold + Quests.STONES_REWARD_GOLD)
	# A kill favour past the west gate points the map at its own hunting ground.
	Errands.talked_to(&"tilly")
	_check("Tilly's rams send you to the plains", Errands.state(&"tilly_rams") == Errands.ASKED
		and WorldMap.AUREWIND in Quests.map_goals())
	for i in 3:
		EventBus.monster_defeated.emit(&"bristle_ram", GameState.PLAYER)
	Errands.talked_to(&"tilly")
	_check("three rams: Tilly's bell", col.count(&"shepherds_bell") >= 1 and Errands.state(&"tilly_rams") == Errands.DONE)
	# Sully, in the Frost Grotto: two lake trout (fished off Neri's dock) for a moss lantern.
	Errands.talked_to(&"sully")
	_check("Sully asks for trout", Errands.state(&"sully_trout") == Errands.ASKED)
	var lanterns := col.count(&"moss_lantern")
	GameState.add_item(&"lake_trout", 2)
	Errands.talked_to(&"sully")
	_check("two trout for a lantern", col.count(&"moss_lantern") == lanterns + 1 and GameState.item_count(&"lake_trout") == 0)
	# The west gate: the Warden's Verdant Crest opens the road to the plains.
	var gate := CardDatabase.get_gate(&"kalmora_west_gate")
	_check("Kalmora's west gate takes a Verdant Crest", gate != null and gate.cost_card_id == &"verdant_crest")
	var west := WorldMap.edges_from(WorldMap.KALMORA).filter(func(e: Dictionary) -> bool: return e.to == WorldMap.AUREWIND)
	_check("and it's the only way west", west.size() == 1 and west[0].gate == &"kalmora_west_gate"
		and not WorldMap.AUREWIND in WorldMap.reachable(WorldMap.KALMORA, GameState.PLAYER, false))
	# Frisalle: the pass toll takes a wolf collar; the ice road is the way round it.
	var toll := CardDatabase.get_gate(&"starfall_pass")
	_check("Frisalle's toll takes an Iron Wolf Collar", toll != null and toll.cost_card_id == &"iron_wolf_collar")
	var north := WorldMap.edges_from(WorldMap.STARFALL).filter(func(e: Dictionary) -> bool: return e.to == WorldMap.FRISALLE)
	var ice := WorldMap.edges_from(WorldMap.STARFALL_GROTTO).filter(func(e: Dictionary) -> bool: return e.to == WorldMap.FRISALLE)
	_check("the pass goes through the toll gate, the ice road doesn't", north.size() == 1 and north[0].gate == &"starfall_pass"
		and ice.size() == 1 and ice[0].gate == &"")
	# "The Merchant's Ledger": read three records (the square, the counting house,
	# Bodo's house), then back to Mirren.
	for title: String in Quests.LEDGER_CLUES:
		var place: Node = load(Quests.LEDGER_CLUES[title]).instantiate()
		_check("'%s' is in %s" % [title, place.name],
			place.get_children().any(func(n: Node) -> bool: return n is Readable and n.title == title))
		place.free()
	_check("Mirren has something to ask", Quests.marker_for(&"mirren") == "!")
	Quests.talked_to(&"mirren")
	_check("talking to Mirren starts it", Quests.stage(&"merchants_ledger") == 1 and "(0/3)" in Quests.tracker_text()
		and WorldMap.FRISALLE in Quests.map_goals())
	for title: String in Quests.LEDGER_CLUES:
		Quests.read(title)
	_check("all three read: back to Mirren", Quests.stage(&"merchants_ledger") == 2 and Quests.marker_for(&"mirren") == "?")
	gold = GameState.currency
	Quests.talked_to(&"mirren")
	_check("Mirren's reward: gold and the Factors' Seal", Quests.stage(&"merchants_ledger") == Quests.DONE
		and col.count(&"factors_seal") == 1 and GameState.currency == gold + Quests.LEDGER_REWARD_GOLD)
	# Ottilie wants a bowl of Chef's stew from Seabright.
	Errands.talked_to(&"ottilie")
	_check("Ottilie asks for Seabright Stew", Errands.state(&"ottilie_stew") == Errands.ASKED)
	GameState.add_item(&"seabright_stew", 1)
	Errands.talked_to(&"ottilie")
	_check("the stew for the hearthstone", col.count(&"frisalle_hearthstone") == 1 and GameState.item_count(&"seabright_stew") == 0)
	# "The Light on the Water" (Sparkle, once her dare's done): the lookout and Bungalow 3
	# only tell you anything after dark.
	_check("no Sparkle quest before her dare", Quests.marker_for(&"sparkle") != "!" or Errands.state(&"sparkle_dare") == Errands.DONE)
	GameState.quest_flags[&"errand:sparkle_dare"] = Errands.DONE
	_check("then Sparkle has something", Quests.marker_for(&"sparkle") == "!")
	Quests.talked_to(&"sparkle")
	_check("watch from the lookout", Quests.stage(&"light_on_water") == 1)
	Quests.read(Quests.LIGHT_LOOKOUT, false)
	_check("by day the telescope shows nothing", Quests.stage(&"light_on_water") == 1)
	Quests.read(Quests.LIGHT_LOOKOUT, true)
	Quests.read(Quests.LIGHT_DOOR, true)
	_check("at night: the light, then Bungalow 3", Quests.stage(&"light_on_water") == 3 and Quests.marker_for(&"sparkle") == "?")
	gold = GameState.currency
	Quests.talked_to(&"sparkle")
	_check("Sparkle's thanks", Quests.stage(&"light_on_water") == Quests.DONE and GameState.currency == gold + Quests.LIGHT_REWARD_GOLD)
	var seabright: Node = load(WorldMap.SEABRIGHT).instantiate()
	_check("the lookout and the door read differently at night", seabright.get_children().filter(func(n: Node) -> bool:
		return n is Readable and n.title in [Quests.LIGHT_LOOKOUT, Quests.LIGHT_DOOR] and not n.night_lines.is_empty()).size() == 2)
	seabright.free()
	# "What the Millstream Carries" (Oda, once she has her news from the lake).
	GameState.quest_flags[&"errand:oda_news"] = Errands.DONE
	_check("Oda has something more", Quests.marker_for(&"oda") == "!")
	Quests.talked_to(&"oda")
	var verdana: Node = load(WorldMap.VERDANA).instantiate()
	for title in Quests.MILLSTREAM_FINDS:
		_check("'%s' is in the reeds" % title, verdana.get_children().any(func(n: Node) -> bool: return n is Readable and n.title == title))
		Quests.read(title)
	verdana.free()
	_check("all three: back to Oda", Quests.stage(&"millstream") == 2 and Quests.marker_for(&"oda") == "?")
	Quests.talked_to(&"oda")
	_check("Oda's thanks", Quests.stage(&"millstream") == Quests.DONE)
	print("PASS" if _failures == 0 else "FAILED: %d check(s)" % _failures)
	get_tree().quit(1 if _failures else 0)


func _check(label: String, ok: bool) -> void:
	if not ok:
		_failures += 1
		print("  FAIL  ", label)
