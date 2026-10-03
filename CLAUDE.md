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

Only Loose and Exposed cards are vulnerable to stealing; Bound cards cannot be stolen. **Going down is different (Jordan): a collector who is beaten or faints always drops one card** where they fell (a carried one if they have any, else one from the binder; a Lockbox-sealed card is safe), see Defeat below.

| Method | Cost | Reward | Counter |
|---|---|---|---|
| Stealth | Free; failed attempt alerts target | One loose card, quietly | An alert/wary target |
| Combat | Time + risk; losing costs you a card | The loser always drops a card on the ground; the winner (or anyone quicker) picks it up | Safe zones, protection card |
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
- **Zone travel (implemented):** rivals move between zones along `WorldMap.EDGES`, paying gate cards like the player (the Raider won't pay). In the player's zone they're `Rival` nodes that walk to the exit; elsewhere `RivalDirector` simulates them coarsely (collecting the zone's real remaining pickups, farming monster drops in the field, binding in towns). Styles: Runner = explorer (goes where cards are left), Raider = hunter (follows a player carrying cards, farms the field), Hoarder = homebody (stays in towns).

## Combat system

Real-time top-down action combat (not a turn-based duel). The player always has:
- **Sword** — melee swing.
- **Pistol** — ranged projectile. Buff cards can make shots more powerful.
- **Dash** — mobility/dodge.

One moveset serves monster fights, boss fights, and rival confrontations.

**Defeat → the nearest town's inn.** When the player or a rival drops to 0 HP (to anyone), they drop one card where they fell (`Combat.resolve_defeat` → `GameState.lose_card`: carried first, else bound; it lies on the ground as a `CardPickup` with `dropped_by`, kept in `GameState.zone_drops`, and anyone may take it; the player is told who picked up their card). Nothing ever goes straight into the winner's hands. Deaths take their time: the player gets a slow-motion moment, crumples while the camera leans in, the screen fades to white (`Transition.faint_to`), and they come round at the inn of the nearest town (`WorldMap.TOWN_INNS`/`inn_of`; register every new town and its inn in `scripts/world/world_map.gd`): lying down, then getting up (`Player._wake_up`), the keeper says one of their `wake_lines` (`Npc.welcome_back`), and the lost card pops up (`CardReveal.show_lost`). Rivals flash, fall and lie there `down_time` (3.2 s) before waking in the nearest town, which becomes their home for binding. **Every kill drops its loot on the ground** where it died, flung out of the body (`Combat.drop_loot`): monsters a card, often a few coins, now and then bread (`LootPickup`, player only); monsters die slowly too (flash, knocked over, fade).

### Regular monsters
Roam zones (tougher variants in later/harder zones). Drop **common** cards on kill (same pool as loose pickups). **Respawn after a cooldown** — this is what lets common `copies_in_world` be treated as "loose pickups + respawning drops" rather than a fixed count.

