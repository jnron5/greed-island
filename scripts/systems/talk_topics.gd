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
			"Forty-seven of them. Harbor cards, forest cards, plains and lake and mountain and snow-village cards, rare ones only a monster gives up. First to carry the whole set into Vetrassa, on the far north-west coast, wins.",
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
		["And the west gate, past the windmill?", [
			"That's the road west: the Aurewind Plains, Verdana, the lake and the mountains beyond. Most of the island, really.",
			"The gate takes a Verdant Crest. Only one creature on this side of the island carries those: the Canopy Warden, east of the forest.",
			"So yes. To go west, you'll have to go and bother the Warden after all.",
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
			"Sit, sit. Cards are the whole of it. Forty-seven make the set, and the set is the race.",
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
			"Eat, drink, rest. Wounds don't close just because you've walked somewhere new. A night in Mate's beds at the Copper Kettle will mend you, or the Heartwood spring in Thornveil, for nothing.",
			"If you fall, you'll wake in the nearest town. Sorenda's closer than Kalmora, once you're up here.",
		]],
	],
	# ---------------- Inn keepers ----------------
	&"jobelle": [
		["How do rooms work?", [
			"Pay me, sleep, wake up whole. Half a day if you want to be up by morning, a whole day if you've really been through it.",
			"Walking about won't mend you, love. Neither will a door. Food helps, a bed fixes. Every town has an inn, ask for the keeper.",
			"Mind, the other racers don't sleep when you do. Not all night, anyway.",
		]],
	],
	&"mate": [
		["How do rooms work?", [
			"Coin on the bar, up the stair, sleep as long as you've paid for. Half a day or a whole one. You come down mended.",
			"The forest's hard on racers. Hounds, boars, the bear. Come back here before you're down to your last heart, not after.",
		]],
	],
	&"tally": [
		["How do rooms work?", [
			"Half a day or a full day, paid up front. I don't run tabs for racers. Only the Company gets a tab, and look how that's gone.",
			"You'll wake with every heart back. The road between here and anywhere won't do that for you.",
		]],
	],
	# ---------------- The plains ----------------
	&"loki": [
		["Who are you?", [
			"Loki. A traveller with a deck of cards and more time than is good for him.",
			"Family? A big one. A wife who works too hard, a son who cooks, a daughter who guards doors for a living, and one who ran off and never wrote.",
			"I come out to the road every race. I like to see the faces of the people who want something badly. You learn a lot about a thing from who comes looking for it."
		]],
		["What do you sell?", [
			"Little helpers. A whisper to lift a card from a pocket, a seal to keep yours in it. Same as Sable sells in Kalmora, only out here, where you need them.",
			"I'll buy cards too. I like to know what racers will part with, and for how much. It tells me more than the cards do.",
		]],
		["The road west is blocked.", [
			"Is it? Rocks fall. Very convenient rocks, all the same size, the week the Company stopped running carts west.",
			"Whatever was going east along that road is going some other way now. Ask yourself which way a thing goes when it doesn't want to be counted.",
			"My wife would tell you it's all for the best. My wife tells me a great many things are for the best. I used to believe her more than I do.",
		]],
	],
	# ---------------- The Starfall Range ----------------
	&"hald": [
		["What lives up by the pass?", [
			"The Rime Stag. Big as a barn door, antlers of ice. It keeps the high snow east of the pass and lets nobody up there in peace.",
			"It charges. Watch its front hoof: when it paws the snow it's picking its line. Step off the line and it'll go right past you and skid. That's your moment.",
			"Get it angry and it rears and stamps, and the ice flies off it in a ring. Keep your distance then.",
			"Kill it and it'll leave you an antler. It comes back, mind. It always has.",
		]],
	],
	# ---------------- Verdana ----------------
	&"aldous": [
		["What's on Kestrel Rise?", [
			"The Colossus. Folk call it a heap of old stones by the watchtower. It isn't. It stands up when you come close.",
			"The circles were raised to keep it sleeping, I think. Someone's been taking stones from them, and it doesn't sleep so well these days.",
			"Its hide turns a blade. Wait until it rises out of the earth with its rune glowing: that's when it's open. Mind the boulders, and when it sinks, keep moving.",
		]],
	],
	# ---------------- Frisalle ----------------
	&"ottilie": [
		["How do rooms work?", [
			"Coin on the bar, hot stone in the bed, sleep as long as you've paid for. Half a day or the whole of one. You come down mended, and fed if I catch you.",
			"The cold takes it out of you faster than wolves do. Come in before you're down to your last heart, not after.",
		]],
		["Why is there a toll?", [
			"Because the wolves took every goat on the upper meadow and nobody in Vetrassa cared. So: one wolf collar a head. You thin the pack, we let you in.",
			"There's another way in, they say, through the ice caves. Anyone who'd rather crawl past a wolves' den than pay me is welcome to.",
		]],
	],
	&"sven": [
		["How do I get through the mountain?", [
			"The pass, with a wolf collar for Ottilie's gate. That's the honest way.",
			"The other way: the ice caves in the east shoulder of the range, past the wolves' den, through the ice wall at the far end. Somebody cut a cart road through it. It comes out behind the counting house.",
			"Two wolves at least in that den. Go in mended, and don't stop to admire the crystals.",
		]],
		["What happened to the pass?", [
			"The slide came down one night last winter, right on the road, with my friend Anselm on it. Clean as a curtain.",
			"I went up after. Drill holes in the rock above, packed with something that smelled of the mines. Weather doesn't drill.",
		]],
	],
	&"liesl": [
		["What's worth seeing in Frisalle?", [
			"The bell tower, up on the top terrace. The guides' names are carved round the door. And the lantern in the belfry, if anyone ever lights it again.",
			"The skating pond, the weigh house, my workshop. The counting house, if you like being stared at by a portrait.",
			"And the cart ruts going up behind the counting house into the mountain. Everyone in Frisalle has seen them. Nobody in Frisalle talks about them.",
		]],
	],
	# ---------------- Seabright Quay ----------------
	&"fennick": [
		["How do rooms work?", [
			"A room at the Seabright Grand: half a day or the full day, settled in advance. Sea view, naturally. You will wake entirely restored.",
			"Racers who faint on the promenade are brought here. The Grand prides itself on its recoveries. Do try not to need one.",
		]],
	],
	&"pepper": [
		["What's good here?", [
			"The stew. It's always the stew. Saffron, mussels, prawns and the morning's catch, three hearts' worth of it. Chef's own recipe.",
			"The lemon tart if you want something lighter, and bread when the oven agrees. Everything here mends you; Chef doesn't believe in food that doesn't.",
			"People carry the stew all over the island, I'm told. I had a letter from an innkeeper up in the snow asking what saffron was.",
		]],
	],
	&"sparkle": [
		["What is there to do here?", [
			"Swim! Dive! Sail! Well, I sail, you watch. The beach is Sassy's, the boats are mine, the terrace is Pepper's and the top floor of the Grand is the Duke's.",
			"Fish off the end of the west jetty if you're the patient sort. I'm not. I just jump in after them.",
			"And look at the sea from the headland at night, through the telescope. Tell me if you see the light. Nobody else will admit they have.",
		]],
	],
	# ---------------- Lake Serin ----------------
	&"neri": [
		["Can I fish here?", [
			"Off the end of my dock, if you like. Cast, and watch the float. When it goes under, pull. Not before, not after.",
			"Trout, mostly. Cook one on a stick and it'll put you right better than any bread. Costs you nothing but the waiting.",
			"Now and then the lake gives up a coin instead. Barge folk dropped a lot of things, crossing at night.",
		]],
	],
}


static func for_npc(npc_id: StringName) -> Array:
	return TOPICS.get(npc_id, [])
