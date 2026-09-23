extends Node2D
## Zoomed-out overview of a zone for screenshots (no player camera). Set `zone`:
## godot --path . --write-movie out.png --quit-after 20 res://tests/zone_overview.tscn
@export_file("*.tscn") var zone := "res://scenes/world/sorenda.tscn"

func _ready() -> void:
	var z: Node = load(zone).instantiate()
	add_child(z)
	await get_tree().process_frame
	var cam := Camera2D.new()
	cam.zoom = Vector2(0.62, 0.62)
	cam.position = Vector2(0, -110)
	add_child(cam)
	cam.make_current()
	for n in get_tree().get_nodes_in_group(&"player"):
		n.get_node("Camera2D").enabled = false
