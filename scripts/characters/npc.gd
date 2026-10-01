class_name Npc
extends CharacterBody2D
## A resident of the island (a dog or cat townsperson). Idles or wanders near
## home, turns to face you, and talks when you press interact nearby. What it
## says comes from the quest system first (Quests.dialogue_for), then its own
## ambient lines, cycling. Then, if they have topics (TalkTopics) or a shop, a
## question list: ask about something, browse their wares, or say goodbye.
## 4-directional animations "idle_<dir>" / "walk_<dir>".

const DIRECTIONS_4: Array[String] = ["east", "south", "west", "north"]
const TALK_RANGE := 34.0

@export var npc_id: StringName
@export var display_name := "Resident"
@export var sprite_frames: SpriteFrames
@export var sprite_offset_y := -26.0
## Ambient things to say, one line per conversation (in order, looping).
@export_multiline var lines: PackedStringArray = []
## 0 = stands still at home.
@export var wander_radius := 0.0
@export var walk_speed := 30.0
## A daily round: points (relative to home) walked in order, pausing at each.
## Overrides wandering.
@export var patrol: PackedVector2Array = []
@export var patrol_pause := 3.0
## Shopkeepers: after talking, open the shop with this stock.
@export var shop_stock: Array[StringName] = []
## Whether this shopkeeper also buys set cards (card merchants do; a baker doesn't).
@export var shop_buys_cards := true
## The shop's name on its window (defaults to the shopkeeper's).
@export var shop_title := ""
## An inn keeper: offers a room for half a day or a full day (Inn).
@export var inn_rooms := false
## What the keeper says when you ask for a room, and when you can't pay.
@export var room_prompt := "A bed, clean sheets, quiet. How long will you sleep?"
@export var room_broke := "That's %d gold. Come back when your purse is heavier."
## A resident who serves a meal at a set hour (Tally's dinner at five): for the
## hour from meal_hour they say meal_lines and the meal mends every heart; in the
## hour before, they say one of pre_meal_lines. -1 = no meal.
@export var meal_hour := -1.0
@export_multiline var meal_lines: PackedStringArray = []
@export_multiline var pre_meal_lines: PackedStringArray = []

## What an inn keeper says when a collector who fainted on the road comes round in
## one of their beds (one per waking, rotating).
@export_multiline var wake_lines: PackedStringArray = []

## Where each resident is in their lines, kept across visits (a scene reload makes
## a new Npc), so coming back doesn't start the same speech over.
static var _next_line: Dictionary = {}

var facing := Vector2.DOWN

var _home := Vector2.ZERO
var _goal := Vector2.ZERO
var _wait := 0.0
var _talking := false
var _patrol_index := 0
var _pausing := true

@onready var sprite: AnimatedSprite2D = $AnimatedSprite2D


func _ready() -> void:
	add_to_group(&"npcs")
	if sprite_frames:
		sprite.sprite_frames = sprite_frames
	sprite.offset.y = sprite_offset_y
	_home = position
	_goal = position
	_wait = randf_range(1.0, 4.0)


func _physics_process(delta: float) -> void:
	if _talking:
		velocity = Vector2.ZERO
	elif not patrol.is_empty():
		_wait -= delta
		var target := _home + patrol[_patrol_index]
		if _pausing:
			velocity = Vector2.ZERO
			if _wait <= 0.0:                      # rested: on to the next stop
				_pausing = false
				_patrol_index = (_patrol_index + 1) % patrol.size()
				_wait = 12.0                      # give up on a stop that can't be reached
		elif position.distance_to(target) < 3.0 or _wait <= 0.0:
			_pausing = true
			_wait = patrol_pause
			velocity = Vector2.ZERO
		else:
			velocity = position.direction_to(target) * walk_speed
	elif wander_radius > 0.0:
		_wait -= delta
		if position.distance_to(_goal) < 3.0:
			velocity = Vector2.ZERO
			if _wait <= 0.0:
				_goal = _home + Vector2.from_angle(randf() * TAU) * randf_range(8.0, wander_radius)
				_wait = randf_range(2.0, 5.0)
		else:
			velocity = position.direction_to(_goal) * walk_speed
			if _wait < -6.0:
				_goal = position  # Stuck against something: give up on this spot.
	move_and_slide()
	_update_animation()
	queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	if _talking or GameState.menus_open > 0 or not event.is_action_pressed(&"interact"):
		return
	var player := get_tree().get_first_node_in_group(&"player") as Node2D
	if player == null or player.global_position.distance_to(global_position) > TALK_RANGE:
		return
	get_viewport().set_input_as_handled()
	talk(player)


func talk(player: Node2D) -> void:
	_talking = true
	facing = global_position.direction_to(player.global_position)
	var said: PackedStringArray = Quests.dialogue_for(npc_id)
	if said.is_empty():
		said = Errands.dialogue_for(npc_id)
	if said.is_empty():
		said = _meal_talk()
	if said.is_empty() and not lines.is_empty():
		said = PackedStringArray([next_line(lines)])
	DialogueBox.say(get_tree(), display_name, said, _done_talking, DialogueBox.portrait_from(sprite.sprite_frames))


