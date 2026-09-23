extends Node
## Signal hub for card state changes, so UI, rival AI and the public tracker
## stay in sync without referencing each other.

signal card_added(collector: StringName, card_id: StringName)
signal card_state_changed(collector: StringName, card_id: StringName, from_state: int, to_state: int)
signal card_stolen(thief: StringName, victim: StringName, card_id: StringName, method: StringName)
signal card_consumed(collector: StringName, card_id: StringName, reason: StringName)
signal card_sold(collector: StringName, card_id: StringName, price: int)
signal gate_opened(gate_id: StringName, by: StringName)
## Public tracker: collector id -> number of final-set cards held (counts only).
signal tracker_changed(counts: Dictionary)
signal currency_changed(amount: int)
