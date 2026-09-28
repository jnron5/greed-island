extends CanvasLayer
## Autoload "PauseMenu": Esc in the open world (no other menu open) pauses the game
## and shows a kit window with the race so far, the controls, and a way back to the
## title. Esc or Resume closes it.

const TITLE_SCENE := "res://scenes/ui/title_screen.tscn"
const CONTROLS := [
	["WASD / Arrows", "Move"], ["J", "Sword"], ["K", "Pistol"], ["Space", "Dash"],
	["E", "Talk, read, open, steal"], ["Q", "Cast Pickpocket's Whisper"], ["H", "Eat or drink to heal"],
	["B / Tab", "Binder"], ["I", "Items"], ["Esc", "Pause"],
]

var is_open := false

var _root: Control
var _race: Label
var _where: Label
var _resume: Button
var _controls: Control
var _journal: Control
var _journal_list: VBoxContainer
var _journal_text: Label
var _journal_title: Label
var _journal_place: Label
var _journal_button: Button
var _map: IslandMap
var _map_button: Button


func _ready() -> void:
	layer = 30
	process_mode = Node.PROCESS_MODE_ALWAYS
	visible = false
	_build()


func _unhandled_input(event: InputEvent) -> void:
	if not event.is_action_pressed(&"pause"):
		return
	if is_open:
		close()
		get_viewport().set_input_as_handled()
	elif GameState.menus_open == 0 and get_tree().current_scene is Zone:
		open()
		get_viewport().set_input_as_handled()


func open() -> void:
	is_open = true
	visible = true
	GameState.push_menu()
	get_tree().paused = true
	var zone := get_tree().current_scene as Zone
	_where.text = zone.display_name if zone and zone.display_name != "" else "Virelia Isle"
	var total := CardDatabase.final_set().size()
	var lines: PackedStringArray = []
	var counts := GameState.tracker_counts()
	for id in counts:
		var who := "You" if id == GameState.PLAYER else "The " + String(id).capitalize()
		lines.append("%s   %d / %d" % [who, counts[id], total])
	_race.text = "\n".join(lines)
	_show_page(&"controls")
	_resume.grab_focus()


func close() -> void:
	if not is_open:
		return
	is_open = false
	visible = false
	get_tree().paused = false
	GameState.pop_menu()


func _to_title() -> void:
	close()
	Transition.go(TITLE_SCENE)


func _build() -> void:
	_root = Control.new()
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(_root)
	var dim := ColorRect.new()
	dim.color = Color(0.02, 0.03, 0.08, 0.7)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.add_child(dim)
	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.add_child(center)
	var window := PanelContainer.new()
	center.add_child(window)
	var row := HBoxContainer.new()
	row.add_theme_constant_override(&"separation", 16)
	window.add_child(row)

	var left := VBoxContainer.new()
	left.custom_minimum_size.x = 130
	left.add_theme_constant_override(&"separation", 6)
	row.add_child(left)
	var title := Label.new()
	title.theme_type_variation = &"TitleLabel"
	title.text = "Paused"
	title.add_theme_font_size_override(&"font_size", 16)
	left.add_child(title)
	_where = Label.new()
	_where.modulate = Color(0.8, 0.9, 0.9)
	left.add_child(_where)
	var race_title := Label.new()
	race_title.theme_type_variation = &"TitleLabel"
	race_title.text = "The Race"
	left.add_child(race_title)
	_race = Label.new()
	left.add_child(_race)
	var spacer := Control.new()
	spacer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	left.add_child(spacer)
	_resume = Button.new()
	_resume.text = "Resume"
	_resume.pressed.connect(close)
	left.add_child(_resume)
	_map_button = Button.new()
	_map_button.text = "Map"
	_map_button.pressed.connect(func() -> void: _show_page(&"controls" if _map.visible else &"map"))
	left.add_child(_map_button)
	_journal_button = Button.new()
	_journal_button.text = "Journal"
	_journal_button.pressed.connect(func() -> void: _show_page(&"controls" if _journal.visible else &"journal"))
	left.add_child(_journal_button)
	var title_button := Button.new()
	title_button.text = "Quit to title"
	title_button.pressed.connect(_to_title)
	left.add_child(title_button)

	var right := VBoxContainer.new()
	right.add_theme_constant_override(&"separation", 3)
	row.add_child(right)
	_controls = right
	_build_journal(row)
	_map = IslandMap.new()
	_map.custom_minimum_size = Vector2(380, 230)
	_map.visible = false
	row.add_child(_map)
	var controls := Label.new()
	controls.theme_type_variation = &"TitleLabel"
	controls.text = "Controls"
	right.add_child(controls)
	var grid := GridContainer.new()
	grid.columns = 2
	grid.add_theme_constant_override(&"h_separation", 10)
	grid.add_theme_constant_override(&"v_separation", 2)
	right.add_child(grid)
	for pair: Array in CONTROLS:
		var key := Label.new()
		key.text = pair[0]
		key.add_theme_color_override(&"font_color", Color(1.0, 0.84, 0.45))
		grid.add_child(key)
		var what := Label.new()
		what.text = pair[1]
		grid.add_child(what)


