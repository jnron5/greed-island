class_name CardSpells
extends RefCounted
## Effects for spell and temporary buff cards. Shared by the player and rivals:
## `caster` is any node in the "collectors" group with a `collector_id`.

const PICKPOCKET := &"pickpockets_whisper"
const LOCKBOX := &"lockbox_seal"
const SECOND_WIND := &"second_wind"

const PICKPOCKET_RANGE := 110.0
const SECOND_WIND_HEAL := 3


## Pickpocket's Whisper: guaranteed steal of one random loose card from the
## nearest collector in range. Consumed on use. Returns the stolen card id,
## or &"" if nothing was cast (the spell is kept).
static func cast_pickpocket(caster: Node2D) -> StringName:
	var caster_id: StringName = caster.get(&"collector_id")
	var col := GameState.collection(caster_id)
	if col == null or col.count(PICKPOCKET) == 0:
		_tell(caster_id, "No Pickpocket's Whisper to cast")
		return &""

	var in_range := collectors_in_range(caster, PICKPOCKET_RANGE)
	if in_range.is_empty():
		_tell(caster_id, "No collector in range")
		return &""
	var target: Node2D = null
	var in_grace := 0.0
	for node in in_range:
		var id: StringName = node.get(&"collector_id")
		if GameState.stealable_card_ids(id, CardCollection.LOOSE_ONLY).is_empty():
			continue
		if GameState.grace_left(id) > 0.0:
			in_grace = maxf(in_grace, GameState.grace_left(id))
			continue
		target = node
		break
	if target == null:
		if in_grace > 0.0:
			_tell(caster_id, "They were just robbed. Wait %ds" % ceili(in_grace))
		else:
			_tell(caster_id, "Nobody nearby is carrying loose cards")
		return &""

	var target_id: StringName = target.get(&"collector_id")
	var card_id: StringName = GameState.stealable_card_ids(target_id, CardCollection.LOOSE_ONLY).pick_random()
	# Spend the spell first so it can never be the card that moves.
	GameState.consume_card(caster_id, PICKPOCKET, &"spell")
	GameState.steal_card(caster_id, target_id, card_id, &"spell", CardCollection.LOOSE_ONLY)
	EventBus.spell_cast.emit(caster_id, PICKPOCKET, target_id)
	CardFx.fly(target, caster)
	return card_id


## Lockbox Seal: protects one copy of `card_id` from theft for a while.
static func use_lockbox(caster_id: StringName, card_id: StringName) -> bool:
	if not GameState.lock_card(caster_id, card_id, LOCKBOX):
		return false
	var card := CardDatabase.get_card(card_id)
	_tell(caster_id, "%s is locked for %ds" % [card.display_name, int(GameState.LOCKBOX_SECONDS)])
	return true


## Second Wind: instant heal. Consumed on use.
static func use_second_wind(caster: Node2D) -> bool:
	var caster_id: StringName = caster.get(&"collector_id")
	if not caster.has_method(&"heal") or not GameState.consume_card(caster_id, SECOND_WIND, &"buff"):
		return false
	caster.heal(SECOND_WIND_HEAL)
	return true


## Return cards: one per town, sold at that town's card shop. Used from the binder,
## the card is spent and carries you to the town's square (a fade through light).
const RETURN_CARDS := {
	&"kalmora_return": WorldMap.KALMORA,
	&"sorenda_return": WorldMap.SORENDA,
	&"verdana_return": WorldMap.VERDANA,
	&"seabright_return": WorldMap.SEABRIGHT,
	&"frisalle_return": WorldMap.FRISALLE,
}


static func is_return(card_id: StringName) -> bool:
	return RETURN_CARDS.has(card_id)


## The return card a town's shops sell (&"" if the town has none).
static func return_card_for(town: String) -> StringName:
	for id: StringName in RETURN_CARDS:
		if RETURN_CARDS[id] == town:
			return id
	return &""


## Spend a return card and go to its town. Refused (and kept) if you're already
## there, fainted, or mid-transition.
static func use_return(caster: Node2D, card_id: StringName) -> bool:
	var caster_id: StringName = caster.get(&"collector_id")
	var town: String = RETURN_CARDS.get(card_id, "")
	if town == "" or caster_id != GameState.PLAYER:
		return false
	var tree := caster.get_tree()
	if tree.current_scene and tree.current_scene.scene_file_path == town:
		_tell(caster_id, "You're already in %s" % WorldMap.town_name(town))
		return false
	if Transition.busy or int(caster.get(&"health")) <= 0:
		return false
	if not GameState.consume_card(caster_id, card_id, &"buff"):
		return false
	_tell(caster_id, "The %s carries you home" % CardDatabase.get_card(card_id).display_name)
	Sfx.play(&"charged")
	GameState.pending_spawn = WorldMap.town_spawn(town)
	Transition.faint_to(town)
	return true


## Other collectors within `radius` of `caster`, nearest first.
static func collectors_in_range(caster: Node2D, radius: float) -> Array[Node2D]:
	var out: Array[Node2D] = []
	for node in caster.get_tree().get_nodes_in_group(&"collectors"):
		if node != caster and node is Node2D and caster.global_position.distance_to(node.global_position) <= radius 				and Zone.same_level(caster.get_tree(), caster.global_position, node.global_position):
			out.append(node)
	out.sort_custom(func(a: Node2D, b: Node2D) -> bool:
		return caster.global_position.distance_squared_to(a.global_position) \
			< caster.global_position.distance_squared_to(b.global_position))
	return out


static func _tell(collector: StringName, text: String) -> void:
	if collector == GameState.PLAYER:
		EventBus.notify.emit(text)
