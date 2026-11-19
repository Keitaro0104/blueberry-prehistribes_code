# Decode the remaining files — Prehistoric Tribes (J2ME, THQ 2008)

Work directory: `~/workspace/j2me-prehistoric-tribes/`
Sources: `extracted/` (JAR contents, untouched), `decompiled-cfr/{e,f,b,c}.java`,
bytecode cross-checked with the `jawa` Python package against `extracted/*.class`.
All findings are in English. Nothing was pushed to GitHub; `extracted/` and
`decompiled-cfr/` were not modified.

New files produced by this task:

- `extract_pngs.py` — splits the concatenated-PNG packs (see §1).
- `sprites/pi0/`, `sprites/pi8/`, `sprites/pi9/` — the split PNGs + `index.csv` per pack.
- `task-table.csv` — all 112 villager task codes with their per-task table values (see §3).

---

## 1. Sprite sheets — `pi0`, `pi8`, `pi9`

### Format (proven from code)

`e.java d()` reads a pack into a fixed buffer, then loops: read 2-byte
**big-endian** length, then that many bytes = one PNG; a `0xFF` byte ends the
stream (`e.java`, `f.java c(byte)` at f.java:2577). `extract_pngs.py`
implements exactly this and writes the PNGs to `sprites/<pack>/NN.png`
plus an `index.csv` (index, width, height, bytes, SHA-256).

### Counts and sizes

| Pack | File size | PNGs | Consumed | Trailing bytes |
|---|---|---|---|---|
| `pi0` | 62,502 | **27** | 62,493 | 9 (8× `0x00` + `0xFF`) |
| `pi8` | 129,809 | **12** | 129,808 | 1 (`0xFF`) |
| `pi9` | 8,597 | **6** | 8,596 | 1 (`0xFF`) |

All PNGs are 8-bit palette, except `pi0[25]` (RGBA).

**`pi0` (27 images):** 00 128×136, 01 100×113, 02 121×151, 03 114×62,
04 61×69, 05 76×111, 06 50×87, 07 52×132, 08 66×48, 09 105×35, 10 34×125,
11 94×28, 12 102×71, 13 28×108, 14 40×100, 15 40×46, 16 77×72, 17 176×30,
18 190×59, 19 35×76, 20 57×26, 21 37×54, 22 50×38, 23 84×26, 24 38×38,
25 181×39 (RGBA), 26 70×24.

**`pi8` (12 images):** 00–09 all 240×130, 10 200×211, 11 226×165.

**`pi9` (6 images):** 00 76×111, 01 105×35, 02 105×35, 03 105×35,
04 40×100, 05 40×46. Same dimensions as some `pi0` images but different
SHA-256 hashes — not byte-identical duplicates.

### What each sheet likely contains (sizes + visual check + loading)

- `pi0[00]` (128×136) — UI/icon atlas: faces, emoticons, resource icons,
  tools, bars.
- `pi0[01]` (100×113) — building/object atlas: huts, tents, trees, rocks, weapons.
- `pi0[02]` (121×151) — villager portrait grid (faces).
- `pi0[05]` (76×111) and `pi9[00]` (76×111) — dense repeating pattern,
  likely terrain/texture; same size, different content.
- `pi0[07]` (52×132) — trees/plants atlas.
- `pi0[18]` (190×59) — "PREHISTORIC TRIBES" stone logo.
- `pi0[25]` (181×39, RGBA) — bitmap digit strip `0123456789. % / p`
  (HUD number font).
- `pi8[00]` (240×130) — story scene: mammoth, waterfall, saber-tooth tiger.
- `pi8[10]` (200×211) — warrior standing on a defeated enemy.
- `pi8[11]` (226×165) — cooking over a fire.

### How they are loaded

- `e.java` array `{"/pi0", "/pi9", "/pi8"}`; `e.d()` loads `pi0` → `f.a[0][]`
  and `pi9` → `f.a[1][]` at startup. Only the first 27 images are actually
  created (`if (by2 < 27)`); `e.d()` reads into a fixed 62,502-byte buffer —
  exactly the size of `pi0`.
