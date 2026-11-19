# Prehistoric Tribes (THQ, 2008, J2ME) — Data-file analysis: `pd0` and `/a`

**Game:** Prehistoric Tribes (THQ Wireless / Gear Games, 2008), MIDP-2.0, 240×320.
**Source files analysed:** `extracted/pd0` (96,990 bytes), `extracted/a` (18,842 bytes) from
`prehistoric_tribes_240x320-84398_4_at1w.jar`, cross-referenced against the CFR 0.152 decompile
(`decompiled-cfr-renamed/{b,e,f}.java`, re-decompiled with `--renamedupmembers true`).
**Parser:** `decode_pd0.py` (in this folder). **Full numeric dump:** `pd0-tables.txt` (407 KB).
**Status labels used below:** ✅ PROVEN (code reads the value and the data matches the use),
🔶 INFERRED (strong pattern / single code use, not fully pinned down), ❓ UNKNOWN (no code use found).

## 0. The big correction: the balance data is NOT in `pd0`

An earlier pass assumed the balance tables lived in `pd0`. That is wrong. `pd0` holds
**graphics / animation / sprite data** (see §1). Almost all **game balance** (building costs, HP,
waves, AI, tasks) lives in the `/a` file (see §2). Record indices cited in this report (138, 97,
206, 221, …) are **`/a` record indices**, not `pd0` table indices.

## 1. `pd0` — layout (✅ PROVEN from `e.java` method `b()`)

One discarded header byte `0x0B` (= 11, the number of short tables), then 11 big-endian short
tables, then 25 byte tables. Lengths come from a hardcoded sizes array (a field of `e`):
`{119,1291,162,162,2782,144,1069,6903,823,1721,5492, 119,1291,1291,1291,162,162,162,2782,2782,144,1069,1069,6903,6903,6903,823,1721,42,5492,5492,1810,1810,1810,1810,1810}`.
Short tables = 20,668 shorts (41,336 bytes); byte tables = 55,653 bytes; total 96,990 bytes — parse
asserts pass exactly.

| Idx | Type | Len | First values | Role (from code use) |
|-----|------|-----|--------------|----------------------|
| b0 | short | 119 | 0,1,2,2,3,3,3,5… (→1272) | ✅ Sprite-group start offsets; `b0[type+1]` = start, `j0[type]` = count (`f.java:928,2038`) |
| b1 | short | 1291 | 0,1,2,3,4,5,6,7… | ✅ Packed tile/sprite entries; `b1[N] & 0xFFF` = image/tile id, bits 12–15 = flags |
| b2 | short | 162 | 0,1,2,3,4,6,7,8… | 🔶 Animation-sequence data (`f.java:1166–1168`) |
| b3 | short | 162 | 0,2,4,5,6,8,9,10… | 🔶 Animation-sequence data (`f.java:1166–1168`) |
| b4 | short | 2782 | 0,1,2,3,4,5,6,7… | 🔶 Animation-sequence data (`f.java:1460–1463`) |
| b5 | short | 144 | 0,1,2,3,4,5,6,7… | 🔶 Particle/effect sprites (`f.java:1539–1540`) |
| b6 | short | 1069 | 0,1,2,3,4,5,6,7… | 🔶 Particle/effect sprites (`f.java:1539–1540`) |
| b7 | short | 6903 | 0,1,2,3,4,5,6,7… | ✅ Large sprite/frame table (`f.java:1215–1252`) |
| b8 | short | 823 | 0,1,2,3,4,5,6,7… | 🔶 Animation-sequence data |
| b9 | short | 1721 | 0,1,2,3,4,5,6,7… | ✅ Start indices + counts (`f.java:1544,1623`) |
| b10 | short | 5492 | 0,1,2,3,4,5,6,7… | ✅ Packed entries with bitfields (`f.java:1550–1552,1624–1625`) |
| j0 | byte | 119 | 1,1,0,1,0,0,1,0… | ✅ Sprite-group counts (with b0) |
| j1 | byte | 1291 | 0,0,0,0,0,0,0,0… | ✅ X pixel offsets for b1 entries |
| j2 | byte | 1291 | 0,0,0,0,0,0,0,0… | ✅ Y pixel offsets for b1 entries |
| j3 | byte | 1291 | 0,0,0,0,0,0,0,0… | ✅ Type flags for b1 entries (`j3>>6`) |
| j4 | byte | 162 | 0,0,0,0,0,0,0,0… | 🔶 Animation data (with b2/b3) |
| j5 | byte | 162 | 0,0,0,0,0,0,0,0… | 🔶 Animation data |
| j6 | byte | 162 | 0,0,0,0,0,0,0,0… | 🔶 Animation data |
| j7 | byte | 2782 | 0,0,0,0,0,0,0,0… | 🔶 Animation data (with b4) |
| j8 | byte | 2782 | 0,0,0,0,0,0,0,0… | 🔶 Animation data (with b4) |
| j9 | byte | 144 | 0,0,0,0,0,0,0,0… | 🔶 Particle data (with b5) |
| j10 | byte | 1069 | 0,0,0,0,0,0,0,0… | 🔶 Particle data (with b6) |
| j11 | byte | 1069 | 0,0,0,0,0,0,0,0… | 🔶 Particle data (with b6) |
| j12 | byte | 6903 | 0,0,0,0,0,0,0,0… | ✅ Frame data (with b7) |
| j13 | byte | 6903 | 0,0,0,0,0,0,0,0… | ✅ Frame data (with b7) |
| j14 | byte | 6903 | 0,0,0,0,0,0,0,0… | ✅ Frame data (with b7) |
| j15 | byte | 823 | 0,0,0,0,0,0,0,0… | 🔶 Animation data (with b8) |
| j16 | byte | 1721 | 1,1,1,1,1,1,1,1… | ✅ Counts (with b9) |
| j17 | byte | 42 | 0,0,0,0,0,0,0,0… | ❓ Rarely used |
| j18 | byte | 5492 | 0,0,0,0,0,0,0,0… | ✅ Packed data (with b10) |
| j19 | byte | 5492 | 0,0,0,0,0,0,0,0… | ✅ Packed data (with b10) |
| j20 | byte | 1810 | 0,0,0,0,0,0,0,0… | ❓ Font/glyph data (unproven) |
| j21 | byte | 1810 | 0,0,0,0,0,0,0,0… | ❓ Font/glyph data (unproven) |
| j22 | byte | 1810 | 0,0,0,0,0,0,0,0… | ❓ Font/glyph data (unproven) |
| j23 | byte | 1810 | 4,4,4,4,4,4,4,4… | ✅ ×4 widths, used in minimap/text rendering (`f.java:2104,2152`) |
| j24 | byte | 1810 | 4,4,4,4,4,4,4,4… | ✅ ×4 heights, used in minimap/text rendering (`f.java:2104,2152`) |

**Bottom line for `pd0`:** no balance numbers. All tables are sequential/small-value graphics data;
the interesting structure is the pairing (short table + 1–3 byte tables of the same length).

## 2. `/a` — layout (✅ PROVEN from `e.java` method `f()`)

18,842 bytes, **interleaved**: 312 × `[LE u16 record length][that many blob bytes]` (blob total
17,638 bytes), then 5 × `[LE u16 group length][that many BE u16 values]` (group lengths
[122, 121, 6, 24, 12], 285 values total). `f.var_short_arr_a` = 312 cumulative record offsets;
`f.var_byte_arr_a` = the 17,638-byte blob. `b.var_short_arr_a = f.var_short_arr_a`,
`b.var_byte_arr_b = f.var_byte_arr_a` (`b.java:227–228`). All accesses are
`byte_arr_b[short_a[REC] + offset]`. Full per-record dump: `pd0-tables.txt`; compact inventory:
Appendix A of this file.

The 5 trailing groups (`var_short_arr_b`, cumulative offsets `c[] = [0,122,243,249,273]`) are
fixed-point math tables — see §9.

## 3. The building table — `/a` record 138 (✅ PROVEN, 624 bytes = 24 rows × 26 columns)

**Columns = object types 0–25.** Types 0–11 are the 12 buildings; 20–22 are the 3 traps;
12–19 are construction-site proxies (see row 16); 23–25 are unidentified.

| Type | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
|------|---|---|---|---|---|---|---|---|---|---|----|----|
| Name | Armoury | Gym | Hut | Chief's hut | Kitchen | Range | Store | Disco | Sanctuary | PIA centre | Nursery | Tower |

