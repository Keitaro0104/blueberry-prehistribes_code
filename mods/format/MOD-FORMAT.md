# Prehistoric Tribes — Mod Format v0.1

English. For the J2ME game Prehistoric Tribes (THQ Wireless / Gear Games, 2008).
This spec is derived from the decoded original data formats; see the research
in this repo (`PETA-SISTEM.md`, `PD0-ANALYSIS.md`, `MA-MAPS.md`,
`DECODE-REMAINING.md`). Nothing in this spec requires game assets: a mod is
plain JSON files plus optional PNG sprites.

## 1. Goals

1. **Anyone can add a map, a building variant, and later a unit or a weapon,
   without touching binary files or Java code.**
2. **Mods are data, not code.** A mod never contains `.class`, `.jar`, or
   decompiled game code.
3. **Human-readable first.** A modder edits JSON in a text editor; a loader
   converts it to the original binary formats.
4. **Versioned.** Every mod declares `format_version`. Loaders must reject
   versions they do not understand instead of guessing.
5. **Lossless round-trip for the base game.** Every field maps back to a
   known place in the original data (see §7). Anything that cannot be
   mapped is marked open, not silently invented.

## 2. Principles

- **One mod = one folder.** A mod folder contains a manifest and content
  files. It never modifies the base game files.
- **IDs are mod-local strings** (`"green-valley"`, `"large_hut"`), except
  where they must match the original numeric type (`base_type`).
- **Numbers are plain integers.** Costs and HP are integers, never floats.
  Resource amounts are whole units, as in the original stock arrays.
- **Explicit is better than clever.** Win/lose conditions are written out
  as booleans, not only as a bitfield. The original bitfield value is kept
  alongside them for traceability.
- **Validation before loading.** A loader must validate a mod against §6
  and refuse it with a readable error if it fails. Never load a half-valid mod.

## 3. Mod folder layout

```
my-mod/
  mod.json            # manifest (required)
  maps/
    green-valley.json # one map per file (v0.1)
  buildings/
    large-hut.json    # one building per file (v0.1)
  units/              # v0.2, see §8
  weapons/            # v0.2, see §8
  sprites/            # optional PNG files, referenced by name (v0.1: reference only)
```

Rules:

- File names use lowercase letters, digits, `-`, `_` only.
- `mod.json` is required. A folder without it is not a mod.
- Unknown files are ignored by loaders, but must never be game assets
  (no `.jar`, `.class`, or files copied from the original JAR).

## 4. Manifest — `mod.json`

| Field | Type | Required | Meaning |
|---|---|---|---|
| `format_version` | string | yes | `"0.1"` for this spec. |
| `id` | string | yes | Unique mod id, e.g. `"green-valley-mod"`. Lowercase, digits, `-`, `_`. |
| `name` | string | yes | Human-readable name. |
| `author` | string | no | Mod author. |
| `description` | string | no | One or two sentences. |
| `game` | string | yes | Must be `"prehistoric-tribes"`. |
| `maps` | array of strings | no | File paths of maps in this mod, e.g. `["maps/green-valley.json"]`. |
| `buildings` | array of strings | no | File paths of buildings, e.g. `["buildings/large-hut.json"]`. |
| `units` | array of strings | no | Reserved for v0.2. Must be empty or absent in v0.1. |
| `weapons` | array of strings | no | Reserved for v0.2. Must be empty or absent in v0.1. |

Example:

```json
{
  "format_version": "0.1",
  "id": "green-valley-mod",
  "name": "Green Valley",
  "author": "Example Author",
  "description": "A small example map plus a cheaper, weaker hut variant.",
  "game": "prehistoric-tribes",
  "maps": ["maps/green-valley.json"],
  "buildings": ["buildings/large-hut.json"]
}
```

## 5. Map schema (v0.1, final)

One file per map. `kind` must be `"map"`.

| Field | Type | Required | Meaning / source |
|---|---|---|---|
| `format_version` | string | yes | `"0.1"`. |
| `kind` | string | yes | `"map"`. |
| `id` | string | yes | Mod-local map id, e.g. `"green-valley"`. |
| `name` | string | yes | Display name, e.g. `"Green Valley"`. Shown in the map list. Original names live in text file `s` indices 82–91. |
| `description` | string | no | Short description. |
| `width` | integer | yes | Tiles across. 1–96. Original: `/a` record 149, width per level. |
| `height` | integer | yes | Tiles down. 1–96. Original: `/a` record 149, height per level. |
| `based_on` | object | no | `{ "level_q": 0, "name": "outside", "size": [40, 32] }` — the original level this map is modelled on, for reference only. |
| `tiles` | array of arrays of integers | yes | `height` rows, each `width` tile IDs, row-major, top row first. Row = y (0 = top), column = x (0 = left). See tile ID rules below. |
| `spawns` | array of objects | no | Spawn points. Each: `{ "type": 1–5, "row": int, "col": int }`. The tile at that position in `tiles` must be `174 + type` (175–179). Original: `f.aN()` registers tiles 175–179 as map objects, types 1–5, arguments from `/a` record 110 = `[20, 20, 20, 15, 25]`. |
| `player_start` | object | no | `{ "row": int, "col": int }` — starting cursor position. Must be inside the map and on a walkable tile. Original: `/a` record 150 (spawn cursor per level; q0 is (15, 5) as x,y). |

