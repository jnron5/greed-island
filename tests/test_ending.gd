extends Node
## The end of the race. Freya's "An Audience Before the Throne" (two of the quests
## that follow the carts done: read the Throne Ledger, tell her); the Steward counts
## the whole set and the King steps out (Ending.crown); which endings are open
## (Ending.choices: closing the North Shaft needs both mine quests and the audience);
## the ending pages for each; and a rival with the whole set heading for Vetrassa and
## winning the race when they get there.
## Run: godot --headless --path . res://tests/test_ending.tscn

const P := &"player"
const SCREEN := preload("res://scripts/ui/ending_screen.gd")

var _failures := 0


func _ready() -> void:
	get_tree().current_scene = null
	_run.call_deferred()


func _run() -> void:
	RivalDirector.enabled = false
	Ending.show_scene = false
	TimeOfDay.paused = true
	GameState.new_game(GameState.DEFAULT_RIVALS)

	# An Audience Before the Throne.
	_check("Freya has nothing to ask of a newcomer", Quests.marker_for(&"freya") == "" and Quests.dialogue_for(&"freya").is_empty())
	Quests.set_stage(&"merchants_ledger", Quests.DONE)
	_check("one quest that follows the carts isn't enough", not Quests.audience_ready())
	Quests.set_stage(&"light_on_water", Quests.DONE)
	_check("two are: Freya has a '!'", Quests.audience_ready() and Quests.marker_for(&"freya") == "!"
		and Quests.dialogue_for(&"freya").size() >= 3)
	Quests.talked_to(&"freya")
	_check("the audience starts", Quests.stage(&"audience_throne") == 1 and Quests.wants(Quests.THRONE_LEDGER))
	Quests.read(Quests.THRONE_LEDGER)
	_check("reading the Throne Ledger sends you back to her", Quests.stage(&"audience_throne") == 2 and Quests.marker_for(&"freya") == "?")
	var gold := GameState.currency
	Quests.talked_to(&"freya")
	_check("and she pays you for it", Quests.stage(&"audience_throne") == Quests.DONE and GameState.currency == gold + Quests.AUDIENCE_REWARD_GOLD)

	# The Guest List (Sassy): the royal family all decline; Sully writes back.
	_check("Sassy waits until she's given you the card from her hat", Quests.marker_for(&"sassy") != "!")
	GameState.quest_flags[&"errand:sassy_gift"] = Errands.DONE
	_check("then she has invitations", Quests.marker_for(&"sassy") == "!" and Quests.dialogue_for(&"sassy").size() >= 3)
	Quests.talked_to(&"sassy")
	_check("the guest list starts", Quests.stage(&"guest_list") == 1)
	_check("Sully can take the blank envelope", Quests.marker_for(&"sully") == "!")
	Quests.talked_to(&"sully")
	Quests.took_over = false
	_check("and writes on the back of it", Quests.flag(&"invite:sully") and Quests.marker_for(&"sully") == "")
	for guest: StringName in Quests.GUESTS:
		_check("%s has an invitation coming, and declines it" % guest, Quests.marker_for(guest) == "!"
			and Quests.dialogue_for(guest) == PackedStringArray(Quests.GUEST_DECLINES[guest]))
		Quests.talked_to(guest)
		Quests.took_over = false
	_check("all four delivered sends you back to Sassy", Quests.stage(&"guest_list") == 2 and Quests.marker_for(&"sassy") == "?")
	var purse := GameState.currency
	Quests.talked_to(&"sassy")
	_check("she pays you for the walking", Quests.stage(&"guest_list") == Quests.DONE and GameState.currency == purse + Quests.GUEST_REWARD_GOLD)
	Quests.set_stage(&"guest_list", Quests.NOT_STARTED)
	GameState.quest_flags.erase(&"errand:sassy_gift")

	# Which endings are open.
	_check("only ruling as kings always have, knowing nothing of the mine", _ids() == [Ending.RULE])
	Quests.set_stage(&"foremans_names", Quests.DONE)
	_check("the names open paying the laborers", _ids() == [Ending.RULE, Ending.WAGES])
	Quests.set_stage(&"beneath_dunes", Quests.DONE)
	_check("both mine quests and the audience open closing the shaft", _ids() == [Ending.RULE, Ending.WAGES, Ending.CLOSE])

	# The Steward counts the set.
	_check("without the set, no turn-in", not Ending.has_set(P) and Quests.marker_for(&"steward") == "")
	for card: CardData in CardDatabase.final_set():
		for i in card.final_set_count:
			GameState.add_loose_card(P, card.id)
	_check("with the whole set, the Steward has a '?'", Ending.has_set(P) and Quests.marker_for(&"steward") == "?"
		and Quests.dialogue_for(&"steward").size() >= 3)
	var throne := await _load(WorldMap.VETRASSA_PALACE)
	_check("the Steward waits in the throne room", throne.get_node_or_null(^"Npc_steward") != null)
	Quests.talked_to(&"steward")
	await get_tree().process_frame
	var king := throne.get_node_or_null(^"King") as Npc
	_check("handing it in, the King steps out beside the throne", GameState.quest_flags.get(&"crowned", false) and king != null and king.display_name == "Loki")
	Ending.finish(get_tree(), Ending.CLOSE)
	_check("choosing ends the race: the player won, the shaft closed", Ending.is_over()
		and GameState.quest_flags.get(&"ending") == Ending.CLOSE and GameState.quest_flags.get(&"winner") == P)

	# The ending pages.
	for ending: StringName in [Ending.RULE, Ending.WAGES, Ending.CLOSE]:
		var pages: Array[Dictionary] = SCREEN.pages(ending, P, GameState.DEFAULT_RIVALS)
		_check("the %s ending has its pages, the two rivals' fates among them" % ending, pages.size() >= 5
			and pages.any(func(p: Dictionary) -> bool: return p.title == "The other racers" and "Raider" in p.text and "Runner" in p.text))
	for rival: StringName in GameState.RIVALS:
		var lost: Array[Dictionary] = SCREEN.pages(Ending.LOST, rival, GameState.DEFAULT_RIVALS)
		_check("losing to the %s has its pages" % rival, lost.size() >= 3)
	for p: Dictionary in SCREEN.pages(Ending.WAGES, P, GameState.DEFAULT_RIVALS):
		if p.art != "":
			_check("art for '%s' exists" % p.title, ResourceLoader.exists("res://assets/ui/ending/%s.png" % p.art))

	# A rival wins the race.
	GameState.new_game(GameState.DEFAULT_RIVALS)
	for card: CardData in CardDatabase.final_set():
		for i in card.final_set_count:
			GameState.add_loose_card(&"runner", card.id)
	_check("a rival with the whole set heads for Vetrassa", RivalDirector.choose_destination(&"runner", WorldMap.FRISALLE) == WorldMap.VETRASSA
		and RivalDirector.choose_destination(&"runner", WorldMap.VETRASSA) == WorldMap.VETRASSA)
	_check("and the player hears of it", GameState.quest_flags.get(&"heading_home:runner", false))
	GameState.move_rival(&"runner", WorldMap.VETRASSA, Vector2(900, 0))
	RivalDirector.tick_rival(&"runner", 1.0)
	_check("and reaching it, wins the race", Ending.is_over() and GameState.quest_flags.get(&"ending") == Ending.LOST
		and GameState.quest_flags.get(&"winner") == &"runner")
	_check("the Raider without the set doesn't", not Ending.has_set(&"raider"))
	for r: StringName in GameState.RIVALS:
		_check("the %s has words for the last road, Duskara and Vetrassa" % r,
			RivalLines.greeting(r, WorldMap.KALMORA, true) == &"homeward" and RivalLines.pick(r, &"homeward") != ""
			and RivalLines.pick(r, RivalLines.greeting(r, WorldMap.DUSKARA, false)) != ""
			and RivalLines.pick(r, RivalLines.greeting(r, WorldMap.VETRASSA, false)) != "")
	GameState.new_game(GameState.DEFAULT_RIVALS)
	_check("a new game starts the race again", not Ending.is_over())

	print("PASS" if _failures == 0 else "FAILED: %d check(s)" % _failures)
	get_tree().quit(1 if _failures else 0)


func _ids() -> Array:
	return Ending.choices().map(func(c: Dictionary) -> StringName: return c.id)


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
