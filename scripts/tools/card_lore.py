"""Writes each set card's backstory (CardData.lore, the back of the card) into its
.tres. Keep each under ~190 characters so it fits the card back.
Run: python scripts/tools/card_lore.py"""
import glob
import re

LORE = {
    "harbor_lantern": "Every Kalmora pier hangs one, and every one is lit at dusk by hand. The night the southern barges run dark, the lanterns on the far quay stay out. Nobody is told why.",
    "salt_compass": "Old fishers swear the needle points to whatever you have lost at sea. Guard Rook's north arch opens for no other card, by an order older than anyone can remember.",
    "gull_feather": "Deckhands trade one before every long haul. The luck is said to last until the feather is lost, or until you give it to someone who needs it more.",
    "terracotta_tile": "Stamped with the old port crest, from before the King's anchor replaced it. Half the roofs in Kalmora still wear the old crest, and nobody has the heart to change them.",
    "fishers_knot": "Every fisher on the island ties it, and every family claims their grandmother invented it. It holds under any weight and slips free with one pull, if you know where.",
    "tide_bell": "Cast from the hull of the first ship to reach Kalmora. Fishers swear it rings an hour before high water, even on still nights. It also rang the night the unmarked barges came in.",
    "lighthouse_wick": "The keeper trims a new one every week and keeps the old ones in a jar. This one burned the night of the great storm, and has never quite gone cold since.",
    "coral_coin": "Money from before the cards, carved from the red reef off the south cape. The reef stopped growing the year the first race was called. The coins stopped being money soon after.",
    "net_mender": "A bone needle, worn smooth by four generations of fishers' hands. The last owner mended nets for the Duskara barges, and asked for no pay but the needle.",
    "sea_glass": "Frosted green glass that washes up only on Kalmora's beach, from bottles nobody remembers drinking. Children say it's what's left of a sunken lighthouse.",
    "thorn_sprig": "Snapped from a Thornveil bramble that grows back overnight. The hounds nest in them, which is why the hounds so often carry one.",
    "moss_lantern": "Sorenda's glowing moss packed into a hollow gourd. It needs no oil and no flame. It dims, the villagers say, when someone nearby is lying.",
    "veyra_reed": "Cut from the shallows of Lake Veyra, where the water is so still you can hear the reeds grow. Sorenda's pipers will play nothing else.",
    "bark_rune": "A symbol carved into bark, older than Sorenda. The same rune is carved on the stone circle, and, a traveller once swore, on a door deep under the dunes.",
    "hollow_acorn": "Something has been living in it. Something small, that left in a hurry and took its supper with it. Forest children keep them as tiny houses for wishes.",
    "fern_sigil": "Pressed ferns arranged into a deliberate shape by someone patient. Hunters leave them at their camps to say: I was here, I'm coming back, leave my things alone.",
    "mushroom_ring": "Step inside a ring and the forest goes quiet. Juniper the herbalist says the rings grow over places where someone once stood very still for a very long time.",
    "owl_quill": "Sorenda's scribes write only with these. They say an owl quill can't write a lie; the ink simply won't take. The foreman's ledgers are written in ordinary pen.",
    "thatch_charm": "Woven from a Sorenda roof to keep the rain out. Every house hangs one by its door, and one more for anyone in the family who is far away.",
    "canopy_seed": "Falls once a season from the highest trees, spinning so slowly it can take an hour to land. Catch one before it touches the ground and it's yours to keep.",
    "root_knot": "A tangle of roots grown almost into a hand, reaching up out of the soil. The Warden's roots grow like this. So, the elders say, did the first Sorenda children.",
    "briar_wren": "A small brown bird that nests only among thorns, where nothing can reach it. It sings loudest when the hounds are near, which is why hunters listen for it.",
    "sunken_crown_shard": "A sliver of gold from a crown no history mentions, hauled up in a fishing net off Kalmora. The harbormaster logged it, then tore the page out of her own log.",
    "lighthouse_lens": "Ground from a single piece of glass by the first keeper. Focused through it, light shows what's hidden: writing under paint, footprints on stone, a door in a wall.",
    "veyra_pearl": "Lake Veyra gives up one only when it chooses to. Divers who go looking for pearls come up with nothing; the pearls turn up in the nets of people who weren't.",
    "elderwood_heart": "Heartwood from a tree that fell before Sorenda was built, still warm to the touch. The Heartwood spring rises where its roots once drank.",
    "sorenda_star_map": "Charts stars that are not in tonight's sky. Elder Moss says they were there when the first race was run, and went out one by one with every race since.",
    "warden_mask": "Bark and leaves grown into the shape of a face. The Warden wears a new one every season. Nobody has ever seen what's underneath, and nobody who tried came back to say.",
    "canopy_eye": "It still blinks. Whatever the Warden saw through it, it goes on seeing, and on quiet nights it turns in your hand toward the east, toward the dunes.",
    "verdant_crest": "The mark of whatever the Warden guards: a leaf over a closed hand. The same mark is cut into Sorenda's oldest doorpost, below the notches Elder Moss carves.",
    # Past Kalmora's west gate: three cards for each region.
    "bristle_fleece": "Combed off the thorns where the wild rams scratch. The Hensleys spin it into rope for the fold gate, the only rope on the downs the rams can't chew through.",
    "shepherds_bell": "Every flock on the downs has a bell, and every bell is a different note. Tilly can tell you which farm a sheep came from with her eyes shut. Some notes stopped ringing years ago.",
    "crown_stone_rubbing": "Taken from the Stonewatch circle. Under the crown the figures shrink, row after row. Aldous counts one row for every king. The last row is still being carved.",
    "golden_sheaf": "Verdana ties the first sheaf in red and hangs it over the inn door for luck. These last years the Company has bought the sheaf too, along with everything else in the field.",
    "harvest_oak_leaf": "The Harvest Oak drops one leaf for every child born in Verdana, the old women say. Oda keeps every leaf that falls in a box. The box hasn't been full in a long time.",
    "millers_seal": "The mill's seal goes on every sack that leaves Verdana. Some sacks carry a second mark under it: a small sun, the same red sun stamped on the Duskara crates.",
    "heron_plume": "Serin's herons stand so still in the shallows that fish swim between their legs. Fishers wear a plume in their hat to borrow the patience. Neri has worn his to grey.",
    "serin_lily": "Serin lilies open at first light and close by noon. Folk on the shore say a lily that stays shut all day is keeping a secret for someone under the water.",
    "barge_bell": "Off a barge that sank crossing Serin by night, with no lights and no name painted on her. When the wind is right the bell still sounds, down under the water.",
    "iron_wolf_collar": "Found on the frost wolves of the Starfall Range. Nobody collars a wild wolf. The tags carry a number and a small red sun, and the wolves won't let anyone near the north road.",
    "starfall_edelweiss": "Grows where nothing else will, on the windward rocks above the tarn. Mountain folk give one to someone leaving for good. Hald has three pressed in his window, all from the same year.",
    "fallen_star_shard": "The range is named for nights when stars fall into the snow. Sorenda's star map marks the stars that have gone out. This shard is the shape of one of them.",
}


def main():
    for path in glob.glob("data/cards/set_*.tres"):
        s = open(path, encoding="utf-8").read()
        card = re.search(r'id = &"(\w+)"', s).group(1)
        if card not in LORE:
            continue
        text = LORE[card].replace('"', '\\"')
        assert len(LORE[card]) <= 200, (card, len(LORE[card]))
        if re.search(r"^lore = ", s, re.M):
            s = re.sub(r'^lore = ".*"$', f'lore = "{text}"', s, flags=re.M)
        else:
            s = re.sub(r'^(description = ".*")$', lambda m: m.group(1) + f'\nlore = "{text}"', s, count=1, flags=re.M)
        open(path, "w", encoding="utf-8", newline="\n").write(s)
    print("lore written for", len(LORE), "cards")


if __name__ == "__main__":
    main()
