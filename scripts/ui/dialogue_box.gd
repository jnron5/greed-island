class_name DialogueBox
extends CanvasLayer
## Speech box at the bottom of the screen: speaker name, typewriter text,
## interact/accept to advance. One per zone (group "dialogue_box").
## Start a conversation with DialogueBox.say(tree, speaker, lines, on_done).

signal finished

const CHARS_PER_SECOND := 45.0

var _lines: PackedStringArray = []
var _index := 0
var _shown := 0.0
var _on_done: Callable
var _speaker: Label
var _text: Label
var _hint: Label


func _ready() -> void:
	layer = 9
	visible = false
	add_to_group(&"dialogue_box")
	var root := Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.theme = Theme.new()
	root.theme.default_font_size = 10
	add_child(root)
	var panel := PanelContainer.new()
	panel.anchor_left = 0.5
	panel.anchor_right = 0.5
	panel.anchor_top = 1.0
	panel.anchor_bottom = 1.0
	panel.offset_left = -260
	panel.offset_right = 260
	panel.offset_top = -96
	panel.offset_bottom = -12
	root.add_child(panel)
	var margin := MarginContainer.new()
	for side in ["left", "right", "top", "bottom"]:
		margin.add_theme_constant_override("margin_" + side, 8)
	panel.add_child(margin)
	var box := VBoxContainer.new()
	margin.add_child(box)
	_speaker = Label.new()
	_speaker.add_theme_color_override("font_color", Color(1.0, 0.85, 0.45))
	box.add_child(_speaker)
	_text = Label.new()
	_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_text.size_flags_vertical = Control.SIZE_EXPAND_FILL
	box.add_child(_text)
	_hint = Label.new()
	_hint.text = "E ▸"
	_hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_hint.modulate = Color(1, 1, 1, 0.6)
	box.add_child(_hint)


static func say(tree: SceneTree, speaker: String, lines: PackedStringArray, on_done := Callable()) -> void:
	var box := tree.get_first_node_in_group(&"dialogue_box") as DialogueBox
	if box == null or lines.is_empty():
		if on_done.is_valid():
			on_done.call()
		return
	box.open(speaker, lines, on_done)


func open(speaker: String, lines: PackedStringArray, on_done: Callable) -> void:
	if visible:
		return
	_speaker.text = speaker
	_lines = lines
	_index = 0
	_on_done = on_done
	_show_line()
	visible = true
	GameState.push_menu()


func is_open() -> bool:
	return visible


func _process(delta: float) -> void:
	if not visible:
		return
	var line := _lines[_index]
	if _shown < line.length():
		_shown = minf(_shown + CHARS_PER_SECOND * delta, line.length())
		_text.visible_characters = int(_shown)
	_hint.visible = _shown >= line.length()


func _unhandled_input(event: InputEvent) -> void:
	if not visible or not (event.is_action_pressed(&"interact") or event.is_action_pressed(&"ui_accept")):
		return
	get_viewport().set_input_as_handled()
	if _shown < _lines[_index].length():
		_shown = _lines[_index].length()  # Skip the typing.
		_text.visible_characters = -1
		return
	_index += 1
	if _index < _lines.size():
		_show_line()
		return
	visible = false
	GameState.pop_menu()
	finished.emit()
	if _on_done.is_valid():
		_on_done.call()


func _show_line() -> void:
	_text.text = _lines[_index]
	_text.visible_characters = 0
	_shown = 0.0