### Boss monsters
One (or more) per zone, guarding tough gates/optional areas. Drop **rare** cards. *(Implemented: the Canopy Warden in Warden's Grove, east of Thornveil — `BossData` in `data/bosses/`, `scripts/characters/boss.gd`. Canopy → telegraphed drop → grounded swipes/lashes → climbs back; each kill drops one of each of its 3 cards; respawn gates are those whose GateData.respawns_boss names it — keep respawn gates ≥ kill cap − 1, the validator warns otherwise. Hunter rivals go for a boss before following the player, but only while they lack one of its final-set cards.)* **Killable a limited number of times per playthrough (3-4 total)**, then that source is gone for the rest of the game. **Respawn is gate-based** (not real-time, not zone-entry) — a boss becomes killable again once a specific gate is opened. This paces scarcity against actual player/rival progress rather than raw playtime.

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

**Town look is defined by Jordan's concept renders in `docs/reference/kalmora_concept_a.webp` / `_b.webp` — check them before any town art or layout work.** Lush, saturated, dense: towns hug the water (plank docks, moored ship, beach cove, surf on rocky cliffs, lighthouse headland), buildings shoulder to shoulder around a fountain square, mixed red terracotta and slate-blue roofs, palms/bushes/flower beds in every gap, blue-and-gold banners, warm light paving. **Environment style: modern multilevel towns — Sea of Stars (Sabotage Studio) is the reference.** Towns are built on terraces and cliffs at several *real* walkable heights joined by stairs/ramps (not one flat plane with scattered props), with dense hand-crafted detail, buildings built into the terrain, and lighting/atmosphere (lamp and window glow, water shimmer, time-of-day tint). Reference is for style only — no names/assets from it.

**Residents are anthropomorphic bipedal dogs and cats only** (no humans, no other species; variety from breeds, outfits, builds). The player and rivals are the exception: cloaked outsider wanderers (see below), restyled with more detail to fit.

**Character look: Journey-inspired cloaked wanderers.** Player and all rivals are small hooded figures in long flowing cloaks — face hidden in hood shadow with two glowing eyes, trailing scarf, no visible arms, thin legs, a glyph band near the hem. Journey (thatgamecompany) is a *style* inspiration only: designs, colors and glyphs are original. Collectors are told apart by cloak color and silhouette.

- Character sprites: 16x16–32x32 px.
- Per-biome palettes: Thornveil Forest (greens/browns), Frisalle/Starfall Range (whites/blues), Siroth Dunes (tans/oranges), Aurewind Plains (golds/greens).
- **Player + all 3 rivals: 8-directional** (author N/NE/E/SE/S, mirror horizontally for NW/W/SW). **The player's sword and pistol are drawn in code** (`Player._draw_gear`): PixelLab animates only the body (a weaponless lunge for `sword_*`, a recoil for `pistol_*`), and one sword sprite and one pistol sprite (`assets/sprites/player/fx/`) are swung and aimed to the exact facing, with a slash crescent and muzzle flash, so they're identical in all 8 directions. Generated weapon frames never stayed consistent; don't go back to them.
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

## Testing (headless)

Every check runs as a scene (not a `-s` script) so the autoloads exist:

```
godot --headless --path . res://scripts/tools/run_soft_lock_check.tscn   # no-soft-lock validator (also checks placed copies, boss respawn gates)
godot --headless --path . res://tests/test_<name>.tscn                    # inn (hearts carry over, rooms), card_loop, stealth, combat, respawn_flow, rival_travel, boss, gates, elevation, town, interiors (Kalmora, Sorenda, Verdana, Lake Serin, Starfall, Seabright Quay, Frisalle), forest_reach (incl. the Hollow, the four regions past the west gate, Seabright Quay and Frisalle), stag, colossus, thornveil, quests (incl. errands, the Frisalle toll and ice road, The Merchant's Ledger), card_reveal, save, loadout (charms, rebuy), return (town return cards), tour (every zone, day and night; run it windowed too)
```

Zone layout lives in the scene files, plus `scripts/world/world_map.gd` (origins, towns, edges). Lake Veyra is generated by `python scripts/tools/build_lake_veyra.py` (edit the layout there, not in the editor; water collision follows the smooth lake at 8px, barrier lines are drawn as bramble hedges), then dressed by `build_forest.py lake_veyra` (smooth shore, reed beds, the forest lake's animated water clipped to the lake). **Thornveil Forest** is built entirely by `python scripts/tools/build_thornveil.py`, traced from Jordan's concept `docs/reference/thornveil_concept.webp` (layout in `scripts/tools/thornveil_layout.py`, concept px mapped to the world at 1.5x): six heights (lake, south lowland, plaza, east rise, north terrace, north gate strip) from terrace polygons, composed with the PixelLab forest-terrace cliff set (`assets/sprites/tiles/thornveil/cliff/`) and Kalmora's rock-over-water set for the lake; cliff faces hang below each terrace edge (`grow_down`), as the concept draws them. Streams are painted water ribbons across the terraces (read from the concept's blue), not channels; dirt paths come straight from the concept's path colour; trees are dense where the concept is canopy and along the map edges, kept out of named clearings. Things to do there: chests (`scripts/systems/chest.gd`, gold and food and a few cards, opened once by each collector), Tobin's camp (trader), the Heartwood spring (`healing_spring.gd`, heals), the stone circle and rune stones, readables; `tests/test_thornveil` covers them and the exits. Edit the layout in those two scripts, not the editor. Warden's Grove ground is painted from the PixelLab forest-path Wang tileset by `python scripts/tools/build_ground.py` (its `ZONES` also hold Sorenda's bounds and paths, which build_forest.py reads; Sorenda's scene itself comes from build_sorenda.py) — paths/plazas are shapes in that script, it colour-grades to the Thornveil palette and scatters `ForestTree*` nodes; re-run after changing a layout. Sorenda, Warden's Grove and Lake Veyra are then dressed as real forest by `python scripts/tools/build_forest.py` (after build_ground; `FORESTS`, residents and readables per zone in `LIFE`): Kalmora's meadow grass shaded and dappled, meandering dirt paths blended per pixel, a double treeline along every edge (so the zone's walls are visible trees), clustered groves of PixelLab-animated firs and oaks (`scenes/world/props/forest_*.tscn`), undergrowth in patches, rocks/logs/stumps with visible colliders, baked shadows; everything that matters (cards, monsters, markers, exits) keeps a clear margin, and `tests/test_forest_reach` walks the zone to prove it. Kalmora is a **multilevel** harbor town generated entirely by `python scripts/tools/build_kalmora.py` (art in `assets/sprites/tiles/kalmora2/`). Its layout is **traced from the people-free concept map `docs/reference/kalmora_concept_c.webp`**: every position in the script is in that image's pixel coordinates, mapped to the world at 1.4x by `W()` (so read positions straight off the concept). Decorations that land on a wall/stairs/another object are nudged to the nearest open spot or skipped with a warning; soft contact shadows under every building, tree and prop are baked into the ground image. Terrain: a corner heightmap (sea / harbor / town / upper) is composed from chained PixelLab **pro cliff tilesets** by `scripts/tools/terrain.py` — a cliff set per pair of levels that meet (any height difference; per-region sets such as stone harbor walls vs. rocky coast), terrace walls grown upward and sea cliffs grown downward over the water, stairs that find their own wall edge. Grass over paving and dirt paths over grass are blended per pixel by `soft_surface()` in the builder (rounded corners, slightly ragged edge, soft rim) — don't go back to Wang corner tiles for those, they step along tile corners. Lawns use the Wang grass set named by `GRASS` (`wang/<name>`, chained to the paving's base tile); cliff-top grass joined to a lawn is repainted to match (`regrass()`). The beach is painted per pixel (`paint_sand()`: rippled sand, wet bands at the waterline, broken foam). The builder also writes a surface map (green = sand) that `Zone.surface_map` reads: sand takes footprints that fade after a few seconds (`scripts/world/footprints.gd`). **Motion is real animation, never shader warping:** palms and trees are PixelLab-animated frame strips (`animate_image`) in `kalmora2/anim/`, played as AnimatedSprite2D (`ANIMATED` in the builder), with swaying grass tufts around tree bases (`TUFT_RING`); neighbours start on different frames. Ambient life: gull flocks (`GULLS`, `scripts/world/gull_flock.gd`, a side-on PixelLab flap strip flipped to face its heading, shadow on the water); groves of round trees and cypresses (`cypress_g`, recoloured to the palm palette) instead of rows; a two-sided market street on the lane from the fountain to the lighthouse; `TOWN_READABLES` (notice board, fountain plaque, keeper's log, barred archway) carry the story in the open town. Kalmora's water is a PixelLab-animated wave tile (`anim/bay_water.png`, made seamless by patching each frame's border from its own middle) repeated by `TiledAnimation` and clipped to every water pixel of the ground (`kalmora_bay_mask.png`, `bay_water()`), so all of Kalmora's water — bay, beach channels, canal — rolls the same way. Palm trunks stay still — only the fronds move: PixelLab bends the whole tree, so its frames go through `python scripts/tools/lock_palm_trunk.py <strip> <frames...>`. The broadleaf tree `tree3_g` is recoloured to the palm's palette and outline so it matches. Fields, sand and plank docks are painted with `terrain.overlay()` from 16-tile Wang sets chained to the cliff sets' base tiles; the level map's green channel marks dry sea-level ground (docks, beach) so the water shimmer skips it; the builder grades the ground toward the concept palette. Sprites must not carry their own ground (no grass disc under trees, no plinth of land under buildings) — ask PixelLab for 'no ground, no base' and regenerate if one comes back with it. Buildings and big props are PixelLab `create_map_object`s (front-facing, 'gable end and facade facing the viewer straight on, symmetrical, not isometric' — otherwise they come out angled); their flat backgrounds are removed with `python scripts/tools/keyout.py <png>...`. `create_map_object` in basic mode kept drawing Sorenda's houses angled or cropped; `create_image_pro` with a front-facing building as `style_image_url` and 'the whole building including the roof eaves fits inside the image with an empty margin' worked. **Town dressing is placed on purpose, never random:** buildings front streets, props sit in clusters that explain themselves (cargo by the jetty, stalls around the plaza, planters at doors), listed in BUILDINGS/TREES/PROPS/LAMPS; the build fails if a prop lands on a cliff, stairs, card, spawn or resident. Edit the layout in that script, not the editor. **Collision matches the art, both ways:** water blocks pixel-accurately (`terrain.mask_rects()` over the ground's water pixels, decks and bridges cleared; `tests/test_thornveil` samples water in Thornveil and Kalmora and fails on any walkable spot), buildings block their whole footprint (`building_depth()`, ~45% of the sprite's height, not just the front wall's foot), props get a depth from their sprite; check with a `--debug-collisions` render. **Elevation rules:** `Zone.level_at()` reads the level map; hits, sight, stealth steals and Pickpocket only work between characters on the same level. `Zone.find_path()` (AStarGrid2D over the zone's World collision) gives rivals real routes up stairs and around obstacles. New static props: `python scripts/tools/make_prop.py <name> <texture> <footprint w> <h>`. Animated props (e.g. the fountain) from a horizontal frame strip: `python scripts/tools/make_animated_prop.py <name> <strip> <frames> <fps> <footprint w> <h>`. Zones clamp the player camera to their ground sprite (`GroundTiles`/`Ground`). Gated pickups set `behind_gate` so rivals only take cards they can reach or pay for.

**UI look:** every screen uses the project theme `assets/ui/theme.tres` (set as the default in project.godot), built by `python scripts/tools/build_ui_kit.py` (cuts the PixelLab UI sources in `assets/ui/src/` into pieces) then `godot --headless --path . -s scripts/tools/make_theme.gd`. Teal enamel windows with gold trim and shell corners, kit buttons, the PixelLab pixel fonts (`assets/fonts/`, text at size 8 = crisp at 2x), type variations `TitleLabel` (gold title font), `InkLabel` (dark text on parchment), `DialoguePanel`, `NamePlate`, `InsetPanel`. Don't add plain ColorRect/blue-box UI: build from the kit. The dialogue box is a parchment panel with a name plate and the speaker's portrait (`DialogueBox.portrait_from(sprite_frames)`); the binder is an open ring binder with six sleeves a page in set order (`scripts/ui/binder.gd`); cards are `CardView` (front/back, keeps the smooth font for its small ink text).

**Town life systems:** residents are `Npc` nodes (scenes/characters/npc.tscn; sprites in assets/sprites/npcs/<id>/) with ambient lines, optional wandering and optional `shop_stock`; conversations go through `DialogueBox.say()`. Quests live in the `Quests` autoload (state in GameState.quest_flags; one flow function per quest — "The Unmarked Cargo" is the first) and clue objects call `Quests.inspect()`. Interiors are Zones with `interior = true` built by `python scripts/tools/build_interiors.py` from one PixelLab room image each plus collision rects; every Kalmora building has a door, a ZoneExit placed by build_kalmora.py (DOORS) that needs the interact key (`needs_interact`, "[E] Enter" prompt); rooms are drawn at 1x (`ROOM_SCALE`), so furniture colliders cover only the footprint and leave aisles a cloak fits through (no freestanding door frames in the art), and each way out shows a gold arrow (`exit_hint`); each room has walls/furniture blocks traced from its art and `Readable` story objects (letters, ledgers, portraits: `scripts/systems/readable.gd`), and `tests/test_interiors` checks every door round-trips and every resident and readable is reachable walking with the player's real feet shape and interiors are registered in WorldMap.ZONES without EDGES (rivals never enter). `TimeOfDay` autoload tints outdoor zones (CanvasModulate) and drives `LampLight` glow; zones with a level map get a water-shimmer shader.

**Most cards come from people.** Residents hand cards over through **Errands** (`scripts/autoload/errands.gd`: one favour per resident — a chat, an item from your satchel, gold, monster kills counted from `EventBus.monster_defeated`, visiting a place, or holding N cards; "!" to ask, "?" to hand in). Quests reward cards too (Elder Moss gives the Sorenda Star Map). A minority of cards sit in chests (`scripts/systems/chest.gd`: a card and/or gold or satchel items, may sit behind a gate); **every collector opens each chest once** (keys per collector via `WorldMap.taken_key`; the sprite shows the player's), and opening one only says what you found — no text box. Most chests hold gold and food. Monster, boss and dummy kills leave their card on the ground to be picked up (`Combat.drop_loot`); shops sell some. Rivals get errand cards and chest cards off screen: `WorldMap` lists both as the zone's pickups (errands as `errand:<id>`). Loose `CardPickup`s are only ever drops (kills and collectors going down). Builders place chests (`chest_node` in build_kalmora.py (CARD_CHESTS/LOOT) / build_thornveil.py / build_hollow.py / build_sorenda.py). Every card has PixelLab art (`assets/cards/art/`, 66x47) and a backstory (`scripts/tools/card_lore.py` writes `lore`).

**No tutorial: the townspeople teach.** After a resident's own line, a question list opens (`DialogueBox.ask`, topics in `scripts/systems/talk_topics.gd`): Mirela explains the race, Rook gates, Luca binding and stealing, Tomas fighting, Sable the card system and her wares, Greta items, Ilse treasure hunting, and Sorenda's folk the forest. In the world nobody knows what the prize really is: only "riches beyond your wildest dreams". Shops show a line describing each thing for sale.

**Saving:** `SaveGame` autoload keeps one save in `user://savegame.dat`, written each time the player arrives somewhere (`EventBus.area_entered`), never from headless runs; the title offers Continue. Add any new run state to its save/continue.

**Return cards:** one per town (Kalmora, Sorenda, Verdana, Seabright, Frisalle Return; `CardSpells.RETURN_CARDS`), one-use BUFF_TEMP cards at 150 gold, sold only at that town's card shop: every `Merchant` stall adds its own town's card to its stock automatically (`CardSpells.return_card_for`), Sable sells Kalmora's, and Fennick sells Seabright's (no card shop there; `extra_stock` on a keeper in build_interiors.py). Used from the binder ("Use"): the card is spent and you fade through light to the town's `town` spawn; refused, and kept, when you're already in that town. The first one is free: one resident per town gives it the first time you talk to them (`Quests.WELCOME_GIFTS`: Jobelle, Mate, Tally, Fennick, Sven; residents with no favour of their own, since quest dialogue comes first), player only. A new town gets a return card and a giver too; `tests/test_return`.

**Charms and the rebuy shelf:** passive buff cards are worn from the binder's detail panel (`GameState.equip`, `EQUIP_SLOTS` = 2); a worn charm is held Exposed, so it can be stolen. Hollowpoint (pistol +1), Tidewalker's Anklet (dash recovers twice as fast) and Mossheart (heals out of danger) are applied in player.gd. Cards the player spends on gates are remembered (`GameState.spent_on_gates`) and the card merchant sells them back at `REBUY_MARKUP` x their worth.

**Audio:** effects and ambient beds are synthesised (no samples yet) by `python scripts/tools/make_sfx.py` (assets/audio/sfx/) and `make_ambience.py` (assets/audio/ambience/, seamless 24 s loops). `Sfx.play(&"name")` plays an effect (pooled, slight pitch variation; event sounds such as cards, gold, gates and steals are hooked to EventBus inside Sfx); `Ambience` picks a bed per place on arrival (harbor, forest day/night, cave, room). Volumes live in `Settings` (user://settings.cfg, pause-menu sliders). Nothing plays in headless runs.

**Rivals talk:** short lines in a speech bubble (`scripts/characters/rival_lines.gd`, `WorldPrompt.bubble`) when they first meet you in a zone, rob you, get robbed, or open a chest; each voice follows its backstory, and none of them knows the prize.

**Satchel items** (not cards): `ItemData` in `data/items/*.tres` (heal amount, price, PixelLab icon), catalogue `Items` (`scripts/systems/items.gd`), counts in `GameState.items`, bought at Greta's Provisions (an Npc with `shop_stock` of item ids, `shop_buys_cards = false`), used from the character menu's Items page or with H (quick heal picks the smallest item that covers your wounds). The character menu (`binder.gd`) has two pages: Binder (B) and Items (I); Tab flips.

**Text:** body text is a smooth sans (Godot's built-in Open Sans, SIL OFL; `TEXT_SIZE` 11 in make_theme.gd) — the pixel fonts distorted at any size but their native one and read poorly; titles keep the gold pixel font at its native 16; world prompts use the body font at 9. Entering an area emits `EventBus.area_entered` and the HUD shows its name large (32, rooms 20) with the part after a comma as a subtitle. **HUD:** everything sits in the top-left corner (hearts, purse with the time of day beside it (`TimeOfDay.part_of_day()`), a one-row race count, then the quest/favour lines) and fades while the player walks behind it; the controls hint shows for the first 90 seconds only.

**Day and night:** a day is 30 minutes (`TimeOfDay.DAY_SECONDS`). Outdoors, night is a colour grade (`NightGrade`, `assets/shaders/night_grade.gdshader`: colour drains to moonlit blue except where lamps reach), not just a darker tint. Kalmora's windows glow from inside after dusk (`WindowGlow` overlays made by build_kalmora.py from hand-marked window rects, `WINDOWS`), lanterns hang over the market (`StringLights`), the lighthouse sweeps the bay (`LighthouseBeam`), the windmill turns (sails drawn per frame by `scripts/tools/make_windmill_sails.py`, cut out of the building sprite), and the player carries a faint glow. Caves are `underground` zones: their own dark CanvasModulate, lit by glowing props.

**Player sprite:** 85% scale. Its frames use the PixelLab direction labels as they are (authored S/SE/E/NE/N, the west side mirrored from the east); don't remap them. Card gates are drawn from `assets/sprites/gates/` (`look`: "gate" art, "bars" for Kalmora's arch, "seal" for a drawn door). Thornveil's water is three frame animations made by `scripts/tools/make_forest_water.py` from PixelLab tiles (`assets/sprites/tiles/thornveil/water/`): a calm teal lake (Lake Veyra uses it too), streams that flow downstream, and falling water poured down each waterfall's shape (`find_falls`/`make_fall_strip` in build_thornveil.py), never a pasted sprite. Gates across east-west passages (`vertical`) are drawn side-on.

**Sorenda** is built by `python scripts/tools/build_sorenda.py` (the village: six PixelLab homes round the green and the Copper Kettle inn by the south road, each enterable — interiors in build_interiors.py with `town` = Sorenda — the moss gate and the Hollow's cave mouth), then `python scripts/tools/build_forest.py sorenda` dresses it (ground, trees, residents and readables from LIFE). **The Hollow** (`scenes/world/sorenda_hollow.tscn`, `python scripts/tools/build_hollow.py`) is a cave behind the moss gate, composed from a PixelLab cave cliff set: glowing mushrooms, the hollow bear (`scenes/characters/hollow_bear.tscn`, a tough monster) in its den, and the satchel at the far end for "What the Trees Remember". It's on the world map with EDGES (rivals may enter).

**Past Kalmora's west gate** (`kalmora_west_gate`, costs the Canopy Warden's Verdant Crest, a side-on gate at the end of the west road through the windmill farm): the **Aurewind Plains** (hub: gold-green downs, the King's Road, the Stonewatch Downs plateau with the stone circle, Kestrel Rise, the Hensley farm and barn, a travellers' camp, Sunmere pond, the dune road west closed by a rockfall — Siroth Dunes/Duskara later), **Verdana** (town, south: cobbled square round the Harvest Oak, the Sheaf & Sickle inn, Marta's farmhouse, Aldous's house on the upper green, a working barn and windmill, wheat fields), **Lake Serin** (north of the plains: the lake with Stone Point, Heron Bluffs, Neri's hut and dock) and the **Starfall Range** (north of the lake: snow, three terraces joined by stairs, a frozen tarn, Hald's cabin, the pass to Frisalle closed by an avalanche, dug through to Frisalle's toll gate). All four are built by `python scripts/tools/build_region.py [zone]` from the layouts in `scripts/tools/region_layouts.py` (edit there, not in the editor): a corner heightmap composed with a PixelLab cliff set (forest_terrace, or `assets/sprites/tiles/starfall/cliff/snow`), stairs cut into south-facing walls, grass mapped onto a biome palette by brightness (`palette`), dirt roads by distance to their centre line with wheel ruts, wheat fields in rows, cobbled `plazas`, lakes (water per pixel, the forest lake animation clipped to it with a depth layer over it: pale shallows at the shore, darker toward the middle; collision following the water), docks, ice, snow painted as drifts with wind ripples and glints (paths are packed snow with old footprints and a bright bank, not an outline; PixelLab's snow Wang sets came back as flat dots and checker grids, so don't use them), terrace spurs and bays in `starfall_level`, treelines along every edge, groves, undergrowth, animated grass tufts, buildings with doors/window glow, props, lanterns (nudged off paths), campfires, residents, readables, chests, monsters, `snowfall` (`scripts/world/snowfall.gd`). The build fails if anything that matters can't be walked to. Every Verdana building has an interior (inn, farmhouse, scholar's house, weaver's cottage, bakery, barn, mill: build_interiors.py); only the plains' Hensley barn (`WorkingBarn`) stays shut. Ambient animals: Tilly's sheep in a dry-stone fold on the plains and mountain goats in the Starfall Range are `Npc`s (several per id via `node`, `offset` for short sprites); herons in Lake Serin's shallows and hens in Verdana are `decor` (PixelLab animate_image strips, no collision). A card merchant stall stands in Verdana's square (`merchant`); lily pads and moored rowboats are `afloat`. **The Frost Grotto** (`scenes/world/starfall_grotto.tscn`, `python scripts/tools/build_grotto.py`) is an ice cave behind a cave mouth (a `portals` exit) in the Starfall Range's east shoulder, composed from a PixelLab ice cave cliff set: glowing ice crystals, frost wolves, the smugglers' crates, an ice wall with Frisalle's daylight behind it, and the cache holding the **Frostfang Charm** (sword hits freeze monsters for a moment: `Hitbox.freeze`). New monsters: Bristle Ram (plains) and Frost Wolf (Starfall), from PixelLab quadrupeds. "Stones That Remember" (Aldous, Verdana): read the three standing stones (`Quests.STONES`: the Aurewind circle, Stone Point, the Starfall stone), reward the Stonesong Charm (+1 heart while worn). Errands: Tilly (3 rams), Marta (a smoked fish), Oda (visit Lake Serin), Neri (a tonic), Hald (3 wolves); kill favours name their hunting ground (`hunt`). **The final set is 47 cards**: the thirty from Kalmora and Thornveil plus three per region past the west gate (and three in Frisalle, below): Bristle Fleece (ram drop), Shepherd's Bell (Tilly), Crown Stone Rubbing (Kestrel Rise chest); Golden Sheaf (Marta), Harvest Oak Leaf (Oda), Miller's Seal (barn loft chest); Heron Plume (Neri), Serin Lily (Stone Point chest), Drowned Barge Bell (Heron Bluffs chest); Iron Wolf Collar (frost wolf drop), Starfall Edelweiss (Hald), Fallen Star Shard (the pass cairn). Plus the Rime Antler, dropped by the **Rime Stag** (`scripts/characters/rime_stag.gd`, extends Boss; `data/bosses/rime_stag.tres`), the Starfall Range's boss on the high snowfield east of the pass (`boss` in the layout: its arena is kept clear): it stalks, paws out a charge line and gallops down it, skids winded (hits hurt more then), sweeps its antlers up close and, enraged, stamps out a ring of ice shards (`Projectile.ice`). Kill cap 3; respawned by the west gate and the Warden's Sanctum. And the Cairn Heart, dropped by the **Cairn Colossus** (`scripts/characters/cairn_colossus.gd`), the Aurewind Plains' boss on Kestrel Rise: asleep it is a heap of standing stones (`dormant_texture`); awake its stone turns two thirds of every blow while it walks; it hurls boulders and, sunk into the earth (untouchable), raises stone pillars under its target, both as marked `GroundImpact`s (`scripts/systems/ground_impact.gd`, reusable for any boss); it surfaces with its rune open (full damage) and pounds the ground up close. Kill cap 3; respawned by Kalmora's north gate and the Veyra shore path; `tests/test_colossus`. **Boss deaths are dramatic** (`Boss._dramatic_death`): slow motion, white/red convulsions with camera jolts, a collapse, a burst of light and rising motes, and only then do the cards and a purse of gold spill out on the ground (the Colossus crumbles into its heap of stones). **Shared boss fights:** collectors together in an awake boss's arena keep a truce (`Combat.in_truce`: rivals can't hurt anyone in it; the player can, which breaks it, `Boss.truce_broken`); fighters (Raider, Hoarder) go for the boss, the Runner keeps it busy from a distance, all cheer (`RivalLines` boss_join/boss_cheer); if it falls to more than one of them with the truce kept (`EventBus.boss_shared_win`) they say so (boss_won), gather their prize and leave the zone without touching anyone (`Rival._peace_until`). Outside that, rivals are everyone's rivals: hunters go after whoever leads (rivals included), anyone sneaks a loose card off anyone (`Rival._sneak_mark`), fighters (`RivalProfile.fights_back`) hit back and go after whoever robbed them; `tests/test_stag` covers the truce. PixelLab animation templates sometimes return frames on an opaque grey box: check imported sheets on a magenta background and clear them with `python scripts/tools/key_frame_boxes.py <sheet> <cell w> <cell h>` (only boxes, never outlines). Aldous and Hald explain their bosses when asked. **A respawn gate opened while its boss is alive is owed** (`bosses[id].owed`), so the boss comes back after its next kill; `tests/test_stag`. Ambience beds: meadow, lake, mountain. Pell gives **Emberburst Rounds** after "What the Trees Remember": a charm that lets you hold the pistol to charge a round that bursts where it lands (`scripts/systems/explosion.gd`).

## Major characters

Twelve residents are the island's major characters (Jordan's list: breeds, coats, families and personalities are fixed). Use them whenever a role fits instead of inventing someone new.

| Name | Breed / coat | Role | In game |
|---|---|---|---|
| Chef | German Shepherd, black and brown | The royal son. Owns the gourmet restaurant in Vetrassa the whole island talks about; the Hoarder's family dines there, and Chef hears everything said over the plates | mentioned (Mate, Jobelle, Loki) |
| Freya | German Shepherd, black and brown | The royal daughter, Chef's sister. Captain of the King's Guard in Vetrassa; keeps the throne room for "An Audience Before the Throne" | later |
| Loki | German Shepherd, black and brown | **The King of Virelia Isle**, Xena's husband, father of Chef, Freya and Sully. Travels the roads incognito every race to watch the racers; nobody knows who he is and he never says (the prize stays secret) | yes: plays cards by the travellers' fire on the Aurewind Plains (Loki's Table: whispers, seals, second winds; buys cards); his lines hint at his family and his wife's 'for the best' |
| Xena | German Shepherd, all black | **The Queen**, Loki's wife, and foreman of the Duskara mines: hard, capable, believes she protects her laborers by keeping them working; keeps the ledgers ("The Foreman's Names") | later |
| Sully | German Shepherd, all black | The King and Queen's estranged son, adopted as a boy by the sisters Jobelle, Mate and Tilly (his brother now; he doesn't use his birth name). Runs the escape line out of his mother's mine ("Beneath the Dunes") | yes: keeps the escape line's way-station in the Frost Grotto (errand: two lake trout for a moss lantern; `NPCS` in build_grotto.py) |
| Tilly | Labrador, yellow | Shepherd on the Aurewind Plains; the youngest of the three sisters (with Jobelle and Mate), Tally's best friend (errand: the bristle rams) | yes |
| Tally | Australian Shepherd, black/white/brown | Keeps the Sheaf & Sickle in Verdana and its tally of the Company's unpaid debts. Highly energetic, hates men (Bruno is the only one allowed in her kitchen), and dinner is at FIVE sharp, every day | yes: serves dinner 17:00-18:00 (it mends every heart), warns you the hour before |
| Jobelle | tabby cat | Kalmora's innkeeper (the Salted Lantern; Otto keeps the bar). Sweet and caring; the eldest sister, she worries over Mate and Tilly | yes |
| Mate | tabby cat, female | Sorenda's innkeeper (the Copper Kettle), Jobelle's and Tilly's sister. Missing her left arm (lost to a Thornveil hound). Abrasive; HATES Chef and insists her inn food beats his restaurant | yes |
| Sparkle | Maltese, white (an upright puppy: long silky coat, topknot with a red bow) | The royal family's cousin (the King's niece), Sassy's sister. Fearless. **Co-owner of Seabright Quay** (runs the boats and the diving); will be part of several future story quests | yes: strolls the quay at Seabright (errand: go all the way into the Frost Grotto, which she isn't allowed to) |
| Sassy | Schnauzer, gray | The royal family's cousin (the King's niece), Sparkle's sister. Slightly airheaded. **Co-owner of Seabright Quay** (runs the guests and the parties); will be part of several future story quests | yes: "working" on a sun lounger on Seabright's beach (gives you a card she found in her hat just for talking) |
| Duke | Dachshund | A wealthy aristocrat in Vetrassa, Chef's best friend and his number one customer. Part of shady dealings with the Duskara mines (a buyer or backer of what comes out of them; ties to the Hoarder's family's trade). Pays Seabright's upkeep for the Company and keeps the Grand's whole top floor; signs the Frisalle ice-road letters 'D.' with a dachshund's head over a crossed pick | yes: at his table on the Saltglass Terrace at Seabright Quay, with three silent 'Company men' in suits (one guarding Bungalow 3); charming and evasive. Vetrassa later |

**Seabright Quay, the Royal Resort** (`scenes/world/seabright_quay.tscn`, south of Verdana, `RESORT` in region_layouts.py; the feel of a luxury quay resort like FFXV's Galdin Quay, style only). **Sparkle and Sassy own it** (the King's gift to his nieces; its upkeep is paid by the Duskara Mining Company through the Duke, and the sisters keep the bills in a drawer unopened). The road comes down through palms to a forecourt with Kalmora's fountain; stairs drop to a cobbled quay (benches, lamps, café tables, the brass plaque); a long railed boardwalk runs out over clear turquoise water to the **Saltglass Terrace**, an open-air restaurant on its own deck in the bay serving **Chef's dishes** (Chef stays in Vetrassa and sends recipes and complaints): **Pepper**, a Dalmatian he trained, cooks at the open kitchen and sells Seabright Stew (3 hearts), Chef's Lemon Tart (2) and bread; tables under parasols, the menu board. Jetties run east and west from the terrace, lined with private **overwater bungalows** (props, no way in; Bungalow 3 has a readable door) and the **sisters' own bungalow** at the far east end (interior `seabright_bungalow`: the deed, Sparkle's dive log, Sassy's seating plan, a letter from Chef); yachts bobbing at their moorings south of the east jetty (a PixelLab-animated strip as `decor`); rowboats, crates and a fishing spot at the west end; a diving pier off the terrace's sea side. The **Seabright Grand** (`resort/pavilion.png`, interior `seabright_hotel`: Fennick the poodle concierge keeps the rooms, the town's inn, and the guest register) stands on the grassy headland to the east over the bay, with the lookout and its telescope past it. West of the quay a white beach curls round a cove (loungers, parasols, cabanas, the thatched beach bar, Sassy). Sparkle strolls the quay. Staff and guests: a Corgi waiter on the terrace, a Boxer lifeguard on the beach, and the Duke with his Company men. **Story hooks for future quests** (Jordan: the sisters will be part of several story quest lines): the unlit barge seen from the lookout and the light on the water at night, letting something down on a rope at the old reef (Sparkle's dive log, ties to Halmeer's 'The Smuggler's Route'); the Duke's standing booking of the Grand's top floor and his nameless 'Company' guests (the register, Sassy's seating plan, Pepper's lines, the Saltglass menu's private dining); the Company paying for everything; nobody in the royal family comes to the sisters' parties. Region builder features it added: `cliffs`/`flats` (a cliff set per pair of levels, Kalmora's sea_quay, quay_town and sea_rock), `sea_level` (Kalmora's animated sea clipped to the sea pixels), `beaches` (polygons: sand replaces the sea with a ragged waterline, wet band and shell flecks), `sea_depth` (a layer over the waves: turquoise shallows near land, sandy-pale off the beach, deep blue offshore, broken foam on the sand, the boardwalk's shadow and pilings), `dock_rails` (a white rail and posts along every deck edge over water; docks are walkable across quay walls), `pools`, `palm` trees, `instances` and `dress_levels`/`tree_levels` (which levels may carry undergrowth/tufts and trees, keeping them off cobbles and sand). NPC sprites whose PixelLab breathing-idle template smears them (Sparkle, Pepper) get their idle from the clean rotations plus a 1 px breath added after import. Ambience: harbor.

