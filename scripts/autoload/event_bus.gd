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
signal card_locked(collector: StringName, card_id: StringName, seconds: float)
signal spell_cast(caster: StringName, spell_id: StringName, target: StringName)
## A stealth attempt was caught (the victim noticed).
signal stealth_failed(thief: StringName, victim: StringName)
## A fight between collectors ended; `card_id` is what the winner took (&"" if nothing).
signal combat_won(winner: StringName, loser: StringName, card_id: StringName)
## The player went down to a monster and woke up in town.
signal player_fainted(dropped_card: StringName)
signal safe_zone_changed(collector: StringName, inside: bool)
## Short player-facing message for the HUD.
signal notify(text: String)
## A menu opened or closed; the player ignores gameplay input while any is open.
signal menus_changed(open_count: int)