| Row (offset) | Meaning | Status | Values (types 0–25) |
|---|---|---|---|
| 0 (+0) | ? | ❓ no code use found | `1,2,4,2,5,2,0,5,2,2,5,2, 0,0,0,0,0,0,0,0, 1,1,1, 0,0,0` |
| 1 (+26) | ? | ❓ no code use found | `1,4,4,0,7,4,0,7,2,3,0,2, 0,0,0,0,0,0,0,0, 0,0,0, 0,0,0` |
| 2 (+52) | ? | ❓ no code use found | `1,0,0,0,0,0,0,0,0,0,0,0, 4,4,4,3,2,2,1,1, 0,0,0, 0,0,0` |
| 3 (+78) | ? (values 1–26 sequential) | ❓ no code use found | `1,2,3,…,26` |
| 4 (+104) | **Width (tiles)** | ✅ `f.java:5466` | `3,5,2,4,4,6,3,5,3,4,4,1, 4,5,6,4,3,3,2,1, 1,1,1, 1,3,2` |
| 5 (+130) | **Height (tiles)** | ✅ `f.java:5467` | `2,4,2,4,3,4,3,4,3,4,4,1, 4,4,4,3,3,2,2,1, 1,1,1, 1,2,2` |
| 6 (+156) | Worker-assignment flag (0 or −1) | 🔶 used `b.java:1411,1812,2151`; exact rule unresolved | `0,−1,−1,−1,0,−1,−1,0,0,−1,−1,−1, 0,0,0,0,0,0,0,0, −1,−1,−1, −1,0,0` |
| 7 (+182) | **Max HP, level 1** | ✅ `f.java:4138` | `40,70,25,120,60,70,50,90,50,60,40,50, 5,5,5,5,5,5,5,5, 5,5,5, 20,20,0` |
| 8 (+208) | **Max HP, level 2** | ✅ `f.java:4138` | `55,100,40,70,80,100,70,110,60,80,50,70, 50×8, 50,50,50, 0,0,0` |
| 9 (+234) | **Max HP, level 3** | ✅ `f.java:4138` | `70,90,90,90,90,90,90,90,90,90,90,90, 50×8, 50,50,50, 0,0,0` |
| 10 (+260) | **Upgrade cost, resource 0** | ✅ `b.java:2964`, displayed `f.java:2204–2220` | `20,40,15,30,30,40,25,30,0,30,20,10, 5,0,5,4,5,4,0,0, 10,10,5, 10,0,0` |
| 11 (+286) | **Upgrade cost, resource 1** | ✅ same | `10,30,5,20,20,30,20,25,20,15,10,10, 0,5,2,4,0,0,0,0, 0,5,10, 10,0,0` |
| 12 (+312) | **Upgrade cost, resource 2** | ✅ same | `0,0,0,0,0,0,0,0,10,0,0,0, 0,0,0,0,3,4,0,0, 0,0,0, 4,0,0` |
| 13 (+338) | **Construction cost, resource 0** — and per-role value A (cols 12–21) | ✅ `b.java:2964` (cols 0–11); role use `f.java:2313` | `10,15,5,50,10,15,18,10,10,10,10,10, 0,1,1,0,0,1,0,0, 0,0,0, 10,0,0` |
| 14 (+364) | **Construction cost, resource 1** — and per-role value B (cols 12–21) | ✅ `b.java:2964` (cols 0–11); role use `f.java:2314` | `5,15,10,50,20,15,18,25,0,15,5,10, 2,3,4,5,6,7,0,0, 0,0,0, 10,0,0` |
| 15 (+390) | ? (col 8 = 10, col 23 = 4, rest 0) | ❓ no code use found | `0,0,0,0,0,0,0,0,10,0,0,0, 0,0,0,0,0,0,0,0, 0,0,0, 4,0,0` |
| 16 (+416) | **Construction-site proxy type** (same footprint) | ✅ PROVEN by exact width+height match for all 12 buildings (§3.1) | `17,13,18,12,15,14,16,13,16,12,12,19, 0,0,0,0,0,0,0,0, 0,0,0, 0,0,0` |
| 17 (+442) | Build-menu order | 🔶 values are a permutation of 0–11; no code use found | `1,2,0,3,4,5,6,7,8,9,10,11, 0,0,0,0,0,0,0,0, 0,0,0, 0,0,0` |
| 18 (+468) | Cost-display count (usually = # of nonzero cost resources) | 🔶 `f.java:2201` (layout centring); cols 22–23 mismatch the count | `2,2,2,2,2,2,2,2,2,2,2,2, 1,1,2,2,2,2,0,0, 1,2,3, 0,0,0` |
| 19 (+494) | Upgrade work units (used as work target while upgrading) | 🔶 `b.java:1811,1826,2194,2201`; values 1–4 too small for HP | `2,4,1,3,3,4,2,4,2,3,3,1, 1,1,2,2,2,2,0,0, 1,1,1, 0,0,0` |
| 20 (+520) | HP-bar vertical offset (×8 px) | ✅ `f.java:1783` | `1,2,3,2,2,2,1,3,2,3,2,7, 2,2,2,2,2,2,2,2, 0,0,0, 0,0,0` |
| 21 (+546) | **Mood bonus, level 1** | ✅ `b.java` `W()` — `rec138[(21+level−1)*26+type]` | `−1,0,0,0,0,0,0,2,0,0,0,0, 0,0,0,0,0,0,0,0, 0,0,0, 0,0,0` |
| 22 (+572) | **Mood bonus, level 2** | ✅ `W()` | `0,0,2,0,2,0,0,3,1,0,0,1, 0,0,0,0,0,0,0,0, 0,0,0, 0,0,0` |
| 23 (+598) | **Mood bonus, level 3** | ✅ `W()` | `1,0,0,0,0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0, 0,0,0, 0,0,0` |

Formulas (✅ from code):
- **Max HP** = `rec138[(7 + level − 1) * 26 + type]`, level 1–3 (`f.java:4138`).
- **Construction** pays rows 13–15 in full, from tribe stock `[2],[3],[4]` (`b.java:2964–2975`).
- **Upgrade** pays rows 10–12 progressively: `cost × V / (maxHP × 2)` per work chunk
  (`b.java:2964`, `V` = work done, `8566` = building's max HP).
- **Repair** cost is the same rows 10–12, scaled the same way (`b.java:2964,3016`).
- Oddity (data as-is, ✅): Chief's hut HP **falls** from 120 (L1) to 70 (L2) then 90 (L3); Gym falls
  from 100 (L2) to 90 (L3). Not a parse error — the bytes say so.
- **Trap costs** (rows 10–12): net trap (type 20) = 10/0/0; spring trap (21) = 10/5/0; pit trap (22) = 5/10/0.
- **Resource identities** (🔶): the three cost resources are stock `[2],[3],[4]`; the game's four
  resources are food, wood, stone, bones (`d0[230]`). Stock `[0]` is food (consumed by the eat task,
  `b.java:4274,4316`). Which of wood/stone/bones maps to stock `[2]/[3]/[4]` is **not proven** — the
  cost UI draws icons `627+i` (`f.java:2204`) and the icon order was not decoded.

### 3.1 Row 16 — construction-site proxies (✅ PROVEN)

When a building is ordered, `f.a()` first places a proxy object of type `rec138[416+type]`
(`b.java:5339` AI path; `f.java:5545–5555` — proxies are types 12–19: the placed object is linked
to the real building type in field `9237`, and its HP is set from the real type's row 7).
The proxy has the **same width and height** as the real building — verified for all 12:

| Building | w×h | Proxy | Proxy w×h |
|---|---|---|---|
| Armoury | 3×2 | 17 | 3×2 |
| Gym | 5×4 | 13 | 5×4 |
| Hut | 2×2 | 18 | 2×2 |
| Chief's hut | 4×4 | 12 | 4×4 |
| Kitchen | 4×3 | 15 | 4×3 |
| Range | 6×4 | 14 | 6×4 |
| Store | 3×3 | 16 | 3×3 |
| Disco | 5×4 | 13 | 5×4 |
| Sanctuary | 3×3 | 16 | 3×3 |
| PIA centre | 4×4 | 12 | 4×4 |
| Nursery | 4×4 | 12 | 4×4 |
| Tower | 1×1 | 19 | 1×1 |

Proxies have HP 5 at level 1 and 50 at levels 2–3 (rows 7–9, cols 12–19). The 8 proxy types are
simply the 8 distinct footprints among the 12 buildings.

### 3.2 Upgrade limits (✅ PROVEN)

- Max building level = **3** (HP rows 7–9 only; AI max levels in rec 244 are all 1–3; initial levels
  in rec 113 are 1–3).
- Rec 80 `[3,7,3,5,5,7,5,6,3,5,3,2]` is 🔶 **worker capacity per building type** (used at
  `b.java:4274` as `assigned < rec80[type]` when assigning villagers to a building): Armoury 3,
  Gym 7, Hut 3, Chief's hut 5, Kitchen 5, Range 7, Store 5, Disco 6, Sanctuary 3, PIA 5,
  Nursery 3, Tower 2.
- Open question: HP for levels 4–7 does not exist in the table, so if rec 80 were a level cap the
  game would read cost rows as HP — the capacity reading is the consistent one.

## 4. Villager HP by age — records 97 and 98 (✅ PROVEN)

`b.java:3939–3943`: each tick, `dHP = rec97[age] + rand(255,5) − 2`; `HP = clamp(HP + dHP, 0, rec98[age])`.
`rec97` values are unsigned bytes read as **signed** (🔶 the signed reading is inferred from the
formula context; 255 = −1 etc. — the code adds the byte to a signed int, so values >127 act negative).

| Age | rec97 (HP change/tick) | rec98 (max HP) |
|-----|------------------------|----------------|
| 0–12 | +3 | 99 |
| 13–19 | +2 | 99 |
| 20–29 | +1 | 99 |
| 30–39 | 0 | 99 |
| 40–55 | −1 (255) | 99 → 94 (declines 1 per few years) |
| 56–60 | −2 (254) | ~93–89 |
| 61–70 | −3 (253) | ~88–79 |
| 71–75 | −4 (252) | ~78–74 |
| 76–79 | −5 (251) | ~73–70 |
| 80–82 | −6 (250) | ~69–67 |
| 83–85 | −7 (249) | ~66–64 |
| 86–88 | −8 (248) | ~63–61 |
| 89–91 | −9 (247) | ~60–58 |
| 92–94 | −10 (246) | ~57–55 |
| 95–96 | −11 (245) | ~54–53 |
| 97–98 | −12 (244) | ~52–51 |
| 99 | −20 (236) | ~50 |
| 100 | −20 (236) | 0 (death) |

Rec 98 (101 values): 99 for ages 0–49, then 98, 97, 96… declining to 0 at age 100. So villagers
**heal while young, slowly lose HP from age 40, and die at 100**. Exact per-age values are in
`pd0-tables.txt` (records 97, 98).

## 5. Task economy — records 71, 72, 73, 76 (✅ PROVEN as material consumption)

When a villager starts a task, the game deducts materials (`b.java:2954–2955`): for each sub-task
`R` in `rec73[S] .. rec73[S+1]-1`, `stock[rec71[R]] -= rec72[R]`. If the stock is short, the task
cannot start and the villager shows a "need" icon `rec76[rec71[R]]` (`b.java:3044–3046`).

- **Rec 71** (task → stock index, 29 values): `[2,2,3,2,3,2,4,2,4,2,2,3,2,3,2,3,1,2,2,4,4,3,3,5,3,7,8,9,10]`
- **Rec 72** (task → amount, 29 values): `[5,5,2,4,4,5,3,4,4,10,10,5,5,10,10,10,1,5,10,5,10,5,10,1,5,1,1,1,1]`
- **Rec 73** (sub-task ranges, 23 values): `[0,1,3,5,7,9,10,12,14,16,17,18,19,20,21,22,23,24,25,26,27,28,29]` — 22 task groups of 1–2 sub-tasks.
- **Rec 76** (resource → need icon, 11 values): `[1,1,2,3,4,8,9,10,11,12,13]`
- **Tribe stock** (`var_short_arr_arr_a[u]`, 26 shorts, ✅ from code): `[0]` = food (eaten, `b.java:4274,4316`),
  `[2],[3],[4]` = the three construction resources (wood/stone/bones, order unproven — §3),
  `[11]` = population, `[12]` = males, `[13]` = females, `[14]` = buildings, `[16]` = living space,
  `[24]` = score. Indices `[1],[5]–[10],[15],[17]–[23],[25]` are 🔶 not fully mapped
  (tasks 25–28 consume stock `[7],[8],[9],[10]` — likely weapon stocks).
- **Rec 41** (task → category, 112 values, 0–16) and **Rec 42** (category → property, 17 values:
  `[0,0,0,0,0,0,0,0,0,0,1,5,4,2,0,0,0]`) gate task eligibility (`b.java:781,832,1021,1221,1841`).
  Exact category names are ❓ unknown — the values 3, 7, 16 are treated specially in code.
- Gathering/production (which tasks *add* to stock) was not fully traced — ❓ open.

## 6. Damage, weapons, projectiles (✅ PROVEN)

- **Melee damage** (`b.java:3715`): `(meleeSkill / 3 + rec102[role]) × (rand(11 − defense) + defense) / 10`
  - **Rec 102** (damage bonus by role, 10): `[1,1,2,3,5,3,0,0,0,0]` — roles 0–5 fight, roles 6–9 do not.
- **Throwing damage** (`b.java:3790`): adds `rec124[throwSkill]`.
  - **Rec 124** (by throwing skill, 10): `[1,1,1,2,2,3,3,4,6,8]`
- **Rec 79** (weapon by task, 10): `[1,1,5,2,2,1,1,5,2,2]` — which weapon a task uses.
- **Rec 159** (projectile gravity / flight factor by weapon, 3 values): `[25,30,40]` — used in the
  parabola math (`b.java:3645,3673–3674`): flight time = `distance > g ? distance / g : 1`.
  So weapon 0 arcs slowest (25), weapon 2 fastest (40). Weapon names are ❓ unknown (3 weapons:
  probably stone / spear / ?).
- **Rec 103** (9 values): `[4,3,0,5,2,1,4,3,0]` — 🔶 weapon-related, exact use unproven.
- **Rec 100** (17 values): `[1,0,0,0,0,0,0,0,0,0,0,0,0,2,2,2,0]` — used in a combat/role check
  (`b.java:1021`). 🔶

## 7. Enemy waves — records 206–217, 220, 241 (✅ PROVEN)

Difficulty `d = var_byte_b`: **0 = easy, 1 = hard** (🔶 set at `f.java:4784,4965,6271` from the
settings/save; the formulas below behave consistently: hard = more attackers, higher skill cap,
shorter intervals). Levels `q = 0–11`; **level 3 is all zeros** — it is special-cased as a tutorial
in code. All wave records are per-level (12 values); difficulty pairs are adjacent records
(`206+d`, `208+d`, …).

| Rec | Meaning | Easy (d=0) | Hard (d=1) |
|-----|---------|-----------|-----------|
| 206 / 207 | Wave base size | `[2,2,2,0,3,3,3,3,3,3,3,3]` | `[2,2,3,0,4,4,4,4,4,4,4,4]` |
| 208 / 209 | Wave max size | `[4,4,5,0,6,7,7,7,7,7,7,7]` | `[4,4,6,0,7,8,8,8,8,8,8,8]` |
| 210 / 211 | Wave growth divisor (÷1000 ticks) | `[20,20,13,0,13,10,10,10,10,10,10,10]` | `[15,15,10,0,10,8,8,8,8,8,8,8]` |
| 212 / 213 | Attacker weapon-skill cap | `[0,1,2,0,4,5,6,5,5,4,6,6]` | `[2,3,6,0,5,7,9,8,8,7,8,9]` |
| 214 | Wave interval base (×100 ticks) | `[40,40,30,10,45,30,25,30,30,30,30,28]` | same record |
| 215 | Interval reduction per difficulty | `[10,10,5,0,7,5,5,0,0,0,0,0]` | same record |
| 217 | Wave-start gate | `[3,0,0,9,0,0,0,0,0,0,0,0]` | same record |
| 220 | Enemy military count M | `[0,9,14,0,16,19,29,25,20,24,21,19]` | same record |
| 241 | AI tick interval (×10 ticks) | `[100,100,70,10,60,50,50,50,50,50,50,50]` | same record |

Formulas (✅ `b.java` `av()` ~line 5490, `as()` ~line 5347):
- **Wave size:** `x = clamp(rec[206+d][q] + tick / rec[210+d][q] / 1000, 0, rec[208+d][q])`;
  attackers = `x/2 + rand(x+1)` (so a wave is at most ~max size, growing slowly over the level).
- **Wave timing:** `aQ = (rec[214][q] − rec[215][q] × d) × 100`; next wave at
  `tick + aQ/4 + rand(aQ × 3/2)`. Hard shortens the interval (e.g. level 0: 4000 → 3000 ticks).
- **Skill cap:** `y = rec[212+d][q]`, scaled down early in the level; attackers are enemy adults
  with weapon skill ≥ `y/2`, flagged `0x40`, HP set to ~half + growth.
- **Gate:** waves only start once `var_byte_f >= rec[217][q]` (mostly 0 = immediately; level 0 needs
  3, level 3 needs 9). The exact meaning of `var_byte_f` is ❓ unresolved (starts 0, +50 at several
  events, set to 2 at one point).
- **Level duration** (`b.java:5233`): `var_int_A = rec216[q] × 500` ticks.
  **Rec 216:** `[16,0,50,100,60,60,15,60,60,60,60,60]` — level 1 has 0 (no time limit / tutorial),
  level 3 is 50,000 ticks (longest), most later levels 30,000 ticks. In seconds at the usual
  50 ms/tick (🔶 tick rate not verified in this pass): L0 400 s, L2 1,250 s, L3 2,500 s, L4–L5 and
  L7–L11 1,500 s, L6 375 s.

## 8. Enemy AI and level data (✅ PROVEN)

- **AI build order** — rec 243 (type, 139), rec 244 (max level, 139), rec 245 (x, 139),
  rec 246 (y, 139); per-level ranges in **rec 247** (13): `[0,0,7,16,16,29,44,63,80,96,111,125,139]`
  (level q builds entries `247[q] .. 247[q+1]-1`; level 0 and 3 build nothing). `ar()` runs every
  `rec241[q] × 10` ticks: it repairs buildings with HP < max/4 and upgrades buildings below the
  rec 244 max level, and places new buildings from the order list via the row-16 proxy (§3.1).
  First entries of rec 243: `[6,1,5,4,0,11,11, …]` — store, gym, range, kitchen, armoury, tower…
- **Enemy role tables** — rec 221 is length 0, so `short_a[221+q]` = start of rec `222+q`.
  Layout ✅ PROVEN by length check: rec `222+q` has exactly `4 × rec220[q]` entries
  (e.g. level 1: M=9 → 36; level 6: M=29 → 116): `[tasks M][x M][y M][roles M]`.
  Level 1 (rec 222): tasks `[14,11,10,66,58,81,81,69,69]`, x `[57,53,48,51,50,40,40,39,39]`,
  y `[23,19,20,29,14,32,40,35,37]`, roles `[0,0,0,2,2,2,2,0,0]`.
- **Level → map** — **rec 248:** `[0,0,1,2,3,4,4,5,6,7,8,9]` (levels 0–1 share map 0; levels 4–5 share map 4).
- **Trigger zones** — rec 218 (12 rects): `[[0,0,0,0],[42,12,62,46],[43,1,62,20],[0,0,0,0],[8,3,60,26],[22,2,62,27],[69,0,93,88],[1,1,27,62],[1,1,27,34],[1,1,25,32],[1,1,45,22],[44,1,62,56]]`;
  rec 219 (12 rects, point-in-rect test `b.java:5423`): `[[0,0,0,0],[28,1,62,46],[30,1,62,32],[49,1,63,33],[8,3,60,46],[9,2,62,39],[60,0,93,88],[1,1,44,62],[1,1,44,44],[1,1,36,46],[1,1,45,42],[34,1,62,56]]`;
  rec 101 (7 rects, `b.java:2327`): `[0,0,0,0, 28,32,45,42, 0,44,37,79, 0,0,0,0, 1,57,62,93, 0,0,0,0, 0,0,0,0]`.
- **Rally point per level** — rec 233 (x): `[24,44,52,58,47,35,68,29,24,26,20,41]`; rec 234 (y):
  `[28,36,20,17,27,27,34,41,21,15,19,25]`; rec 235 (route count): `[1,1,4,0,3,3,3,2,4,4,3,3]`.
- **Wave paths** — rec 236 (31 waypoint counts), rec 237 (31 offsets), rec 238 (13 path-set starts:
  `[0,1,2,6,6,9,12,15,17,21,25,28,31]`), rec 239 (188 bytes waypoint data, first pairs
  `[10,15, 24,28, 10,15, 37,30, 35,49, …]`), rec 240 (13 offsets: `[0,2,6,36,36,50,72,98,108,130,156,174,188]`).
  Waypoints advance every 150 ticks (`aw()`).
- **Spawning** — rec 265 (60 = 12 levels × 5), rec 266 (104 random points, first 40:
  `[32,35,35,37,47,30,59,32,33,27,41,28,35,12,37,24,30,32,34,35,35,34,38,37,41,36,45,38,17,25,19,33,20,34,29,37,38,34,45,36]`),
  rec 267 (13 offsets: `[0,0,1,4,4,7,11,14,16,19,22,24,26]`), rec 271 (56 points), rec 272 (13 offsets:
  `[0,0,0,0,0,0,3,5,7,9,12,13,14]`). Random-point helper `n()` (`b.java` ~5312) uses pairs (266,267)
  and (271,272).
- **Traps** — **rec 268** (trap-spawn chance per level): `[0,2,6,0,6,10,12,6,8,8,6,5]`.
- **Sanctuary** — **rec 269** (spawn interval ×50 ticks): `[100,100,100,100,40,30,30,30,30,30,30,30]`;
  **rec 270** (spawn count): `[0,0,0,0,0,1,2,1,1,1,1,1]` — sanctuaries only spawn from level 5.
- **Mood** — rows 21–23 of rec 138 (§3): working in a Disco gives +2/+3 mood (L1/L2); Armoury L1
  gives −1; Hut L2 +2; Kitchen L2 +2; Sanctuary L2 +1; Tower L2 +1; Armoury L3 +1.

## 9. The 5 fixed-point groups at the end of `/a` (✅ layout, 🔶 interpretation)

`var_short_arr_b`, 285 BE u16 values, cumulative offsets `c[] = [0,122,243,249,273]`.

| Group | Len | First values | Use / interpretation |
|-------|-----|--------------|----------------------|
| 0 | 122 | 0, 25856, 51712, 12033, 37889, 63745, 24066, 49922, 10243… | 🔶 Arithmetic progression mod 65536 (step 25856); exact use not traced |
| 1 | 121 | 0, 5632, 11264, 16896, 22528, 28160, 33792, 39424, 45056, 50688, 56320, 5632, 7936, 12544… | ✅ **Distance table, 11×11** (`b.java:3644`: `short_b[c[1] + |dx|*11 + |dy|]`); value ≈ `sqrt(dx²+dy²) × 512` (e.g. (1,1) → 7936 ≈ 512√2) |
| 2 | 6 | 12800, 12800, 53255, 60930, 24065, 12800 | 🔶 Copied into `var_short_arr_d` (`b.java:5765`); use untraced |
| 3 | 24 | 51200, 11265, 59395, 11265, 51200, 51200, 51200, 51200, 51200, 64000, 11265, 64000, 51200, 51200, 51200, 51200, 4135×8 | ✅ **Projectile velocity table, 3 weapons × 8 directions** (`b.java:3673`: `short_b[c[3] + weapon*8 + dir]`); fixed-point ÷256 (51200 = 200, 64000 = 250, 4135 ≈ 16.2; 59395 as signed = −6141 ≈ −24) |
| 4 | 12 | 34835, 0, 40975, 57390, 28695, 40975, 0, 28695, 28695, 28695, 28695, 28695 | ✅ **Per-level time gate** (`b.java:3992,4058`): villagers age / act only once `tick >= short_b[c[4]+q]`; values are raw u16 (some >32767, i.e. negative as signed — the comparison is unsigned, so those levels' gates are effectively very late) |

## 10. Other notable `/a` records

- **Rec 83 / 84 — HP ladder per building type** (✅ use at `b.java:4316`: `currentHP < rec83[rec84[type] + level]`).
  Rec 84 (cumulative offsets): `[0,4,12,16,22,28,36,42,49,53,59,63,66]`; rec 83 (66 values) per type:
  Armoury `[5,20,30,40]`, Gym `[5,10,20,30,40,50,60,70]`, Hut `[5,15,20,25]`,
  Chief's hut `[5,30,35,40,45,120]`, Kitchen `[5,20,30,40,50,60]`, Range `[5,10,20,30,40,50,60,70]`,
  Store `[5,20,30,40,45,50]`, Disco `[5,20,35,50,65,80,90]`, Sanctuary `[5,20,35,50]`,
  PIA `[5,20,30,40,50,60]`, Nursery `[5,20,30,40]`, Tower `[5,30,50]`. Each ladder ends at the
  type's level-1 max HP (🔶 likely repair/construction checkpoints; the exact trigger is `b.java:4316`).
- **Rec 53** (625 = 25×25, ✅ distance lookup, `b.java` `boolean_h()`: `rec53[(dy+12)*25 + (dx+12)] / 10`
  compared with a villager's range) and **rec 54** (169 = 13×13, 🔶 second distance grid).
- **Rec 80** — see §3.2 (worker capacity, 🔶).
- **Rec 113** (36 values: `[1,1,2,1,1,1,1,1,1,1,1,1,2,2,2,1,2,2,1,1,1,1,1,1,3,2,2,1,2,2,1,2,2,2,1,2]`) —
  ✅ initial building level by type and campaign phase (`f.java:5540`: phase 0/1/2 → offsets 0/12/24).
- **Rec 1** (16): `[1,1,0,255,255,255,0,1,0,1,1,1,0,255,255,255]` — ❓ (flags, −1 = 255).
- **Rec 15** (18): `[0,0,2,3,4,5,6,7,8,0,0,3,4,6,7,8,10,11]` — ❓.
- **Rec 16** (76): task/menu codes (values 0–103, many 77s) — ❓.
- **Rec 17** (10): `[0,1,2,22,30,32,33,34,54,74]` — ❓. **Rec 18** (10): `[0,5,5,0,0,5,0,0,0,0]` — ❓.
  **Rec 19** (2): `[0,3]` — ❓.
- **Rec 41/42** — see §5. **Rec 50** (112 values, mostly 35/50/65/80/100/127) and **rec 51** (112 values,
  mostly 253–255 with 0–6) — 🔶 paired per-something tables (task timing?), exact use unproven.
- **Rec 74** (16): `[2,2,3,4,4,2,2,3,3,1,2,2,4,4,3,3]` — ❓. **Rec 85** (4): `[2,4,7,10]` — ❓.
  **Rec 86** (9): `[28,0,29,30,31,32,33,34,35]` — ❓.
- **Rec 99** (32): `[0×11,1,1,1,1,0,0,0,1,2,2,2,3,0,0,1,2,3,4,5,6,7]` — ❓.
- **Rec 100/102/103/124/159** — see §6. **Rec 107** (11): `[17,16,75,69,70,71,72,73,74,42,41]` — ❓.
  **Rec 114** (6): `[1,5,9,61,72,100]` — ❓. **Rec 121** (14): `[69,22,21,24,19,20,25,23,26,26,26,26,26,26]` — ❓.
- **Rec 126** (17): `[255,69,69,69,69,69,69,69,70,71,72,73,74,75,17,16,255]`; **rec 127** (17):
  `[0,255,255,255,255,255,255,255,255,255,255,255,255,255,0,0,0]` — 🔶 paired tables (69–75 are task codes).
- **Rec 128** (8): `[5,7,9,11,13,15,22,30]`; **rec 129** (30 values); **rec 130** (5): `[0,6,13,21,30]`
  (cumulative offsets into rec 129: groups of 6,7,8,9) — ❓.
- **Rec 153** (long, mostly 0/1 flags) and **rec 155** (112 values, incl. 254/255) — ❓.
- **Rec 179** (3): `[6,4,5]` — ❓. **Rec 195** (100 bytes, first 40:
  `[2,4,5,6,3,5,7,8,9,10,12,12,12,12,12,12,12,11,12,12,1,2,2,0,1,2,2,0,0,2,0,0,0,0,0,0,0,0,0,0]`)
  and **rec 196** (236 bytes, mostly 0 with 42/8/12/16/17/135/157/158) — 🔶 menu/layout tables
  (used as `byte_arr_a[short_a[195] + 60 + screen]`), exact layout unproven.
- **Rec 232** — level 11 enemy role table (see §8). **Rec 265–272** — see §8.
- **Rec 273/274/276/277/278** (12 values each, per level) — ❓ per-level parameters, no code use traced:
  273 `[0,40,35,0,30,25,20,25,25,25,25,20]`; 274 `[0,15,10,0,18,15,10,18,18,18,20,18]`;
  276 `[0,20,30,0,30,35,45,40,40,40,40,40]`; 277 `[255,255,20,255,15,15,10,15,15,15,15,15]`;
  278 `[255,255,255,255,30,25,25,30,30,30,30,30]`. (Rec 275 `[0,15,20,0,25,30,40,35,35,35,35,35]`
  also untraced.)
- **Rec 283** (6): `[12,13,14,8,8,8]` — ❓. **Rec 296** (23):
  `[0,1,3,2,2,2,2,0,0,1,2,0,4,0,0,0,1,1,2,1,0,0,0]` — ❓. **Rec 297** (23):
  `[10,16,0,12,2,5,1,50,50,4,9,2,0,20,50,60,2,0,8,1,5,50,50]` — ❓.
- **Rec 298** (23): `[10,5,5,20,10,20,20,50,50,10,40,2,2,20,50,60,10,10,100,10,5,50,50]` — ❓.
- **Rec 299** (9): `[40,50,60,60,50,65,80,95,110]`; **rec 300** (9): `[0,4,1,5,8,7,9,0,11]` — ❓.
- **Rec 305** (20): `[5,6,7,8,9,10,11,12,13,14,15,16,17,18,18,19,20,21,22,22]`; **rec 306** (3): `[0,6,20]` — ❓.
- **Rec 311** (687 bytes, last record, first 40: `[0,0,0,0,2,1,2,1,2,1,2,1,0,1,0,2,1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1]`) — ❓ largest
  single record; purpose unknown (possibly map/object placement data).

## 11. What is proven / inferred / still unknown

**✅ PROVEN:** `pd0` layout (36 tables, exact lengths); `/a` layout (312 interleaved records + 5 groups);
building table geometry (width/height), HP levels 1–3, construction vs upgrade cost rows and their
payment formulas, trap costs, construction-site proxies (row 16) with exact footprint match; villager
HP-by-age curves and the per-tick formula; task material consumption (rec 71/72/73) and the need-icon
table (rec 76); melee/throw damage formulas and their tables; projectile gravity factors; the full
wave system (size/timing/skill-cap formulas, all per-level values, difficulty pairs); level durations
(rec 216); AI build-order data and its per-level ranges; the 4×M enemy role-table layout (verified by
length for all 12 levels); level→map, rally points, wave paths, trap/sanctuary spawn tables; mood
bonuses per building level; the distance table (group 1) and projectile velocity table (group 3);
the per-level time gate (group 4); the HP ladder (rec 83/84); worker capacity reading of rec 80
(formula use proven, name inferred).

**🔶 INFERRED (needs one more confirmation):** the three construction-resource identities
(wood/stone/bones order vs stock [2]/[3]/[4]); stock `[0]` = food; rec 80 = worker capacity;
row 6 = worker-assignment flag; row 17 = build-menu order; row 18 = cost-display count; row 19 =
upgrade work units; row 13/14 columns 12–21 = per-role display values; difficulty 0 = easy /
1 = hard; the signed-byte reading of rec 97; group 0 and group 2 purposes; rec 83 = repair
checkpoints; the 50 ms/tick rate used for the seconds conversions.

**❓ UNKNOWN:** rec 138 rows 0, 1, 2, 3, 15 (no code use found — possibly dead/editor data);
building-table types 23–25; the exact meaning of `var_byte_f` (wave gate counter); the gathering /
production side of the task economy; weapon names for the 3 projectile types; task-category names
(rec 41/42); records 273–278, 283, 296–300, 305, 306, 311 and most of the ~150 records listed in
Appendix A without a role.

## 12. Open questions (for a follow-up pass)

1. Resolve the resource names: trace the HUD drawing code (`f.java` resource icons 627–629) to map
   stock `[2]/[3]/[4]` → wood/stone/bones.
2. Trace `var_byte_f` and the task-production code (what adds to stock) in `b.java`.
3. Find uses of rec 138 rows 0–3, 15, 17 via computed offsets (e.g. `(row+level)*26`), or confirm dead data.
4. Identify records 273–278, 283, 296–300, 305, 306, 311 (311 is 687 bytes — the largest record).
5. Confirm the main-loop tick rate (50 ms?) to turn tick counts into seconds.
6. Name the 3 weapons (rec 159) and the 10 roles (rec 102) from the in-game text tables.

## Files

- `decode_pd0.py` — parser for `pd0` (36 tables) and `/a` (312 records + 5 groups); asserts exact sizes.
- `pd0-tables.txt` — full numeric dump of every table and record (407 KB).
- `pd0-analysis.md` — this file.
- `rec-inventory.txt` — compact per-record inventory (index, length, first values), source for Appendix A.
- Originals untouched: `extracted/pd0`, `extracted/a`.

## Appendix A — `/a` record inventory (all 312 records)

Length and first 8 values per record; role notes where established in this report. Full values in `pd0-tables.txt`.

| Rec | Len | First values | Role |
|-----|-----|--------------|------|
| 0 | 32 | `[0, 255, 255, 255, 255, 0, 255, 255]` |  |
| 1 | 16 | `[1, 1, 0, 255, 255, 255, 0, 1]` | flags? |
| 2 | 16 | `[0, 1, 1, 1, 0, 255, 255, 255]` |  |
| 3 | 9 | `[5, 6, 7, 4, 0, 0, 3, 2]` |  |
| 4 | 9 | `[5, 4, 3, 6, 0, 2, 7, 0]` |  |
| 5 | 42 | `[0, 245, 0, 0, 7, 249, 0, 0]` |  |
| 6 | 56 | `[0, 7, 248, 0, 0, 5, 245, 250]` |  |
| 7 | 42 | `[0, 248, 0, 0, 5, 251, 0, 0]` |  |
| 8 | 56 | `[0, 6, 251, 0, 0, 4, 248, 252]` |  |
| 9 | 42 | `[0, 7, 0, 0, 5, 5, 0, 0]` |  |
| 10 | 56 | `[0, 3, 3, 0, 0, 3, 5, 3]` |  |
| 11 | 42 | `[0, 4, 0, 0, 3, 3, 0, 0]` |  |
| 12 | 10 | `[0, 0, 0, 3, 7, 12, 18, 25]` |  |
| 13 | 56 | `[0, 2, 2, 0, 0, 2, 3, 2]` |  |
| 14 | 10 | `[0, 0, 0, 4, 9, 16, 24, 33]` |  |
| 15 | 18 | `[0, 0, 2, 3, 4, 5, 6, 7]` | ? |
| 16 | 74 | `[69, 69, 58, 61, 65, 103, 66, 72]` | task/menu codes? |
| 17 | 10 | `[0, 1, 2, 22, 30, 32, 33, 34]` | ? |
| 18 | 10 | `[0, 5, 5, 0, 0, 5, 0, 0]` | ? |
| 19 | 2 | `[0, 3]` | ? |
| 20 | 20 | `[2, 2, 3, 2, 2, 2, 0, 2]` |  |
| 21 | 60 | `[7, 5, 0, 7, 5, 0, 7, 5]` |  |
| 22 | 60 | `[1, 2, 0, 2, 3, 0, 1, 2]` |  |
| 23 | 60 | `[2, 2, 0, 4, 4, 0, 2, 2]` |  |
| 24 | 20 | `[1, 2, 1, 2, 3, 2, 1, 2]` |  |
| 25 | 20 | `[1, 3, 1, 3, 1, 3, 2, 3]` |  |
| 26 | 112 | `[19, 19, 106, 85, 85, 19, 19, 106]` | waypoint data? |
| 27 | 112 | `[7, 3, 2, 5, 1, 7, 3, 2]` | task flags? |
| 28 | 112 | `[0, 0, 99, 83, 83, 0, 0, 99]` | waypoint data? |
| 29 | 112 | `[69, 69, 60, 69, 69, 69, 69, 60]` |  |
| 30 | 112 | `[0, 0, 156, 0, 0, 156, 156, 156]` |  |
| 31 | 112 | `[19, 19, 13, 85, 85, 13, 13, 13]` |  |
| 32 | 112 | `[44, 44, 44, 44, 44, 0, 0, 44]` | waypoint data? |
| 33 | 112 | `[13, 13, 13, 13, 13, 4, 4, 13]` |  |
| 34 | 112 | `[0, 0, 0, 0, 0, 0, 0, 0]` |  |
| 35 | 112 | `[41, 41, 41, 41, 41, 41, 41, 41]` |  |
| 36 | 112 | `[0, 0, 0, 0, 0, 0, 0, 0]` |  |
| 37 | 112 | `[10, 10, 15, 10, 10, 10, 10, 15]` |  |
| 38 | 112 | `[1, 1, 1, 1, 1, 238, 238, 238]` |  |
| 39 | 112 | `[0, 0, 0, 0, 0, 0, 0, 0]` | task gate? |
| 40 | 112 | `[255, 255, 255, 255, 255, 255, 255, 255]` |  |
| 41 | 112 | `[0, 0, 0, 0, 0, 0, 0, 0]` | task->category |
| 42 | 17 | `[0, 0, 0, 0, 0, 0, 0, 0]` | category property |
| 43 | 112 | `[8, 8, 3, 8, 8, 8, 8, 3]` |  |
| 44 | 14 | `[10, 17, 16, 18, 67, 37, 49, 69]` |  |
| 45 | 112 | `[1, 1, 1, 1, 1, 2, 2, 2]` |  |
| 46 | 112 | `[5, 5, 5, 5, 5, 5, 5, 5]` |  |
| 47 | 112 | `[9, 9, 9, 9, 9, 9, 9, 9]` |  |
| 48 | 112 | `[2, 2, 2, 2, 2, 2, 2, 2]` |  |
| 49 | 112 | `[99, 99, 99, 99, 99, 99, 99, 99]` |  |
| 50 | 112 | `[35, 35, 50, 35, 35, 35, 35, 50]` | paired w/51? |
| 51 | 112 | `[253, 253, 254, 253, 253, 253, 253, 254]` | paired w/50? |
| 52 | 112 | `[45, 45, 70, 45, 45, 45, 45, 70]` |  |
| 53 | 625 | `[100, 100, 100, 100, 100, 100, 100, 100]` | 25x25 distance |
| 54 | 169 | `[1, 3, 3, 3, 3, 5, 5, 5]` | 13x13 distance |
| 55 | 14 | `[0, 1, 4, 9, 16, 25, 36, 49]` |  |
| 56 | 44 | `[20, 28, 21, 19, 5, 5, 5, 5]` |  |
| 57 | 65 | `[58, 61, 62, 63, 64, 65, 65, 65]` |  |
| 58 | 65 | `[52, 61, 62, 63, 64, 65, 65, 65]` |  |
| 59 | 67 | `[56, 77, 56, 77, 78, 77, 56, 77]` |  |
| 60 | 67 | `[56, 76, 56, 76, 56, 76, 56, 76]` |  |
| 61 | 5 | `[0, 0, 106, 93, 92]` |  |
| 62 | 5 | `[0, 0, 1, 255, 1]` |  |
| 63 | 74 | `[1, 1, 1, 1, 5, 1, 255, 10]` |  |
| 64 | 14 | `[255, 1, 1, 1, 10, 1, 1, 1]` |  |
| 65 | 74 | `[8, 8, 8, 1, 4, 1, 0, 4]` |  |
| 66 | 74 | `[30, 40, 50, 100, 100, 100, 100, 100]` |  |
| 67 | 74 | `[5, 7, 10, 5, 75, 7, 5, 99]` |  |
| 68 | 21 | `[0, 3, 11, 14, 17, 19, 30, 33]` |  |
| 69 | 80 | `[0, 1, 2, 3, 0, 2, 5, 8]` |  |
| 70 | 20 | `[0, 1, 0, 0, 0, 1, 0, 2]` |  |
| 71 | 29 | `[2, 2, 3, 2, 3, 2, 4, 2]` | task->stock |
| 72 | 29 | `[5, 5, 2, 4, 4, 5, 3, 4]` | task->amount |
| 73 | 23 | `[0, 1, 3, 5, 7, 9, 10, 12]` | task group ranges |
| 74 | 16 | `[2, 2, 3, 4, 4, 2, 2, 3]` | ? |
| 75 | 16 | `[2, 4, 4, 7, 7, 9, 9, 9]` |  |
| 76 | 11 | `[1, 1, 2, 3, 4, 8, 9, 10]` | resource->need icon |
| 77 | 10 | `[255, 0, 1, 255, 255, 2, 254, 254]` |  |
| 78 | 21 | `[127, 19, 85, 127, 127, 106, 127, 127]` |  |
| 79 | 10 | `[1, 1, 5, 2, 2, 1, 1, 5]` | weapon by task |
| 80 | 12 | `[3, 7, 3, 5, 5, 7, 5, 6]` | worker capacity (inferred) |
| 81 | 54 | `[39, 39, 43, 39, 43, 39, 43, 39]` | enemy appearance? |
| 82 | 13 | `[0, 3, 10, 13, 18, 23, 30, 35]` | cumulative offsets->81 |
| 83 | 66 | `[5, 20, 30, 40, 5, 10, 20, 30]` | HP ladder |
| 84 | 13 | `[0, 4, 12, 16, 22, 28, 36, 42]` | offsets->83 |
| 85 | 4 | `[2, 4, 7, 10]` | ? |
| 86 | 9 | `[28, 0, 29, 30, 31, 32, 33, 34]` | ? |
| 87 | 4 | `[94, 95, 96, 97]` |  |
| 88 | 9 | `[5, 3, 7, 8, 9, 10, 11, 11]` |  |
| 89 | 14 | `[0, 1, 196, 146, 131, 101, 128, 0]` |  |
| 90 | 14 | `[1, 1, 255, 255, 255, 1, 0, 0]` |  |
| 91 | 7 | `[41, 41, 89, 118, 41, 41, 41]` |  |
| 92 | 7 | `[127, 50, 30, 127, 127, 127, 127]` |  |
| 93 | 50 | `[0, 1, 0, 1, 2, 3, 0, 1]` |  |
| 94 | 13 | `[0, 2, 6, 12, 17, 24, 28, 30]` |  |
| 95 | 35 | `[0, 1, 0, 1, 2, 3, 0, 1]` |  |
| 96 | 13 | `[0, 2, 6, 8, 11, 14, 18, 20]` |  |
| 97 | 101 | `[3, 3, 3, 3, 3, 3, 3, 3]` | villager HP delta by age |
| 98 | 101 | `[99, 99, 99, 99, 99, 99, 99, 99]` | villager max HP by age |
| 99 | 32 | `[0, 0, 0, 0, 0, 0, 0, 0]` | ? |
| 100 | 17 | `[1, 0, 0, 0, 0, 0, 0, 0]` | combat/role check |
| 101 | 28 | `[0, 0, 0, 0, 28, 32, 45, 42]` | 7 rects |
| 102 | 10 | `[1, 1, 2, 3, 5, 3, 0, 0]` | damage bonus by role |
| 103 | 9 | `[4, 3, 0, 5, 2, 1, 4, 3]` | weapon-related? |
| 104 | 9 | `[1, 1, 1, 1, 1, 5, 1, 1]` |  |
| 105 | 6 | `[1, 5, 1, 1, 1, 1]` |  |
| 106 | 3 | `[10, 20, 30]` |  |
| 107 | 11 | `[17, 16, 75, 69, 70, 71, 72, 73]` | ? |
| 108 | 9 | `[14, 15, 13, 7, 8, 9, 10, 11]` |  |
| 109 | 5 | `[4, 3, 0, 5, 2]` |  |
| 110 | 8 | `[0, 20, 20, 20, 15, 25, 25, 15]` |  |
| 111 | 20 | `[2, 2, 1, 1, 0, 2, 0, 2]` |  |
| 112 | 5 | `[15, 25, 60, 40, 1]` |  |
| 113 | 36 | `[1, 1, 2, 1, 1, 1, 1, 1]` | initial building level |
| 114 | 6 | `[1, 5, 9, 61, 72, 100]` | ? |
| 115 | 5 | `[1, 51, 1, 31, 0]` |  |
| 116 | 5 | `[50, 100, 30, 60, 21]` |  |
| 117 | 5 | `[19, 19, 85, 85, 106]` |  |
| 118 | 5 | `[0, 0, 83, 83, 99]` |  |
| 119 | 5 | `[4, 4, 3, 3, 2]` |  |
| 120 | 9 | `[1, 3, 4, 0, 2, 4, 4, 0]` |  |
| 121 | 14 | `[69, 22, 21, 24, 19, 20, 25, 23]` | ? |
| 122 | 10 | `[4, 4, 2, 3, 3, 4, 4, 2]` | ? |
| 123 | 5 | `[3, 3, 8, 0, 0]` | ? |
| 124 | 10 | `[1, 1, 1, 2, 2, 3, 3, 4]` | throw damage by skill |
| 125 | 4 | `[1, 1, 2, 3]` | ? |
| 126 | 17 | `[255, 69, 69, 69, 69, 69, 69, 69]` | paired w/127? |
| 127 | 17 | `[0, 255, 255, 255, 255, 255, 255, 255]` | paired w/126? |
| 128 | 8 | `[5, 7, 9, 11, 13, 15, 22, 30]` | ? |
| 129 | 30 | `[0, 0, 0, 1, 1, 0, 0, 0]` | ? |
| 130 | 5 | `[0, 6, 13, 21, 30]` | offsets->129 |
| 131 | 40 | `[0, 0, 1, 1, 2, 2, 2, 0]` |  |
| 132 | 5 | `[0, 8, 17, 28, 40]` |  |
| 133 | 18 | `[2, 4, 0, 1, 2, 4, 0, 1]` |  |
| 134 | 5 | `[0, 3, 7, 12, 18]` |  |
| 135 | 24 | `[1, 3, 5, 0, 1, 3, 5, 7]` |  |
| 136 | 5 | `[0, 4, 9, 16, 24]` |  |
| 137 | 11 | `[2, 6, 4, 0, 1, 5, 8, 9]` |  |
| 138 | 624 | `[1, 2, 4, 2, 5, 2, 0, 5]` | BUILDING TABLE |
| 139 | 109 | `[0, 0, 4, 0, 0, 0, 0, 0]` |  |
| 140 | 26 | `[0, 2, 6, 10, 15, 22, 26, 28]` |  |
| 141 | 18 | `[255, 0, 1, 255, 0, 1, 255, 0]` |  |
| 142 | 5 | `[25, 2, 1, 3, 4]` |  |
| 143 | 17 | `[0, 2, 6, 0, 2, 3, 4, 6]` |  |
| 144 | 4 | `[0, 3, 9, 17]` |  |
| 145 | 12 | `[5, 8, 8, 6, 5, 6, 0, 0]` |  |
| 146 | 5 | `[11, 1, 2, 3, 4]` |  |
| 147 | 23 | `[19, 67, 27, 68, 20, 21, 22, 22]` |  |
| 148 | 3 | `[1, 0, 1]` |  |
| 149 | 24 | `[64, 48, 64, 48, 64, 80, 64, 64]` |  |
| 150 | 24 | `[15, 5, 15, 5, 8, 69, 39, 61]` |  |
| 151 | 58 | `[0, 1, 2, 3, 5, 0, 1, 2]` |  |
| 152 | 16 | `[0, 5, 11, 13, 15, 16, 18, 21]` |  |
| 153 | 203 | `[1, 1, 1, 1, 1, 1, 1, 1]` | flags? |
| 154 | 9 | `[0, 0, 3, 4, 6, 8, 9, 10]` |  |
| 155 | 112 | `[0, 1, 1, 1, 1, 1, 1, 2]` | ? |
| 156 | 50 | `[0, 1, 3, 5, 4, 51, 2, 4]` |  |
| 157 | 7 | `[0, 0, 15, 21, 27, 36, 50]` |  |
| 158 | 3 | `[1, 2, 2]` |  |
| 159 | 3 | `[25, 30, 40]` | projectile gravity by weapon |
| 160 | 112 | `[69, 69, 12, 69, 69, 69, 69, 12]` |  |
| 161 | 47 | `[23, 24, 25, 26, 27, 28, 29, 30]` |  |
| 162 | 47 | `[9, 18, 27, 36, 45, 54, 63, 72]` |  |
| 163 | 11 | `[0, 11, 12, 13, 24, 35, 36, 36]` |  |
| 164 | 203 | `[21, 21, 21, 141, 142, 143, 144, 146]` |  |
| 165 | 203 | `[100, 100, 100, 25, 50, 75, 100, 100]` |  |
| 166 | 113 | `[0, 0, 0, 0, 0, 0, 0, 0]` |  |
| 167 | 2 | `[0, 1]` |  |
| 168 | 4 | `[0, 1, 0, 1]` |  |
| 169 | 112 | `[255, 255, 255, 255, 255, 255, 255, 255]` |  |
| 170 | 15 | `[90, 70, 127, 127, 127, 80, 127, 45]` |  |
| 171 | 162 | `[254, 254, 254, 254, 254, 254, 254, 254]` |  |
| 172 | 65 | `[55, 75, 77, 96, 79, 69, 69, 69]` |  |
| 173 | 65 | `[56, 76, 78, 97, 80, 70, 70, 70]` |  |
| 174 | 21 | `[0, 1, 5, 9, 14, 21, 25, 25]` |  |
| 175 | 67 | `[55, 55, 75, 77, 96, 79, 69, 69]` |  |
| 176 | 67 | `[56, 56, 76, 78, 97, 80, 70, 70]` |  |
| 177 | 21 | `[0, 2, 6, 10, 13, 20, 24, 26]` |  |
| 178 | 8 | `[0, 1, 3, 0, 0, 2, 0, 0]` |  |
| 179 | 3 | `[6, 4, 5]` | ? |
| 180 | 3 | `[30, 50, 20]` |  |
| 181 | 3 | `[5, 100, 0]` |  |
| 182 | 3 | `[2, 4, 0]` |  |
| 183 | 3 | `[25, 15, 15]` |  |
| 184 | 6 | `[48, 50, 52, 47, 49, 51]` |  |
| 185 | 84 | `[25, 25, 100, 25, 25, 100, 30, 50]` |  |
| 186 | 8 | `[0, 29, 30, 45, 46, 13, 79, 64]` |  |
| 187 | 8 | `[0, 0, 0, 0, 0, 1, 0, 69]` |  |
| 188 | 4 | `[137, 42, 42, 42]` |  |
| 189 | 20 | `[0, 3, 3, 5, 8, 9, 27, 1]` |  |
| 190 | 136 | `[2, 2, 4, 4, 4, 6, 6, 8]` |  |
| 191 | 136 | `[5, 7, 9, 11, 13, 15, 17, 19]` |  |
| 192 | 16 | `[4, 5, 6, 7, 8, 9, 10, 11]` |  |
| 193 | 12 | `[255, 83, 0, 255, 255, 115, 255, 17]` |  |
| 194 | 270 | `[0, 0, 0, 1, 1, 1, 2, 2]` |  |
| 195 | 100 | `[2, 4, 5, 6, 3, 5, 7, 8]` | menu/layout? |
| 196 | 231 | `[0, 0, 0, 17, 12, 0, 0, 0]` | menu/layout? |
| 197 | 12 | `[4, 4, 2, 2, 2, 2, 3, 0]` |  |
| 198 | 31 | `[7, 8, 12, 22, 23, 24, 25, 26]` |  |
| 199 | 28 | `[27, 27, 51, 16, 38, 21, 7, 11]` |  |
| 200 | 28 | `[11, 11, 71, 34, 57, 2, 17, 2]` |  |
| 201 | 13 | `[0, 1, 2, 5, 11, 15, 17, 19]` |  |
| 202 | 12 | `[1, 1, 3, 0, 2, 2, 2, 2]` |  |
| 203 | 12 | `[8, 8, 8, 1, 5, 4, 4, 7]` |  |
| 204 | 12 | `[40, 40, 35, 100, 25, 35, 30, 30]` |  |
| 205 | 12 | `[2, 3, 3, 0, 6, 3, 3, 3]` |  |
| 206 | 12 | `[2, 2, 2, 0, 3, 3, 3, 3]` | wave base size easy |
| 207 | 12 | `[2, 2, 3, 0, 4, 4, 4, 4]` | wave base size hard |
| 208 | 12 | `[4, 4, 5, 0, 6, 7, 7, 7]` | wave max easy |
| 209 | 12 | `[4, 4, 6, 0, 7, 8, 8, 8]` | wave max hard |
| 210 | 12 | `[20, 20, 13, 0, 13, 10, 10, 10]` | wave growth easy |
| 211 | 12 | `[15, 15, 10, 0, 10, 8, 8, 8]` | wave growth hard |
| 212 | 12 | `[0, 1, 2, 0, 4, 5, 6, 5]` | skill cap easy |
| 213 | 12 | `[2, 3, 6, 0, 5, 7, 9, 8]` | skill cap hard |
| 214 | 12 | `[40, 40, 30, 10, 45, 30, 25, 30]` | wave interval base |
| 215 | 12 | `[10, 10, 5, 0, 7, 5, 5, 0]` | interval reduction |
| 216 | 12 | `[16, 0, 50, 100, 60, 60, 15, 60]` | level duration x500 |
| 217 | 12 | `[3, 0, 0, 9, 0, 0, 0, 0]` | wave gate |
| 218 | 48 | `[0, 0, 0, 0, 42, 12, 62, 46]` | trigger rects |
| 219 | 48 | `[0, 0, 0, 0, 28, 1, 62, 46]` | trigger rects 2 |
| 220 | 12 | `[0, 9, 14, 0, 16, 19, 29, 25]` | enemy military count M |
| 221 | 0 | `[]` | (len 0) role tables base |
| 222 | 36 | `[14, 11, 10, 66, 58, 81, 81, 69]` | enemy roles L1 |
| 223 | 56 | `[13, 11, 10, 14, 58, 66, 81, 81]` | enemy roles L2 |
| 224 | 0 | `[]` | enemy roles L3 (empty) |
| 225 | 64 | `[15, 10, 13, 11, 14, 58, 66, 57]` | enemy roles L4 |
| 226 | 76 | `[15, 13, 14, 10, 11, 58, 66, 57]` | enemy roles L5 |
| 227 | 116 | `[15, 14, 10, 11, 13, 11, 58, 58]` | enemy roles L6 |
| 228 | 100 | `[10, 10, 11, 11, 13, 13, 14, 58]` | enemy roles L7 |
| 229 | 80 | `[15, 11, 13, 10, 11, 14, 58, 66]` | enemy roles L8 |
| 230 | 96 | `[10, 10, 11, 14, 13, 11, 58, 66]` | enemy roles L9 |
| 231 | 84 | `[13, 10, 11, 11, 14, 14, 58, 66]` | enemy roles L10 |
| 232 | 76 | `[10, 10, 13, 11, 11, 11, 14, 58]` | enemy roles L11 |
| 233 | 12 | `[24, 44, 52, 58, 47, 35, 68, 29]` | rally x |
| 234 | 12 | `[28, 36, 20, 17, 27, 27, 34, 41]` | rally y |
| 235 | 12 | `[1, 1, 4, 0, 3, 3, 3, 2]` | rally route count |
| 236 | 31 | `[1, 2, 3, 4, 4, 4, 2, 2]` | waypoint counts |
| 237 | 31 | `[0, 0, 0, 6, 14, 22, 0, 4]` | waypoint offsets |
| 238 | 13 | `[0, 1, 2, 6, 6, 9, 12, 15]` | path-set starts |
| 239 | 188 | `[10, 15, 24, 28, 10, 15, 37, 30]` | waypoint data |
| 240 | 13 | `[0, 2, 6, 36, 36, 50, 72, 98]` | waypoint offsets 2 |
| 241 | 12 | `[100, 100, 70, 10, 60, 50, 50, 50]` | AI tick interval x10 |
| 242 | 12 | `[0, 3, 4, 0, 5, 5, 6, 7]` |  |
| 243 | 139 | `[6, 1, 5, 4, 0, 11, 11, 6]` | AI build order type |
| 244 | 139 | `[1, 1, 1, 1, 2, 1, 1, 1]` | AI build max level |
| 245 | 139 | `[51, 40, 48, 51, 50, 40, 40, 58]` | AI build x |
| 246 | 139 | `[21, 25, 37, 29, 14, 32, 40, 9]` | AI build y |
| 247 | 13 | `[0, 0, 7, 16, 16, 29, 44, 63]` | AI build per-level ranges |
| 248 | 12 | `[0, 0, 1, 2, 3, 4, 4, 5]` | level->map |
| 249 | 10 | `[0, 2, 3, 4, 5, 7, 8, 9]` |  |
| 250 | 50 | `[0, 2, 0, 0, 0, 0, 0, 0]` |  |
| 251 | 135 | `[1, 1, 1, 1, 1, 1, 1, 1]` |  |
| 252 | 260 | `[4, 2, 0, 0, 2, 0, 2, 0]` |  |
| 253 | 175 | `[164, 132, 132, 1, 1, 1, 1, 1]` |  |
| 254 | 300 | `[196, 194, 192, 192, 194, 194, 194, 192]` |  |
| 255 | 335 | `[198, 194, 194, 194, 192, 194, 194, 196]` |  |
| 256 | 300 | `[1, 1, 1, 1, 1, 1, 1, 1]` |  |
| 257 | 350 | `[6, 0, 0, 4, 4, 2, 0, 2]` |  |
| 258 | 310 | `[6, 2, 4, 4, 0, 4, 2, 4]` |  |
| 259 | 325 | `[6, 4, 4, 2, 2, 4, 0, 0]` |  |
| 260 | 305 | `[6, 0, 2, 0, 0, 2, 2, 0]` |  |
| 261 | 300 | `[8, 4, 4, 4, 2, 4, 4, 4]` |  |
| 262 | 12 | `[10, 27, 52, 35, 60, 67, 60, 70]` |  |
| 263 | 264 | `[0, 0, 0, 0, 0, 0, 0, 0]` |  |
| 264 | 12 | `[100, 20, 20, 100, 20, 15, 20, 20]` |  |
| 265 | 60 | `[0, 0, 0, 0, 0, 2, 2, 0]` | spawn? |
| 266 | 104 | `[32, 35, 35, 37, 47, 30, 59, 32]` | spawn points A |
| 267 | 13 | `[0, 0, 1, 4, 4, 7, 11, 14]` | offsets->266 |
| 268 | 12 | `[0, 2, 6, 0, 6, 10, 12, 6]` | trap spawn chance |
| 269 | 12 | `[100, 100, 100, 100, 40, 30, 30, 30]` | sanctuary interval x50 |
| 270 | 12 | `[0, 0, 0, 0, 0, 1, 2, 1]` | sanctuary count |
| 271 | 56 | `[17, 43, 20, 45, 27, 43, 35, 46]` | spawn points B |
| 272 | 13 | `[0, 0, 0, 0, 0, 0, 3, 5]` | offsets->271 |
| 273 | 12 | `[0, 40, 35, 0, 30, 25, 20, 25]` | per-level ? |
| 274 | 12 | `[0, 15, 10, 0, 18, 15, 10, 18]` | per-level ? |
| 275 | 12 | `[0, 15, 20, 0, 25, 30, 40, 35]` | per-level ? |
| 276 | 12 | `[0, 20, 30, 0, 30, 35, 45, 40]` | per-level ? |
| 277 | 12 | `[255, 255, 20, 255, 15, 15, 10, 15]` | per-level ? |
| 278 | 12 | `[255, 255, 255, 255, 30, 25, 25, 30]` | per-level ? |
| 279 | 12 | `[2, 3, 2, 4, 3, 2, 3, 3]` |  |
| 280 | 128 | `[90, 91, 92, 93, 94, 95, 96, 97]` |  |
| 281 | 63 | `[0, 10, 20, 30, 40, 49, 58, 68]` |  |
| 282 | 63 | `[0, 6, 12, 18, 24, 30, 36, 42]` |  |
| 283 | 6 | `[12, 13, 14, 8, 8, 8]` | ? |
| 284 | 6 | `[0, 12, 25, 0, 0, 0]` |  |
| 285 | 6 | `[254, 4, 4, 3, 4, 5]` |  |
| 286 | 21 | `[15, 18, 26, 0, 0, 0, 28, 29]` |  |
| 287 | 21 | `[1, 3, 4, 0, 0, 0, 1, 5]` |  |
| 288 | 8 | `[0, 3, 8, 11, 17, 18, 19, 21]` |  |
| 289 | 84 | `[0, 0, 100, 100, 0, 0, 0, 0]` |  |
| 290 | 8 | `[0, 12, 32, 44, 68, 72, 76, 84]` |  |
| 291 | 12 | `[3, 5, 3, 6, 1, 1, 2, 0]` |  |
| 292 | 21 | `[2, 2, 2, 2, 3, 3, 5, 5]` |  |
| 293 | 21 | `[0, 0, 2, 2, 0, 0, 0, 0]` |  |
| 294 | 6 | `[11, 13, 20, 21, 21, 23]` |  |
| 295 | 23 | `[4, 5, 6, 7, 8, 9, 10, 11]` |  |
| 296 | 23 | `[0, 1, 3, 2, 2, 2, 2, 0]` | ? |
| 297 | 23 | `[10, 16, 0, 12, 2, 5, 1, 50]` | ? |
| 298 | 23 | `[10, 5, 5, 20, 10, 20, 20, 50]` | ? |
| 299 | 9 | `[40, 50, 60, 60, 50, 65, 80, 95]` | ? |
| 300 | 9 | `[0, 4, 1, 5, 8, 7, 9, 0]` | ? |
| 301 | 9 | `[64, 63, 65, 65, 68, 66, 69, 64]` |  |
| 302 | 6 | `[0, 0, 0, 4, 4, 9]` |  |
| 303 | 8 | `[0, 0, 32, 39, 49, 55, 55, 59]` |  |
| 304 | 16 | `[255, 0, 0, 253, 253, 0, 252, 252]` |  |
| 305 | 20 | `[5, 6, 7, 8, 9, 10, 11, 12]` | ? |
| 306 | 3 | `[0, 6, 20]` | ? |
| 307 | 2 | `[6, 14]` |  |
| 308 | 1 | `[76]` |  |
| 309 | 76 | `[0, 3, 15, 18, 20, 22, 24, 26]` |  |
| 310 | 142 | `[0, 3, 15, 18, 20, 22, 24, 26]` |  |
| 311 | 687 | `[0, 0, 0, 0, 2, 1, 2, 1]` | ? (largest) |
