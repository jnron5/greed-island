extends CanvasLayer
## Autoload "Transition": changes scene with a short fade through black (doors,
## zone edges, waking up in town), so going indoors feels like going indoors.
## Player input is held while the screen is dark. Instant when running headless.

const FADE_OUT := 0.18
const FADE_IN := 0.25

var busy := false
var _black: ColorRect


func _ready() -> void:
	layer = 50
	process_mode = Node.PROCESS_MODE_ALWAYS
	_black = ColorRect.new()
	_black.color = Color(0.02, 0.015, 0.03)
	_black.set_anchors_preset(Control.PRESET_FULL_RECT)
	_black.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_black.modulate.a = 0.0
	add_child(_black)


func go(scene_path: String) -> void:
	if busy:
		return
	if DisplayServer.get_name() == "headless":
		get_tree().change_scene_to_file.call_deferred(scene_path)
		return
	busy = true
	GameState.push_menu()
	var out := create_tween()
	out.tween_property(_black, "modulate:a", 1.0, FADE_OUT)
	await out.finished
	get_tree().change_scene_to_file(scene_path)
	await get_tree().process_frame
	await get_tree().process_frame
	var back := create_tween()
	back.tween_property(_black, "modulate:a", 0.0, FADE_IN)
	await back.finished
	GameState.pop_menu()
	busy = false
