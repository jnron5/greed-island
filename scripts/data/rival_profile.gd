@tool
class_name RivalProfile
extends Resource
## One rival archetype. Zones spawn rivals from these (res://data/rivals/) based
## on where GameState says each rival currently is.

@export var id: StringName
@export var display_name: String
@export var sprite_frames: SpriteFrames
## Lifts the sprite so its feet sit on the node origin.
@export var sprite_offset_y := -26.0
## Zone the rival starts the race in (it appears at RivalSpots/<id> there).
@export_file("*.tscn") var start_zone: String

@export_group("Movement")
@export var move_speed := 95.0
@export var carry_limit := 2

@export_group("Stealth")
@export var steal_urge := 0.35

@export_group("Combat")
@export var max_health := 5
@export var hunts := false
@export var attack_damage := 1