> **J2ME repack note (proven 2026-11-19):** in the original engine `player_start` is *not* where the camera starts — the camera follows the player's tribe, whose spawn comes from the level's setup table (`/a` record 261). A repacked map must set record 150 to the centroid of the remapped player villagers, or the viewport starts over unseen fog-of-war terrain and renders black. A future Android loader that spawns the tribe at `player_start` can use it for the camera too.
| `win_lose` | object | yes | See below. |
| `source_notes` | string | no | Free-text notes on where the values came from. |

### Tile IDs (proven ranges — see `MA-MAPS.md`)

- **0** — open ground (most common tile on every original map).
- **3** — open-ground variant, walkable. Base tiles ≤ 8 get +0..2 random
  jitter at load in the original game, so 3 may appear in game as 3, 4, or 5.
- **43** — blocked obstacle. Blocked ranges in the original are
  6–8, 29–75, 115–127, 135–175, 183–215 (from `pd0` table `b[9]` bit 13).
  Tile 43 is inside 29–75 and is the most frequent non-ground tile on the
  original maps, so it is the recommended obstacle tile in v0.1.
- **175–179** — spawn tiles, types 1–5. Must match the `spawns` list.
  What each spawn type places (resource, unit, building) is **not yet
  proven** — see §9.
- Any other tile ID is allowed only if it is in a proven range:
  walkable 0–5, 9–28, 76–114, 128–134, 176–179 is spawn, 180–231 are
  special markers (see below), 232–242 are other graphics. **Tile visual
  meanings (which ID is grass, water, forest, rock) are not proven** —
  tile IDs are graphics indices, and v0.1 treats them as opaque numbers.
  Do not invent terrain names for IDs.
- Tiles **180–231** get marker `c=-124` in the original loader, and
  **63–75 / 115–127** get marker `c=-125` (except level q=3, where that
  step is skipped). A v0.1 loader must reproduce those markers, or refuse
  maps using those IDs. In the example map they are not used.
- Border cells (first/last row, last column) are forced to `c=-126` by the
  original loader. Mod maps should still put blocked tiles on the border
  themselves, so the map is valid even before that step.

### Win/lose (`win_lose` object)

Original source: file `/a` record 279, per level q=0–6 values
`[2, 3, 2, 4, 3, 2, 3]`; decided by `b.ak()`, not `b.k()`
(`b.k()` only sets a music phase). Verdict comes ~40 ticks after the
condition is armed: `u == 41` = win, `u == 90` = lose.

| Field | Type | Required | Meaning |
|---|---|---|---|
| `flags` | integer | yes | Original record-279 value (0–7). Bit 1 (value 1) = win by destroying all enemy buildings. Bit 2 (value 2) = lose if building slot 1 is destroyed. Bit 4 (value 4) = unproven, only set for q=3. |
| `win_by_destroying_enemy_buildings` | boolean | yes | Must equal `flags & 1`. |
| `lose_if_key_building_destroyed` | boolean | yes | Must equal `flags & 2`. |
| `lose_if_tribe_wiped_out` | boolean | yes | Always `true` in the original: losing by population reaching 0 applies in every mission (`b.ak()`). |

## 6. Building schema (v0.1, final)

One file per building. `kind` must be `"building"`.

