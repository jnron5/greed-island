extends Node
## The journal (the character menu's third page) and the one quest the HUD shows:
## starting a quest writes it in the journal and shows it; picking another in the
## journal shows that one instead; hiding it shows nothing; finished quests move to
## the finished list with what they came to; favours are in it too. Readables a
## running quest wants say so (Quests.wants).
## Run: godot --headless --path . res://tests/test_journal.tscn

var _failures := 0


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	RivalDirector.enabled = false
	GameState.new_game(GameState.DEFAULT_RIVALS)
	_check("an empty journal shows nothing", Quests.journal().is_empty() and Quests.tracked_text() == "")
	Quests.talked_to(&"pell")
	_check("a started quest is in the journal", Quests.journal().size() == 1 and Quests.journal()[0].id == &"trees_remember")
	_check("and on screen", Quests.tracked_text().begins_with("What the Trees Remember\n"))
	Quests.talked_to(&"aldous")
	_check("the newest quest shows", Quests.tracked_id() == &"stones_remember")
	_check("only one shows", Quests.tracked_text().count("\n") == 1)
	Quests.track(&"trees_remember")
	_check("picking one in the journal shows it", Quests.tracked_text().begins_with("What the Trees Remember"))
	Quests.track(&"none")
	_check("hiding it shows nothing", Quests.tracked_text() == "")
	Quests.track(&"trees_remember")
	_check("a stone a running quest wants is marked", Quests.wants("The Aurewind circle") or Quests.STONES.keys().any(
		func(t: String) -> bool: return Quests.wants(t)))
	Quests.read(Quests.SATCHEL_TITLE)
	Quests.talked_to(&"moss")
	var done := Quests.journal().filter(func(e: Dictionary) -> bool: return e.id == &"trees_remember")
	_check("a finished quest stays in the journal, finished", done.size() == 1 and done[0].done and done[0].step != "")
	_check("the screen moves on to a running one", Quests.tracked_id() == &"stones_remember")
	Errands.talked_to(&"pip")
	_check("a favour is in the journal", Quests.journal().any(func(e: Dictionary) -> bool: return e.id == &"errand:pip_bread"))
	print("PASS" if _failures == 0 else "FAILED: %d check(s)" % _failures)
	get_tree().quit(1 if _failures else 0)


func _check(label: String, ok: bool) -> void:
	if not ok:
		_failures += 1
		print("  FAIL  ", label)
