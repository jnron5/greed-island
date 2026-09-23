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


func _ready() -> void:
	EventBus.tracker_changed.connect(_on_tracker_changed)
	EventBus.currency_changed.connect(func(amount: int) -> void: currency_label.text = "%d gold" % amount)
	EventBus.card_added.connect(_on_card_added)
	EventBus.card_stolen.connect(_on_card_stolen)
	EventBus.notify.connect(_toast)
	EventBus.card_added.connect(_update_spells.unbind(2))
	EventBus.card_consumed.connect(_update_spells.unbind(3))
	EventBus.card_stolen.connect(_update_spells.unbind(4))
	_update_spells()
	_on_tracker_changed(GameState.tracker_counts())
	currency_label.text = "%d gold" % GameState.currency
	toast_label.text = ""
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


func _on_card_stolen(thief: StringName, victim: StringName, card_id: StringName, _method: StringName) -> void:
	if thief == GameState.PLAYER:
		_toast("Pickpocketed %s from the %s!" % [_card_name(card_id), NAMES.get(victim, String(victim))])
	elif victim == GameState.PLAYER:
		_toast("The %s stole your %s!" % [NAMES.get(thief, String(thief)), _card_name(card_id)])


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
