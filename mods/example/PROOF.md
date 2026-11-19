# Proof: Green Valley loads and plays in the real game

**Verdict: the mod format works.** The example map `example-map.json`
("Green Valley", 40x32) was encoded with our own encoder, packed into
the original Prehistoric Tribes J2ME JAR in place of level q=11, and
loaded and played in the freej2me emulator: the map appears in the
Custom Game list under its new name, the level loads without a crash,
the player's tribe (11 villagers), buildings, and terrain render, the
HUD shows the correct starting resources, the game ticks, the camera
scrolls, and the in-game menu opens. No original level (q=0..10)
changed.

> The repacked JAR itself is a local test artifact only. It is **not**
> in this repo and must never be uploaded or pushed to GitHub: it
> contains the original game's code and assets. Only the tools
> (`tools/convert_map.py`, `tools/repack_jar.py`) and this note are
> meant for the repo. The original JAR was read from
> `workspace/user/files/prehistoric_tribes_240x320-84398_4_at1w.jar`.

## 1. Which slot was replaced, and why

**Slot: q=11, `ma` piece 9 ("plot of land", custom-only).**

- `ma` piece 0 is shared by q=0 (tutorial, 40x32, uses 43% of the
  piece) and q=1 (campaign mission 1, 64x48, uses 100%). Replacing
  it would break campaign mission 1.
- `ma` piece 4 is shared by q=5 (64x96, 66%) and q=6 (96x96, 100%).
  Replacing it would break campaign missions 5 and 6.
