extends Node
## The North Shaft under Duskara and its two quests. "Beneath the Dunes" (Rafi, after
## his tonic): through the tally gate (a Brass Tally Tag), Ada in the bunks follows you,
## out the crawl into the Bone Hollow and to Zahra at the Sunwell; Rafi gives the Green
## Lamp (rivals notice you half as fast). "The Foreman's Names" (Hesper): read the
## foreman's ledger of names in the lower office and bring it to her; Oda in Verdana
## hears about Corin afterwards.
## Run: godot --headless --path . res://tests/test_mine.tscn

const P := &"player"

var _failures := 0


func _ready() -> void:
	get_tree().current_scene = null
	_run.call_deferred()


func _run() -> void:
	RivalDirector.enabled = false
	TimeOfDay.paused = true
	TimeOfDay.set_hour(23.0)
	GameState.new_game(GameState.DEFAULT_RIVALS)
	_check("Rafi has nothing to ask before his favour", Quests.marker_for(&"rafi") != "!" or Errands.state(&"rafi_tonic") != Errands.DONE)
	GameState.quest_flags[&"errand:rafi_tonic"] = Errands.DONE
	_check("then he does", Quests.marker_for(&"rafi") == "!" and Quests.dialogue_for(&"rafi").size() >= 3)
	Quests.talked_to(&"rafi")
	_check("Beneath the Dunes starts", Quests.stage(&"beneath_dunes") == 1)

	var mine := await _load(WorldMap.DUSKARA_MINE)
	var gate := mine.get_node_or_null(^"Gate_duskara_tally_gate")
	_check("the tally gate stands at the landing, wanting a tag", gate != null
		and CardDatabase.get_gate(&"duskara_tally_gate") != null if CardDatabase.has_method(&"get_gate") else gate != null)
	var bunk := mine.get_node_or_null(^"Npc_ada") as Npc
	_check("Ada's in the bunks, with a '!'", bunk != null and Quests.marker_for(&"ada") == "!")
	Quests.talked_to(&"ada")
	await get_tree().process_frame
	var ada := mine.get_node_or_null(^"Escort_ada") as Npc
	_check("she follows you", Quests.stage(&"beneath_dunes") == 2 and ada != null and ada.follow_player)
	var player := get_tree().get_first_node_in_group(&"player") as Node2D
	ada.global_position = player.global_position + Vector2(0, -150)
	for i in 90:
		await get_tree().physics_frame
	_check("and keeps up", ada.global_position.distance_to(player.global_position) < 90.0)
	_check("the way out to the dunes is the escape crawl", (mine.get_node(^"ToDunes") as ZoneExit).target_scene == WorldMap.SIROTH)

	var dunes := await _load(WorldMap.SIROTH)
	_check("she comes up into the dunes with you", dunes.get_node_or_null(^"Escort_ada") != null)
	_check("Zahra is waiting for her", Quests.marker_for(&"zahra") == "?")
	Quests.talked_to(&"zahra")
	await get_tree().process_frame
	_check("Ada goes with the caravan", Quests.stage(&"beneath_dunes") == 3 and dunes.get_node_or_null(^"Escort_ada") == null)
	var gold := GameState.currency
	Quests.talked_to(&"rafi")
	_check("Rafi gives the Green Lamp", Quests.stage(&"beneath_dunes") == Quests.DONE
		and GameState.collection(P).count(CardSpells.GREEN_LAMP) == 1 and GameState.currency == gold + Quests.ADA_REWARD_GOLD)
	var mine2 := await _load(WorldMap.DUSKARA_MINE)
	_check("her bunk is empty afterwards", mine2.get_node_or_null(^"Npc_ada") == null or mine2.get_node(^"Npc_ada").is_queued_for_deletion())

	# The Foreman's Names.
	Quests.talked_to(&"hesper")   # (her welcome gift first)
	_check("Hesper has a quest once she's given her gift", Quests.marker_for(&"hesper") == "!")
	Quests.talked_to(&"hesper")
	_check("The Foreman's Names starts", Quests.stage(&"foremans_names") == 1 and Quests.wants(Quests.NAMES_LEDGER))
	Quests.read(Quests.NAMES_LEDGER)
	_check("reading the ledger is enough", Quests.stage(&"foremans_names") == 2 and Quests.marker_for(&"hesper") == "?")
	Quests.talked_to(&"hesper")
	_check("Hesper takes the names", Quests.stage(&"foremans_names") == Quests.DONE)
	GameState.quest_flags[&"quest:millstream"] = Quests.DONE
	GameState.quest_flags[&"errand:oda_news"] = Errands.DONE
	_check("and Oda hears about Corin", "Transferred" in " ".join(Quests.dialogue_for(&"oda")))

	# The Green Lamp, worn.
	var rival: Rival = load("res://scenes/characters/rival.tscn").instantiate()
	rival.apply_profile(GameState.rival_profile(GameState.active_rivals[0]))
	mine2.add_child(rival)
	var me := get_tree().get_first_node_in_group(&"player") as Node2D
	rival.global_position = me.global_position + Vector2(0, -40)
	await get_tree().process_frame
	var plain := rival.awareness.perceived_gain(me)
	GameState.equip(CardSpells.GREEN_LAMP)
	_check("wearing the Green Lamp, rivals notice you half as fast", plain > 0.0 and is_equal_approx(rival.awareness.perceived_gain(me), plain * 0.5))
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
