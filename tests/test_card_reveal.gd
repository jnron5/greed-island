extends Node
## Headless test of the first-card reveal: the player's first copy of a card pops it
## up and pauses the game; dismissing resumes; later copies and rivals' cards don't.
## Run: godot --headless --path . res://tests/test_card_reveal.tscn

const P := &"player"

var _failures := 0


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	RivalDirector.enabled = false
	GameState.new_game(GameState.DEFAULT_RIVALS)
	CardReveal.force = true
	var tide_bell := CardDatabase.get_card(&"tide_bell")
	_check("tide bell has art and lore", tide_bell != null and tide_bell.icon != null and tide_bell.lore != "")

	GameState.add_loose_card(&"runner", &"tide_bell")
	await get_tree().process_frame
	_check("a rival's card doesn't pop up", not CardReveal.showing)

	GameState.add_loose_card(P, &"tide_bell")
	await get_tree().process_frame
	_check("first tide bell pops up", CardReveal.showing and CardReveal.visible)
	_check("game paused while shown", get_tree().paused)
	_check("player input frozen", GameState.menus_open == 1)

	_check("front shows the description", CardReveal._view._text.text == tide_bell.description)
	await CardReveal.flip()
	_check("E turns it over to the lore", CardReveal._view.showing_back and CardReveal._view._lore.text == tide_bell.lore)
	await CardReveal.flip()
	_check("and back again", not CardReveal._view.showing_back)
	await CardReveal.dismiss()
	_check("dismissed", not CardReveal.showing and not CardReveal.visible)
	_check("game resumed", not get_tree().paused and GameState.menus_open == 0)

	GameState.add_loose_card(P, &"tide_bell")
	await get_tree().process_frame
	_check("second tide bell doesn't pop up", not CardReveal.showing)

	GameState.add_loose_card(P, &"sea_glass")
	GameState.add_loose_card(P, &"coral_coin")
	await get_tree().process_frame
	_check("two new cards: first shown", CardReveal.showing)
	await CardReveal.dismiss()
	await get_tree().process_frame
	_check("two new cards: second queued", CardReveal.showing)
	await CardReveal.dismiss()
	_check("queue empty, game resumed", not CardReveal.showing and not get_tree().paused)

	GameState.new_game(GameState.DEFAULT_RIVALS)
	_check("new game forgets seen cards", GameState.seen_cards.is_empty())
	CardReveal.force = false
	print("PASS" if _failures == 0 else "FAILED: %d check(s)" % _failures)
	get_tree().quit(1 if _failures else 0)


func _check(label: String, ok: bool) -> void:
	if not ok:
		_failures += 1
		print("  FAIL: ", label)
