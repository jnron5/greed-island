extends Control
## The end of the race, told in a few pages over PixelLab paintings: how it ended
## (quest_flags "ending" and "winner", set by Ending.finish), what became of the
## island and of the two rivals you raced, then back to the title. Accept, click or
## E turns the page.

const TITLE_SCENE := "res://scenes/ui/title_screen.tscn"
const ART := "res://assets/ui/ending/"
const RIVAL_NAMES := { &"hoarder": "the Hoarder", &"raider": "the Raider", &"runner": "the Runner" }

var _pages: Array[Dictionary] = []
var _page := -1
var _art: TextureRect
var _title: Label
var _text: Label
var _hint: Label
var _turning := false


func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	process_mode = Node.PROCESS_MODE_ALWAYS
	var back := ColorRect.new()
	back.color = Color(0.02, 0.02, 0.04)
	back.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(back)
	_art = TextureRect.new()
	_art.set_anchors_preset(Control.PRESET_FULL_RECT)
	_art.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_art.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	_art.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(_art)
	var fade := TextureRect.new()
	var grad := GradientTexture2D.new()
	grad.gradient = Gradient.new()
	grad.gradient.set_color(0, Color(0.02, 0.02, 0.04, 0.0))
	grad.gradient.set_color(1, Color(0.02, 0.02, 0.04, 0.92))
	grad.fill_from = Vector2(0, 0.3)
	grad.fill_to = Vector2(0, 0.8)
	fade.texture = grad
	fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	fade.stretch_mode = TextureRect.STRETCH_SCALE
	add_child(fade)

	_title = Label.new()
	_title.theme_type_variation = &"TitleLabel"
	_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_title.add_theme_constant_override(&"outline_size", 6)
	_title.add_theme_color_override(&"font_outline_color", Color(0.06, 0.04, 0.03))
	_title.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	_title.offset_top = -150
	_title.offset_bottom = -126
	add_child(_title)
	_text = Label.new()
	_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_text.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_text.add_theme_constant_override(&"outline_size", 4)
	_text.add_theme_color_override(&"font_outline_color", Color(0.02, 0.02, 0.04))
	_text.add_theme_color_override(&"font_color", Color(0.95, 0.92, 0.85))
	_text.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	_text.offset_left = 70
	_text.offset_right = -70
	_text.offset_top = -120
	_text.offset_bottom = -24
	add_child(_text)
	_hint = Label.new()
	_hint.text = "E"
	_hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_hint.add_theme_color_override(&"font_color", Color(0.85, 0.72, 0.4, 0.7))
	_hint.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	_hint.offset_left = -40
	_hint.offset_top = -22
	_hint.offset_right = -14
	_hint.offset_bottom = -8
	add_child(_hint)

	_pages = pages(GameState.quest_flags.get(&"ending", Ending.RULE),
		GameState.quest_flags.get(&"winner", GameState.PLAYER), GameState.active_rivals)
	Ambience.silence()
	_next()


func _unhandled_input(event: InputEvent) -> void:
	var turn: bool = event.is_action_pressed(&"ui_accept") or event.is_action_pressed(&"interact") \
		or (event is InputEventMouseButton and event.pressed)
	if turn:
		get_viewport().set_input_as_handled()
		_next()


func _next() -> void:
	if _turning:
		return
	_page += 1
	if _page >= _pages.size():
		Transition.go(TITLE_SCENE)
		return
	_turning = true
	var p: Dictionary = _pages[_page]
	var out := create_tween()
	out.tween_property(_text, "modulate:a", 0.0, 0.25)
	out.parallel().tween_property(_title, "modulate:a", 0.0, 0.25)
	if p.get("art", "") != "":
		var tex := load(ART + String(p.art) + ".png") as Texture2D
		if tex and tex != _art.texture:
			out.parallel().tween_property(_art, "modulate:a", 0.0, 0.25)
			out.tween_callback(func() -> void: _art.texture = tex)
	out.tween_callback(func() -> void:
		_title.text = p.title
		_text.text = p.text)
	out.tween_property(_art, "modulate:a", 1.0, 0.6)
	out.parallel().tween_property(_title, "modulate:a", 1.0, 0.6)
	out.parallel().tween_property(_text, "modulate:a", 1.0, 0.9)
	out.tween_callback(func() -> void: _turning = false)