- `pi8` is loaded **lazily** by `f.java c(byte)` (f.java:2577) into
  `f.a[2][0]`, at most 12 images, stopping at `0xFF`; only the requested
  index is kept and drawn at f.java:2161. So `pi8` = story/cutscene art
  shown on demand, while `pi0`/`pi9` = in-game art loaded up front.

---

## 2. Font data file `a` (18,842 bytes) — fully decodable, with two corrections

### Correction 1: the 312-entry array holds cumulative *starts*, not lengths

`e.java f()`:

- `f.a:[B = new byte[17638]` — the blob (all record data concatenated).
- `f.a:[S = new short[312]` — **cumulative start offsets**:
  `a[n+1] = a[n] + length`, with `a[0] = 0`. Final cumulative offset 16,951;
  last record 687 bytes (16,951 + 687 = 17,638). Record lengths are read as
  **little-endian** 2-byte values interleaved with the data
  (`n = (b2 << 8) + b1`).
- `f.b:[S = new short[570]` — the offset table, in 5 groups (see below).
- `f.c:[S = new short[5]` — cumulative group bases `[0, 122, 243, 249, 273]`.

Parse verified: 312 records end exactly at offset 18,262; the 5 groups of
big-endian shorts (580 bytes) end exactly at 18,842 = file size. Record
lengths: mostly 112 bytes for records 26–52 (the task tables), 2 zero-length
entries, max 687 (record 311).

### Correction 2: file `a` is not only a font file — it is the game's data file

- **Records 0–279 = game data tables.** Records 26–52 are the per-task
  tables (112 bytes each, except 42 = 17 bytes and 44 = 14 bytes); record 53
  is a 625-byte 25×25 distance/direction table; records 279–302 are the
  per-mission tables (win/lose flags, scripted events, timers — see §4).
- **Records 280–311 = font tables.** `c.java` renders text as:
  glyph code = `blob[starts[280] + byte]`; glyph row = code/30, col = code%30;
  glyph width =
  `blob[starts[281+s] + row*21 + col + 1] - blob[starts[281+s] + row*21 + col]`
  (`s` = font size/style); drawn from `pi0[25+s]` (the digit strip and its
  siblings). Record lengths 280–311: `[128, 63, 63, 6, 6, 6, 21, 21, 8, 84,
  8, 12, 21, 21, 6, 23, 23, 23, 23, 9, 9, 9, 6, 8, 16, 20, 3, 2, 1, 76,
  142, 687]`.

### The 570-entry offset table (`f.b:[S`, groups 0–4)

- **Group 0 (122 entries):** entity-field offsets, `group0[i] = i*101`.
  The villager/entity array is `byte[9983]`; field *i* of villager *v* lives
  at `entity[i*101 + v]`. This explains every magic number in the code:
  2828 = group0[28] = task/status field, 404 = group0[4] = progress counter,
  3131/3232 = target x/y, 6464 = animation/state, 3838 = current pose,
  1111 = skill/level, 2929 = type/role, 3535, 4444, 6161, 7979, etc.
- **Group 1 (121 entries, 11×11):** first row `0, 22, 44, …, 220` (step 22);
  exact use unproven — likely a precomputed distance/offset table.
- **Group 2 (6):** `[50, 50, 2000, 750, 350, 50]`.
- **Group 3 (24):** mostly 200–300, then eight × 10000.
- **Group 4 (12):** `[5000, 0, 4000, 12000, 6000, 4000, 0, 6000, 6000,
  6000, 6000, 6000]`.

**Verdict: yes, fully decodable** — the parse above reproduces the file
byte-for-byte, and the record/offset tables are all exercised by the code.

### Bonus: `pd0` (96,990 bytes) also fully decoded

`pd0` is a *different* file (the balance tables). Its 36 table lengths are
hardcoded as a `short[36]` literal in `e`'s constructor:
short tables (11): `[119, 1291, 162, 162, 2782, 144, 1069, 6903, 823, 1721,
5492]`; byte tables (25): `[119, 1291, 1291, 1291, 162, 162, 162, 2782,
2782, 144, 1069, 1069, 6903, 6903, 6903, 823, 1721, 42, 5492, 5492, 1810,
1810, 1810, 1810, 1810]`. Layout: 1 header byte (`11`) + 11 short tables
(20,668 shorts = 41,336 bytes, big-endian `readShort`) + 25 byte tables
(55,653 bytes) = 96,990 exactly. Note: the win/lose flags are **not** in
`pd0` — they are file-`a` record 279 (§4).