**Frisalle** (`scenes/world/frisalle.tscn`, `FRISALLE` in region_layouts.py, the snow village north over the Starfall pass): the pass is closed by an avalanche dug through to a **card gate** (`starfall_pass`, Frisalle's toll: one Iron Wolf Collar, `gates` in a region layout emit `card_gate.tscn`; a bank of boulders either side and an exit gap exactly the gate's width, so it can't be walked round). **The ice road** is the way round the toll (pay in effort, past the wolves' den): the Frost Grotto's ice wall has been cut through by the smugglers into a tunnel that comes out of an ice-cave mouth behind Frisalle's upper terrace (`ToFrisalle` in build_grotto.py, `portals` in the layout, EDGES both ways with no gate). Three heights: the lower valley (the pass road, a frozen pond, frost wolves), the village terrace (a cobbled square under strings of lanterns round the weigh house and a loaded sled, a knitwear stall and the card merchant at the toy stall (`merchant`), a fire pit, the skating pond with a snowman, the signpost, a goat pen, woodpiles; the **Hearth & Horn** inn, the woodcarver's, the guide's lodge, the weigh master's house, and private neighbours' chalets as props) and the upper terrace (the factors' **counting house** and the **bell tower** with the guides' names). Alpine chalets, steep snowy roofs, smoke curling from every chimney (`smoke()`/`CHIMNEYS` in the layout: a PixelLab-animated strip as `decor`), blue shadows, snowfall (all PixelLab: `assets/sprites/tiles/frisalle/`, props in `props/`). Every building is enterable (build_interiors.py `frisalle_*`). Residents: **Ottilie** (Bernese Mountain Dog, keeps the Hearth & Horn; warm, fierce; her husband Anselm, a guide, died in the slide; the toll was her idea; errand: bring her a Seabright Stew from Pepper, for the Frisalle Hearthstone), **Mirren** (Siamese cat, the factors' nervous clerk; quest **"The Merchant's Ledger"**: read the weigh house tally board, the great ledger in the counting house and the letter hidden in Bodo's desk (`Quests.LEDGER_CLUES`), reward 60 gold and the Factors' Seal; if the Hoarder is racing, the Vetrassa factors are their family's people), **Bodo** (Saint Bernard weigh master, newly and inexplicably rich), **Liesl** (Norwegian Forest Cat woodcarver) and **Sven** (Husky guide, out of work since the slide). The story: the slide was brought down on purpose (drill marks) so nobody would see forty carts a winter come through an ice road under the mountain (the Frost Grotto's smugglers), weighed at night, sealed with the factors' second seal and sent to Vetrassa 'for the Company', signed 'D.' with a dachshund's head: the Duke. Cards: Frisalle Hearthstone (Ottilie), Factors' Seal (Mirren's quest), Snowglass Lantern (the bell tower chest). Ambience: mountain.

**Inns:** every town has one, and its keeper (`Npc.inn_rooms`, set by `"inn"` in build_interiors.py) rents a room for half a day or a full day (`scripts/systems/inn.gd`: 10 / 18 gold). Sleeping fades out (`Transition.rest`), moves `TimeOfDay` on, lets the rivals roam a sixth of that time off screen (`RivalDirector.pass_time`) and mends every heart. **Hearts carry from area to area** (`GameState.player_health`, saved): changing zone never heals. Rest, food, the Heartwood spring, Mossheart and waking in town after fainting do. Keepers are set up by `"inn"`/`"keeper"` in build_interiors.py: their own room prompt and broke line, food and tonics over the counter (`INN_STOCK`), and a `meal_hour` (Tally's dinner). Every resident's ambient `lines` rotate one per conversation and carry on across visits (`Npc.next_line`, starting at a random line), so write keepers long lists of lines in their own voice. A new town needs an inn keeper; `tests/test_inn` checks them. **Fishing:** `fishing` spots in a region layout (`scripts/systems/fishing_spot.gd`; one off Neri's dock on Lake Serin): cast, wait for the float to go under, reel in on the bite (early spooks it, late loses it); mostly Lake Trout (heals 2, not sold), now and then a coin. Food that costs time instead of gold.
