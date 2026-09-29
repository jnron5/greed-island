class_name RivalLines
extends RefCounted
## What the rivals say out loud: short lines in a speech bubble when they first run
## into you somewhere, rob you, get robbed by you, or open a chest. Each voice
## follows its backstory (CLAUDE.md, Rivals): the Raider grew up in the Duskara mine
## and fights for leverage, the Hoarder's family money comes from it, the Runner saw
## it and has been running since. None of them knows what the prize really is.

const LINES := {
	&"raider": {
		&"greet": ["You again.", "Keep your cards bound, cloak.", "Out of my way.", "Stay loose and I'll take it."],
		&"stole": ["Mine now.", "You'll live.", "Should've bound it."],
		&"robbed": ["...Bold.", "I'll have that back.", "You'll regret that."],
		&"chest": ["Every card counts.", "Not leaving this for them."],
	},
	&"hoarder": {
		&"greet": ["Oh. You.", "Do keep your distance.", "My family has raced for four generations.", "Mind my pack."],
		&"stole": ["Finders keepers, dear.", "It's only a card.", "You'll find another."],
		&"robbed": ["How dare you!", "That was mine!", "Thief! Thief!"],
		&"chest": ["Another for the collection.", "Mother will be pleased."],
	},
	&"runner": {
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
