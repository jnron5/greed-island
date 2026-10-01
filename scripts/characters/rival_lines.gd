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
	},
}
const SHOW_SECONDS := 2.8


static func pick(rival: StringName, moment: StringName) -> String:
	var lines: Array = LINES.get(rival, {}).get(moment, [])
	return "" if lines.is_empty() else lines.pick_random()
