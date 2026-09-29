class_name TalkTopics
extends RefCounted
## What residents can be asked about. After a resident's own line, a question list
## opens ("Ask about..."); each topic is a short explanation in their own voice. This
## is how the game teaches itself: the harbor folk explain the race, the card seller
## the cards, the grocer the satchel, the smith fighting, and so on. There is no
## tutorial beyond this.
##
## Nobody on the island knows what the race's prize really is. They only know it's
## riches beyond anyone's dreams. Keep it that way here.
##
## npc id -> Array of [question, PackedStringArray of lines].

const TOPICS := {
	# ---------------- Kalmora ----------------
	&"mirela": [
		["What is the race?", [
			"Every generation the King calls a race. Collectors from off-island come to Kalmora and try to gather one full set of cards.",
			"Thirty of them. Harbor cards, forest cards, rare ones only a monster gives up. First to carry the whole set into Vetrassa, on the far north-west coast, wins.",
			"Wins what? Riches beyond anything, is all anyone says. The winners never come back to tell it.",
		]],
		["Who am I racing?", [
			"Two others this year, same as you: cloaked, from off-island, in a hurry.",
			"The board by my office keeps the count, how many set cards each of you holds. Not which ones. Only the King's clerks know that.",
			"They follow the rules you do. They'll also rob you blind if you let them.",
		]],
	],
	&"rook": [
		["How do gates work?", [
			"See the seal on this arch? A card gate. Hold the right card, press up to it, and it takes the card and opens. For good.",
			"The card's spent, mind. Gone from your hand, gone from the island. That's the choice the race is built on.",
			"Every card that opens a gate is one you might need for the set. Spend what you can spare.",
		]],
		["What's north of here?", [
			"Thornveil Forest. Terraces, streams, hounds, boars. Sorenda's up the forest road, a village of good folk.",
			"There's chests hidden all over the forest, if you've the eyes for it. And the Warden, deeper in. Leave the Warden alone.",
		]],
	],
	&"sailor": [
		["How do I keep my cards safe?", [
			"A card you've just picked up is loose. Anyone who beats you in a fight, sneaks up on you, or casts the right spell can take a loose card.",
			"Bind it in your binder and it's safe. Open it with B. Binding's quick in a town like this, slow out in the wild.",
			"Cards you spend on a gate come out of the binder, exposed for a moment. That's when thieves strike.",
		]],
		["Can I steal cards too?", [
			"Course you can. Sneak up behind another racer and press E. If they notice you, they'll turn and fight.",
			"Or beat them outright; the winner takes a card. Or buy a Pickpocket's Whisper from Sable and it can't miss.",
			"They'll do the same to you. That's the race.",
		]],
	],
	&"tomas": [
		["How do I fight?", [
			"J swings your sword. K fires that pistol you keep under the cloak. Space dashes, and you can't be hit mid-dash.",
			"Watch a beast before it strikes. Hounds crouch before they lunge; boars paw the ground before they charge. Dash through it, then hit back.",
			"Fall in a fight and you'll wake in the nearest town, lighter a loose card. Monsters drop cards when they go down, straight into your hands.",
		]],
	],
	&"otto": [
		["Heard any rumours?", [
			"The Hoarder's family owns half the ships in this harbor. The Raider's from the dunes, they say. And the Runner never sits long enough to be asked.",
			"The prize? Riches beyond your wildest dreams. That's all anyone knows. Nobody who's won has ever said more.",
		]],
		["Where do cards come from?", [
			"Everywhere, if you look. Folk around town have some and they'll part with them for a favour, or a chat.",
			"Monsters drop them. Chests hide them, off the paths. Sable sells a few, and the Warden in the forest guards the rarest.",
		]],
	],
	&"sable": [
		["How do cards work?", [
			"Sit, sit. Cards are the whole of it. Thirty make the set, and the set is the race.",
			"Commons turn up everywhere: residents, chests, monsters. Rares are scarce. Boss cards only fall from the forest's Warden, and only so many times.",
			"Every card you carry is either loose, bound or exposed. Loose can be stolen. Bound, in your binder, is safe. Exposed is a card you're using, a gate or a spell, and thieves love those.",
		]],
		["What do you sell?", [
			"Spell and buff cards. They don't count toward the set; they're tools.",
			"A Pickpocket's Whisper steals one loose card from a racer near you, no roll, no risk. Q to cast it.",
			"A Lockbox Seal keeps one card safe for a while. Second Wind puts you back on your feet mid-fight.",
			"And charms. Wear a charm and it works for you all the time: a Hollowpoint makes your shots bite, a Tidewalker's Anklet puts spring in your dash. Two at a time, and mind: a charm you're wearing can be stolen.",
		]],
		["Should I sell my cards?", [
			"I'll buy set cards. But mind: a card I buy leaves the island. Forever. There'll be one fewer for anybody to find.",
			"Sell the spares. Never the last copy of anything.",
			"And if a gate ate a card you needed after all: I buy up what the gates take. I'll sell it back to you. Not cheaply.",
		]],
	],
	&"greta": [
		["How do items work?", [
			"Your satchel's for food and tonics. Items, not cards. Nobody steals a loaf of bread in this race.",
			"Press I to open your satchel and eat or drink what you like. Or H, in a pinch, and you'll take whatever fits your wounds best.",
			"Bread and smoked fish for scrapes. Healer's Tonic for worse. Sea-Salt Elixir when you're nearly done for.",
		]],
		["Where else can I find food?", [
			"Chests, sometimes. Folk leave all sorts in them. And there's a spring in Thornveil that heals you right up, if you find it.",
		]],
	],
	&"ilse": [
		["How do I find treasure?", [
			"Walk off the paths. Chests hide where the land hides them: behind cliffs, on islands, in dead-end clearings.",
			"Each chest opens once for you. The other racers get their own go, so there's no racing them to it.",
			"Your map's in the pause menu, Esc. It shows the roads between places and which are still shut by a gate.",
		]],
	],
	&"brannoc": [
		["Any fighting advice?", [
			"Swing, then step off. Everything out there wants you to stand still.",
			"Your pistol keeps you out of reach. Your sword's for when they close in. Your dash is the thing that keeps you alive.",
			"The straw dummies in the west meadow don't hit back. Practise there. They give up a card now and then, too.",
		]],
	],
	&"nonna": [
		["What do you know about the race?", [
			"My grandmother saw three races. Every time, the island went mad for cards, and every time somebody won and went off to Vetrassa.",
			"Riches beyond dreaming, they said. Nobody ever saw the riches. Grandmothers notice things like that.",
		]],
	],
	# ---------------- Sorenda ----------------
	&"moss": [
		["What is Sorenda?", [
			"The oldest village on Virelia. We were here before the kings, before the cards. The forest remembers that, even if Vetrassa doesn't.",
			"Rest here. Bind your cards; you're safe inside the village.",
		]],
	],
	&"harl": [
		["What should I watch for in the forest?", [
			"Briar hounds run in packs and lunge. Moss boars charge in a straight line and can't turn to save their lives.",
			"Keep an eye on your hearts, top left. Eat before you're empty, not after.",
		]],
	],
	&"pell": [
		["Where is the Hollow?", [
			"North-east of the green, through the old moss gate. It's a cave under the roots. Dark, deep, and something lives in it now.",
		]],
	],
	&"wren": [
		["Can you tell me about the cards?", [
			"The forest cards are Thornveil's own: thorn, moss, reed, acorn. The hounds and boars carry them, the way birds carry seeds.",
			"Some you'll find in chests, and some of us here have a card put by. Ask around. Folk give more than you'd think, to someone polite.",
		]],
	],
	&"juniper": [
		["How do I heal?", [
			"Eat, drink, rest. The Heartwood spring in Thornveil heals you right to full, for nothing.",
			"If you fall, you'll wake in the nearest town. Sorenda's closer than Kalmora, once you're up here.",
		]],
	],
}


static func for_npc(npc_id: StringName) -> Array:
	return TOPICS.get(npc_id, [])
