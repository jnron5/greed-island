extends Node2D
## Zoomed-out overview of a zone for screenshots (no player camera). Set `zone`:
## godot --path . --write-movie out.png --quit-after 20 res://tests/zone_overview.tscn
@export_file("*.tscn") var zone := "res://scenes/world/sorenda.tscn"
@export var zoom := 0.62
@export var center := Vector2(0, -110)
## Hour of day to freeze at (-1 = leave the clock alone).
@export var hour := -1.0
## Hide HUD/menus (CanvasLayers) for clean map shots.
@export var hide_ui := false

func _ready() -> void:
	if hour >= 0.0:
		TimeOfDay.paused = true
		TimeOfDay.set_hour(hour)
	var z: Node = load(zone).instantiate()
	add_child(z)
	await get_tree().process_frame
	var cam := Camera2D.new()
	cam.zoom = Vector2(zoom, zoom)
	cam.position = center
	add_child(cam)
	cam.make_current()
	for n in get_tree().get_nodes_in_group(&"player"):
		n.get_node("Camera2D").enabled = false
	if hide_ui:
		for layer in z.find_children("*", "CanvasLayer", true, false):
			layer.visible = false
