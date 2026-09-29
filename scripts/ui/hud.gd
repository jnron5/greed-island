extends CanvasLayer
## Health, currency, the public race tracker (card counts only, never which cards),
## the active quest, and short messages. Built from the UI kit (assets/ui/): a heart
## bar, purse and race counts in a small window top-left with the quests under it
## (nothing on the right, so the view stays clear), messages on a name plate at the
## bottom.

const NAMES: Dictionary[StringName, String] = {
	&"player": "You", &"hoarder": "Hoarder", &"raider": "Raider", &"runner": "Runner",
}
## Each collector's cloak colour (see the character notes in CLAUDE.md).
const COLORS: Dictionary[StringName, Color] = {
	&"player": Color(0.86, 0.62, 0.36), &"hoarder": Color(0.62, 0.32, 0.5),
	&"raider": Color(0.55, 0.55, 0.6), &"runner": Color(0.62, 0.82, 0.96),
}
const HEART_BAR := preload("res://assets/ui/bar_heart.png")
const LONG_BAR := preload("res://assets/ui/bar_long.png")
const COIN := preload("res://assets/ui/medal_star.png")
const SLOT := preload("res://assets/ui/slot.png")
const BAR_FILL := Rect2(15, 5, 37, 4)        # inside bar_heart.png
const HINT := "J Sword   K Pistol   Space Dash   Q Pickpocket   E Talk/Steal   H Heal   B Binder   I Items"

var health_label: Label
var currency_label: Label
var toast_label: Label
var spell_label: Label
var quest_label: Label

var _root: Control
var _heart_fill: ColorRect
var _race_rows: HBoxContainer
var _quest_panel: PanelContainer
var _spell_box: Control
var _toast_plate: PanelContainer
var _toast_tween: Tween
var _area_box: VBoxContainer
var _area_title: Label
var _area_sub: Label
var _area_tween: Tween
var _boss_bar: Control
var _boss_fill: ColorRect
var _boss_label: Label
var _corner: Array[Control] = []
var _hint: Label
var _hint_time := 90.0


func _ready() -> void:
	layer = 3  # above the night grade (NightGrade, layer 1)
	_root = $Root
	_build()
	EventBus.tracker_changed.connect(_on_tracker_changed)
	EventBus.currency_changed.connect(func(amount: int) -> void: currency_label.text = str(amount))
	EventBus.card_added.connect(_on_card_added)
	EventBus.card_stolen.connect(_on_card_stolen)
	EventBus.stealth_failed.connect(_on_stealth_failed)
	EventBus.combat_won.connect(_on_combat_won)
	EventBus.gate_opened.connect(_on_gate_opened)
	EventBus.boss_bar.connect(_on_boss_bar)
	EventBus.boss_returned.connect(_on_boss_returned)
	_build_boss_bar()
	Quests.quest_changed.connect(_update_quest.unbind(2))
	# Favours count items, gold, cards and kills: refresh the tracker when those change.
	EventBus.items_changed.connect(_update_quest)
	EventBus.currency_changed.connect(_update_quest.unbind(1))
	EventBus.card_added.connect(_update_quest.unbind(2))
	EventBus.monster_defeated.connect(_update_quest.unbind(2))
	EventBus.notify.connect(_update_quest.unbind(1))
	_update_quest()
	RivalDirector.rival_departed.connect(_on_rival_departed)
	RivalDirector.rival_arrived.connect(_on_rival_arrived)
	EventBus.notify.connect(_toast)
	EventBus.area_entered.connect(_show_area)
	EventBus.card_added.connect(_update_spells.unbind(2))
	EventBus.card_consumed.connect(_update_spells.unbind(3))
	EventBus.card_stolen.connect(_update_spells.unbind(4))
	_update_spells()
	_on_tracker_changed(GameState.tracker_counts())
	currency_label.text = str(GameState.currency)
	_toast_plate.modulate.a = 0.0
	if GameState.pending_notice != "":
		_toast.call_deferred(GameState.pending_notice)
		GameState.pending_notice = ""
	var player := get_tree().get_first_node_in_group(&"player") as Player
	if player:
		player.health_changed.connect(_on_health_changed)
		_on_health_changed(player.health, player.max_health)