## The player has just come round in this keeper's inn: they turn to them and say
## welcome back, then `on_done` runs (the lost card is shown).
func welcome_back(on_done: Callable) -> void:
	var player := get_tree().get_first_node_in_group(&"player") as Node2D
	if player:
		facing = global_position.direction_to(player.global_position)
	var line := next_line(wake_lines) if not wake_lines.is_empty() else "Welcome back. You gave us a fright."
	DialogueBox.say(get_tree(), display_name, PackedStringArray([line]), on_done,
		DialogueBox.portrait_from(sprite.sprite_frames))


## The next of `pool`, one per conversation, looping; remembered across visits.
## Starts somewhere random so two playthroughs don't open the same way.
func next_line(pool: PackedStringArray) -> String:
	var key := String(npc_id) + ":" + str(pool.size())
	if not _next_line.has(key):
		_next_line[key] = randi() % pool.size()
	var i: int = _next_line[key] % pool.size()
	_next_line[key] = i + 1
	return pool[i]


## Around the meal hour: the meal itself (and every heart mended), or the warning
## that it's coming. Empty the rest of the day.
func _meal_talk() -> PackedStringArray:
	if meal_hour < 0.0:
		return PackedStringArray()
	var h := TimeOfDay.hour
	if h >= meal_hour and h < meal_hour + 1.0 and not meal_lines.is_empty():
		var player := get_tree().get_first_node_in_group(&"player") as Player
		if player and player.health < player.max_health:
			player.heal(player.max_health)
			Sfx.play(&"heal")
			EventBus.notify.emit("Dinner. Every heart mended.")
		return meal_lines
	if h >= meal_hour - 1.0 and h < meal_hour and not pre_meal_lines.is_empty():
		return PackedStringArray([next_line(pre_meal_lines)])
	return PackedStringArray()


func _done_talking() -> void:
	Quests.talked_to(npc_id)
	Errands.talked_to(npc_id)
	_offer_topics()


## The question list after a chat: this resident's topics, their shop, goodbye.
func _offer_topics() -> void:
	var topics := TalkTopics.for_npc(npc_id)
	if topics.is_empty() and shop_stock.is_empty() and not inn_rooms:
		_talking = false
		return
	var options := PackedStringArray()
	for topic: Array in topics:
		options.append(topic[0])
	if inn_rooms:
		options.append("I'd like a room")
	if not shop_stock.is_empty():
		options.append("Let me see your wares")
	options.append("Goodbye")
	DialogueBox.ask(get_tree(), display_name, "Anything else?", options, _on_topic,
		DialogueBox.portrait_from(sprite.sprite_frames))


func _on_topic(index: int) -> void:
	var topics := TalkTopics.for_npc(npc_id)
	if index < topics.size():
		DialogueBox.say(get_tree(), display_name, PackedStringArray(topics[index][1]), _offer_topics,
			DialogueBox.portrait_from(sprite.sprite_frames))
		return
	var at := topics.size()
	if inn_rooms:
		if index == at:
			_offer_room()
			return
		at += 1
	_talking = false
	if index == at and not shop_stock.is_empty():
		var shop := get_tree().get_first_node_in_group(&"shop_panel") as ShopPanel
		if shop:
			shop.open_with(shop_stock, shop_title if shop_title != "" else display_name, shop_buys_cards)


## Half a day or a full day; pay, sleep, wake mended.
func _offer_room() -> void:
	var offers := Inn.offers()
	var options := PackedStringArray()
	for offer: Array in offers:
		options.append(offer[0])
	options.append("Never mind")
	var portrait := DialogueBox.portrait_from(sprite.sprite_frames)
	DialogueBox.ask(get_tree(), display_name, room_prompt, options,
		func(pick: int) -> void:
			if pick >= offers.size():
				_offer_topics()
				return
			var offer: Array = offers[pick]
			if not Inn.sleep(get_tree(), offer[1], offer[2]):
				DialogueBox.say(get_tree(), display_name, PackedStringArray([room_broke % offer[2] if "%d" in room_broke else room_broke]),
					_offer_topics, portrait)
				return
			_talking = false
			EventBus.notify.emit("You slept %s. Every heart mended." % ("half a day" if offer[1] < 24.0 else "a full day")),
		portrait)


func _update_animation() -> void:
	if sprite.sprite_frames == null:
		return
	if velocity.length() > 1.0:
		facing = velocity.normalized()
	var dir := DIRECTIONS_4[wrapi(roundi(facing.angle() / (PI / 2.0)), 0, 4)]
	var action := "walk" if velocity.length() > 1.0 else "idle"
	for candidate in [action, "idle"]:
		var anim := StringName("%s_%s" % [candidate, dir])
		if sprite.sprite_frames.has_animation(anim):
			if sprite.animation != anim:
				sprite.play(anim)
			return


func _draw() -> void:
	var player := get_tree().get_first_node_in_group(&"player") as Node2D
	var marker := Quests.marker_for(npc_id)
	if marker == "":
		marker = Errands.marker_for(npc_id)
	if marker != "":
		WorldPrompt.marker(self, Vector2(0, sprite_offset_y * 2 - 8), marker, Color(1, 0.85, 0.3))
	if player and not _talking and player.global_position.distance_to(global_position) <= TALK_RANGE:
		WorldPrompt.draw(self, Vector2(0, sprite_offset_y * 2), "E", "Talk")