---

## 3. Villager task codes (status field `entity[2828+v]`, values 0–111)

### How tasks work (proven)

- Setter: `b.java a(int n, byte by)` (b.java:841). Only changes the field if
  different; resets `entity[404+n] = 0` (progress counter); masks
  `entity[1111+n] &= 0x0F`; recomputes the duration `B` from record 38
  (see below); if the new task is 83–85, calls `C()`; sets
  `entity[3838+n]` (current pose) from record 32.
- Duration (record 38): `B = blob[starts[38] + task]` (signed byte).
  Mostly `1`; `0` for tasks 51–91, 98, 100–104, 109, 111 (untimed/state
  tasks that last until changed externally); `-18` for tasks 5–9 and 92/93/106
  (duration read from entity field `offsets[18] = 1818`); `10` for task 105,
  `3` for 107, `2` for 95/96.
- Movement class (record 39): `0` = move to target (47 tasks), `1` =
  stationary (38 tasks, mostly 51–104), `2` = other (27 tasks: 26–43, 59,
  87, 94–97, 99, 109, 110). `R()` returns early when record 39 is `1` or
  the task is ≤ 9 (b.java:444–452).
- Flags (record 27), tested as bitmasks in `b.java`: bit 1 (41 tasks),
  bit 2 (12), bit 4 (4), bit 8 (11), bit 16 (85), bit 32 (38), bit 64 (37),
  bit 128 (4). Individual bit meanings are **not** named in the code; the
  call sites are: `&1` b.java:939, `&2` b.java:883, `&4` b.java:1107
  (only when task > 9), `&8` b.java:2706, `&0x10` b.java:2771, `&0x20`
  b.java:2755, `&0x40` b.java:3182, `&0x80` b.java:2151.
- Category (record 41): 17 categories (0–16). Distribution: cat 0 = 49
  tasks, cat 8 = 14, cat 12 = 11, cat 11 = 6, cat 16 = 5, cat 14 = 4,
  cats 9/13 = 3 each, cats 1–7 = 2 each, cats 10/15 = 1 each. Code checks:
  `== 0`, `!= 3`, `!= 7`, `13–15`, `== 16` (b.java:784–785, 835, 1024,
  1107, 1273). Record 42 maps category → a small value
  `[0,0,0,0,0,0,0,0,0,1,5,4,2,0,0,0,0]` (only categories 9–12 non-zero),
  used in combat/formation checks (b.java:1677, 1848, 1856, 2155, 4256, 4400).
- Priority (record 43, 0–9): higher wins when two villagers target the same
  thing (b.java:737).
- Completion effect (records 45/46/47 + 64): when a task finishes, `K()`
  calls `a(rec45, rec46, rec47, rec64[rec45])` (b.java:2782), which loops
  `rec64[rec45]` times calling `d(rec45, rec46+i, rec47)`; `d()` ORs bits
  into the per-tribe bitfield `f.a[tribe][word][rec46+i]`
  (`f.a = new int[2][3][96]`). Effect types: 1 (tasks 0–4), 2 (5–9),
  7 (10–16, amount/index 15), 5 (19–43, 50/25/20), 6 (60 and 84–86),
  11 (95–98, 20–40); type 0 = no effect (most tasks ≥ 44). `rec64` =
  `[-1, 1, 1, 1, 10, 1, …]` — type 4 repeats 10 times, type 0 never runs.
  The exact meaning of each bit is **unproven** from code alone.
- Threshold (record 49): task completes when `entity[404+v] >= rec49[task]`
  (b.java:2604, 2611). Values include sentinels 99/100/127.
- Period (record 50, %) and chance (record 52, %): `rec50[task] == 127` or
  `rec52[task] == 127` = special (disabled/always); otherwise `rec50` drives
  a periodic trigger (`this.a.c % (rec50 * (u*4+1)) <= 3`, b.java:4001) and
  `rec52` is used as a percentage (b.java:4012).
