# System Map — Prehistoric Tribes (J2ME, THQ / Gear Games, 2008)

In English, for learning at source-code level.
Source: JAR `prehistoric_tribes_240x320-84398_4_at1w.jar` (487 KB, MIDP-2.0, 240x320),
decompiled with CFR 0.152 → 13,418 lines, 7 classes. Class and field names were
obfuscated to `a`–`f`, so some meanings are inferred from context and game text.
Anything not yet certain is marked as such.

## 1. Game identity

- MIDlet: `Prehistoric Tribes`, version 0.1.28, vendor THQ, `MIDlet-1: Prehistoric Tribes, icon.png, tribes`
- `MicroEdition-Profile: MIDP-2.0`, `CLDC-1.0`, `Cheat-Support: off` in the manifest (but cheat code exists, see §4)
- Credits in the text: © 2008 THQ Wireless Inc., wireless version developed by Gear Games, Ltd.
- Genre: real-time village strategy, not arcade. Two tribes (player + enemy) on a grid map.

## 2. Code map (7 classes)

| Class | Lines | Role |
|---|---|---|
| `tribes` | 78 | MIDlet entry point. `startApp` → thread → loading → game |
| `d` | 53 | Loading / splash screen (Canvas) |
| `f` | 6,680 | Main game: Canvas + game loop + input + rendering + save/load |
| `b` | 5,805 | World logic: map, villagers, buildings, enemy AI, combat |
| `e` | 280 | Resource loader (`ma`, `pd0`, `pi0/pi8/pi9`, `sa`, font) |
| `c` | 404 | Text/language loader (`s`, `t`, `d0`) + text drawing |
| `a` | 118 | MIDI music player |

## 3. Main flow

`startApp()` → `run()` in `tribes`:
- Create the loading screen `d`, show `l0` (THQ logo, 1 second) → `l1` (Gear Games logo, 2 seconds) → `l2` (title screen, 2 seconds). Total about 5 seconds. The number 5 means "finished" (images are only drawn when the number is < 4).
- Then `new f(this)`, and `f.a()` starts the game thread.
- `pauseApp()` → `f.d()`, `destroyApp()` → `f.b()`.

Game loop, `f.run()` (lines 485-540):
- Set up the world with `new b()`, the loader with `new e(this)`, and `setCurrent(this)`.
- Try to load a save: `d(0)` first (settings), and if that fails try `d(1)`, then `d(2)`.
- Starting values: `Q=14` (main menu), `v=0` (menu mode).
- Each iteration: `aS()` (pause + music) → `h()` (update logic) → `m()` (draw to buffer) → `l()` (repaint + wait for paint to finish) → sleep for the remaining time.
- Target about 50 ms per tick when mode `c` is true → **about 20 ticks per second**. The value for the other mode cannot be determined safely because the field names collide after obfuscation.
- `h()`: the animation counter resets at 8, another counter resets at 120. If `v==0` (menu) → `ak()`; if `v==1` (in game) → `V()` (input) + `k()` (find the nearest building/unit to the cursor), a periodic trigger every 6 ticks, then `j()` → `b.g(), b.e(), b.h(), b.i()` (world update). If the mission-end counter `u` reaches 41 or 90 → `v=0, Q=24` (mission-end screen).

States (`v` and `Q`, screen numbers, not names):
- `v==0` = menu, `v==1` = in game. `R` = the previous screen (for going back).
- Q 14 = main menu. Q 10/11 = pause in game. Q 20 = building/unit info popup. Q 22/23 = load/result. Q 24 = mission end. Q 25 = exit from the game. Q 27 = system pause (from `hideNotify()`, not from a button; returning goes through `showNotify()` → `Q=R`). Q 32 = advert screen `/l3`.
- Starting a game: `am()`, `T=1` → `v=1`. There is a level boundary `q < 7` vs `q >= 7` (campaign vs custom, which matches the text, though the code itself does not use those words).

## 4. Input

- Loading screen: `keyPressed()` is empty, keys are ignored.
- Softkeys: left `-6` (or `6` / `*`), right `-7` (or `7` / `#`).
- D-pad via `getGameAction` + number keys: up `2`, down `8`, left `4`, right `6`, select/centre `5` (FIRE). Number keys `1/3/7/9` = change group, `0` = group 0.
- `keyReleased()`: turns off the direction flags; releasing the centre key quickly (< 4 ticks) = a tap to select.
- Softkeys in game: left → open the build menu (`w=2`); right → close the menu / cancel selection / open the pause screen Q 10/11.
- Cheat (a fact from the code, `m()` lines 6595-6680): the sequence `8,7,3,9,1`, then a sixth key: `1` → flag `af`, `3` → flag `ag`, `7` → +100 to the first 5 resources, `9` → `u=1`. The manifest says Cheat-Support is off, but the cheat code is there.

