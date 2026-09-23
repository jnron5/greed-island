# Card Race (working title) — Project Context

This is a single-player open-world card-collection game built in Godot 4, for release on Steam and mobile. This file is the full design context — read it before doing any implementation work.

**Engine/rendering:** Godot 4, Compatibility renderer (widest device support across Steam Deck/desktop and phones; 2D game doesn't benefit from Forward+'s 3D clustered lighting).
**View:** Top-down 2D.
**No player leveling system** — combat difficulty comes from encounter design, not player stat growth. Power curve (if any) comes from cards/equipment only.

---

## Concept and pillars

You and two AI rivals race to collect a full card set. Every card can be spent to progress (gates) or kept to win (final set). Pillars:
- **Exploration** — cards work as keys; the best cards sit in places worth finding.
- **PvP stealing** — you and both rivals can take cards from each other.
- **Cards do double duty** — the cards you need to win are the same ones you consume to open gates.

## Win condition and the race

First collector to hold the complete set at the final turn-in location (Vetrassa) wins — winner can be a rival. Three collectors total (player + 2 chosen rivals, see Rival Selection). A public tracker shows card **counts** per collector, not which cards. Rivals follow the same rules as the player, including consuming gate cards.

## Cards — three categories

### 1. Set/gate cards
Card fields: `id`, `rarity` (common/rare — sets gate cost), `copies_in_world` (or `max_possible_copies` for boss-sourced rares), `gate_card` (bool), `is_final_set_member` (bool), `replacement_sources`.

**No-soft-lock rule (CRITICAL — needs a Godot editor script):**
- Common cards: `copies_in_world` ≥ (final set need + total gate consumption). Commons are effectively infinite since they also drop from respawning monsters, so this is easy to satisfy.
- Boss-sourced rares (stricter, accounts for 3 competitors all needing the card): `max_possible_copies ≥ (final set need × 3 competitors) + total gate consumption across zones`. `max_possible_copies = starting drops + (respawns × kill cap)`.
- **Sold cards are permanently removed from `copies_in_world`** — selling is a real subtraction from world supply, not a neutral transfer back through the merchant. The validator must treat sales as consumption.

Card states: **Loose** (picked up) → **Bound** (slotted in binder, protected, cannot be stolen) → **Exposed** (in use, vulnerable to all 3 steal methods) → **Consumed** (gate spent, permanent). Binder slotting is instant in safe zones (towns), slower elsewhere. A lockbox card gives temporary protection to one card.

- **Rebuy merchant** — late-game, sells back spent cards at a steep price (safety net).
- **Permanent unlocks** — a gate opened stays open.
- **Scaling** — early gates cost common cards, big/late gates cost rare cards.
- **Alternate routes** — some gates also open via a hard fight or hidden path (pay in effort instead of a card).

### 2. Buff cards (separate pool, NOT monster/boss drops)
Don't count toward the final set, don't open gates. Obtained via **purchase (towns) or quest rewards only**.
- **Temporary** — consumed on use (same pattern as spell-steal cards). Duration/condition-based effect (bonus damage, brief invulnerability, instant heal). Emergency/clutch use.
- **Passive** — equipped in a separate loadout (not the collection binder). Ongoing effect while equipped (e.g., more powerful pistol shots). **Capped at 2-3 equipped slots.** **Stealable while equipped** — consistent with the theft system applying to every card type.

## Stealing — three methods, gated by card state

Only Loose and Exposed cards are vulnerable; Bound cards cannot be stolen.

| Method | Cost | Reward | Counter |
|---|---|---|---|
| Stealth | Free; failed attempt alerts target | One loose card, quietly | An alert/wary target |
| Combat | Time + risk; losing costs you a card | Winner takes one loose/exposed card | Safe zones, protection card |
| Spell card | Consumes the spell card | Guaranteed steal of one loose card | Lockbox/shield card |

Rivals use all three methods on the player and each other.

## Rivals