- Mood delta (record 51, −3…+6): added to `w` at b.java:4064.
- Other per-task records: 26 (field indirection, values {19,42,85,106,119}
  → offsets), 28 (target-field indirection, values {0,43,83,99}),
  29 (animation/state id shown — tasks 19–26 forced to 69, b.java:789),
  30 (amount/threshold, sentinels 99/100/127), 31 (field indirection,
  values {4,5,13,19,20,21,36,65,85} → offsets), 32 ({0,44} — pose source),
  33 ({13,4,−4…−1} — value-or-field), 34 ({0,1,3,5,−36} — value-or-field,
  negative = entity field), 35 (field indirection {15,36,41,69,70,71,73,74}),
  36 (delta {−3,0,1,2,3,5,10}), 37 (required skill level {2…16}, tested
  against `(entity[1111+v] & 0xFF) >> 4`, b.java:1598), 40 (−1 = don't touch,
  else 1–7 written to field 3535, b.java:2013–2016), 44 (14 bytes, indexed by
  a 0–13 type: `[10,17,16,18,67,37,49,69,70,71,72,73,74,75]` → entity field,
  b.java:2925–2938), 48 ({0,2} flag, bit 2 tested b.java:2562, 2625).
- Distance/direction table (record 53, 625 bytes = 25×25): value =
  `10 × Chebyshev-distance + direction`, direction 0=E, 1=SE, 2=S, 3=SW,
  4=W, 5=NW, 6=N, 7=NE; center (0,0) = 0; cells outside the valid region
  hold sentinel `100` (treated as "too far", cf. `> 29` check b.java:720).
  Slight asymmetry at the extreme rows (dy=−12 valid for dx −5…+3, dy=+12
  for dx −4…+4) is an observed quirk of the table data.

### Task table

Full per-task data (all records above, one row per code 0–111) is in
**`task-table.csv`** (columns: task, label, evidence, flags27, anim29,
val30, field31, link32, val33, val34, field35, delta36, req37, dur38,
move39, dir40, cat41, catval42, prio43, eff45, eff46, eff47, flag48,
thresh49, period50, mood51, chance52).

Labels below are **PROVEN** where an assignment/comparison site pins the
meaning, **INFERRED** where only the table values + family ranges support
it, and **UNKNOWN** otherwise. Codes with no entry have no direct evidence.

| Code(s) | Meaning | Evidence |
|---|---|---|
| 0–4 | go-to + interact (effect bit 1) | INFERRED |
| 5–9 | go-to + interact (effect bit 2); duration from entity field 1818 | INFERRED |
| 10–16 | resource gathering (effect bit 7) | INFERRED; 12 assigned b.java:1290, 2710 |
| 17 | newborn / child | PROVEN (f.java:5287) |
| 19–26 | work (display animation 69) | INFERRED (b.java:789) |
| 28–49 | spell/skill family (range check b.java:2551) | INFERRED |
| 44–50 | job tasks, `44 + role` (role 0–6) | PROVEN (f.java:3620, 4224, 4233) |
| 50 | job task (role 6) | PROVEN (b.java:3255) |
| 51, 58 | building-linked | INFERRED |
| 55 | assigned b.java:1671 | PROVEN-assigned |
| 57 | building worker (restored on release, f.java:3237) | PROVEN |
| 59 | building work | PROVEN (b.java:2368, 3907, 3977) |
| 60 | assigned b.java:1292, 2714 | PROVEN-assigned |
| 69 | idle / return home | PROVEN (many assignments) |
| 73 | assigned b.java:2717 | PROVEN-assigned |
| 77–85 | combat / formation | 79 PROVEN (b.java:3313), 80 PROVEN (b.java:1854), 83 PROVEN (b.java:3079), 85 PROVEN (b.java:1636, 1852); 78/84 INFERRED |
| 87 | dismiss / flee / unassign | PROVEN (many assignments) |
| 92, 93, 106 | wild animal attacker | PROVEN (checked together, e.g. f.java:4121, 5699) |
| 94 | fetch (`K()` case 94: `a(4444+v, 10)`) | PROVEN (b.java:2784) |
| 95 | clear building flag | PROVEN (b.java:2784) |
| 96 | set mood 99 / disease spread | PROVEN (b.java:2784) |
| 97 | disease-spot list shift | PROVEN (b.java:2784) |
| 99 | assigned b.java:4274 | PROVEN-assigned |
| 105 | held / selected by player (restored to 69 or 57 on release) | PROVEN (f.java:2985, 3131, 3236) |
| 107 | child | PROVEN (b.java:2697) |
| 109 | go to hut / mate step | PROVEN (b.java:3124) |
| 110 | countdown task (`110 − entity[1515+v]`) | PROVEN (b.java:3399, 3420) |
| 111 | mating | PROVEN (b.java:3454–3455) |
| 18, 27, 53, 54, 56, 61–68, 70–72, 74–76, 86, 88–91, 98, 100–104, 108 | no direct evidence | UNKNOWN |

