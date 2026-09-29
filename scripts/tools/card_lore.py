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
