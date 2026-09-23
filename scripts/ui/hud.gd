extends CanvasLayer
## Health, currency, and the public race tracker (card counts only, never which cards).

const NAMES: Dictionary[StringName, String] = {
	&"player": "You", &"hoarder": "Hoarder", &"raider": "Raider", &"runner": "Runner",
}

@onready var health_label: Label = %HealthLabel
@onready var currency_label: Label = %CurrencyLabel
@onready var tracker_label: Label = %TrackerLabel
@onready var toast_label: Label = %ToastLabel
@onready var spell_label: Label = %SpellLabel

var _toast_tween: Tween
var _boss_bar: Control
var _boss_fill: ColorRect
var _boss_label: Label


func _ready() -> void:
	EventBus.tracker_changed.connect(_on_tracker_changed)
	EventBus.currency_changed.connect(func(amount: int) -> void: currency_label.text = "%d gold" % amount)
	EventBus.card_added.connect(_on_card_added)
	EventBus.card_stolen.connect(_on_card_stolen)
	EventBus.stealth_failed.connect(_on_stealth_failed)
	EventBus.combat_won.connect(_on_combat_won)
	EventBus.gate_opened.connect(_on_gate_opened)
	EventBus.boss_bar.connect(_on_boss_bar)
	EventBus.boss_returned.connect(_on_boss_returned)
	_build_boss_bar()
	RivalDirector.rival_departed.connect(_on_rival_departed)
	RivalDirector.rival_arrived.connect(_on_rival_arrived)
	EventBus.notify.connect(_toast)
	EventBus.card_added.connect(_update_spells.unbind(2))
	EventBus.card_consumed.connect(_update_spells.unbind(3))
	EventBus.card_stolen.connect(_update_spells.unbind(4))
	_update_spells()
	_on_tracker_changed(GameState.tracker_counts())
	currency_label.text = "%d gold" % GameState.currency
	toast_label.text = ""
	if GameState.pending_notice != "":
		_toast.call_deferred(GameState.pending_notice)
		GameState.pending_notice = ""
	var player := get_tree().get_first_node_in_group(&"player") as Player
	if player:
		player.health_changed.connect(_on_health_changed)
		_on_health_changed(player.health, player.max_health)


func _on_health_changed(current: int, maximum: int) -> void:
	health_label.text = "HP %d/%d" % [current, maximum]


func _on_tracker_changed(counts: Dictionary) -> void:
	var total := CardDatabase.final_set().size()
	var lines: PackedStringArray = []
	for id in counts:
		lines.append("%s  %d/%d" % [NAMES.get(id, String(id)), counts[id], total])
	tracker_label.text = "\n".join(lines)


func _on_card_added(collector: StringName, card_id: StringName) -> void:
	if collector == GameState.PLAYER:
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
	_boss_bar = Control.new()
	_boss_bar.set_anchors_preset(Control.PRESET_CENTER_TOP)
	_boss_bar.position = Vector2(-110, 8)
	_boss_bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_boss_bar.visible = false
	$Root.add_child(_boss_bar)
	_boss_label = Label.new()
	_boss_label.add_theme_font_size_override("font_size", 10)
	_boss_label.add_theme_color_override("font_outline_color", Color.BLACK)
	_boss_label.add_theme_constant_override("outline_size", 4)
	_boss_label.size = Vector2(220, 14)
	_boss_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_boss_bar.add_child(_boss_label)
	var back := ColorRect.new()
	back.color = Color(0, 0, 0, 0.7)
	back.position = Vector2(0, 16)
	back.size = Vector2(220, 6)
	_boss_bar.add_child(back)
	_boss_fill = ColorRect.new()
	_boss_fill.color = Color(0.45, 0.8, 0.35)
	_boss_fill.position = Vector2(1, 17)
	_boss_fill.size = Vector2(218, 4)
	_boss_bar.add_child(_boss_fill)


func _on_boss_bar(boss_name: String, current: int, maximum: int, shown: bool) -> void:
	_boss_bar.visible = shown
	_boss_label.text = boss_name
	var frac := float(current) / maximum if maximum > 0 else 0.0
	_boss_fill.size.x = 218.0 * frac
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


func _update_spells() -> void:
	var n := GameState.collection(GameState.PLAYER).count(CardSpells.PICKPOCKET)
	spell_label.text = "Q  Pickpocket's Whisper x%d" % n if n > 0 else ""


func _card_name(card_id: StringName) -> String:
	var card := CardDatabase.get_card(card_id)
	return card.display_name if card else String(card_id)


func _toast(text: String) -> void:
	toast_label.text = text
	toast_label.modulate.a = 1.0
	if _toast_tween:
		_toast_tween.kill()
	_toast_tween = create_tween()
	_toast_tween.tween_interval(2.0)
	_toast_tween.tween_property(toast_label, "modulate:a", 0.0, 0.5)
