@tool
class_name GateData
extends Resource
## A card-locked gate. Each gate lives as a .tres in res://data/gates/.
## Opening a gate consumes the cost cards permanently; the gate stays open.

@export var id: StringName
@export var display_name: String
@export var zone: StringName
@export var cost_card_id: StringName
@export var cost_amount := 1
## Gate also opens via a hard fight or hidden path (pay in effort, not cards).
@export var has_alternate_route := false
## Boss that becomes killable again when this gate opens (gate-based respawn).
@export var respawns_boss: StringName
