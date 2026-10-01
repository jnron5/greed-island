extends CanvasLayer
## Autoload "CardReveal": the first time the player gets a card of a kind, the game
## pauses and the card pops up in the middle of the screen. E turns it over to read
## its lore; attack, dash, Enter, Esc or a click put it away. Several new cards at
## once queue up. Off in headless runs (tests) unless `force` is set.

const SCALE := 1.6
const CENTER_Y := 180.0
const HINT_FRONT := "E  turn over      J / Space  continue"
const HINT_BACK := "E  turn back      J / Space  continue"
const MIN_SHOW := 0.5           # seconds before it can be dismissed
const RARITY_NAMES := { CardData.Rarity.COMMON: "Common", CardData.Rarity.RARE: "Rare", CardData.Rarity.BOSS: "Boss" }
const CATEGORY_NAMES := { CardData.Category.SET: "Set card", CardData.Category.BUFF_TEMP: "Buff",
		CardData.Category.BUFF_PASSIVE: "Passive buff", CardData.Category.SPELL: "Spell" }

## Show reveals even when running headless (for tests).
var force := false
var showing := false
var _flipping := false


## True while `card_id` is on screen or waiting to be (the HUD skips its toast then).
func revealing(card_id: StringName) -> bool:
	return _queue.has(card_id) or (showing and _view.card != null and _view.card.id == card_id)

var _queue: Array[StringName] = []
## Cards in the queue that are being shown as lost (fainting), not found.
var _lost: Dictionary = {}
var _root: Control
var _shown_for := 0.0
var _dim: ColorRect
var _pivot: Control
var _view: CardView
var _shine: ColorRect
var _title: Label
var _kind: Label
var _hint: Label


func _ready() -> void:
	layer = 20
	process_mode = Node.PROCESS_MODE_ALWAYS
	_build()
	visible = false
	EventBus.card_added.connect(_on_card_added)


func _on_card_added(collector: StringName, card_id: StringName) -> void:
	if collector != GameState.PLAYER or not GameState.mark_card_seen(card_id):
		return
	if DisplayServer.get_name() == "headless" and not force:
		return
	_queue.append(card_id)
	if not showing:
		_show_next.call_deferred()


## Shows a card the player has just lost (they went down and dropped it), so they
## know what to go back for.
func show_lost(card_id: StringName) -> void:
	if card_id == &"" or (DisplayServer.get_name() == "headless" and not force):
		return
	_lost[card_id] = true
	_queue.append(card_id)
	if not showing:
		_show_next.call_deferred()


func _show_next() -> void:
	if showing or _queue.is_empty():
		return
	var next_id: StringName = _queue.pop_front()
	var lost: bool = _lost.has(next_id)
	_lost.erase(next_id)
	_title.text = "You lost a card" if lost else "New card!"
	_title.add_theme_color_override(&"font_color", Color(1.0, 0.5, 0.42) if lost else Color(1.0, 0.86, 0.45))
	var card := CardDatabase.get_card(next_id)
	if card == null:
		_show_next()
		return
	showing = true
	_shown_for = 0.0
	_view.card = card
	_view.showing_back = false
	_hint.text = HINT_FRONT
	_kind.text = ("It fell where you went down. Go back for it before somebody else does." if lost
		else "%s · %s" % [RARITY_NAMES.get(card.rarity, ""), CATEGORY_NAMES.get(card.category, "")])
	visible = true
	GameState.push_menu()
	get_tree().paused = true
	# Pop in: from small and tilted to full size with a little overshoot, then a shine.
	_place(0.0)
	_dim.modulate.a = 0.0
	for label in [_title, _kind, _hint]:
		label.modulate.a = 0.0
	_pivot.scale = Vector2.ONE * 0.2
	_pivot.rotation = -0.35
	_shine.position.x = -60
	var tw := create_tween().set_parallel()
	tw.tween_property(_dim, "modulate:a", 1.0, 0.25)
	tw.tween_property(_pivot, "scale", Vector2.ONE * SCALE, 0.45).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw.tween_property(_pivot, "rotation", 0.0, 0.45).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw.tween_property(_title, "modulate:a", 1.0, 0.3).set_delay(0.2)
	tw.tween_property(_kind, "modulate:a", 1.0, 0.3).set_delay(0.35)
	tw.tween_property(_hint, "modulate:a", 0.8, 0.3).set_delay(0.8)
	tw.tween_property(_shine, "position:x", CardView.SIZE.x + 110, 0.8).set_delay(0.5).set_trans(Tween.TRANS_SINE)


