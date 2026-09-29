class_name Binder
extends CanvasLayer
## The player's binder: an open ring binder (assets/ui/binder.png) whose pages hold
## the cards in clear sleeves, six to a page, in set order. Owned cards show their
## picture, name and count, with a padlock when bound (safe) or a red "!" when a copy
## is loose or exposed (stealable); missing ones show their set number. A second tab
## holds charms and spells. Open a card to see it large, turn it over (E) and bind,
## take out, lock or use it. Binding is instant in towns and slower in the field.
## The character menu has two pages, picked by the tabs along its top: the Binder,
## and Items (the satchel: bread, tonics and the like, used here to heal). B opens
## the binder page, I the items page, Tab switches.

const BINDER := preload("res://assets/ui/binder.png")
const SLOT := preload("res://assets/ui/slot.png")
## Pocket positions on the binder image (scripts/tools/build_ui_kit.py bakes the sleeves).
const POCKET := Vector2(88, 84)
const POCKET_COLS := [58, 158, 316, 416]
const POCKET_ROWS := [27, 117, 207]
const PER_SPREAD := 12
const ART := Vector2(66, 47)
const INK := Color(0.28, 0.16, 0.08)
const FADED := Color(0.55, 0.45, 0.33)
const SAFE := Color(0.95, 0.75, 0.3)
const DANGER := Color(0.85, 0.22, 0.2)

var is_open := false
var page := 0                    # 0 the binder, 1 items

var _tab := 0                    # 0 set cards, 1 charms and spells
var _spread := 0
var _selected := 0               # pocket index within the spread
var _root: Control
var _book: TextureRect
var _pockets: Array[Control] = []
var _highlight: Panel
var _title: Label
var _status: Label
var _page_label: Label
var _tabs: Array[Button] = []
var _detail: Control
var _detail_view: CardView
var _detail_info: Label
var _detail_actions: VBoxContainer
var _detail_card: StringName
## card id -> true while a field bind is in progress
var _binding: Dictionary[StringName, bool] = {}


var _pages: Array[Button] = []
var _binder_bits: Control
var _items_page: Control
var _item_list: VBoxContainer
var _item_rows: Array[Control] = []
var _item_name: Label
var _item_text: Label
var _item_icon: TextureRect
var _item_use: Button
var _item_selected := 0

func _ready() -> void:
	layer = 10
	visible = false
	_build()
	for sig in [EventBus.card_added, EventBus.card_state_changed, EventBus.card_stolen, EventBus.card_consumed,
			EventBus.card_locked, EventBus.safe_zone_changed]:
		sig.connect(func(_a = null, _b = null, _c = null, _d = null) -> void: _refresh())


func open(on_page := 0) -> void:
	if is_open:
		return
	Sfx.play(&"ui_click")
	page = on_page
	is_open = true
	visible = true
	GameState.push_menu()
	_close_detail()
	_refresh()


func close() -> void:
	if not is_open:
		return
	is_open = false
	visible = false
	GameState.pop_menu()


