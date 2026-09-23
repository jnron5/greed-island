class_name Binder
extends MenuPanel
## The player's collection. Bind loose cards to protect them (instant in towns,
## slower in the field), take bound cards out (exposed), cast spells, lock cards.

## card id -> true while a field bind is in progress
var _binding: Dictionary[StringName, bool] = {}


func _init() -> void:
	title = "Binder"
	toggle_action = &"binder"


func _status_text() -> String:
	var progress: int = GameState.tracker_counts().get(GameState.PLAYER, 0)
	var where := "In town: binding is instant." if GameState.is_in_safe_zone(GameState.PLAYER) \
		else "In the field: binding takes %.1fs per card." % GameState.FIELD_BIND_TIME
	return "Set %d/%d   %s   Loose and exposed cards can be stolen; bound cards are safe." \
		% [progress, CardDatabase.final_set().size(), where]


func _build_rows() -> void:
	var col := GameState.collection(GameState.PLAYER)
	var ids := col.card_ids()
	if ids.is_empty():
		add_header("No cards yet. Pick some up around Kalmora.")
		return
	ids.sort_custom(func(a: StringName, b: StringName) -> bool:
		var ca := CardDatabase.get_card(a)
		var cb := CardDatabase.get_card(b)
		if ca.category != cb.category:
			return ca.category < cb.category
		return ca.display_name < cb.display_name)

	var has_lockbox := col.count(CardSpells.LOCKBOX) > 0
	var last_group := ""
	for id in ids:
		var card := CardDatabase.get_card(id)
		var group := "Set cards" if card.category == CardData.Category.SET else "Spells & buffs"
		if group != last_group:
			last_group = group
			add_header(group)
		var loose := col.count(id, CardCollection.State.LOOSE)
		var bound := col.count(id, CardCollection.State.BOUND)
		var exposed := col.count(id, CardCollection.State.EXPOSED)
		var detail := "loose %d  bound %d  exposed %d" % [loose, bound, exposed]
		if GameState.is_locked(GameState.PLAYER, id):
			detail += "  [locked %ds]" % ceili(GameState.lock_time_left(GameState.PLAYER, id))

		var buttons: Array = []
		if _binding.has(id):
			buttons.append(["Binding...", func() -> void: pass, false])
		elif loose > 0:
			buttons.append(["Bind", _bind.bind(id, CardCollection.State.LOOSE), true])
		if exposed > 0 and not _binding.has(id):
			buttons.append(["Put back", _bind.bind(id, CardCollection.State.EXPOSED), true])
		if bound > 0:
			buttons.append(["Take out", func() -> void: GameState.expose_card(GameState.PLAYER, id), true])
		if id == CardSpells.PICKPOCKET:
			buttons.append(["Cast (Q)", _cast_pickpocket, true])
		elif id == CardSpells.SECOND_WIND:
			buttons.append(["Use", _use_second_wind, true])
		elif has_lockbox and id != CardSpells.LOCKBOX:
			var can_lock := GameState.stealable_copies(GameState.PLAYER, id) > 0 \
				and not GameState.is_locked(GameState.PLAYER, id)
			buttons.append(["Lock", func() -> void: CardSpells.use_lockbox(GameState.PLAYER, id), can_lock])
		add_row(card.display_name, card_color(card), detail, buttons)


## Loose -> Bound or Exposed -> Bound, after the bind time for where the player stands.
func _bind(id: StringName, from: CardCollection.State) -> void:
	var delay := GameState.bind_time(GameState.PLAYER)
	if delay > 0.0:
		_binding[id] = true
		rebuild()
		await get_tree().create_timer(delay).timeout
		_binding.erase(id)
	GameState.change_state(GameState.PLAYER, id, from, CardCollection.State.BOUND)
	rebuild()


func _cast_pickpocket() -> void:
	var player := get_tree().get_first_node_in_group(&"player") as Player
	if player:
		CardSpells.cast_pickpocket(player)


func _use_second_wind() -> void:
	var player := get_tree().get_first_node_in_group(&"player") as Player
	if player and CardSpells.use_second_wind(player):
		EventBus.notify.emit("Second Wind: +%d HP" % CardSpells.SECOND_WIND_HEAL)