func _build() -> void:
	# Top-left: hearts and purse.
	var left := VBoxContainer.new()
	left.position = Vector2(4, 4)
	left.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(left)
	var status := PanelContainer.new()
	status.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	left.add_child(status)
	var col := VBoxContainer.new()
	col.add_theme_constant_override(&"separation", 2)
	status.add_child(col)
	var hp_row := HBoxContainer.new()
	col.add_child(hp_row)
	var bar := TextureRect.new()
	bar.texture = HEART_BAR
	hp_row.add_child(bar)
	_heart_fill = ColorRect.new()
	_heart_fill.color = Color(0.86, 0.22, 0.24)
	_heart_fill.position = BAR_FILL.position
	_heart_fill.size = BAR_FILL.size
	bar.add_child(_heart_fill)
	var shine := ColorRect.new()
	shine.color = Color(1, 1, 1, 0.3)
	shine.size = Vector2(BAR_FILL.size.x, 1)
	_heart_fill.add_child(shine)
	health_label = Label.new()
	hp_row.add_child(health_label)
	var gold_row := HBoxContainer.new()
	col.add_child(gold_row)
	var coin := TextureRect.new()
	coin.texture = COIN
	gold_row.add_child(coin)
	currency_label = Label.new()
	currency_label.theme_type_variation = &"TitleLabel"
	currency_label.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	gold_row.add_child(currency_label)

	# Under the hearts and purse: the race as one slim row (a dot and a count per
	# collector), then the quests as plain outlined text. Everything sits in the
	# top-left corner and fades when the player walks behind it (_process), so no
	# window covers the play area.
	_race_rows = HBoxContainer.new()
	_race_rows.add_theme_constant_override(&"separation", 6)
	col.add_child(_race_rows)
	_quest_panel = PanelContainer.new()
	var backing := StyleBoxFlat.new()
	backing.bg_color = Color(0.02, 0.08, 0.1, 0.45)
	backing.set_corner_radius_all(3)
	backing.set_content_margin_all(4)
	_quest_panel.add_theme_stylebox_override(&"panel", backing)
	_quest_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	left.add_child(_quest_panel)
	quest_label = Label.new()
	quest_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	quest_label.custom_minimum_size.x = 170
	quest_label.add_theme_font_size_override(&"font_size", 10)
	quest_label.add_theme_color_override(&"font_color", Color(1.0, 0.93, 0.72))
	_quest_panel.add_child(quest_label)
	_corner = [status, _quest_panel]

	# Bottom-left: the spell ready to cast, and the controls.
	_spell_box = HBoxContainer.new()
	_spell_box.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
	_spell_box.offset_left = 6
	_spell_box.offset_top = -40
	_root.add_child(_spell_box)
	var slot := TextureRect.new()
	slot.texture = SLOT
	_spell_box.add_child(slot)
	spell_label = Label.new()
	spell_label.add_theme_color_override(&"font_color", Color(0.6, 0.92, 0.96))
	_spell_box.add_child(spell_label)
	# The controls, for the first minute and a half of play (the pause menu keeps them).
	_hint = Label.new()
	_hint.text = HINT
	_hint.modulate = Color(1, 1, 1, 0.65)
	_hint.add_theme_font_size_override(&"font_size", 9)
	_hint.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
	_hint.offset_left = 6
	_hint.offset_top = -16
	_root.add_child(_hint)

	# Messages on a name plate at the bottom centre.
	_toast_plate = PanelContainer.new()
	_toast_plate.theme_type_variation = &"NamePlate"
	_toast_plate.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	_toast_plate.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_toast_plate.offset_top = -62
	_toast_plate.offset_bottom = -40
	_toast_plate.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(_toast_plate)
	toast_label = Label.new()
	toast_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_toast_plate.add_child(toast_label)
	_build_area_banner()