func _unhandled_input(event: InputEvent) -> void:
	if not is_open:
		if GameState.menus_open == 0 and (event.is_action_pressed(&"binder") or event.is_action_pressed(&"items")):
			open(1 if event.is_action_pressed(&"items") else 0)
			get_viewport().set_input_as_handled()
		return
	get_viewport().set_input_as_handled()
	# Tab flips between the binder and the satchel; I jumps to the satchel.
	if (event is InputEventKey and event.pressed and not event.echo and event.physical_keycode == KEY_TAB) \
			or (page == 0 and event.is_action_pressed(&"items")):
		_set_page(1 - page if event is InputEventKey and event.physical_keycode == KEY_TAB else 1)
		return
	if page == 1:
		_items_input(event)
		return
	if _detail.visible:
		if event.is_action_pressed(&"interact"):
			_detail_view.showing_back = not _detail_view.showing_back
		elif event.is_action_pressed(&"ui_cancel") or event.is_action_pressed(&"pause") or event.is_action_pressed(&"binder"):
			_close_detail()
		return
	if event.is_action_pressed(&"pause") or event.is_action_pressed(&"binder") or event.is_action_pressed(&"ui_cancel"):
		close()
	elif event.is_action_pressed(&"ui_accept") or event.is_action_pressed(&"interact"):
		_open_detail(_selected)
	elif event.is_action_pressed(&"ui_left") or event.is_action_pressed(&"move_left"):
		_move(-1, 0)
	elif event.is_action_pressed(&"ui_right") or event.is_action_pressed(&"move_right"):
		_move(1, 0)
	elif event.is_action_pressed(&"ui_up") or event.is_action_pressed(&"move_up"):
		_move(0, -1)
	elif event.is_action_pressed(&"ui_down") or event.is_action_pressed(&"move_down"):
		_move(0, 1)


# ---------------------------------------------------------------- pages

func _cards() -> Array[CardData]:
	var all := CardDatabase.all_cards()
	var out: Array[CardData] = []
	out.assign(all.filter(func(c: CardData) -> bool:
		return c.category == CardData.Category.SET if _tab == 0 else c.category != CardData.Category.SET))
	out.sort_custom(func(a: CardData, b: CardData) -> bool: return a.resource_path < b.resource_path)
	return out


func _spreads() -> int:
	return maxi(1, ceili(_cards().size() / float(PER_SPREAD)))


func _move(dx: int, dy: int) -> void:
	var col := _selected % 4 + dx
	var row := _selected / 4 + dy
	if col < 0:
		if _spread > 0:
			_turn(-1)
			col = 3
		else:
			col = 0
	elif col > 3:
		if _spread < _spreads() - 1:
			_turn(1)
			col = 0
		else:
			col = 3
	_selected = clampi(row, 0, 2) * 4 + clampi(col, 0, 3)
	_place_highlight()


func _turn(step: int) -> void:
	var next := clampi(_spread + step, 0, _spreads() - 1)
	if next == _spread:
		return
	_spread = next
	# A quick page turn: the pages dip and come back.
	var tw := create_tween()
	tw.tween_property(_book, "scale:x", 0.94, 0.06)
	tw.tween_property(_book, "scale:x", 1.0, 0.08)
	_refresh()


func _set_tab(tab: int) -> void:
	_tab = tab
	_spread = 0
	_selected = 0
	_refresh()


func _refresh() -> void:
	if not is_open:
		return
	_book.visible = page == 0
	_binder_bits.visible = page == 0
	_items_page.visible = page == 1
	for i in _pages.size():
		_pages[i].button_pressed = i == page
	if page == 1:
		_fill_items()
		return
	var col := GameState.collection(GameState.PLAYER)
	var cards := _cards()
	var total := CardDatabase.final_set().size()
	var progress: int = GameState.tracker_counts().get(GameState.PLAYER, 0)
	_title.text = "Binder" if _tab == 0 else "Charms & Spells"
	var where := "In town: binding is instant." if GameState.is_in_safe_zone(GameState.PLAYER) \
		else "In the field: binding takes %.1fs a card." % GameState.FIELD_BIND_TIME
	_status.text = "Set %d/%d   %s   Bound cards can't be stolen." % [progress, total, where]
	_page_label.text = "%d / %d" % [_spread + 1, _spreads()]
	for i in _tabs.size():
		_tabs[i].button_pressed = i == _tab
	for i in PER_SPREAD:
		var k := _spread * PER_SPREAD + _slot(i)
		_fill_pocket(_pockets[i], cards[k] if k < cards.size() else null, k + 1, col)
	_place_highlight()
	if _detail.visible:
		_fill_detail()


