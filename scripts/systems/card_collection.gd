class_name CardCollection
extends RefCounted
## Cards held by one collector (player or rival), counted per card state.
## Consumed cards are gone, so they are not tracked here.

enum State { LOOSE, BOUND, EXPOSED }

## Loose and exposed cards can be stolen; bound cards cannot.
const STEALABLE: Array[State] = [State.LOOSE, State.EXPOSED]
## Spell steals only take loose cards.
const LOOSE_ONLY: Array[State] = [State.LOOSE]

var owner_id: StringName
## card id -> PackedInt32Array indexed by State
var _counts: Dictionary[StringName, PackedInt32Array] = {}


func _init(p_owner_id: StringName) -> void:
	owner_id = p_owner_id


func add(card_id: StringName, state := State.LOOSE, amount := 1) -> void:
	# Packed arrays are value types: modify a copy, then write it back.
	var c: PackedInt32Array = _counts.get(card_id, PackedInt32Array([0, 0, 0]))
	c[state] += amount
	_counts[card_id] = c


## Removes one copy in `state`. Returns false if none held in that state.
func remove(card_id: StringName, state: State) -> bool:
	if count(card_id, state) == 0:
		return false
	add(card_id, state, -1)
	return true


func move(card_id: StringName, from: State, to: State) -> bool:
	if not remove(card_id, from):
		return false
	add(card_id, to)
	return true


## Count of `card_id`, in one state or (state = -1) across all states.
func count(card_id: StringName, state := -1) -> int:
	var c: PackedInt32Array = _counts.get(card_id, PackedInt32Array([0, 0, 0]))
	return c[0] + c[1] + c[2] if state == -1 else c[state]


func card_ids() -> Array[StringName]:
	var out: Array[StringName] = []
	for id in _counts:
		if count(id) > 0:
			out.append(id)
	return out


## Card ids with at least one stealable copy, paired with the state to take it from.
func stealable() -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	for id in _counts:
		for state in STEALABLE:
			if count(id, state) > 0:
				out.append({ "card_id": id, "state": state })
	return out


## Distinct final-set cards held at the required count, for the public tracker.
func set_progress(final_set: Array[CardData]) -> int:
	var n := 0
	for card in final_set:
		if count(card.id) >= card.final_set_count:
			n += 1
	return n


func has_complete_set(final_set: Array[CardData]) -> bool:
	return not final_set.is_empty() and set_progress(final_set) == final_set.size()
