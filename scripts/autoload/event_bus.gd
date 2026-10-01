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
## The player arrived in an area (a zone or a room): the HUD shows its title large.
signal area_entered(title: String, interior: bool)
## The player's satchel changed (an item bought, used or found).
signal items_changed()
## The player's worn passive cards changed (GameState.equipped).
signal loadout_changed()
signal card_locked(collector: StringName, card_id: StringName, seconds: float)
signal spell_cast(caster: StringName, spell_id: StringName, target: StringName)
## A stealth attempt was caught (the victim noticed).
signal stealth_failed(thief: StringName, victim: StringName)
## A fight between collectors ended; `card_id` is what the winner took (&"" if nothing).
signal combat_won(winner: StringName, loser: StringName, card_id: StringName)
## Someone picked a card up off the ground (dropped_by: who lost it, or empty).
signal card_picked_up(collector: StringName, card_id: StringName, dropped_by: StringName)
## The player went down to a monster and woke up in town.
signal player_fainted(dropped_card: StringName)
## A boss went down; `killer` is whoever landed the last hit (or a monster id).
signal boss_defeated(boss_id: StringName, killer: StringName)
## A boss became killable again (gate-based respawn).
signal boss_returned(boss_id: StringName, gate_id: StringName)
## A boss fell to several collectors fighting together, truce kept.
signal boss_shared_win(boss_id: StringName, members: Array)
## Boss health bar: shown while a fight is on, hidden when `shown` is false.
signal boss_bar(boss_name: String, current: int, maximum: int, shown: bool)
signal safe_zone_changed(collector: StringName, inside: bool)
## Short player-facing message for the HUD.
signal notify(text: String)
## A monster (not a boss) went down; `kind` is its scene's file name (briar_hound, moss_boar).
signal monster_defeated(kind: StringName, killer: StringName)
## A menu opened or closed; the player ignores gameplay input while any is open.
signal menus_changed(open_count: int)