func _fill_pocket(pocket: Control, card: CardData, number: int, col: CardCollection) -> void:
	for child in pocket.get_children():
		child.queue_free()
	pocket.set_meta(&"card", card.id if card else &"")
	if card == null:
		return
	var have := col.count(card.id)
	if have == 0:
		var num := Label.new()
		num.text = "No. %02d" % number if _tab == 0 else "?"
		num.theme_type_variation = &"InkLabel"
		num.add_theme_color_override(&"font_color", FADED)
		num.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		num.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		num.size = POCKET
		pocket.add_child(num)
		return
	var frame := ColorRect.new()                      # a dark mount behind the picture
	frame.color = Color(0.18, 0.12, 0.08)
	frame.position = Vector2((POCKET.x - ART.x) / 2 - 1, 4)
	frame.size = ART + Vector2(2, 2)
	pocket.add_child(frame)
	if card.icon:
		var clip := Control.new()
		clip.clip_contents = true
		clip.position = frame.position + Vector2.ONE
		clip.size = ART
		pocket.add_child(clip)
		var art := TextureRect.new()
		art.texture = card.icon
		art.stretch_mode = TextureRect.STRETCH_KEEP_CENTERED
		art.size = ART
		clip.add_child(art)
	else:
		var blank := ColorRect.new()
		blank.color = Color(0.12, 0.3, 0.36)
		blank.position = frame.position + Vector2.ONE
		blank.size = ART
		pocket.add_child(blank)
		var medal := TextureRect.new()
		medal.texture = preload("res://assets/ui/medal_shell.png")
		medal.position = blank.position + (ART - Vector2(17, 18)) / 2
		pocket.add_child(medal)
	var name_label := Label.new()
	name_label.theme_type_variation = &"InkLabel"
	name_label.text = card.display_name
	name_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	name_label.clip_text = true
	name_label.position = Vector2(2, 53)
	name_label.size = Vector2(POCKET.x - 4, 12)
	pocket.add_child(name_label)
	var count := Label.new()
	count.theme_type_variation = &"InkLabel"
	count.text = "x%d" % have
	count.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	count.position = Vector2(4, 67)
	count.size = Vector2(POCKET.x - 10, 12)
	pocket.add_child(count)
	var at_risk := GameState.stealable_copies(GameState.PLAYER, card.id) > 0
	var badge := Label.new()
	badge.position = Vector2(6, 67)
	badge.size = Vector2(60, 12)
	badge.theme_type_variation = &"InkLabel"
	if _binding.has(card.id):
		badge.text = "binding..."
		badge.add_theme_color_override(&"font_color", FADED)
	elif at_risk:
		badge.text = "! at risk"
		badge.add_theme_color_override(&"font_color", DANGER)
	else:
		badge.text = "bound"
		badge.add_theme_color_override(&"font_color", Color(0.6, 0.42, 0.12))
	pocket.add_child(badge)


## Pockets are laid out 4 across the spread (index = row * 4 + column) but filled a
## page at a time, like a real binder: the left page holds slots 0-5, the right 6-11.
static func _slot(pocket: int) -> int:
	var col := pocket % 4
	return (col / 2) * 6 + (pocket / 4) * 2 + col % 2


func _place_highlight() -> void:
	var pocket := _pockets[_selected]
	_highlight.position = pocket.position - Vector2(2, 2)
	_highlight.size = POCKET + Vector2(4, 4)


# ---------------------------------------------------------------- one card

func _open_detail(index: int) -> void:
	_selected = index
	_place_highlight()
	var id: StringName = _pockets[index].get_meta(&"card", &"")
	if id == &"" or GameState.collection(GameState.PLAYER).count(id) == 0:
		return
	_detail_card = id
	_detail_view.card = CardDatabase.get_card(id)
	_detail_view.showing_back = false
	_detail.visible = true
	_fill_detail()


func _close_detail() -> void:
	_detail.visible = false
	_detail_card = &""


