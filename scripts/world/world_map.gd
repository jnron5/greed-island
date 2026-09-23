class_name WorldMap
extends RefCounted
## Where each zone sits on Virelia Isle, so a spot in any zone can be compared
## with every town ("respawn in the nearest town"). A zone's local coordinates
## are offset by its `origin`; towns list where people wake up.
##
## Add each new zone/town here when its scene is created. Origins line up the
## zone exits: Thornveil's south exit (local y 125) meets Kalmora's north exit
## (local y -360), so Thornveil sits 485px north of Kalmora.

const KALMORA := "res://scenes/world/kalmora.tscn"
const THORNVEIL := "res://scenes/world/thornveil.tscn"

const ZONES := {
	KALMORA: { "origin": Vector2(0, 0) },
	THORNVEIL: { "origin": Vector2(0, -485) },
}

## Town scene -> { name, spawn marker (under "Spawns"), local position of that marker }
const TOWNS := {
	KALMORA: { "name": "Kalmora", "spawn": &"town", "position": Vector2(0, 40) },
}


## Island-space position of `local_pos` inside `zone`.
static func to_island(zone: String, local_pos: Vector2) -> Vector2:
	return ZONES.get(zone, {}).get("origin", Vector2.ZERO) + local_pos


## Scene path of the town closest to `local_pos` in `zone` (straight-line).
static func nearest_town(zone: String, local_pos: Vector2) -> String:
	var here := to_island(zone, local_pos)
	var best := KALMORA
	var best_dist := INF
	for town: String in TOWNS:
		var d := here.distance_to(to_island(town, TOWNS[town].position))
		if d < best_dist:
			best = town
			best_dist = d
	return best


static func town_name(town: String) -> String:
	return TOWNS.get(town, {}).get("name", "town")


static func town_spawn(town: String) -> StringName:
	return TOWNS.get(town, {}).get("spawn", &"town")
