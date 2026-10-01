class_name Inn
extends RefCounted
## Renting a room. Every town's inn keeper (an Npc with `inn_rooms`) offers half a
## day's sleep or a full day's; you pay, the screen goes dark, the clock moves on and
## you wake with every heart back. Walking from place to place never heals: rest,
## food, springs and charms do.
##
## The rivals don't wait for you, but they sleep too: while you're out they get
## RIVAL_SHARE of the time you slept to roam the island (off screen, like always).

const HALF_DAY_PRICE := 10
const FULL_DAY_PRICE := 18
const RIVAL_SHARE := 1.0 / 6.0


## The keeper's question list for a room: [label, hours, price].
static func offers() -> Array:
	return [
		["Half a day (%d gold)" % HALF_DAY_PRICE, 12.0, HALF_DAY_PRICE],
		["A full day (%d gold)" % FULL_DAY_PRICE, 24.0, FULL_DAY_PRICE],
	]


## Pays and sleeps `hours`. False (and nothing happens) when the purse is short.
static func sleep(tree: SceneTree, hours: float, price: int) -> bool:
	if GameState.currency < price:
		return false
	GameState.add_currency(-price)
	Transition.rest(func() -> void:
		TimeOfDay.set_hour(TimeOfDay.hour + hours)
		RivalDirector.pass_time(hours / 24.0 * TimeOfDay.DAY_SECONDS * RIVAL_SHARE)
		GameState.player_health = -1
		var player := tree.get_first_node_in_group(&"player") as Player
		if player:
			player.heal(player.max_health))
	return true
