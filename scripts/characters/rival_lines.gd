class_name RivalLines
extends RefCounted
## What the rivals say out loud: short lines in a speech bubble when they first run
## into you somewhere, rob you, get robbed by you, open a chest, team up against a
## boss (and win, or get betrayed), or pick a fight. Each voice
## follows its backstory (CLAUDE.md, Rivals): the Raider grew up in the Duskara mine
## and fights for leverage, the Hoarder's family money comes from it, the Runner saw
## it and has been running since. None of them knows what the prize really is.

const LINES := {
	&"raider": {
		&"boss_join": ["Truce. Just till it's down.", "Fine. We kill it first.", "Hit it, not me. Then we'll see."],
		&"boss_cheer": ["Again! While it's open!", "Keep moving!", "Good hit.", "Don't stop now.", "Left side, it's slow there."],
		&"boss_won": ["Good fight. Don't spoil it.", "Taking what's mine and going.", "We're square. Today."],
		&"betrayed": ["I knew it. Truce is off.", "You'd stab me with the beast still breathing?", "Fine. You first, then."],
		&"fight": ["Hand it over.", "You're carrying too much.", "Nothing personal."],
		&"greet": ["You again.", "Keep your cards bound, cloak.", "Out of my way.", "Stay loose and I'll take it."],
		&"stole": ["Mine now.", "You'll live.", "Should've bound it."],
		&"robbed": ["...Bold.", "I'll have that back.", "You'll regret that."],
		&"chest": ["Every card counts.", "Not leaving this for them."],
		&"greet_duskara": ["I know these streets. I know what's under them.", "Smell that? Card dust. I grew up breathing it.", "Don't drink the Company's water."],
		&"greet_vetrassa": ["So this is where it all ends up.", "Pretty town. Built on the shaft, every stone.", "Don't get between me and those steps."],
		&"homeward": ["It's done. I'm going up those steps.", "All of it. Try and take it.", "Got the lot. Now they'll have to listen."],
	},
	&"hoarder": {
		&"boss_join": ["Very well, a temporary arrangement.", "Do try not to get in my way.", "Together, then. How common."],
		&"boss_cheer": ["Bravo!", "Keep at it, I'm right behind you.", "Mind the stomping!", "Splendid timing!"],
		&"boss_won": ["A civil victory. I'll take my share and go.", "Lovely working with you. Truly. Goodbye.", "Do give my regards to nobody."],
		&"betrayed": ["Of all the ungrateful...!", "So much for manners.", "I'll remember this!"],
		&"fight": ["Back off, ruffian!", "You'll not have my pack!"],
		&"greet": ["Oh. You.", "Do keep your distance.", "My family has raced for four generations.", "Mind my pack."],
		&"stole": ["Finders keepers, dear.", "It's only a card.", "You'll find another."],
		&"robbed": ["How dare you!", "That was mine!", "Thief! Thief!"],
		&"chest": ["Another for the collection.", "Mother will be pleased."],
		&"greet_duskara": ["Dreadful heat. Grandfather built a house here once, for the view.", "The Company keeps a lovely office. Shame about the town.", "Don't stare at the children, dear. It only encourages them."],
		&"greet_vetrassa": ["Home, more or less. Mother's townhouse is just off the square.", "We dine at Chef's. Everyone does, who matters.", "The Steward knows my family. He'll count my cards first."],
		&"homeward": ["The full set! Mother will be beside herself.", "Do stand aside, I have an appointment with a throne.", "Four generations, and I'm the one who finished it."],
	},
	&"runner": {
		&"boss_join": ["Okay. Okay. Together.", "Just this once.", "I'll keep it busy."],
		&"boss_cheer": ["Over here, beast!", "Now! Hit it now!", "I'll draw it off!", "You're doing it!"],
		&"boss_won": ["We did it. Thanks. I mean it.", "Taking mine and running. Good luck.", "Don't follow me. But thank you."],
		&"betrayed": ["Really? Now?", "I trusted you!", "...Should've known."],
		&"fight": ["Leave me alone!", "Not today!"],
		&"greet": ["Not now.", "Can't stop.", "Don't follow me.", "Still racing? Good."],
		&"stole": ["Sorry. I need it more.", "Sorry.", "Keep running."],
		&"robbed": ["Hey!", "Fine. Keep it.", "...I've lost worse."],
		&"chest": ["Found one.", "One more step away."],
		&"greet_duskara": ["I swore I'd never come back here.", "Don't look up at the terrace. Just walk.", "Keep your head down. They count heads here."],
		&"greet_vetrassa": ["Almost there. Almost out.", "The ships leave from here. Did you know?", "I can see the sea from the steps. I can see away."],
		&"homeward": ["I've got all of it. Don't stop me.", "Nearly out. Nearly.", "Last road. Please. Let me go."],
	},
}
const SHOW_SECONDS := 2.8


## The greeting for meeting the player in `zone`: carrying the whole set, it's the
## last road; in Duskara and Vetrassa, each has their own thing to say.
static func greeting(rival: StringName, zone: String, has_set: bool) -> StringName:
	if has_set:
		return &"homeward"
	if zone == WorldMap.DUSKARA:
		return &"greet_duskara"
	if zone == WorldMap.VETRASSA:
		return &"greet_vetrassa"
	return &"greet"


static func pick(rival: StringName, moment: StringName) -> String:
	var lines: Array = LINES.get(rival, {}).get(moment, [])
	return "" if lines.is_empty() else lines.pick_random()