## The area's name, large, in the upper third: a gold title (the part before a comma)
## over a smaller subtitle (the rest), between two gold rules; it fades in, holds and
## fades out. Rooms get a smaller one.
func _show_area(area: String, interior: bool) -> void:
	var parts := area.split(",", false, 1)
	_area_title.text = parts[0].strip_edges()
	_area_title.add_theme_font_size_override(&"font_size", 20 if interior else 32)
	_area_sub.text = parts[1].strip_edges() if parts.size() > 1 else ""
	_area_sub.visible = _area_sub.text != ""
	if _area_tween:
		_area_tween.kill()
	_area_box.modulate.a = 0.0
	_area_tween = create_tween()
	_area_tween.tween_property(_area_box, "modulate:a", 1.0, 0.5)
	_area_tween.tween_interval(2.4)
	_area_tween.tween_property(_area_box, "modulate:a", 0.0, 0.9)


func _build_area_banner() -> void:
	_area_box = VBoxContainer.new()
	_area_box.set_anchors_preset(Control.PRESET_CENTER_TOP)
	_area_box.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_area_box.offset_top = 58
	_area_box.alignment = BoxContainer.ALIGNMENT_CENTER
	_area_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_area_box.add_theme_constant_override(&"separation", 2)
	_area_box.modulate.a = 0.0
	_root.add_child(_area_box)
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override(&"separation", 10)
	_area_box.add_child(row)
	for side in 2:
		var rule := ColorRect.new()
		rule.color = Color(1.0, 0.84, 0.45, 0.85)
		rule.custom_minimum_size = Vector2(46, 2)
		rule.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		row.add_child(rule)
		if side == 0:
			_area_title = Label.new()
			_area_title.theme_type_variation = &"TitleLabel"
			_area_title.add_theme_constant_override(&"outline_size", 6)
			_area_title.add_theme_color_override(&"font_outline_color", Color(0.08, 0.05, 0.03))
			row.add_child(_area_title)
	_area_sub = Label.new()
	_area_sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_area_sub.add_theme_font_size_override(&"font_size", 12)
	_area_box.add_child(_area_sub)


func _on_health_changed(current: int, maximum: int) -> void:
	health_label.text = "%d/%d" % [current, maximum]
	var frac := clampf(float(current) / maxi(maximum, 1), 0.0, 1.0)
	_heart_fill.size.x = roundf(BAR_FILL.size.x * frac)


func _on_tracker_changed(counts: Dictionary) -> void:
	for child in _race_rows.get_children():
		child.queue_free()
	for id in counts:
		var dot := ColorRect.new()
		dot.color = COLORS.get(id, Color.WHITE)
		dot.custom_minimum_size = Vector2(5, 5)
		dot.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		dot.tooltip_text = NAMES.get(id, String(id))
		_race_rows.add_child(dot)
		var count := Label.new()
		count.text = "%s %d" % [NAMES.get(id, String(id)), counts[id]]
		count.add_theme_font_size_override(&"font_size", 9)
		_race_rows.add_child(count)


## The corner UI fades while the player stands behind it; the controls hint fades
## out after a while.
func _process(delta: float) -> void:
	var player := get_tree().get_first_node_in_group(&"player") as Node2D
	if player:
		var at := player.get_global_transform_with_canvas().origin
		for panel in _corner:
			var r := panel.get_global_rect().grow(18)
			panel.modulate.a = move_toward(panel.modulate.a, 0.3 if r.has_point(at) else 1.0, delta * 4.0)
	if _hint_time > 0.0:
		_hint_time -= delta
		_hint.modulate.a = clampf(_hint_time / 3.0, 0.0, 0.65)
		_hint.visible = _hint_time > 0.0


func _on_card_added(collector: StringName, card_id: StringName) -> void:
	# A card's first copy gets the full-screen reveal instead of a toast.
	if collector == GameState.PLAYER and not CardReveal.revealing(card_id):
		_toast("Picked up: %s" % _card_name(card_id))


func _on_card_stolen(thief: StringName, victim: StringName, card_id: StringName, method: StringName) -> void:
	if thief == GameState.PLAYER:
		var verb := "Lifted %s from the %s unnoticed" if method == &"stealth" else "Pickpocketed %s from the %s!"
		_toast(verb % [_card_name(card_id), NAMES.get(victim, String(victim))])
	elif victim == GameState.PLAYER:
		if method == &"stealth":
			_toast("Your satchel feels lighter...")  # Quiet: you don't see who or what.
		else:
			_toast("The %s stole your %s!" % [NAMES.get(thief, String(thief)), _card_name(card_id)])


