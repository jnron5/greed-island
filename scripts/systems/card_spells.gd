class_name CardSpells
extends RefCounted
## Effects for spell and temporary buff cards. Shared by the player and rivals:
## `caster` is any node in the "collectors" group with a `collector_id`.

const PICKPOCKET := &"pickpockets_whisper"
const LOCKBOX := &"lockbox_seal"
const SECOND_WIND := &"second_wind"

const PICKPOCKET_RANGE := 110.0
const SECOND_WIND_HEAL := 3

## Sold in Duskara's card souk. Spells:
const MIRAGE := &"mirage_veil"          # rivals lose sight of you for a while
const DUST_DEVIL := &"dust_devil"       # a whirl of sand stuns everyone close
## Temporary buffs (boons):
const SCARAB_FURY := &"scarab_fury"     # sword hits harder
const GLASS_SKIN := &"glass_skin"       # nothing hurts you, briefly
const SWIFTSAND := &"swiftsand_draught" # you run faster
## Passive charms:
const SCARAB_WARD := &"scarab_ward"     # a hit sometimes turns aside
const PROSPECTOR := &"prospectors_charm" # monsters drop more gold
const BOON_SECONDS := {MIRAGE: 20.0, SCARAB_FURY: 30.0, GLASS_SKIN: 6.0, SWIFTSAND: 30.0}
const DUST_DEVIL_RANGE := 130.0
const DUST_DEVIL_STUN := 2.5
const SCARAB_FURY_BONUS := 2
const SWIFTSAND_SPEED := 1.4
const SCARAB_WARD_CHANCE := 0.25
const PROSPECTOR_GOLD := 1.5


## Whether a card is used from the binder with "Use" (a spell or a buff the
## collector spends on themselves).
static func is_usable(card_id: StringName) -> bool:
	return card_id == SECOND_WIND or card_id == DUST_DEVIL or BOON_SECONDS.has(card_id) or is_return(card_id)


## Uses a card from the binder: spends it and starts its effect. False (and the
## card kept) when it can't be used right now.
static func use(caster: Node2D, card_id: StringName) -> bool:
	var caster_id: StringName = caster.get(&"collector_id")
	if card_id == SECOND_WIND:
		return use_second_wind(caster)
	if is_return(card_id):
		return use_return(caster, card_id)
	if card_id == DUST_DEVIL:
		return cast_dust_devil(caster)
	if not BOON_SECONDS.has(card_id) or not GameState.consume_card(caster_id, card_id, &"buff"):
		return false
	GameState.add_boon(caster_id, card_id, BOON_SECONDS[card_id])
	var card := CardDatabase.get_card(card_id)
	_tell(caster_id, "%s: %ds" % [card.display_name if card else String(card_id), int(BOON_SECONDS[card_id])])
	EventBus.spell_cast.emit(caster_id, card_id, &"")
	return true


## Dust Devil: a whirl of sand round the caster. Every rival and monster close by is
## blinded and staggered for a moment (they can't move, strike or steal).
static func cast_dust_devil(caster: Node2D) -> bool:
	var caster_id: StringName = caster.get(&"collector_id")
	if not GameState.consume_card(caster_id, DUST_DEVIL, &"spell"):
		return false
	var hit := 0
	for group in [&"collectors", &"monsters"]:
		for node in caster.get_tree().get_nodes_in_group(group):
			var n := node as Node2D
			if n == null or n == caster or not n.has_method(&"stun"):
				continue
			if n.global_position.distance_to(caster.global_position) <= DUST_DEVIL_RANGE \
					and Zone.same_level(caster.get_tree(), caster.global_position, n.global_position):
				n.stun(DUST_DEVIL_STUN)
				hit += 1
	Sfx.play(&"whirl")
	var whirl := DustDevilFx.new()
	whirl.position = caster.position
	caster.get_parent().add_child(whirl)
	EventBus.spell_cast.emit(caster_id, DUST_DEVIL, &"")
	_tell(caster_id, "Dust Devil! %d caught in the sand" % hit if hit else "Dust Devil! Nobody close enough")
	return true


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
	&"duskara_return": WorldMap.DUSKARA,
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