All **three archetypes are built**; at the start of a playthrough, the **player chooses 2 of 3** to race against (gives 3 possible pairings for replay variety).

| Archetype | Behavior | Backstory (see Story section) |
|---|---|---|
| Hoarder | Stays near safe zones, builds a big collection slowly; hard to reach early, rich target late | Profiteer — family wealth built on the Duskara mine trade; complicit, not a victim |
| Raider | Hunts whoever holds the most cards (including the player); mostly skips gates | Survivor — grew up laboring in the Duskara mine, escaped, fights for leverage to expose/destroy it |
| Runner | Rushes gates, explores fast, holds few cards at a time | Witness — saw the mine's truth firsthand, has been running ever since |

- **Grace period** — a robbed collector can't be targeted again for a short time.
- **Pressure on the leader** — both rivals prioritize whoever holds the most set cards (including the player).
- **No denial play** — rivals only boss-hunt when they genuinely need the card; a leading rival never snipes a boss purely to deny the player.
- **Difficulty tuning** — via rival speed/aggression, never by giving them extra cards.
- Rival state machine: find card → carry → return home, plus a **hunt boss** behavior when a rival needs a rare and a boss with remaining kills is the fastest path.

## Combat system

Real-time top-down action combat (not a turn-based duel). The player always has:
- **Sword** — melee swing.
- **Pistol** — ranged projectile. Buff cards can make shots more powerful.
- **Dash** — mobility/dodge.

One moveset serves monster fights, boss fights, and rival confrontations.

### Regular monsters
Roam zones (tougher variants in later/harder zones). Drop **common** cards on kill (same pool as loose pickups). **Respawn after a cooldown** — this is what lets common `copies_in_world` be treated as "loose pickups + respawning drops" rather than a fixed count.

### Boss monsters
One (or more) per zone, guarding tough gates/optional areas. Drop **rare** cards. **Killable a limited number of times per playthrough (3-4 total)**, then that source is gone for the rest of the game. **Respawn is gate-based** (not real-time, not zone-entry) — a boss becomes killable again once a specific gate is opened. This paces scarcity against actual player/rival progress rather than raw playtime.

## World map — Virelia Isle

Full open island, 6 towns, 4 named biomes, open-world (no forced difficulty-by-distance — difficulty is by region identity). First playable slice = Kalmora + Thornveil Forest/Sorenda.

**Towns:**
- **Kalmora**, Port of Beginnings — SE coast, starting town. Warm coastal Mediterranean architecture (terracotta roofs, whitewashed walls, lighthouse tower, docks).
- **Vetrassa** — NW coast, final turn-in town (opposes Kalmora across the isle; both ports, symmetric start/finish). Same port-town language as Kalmora but cooler (slate-blue roofs, stone).
- **Sorenda** — forest village in Thornveil Forest. Low, half-hidden among trees, wooden/thatched.
- **Frisalle** — snowy village in the Starfall Range. Alpine chalets, steep roofs, blue-toned shadows.
- **Duskara** — desert town in Siroth Dunes. Sandstone towers, domed rooftops, ochre/tan palette. **Site of the hidden card-harvesting mine (see Story).**
- **Verdana** — plains town in Aurewind Plains. Pastoral, gold-green.
- **Halmeer** — south coast near the southern cape. Cliffside, same port-town DNA as Kalmora/Vetrassa but smaller/remote.

**Biomes/landmarks:** Starfall Range (mountains, separates Frisalle from Siroth Dunes), Thornveil Forest (contains Lake Veyra + Sorenda), Siroth Dunes (contains Duskara), Aurewind Plains (contains Lake Serin + Verdana + ancient standing-stone ruins — exploration hook).

## Art direction

Pixel art via **PixelLab AI** (connected via MCP).

**Character look: Journey-inspired cloaked wanderers.** Player and all rivals are small hooded figures in long flowing cloaks — face hidden in hood shadow with two glowing eyes, trailing scarf, no visible arms, thin legs, a glyph band near the hem. Journey (thatgamecompany) is a *style* inspiration only: designs, colors and glyphs are original. Collectors are told apart by cloak color and silhouette.