func _on_combat_won(winner: StringName, loser: StringName, card_id: StringName) -> void:
	var prize := " and took %s" % _card_name(card_id) if card_id != &"" else ""
	if winner == GameState.PLAYER:
		_toast("You beat the %s%s!" % [NAMES.get(loser, String(loser)), prize])
	elif loser == GameState.PLAYER:
		_toast("The %s beat you%s!" % [NAMES.get(winner, String(winner)), prize])


## Boss name and health across the top of the screen while a fight is on.
func _build_boss_bar() -> void:
	_boss_bar = PanelContainer.new()
	_boss_bar.set_anchors_preset(Control.PRESET_CENTER_TOP)
	_boss_bar.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_boss_bar.offset_top = 4
	_boss_bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_boss_bar.visible = false
	_root.add_child(_boss_bar)
	var col := VBoxContainer.new()
	col.add_theme_constant_override(&"separation", 1)
	_boss_bar.add_child(col)
	_boss_label = Label.new()
	_boss_label.theme_type_variation = &"TitleLabel"
	_boss_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	col.add_child(_boss_label)
	var bar := TextureRect.new()
	bar.texture = LONG_BAR
	col.add_child(bar)
	_boss_fill = ColorRect.new()
	_boss_fill.position = Vector2(15, 5)
	_boss_fill.size = Vector2(95, 4)
	bar.add_child(_boss_fill)


func _on_boss_bar(boss_name: String, current: int, maximum: int, shown: bool) -> void:
	_boss_bar.visible = shown
	_boss_label.text = boss_name
	var frac := float(current) / maximum if maximum > 0 else 0.0
	_boss_fill.size.x = roundf(95.0 * frac)
	_boss_fill.color = Color(0.9, 0.35, 0.25) if frac <= 0.5 else Color(0.45, 0.8, 0.35)


func _on_boss_returned(boss_id: StringName, gate_id: StringName) -> void:
	var boss := GameState.boss_data(boss_id)
	var gate := CardDatabase.get_gate(gate_id)
	if boss and gate:
		_toast("Opening the %s stirred something... the %s has returned." % [gate.display_name, boss.display_name])


func _on_gate_opened(gate_id: StringName, by: StringName) -> void:
	if by != GameState.PLAYER:
		var gate := CardDatabase.get_gate(gate_id)
		_toast("The %s paid to open the %s" % [NAMES.get(by, String(by)), gate.display_name if gate else "gate"])


func _on_rival_departed(id: StringName, from_zone: String, to_zone: String) -> void:
	if from_zone == RivalDirector.player_zone():
		_toast("The %s headed for %s" % [NAMES.get(id, String(id)), WorldMap.zone_name(to_zone)])


func _on_rival_arrived(id: StringName, zone: String) -> void:
	if zone == RivalDirector.player_zone():
		_toast("The %s arrived in %s" % [NAMES.get(id, String(id)), WorldMap.zone_name(zone)])


func _on_stealth_failed(thief: StringName, victim: StringName) -> void:
	if thief == GameState.PLAYER:
		_toast("The %s caught you! It's on alert." % NAMES.get(victim, String(victim)))
	elif victim == GameState.PLAYER:
		_toast("You caught the %s reaching for your cards!" % NAMES.get(thief, String(thief)))


func _update_quest() -> void:
	var text := Quests.tracker_text()
	quest_label.text = text
	_quest_panel.visible = text != ""


func _update_spells() -> void:
	var n := GameState.collection(GameState.PLAYER).count(CardSpells.PICKPOCKET)
	spell_label.text = "Q  Pickpocket's Whisper x%d" % n if n > 0 else ""
	_spell_box.visible = n > 0


func _card_name(card_id: StringName) -> String:
	var card := CardDatabase.get_card(card_id)
	return card.display_name if card else String(card_id)


func _toast(text: String) -> void:
	toast_label.text = text
	_toast_plate.reset_size()
	_toast_plate.modulate.a = 1.0
	if _toast_tween:
		_toast_tween.kill()
	_toast_tween = create_tween()
	_toast_tween.tween_interval(2.4)
	_toast_tween.tween_property(_toast_plate, "modulate:a", 0.0, 0.5)
