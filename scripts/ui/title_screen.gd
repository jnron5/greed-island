extends Control
## Title screen: the harbor of Kalmora drifting behind the game's name, then the
## choice of rivals (2 of the 3, CLAUDE.md "Rivals") before the race begins.

const BACKDROP := preload("res://assets/ui/title_bg.png")
const START_SCENE := "res://scenes/world/kalmora.tscn"
## What each rival is like, in the game's own words (their full stories unfold in play).
const RIVAL_TEXT := {
	&"hoarder": ["The Hoarder", "Keeps to the towns and never stops collecting. Hard to rob early, a rich prize late."],
	&"raider": ["The Raider", "Hunts whoever holds the most cards. Skips gates, takes what it wants, fights for everything."],
	&"runner": ["The Runner", "Fastest on the island. Rushes gates and roads, carries little, is always somewhere else."],
}

var _pan := 0.0
var _backdrop: TextureRect
var _menu: VBoxContainer
var _pick: Control
var _chosen: Array[StringName] = []
var _cards: Dictionary = {}
var _start_button: Button
var _pick_hint: Label
var _heading: Array[Control] = []


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	_backdrop = TextureRect.new()
	_backdrop.texture = BACKDROP
	add_child(_backdrop)
	var shade := ColorRect.new()                 # darken toward the bottom for the menu
	shade.set_anchors_preset(Control.PRESET_FULL_RECT)
	shade.color = Color(0.02, 0.03, 0.06, 0.35)
	add_child(shade)
	var fade := TextureRect.new()
	var grad := GradientTexture2D.new()
	grad.gradient = Gradient.new()
	grad.gradient.set_color(0, Color(0.02, 0.03, 0.06, 0.0))
	grad.gradient.set_color(1, Color(0.02, 0.03, 0.06, 0.85))
	grad.fill_from = Vector2(0, 0.35)
	grad.fill_to = Vector2(0, 1)
	fade.texture = grad
	fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	fade.stretch_mode = TextureRect.STRETCH_SCALE
	add_child(fade)

	var title := Label.new()
	title.theme_type_variation = &"TitleLabel"
	title.text = "Card Race"
	title.add_theme_font_size_override(&"font_size", 32)
	title.add_theme_constant_override(&"outline_size", 6)
	title.add_theme_color_override(&"font_outline_color", Color(0.08, 0.05, 0.03))
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.set_anchors_preset(Control.PRESET_TOP_WIDE)
	title.offset_top = 70
	add_child(title)
	var sub := Label.new()
	sub.text = "A race for riches beyond measure"
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	sub.set_anchors_preset(Control.PRESET_TOP_WIDE)
	sub.offset_top = 112
	add_child(sub)
	_heading = [title, sub]

	_menu = VBoxContainer.new()
	_menu.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	_menu.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_menu.offset_top = -110
	_menu.offset_left = -60
	_menu.offset_right = 60
	_menu.add_theme_constant_override(&"separation", 6)
	add_child(_menu)
	if SaveGame.has_save():
		_menu_button("Continue", func() -> void: SaveGame.continue_game())
	_menu_button("New Game", _show_pick)
	_menu_button("Quit", func() -> void: get_tree().quit())
	(_menu.get_child(0) as Button).grab_focus.call_deferred()

	_build_pick()


func _process(delta: float) -> void:
	# A slow drift across the harbor and back.
	_pan += delta * 0.025
	var room := BACKDROP.get_size() - size
	var t := 0.5 - 0.5 * cos(_pan)
	_backdrop.position = -Vector2(room.x * t, room.y * (0.82 + 0.12 * sin(_pan * 0.7))).round()   # over the harbor


func _menu_button(text: String, action: Callable) -> Button:
	var b := Button.new()
	b.text = text
	b.custom_minimum_size = Vector2(120, 22)
	b.pressed.connect(action)
	_menu.add_child(b)
	return b


# ---------------------------------------------------------------- choosing rivals

func _build_pick() -> void:
	_pick = Control.new()
	_pick.set_anchors_preset(Control.PRESET_FULL_RECT)
	_pick.visible = false
	add_child(_pick)
	var heading := Label.new()
	heading.theme_type_variation = &"TitleLabel"
	heading.text = "Choose your two rivals"
	heading.add_theme_font_size_override(&"font_size", 16)
	heading.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	heading.set_anchors_preset(Control.PRESET_TOP_WIDE)
	heading.offset_top = 30
	_pick.add_child(heading)
	var row := HBoxContainer.new()
	row.set_anchors_preset(Control.PRESET_CENTER)
	row.grow_horizontal = Control.GROW_DIRECTION_BOTH
	row.grow_vertical = Control.GROW_DIRECTION_BOTH
	row.add_theme_constant_override(&"separation", 10)
	_pick.add_child(row)
	for id in GameState.RIVALS:
		var card := _rival_card(id)
		row.add_child(card)
		_cards[id] = card
	_pick_hint = Label.new()
	_pick_hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_pick_hint.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	_pick_hint.offset_top = -62
	_pick_hint.offset_bottom = -48
	_pick.add_child(_pick_hint)
	_start_button = Button.new()
	_start_button.text = "Begin the race"
	_start_button.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	_start_button.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_start_button.offset_top = -42
	_start_button.offset_bottom = -20
	_start_button.offset_left = -70
	_start_button.offset_right = 70
	_start_button.pressed.connect(_begin)
	_pick.add_child(_start_button)
	_refresh_pick()