| Field | Type | Required | Meaning / source |
|---|---|---|---|
| `format_version` | string | yes | `"0.1"`. |
| `kind` | string | yes | `"building"`. |
| `id` | string | yes | Mod-local id, e.g. `"large_hut"`. |
| `name` | string | yes | Display name. Original names: text file `s` indices 0–11. |
| `base_type` | integer | yes | Original building type this entry is based on, 0–11 (see table below). v0.1 buildings are **variants of an existing type**: they reuse that type's code path (behaviour, role requirements, sprite family). A genuinely new type (12+) is not possible in v0.1 — see §9. |
| `description` | string | no | Short description. Original: text file `t` indices 0–11. |
| `width` | integer | yes | Tiles wide. Original: `/a` record 138, row 4. |
| `height` | integer | yes | Tiles tall. Original: `/a` record 138, row 5. |
| `hp_by_level` | array of 3 integers | yes | Max HP at levels 1, 2, 3. Original: record 138, rows 7–9. All > 0. |
| `build_cost` | object | yes | Full construction cost, paid once. Keys are resource names, values are integers ≥ 0. Original: record 138, rows 13–15, paid from tribe stock `[2], [3], [4]`. |
| `upgrade_cost` | object | yes | Upgrade cost per level step, paid progressively. Original: record 138, rows 10–12. Same keys as `build_cost`. |
| `mood_bonus_by_level` | array of 3 integers | no | Mood bonus at levels 1, 2, 3. Original: record 138, rows 21–23. Default `[0, 0, 0]`. |
| `worker_capacity` | integer | no | How many villagers can be assigned to this building. Original: `/a` record 80 (inferred as worker capacity). Default: the base type's value. |
| `living_space` | integer | no | Extra living space this building adds. Only the Hut uses it in the original (+4, capped at 50 tribe-wide). Default 0. |
| `sprite_ref` | string | no | Reference to the original sprite source, e.g. `"pi0[01]"` (building/object atlas). In v0.1 this is a reference only — custom sprite loading is not yet defined (see §9). |
| `source` | object | no | `{ "record": 138, "notes": "..." }` — traceability note. |

### Resource names

Costs use the names `wood`, `stone`, `bones` (and `food` where a cost
ever uses it — construction in the original never charges food).
**Caveat (inferred, not proven):** the original construction costs are
paid from tribe stock `[2], [3], [4]`, and the four resources are food,
wood, stone, bones (stock `[0]` is food). Which of wood/stone/bones maps
to stock `[2]/[3]/[4]` is **not proven** — the format uses the order
wood = stock 2, stone = stock 3, bones = stock 4, and a loader must use
that same order consistently. If the order is later proven wrong, only
the loader's mapping changes, not the mod files. See `PD0-ANALYSIS.md` §3.

### Original building types (base_type)

| base_type | Name | Width × height | HP L1/L2/L3 | Build cost (wood/stone/bones) | Upgrade cost |
|---|---|---|---|---|---|
| 0 | Armoury | 3×2 | 40/55/70 | 10/5/0 | 20/10/0 |
| 1 | Gym | 5×4 | 70/100/90 | 15/15/0 | 40/30/0 |
| 2 | Hut | 2×2 | 25/40/90 | 5/10/0 | 15/5/0 |
| 3 | Chief's hut | 4×4 | 120/70/90 | 50/50/0 | 30/20/0 |
| 4 | Kitchen | 4×3 | 60/80/90 | 10/20/0 | 30/20/0 |
| 5 | Range | 6×4 | 70/100/90 | 15/15/0 | 40/30/0 |
| 6 | Store | 3×3 | 50/70/90 | 18/18/0 | 25/20/0 |
| 7 | Disco | 5×4 | 90/110/90 | 10/25/0 | 30/25/0 |
| 8 | Sanctuary | 3×3 | 50/60/90 | 10/0/10 | 0/20/10 |
| 9 | PIA centre | 4×4 | 60/80/90 | 10/15/0 | 30/15/0 |
| 10 | Nursery | 4×4 | 40/50/90 | 10/5/0 | 20/10/0 |
| 11 | Tower | 1×1 | 50/70/90 | 10/10/0 | 10/10/0 |

Source: `/a` record 138, rows 4–5 (size), 7–9 (HP), 13–15 (build cost),
10–12 (upgrade cost). All values verified in `PD0-ANALYSIS.md` §3.
Notes: Chief's hut HP falls from 120 (L1) to 70 (L2) and Gym from 100
(L2) to 90 (L3) — that is what the data says, not a parse error.
Mood bonuses per level (rows 21–23): Disco +2/+3/0, Hut 0/+2/0,
Kitchen 0/+2/0, Sanctuary 0/+1/0, Tower 0/+1/0, Armoury −1/0/+1,
all other buildings 0/0/0. Worker capacity (record 80):
`[3, 7, 3, 5, 5, 7, 5, 6, 3, 5, 3, 2]`.

### Traps

Traps are building types 20–22 in the original (net trap 10/0/0,
spring trap 10/5/0, pit trap 5/10/0 — upgrade-cost rows 10–12).
Traps are **not** in the v0.1 building schema: they are not placed like
buildings and are stored separately in code. They are listed here so
modders do not mistake them for buildings 12–19, which are
construction-site proxies (record 138, row 16), not real buildings.

