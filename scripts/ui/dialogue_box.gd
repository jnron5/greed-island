class_name DialogueBox
extends CanvasLayer
## Speech box at the bottom of the screen: a parchment panel with the speaker's
## name plate and portrait, typewriter text, and a bobbing arrow when the line is
## done; interact/accept advances. One per zone (group "dialogue_box").
## Start a conversation with DialogueBox.say(tree, speaker, lines, on_done, portrait).
## DialogueBox.ask() puts a question with a short list of answers on screen (a
## resident's "Ask about..." topics); up/down picks, interact chooses, cancel backs out.

signal finished

const CHARS_PER_SECOND := 45.0
const PORTRAIT_FRAME := preload("res://assets/ui/portrait.png")

var _lines: PackedStringArray = []
var _index := 0
var _shown := 0.0
var _on_done: Callable
var _panel: PanelContainer
var _speaker: Label
var _plate: PanelContainer
var _text: Label
var _portrait_box: Control
var _portrait: TextureRect
var _arrow: Polygon2D
var _time := 0.0
var _choices: PanelContainer
var _choice_list: VBoxContainer
var _options: PackedStringArray = []
var _choice := 0
var _on_pick: Callable


func _ready() -> void:
	layer = 9
	visible = false
	add_to_group(&"dialogue_box")
	var root := Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(root)

	_panel = PanelContainer.new()
	_panel.theme_type_variation = &"DialoguePanel"
	_panel.anchor_left = 0.5
	_panel.anchor_right = 0.5
	_panel.anchor_top = 1.0
	_panel.anchor_bottom = 1.0
	_panel.offset_left = -230
	_panel.offset_right = 230
	_panel.offset_top = -92
	_panel.offset_bottom = -8
	root.add_child(_panel)
	var row := HBoxContainer.new()
	row.add_theme_constant_override(&"separation", 8)
	_panel.add_child(row)

	# The speaker's portrait in the kit's round frame (hidden for objects and signs).
	_portrait_box = Control.new()
	_portrait_box.custom_minimum_size = Vector2(36, 35)
	_portrait_box.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(_portrait_box)
	var disc := ColorRect.new()
	disc.color = Color(0.1, 0.27, 0.33)
	disc.position = Vector2(4, 3)
	disc.size = Vector2(28, 28)
	_portrait_box.add_child(disc)
	var clip := Control.new()
	clip.clip_contents = true
	clip.position = Vector2(4, 4)
	clip.size = Vector2(28, 27)
	_portrait_box.add_child(clip)
	_portrait = TextureRect.new()
	_portrait.stretch_mode = TextureRect.STRETCH_KEEP_CENTERED
	_portrait.size = Vector2(28, 27)
	clip.add_child(_portrait)
	var ring := TextureRect.new()
	ring.texture = PORTRAIT_FRAME
	_portrait_box.add_child(ring)

	_text = Label.new()
	_text.theme_type_variation = &"InkLabel"
	_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_text.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	row.add_child(_text)

	# Name plate sitting on the panel's top edge.
	_plate = PanelContainer.new()
	_plate.theme_type_variation = &"NamePlate"
	_plate.anchor_left = 0.5
	_plate.anchor_right = 0.5
	_plate.anchor_top = 1.0
	_plate.anchor_bottom = 1.0
	_plate.offset_left = -214
	_plate.offset_right = -214
	_plate.offset_top = -104
	_plate.offset_bottom = -84
	root.add_child(_plate)
	_plate.custom_minimum_size = Vector2(72, 20)
	_speaker = Label.new()
	_speaker.theme_type_variation = &"TitleLabel"
	_speaker.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_plate.add_child(_speaker)

	# Choice list: a small panel standing on the dialogue box's right-hand corner.
	_choices = PanelContainer.new()
	_choices.theme_type_variation = &"DialoguePanel"
	_choices.anchor_left = 0.5
	_choices.anchor_right = 0.5
	_choices.anchor_top = 1.0
	_choices.anchor_bottom = 1.0
	_choices.offset_right = 230
	_choices.offset_bottom = -96
	_choices.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	_choices.grow_vertical = Control.GROW_DIRECTION_BEGIN
	_choices.visible = false
	root.add_child(_choices)
	_choice_list = VBoxContainer.new()
	_choice_list.add_theme_constant_override(&"separation", 1)
	_choices.add_child(_choice_list)

	_arrow = Polygon2D.new()
	_arrow.polygon = PackedVector2Array([Vector2(-4, 0), Vector2(4, 0), Vector2(0, 5)])
	_arrow.color = Color(0.55, 0.3, 0.1)
	_panel.add_child(_arrow)


