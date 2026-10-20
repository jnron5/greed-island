extends Node
## Halmeer, the last port on the south coast. "The Smuggler's Route" (Nessa at the
## cape light): the tide board, the salt house door and the barge's log in the sea
## cave, then back to her for the Keeper's Lamp (by night, savage beasts see and hit
## a wearer no harder than by day). Ferro's and Grisel's favours, Maudie's welcome
## gift, and the road to and from Seabright.
## Run: godot --headless --path . res://tests/test_halmeer.tscn

const P := &"player"

var _failures := 0


func _ready() -> void:
	get_tree().current_scene = null
	_run.call_deferred()


func _run() -> void:
	RivalDirector.enabled = false
	TimeOfDay.paused = true
	GameState.new_game(GameState.DEFAULT_RIVALS)

	_check("Halmeer is a town with an inn", WorldMap.is_town(WorldMap.HALMEER) and WorldMap.inn_of(WorldMap.HALMEER) == WorldMap.HALMEER_INN)
	_check("the cliff road joins it to Seabright both ways",
		not WorldMap.next_hop(WorldMap.SEABRIGHT, WorldMap.HALMEER, P, true).is_empty()
		and not WorldMap.next_hop(WorldMap.HALMEER, WorldMap.SEABRIGHT, P, true).is_empty())
	_check("Maudie gives the Halmeer Return", Quests.gift_waiting(&"maudie") and Quests.WELCOME_GIFTS[&"maudie"] == &"halmeer_return"
		and CardSpells.RETURN_CARDS.get(&"halmeer_return") == WorldMap.HALMEER)

	# The Smuggler's Route.
	_check("Nessa has a '!'", Quests.marker_for(&"nessa") == "!" and Quests.dialogue_for(&"nessa").size() >= 3)
	Quests.talked_to(&"nessa")
	_check("the route starts", Quests.stage(&"smugglers_route") == 1)
	for title: String in Quests.SMUGGLER_CLUES:
		_check("'%s' is wanted" % title, Quests.wants(title))
		Quests.read(title)
	_check("all three found sends you back to Nessa", Quests.stage(&"smugglers_route") == 2 and Quests.marker_for(&"nessa") == "?")
	var gold := GameState.currency
	Quests.talked_to(&"nessa")
	_check("she pays you and gives you her lamp", Quests.stage(&"smugglers_route") == Quests.DONE
		and GameState.currency == gold + Quests.SMUGGLER_REWARD_GOLD
		and GameState.collection(P).count(CardSpells.KEEPERS_LAMP) == 1)
	_check("the route counts toward Freya's audience", Quests.AUDIENCE_NEEDS.has(&"smugglers_route"))

	# The town, its people and its favours.
	var town := await _load(WorldMap.HALMEER)
	for node: String in ["Npc_ferro", "Npc_grisel"]:
		_check("%s is on the quay" % node, town.get_node_or_null(NodePath(node)) != null)
	_check("Ferro's favour is a lemon tart, for the Fisher's Float", Errands.ERRANDS[&"ferro_tart"].card == &"fishers_float")
	_check("Grisel's favour is a sea-salt elixir, for the Bill of Lading", Errands.ERRANDS[&"grisel_elixir"].card == &"bill_of_lading")
	for id: StringName in [&"fishers_float", &"smugglers_knot", &"bill_of_lading"]:
		var card := CardDatabase.get_card(id)
		_check("%s is in the final set, with its art" % id, card != null and card.is_final_set_member and card.icon != null)

	# The Keeper's Lamp against a savage beast.
	var beast := town.find_children("*", "Monster", true, false)
	if beast.is_empty():
		var other := await _load(WorldMap.THORNVEIL)
		beast = other.find_children("*", "Monster", true, false)
	var m := beast[0] as Monster
	TimeOfDay.set_hour(23.0)
	m._update_night()
	var player := get_tree().get_first_node_in_group(&"player") as Node2D
	var keen := m._aggro_for(player)
	GameState.equip(CardSpells.KEEPERS_LAMP)
	_check("by night a savage beast sees a lamp-wearer no sooner than by day", m.night and m._aggro_for(player) < keen)

	print("PASS" if _failures == 0 else "FAILED: %d check(s)" % _failures)
	get_tree().quit(1 if _failures else 0)


func _load(path: String) -> Zone:
	get_tree().change_scene_to_file(path)
	await get_tree().process_frame
	while get_tree().current_scene == null or get_tree().current_scene.scene_file_path != path:
		await get_tree().process_frame
	await get_tree().physics_frame
	await get_tree().physics_frame
	return get_tree().current_scene as Zone


func _check(label: String, ok: bool) -> void:
	print("  %s  %s" % ["ok  " if ok else "FAIL", label])
	if not ok:
		_failures += 1