- Character sprites: 16x16–32x32 px.
- Per-biome palettes: Thornveil Forest (greens/browns), Frisalle/Starfall Range (whites/blues), Siroth Dunes (tans/oranges), Aurewind Plains (golds/greens).
- **Player + all 3 rivals: 8-directional** (author N/NE/E/SE/S, mirror horizontally for NW/W/SW — verify sword-swing arc still reads correctly once mirrored).
- **Monsters + bosses: 4-directional.**
- Animation budget — Player: idle, run, sword-swing, pistol-fire, dash (all 8-directional). Rivals: idle, run, combat-equivalents. **No walk cycles** — characters only run. Monsters/bosses: idle, move, 1-2 attacks.
- Character silhouettes:
  - **Player** — sand-tan/rust cloak to the ground, gold glyph band, long scarf; sword and pistol kept under the cloak.
  - **Hoarder** — bulky layered plum/wine cloak, overstuffed pack visibly full of cards.
  - **Raider** — lean, torn charcoal/ash cloak, cloth mask under the hood, short blade held ready.
  - **Runner** — lightest build, short ivory/sky-blue cloak, very long scarf, no gear or weapon.
  - **Bosses** — per-zone biome identity: icy antlered stag (Starfall Range), burrowing sand-serpent (Siroth Dunes), canopy-camouflaged creature (Thornveil Forest), rooted/stone creature tied to the standing stones (Aurewind Plains).
- **First-batch asset list:** (1) Player 8-directional idle+run, (2) Thornveil Forest tileset, (3) one rival (whichever ships in the first slice).

## Story — moral compromise (tone: Hunter x Hunter's Chimera Ant arc)

**The island's prosperity isn't free.** Virelia's towns look idyllic, but the card economy is partly sustained by an underclass — indentured laborers, possibly children — working the hidden **Duskara mine**. Discoverable only through quests/environmental storytelling; invisible if the player doesn't look.

**No clean opt-out.** The player's own mechanics (stealing, consuming cards on gates, buying cheap rares) are the same economy the laborers feed into — no way to stop participating while still racing.

**The prize is real** — kingship of Virelia Isle, genuine and worth winning, kept **secret from the player until the very end** (One Piece-style reveal: the king is stepping down and hands power to whoever completes the set). The moral weight comes after winning: what do you do with what you learned. Branches at the ending:
- Continue as things have always been (default/clean-win path).
- Actively dismantle the system (harder, quest-gated).
- Something murkier in between (no fully satisfying "fix," intentionally).

**Rival backstories** — each a different relationship to the mine's truth (see Rivals table above for the one-line version; full version):
- **Raider (survivor)** — grew up laboring in the mine, escaped, fights for everything because they've had to. Racing = leverage to expose or destroy it.
- **Hoarder (profiteer)** — family wealth built on the mine trade, benefited from looking away. Hoards from fear of losing status. Morally grey, not a victim, not a cartoon villain.
- **Runner (witness)** — saw the truth firsthand without being laborer or profiteer, has been running ever since. Winning = means to finally leave Virelia, or (if pushed) finally act on what they saw.

Which 2 of 3 rivals the player picks determines the emotional shape of that playthrough (victim+profiteer, victim+witness, or profiteer+witness).

## Quests — first pass (8 quests, 1-2 per town, may be altered)

Rewards lean toward buff cards or currency.

