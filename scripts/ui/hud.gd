extends CanvasLayer
## Health, currency, and the public race tracker (card counts only, never which cards).

const NAMES: Dictionary[StringName, String] = {
	&"player": "You", &"hoarder": "Hoarder", &"raider": "Raider", &"runner": "Runner",
}

@onready var health_label: Label = %HealthLabel
@onready var currency_label: Label = %CurrencyLabel
@onready var tracker_label: Label = %TrackerLabel
@onready var toast_label: Label = %ToastLabel


func _ready() -> void:
	EventBus.tracker_changed.connect(_on_tracker_changed)
	EventBus.currency_changed.connect(func(amount: int) -> void: currency_label.text = "%d gold" % amount)
	EventBus.card_added.connect(_on_card_added)
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
	if collector != GameState.PLAYER:
		return
	var card := CardDatabase.get_card(card_id)
	toast_label.text = "Picked up: %s" % (card.display_name if card else String(card_id))
	var tween := create_tween()
	toast_label.modulate.a = 1.0
	tween.tween_interval(1.5)
	tween.tween_property(toast_label, "modulate:a", 0.0, 0.5)