Family ranges used by the code (range checks, not per-code proof):
`<= 9` movement/idle, `10–16` gathering, `19–26` work, `28–49` spell/skill,
`44–50` jobs, `69/79/80/83–85` combat/formation, `109–111` mating.

---

## 4. Win / lose — exact conditions as proven from code

### Correction: `b.java k()` does NOT decide win/lose

`b.k()` (b.java:5002) is short: if `a.v == 1 && K < 50` → `a.h = 2`; else if
`(a.N || a.L || O completed) && a.v == 1` → `a.h = 1`; else `a.h = 0`. Its
only call site is `f.java aQ()` (f.java:6565, music selection:
track = `b[h*2 + random]`). So `h` is a phase/mood value for music, not the
verdict. `K` in `b` starts at 50 (`b.a()`, b.java:243), increments toward 50
each world tick (`b.e()`, b.java:1122), and resets to 0 when a villager is
in a `<= 9` task (b.java:1201).

### The real endgame: `b.ak()` (b.java:4888) arms a byte timer `f.u`

(`f.u` here is a `byte` timer — distinct from the many boolean `u` fields;
CFR reuses the name.)

```java
// WIN
if (a[1][14] <= 0 && (blob[starts[279] + q] & 1) != 0) {
    if (f.u == 0) f.u = 1;
}
// LOSE
else if ((a[0][11] <= 0
          || (a[8506] <= 0 && (blob[starts[279] + q] & 2) != 0))
         && f.u == 0) {
    f.u = 50;
}
```

- `a[u][11]` = tribe population (incremented on spawn/capture, decremented
  on death in `b.m()`); `[12]` = male, `[13]` = female, `[14]` = building
  count (`f.java`:5580 `++` on build, 5648 `--` on demolish), `[16]` = living
  space.
- `a[8506]` = `f.e[8506]` = HP of player building slot 1 (player slots 1–30,
  enemy 31–60, `f.java a(byte,…)` at f.java:5475). Which building type slot 1
  is depends on level-load order — **not proven** from code.
- The flag table is file-`a` **record 279** (not `pd0`): per-mission flags
  for `q = 0…6` are `[2, 3, 2, 4, 3, 2, 3]` (record length 12; entries 7–11
  unused by this check).

### Per-mission win/lose flags (record 279)

| Mission `q` | Flag | Bit 1 (&1): win by destroying all enemy buildings | Bit 2 (&2): lose if building slot 1 destroyed |
|---|---|---|---|
| 0 | 2 | no | yes |
| 1 | 3 | **yes** | yes |
| 2 | 2 | no | yes |
| 3 | 4 | no | no (bit 4 set — see note) |
| 4 | 3 | **yes** | yes |
| 5 | 2 | no | yes |
| 6 | 3 | **yes** | yes |

So: **losing by having your whole tribe wiped out (`a[0][11] <= 0`) applies
in every mission**; losing by building slot 1 applies in all missions except
3; winning by destroying all enemy buildings applies only in missions 1, 4,
6. Bit 4 (value 4, mission 3 only) is **never tested in `ak()`** — only `&1`
and `&2` are checked anywhere for record 279 — so its meaning is unproven;
mission 3's win condition must come from its scripted events instead
(see below).