## The pages for an ending: [{title, text, art}], art a file in assets/ui/ending/.
static func pages(ending: StringName, winner: StringName, rivals: Array[StringName]) -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	if ending == Ending.LOST:
		var who: String = RIVAL_NAMES.get(winner, "a rival")
		out.append({ "art": "vetrassa", "title": "The race is over",
			"text": "Word came down the mountain road and into every town by nightfall: %s had carried the whole set up the palace steps in Vetrassa. The Steward counted it twice." % who })
		match winner:
			&"raider":
				out.append({ "art": "dawn", "title": "A crown for the survivor",
					"text": "The old card player from the plains fire walked out of the back of the throne room and handed the crown to hands that had worked the North Shaft. The Raider's first order closed it. The island got poorer, and nobody ever went down the shaft again." })
			&"runner":
				out.append({ "art": "vetrassa", "title": "A crown for the witness",
					"text": "The Runner held the crown for a single day. Then they gave it back, walked down to the quay and took the first ship off the island, and the old King sat down on his throne again as if he'd never left. They say the Runner left a letter about Duskara on the throne. Nobody admits to reading it." })
			_:
				out.append({ "art": "shaft", "title": "A crown for the profiteer",
					"text": "The Hoarder's family threw the greatest feast Chef's restaurant had ever served. The seam under Duskara was worked another year, and the year after. You never found out what the race had been for; only that it hadn't been for you." })
		out.append({ "art": "vetrassa", "title": "And you",
			"text": "You still have your cards, and the island is still here, and the roads still run between the towns. There will be another race, one day. There always is." })
		out.append({ "art": "", "title": "Card Race", "text": "Thank you for playing." })
		return out

	out.append({ "art": "throne", "title": "The Crown of Virelia",
		"text": "The Steward counted all %d cards of the set, twice. Then the old card player from the travellers' fire walked in from the back of the throne room, and sat down on the throne as if it had always been his. It had. Loki, King of Virelia Isle, had watched your whole race from the roadside." % CardDatabase.final_set().size() })
	out.append({ "art": "throne", "title": "What was promised",
		"text": "The race was never for riches. It was for the island: the King steps down for whoever can gather the whole set, whoever can take everything the island gives and keep it. Now it is yours. So is everything that pays for it." })
	match ending:
		Ending.CLOSE:
			out.append({ "art": "dawn", "title": "The North Shaft closes",
				"text": "Your first order was read out on the Company terrace in Duskara: the North Shaft closed, the ledgers of names opened, every debt in the Company store forgiven. The foreman read it twice. Then she unlocked the gate herself." })
			out.append({ "art": "dawn", "title": "What it cost",
				"text": "The card trade collapsed within a season. Seabright's lamps went dark, the Duke left for the mainland with the Grand's top floor packed in crates, and every town complained that it was poorer. Nobody new went down the shaft. The ones who came up went home, or north, or to a well in Duskara where their names are written on the wall." })
			out.append({ "art": "vetrassa", "title": "The son who hid",
				"text": "That spring the escape line's way-station in the Frost Grotto was packed up and left empty, a moss lantern still burning on the crate. A week later a tall black shepherd walked up the palace steps in Vetrassa for the first time in twenty years. Freya let him past without a word." })
			out.append({ "art": "throne", "title": "The last race",
				"text": "There was no next race. The set was broken up and given away, a card to every town. The Throne Ledger ends with a page in your hand: 'Seam closed. Count kept.'" })
		Ending.WAGES:
			out.append({ "art": "shaft", "title": "Wages for the deep",
				"text": "You kept the mine. The island needs its cards, you told the court, and the laborers need their bread. But the Company would pay wages now, in coin, not scrip, and no child would go down the shaft. You signed it, and you meant it." })
			out.append({ "art": "new_shaft", "title": "And yet",
				"text": "The Company paid the wages, and raised the price of water. The children stopped going down the North Shaft; a new shaft opened far out in the dunes, where nobody had thought to write an order about it. Every season your inspectors' reports came back clean. You learned to read them quickly." })
			out.append({ "art": "shaft", "title": "The foreman",
				"text": "The foreman paid the wages to the copper, and counted every head in and every head out, as she always had. She sent the King one letter that year. It said only: 'You see? They are fed. They are counted. I did protect them.'" })
			out.append({ "art": "throne", "title": "The Throne Ledger",
				"text": "'Seam worked. Count better.' It was the truest thing any king had written there, and it was still not enough." })
		_:
			out.append({ "art": "shaft", "title": "As kings always have",
				"text": "You took the crown and the ledger with it. The seam under Duskara was worked another year, and the year after. The carts came over the mountain at night, the Duke kept his table at Chef's, and Virelia was prosperous and beautiful. The race was run again, in your name." })
			out.append({ "art": "throne", "title": "The Throne Ledger",
				"text": "On the last page of the Throne Ledger, under a long line of kings, you wrote what every one of them had written: 'Seam worked. Count true.' Then you signed it." })
	var fates := PackedStringArray()
	for r: StringName in rivals:
		fates.append(_fate(r, ending))
	if not fates.is_empty():
		out.append({ "art": "vetrassa", "title": "The other racers", "text": " ".join(fates) })
	out.append({ "art": "", "title": "Card Race", "text": "Thank you for playing." })
	return out


static func _fate(rival: StringName, ending: StringName) -> String:
	match rival:
		&"raider":
			match ending:
				Ending.CLOSE:
					return "The Raider came to the shaft the day it closed and stood a long while at the top of it, mask off."
				Ending.WAGES:
					return "The Raider didn't believe in your wages. They went out into the dunes looking for the new shaft, and found it."
			return "The Raider was last seen at the gate of the North Shaft with a crowbar, which was the last thing the Company wanted to see."
		&"hoarder":
			match ending:
				Ending.CLOSE:
					return "The Hoarder's family lost everything when the trade fell. To everyone's surprise, the Hoarder sold the rest of the collection and paid the Cistern's water for ten years."
				Ending.WAGES:
					return "The Hoarder's family bought shares in the new Company. They were very good shares."
			return "The Hoarder's family dined at Chef's every night of your reign, and toasted you, and grew richer."
		&"runner":
			match ending:
				Ending.CLOSE:
					return "The Runner stopped running. They walked into Duskara with a green lamp lit, and stayed to help."
				Ending.WAGES:
					return "The Runner stayed long enough to see whether the wages were real. Then they took a ship."
			return "The Runner took the first ship off Virelia and never came back."
	return ""