func _fill_detail() -> void:
	var id := _detail_card
	var col := GameState.collection(GameState.PLAYER)
	if col.count(id) == 0:
		_close_detail()
		return
	var loose := col.count(id, CardCollection.State.LOOSE)
	var bound := col.count(id, CardCollection.State.BOUND)
	var exposed := col.count(id, CardCollection.State.EXPOSED)
	var info := "Bound %d  (safe)\nLoose %d\nExposed %d" % [bound, loose, exposed]
	if GameState.is_locked(GameState.PLAYER, id):
		info += "\nLocked for %ds" % ceili(GameState.lock_time_left(GameState.PLAYER, id))
	var worn := GameState.is_equipped(id)
	if worn:
		info += "\nWorn (%d/%d slots). Worn cards can be stolen." % [GameState.equipped.size(), GameState.EQUIP_SLOTS]
	_detail_info.text = info
	for child in _detail_actions.get_children():
		child.queue_free()
	var buttons: Array = []
	if _binding.has(id):
		buttons.append(["Binding...", Callable(), false])
	elif loose > 0:
		buttons.append(["Bind", _bind.bind(id, CardCollection.State.LOOSE), true])
	var card := CardDatabase.get_card(id)
	if card and card.category == CardData.Category.BUFF_PASSIVE:
		if worn:
			buttons.append(["Take off", _take_off.bind(id), true])
		else:
			buttons.append(["Wear", _wear.bind(id), loose + bound > 0 and GameState.equipped.size() < GameState.EQUIP_SLOTS])
	if exposed > 0 and not _binding.has(id) and not worn:
		buttons.append(["Put back", _bind.bind(id, CardCollection.State.EXPOSED), true])
	if bound > 0:
		buttons.append(["Take out", func() -> void: GameState.expose_card(GameState.PLAYER, id), true])
	if id == CardSpells.PICKPOCKET:
		buttons.append(["Cast (Q)", _cast_pickpocket, true])
	elif id == CardSpells.SECOND_WIND:
		buttons.append(["Use", _use_second_wind, true])
	elif col.count(CardSpells.LOCKBOX) > 0 and id != CardSpells.LOCKBOX:
		var can_lock := GameState.stealable_copies(GameState.PLAYER, id) > 0 and not GameState.is_locked(GameState.PLAYER, id)
		buttons.append(["Lock", func() -> void: CardSpells.use_lockbox(GameState.PLAYER, id), can_lock])
	for b: Array in buttons:
		var button := Button.new()
		button.text = b[0]
		button.disabled = not b[2]
		button.focus_mode = Control.FOCUS_NONE
		if b[1] is Callable and (b[1] as Callable).is_valid():
			button.pressed.connect(b[1])
		_detail_actions.add_child(button)


## Loose -> Bound or Exposed -> Bound, after the bind time for where the player stands.
func _bind(id: StringName, from: CardCollection.State) -> void:
	var delay := GameState.bind_time(GameState.PLAYER)
	if delay > 0.0:
		_binding[id] = true
		_refresh()
		await get_tree().create_timer(delay).timeout
		_binding.erase(id)
	GameState.change_state(GameState.PLAYER, id, from, CardCollection.State.BOUND)
	_refresh()


func _wear(id: StringName) -> void:
	if GameState.equip(id):
		var card := CardDatabase.get_card(id)
		EventBus.notify.emit("Wearing %s" % card.display_name)
	_refresh()


func _take_off(id: StringName) -> void:
	GameState.unequip(id)
	_refresh()


func _cast_pickpocket() -> void:
	var player := get_tree().get_first_node_in_group(&"player") as Player
	if player:
		close()
		CardSpells.cast_pickpocket(player)


func _use_second_wind() -> void:
	var player := get_tree().get_first_node_in_group(&"player") as Player
	if player and CardSpells.use_second_wind(player):
		EventBus.notify.emit("Second Wind: +%d HP" % CardSpells.SECOND_WIND_HEAL)