## 5. Rendering

- Double buffering: `Image[]` / `Graphics[]`, 4 slots. Loading buffer `a[0]` is 264x352; game buffers `a[1]` and `a[3]` are 264x304, plus a small 79x63 buffer.
- Flow: `m()` draws to the off-screen buffer (map, units, menu) → `l()` → `repaint()` → `paint()` copies the buffer to the screen with `drawRegion`.
- The game is designed for 240x320, but the buffer is 264x352, copied with an offset of (-11,-8) — an 11 px frame on the left and an 8 px frame on top.
- Map tiles are 22x16 pixels. Camera: 11 columns x 18 rows visible. Smooth scrolling is half a tile (11 px horizontally, 8 px vertically).

## 6. World (b.java)

- The map is a grid of at most **96x96 tiles**. Each level's size comes from a table: level 0 is forced to 40x32, level 5 has its width reduced by 32.
- Two grids: `b[][]` = terrain type, `c[][]` = occupant (0 empty, positive = villager number 1-100, negative = building number).
- The map is stored in file `ma` (42,381 bytes), in 10 pieces (offsets 0, 2545, 6965, 10649, 15487, 22633, 27261, 31708, 35466, 39214). Bytes ≥ 250 are repeat codes (simple RLE compression).
- The 10 map names in the text: outside, revenge, escape, wastelands, a new home, great lake, desert pass, forest belt, slaughter, plot of land.
- All balance numbers (costs, HP, damage) are in file `pd0` (96,990 bytes: 11 short tables + 25 byte tables), not in the code. So the exact numbers cannot be read without decoding `pd0`.

### Buildings — 12 types

| # | Building | Function |
|---|---|---|
| 0 | armoury | the armourer produces weapons here |
| 1 | gym | warriors train melee skills |
| 2 | hut | villagers rest and reproduce here, 1 hut = 4 people |
| 3 | chief's hut | the chief's home, where the elders meet |
| 4 | kitchen | place to eat, needs a cook |
| 5 | range | warriors train throwing skills |
| 6 | store | stores all resources + weapons |
| 7 | disco | raises spirits, needs a DJ |
| 8 | sanctuary | the shaman heals + casts spells |
| 9 | pia center | trains scouts, who see further and hide |
| 10 | nursery | children are safe from animals/enemies here |
| 11 | tower | guards see further + attack with throwing weapons |

- At most 30 buildings per tribe. A hut adds +4 living space (capped at 50). The building menu offers: upgrade, repair, cancel upgrade/repair, demolish. When HP runs out → "building is lost!".
- Building requirements: enough stock (otherwise → "need resources!") + the required role must exist (otherwise → "we need a cook / shaman / armourer / dj").

### Villagers

