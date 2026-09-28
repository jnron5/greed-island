extends Node
## Headless test of Sorenda's "What the Trees Remember": Pell starts it, reading the
## satchel in the Hollow moves it on, Elder Moss finishes it with gold and tonics; the
## satchel really is in Sorenda under that title, and the HUD tracks each step.
## Run: godot --headless --path . res://tests/test_quests.tscn

var _failures := 0


func _ready() -> void:
	_run.call_deferred()


func _run() -> void:
	RivalDirector.enabled = false
	GameState.new_game(GameState.DEFAULT_RIVALS)
	var sorenda: Node = load("res://scenes/world/sorenda.tscn").instantiate()
	var satchel := false
	for node in sorenda.get_children():
		if node is Readable and node.title == Quests.SATCHEL_TITLE:
			satchel = true
	sorenda.free()
	_check("the satchel is in Sorenda", satchel)
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
	_check("reward: gold and two tonics", GameState.currency == gold + Quests.TREES_REWARD_GOLD
		and GameState.item_count(&"healers_tonic") == tonics + 2)
	_check("nothing left to track", not "Trees" in Quests.tracker_text())
	print("PASS" if _failures == 0 else "FAILED: %d check(s)" % _failures)
	get_tree().quit(1 if _failures else 0)


func _check(label: String, ok: bool) -> void:
	if not ok:
		_failures += 1
		print("  FAIL  ", label)