# ---------------------------------------------------------------- layout

func _build() -> void:
	_root = Control.new()
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(_root)
	var dim := ColorRect.new()
	dim.color = Color(0.02, 0.03, 0.08, 0.82)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.add_child(dim)

	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	center.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(center)
	var holder := Control.new()
	holder.custom_minimum_size = Vector2(576, 356)
	holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	center.add_child(holder)

	# Page tabs along the top: the binder and the satchel.
	var page_box := HBoxContainer.new()
	page_box.position = Vector2(4, -6)
	page_box.add_theme_constant_override(&"separation", 4)
	holder.add_child(page_box)
	for i in 2:
		var tab := Button.new()
		tab.text = ["Binder", "Items"][i]
		tab.toggle_mode = true
		tab.focus_mode = Control.FOCUS_NONE
		tab.custom_minimum_size.x = 70
		tab.pressed.connect(_set_page.bind(i))
		page_box.add_child(tab)
		_pages.append(tab)
	_title = Label.new()
	_title.theme_type_variation = &"TitleLabel"
	_title.position = Vector2(156, 0)
	holder.add_child(_title)
	_status = Label.new()
	_status.position = Vector2(110, 2)
	_status.size = Vector2(460, 12)
	_status.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	holder.add_child(_status)

	_book = TextureRect.new()
	_book.texture = BINDER
	_book.position = Vector2(0, 16)
	_book.pivot_offset = Vector2(288, 160)
	holder.add_child(_book)
	for i in PER_SPREAD:
		var pocket := Control.new()
		pocket.position = Vector2(POCKET_COLS[i % 4], POCKET_ROWS[i / 4])
		pocket.size = POCKET
		pocket.mouse_filter = Control.MOUSE_FILTER_STOP
		pocket.gui_input.connect(_on_pocket_input.bind(i))
		pocket.mouse_entered.connect(func() -> void:
			_selected = i
			_place_highlight())
		_book.add_child(pocket)
		_pockets.append(pocket)
	_highlight = Panel.new()
	var ring := StyleBoxFlat.new()
	ring.draw_center = false
	ring.border_color = Color(1.0, 0.8, 0.35)
	ring.set_border_width_all(2)
	_highlight.add_theme_stylebox_override(&"panel", ring)
	_highlight.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_book.add_child(_highlight)

	# Tabs as ribbons down the binder's right edge; page turning along the bottom.
	_binder_bits = Control.new()
	_binder_bits.mouse_filter = Control.MOUSE_FILTER_IGNORE
	holder.add_child(_binder_bits)
	var tab_box := VBoxContainer.new()
	tab_box.position = Vector2(530, 40)
	_binder_bits.add_child(tab_box)
	for i in 2:
		var tab := Button.new()
		tab.text = ["Set", "Charms"][i]
		tab.toggle_mode = true
		tab.focus_mode = Control.FOCUS_NONE
		tab.pressed.connect(_set_tab.bind(i))
		tab_box.add_child(tab)
		_tabs.append(tab)
	var prev := Button.new()
	prev.text = "<"
	prev.focus_mode = Control.FOCUS_NONE
	prev.position = Vector2(236, 318)
	prev.pressed.connect(_turn.bind(-1))
	_binder_bits.add_child(prev)
	_page_label = Label.new()
	_page_label.position = Vector2(268, 322)
	_page_label.size = Vector2(40, 12)
	_page_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_binder_bits.add_child(_page_label)
	var next := Button.new()
	next.text = ">"
	next.focus_mode = Control.FOCUS_NONE
	next.position = Vector2(314, 318)
	next.pressed.connect(_turn.bind(1))
	_binder_bits.add_child(next)
	var hint := Label.new()
	hint.text = "Arrows: choose   E: open card   Tab: items   B: close"
	hint.modulate = Color(1, 1, 1, 0.7)
	hint.position = Vector2(8, 340)
	_binder_bits.add_child(hint)
	_build_items(holder)

	# One card, large, over the binder.
	_detail = Control.new()
	_detail.set_anchors_preset(Control.PRESET_FULL_RECT)
	_detail.visible = false
	_root.add_child(_detail)
	var shade := ColorRect.new()
	shade.color = Color(0.02, 0.03, 0.08, 0.75)
	shade.set_anchors_preset(Control.PRESET_FULL_RECT)
	shade.gui_input.connect(func(e: InputEvent) -> void:
		if e is InputEventMouseButton and e.pressed:
			_close_detail())
	_detail.add_child(shade)
	var box := HBoxContainer.new()
	box.set_anchors_preset(Control.PRESET_CENTER)
	box.grow_horizontal = Control.GROW_DIRECTION_BOTH
	box.grow_vertical = Control.GROW_DIRECTION_BOTH
	box.add_theme_constant_override(&"separation", 16)
	_detail.add_child(box)
	var card_holder := Control.new()
	card_holder.custom_minimum_size = CardView.SIZE * 1.6
	box.add_child(card_holder)
	_detail_view = CardView.new()
	_detail_view.scale = Vector2.ONE * 1.6
	card_holder.add_child(_detail_view)
	var side := PanelContainer.new()
	side.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	box.add_child(side)
	var side_col := VBoxContainer.new()
	side_col.custom_minimum_size.x = 110
	side_col.add_theme_constant_override(&"separation", 6)
	side.add_child(side_col)
	_detail_info = Label.new()
	side_col.add_child(_detail_info)
	_detail_actions = VBoxContainer.new()
	side_col.add_child(_detail_actions)
	var detail_hint := Label.new()
	detail_hint.text = "E: turn over\nEsc: back"
	detail_hint.modulate = Color(1, 1, 1, 0.7)
	side_col.add_child(detail_hint)


