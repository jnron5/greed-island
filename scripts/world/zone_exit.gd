class_name ZoneExit
extends Area2D
## Walking into this takes the player to another zone scene, arriving at the
## spawn marker named `target_spawn` there.

@export_file("*.tscn") var target_scene: String
@export var target_spawn: StringName


func _ready() -> void:
	body_entered.connect(_on_body_entered)


func _on_body_entered(body: Node2D) -> void:
	if body is Player and target_scene != "":
		GameState.pending_spawn = target_spawn
		get_tree().change_scene_to_file.call_deferred(target_scene)