- **Kalmora — "The Unmarked Cargo"** — dockworker flags unmarked card shipments. Early, simple observe/fetch.
- **Sorenda — "What the Trees Remember"** — abandoned laborer's satchel found in a grove. Runner's trail surfaces here if chosen.
- **Frisalle — "The Merchant's Ledger"** — financial discrepancies trace to Hoarder's family if chosen.
- **Duskara — "Beneath the Dunes"** (main lore quest, at the mine itself) — witness conditions or help a laborer escape. Biggest reward (passive buff card).
- **Duskara — "The Foreman's Names"** — recover a ledger of missing laborers; personal thread if Raider chosen.
- **Verdana — "Stones That Remember"** — tied to the standing-stone ruins; hints the exploitation is cyclical across past kings.
- **Halmeer — "The Smuggler's Route"** — reveals logistics of moving harvested cards off-site.
- **Vetrassa — "An Audience Before the Throne"** (late-game, optional) — confirms the king's complicity, gates the branching ending.

## Title

Still open. "Greed Island" was considered and set aside (trademark/passing-off risk — distinctive fictional name from an existing franchise, paired with directly-inspired mechanics). Candidates: Virelia: Crown of Cards, Kings of Virelia, The Virelia Race, Virelia Isle, Crown Tide, Sovereign Island, Avarice Island. Use "Card Race" as the working title in code/comments until finalized.

## IP note

Original names, characters, and setting throughout — Hunter x Hunter is a mechanics inspiration only, never a source of names/assets.

---

# Technical directives for implementation

## Folder structure

```
res://
├── autoload/
├── data/
│   └── cards/          # CardData .tres resources, one per card
├── scenes/
│   ├── world/           # One scene per town/zone
│   ├── characters/       # player, rivals, monsters, bosses
│   ├── ui/               # HUD, binder, dialogue, quest log
│   └── systems/           # combat, stealth, gates, rebuy merchant
├── scripts/
│   ├── autoload/
│   ├── characters/
│   ├── systems/
│   └── tools/             # no-soft-lock validator lives here (@tool script)
├── assets/
│   ├── sprites/
│   │   ├── player/
│   │   ├── rivals/
│   │   ├── monsters/
│   │   ├── bosses/
│   │   └── tiles/          # per-biome tilesets
│   ├── cards/               # card art/icons
│   └── audio/
└── addons/
```

## CardData resource (res://scripts/data/card_data.gd, extends Resource)

Fields: `id: String`, `display_name: String`, `rarity: enum {COMMON, RARE, BOSS}`, `category: enum {SET, GATE, BUFF_TEMP, BUFF_PASSIVE}`, `is_final_set_member: bool`, `copies_in_world: int` (or `max_possible_copies` for boss cards), `sell_value: int`, `icon: Texture2D`. Each card is a `.tres` in `res://data/cards/`.

## Autoloads

- **GameState** — player's held cards, binder contents, currency, rival card counts (public tracker), quest flags, which 2 rivals are active.
- **CardDatabase** — loads all CardData resources, lookup by ID.
- **EventBus** — signal hub for card state changes (steal/consume/sell) so UI, rival AI, and tracker stay in sync without tight coupling.

## No-soft-lock validator (res://scripts/tools/)

`@tool` script, run from the editor. Scans `res://data/cards/`, and for each card:
- If common/monster-sourced: check `copies_in_world` ≥ final set need + total gate consumption.
- If boss-sourced rare: check `max_possible_copies` ≥ (final set need × 3) + total gate consumption, since all 3 competitors compete for the same capped pool.
- Must treat sold cards as a subtraction from live supply, not neutral.
Needs a way to distinguish boss-sourced vs. monster/loose-sourced cards to apply the correct formula (e.g., a `source` field on CardData).

## Build order (first playable slice: Kalmora + Thornveil Forest/Sorenda)

1. **Spell-steal card** — tests loose/exposed card states and the binder/tracker loop end to end.
2. **Stealth** — awareness meter on rivals (unaware/suspicious/alert) + chance-based success roll.
3. **Combat** — real-time sword/pistol/dash system, shared by monster fights, boss fights, and rival confrontations.

Slice scope: ~30 set cards (~8 gate cards), a CardData resource, a binder UI with bound/exposed states, a rival state machine (find/carry/return + hunt boss), one hub town (Kalmora) + Thornveil Forest/Sorenda.