func _rival_card(id: StringName) -> Button:
	var profile := GameState.rival_profile(id)
	var b := Button.new()
	b.toggle_mode = true
	b.custom_minimum_size = Vector2(150, 170)
	b.toggled.connect(func(on: bool) -> void: _toggle(id, on))
	var col := VBoxContainer.new()
	col.set_anchors_preset(Control.PRESET_FULL_RECT)
	col.offset_left = 8
	col.offset_right = -8
	col.offset_top = 8
	col.offset_bottom = -8
	col.mouse_filter = Control.MOUSE_FILTER_IGNORE
	b.add_child(col)
	# A gold ring and a ribbon mark the rivals you've picked.
	var ring := Panel.new()
	var style := StyleBoxFlat.new()
	style.draw_center = false
	style.border_color = Color(1.0, 0.8, 0.35)
	style.set_border_width_all(2)
	style.set_corner_radius_all(2)
	ring.add_theme_stylebox_override(&"panel", style)
	ring.set_anchors_preset(Control.PRESET_FULL_RECT)
	ring.offset_left = -3
	ring.offset_top = -3
	ring.offset_right = 3
	ring.offset_bottom = 3
	ring.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ring.name = "Ring"
	b.add_child(ring)
	var ribbon := Label.new()
	ribbon.name = "Ribbon"
	ribbon.theme_type_variation = &"TitleLabel"
	ribbon.text = "Rival"
	ribbon.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	ribbon.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	ribbon.offset_top = -18
	ribbon.offset_bottom = -4
	ribbon.mouse_filter = Control.MOUSE_FILTER_IGNORE
	b.add_child(ribbon)
	var portrait := TextureRect.new()
	portrait.stretch_mode = TextureRect.STRETCH_KEEP_CENTERED
	portrait.custom_minimum_size = Vector2(0, 64)
	portrait.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if profile and profile.sprite_frames and profile.sprite_frames.has_animation(&"idle_south"):
		portrait.texture = profile.sprite_frames.get_frame_texture(&"idle_south", 0)
	col.add_child(portrait)
	var name_label := Label.new()
	name_label.theme_type_variation = &"TitleLabel"
	name_label.text = RIVAL_TEXT[id][0]
	name_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	col.add_child(name_label)
	var blurb := Label.new()
	blurb.text = RIVAL_TEXT[id][1]
	blurb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	blurb.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	blurb.custom_minimum_size = Vector2(134, 0)
	col.add_child(blurb)
	return b


func _toggle(id: StringName, on: bool) -> void:
	if on and not _chosen.has(id):
		_chosen.append(id)
		if _chosen.size() > 2:                   # picking a third lets go of the oldest pick
			var dropped: StringName = _chosen.pop_front()
			(_cards[dropped] as Button).set_pressed_no_signal(false)
	elif not on:
		_chosen.erase(id)
	_refresh_pick()


func _refresh_pick() -> void:
	for id in _cards:
		var card: Button = _cards[id]
		var on := _chosen.has(id)
		card.get_node("Ring").visible = on
		card.get_node("Ribbon").visible = on
		card.modulate = Color.WHITE if on or _chosen.size() < 2 else Color(0.62, 0.62, 0.66)
	_start_button.disabled = _chosen.size() != 2
	_pick_hint.text = "Pick two." if _chosen.size() < 2 else "You'll race the %s and the %s." \
		% [RIVAL_TEXT[_chosen[0]][0].trim_prefix("The "), RIVAL_TEXT[_chosen[1]][0].trim_prefix("The ")]


func _show_pick() -> void:
	_menu.visible = false
	_pick.visible = true
	for c in _heading:
		c.visible = false
	(_cards[GameState.RIVALS[0]] as Button).grab_focus()


func _begin() -> void:
	if _chosen.size() != 2:
		return
	var rivals: Array[StringName] = []
	rivals.assign(_chosen)
	GameState.new_game(rivals)
	GameState.pending_spawn = &"arrival"      # off the boat, at the end of the pier
	Transition.go(START_SCENE)


func _unhandled_input(event: InputEvent) -> void:
	if _pick.visible and (event.is_action_pressed(&"ui_cancel") or event.is_action_pressed(&"pause")):
		_pick.visible = false
		_menu.visible = true
		for c in _heading:
			c.visible = true
		(_menu.get_child(0) as Button).grab_focus()
		get_viewport().set_input_as_handled()