## 7. Validation rules and limits (v0.1)

A loader must reject a mod if any of these fail, with a message naming
the file and field:

1. `format_version` is not `"0.1"`, or `game` is not
   `"prehistoric-tribes"`.
2. `mod.json` lists a file that does not exist, or a content file is not
   listed in `mod.json`.
3. Any JSON file does not parse.
4. Map: `width` or `height` outside 1–96; `tiles` is not exactly
   `height` rows of exactly `width` integers; any tile ID outside 0–242;
   any tile ID in 180–231 or 63–75/115–127 without the loader handling
   the original markers (see §5).
5. Map: any `spawns` entry with `type` outside 1–5, or position outside
   the map, or the tile at that position is not `174 + type`.
6. Map: `player_start` outside the map or on a blocked tile.
7. Map: `win_lose.flags` outside 0–7, or the booleans do not match the
   flags (`win_by_destroying_enemy_buildings == (flags & 1)`,
   `lose_if_key_building_destroyed == (flags & 2)`).
8. Building: `base_type` outside 0–11; `width`/`height` outside 1–6
   (the largest original building is 6×4); any `hp_by_level` value ≤ 0;
   any cost value < 0; `hp_by_level` is not exactly 3 numbers;
   `mood_bonus_by_level`, if present, is not exactly 3 numbers.
9. Building: `worker_capacity` < 0 if present; `living_space` < 0 if present.
10. Hard engine limits (from the original code, unchanged in v0.1):
    at most **50 villagers** per tribe, at most **30 buildings** per
    tribe, map at most **96×96**, at most **12 level values** (q=0–11).
    A mod cannot raise these limits in v0.1 — that needs code changes.
11. No file in the mod is a game asset (`.jar`, `.class`, or a file
    copied from the original JAR). The `.gitignore` in this repo already
    excludes them.

## 8. Mapping table — JSON field → original format

| JSON field | Original location |
|---|---|
| Map `width`, `height` | `/a` record 149, byte pair per level; q=0 forced 40×32 |
| Map `tiles` | `ma` file, RLE-decoded per `f.aN()`; control table `/a` record 197 (run lengths `[4,4,2,2,2,2]`, values `[3,0,43,6,3,0]`); byte < 250 = literal, 250+k = run |
| Map `spawns` | `ma` tiles 175–179; arguments `/a` record 110 `[20,20,20,15,25]` |
| Map `player_start` | `/a` record 150 (spawn cursor per level) |
| Map `win_lose.flags` | `/a` record 279, per level q=0–6: `[2,3,2,4,3,2,3]`; decided by `b.ak()` |
| Map `name` | Text file `s`, indices 82–91 (10 map names) |
| Building `base_type`, `width`, `height` | `/a` record 138, rows 4–5; type names from text `s` 0–11 |
| Building `hp_by_level` | `/a` record 138, rows 7–9; formula `rec138[(7+level−1)*26+type]` |
| Building `build_cost` | `/a` record 138, rows 13–15, paid from stock `[2],[3],[4]` |
| Building `upgrade_cost` | `/a` record 138, rows 10–12, paid progressively |
| Building `mood_bonus_by_level` | `/a` record 138, rows 21–23 |
| Building `worker_capacity` | `/a` record 80 (inferred as worker capacity) |
| Building `living_space` | Hut +4, capped at 50 (`f.java`, hut handling) |
| Building `description` | Text file `t`, indices 0–11 |

## 9. How a loader converts JSON back to the original binary (high level)

This is a design, not an implementation — no loader exists yet.

**Map → `ma` + `/a` records:**
1. Validate the map (§7).
2. Write the tile grid row-major into the RLE encoder: emit literal
   bytes for tiles < 250; use run codes 250+k for the six run pairs in
   record 197 (`[4,4,2,2,2,2]` tiles of `[3,0,43,6,3,0]`).
   Note: the original loader adds +0..2 jitter to base tiles ≤ 8 at
   load, so a re-encoded map will not be byte-identical to the original
   — it must be *play*-identical instead.
3. Append the encoded bytes as a new `ma` piece (or replace a piece),
   update the piece offset table, and write the map's width/height into
   record 149, its name index into the level→map table (record 248),
   and its win/lose flags into record 279.
4. Spawn tiles 175–179 in the grid are picked up by the original
   `f.aN()` code as before — the loader does not need to handle them
   separately.