static func say(tree: SceneTree, speaker: String, lines: PackedStringArray, on_done := Callable(),
		portrait: Texture2D = null) -> void:
	var box := tree.get_first_node_in_group(&"dialogue_box") as DialogueBox
	if box == null or lines.is_empty():
		if on_done.is_valid():
			on_done.call()
		return
	box.open(speaker, lines, on_done, portrait)


## A question with answers: `prompt` is spoken, then `options` are listed; picking one
## closes the box and calls on_pick(index). Cancel picks the last option.
static func ask(tree: SceneTree, speaker: String, prompt: String, options: PackedStringArray,
		on_pick: Callable, portrait: Texture2D = null) -> void:
	var box := tree.get_first_node_in_group(&"dialogue_box") as DialogueBox
	if box == null or options.is_empty():
		return
	box.open(speaker, PackedStringArray([prompt]), Callable(), portrait)
	box._options = options
	box._on_pick = on_pick
	box._choice = 0
	box._fill_choices()


func open(speaker: String, lines: PackedStringArray, on_done: Callable, portrait: Texture2D = null) -> void:
	if visible:
		return
	_options = PackedStringArray()
	_choices.visible = false
	_speaker.text = speaker
	_plate.visible = speaker != ""
	_portrait.texture = portrait
	_portrait_box.visible = portrait != null
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
	_time += delta
	var line := _lines[_index]
	if _shown < line.length():
		_shown = minf(_shown + CHARS_PER_SECOND * delta, line.length())
		_text.visible_characters = int(_shown)
	_arrow.visible = _shown >= line.length() and _options.is_empty()
	_choices.visible = not _options.is_empty() and _shown >= line.length()
	_arrow.position = Vector2(_panel.size.x - 22, _panel.size.y - 18 + roundf(sin(_time * 6.0) * 1.5))


func _unhandled_input(event: InputEvent) -> void:
	if not visible:
		return
	if not _options.is_empty() and _shown >= _lines[_index].length():
		_choice_input(event)
		return
	if not (event.is_action_pressed(&"interact") or event.is_action_pressed(&"ui_accept")):
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


func _choice_input(event: InputEvent) -> void:
	var pick := -1
	if event.is_action_pressed(&"ui_up") or event.is_action_pressed(&"move_up"):
		_choice = wrapi(_choice - 1, 0, _options.size())
	elif event.is_action_pressed(&"ui_down") or event.is_action_pressed(&"move_down"):
		_choice = wrapi(_choice + 1, 0, _options.size())
	elif event.is_action_pressed(&"interact") or event.is_action_pressed(&"ui_accept"):
		pick = _choice
	elif event.is_action_pressed(&"ui_cancel"):
		pick = _options.size() - 1
	else:
		return
	get_viewport().set_input_as_handled()
	if pick < 0:
		_fill_choices()
		return
	var on_pick := _on_pick
	_options = PackedStringArray()
	_choices.visible = false
	visible = false
	GameState.pop_menu()
	finished.emit()
	if on_pick.is_valid():
		on_pick.call(pick)


func _fill_choices() -> void:
	for child in _choice_list.get_children():
		child.queue_free()
	for i in _options.size():
		var label := Label.new()
		label.theme_type_variation = &"InkLabel"
		label.text = ("> " if i == _choice else "   ") + _options[i]
		if i == _choice:
			label.add_theme_color_override(&"font_color", Color(0.62, 0.22, 0.08))
		_choice_list.add_child(label)


func _show_line() -> void:
	_text.text = _lines[_index]
	_text.visible_characters = 0
	_shown = 0.0


## A portrait for a character: the top of its south-facing idle frame (head and
## shoulders), from its SpriteFrames.
static func portrait_from(frames: SpriteFrames) -> Texture2D:
	if frames == null:
		return null
	for anim in [&"idle_south", &"idle", &"walk_south"]:
		if frames.has_animation(anim) and frames.get_frame_count(anim) > 0:
			var image := frames.get_frame_texture(anim, 0).get_image()
			var used := image.get_used_rect()
			var head := Rect2i(used.position.x + used.size.x / 2 - 14, used.position.y - 2, 28, 27)
			return ImageTexture.create_from_image(image.get_region(head.intersection(Rect2i(Vector2i.ZERO, image.get_size()))))
	return null