## Turns the card over (front to back or back to front): it narrows to an edge,
## swaps sides, and widens again.
func flip() -> void:
	if not showing or _flipping:
		return
	_flipping = true
	var tw := create_tween()
	tw.tween_property(_pivot, "scale:x", 0.0, 0.12).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN)
	tw.tween_callback(func() -> void:
		_view.showing_back = not _view.showing_back
		_hint.text = HINT_BACK if _view.showing_back else HINT_FRONT)
	tw.tween_property(_pivot, "scale:x", SCALE, 0.12).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	await tw.finished
	_flipping = false


func dismiss() -> void:
	if not showing:
		return
	showing = false
	var tw := create_tween().set_parallel()
	tw.tween_property(_dim, "modulate:a", 0.0, 0.2)
	tw.tween_property(_pivot, "scale", Vector2.ONE * 0.1, 0.2).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_IN)
	for label in [_title, _kind, _hint]:
		tw.tween_property(label, "modulate:a", 0.0, 0.15)
	await tw.finished
	visible = false
	get_tree().paused = false
	GameState.pop_menu()
	if not _queue.is_empty():
		_show_next()


func _process(delta: float) -> void:
	if showing:
		_shown_for += delta
		_place(sin(_shown_for * 2.2) * 2.0)   # a gentle float


func _input(event: InputEvent) -> void:
	if not showing or _shown_for < MIN_SHOW:
		return
	if not event.is_pressed() or event.is_echo():
		return
	if event.is_action(&"interact"):
		get_viewport().set_input_as_handled()
		flip()
	elif (event is InputEventMouseButton or event.is_action(&"sword") or event.is_action(&"ui_accept")
			or event.is_action(&"pause") or event.is_action(&"dash")):
		get_viewport().set_input_as_handled()
		dismiss()


## Centres the card on screen (whatever the window's width), `bob` px lower.
func _place(bob: float) -> void:
	_pivot.position = Vector2(_root.size.x / 2.0, CENTER_Y + bob)


func _build() -> void:
	var root := Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(root)
	_root = root
	_dim = ColorRect.new()
	_dim.color = Color(0.02, 0.03, 0.08, 0.8)
	_dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.add_child(_dim)
	var strip := ColorRect.new()          # keeps the HUD's own text out from under the hints
	strip.color = Color(0.01, 0.01, 0.03, 0.85)
	strip.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	strip.offset_top = -36
	_dim.add_child(strip)
	# The card turns and scales about its centre.
	_pivot = Control.new()
	root.add_child(_pivot)
	var holder := Control.new()
	holder.position = -CardView.SIZE / 2.0
	holder.size = CardView.SIZE
	_pivot.add_child(holder)
	_view = CardView.new()
	holder.add_child(_view)
	# The shine is clipped to the card's shape.
	var mask := TextureRect.new()
	mask.texture = CardView.silhouette()
	mask.clip_children = CanvasItem.CLIP_CHILDREN_ONLY
	holder.add_child(mask)
	_shine = ColorRect.new()
	_shine.color = Color(1, 1, 0.9, 0.35)
	_shine.size = Vector2(10, 260)
	_shine.position = Vector2(-60, -50)
	_shine.rotation = 0.35
	mask.add_child(_shine)
	_title = _label(root, "New card!", 14, Color(1.0, 0.86, 0.45), 8)
	_kind = _label(root, "", 9, Color(0.75, 0.88, 0.95), 327)
	_hint = _label(root, HINT_FRONT, 8, Color(0.8, 0.8, 0.8), 342)


func _label(parent: Control, text: String, size: int, color: Color, y: float) -> Label:
	var label := Label.new()
	label.text = text
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.set_anchors_preset(Control.PRESET_TOP_WIDE)
	label.offset_top = y
	label.offset_bottom = y + size + 6
	label.add_theme_font_size_override(&"font_size", size)
	label.add_theme_color_override(&"font_color", color)
	label.add_theme_color_override(&"font_outline_color", Color.BLACK)
	label.add_theme_constant_override(&"outline_size", 4)
	parent.add_child(label)
	return label