**Building → `/a` record 138:**
1. Validate the building (§7).
2. For a variant: write its width/height, HP, costs, and mood values
   into a free slot or over the base type's columns, following the
   row layout in §6. A variant that *replaces* a base type writes over
   that type's columns; a variant that *adds* a building needs a free
   type slot — types 23–25 are unidentified in the original data, so
   adding a type is **open** in v0.1.
3. Write `worker_capacity` into record 80 and `living_space` into the
   hut handling, if the loader supports them.

**What a loader must not do:** change the game code, change the tick
rate (~20 ticks/second), or change the save format (`t0`/`t1`/`t2`
RecordStores) in v0.1.

## 10. Units + weapons — v0.2 sketch (NOT final)

These sections are field lists only, based on the decoded data cited.
Do not build against them yet — field meanings marked inferred may change.

### Units (villager) — fields known from the decoded data

Based on `PETA-SISTEM.md` §Villagers and `DECODE-REMAINING.md` §3
(task codes 0–111) and `PD0-ANALYSIS.md` §4:

- `id`, `name` (villager names: ~122 random names in text `s` 106–227)
- `role`: one of villager, warrior, chief, shaman, cook, armourer, DJ,
  scout, guard, child. Default at birth is role 9 (unemployed).
  Job tasks are `44 + role` (roles 0–6, proven).
- `age`: adulthood at 12; HP change per tick and max HP by age come
  from `/a` records 97 and 98 (heal +3/tick at ages 0–12, +2 at 13–19,
  +1 at 20–29, 0 at 30–39, then −1 and worse from age 40; max HP 99
  until 49, declining to 0 at age 100 = death).
- `gender`: 0 male / 1 female.
- `hp`, `max_hp` (by age, record 98).
- `skills`: 2 combat skills (melee, throwing) + 7 civilian skills.
  Damage: melee `(meleeSkill/3 + rec102[role]) × (rand(11−defense)+defense)/10`,
  throwing adds `rec124[throwSkill]` (rec 102 = `[1,1,2,3,5,3,0,0,0,0]`,
  rec 124 = `[1,1,1,2,2,3,3,4,6,8]`).
- `needs`: happiness, hunger, tiredness (0–99 each).
- `task`: task code 0–111 (full table in `task-table.csv`); 20 codes
  are still UNKNOWN.
- Limits: at most 50 villagers per tribe.

**Open for v0.2:** exact role list numbering (rec 102 roles 0–9 are
unnamed), how a new role gets its job task, skill meanings for the
7 civilian skills, and the gathering/production side of the task
economy (which tasks add to stock — not fully traced).

### Weapons — fields known from the decoded data

Based on `PETA-SISTEM.md` and `PD0-ANALYSIS.md` §6:

- `id`, `name`: the six named weapons in text `s` 12–17 are club,
  stone, spear, stone axe, bone mace, tomahawk. Traps (net, spring,
  pit) are separate types 20–22.
- `damage_bonus_by_role`: `/a` record 102, 10 values.
- `throw_damage_by_skill`: `/a` record 124, 10 values.
- `projectile_gravity`: `/a` record 159, 3 values `[25, 30, 40]`
  (one per throwing-weapon class; weapon names for these 3 classes
  are unknown).
- `weapon_by_task`: `/a` record 79, 10 values `[1,1,5,2,2,1,1,5,2,2]`.
- Produced in the Armoury, stored in the Store.

**Open for v0.2:** which of the six named weapons maps to which
projectile class, the exact melee damage per weapon (vs per role),
and how a new weapon is registered (weapon stocks are tribe stock
indices `[7],[8],[9],[10]` — inferred, not proven).

## 11. What is still open

1. Spawn types 1–5: what each type places (resource node, fishing
   spot, etc.). Needs the `b.java` consumers of the 50-slot object list.
2. Custom sprite loading: how a mod PNG replaces a `pi0`/`pi8`/`pi9`
   image, and which sprite index each building/unit uses.
3. Adding a genuinely new building type (beyond 0–11) or weapon:
   needs a free type slot and code-path work; types 23–25 are
   unidentified.
4. The resource-name order (wood/stone/bones vs stock `[2]/[3]/[4]`)
   — inferred, needs the HUD icon trace (`f.java` resource icons 627–629).
5. The q=5 win anomaly (winning q=5 does not advance in `aq()`), and
   the exact role of q=7 ("the end").
6. The 21 scripted mission events (records 286/287/296/297/298) —
   per-mission win conditions for missions 0, 2, 3, 5 live there.
7. Tile visual meanings: which tile ID is grass, water, forest, rock.
   Needs rendering the tileset and matching IDs to pictures.
8. A loader implementation (J2ME repacker and/or Android loader)
   does not exist yet. This spec is format-only.
