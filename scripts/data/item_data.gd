class_name ItemData
extends Resource
## A consumable you carry in your satchel (not a card): bought in shops, used from
## the character menu's Items page or with the quick-heal key. Items can't be stolen
## and don't count toward the race.

@export var id: StringName
@export var display_name := ""
@export_multiline var description := ""
## Health restored when used (0 = none; 99 = to full).
@export var heal := 0
@export var price := 10
@export var icon: Texture2D
