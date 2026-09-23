@tool
class_name BossData
extends Resource
## One zone boss (res://data/bosses/). Bosses drop rare cards, can only be killed
## `kill_cap` times per playthrough, and only come back when a gate whose
## GateData.respawns_boss names them is opened (gate-based respawn).

@export var id: StringName
@export var display_name: String
## Zone scene the boss lives in.
@export_file("*.tscn") var zone: String
@export var kill_cap := 4
## One of each drops per kill (matches boss_drops_per_kill on the cards).
@export var drop_card_ids: Array[StringName] = []
