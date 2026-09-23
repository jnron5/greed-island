extends Node
## Run state: every collector's cards, currency, quest flags, opened gates,
## live world supply, and which 2 of the 3 rivals are racing.

const PLAYER := &"player"
const RIVALS: Array[StringName] = [&"hoarder", &"raider", &"runner"]
## Default pairing until the rival selection screen exists.
const DEFAULT_RIVALS: Array[StringName] = [&"raider", &"runner"]

var active_rivals: Array[StringName] = []
var collections: Dictionary[StringName, CardCollection] = {}
var currency := 0
var quest_flags: Dictionary[StringName, Variant] = {}
var opened_gates: Dictionary[StringName, StringName] = {}  # gate id -> opener
## Copies that can still exist for finite cards. Consuming or selling a card
## permanently subtracts from this; respawning commons are not tracked.
var world_supply: Dictionary[StringName, int] = {}


func _ready() -> void:
	new_game(DEFAULT_RIVALS)


func new_game(rivals: Array[StringName]) -> void:
	assert(rivals.size() == 2, "Pick exactly 2 of the 3 rivals")
	active_rivals = rivals.duplicate()
	collections.clear()
	for id in collectors():
		collections[id] = CardCollection.new(id)
	currency = 0
	quest_flags.clear()
	opened_gates.clear()
	world_supply.clear()
	for card in CardDatabase.all_cards():
		if not card.is_effectively_infinite():
			world_supply[card.id] = card.max_possible_copies()
	_emit_tracker()
	EventBus.currency_changed.emit(currency)


func collectors() -> Array[StringName]:
	var out: Array[StringName] = [PLAYER]
	out.append_array(active_rivals)
	return out


func collection(collector: StringName) -> CardCollection:
	return collections.get(collector)


func add_loose_card(collector: StringName, card_id: StringName) -> bool:
	var col := collection(collector)
	if col == null or CardDatabase.get_card(card_id) == null:
		return false
	col.add(card_id, CardCollection.State.LOOSE)
	EventBus.card_added.emit(collector, card_id)
	_emit_tracker()
	return true


func change_state(collector: StringName, card_id: StringName, from: CardCollection.State, to: CardCollection.State) -> bool:
	var col := collection(collector)
	if col == null or not col.move(card_id, from, to):
		return false
	EventBus.card_state_changed.emit(collector, card_id, from, to)
	return true


## Loose -> Bound: slot into the binder (protected from theft).
func bind_card(collector: StringName, card_id: StringName) -> bool:
	return change_state(collector, card_id, CardCollection.State.LOOSE, CardCollection.State.BOUND)


## Bound -> Exposed: taken out for use (vulnerable again).
func expose_card(collector: StringName, card_id: StringName) -> bool:
	return change_state(collector, card_id, CardCollection.State.BOUND, CardCollection.State.EXPOSED)


## Moves one stealable copy from victim to thief (arrives loose). Bound cards are safe.
func steal_card(thief: StringName, victim: StringName, card_id: StringName, method: StringName) -> bool:
	var from := collection(victim)
	var to := collection(thief)
	if from == null or to == null or thief == victim:
		return false
	for state in CardCollection.STEALABLE:
		if from.remove(card_id, state):
			to.add(card_id, CardCollection.State.LOOSE)
			EventBus.card_stolen.emit(thief, victim, card_id, method)
			_emit_tracker()
			return true
	return false


## Permanently spends one copy (gate cost, spell use). Takes the least protected copy first.
func consume_card(collector: StringName, card_id: StringName, reason: StringName) -> bool:
	var col := collection(collector)
	if col == null:
		return false
	for state in [CardCollection.State.LOOSE, CardCollection.State.EXPOSED, CardCollection.State.BOUND]:
		if col.remove(card_id, state):
			_reduce_supply(card_id)
			EventBus.card_consumed.emit(collector, card_id, reason)
			_emit_tracker()
			return true
	return false


## Sells one copy. Sold cards leave the world for good (not recycled via the merchant).
func sell_card(collector: StringName, card_id: StringName) -> int:
	var card := CardDatabase.get_card(card_id)
	if card == null or not consume_card(collector, card_id, &"sold"):
		return 0
	add_currency(card.sell_value)
	EventBus.card_sold.emit(collector, card_id, card.sell_value)
	return card.sell_value


func open_gate(gate_id: StringName, by: StringName) -> bool:
	var gate := CardDatabase.get_gate(gate_id)
	if gate == null or opened_gates.has(gate_id):
		return false
	var col := collection(by)
	if col == null or col.count(gate.cost_card_id) < gate.cost_amount:
		return false
	for i in gate.cost_amount:
		consume_card(by, gate.cost_card_id, &"gate")
	opened_gates[gate_id] = by
	EventBus.gate_opened.emit(gate_id, by)
	return true


func add_currency(amount: int) -> void:
	currency += amount
	EventBus.currency_changed.emit(currency)


func tracker_counts() -> Dictionary[StringName, int]:
	var final_set := CardDatabase.final_set()
	var out: Dictionary[StringName, int] = {}
	for id in collectors():
		out[id] = collection(id).set_progress(final_set)
	return out


func _reduce_supply(card_id: StringName) -> void:
	if world_supply.has(card_id):
		world_supply[card_id] = maxi(world_supply[card_id] - 1, 0)


func _emit_tracker() -> void:
	EventBus.tracker_changed.emit(tracker_counts())
