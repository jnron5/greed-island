class_name ShopPanel
extends MenuPanel
## A shop: buy what the shopkeeper stocks (satchel items like bread and tonics, or
## spell/buff cards), and, at card merchants, sell set cards. Sold cards leave the
## island for good (GameState removes them from world supply).

var _stock: Array[StringName] = []
var _buys_cards := true


func _init() -> void:
	title = "Merchant"


func _ready() -> void:
	super()
	add_to_group(&"shop_panel")
	EventBus.items_changed.connect(func() -> void:
		if is_open:
			rebuild())


func open_with(stock: Array[StringName], shop_title := "Merchant", buys_cards := true) -> void:
	_stock = stock
	_buys_cards = buys_cards
	set_title(shop_title)
	open()


func _status_text() -> String:
	return "Gold: %d" % GameState.currency


func _build_rows() -> void:
	add_header("Buy")
	for id in _stock:
		var item := Items.get_item(id)
		if item:
			add_row(item.display_name, Color(0.97, 0.92, 0.8), "%dg   (have %d)" % [item.price, GameState.item_count(id)], [
				["Buy", func() -> void: GameState.buy_item(id), GameState.currency >= item.price],
			], item.icon)
			continue
		var card := CardDatabase.get_card(id)
		if card == null:
			continue
		var owned := GameState.collection(GameState.PLAYER).count(id)
		add_row(card.display_name, card_color(card), "%dg   (have %d)" % [card.shop_price, owned], [
			["Buy", func() -> void: GameState.buy_card(GameState.PLAYER, id), GameState.currency >= card.shop_price],
		])

	if not _buys_cards:
		return
	add_header("Sell (sold cards leave the island for good)")
	var col := GameState.collection(GameState.PLAYER)
	var any := false
	for id in col.card_ids():
		var card := CardDatabase.get_card(id)
		if card.category != CardData.Category.SET or card.sell_value <= 0:
			continue
		any = true
		add_row(card.display_name, card_color(card), "x%d" % col.count(id), [
			["Sell %dg" % card.sell_value, func() -> void: GameState.sell_card(GameState.PLAYER, id), true],
		])
	if not any:
		add_header("  Nothing to sell.")
