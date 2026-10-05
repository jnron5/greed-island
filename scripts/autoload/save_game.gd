extends Node
## The run, saved: every collector's cards (with their states), gold, satchel, quests
## and favours, opened gates and chests, bosses, rivals and where they are, the
## journal, the time of day, and where the player stands. Saved automatically each
## time the player arrives somewhere (EventBus.area_entered), and continued from the
## title screen. One slot, in user://.

const PATH := "user://savegame.dat"
const VERSION := 1

## The file in use (the test suite points this elsewhere).
var path := PATH

## Where to put the player once the saved zone has loaded (null = its spawn).
var pending_position: Variant = null

var _suspended := false


func _ready() -> void:
	EventBus.area_entered.connect(func(_title: String, _interior: bool) -> void: save.call_deferred())


func has_save() -> bool:
	return FileAccess.file_exists(path)


## Tests and the title screen stop autosaving while they poke at the state.
func suspend(on: bool) -> void:
	_suspended = on


func save(force := false) -> void:
	# Headless runs are the test suites: they must never overwrite a real save.
	if not force and (_suspended or DisplayServer.get_name() == "headless"):
		return
	var zone := get_tree().current_scene
	var player := get_tree().get_first_node_in_group(&"player") as Node2D
	if not (zone is Zone) or player == null or zone.scene_file_path == "":
		return
	var cards := {}
	for id in GameState.collections:
		var col: CardCollection = GameState.collections[id]
		var held := {}
		for card_id in col.card_ids():
			held[card_id] = [col.count(card_id, 0), col.count(card_id, 1), col.count(card_id, 2)]
		cards[id] = held
	var data := {
		"version": VERSION,
		"zone": zone.scene_file_path,
		"position": player.global_position,
		"health": player.get(&"health"),
		"hour": TimeOfDay.hour,
		"day": TimeOfDay.day,
		"rivals": GameState.active_rivals,
		"cards": cards,
		"currency": GameState.currency,
		"items": GameState.items,
		"quest_flags": GameState.quest_flags,
		"opened_gates": GameState.opened_gates,
		"world_supply": GameState.world_supply,
		"rival_locations": GameState.rival_locations,
		"bosses": GameState.bosses,
		"collected_pickups": GameState.collected_pickups,
		"zone_drops": GameState.zone_drops,
		"seen_cards": GameState.seen_cards,
		"journal": GameState.journal,
		"equipped": GameState.equipped,
		"spent_on_gates": GameState.spent_on_gates,
	}
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file:
		file.store_string(var_to_str(data))


## Loads the saved run and goes to where the player was. False if there is no
## readable save.
func continue_game() -> bool:
	if not has_save():
		return false
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return false
	var data: Variant = str_to_var(file.get_as_text())
	if not (data is Dictionary) or data.get("version", 0) != VERSION:
		return false
	var rivals: Array[StringName] = []
	rivals.assign(data.rivals)
	GameState.new_game(rivals)
	for id: StringName in data.cards:
		var col := GameState.collection(id)
		if col == null:
			continue
		for card_id: StringName in data.cards[id]:
			var counts: Array = data.cards[id][card_id]
			for state in 3:
				if counts[state] > 0:
					col.add(card_id, state, counts[state])
	GameState.currency = data.currency
	GameState.items.assign(data.items)
	GameState.quest_flags.assign(data.quest_flags)
	GameState.opened_gates.assign(data.opened_gates)
	GameState.world_supply.assign(data.world_supply)
	GameState.rival_locations.assign(data.rival_locations)
	GameState.bosses.assign(data.bosses)
	GameState.collected_pickups.assign(data.collected_pickups)
	GameState.zone_drops.assign(data.zone_drops)
	GameState.seen_cards.assign(data.seen_cards)
	GameState.journal.assign(data.journal)
	GameState.equipped.assign(data.get("equipped", []))
	GameState.spent_on_gates.assign(data.get("spent_on_gates", {}))
	TimeOfDay.set_hour(data.hour)
	TimeOfDay.day = int(data.get("day", 0))
	GameState.pending_spawn = &""
	pending_position = data.position
	pending_health = data.get("health", null)
	EventBus.currency_changed.emit(GameState.currency)
	EventBus.items_changed.emit()
	GameState._emit_tracker()
	Transition.go(data.zone)
	return true


## The player's health when the save was made (applied by Zone on arrival).
var pending_health: Variant = null


## Zone calls this once the player is in the scene.
func place_player(player: Node2D) -> void:
	if pending_position is Vector2:
		player.global_position = pending_position
	if pending_health is int and player.get(&"health") != null:
		player.set(&"health", pending_health)
		if player.has_signal(&"health_changed"):
			player.emit_signal(&"health_changed", pending_health, player.get(&"max_health"))
	pending_position = null
	pending_health = null


func delete() -> void:
	if has_save():
		DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