# ---------------------------------------------------------------- journal

## The journal: everything the player has read, by title on the left, the text on a
## parchment page on the right.
func _build_journal(row: HBoxContainer) -> void:
	_journal = HBoxContainer.new()
	_journal.add_theme_constant_override(&"separation", 8)
	_journal.visible = false
	row.add_child(_journal)
	var col := VBoxContainer.new()
	_journal.add_child(col)
	var heading := Label.new()
	heading.theme_type_variation = &"TitleLabel"
	heading.text = "Journal"
	col.add_child(heading)
	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(130, 190)
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	col.add_child(scroll)
	_journal_list = VBoxContainer.new()
	_journal_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(_journal_list)
	var page := PanelContainer.new()
	page.theme_type_variation = &"DialoguePanel"
	page.custom_minimum_size = Vector2(210, 210)
	_journal.add_child(page)
	var margin := MarginContainer.new()
	margin.add_theme_constant_override(&"margin_top", 14)
	margin.add_theme_constant_override(&"margin_left", 6)
	margin.add_theme_constant_override(&"margin_right", 6)
	page.add_child(margin)
	var text_col := VBoxContainer.new()
	text_col.add_theme_constant_override(&"separation", 4)
	margin.add_child(text_col)
	_journal_title = Label.new()
	_journal_title.theme_type_variation = &"InkLabel"
	_journal_title.add_theme_font_override(&"font", preload("res://assets/fonts/virelia_title.tres"))
	text_col.add_child(_journal_title)
	_journal_place = Label.new()
	_journal_place.theme_type_variation = &"InkLabel"
	_journal_place.modulate = Color(1, 1, 1, 0.65)
	text_col.add_child(_journal_place)
	_journal_text = Label.new()
	_journal_text.theme_type_variation = &"InkLabel"
	_journal_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_journal_text.custom_minimum_size.x = 170
	_journal_text.vertical_alignment = VERTICAL_ALIGNMENT_TOP
	_journal_text.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	text_col.add_child(_journal_text)


## The right side shows one page: the controls, the island map or the journal.
func _show_page(page: StringName) -> void:
	_map.visible = page == &"map"
	_map_button.text = "Controls" if page == &"map" else "Map"
	_show_journal(page == &"journal")
	_controls.visible = page == &"controls"


func _show_journal(on: bool) -> void:
	_journal.visible = on
	_journal_button.text = "Controls" if on else "Journal"
	if not on:
		return
	for child in _journal_list.get_children():
		child.queue_free()
	if GameState.journal.is_empty():
		_journal_title.text = "Nothing yet"
		_journal_place.text = ""
		_journal_text.text = "Letters, ledgers and signs you read around the island are kept here."
		return
	for entry: Dictionary in GameState.journal:
		var b := Button.new()
		b.text = entry.title
		b.clip_text = true
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.pressed.connect(_read.bind(entry))
		_journal_list.add_child(b)
	_read(GameState.journal[-1])


func _read(entry: Dictionary) -> void:
	_journal_title.text = entry.title
	_journal_place.text = entry.place
	_journal_text.text = "\n\n".join(entry.lines)