- At most 50 villagers per tribe (player `u=0`, enemy `u=1`). Text: "max villagers".
- They are stored as numbered slots + many parallel arrays, not as objects. Readable fields: position, age, gender (0 male / 1 female), HP / max HP, task/status, 2 combat skills, 7 civilian skills, speed, 3 need meters, role/job.
- Roles: villager, warrior, chief, shaman, cook, armourer, DJ, scout, guard, child. The default at birth is 9 (unemployed). The chief is special, with its slot number stored separately; if the chief dies → "the chief is dead! … choose a new one", and the player picks a new chief.
- Birth/growth: age rises every 125 ticks (player) / 50 ticks (enemy). Adulthood at age 12, when skills are assigned and the task is reset. Children under 12 cannot work.
- Reproduction: an opposite-sex pair with enough mood goes to a hut, status 109→110→111, and a child is born from the hut (when the hut's birth counter reaches 3 → a new villager aged 2).
- Three meters, 0-99 (happiness, hunger, tiredness — labels from the text): mood is calculated from buildings/disco minus hunger/tiredness. Low mood → the villager refuses to work ("leave me alone, tyrant! i'm depressed"). Hunger/tiredness fall over time, and villagers automatically go to eat/rest. A meter reaching 0 can kill. Food is taken from stock; without a kitchen → "our tribe is starving!".
- Disease: a sickness flag, spreading +8 to villagers on neighbouring tiles. The shaman heals.
- Death: HP ≤ 0 → the slot is emptied, text "…is dead". Max HP changes with age (table `pd0`).
- Names: 122 random names in the text (jafar, jumbo, juju, mumbo, konan, fred, barney, … ubika).

### Resources / economy

- Each tribe's stock: an array of 25 numbers, capped at 999.
- 4 material resources (labels from the text): **food, wood, stones, bones**, plus weapons as a separate stock (produced by the armoury, stored in the store).
- Production: when a task finishes, `J()` adds to stock according to table `pd0`. Consumption: building/upgrading/repairing and eating reduce stock.
- Exact production/consumption numbers per building cannot be determined without decoding `pd0`.

### Combat / enemies

- 6 weapons: club, stone, spear, stone axe, bone mace, tomahawk. 3 traps: net trap, spring trap, pit trap (types 20-22, not ordinary buildings).
- A throwing attack is a parabolic projectile: flight time from distance + table gravity, position each tick from a quadratic formula, damage = attacker skill + weapon bonus − target defence + randomness.
- Enemies arrive in waves, not continuously: the attack timer comes from a table (`tabel[214] − tabel[215] × difficulty` + randomness), the number of attackers grows over time (capped by a table), sent in stages every 150 ticks. Warnings: "enemy sighted!", "we're under attack!".
- The enemy AI plays with the same system: it builds/upgrades/repairs its own buildings, schedules attacks, and assigns roles to its villagers from a per-level table. It is not a one-off script.
- Player defence: tower, pia center scouts, traps, and the "form up!" and "call to arms!" commands.
- Win/lose: the texts "you have lost!" / "hurrah! you've won!", with the endgame decided by `b.ak()`: win when enemy buildings reach 0 and the mission flag allows it, lose when player population reaches 0 or a key building is lost where the mission requires it; verdict at `u` = 41 (win) / 90 (lose).
- There are also wild-animal attacks and child theft ("animals have eaten a child!", "the enemy has stolen a child!").

### Other systems

- Real-time with ticks, not turn-based. Each tick `b.e()` processes both tribes in turn (50 villagers + 30 buildings per tribe), then `g()` processes buildings.
- Random: `new Random(1L)` — a fixed seed of 1. Used for starting stats, damage, AI, births, and more.
- Pathfinding: step by step in 8 directions, at most 80 steps, trying another direction if blocked. Spiral search for the nearest empty tile, radius search that expands layer by layer for a target. Distances are precomputed in a 25x25 table.
- Weather/seasons: **none**. Grepping `weather, season, rain, snow, day, night` in `b.java`/`f.java` finds nothing.
- Fog of war: there is a visibility bitmask rebuilt in `b.d()` — probably the explored/visible map, but its function is not yet confirmed.

## 7. Data: languages, text, levels, save/load

### Languages

- 5 folders: 0 English, 1 French, 2 Italian, 3 German, 4 Spanish. Changing language = changing the folder number, then reloading the text.
- The list of language names only exists in folder 0, so the language-selection screen itself is always shown in English.
- String counts (separator `|`): `s` (UI) = 229 pieces, `t` (help/messages) = 72 pieces, `d0` = 236 pieces.
- Accented letters are stored with replacement codes (`franc[ais` = français, `hu^tte` = hütte), translated by the loader through a font table. The raw files look broken, but the game displays them correctly.

### Important text (English)

- Main menu: play | help | options | about | more games | exit
- Pause menu: resume | save | load | quit
- Modes: new game | continue | campaign | custom game | tutorial
- Options: music | hints | off | on | difficulty | easy | hard
- Messages: "building is ready.", "enemy sighted!", "we're under attack!", "building is lost!", "need resources!", "max buildings", "max villagers", "we need a cook / shaman / armourer / dj."
- Warnings: "our tribe is starving! we need a kitchen!", "not enough living space! build more huts.", "our tribe is depressed! a disco will help…", "animals have eaten a child!…", "the chief is dead!…"
- Villager names: about 124 random names.

### Campaign / levels

- Campaign: 12 level values `q = 0`–`11` (campaign path `q = 0`–`6`, `q = 7` is "the end", `q = 8`–`11` custom-only). If `q < 5` after a win, advance to the next mission; winning `q = 6` moves to `q = 7`.
- There are 10 map names in the text, but the campaign has only 7 missions — the mapping from names to missions is not proven (possibly the first 7 are campaign and the rest are custom, or the 10 maps are used in rotation; the table in `pd0` has not been decoded yet).
- Tutorial: its own mode + an "enable tutorial?" option. It is a guided dialogue script in `d0[18]`–`d0[84]` (about 67 pieces): build a store, select a villager, build a hut/kitchen, gather wood/stone, group hotkeys (`7`/`9`), build a gym/armoury/range, "call to arms", happiness, upgrade/repair, fishing, hunting.
- The campaign is locked until the tutorial is passed: "pass the tutorial first!". With no progress yet (`r == 0`), the game forces the tutorial first.
- Full contents of `d0`: [0]–[17] opening story (ice age, the Avnotaklu tribe), [18]–[84] tutorial, [85]–[212] dialogue/cutscenes between missions, [213]–[228] shaman spells + PIA agents + upgrades, [229] controls, [230]–[231] game explanation (4 resources; villager attributes: name, gender, age, happiness, HP, hunger, fatigue; combat vs civilian skills), [233] credits, [234] final score labels.

### Save / load

- RecordStore: prefix `"t"`, 3 slots: **`t0`, `t1`, `t2`**, one record per slot.
- `t0` = settings + campaign progress (7 values: 1 int, 1 boolean, 5 bytes; `r` = the highest campaign level unlocked).
- `t1` = campaign save game (`q < 7`), `t2` = custom save game (`q >= 7`).
- Save contents: level number, difficulty, the whole map (96x96 grid, 3 layers), villagers (up to 100 people + attributes/skills), buildings (up to 60 + position/type/HP), 26 resource numbers, camera position, score/time, flags. Written in order with `DataOutputStream`, read back in exactly the same order — if the order differs, the save is broken.
- Load when the game starts (try `t0`, and if that fails try `t1`/`t2`). Manual save from the save menu → "game saved." / "not enough memory to save game." Automatic save after a mission ends and after winning a campaign mission. There is no autosave every second.
- Saving overwrites: `deleteRecordStore` first, then create a new one. A corrupt save is deleted and loading is tried again, not repaired.

### Resource loader (e.java)

| File | Size | Contents |
|---|---|---|
| `/pd0` | 96,990 | Game data tables (balance/level numbers). `e.b()`: skip 1 byte, read 11 short tables + 25 byte tables |
| `/ma` | 42,381 | Raw map/level data, 9-10 pieces (offsets above) |
| `/pi0` | 62,502 | A set of PNG images (sprite sheet 1) |
| `/pi9` | 8,597 | A set of PNG images (sprite sheet 2) |
| `/pi8` | 129,809 | A set of PNG images (sprite sheet 3), loaded on demand |
| `/sa` | 26,616 | MIDI music, 5 songs joined together. Lengths {8014,6315,5648,3405,3234}, positions {0,8014,14329,19977,23382} |
| `/a` | 18,842 | Font/letter data (312 length numbers + a 17,638-byte blob) |
| `icon.png` | 2,168 | 48x48 icon |

- The 2-byte prefix in `pi0/pi8/pi9`: not a single PNG, but many PNGs joined together, each PNG preceded by a 2-byte big-endian length. Example: the first PNG in `pi0` is 9,120 bytes, in `pi8` 10,910 bytes, in `pi9` 2,814 bytes. First images: `pi0` 128x136, `pi8` 240x130, `pi9` 76x111 (8-bit palette PNG).
- Images `l0`–`l3` (plain PNG): `l0` THQ Wireless logo 240x71, `l1` Gear Games logo 192x114, `l2` title screen 240x321, `l3` French Orange advert 240x320 ("Plus de jeux sur ton mobile? Envoie PLUS au 2 33 33*…") — an operator advert, not part of the game itself.

## 8. Music

- One player, class `a`, MIDI only, no separate sound-effects class.
- 5 songs in a single file `/sa`. `aQ()` picks a random song, `aS()` is checked every tick: if nothing is playing and the game is not paused (Q != 27), play a random song. Volume `setLevel(n * 20)`.

## 9. Open questions

1. Exact costs/HP/damage for each building, weapon, and level — needs the `pd0` tables decoded.
2. The exact mapping of the 10 map names to the 7 campaign missions + tutorial/custom modes.
3. The specific win/lose conditions for each mission (in `b.ak()`, per-mission flags in record 279).
4. The exact meaning of each villager task code (0–111) — only some can be guessed from context.
5. The exact labels for each screen number Q (15, 17, 18, 19, etc.) and the function of the visibility bitmask.
6. The exact format of each piece in `ma` (simply compressed/encoded tiles, not yet fully decoded).

## 10. Working files

- `extracted/` — 43 files from unzipping the JAR
- `decompiled-cfr/` — 7 Java files from CFR
- `ANALISIS-alur-utama.md` — main-flow report
- `tools/` — Java 17 (Temurin) + CFR 0.152 + JADX 1.5.2 (zip)
