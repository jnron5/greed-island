class_name ShopPanel
extends MenuPanel
## Town merchant: buy spell/buff cards, sell set cards. Sold cards leave the
## island for good (GameState removes them from world supply).

var _stock: Array[StringName] = []


func _init() -> void:
	title = "Merchant"


func _ready() -> void:
	super()
	add_to_group(&"shop_panel")


func open_with(stock: Array[StringName]) -> void:
	_stock = stock
	open()


func _status_text() -> String:
	return "Gold: %d" % GameState.currency


func _build_rows() -> void:
	add_header("Buy")
	for id in _stock:
		var card := CardDatabase.get_card(id)
		if card == null:
			continue
		var owned := GameState.collection(GameState.PLAYER).count(id)
		add_row(card.display_name, card_color(card), "%dg   (have %d)" % [card.shop_price, owned], [
			["Buy", func() -> void: GameState.buy_card(GameState.PLAYER, id), GameState.currency >= card.shop_price],
		])

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