func _on_pocket_input(event: InputEvent, index: int) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		_open_detail(index)


# ---------------------------------------------------------------- items page

func _set_page(p: int) -> void:
	page = p
	_item_selected = 0
	_refresh()


## The satchel: a list of what you carry on the left, the chosen item on a parchment
## page on the right with a Use button.
func _build_items(holder: Control) -> void:
	_items_page = Control.new()
	_items_page.position = Vector2(20, 22)
	_items_page.size = Vector2(536, 310)
	_items_page.visible = false
	holder.add_child(_items_page)
	var row := HBoxContainer.new()
	row.add_theme_constant_override(&"separation", 10)
	row.size = _items_page.size
	_items_page.add_child(row)
	var left := PanelContainer.new()
	left.custom_minimum_size = Vector2(250, 300)
	row.add_child(left)
	var left_col := VBoxContainer.new()
	left.add_child(left_col)
	var heading := Label.new()
	heading.theme_type_variation = &"TitleLabel"
	heading.text = "Satchel"
	left_col.add_child(heading)
	_item_list = VBoxContainer.new()
	_item_list.add_theme_constant_override(&"separation", 2)
	left_col.add_child(_item_list)
	var page_panel := PanelContainer.new()
	page_panel.theme_type_variation = &"DialoguePanel"
	page_panel.custom_minimum_size = Vector2(270, 300)
	row.add_child(page_panel)
	var margin := MarginContainer.new()
	for side in ["left", "right", "top", "bottom"]:
		margin.add_theme_constant_override("margin_" + side, 12)
	page_panel.add_child(margin)
	var col := VBoxContainer.new()
	col.add_theme_constant_override(&"separation", 8)
	margin.add_child(col)
	_item_icon = TextureRect.new()
	_item_icon.custom_minimum_size = Vector2(64, 64)
	_item_icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_item_icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	col.add_child(_item_icon)
	_item_name = Label.new()
	_item_name.theme_type_variation = &"InkLabel"
	_item_name.add_theme_font_override(&"font", preload("res://assets/fonts/virelia_title.tres"))
	_item_name.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	col.add_child(_item_name)
	_item_text = Label.new()
	_item_text.theme_type_variation = &"InkLabel"
	_item_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_item_text.custom_minimum_size.x = 240
	col.add_child(_item_text)
	_item_use = Button.new()
	_item_use.text = "Use"
	_item_use.focus_mode = Control.FOCUS_NONE
	_item_use.pressed.connect(_use_selected)
	col.add_child(_item_use)
	var hint := Label.new()
	hint.text = "Up/Down: choose   E: use   H: quick heal   Tab: binder   Esc: close"
	hint.modulate = Color(1, 1, 1, 0.7)
	hint.position = Vector2(-12, 318)
	_items_page.add_child(hint)
	EventBus.items_changed.connect(_refresh)