### The countdown: `f.j()` (f.java:658, 684–685), called every tick from `f.h()`

```java
if (u > 0 && v == 1) {
    u++;
    if (u == 41 || u == 90) {
        v = 0; Q = 24; H = true;
        v = 56 + 41 / u;   // 57 at u==41 (win), 56 at u==90 (lose)
    }
}
```

- Armed at `u = 1` (win) → verdict at `u == 41`, ~40 ticks ≈ 2 s later.
- Armed at `u = 50` (lose) → verdict at `u == 90`, ~40 ticks later.
- Texts (`0/t`): `t[56]` = "you have lost!", `t[57]` = "hurrah! you've won!".

### After the verdict: `f.aq()` (f.java:4673)

- `u == 41` (win): `aM()` (reset world state); if `q < 5` → `q++`, `Q = 23`,
  save progress (`e(0)`); if `q == 6` → campaign finished (`q = 7`,
  `Q = 18`).
- `u == 90` (lose): if `q == 1 || q == 6` → `q--`; then `Q = 16`, `v = 58`
  (lose screen). Other missions retry the same `q`.

### Mission-scripted events (separate from `ak()`)

- Record 288 (cumulative event offsets `[0, 3, 8, 11, 17, 18, 19, 21]`) and
  record 291 (per-mission event counts `[3, 5, 3, 6, 1, 1, 2]`) define 21
  scripted events: q0 = 3, q1 = 5, q2 = 3, q3 = 6, q4 = 1, q5 = 1, q6 = 2.
  Record 286 = event text/trigger ids, 287 = event types
  (`[1,3,4,0,0,0,1,5,1,5,6,7,7,7,7,10,8,1,5,0,1]`), 296 = event-type switch
  values, 297 = event params, 298 = event timers (`J = 120 − rec298[g]`).
  Fired from `b.v()`/`b.u()` (b.java:4752–4888) — e.g. `q == 3` chief-alive
  checks, `q == 2`/`q == 4` timers.
- Record 299 (time thresholds `[40, 50, 60, 60, 50, 65, 80, 95, 110]`, ×100
  ticks), 301 (text ids `[64, 63, 65, 65, 68, 66, 69, 64, 67]`), 302
  (per-mission progress base `[0, 0, 0, 4, 4, 9]`) drive the in-mission
  progress level `L` (b.java:4692–4697).

### Special cases in `ak()` (b.java:4896–4906)

When enemy buildings `<= 4` **and** enemy population `<= 0`:

- `q == 5`: if `u == 0` → `u = 1` (start the win countdown) and return;
  if `u == 20` → `u = 0` and `b.c()` (b.java:1031: clears bit `0x40` from
  field 7979 for villagers 1–50 and re-issues orders to idle villagers).
  So while the near-wipe holds, the countdown is reset at `u == 20` and
  never reaches 41 — mission 5's win therefore comes from its scripted
  event, not from `ak()`. (This is what the code says; it is a puzzle, not
  a typo — reported as observed.)
- `q == 2`: if event index `f < 2` → `f = 2` (skip to scripted event 2).

### What is NOT proven

- Per-mission win conditions beyond the record-279 bits (missions 0, 2, 3,
  5 have no destroy-to-win bit) — those live in the scripted-event code
  (`b.v()`/`b.u()`), which was not fully decoded here.
- Which building type occupies player slot 1 (`a[8506]`).
- The meaning of record-279 bit 4 (mission 3).

---

## What remains (not done in this task)

- Decoding the `pd0` balance tables into named values (costs / HP / damage /
  per-mission `pd0` values). `pd0`'s layout is now fully decoded (§2 bonus),
  so this is mechanical table-reading + matching table indices to code sites.
- Fully decoding the 21 mission-scripted events (records 286/287/296/297/298
  + `b.v()`/`b.u()`), which carry the per-mission win conditions for
  missions 0, 2, 3, 5.
- Naming the individual record-27 flag bits and record-41 categories — needs
  more call-site reading; the raw values are all in `task-table.csv`.
