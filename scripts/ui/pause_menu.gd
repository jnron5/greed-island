extends CanvasLayer
## Autoload "PauseMenu": Esc in the open world (no other menu open) pauses the game
## and shows a kit window with the race so far, the controls, and a way back to the
## title. Esc or Resume closes it.

const TITLE_SCENE := "res://scenes/ui/title_screen.tscn"
const CONTROLS := [
	["WASD / Arrows", "Move"], ["J", "Sword"], ["K", "Pistol"], ["Space", "Dash"],
	["E", "Talk, read, steal"], ["Q", "Cast Pickpocket's Whisper"], ["B", "Binder"], ["Esc", "Pause"],
]

var is_open := false

var _root: Control
var _race: Label
var _where: Label
var _resume: Button


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
	var title_button := Button.new()
	title_button.text = "Quit to title"
	title_button.pressed.connect(_to_title)
	left.add_child(title_button)

	var right := VBoxContainer.new()
	right.add_theme_constant_override(&"separation", 3)
	row.add_child(right)
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
