class_name MenuPanel
extends CanvasLayer
## Base for card menus (binder, shop): a centered panel with a title, a status
## line, and a scrolling list of rows rebuilt from GameState whenever cards change.
## Opening a menu freezes player input via GameState.push_menu().

const RARITY_COLORS := {
	CardData.Rarity.COMMON: Color(0.92, 0.92, 0.88),
	CardData.Rarity.RARE: Color(1.0, 0.82, 0.4),
	CardData.Rarity.BOSS: Color(1.0, 0.55, 0.45),
}
const SPELL_COLOR := Color(0.55, 0.9, 0.95)

@export var title := "Menu"
## Input action that toggles this menu; empty = opened from code only.
@export var toggle_action: StringName

var is_open := false

var _list: VBoxContainer
var _status: Label
var _refresh := 0.0


func _ready() -> void:
	layer = 10
	visible = false
	_build_frame()
	EventBus.card_added.connect(rebuild.unbind(2))
	EventBus.card_state_changed.connect(rebuild.unbind(4))
	EventBus.card_stolen.connect(rebuild.unbind(4))
	EventBus.card_consumed.connect(rebuild.unbind(3))
	EventBus.card_locked.connect(rebuild.unbind(3))
	EventBus.currency_changed.connect(rebuild.unbind(1))
	EventBus.safe_zone_changed.connect(rebuild.unbind(2))


func _process(delta: float) -> void:
	# Refresh once a second so lock timers count down.
	_refresh += delta
	if is_open and _refresh >= 1.0:
		_refresh = 0.0
		rebuild()


func _unhandled_input(event: InputEvent) -> void:
	if is_open:
		if event.is_action_pressed(&"pause") or (toggle_action != &"" and event.is_action_pressed(toggle_action)):
			close()
			get_viewport().set_input_as_handled()
	elif toggle_action != &"" and event.is_action_pressed(toggle_action) and GameState.menus_open == 0:
		open()
		get_viewport().set_input_as_handled()


func open() -> void:
	if is_open:
		return
	is_open = true
	visible = true
	GameState.push_menu()
	rebuild()


func close() -> void:
	if not is_open:
		return
	is_open = false
	visible = false
	GameState.pop_menu()


func rebuild() -> void:
	if not is_open:
		return
	for child in _list.get_children():
		child.queue_free()
	_status.text = _status_text()
	_build_rows()


## Override: fill the list with add_row()/add_header().
func _build_rows() -> void:
	pass


## Override: one line under the title.
func _status_text() -> String:
	return ""


func add_header(text: String) -> void:
	var label := Label.new()
	label.text = text
	label.modulate = Color(0.75, 0.75, 0.7)
	_list.add_child(label)


## One row: a coloured name, a detail column, then buttons given as
## [text, callable, enabled] triples.
func add_row(name_text: String, color: Color, detail: String, buttons: Array) -> void:
	var row := HBoxContainer.new()
	var name_label := Label.new()
	name_label.text = name_text
	name_label.modulate = color
	name_label.custom_minimum_size.x = 150
	name_label.clip_text = true
	row.add_child(name_label)
	var detail_label := Label.new()
	detail_label.text = detail
	detail_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(detail_label)
	for b: Array in buttons:
		var button := Button.new()
		button.text = b[0]
		button.disabled = not b[2]
		button.focus_mode = Control.FOCUS_NONE
		button.pressed.connect(b[1])
		row.add_child(button)
	_list.add_child(row)


static func card_color(card: CardData) -> Color:
	if card.category != CardData.Category.SET:
		return SPELL_COLOR
	return RARITY_COLORS[card.rarity]


func _build_frame() -> void:
	var root := Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.theme = Theme.new()
	root.theme.default_font_size = 10
	add_child(root)

	var dim := ColorRect.new()
	dim.color = Color(0, 0, 0, 0.45)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.add_child(dim)

	var panel := PanelContainer.new()
	panel.anchor_left = 0.5
	panel.anchor_right = 0.5
	panel.anchor_top = 0.5
	panel.anchor_bottom = 0.5
	panel.offset_left = -250
	panel.offset_right = 250
	panel.offset_top = -160
	panel.offset_bottom = 160
	root.add_child(panel)

	var margin := MarginContainer.new()
	for side in ["left", "right", "top", "bottom"]:
		margin.add_theme_constant_override("margin_" + side, 8)
	panel.add_child(margin)
	var vbox := VBoxContainer.new()
	margin.add_child(vbox)

	var header := HBoxContainer.new()
	vbox.add_child(header)
	var title_label := Label.new()
	title_label.text = title
	title_label.add_theme_font_size_override("font_size", 14)
	title_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(title_label)
	var close_button := Button.new()
	close_button.text = "Close (Esc)"
	close_button.focus_mode = Control.FOCUS_NONE
	close_button.pressed.connect(close)
	header.add_child(close_button)

	_status = Label.new()
	_status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_status.modulate = Color(0.85, 0.85, 0.75)
	vbox.add_child(_status)

	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	vbox.add_child(scroll)
	_list = VBoxContainer.new()
	_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(_list)