func _carried() -> Array[ItemData]:
	var out: Array[ItemData] = []
	for item in Items.all_items():
		if GameState.item_count(item.id) > 0:
			out.append(item)
	return out


func _fill_items() -> void:
	_title.text = ""
	var player := get_tree().get_first_node_in_group(&"player") as Player
	_status.text = "Gold: %d   Hearts: %d / %d" % [GameState.currency, player.health if player else 0,
		player.max_health if player else 0]
	for child in _item_list.get_children():
		child.queue_free()
	_item_rows.clear()
	var carried := _carried()
	_item_selected = clampi(_item_selected, 0, maxi(0, carried.size() - 1))
	for i in carried.size():
		var item := carried[i]
		var line := Button.new()
		line.toggle_mode = true
		line.button_pressed = i == _item_selected
		line.focus_mode = Control.FOCUS_NONE
		line.alignment = HORIZONTAL_ALIGNMENT_LEFT
		line.icon = item.icon
		line.expand_icon = false
		line.text = "  %s   x%d" % [item.display_name, GameState.item_count(item.id)]
		line.pressed.connect(func() -> void:
			_item_selected = i
			_fill_items())
		_item_list.add_child(line)
		_item_rows.append(line)
	if carried.is_empty():
		var none := Label.new()
		none.text = "Nothing in your satchel.\nGreta's Provisions in Kalmora\nsells bread and tonics."
		_item_list.add_child(none)
		_item_icon.texture = null
		_item_name.text = "Empty"
		_item_text.text = "Healing food and tonics you buy are kept here. Use them from this page, or press H to eat or drink the best one for your wounds."
		_item_use.disabled = true
		return
	var chosen := carried[_item_selected]
	_item_icon.texture = chosen.icon
	_item_name.text = chosen.display_name
	_item_text.text = chosen.description
	_item_use.disabled = player == null or (chosen.heal > 0 and player.health >= player.max_health)
	_item_use.text = "Use" if not _item_use.disabled else "You're at full health"


func _use_selected() -> void:
	var carried := _carried()
	if _item_selected < carried.size() and GameState.use_item(carried[_item_selected].id):
		EventBus.notify.emit("Used %s." % carried[_item_selected].display_name)
	_refresh()


func _items_input(event: InputEvent) -> void:
	if event.is_action_pressed(&"pause") or event.is_action_pressed(&"binder") or event.is_action_pressed(&"items") \
			or event.is_action_pressed(&"ui_cancel"):
		close()
	elif event.is_action_pressed(&"ui_accept") or event.is_action_pressed(&"interact"):
		_use_selected()
	elif event.is_action_pressed(&"ui_up") or event.is_action_pressed(&"move_up"):
		_item_selected = maxi(0, _item_selected - 1)
		_fill_items()
	elif event.is_action_pressed(&"ui_down") or event.is_action_pressed(&"move_down"):
		_item_selected += 1
		_fill_items()
	elif event.is_action_pressed(&"quick_heal"):
		Items.quick_heal()
		_refresh()