- Pieces 6-9 are used by exactly one level each (q=8..11, all
  custom-only). Piece 9 is the **last** piece, so replacing it cannot
  shift any other piece, and q=11 has no scripted mission events
  (those exist only for q=0..6) and no campaign role. It is reachable
  from the Custom Game menu (segment 249's custom list includes 11).
- No other change was needed for the slot itself: segment 248[11] is
  already 9 (piece index unchanged), and record 279[11] is already 3
  (win/lose flags), exactly Green Valley's flags.

## 2. The encoder (`tools/convert_map.py`)

`convert_map.py` is the inverse of the proven decoder (`decode_ma.py`).
It reads `example-map.json`, validates it against MOD-FORMAT.md §7
(dimensions, tile ranges 0-242, spawn tiles match tiles 174+type,
player_start in bounds, win/lose booleans match flags), and encodes
tiles to `ma` RLE: byte < 250 is one literal tile, byte 250+k repeats
V[k] for T[k] tiles, with T=[4,4,2,2,2,2], V=[3,0,43,6,3,0] (segment
197 control table). `--verify` round-trips the output through an
independent decoder mirror; `--roundtrip` cross-checks with the
proven `decode_ma.decode_map`.

Results:

- Green Valley encodes to **399 bytes** (0.31 bytes/tile) for 1,280
  tiles. Round-trip: 1,280/1,280 tiles identical. Proven-decoder
  cross-check (q=11, piece 9): decodes to exactly the Green Valley
  grid, consuming 399 bytes (12.6% of the piece).
- Strongest validation: encoding the **original** maps q=0, q=1, q=2
  reproduces the original `ma` streams **byte-for-byte identical**
  (1,102 / 2,545 / 4,420 bytes). q=11 encodes to 3,152 bytes vs the
  original 3,167 (round-trip exact, so still a valid encoding).

## 3. Repack steps (`tools/repack_jar.py`)

Built locally in `repack-work/` (never in `repo-push/`). The original
JAR is copied entry by entry, preserving order, compression,
timestamps, and the manifest; only three files change, all with
**unchanged sizes**:

| File | Size | Change |
| --- | --- | --- |
| `ma` | 42,381 | Piece 9 [39214..42381) replaced by the 399-byte Green Valley encoding + zero padding to the original piece length (3,167). Piece offsets are hardcoded in the game code, so the length must not change; bytes past the decoded stream are never read (decoding stops after w*h tiles). |
| `/a` | 18,842 | Segment 149, pair q=11: (64,64) -> (40,32) — map dimensions. Segment 150, pair q=11: (14,44) -> (8,21) — camera/cursor start (see §4). Segment 261, the q=11 level-setup table (60 entries): every entry keeps (v0, v1, v4) and only (x, y) changes by proportional scaling (x*40//64, y*32//64), then nudged to the nearest valid cell. Segment 279 and 248 unchanged (see §1). |
| `0/s` | 1,734 | English text: "plot of land" -> "Green Valley" (both 12 characters). Only q=11 displays name index s[91], so no other screen is affected. Cosmetic only. |

Setup-table remap: **35 villagers + 25 buildings, 20 nudged** to
nearby valid cells (causes: scaled positions landing on spawn tiles,
e.g. Store entry 13 scaled (34,4) hit spawn tile 176 at (5,34); and
scaled footprints overlapping each other, e.g. Hut entry 28 scaled
(30,2) colliding with Kitchen entry 19 at (29,3)), **0
unplaceable**. Without the remap, all 60 starting villagers/buildings
would spawn outside the 40x32 map (original coordinates reach x=58,
y=52), leaving the player with no visible tribe and enemy buildings
that could never be destroyed (the win condition).

Repacked JAR: `prehistoric_tribes_green_valley.jar`, 496,111 bytes
(original 498,387 — smaller only because DEFLATE recompression
differs). Static verification (built into `repack_jar.py`, all
passed): valid zip; manifest byte-identical; all 7 `.class` files
byte-identical (sha256); every other file byte-identical; `ma` and
`/a` sizes unchanged; q=11 decodes to exactly the Green Valley grid
via the proven decoder; **q=0..10 decode exactly as before**.

## 4. The bug found during testing, and the fix

**First repack: the map loaded but the viewport was mostly black**,
with only a small wedge of green grass and rocks visible at the
bottom-left. The HUD was correct (11/1 population, 10/20/10/5
resources), the game ticked, and the in-game menu opened — so the
data loaded, but the terrain did not render.

Diagnosis (from the game code in `f.java` and controlled
experiments):

- The game only draws terrain the player's tribe has "seen" (fog of
  war): a visibility radius around the player's villagers/buildings,
  recorded in bit arrays (`f.java` `a(int,int)`) and applied by the
  dirty-tile redraw loop (`c()` / `o()` / `n()`). The visible region
  is a rounded blob centred on the tribe; outside it the buffer stays
  black.
- The original q=11 has its camera start (segment 150: 14,44) right
  next to its tribe spawn (player villagers at 12-16, 42-45), so it
  renders fully. Our first repack put the camera at the map's
  `player_start` (15,5) while the remapped tribe spawns at (7-10,
  21-22) — far away — so only a sliver of the tribe's visible region
  peeked into the viewport.
- The encoder was exonerated by a control: variant B (the same Green
  Valley encoding padded to 64x64, with `/a` and `0/s` untouched, so
  the camera stayed next to the tribe) renders fine. The original
  40x32 map q=0 also renders fine, so the map size is not the cause.

**Fix:** segment 150[11] is set to the centroid of the remapped
player villagers, **(8,21)** (chief's hut is at (8,18)), instead of
`player_start`. The camera now starts on the tribe, and the map
renders like the original. This is implemented in `repack_jar.py`
(`player_tribe_centroid()`); the tool's docstring explains it.

**Consequence for the format:** in the J2ME repack, `player_start`
is *not* where the camera starts, because the tribe's position comes
from the inherited q=11 setup table (remapped), not from the JSON. A
future loader that spawns the tribe at `player_start` can use it for
the camera as well. MOD-FORMAT.md should gain a note to this effect
when the loader is designed.

## 5. Emulator verification (freej2me)

Environment: freej2me built from source (GitHub `hex007/freej2me`,
Apache Ant 1.10.14, Temurin JDK 17) on Xvfb display :99, driven by a
`java.awt.Robot` script (`repack-work/EmuDriver.java`) that sends
keys and takes screenshots. (freej2me has no releases; it was cloned
and built. AWT needed `libXtst.so.6`, installed from a single
`.deb`.)

**The tutorial gate.** Custom Game is locked until the tutorial is
passed: selecting it shows "PASS THE TUTORIAL FIRST!" (text `t[70]`).
The gate is in `f.java` `aw()`: it opens the map list only if
`r > 0` (or the `af` flag), where `r` is the "highest unlocked level"
byte loaded from the `t0` RecordStore. Playing the whole tutorial
(67 guided steps) was not practical by blind key presses, so the
gate was unlocked by seeding freej2me's `t0` RecordStore with `r=1`
(record = int `l`=0, boolean `W`=false, byte `r`=1, bytes
`s/t/c/p`=0 — the game's own save format, verified against the
save/load code in `f.java`; freej2me's RMS file format is: version /
nextid / count as big-endian u16, then per record a u16 length +
bytes). This simulates a passed tutorial; it changes no map data.
Note for phone testing: on a real phone the user must either pass
the tutorial or use a seeded save to reach Custom Game. The cheat
sequence (8,7,3,9,1,…) exists in the code but is **dead in this
build** — its enabling boolean is never set to true, and the manifest
says `Cheat-Support: off` — so it cannot unlock the gate, in menus
or in-game.

**What was observed with the fixed repack:**

- Boots identically to the original (same splash, language select,
  "PLAY MUSIC?", main menu).
- Custom Game opens (no gate message), difficulty select (EASY),
  then the map list — last entry reads **"GREEN VALLEY"** (the
  original JAR shows "PLOT OF LAND" in the same position; verified
  side by side).
- Selecting Green Valley loads the level: HUD shows **11/1**
  population and **10/20/10/5** resources (food/wood/stone/bones),
  matching the remapped setup table; green grass terrain, the tribe
  (villagers + chief), the Store building, a rock cluster, and a
  berry bush are visible; the game ticks (2,812 pixels change over
  4 seconds — villagers animating); arrow keys scroll the camera;
  the in-game menu (Q) opens the BUILD menu. No crash, no exception
  in the emulator log.
- **Controls (same emulator, same steps):** the original q=11
  ("plot of land", 64x64) renders fully with the same HUD numbers;
  the original q=0 tutorial map (40x32) renders fully; variant B
  (64x64 Green Valley, untouched `/a`) renders. So the rendering
  behaviour of the repack is at parity with the original.

**Known rendering quirk (not a mod defect):** the viewport corners
stay black in freej2me — the visible region is a rounded blob, not
the full rectangle. This happens with the **original** JAR too
(same black corners on q=11 and q=0), so it is a property of the
game's rendering under freej2me (fog-of-war radius and/or the
emulator's handling of the game's scrolling double buffer), not
something the mod introduced. A real-phone test (J2ME Loader) is
still needed to see the full map the way a player would.

## 6. Limits and residual unknowns

- The exact meaning of the `a(x,y)==0` mask in the building
  placement validity check (`f.java` `a(n,n2,n3,bl)`) is still
  unproven (most likely a per-cell "already built on" flag; fresh
  open cells pass). The remap only places buildings on cells its own
  occupancy model marks free, and the emulator run shows the
  buildings present, so this did not block the proof.
- The visibility/fog-of-war radius is inferred from behaviour plus
  the bit-array and dirty-tile code, not proven to an exact radius.
  The enemy tribe's visibility does not reveal terrain to the player
  (observed: enemy villagers inside the viewport did not light it).
- Win/lose on the modded map was **not** tested end-to-end (it would
  need playing until victory or defeat). The flags are correct
  (record 279[11]=3, destroy-to-win + population-lose, same as the
  original q=11), and the enemy buildings were remapped into the map
  so the win condition is reachable in principle.
- Emulator key delivery via `java.awt.Robot` is flaky: a 120 ms key
  hold could register 0, 1, or 2 times per press (the game polls key
  state per tick). Shortening the hold to 45 ms made single presses
  reliable. Every navigation step above was confirmed with a
  screenshot before proceeding.
- Only the English text file (`0/s`) was renamed. The other four
  languages still say "plot of land" for q=11.

## 7. What still needs a real phone test

- Load the repacked JAR in J2ME Loader on Android and play Green
  Valley: confirm the full map renders (no black corners), build a
  building, gather wood/stone, survive a wave, and reach a win/lose
  verdict.
- Confirm the Custom Game gate on a real phone (pass the tutorial
  once, or use a seeded save) and that the renamed map appears.
- Long-term: the Android loader (the real goal of the mod format)
  should spawn the tribe at the JSON's `player_start` and start the
  camera there, so the format's `player_start` means what it says.

## 8. Files

- `tools/convert_map.py` — the map encoder (new, our own code).
- `tools/repack_jar.py` — the JAR repacker, including the setup-table
  remap and the camera-on-tribe fix (new, our own code).
- `mods/example/PROOF.md` — this note.
- Local only, **not** in the repo: `repack-work/` (the repacked JAR
  `prehistoric_tribes_green_valley.jar`, the `variant_b/c/d` test
  JARs, `build_variants.py`, `build_variant_d.py`,
  `repack-report.json`, the freej2me build, the Xvfb/emulator
  screenshots in `shots-new/` and `shots-orig/`, and the seeded
  `t0` RecordStore files under `shots-*/rms/`).
