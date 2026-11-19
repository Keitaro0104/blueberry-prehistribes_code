# Android Port Plan — Prehistoric Tribes (J2ME → Native Android)

English. Design document only — no app code, no push. Sources: the research in
this repo (`PETA-SISTEM.md`, `PD0-ANALYSIS.md`, `MA-MAPS.md`,
`DECODE-REMAINING.md`, `task-table.csv`) and the mod format (`mods/format/MOD-FORMAT.md`).

Goal: a native Android reimplementation of Prehistoric Tribes (THQ / Gear Games,
2008) that is **touch-first** (Clash of Clans / Art of War style — no D-pad
cursor at all) and **moddable without repacking**: mods are JSON + PNG files in
a folder on the phone, loaded at runtime.

---

## 0. What is being ported, in one paragraph

A real-time 2D tile village strategy game. Two tribes (player + enemy) on a grid
map up to 96×96 tiles, tiles 22×16 px, camera showing 11×18 tiles in the
original. Max 50 villagers and 30 buildings per tribe. 12 building types, 6
weapons, 3 traps, 4 resources (food, wood, stones, bones) plus weapon stock.
Game loop ~20 ticks/second (50 ms/tick). Fog of war: only terrain the player's
tribe has seen is drawn (proven by the repack work — a camera parked over
unseen terrain renders black). Win/lose is decided by `b.ak()` (not `b.k()`):
win when enemy buildings reach 0 and the mission flag allows it, lose when
player population reaches 0 or a key building is lost where the mission
requires it; the verdict lands ~40 ticks (~2 s) after the condition arms
(`u == 41` win, `u == 90` lose). The original input was a D-pad cursor plus
softkeys. There was no touch input at all.

## 1. Engine choice

### 1.1 Candidates

| | Kotlin + Android Canvas / View | libGDX (Kotlin) | Godot 4 |
|---|---|---|---|
| What it is | Hand-rolled: `SurfaceView` + `Canvas.drawBitmap`, own loop, own gestures | Mature 2D game framework: `SpriteBatch`, `OrthographicCamera`, gesture detectors, desktop + Android backends | Full game engine with visual editor, GDScript/C# |
| 2D tile rendering | Manual, but trivial at this scale (~200 visible tiles + ~100 entities per frame) | Solved: batched quads, camera + zoom built in | TileMap node, but a different model from the original's per-tile blit |
| Touch / camera | Hand-roll `GestureDetector` + `ScaleGestureDetector` | `GestureDetector` + `InputMultiplexer` built in; pinch/pan/double-tap are one-liners | Built in, but wired through the scene tree |
| Game-loop fidelity | Full control; fixed 50 ms timestep is easy | Full control; fixed timestep is easy | Fixed physics tick exists, but the simulation would be re-expressed as nodes/signals |
| Mod folders from storage | Plain file I/O | Plain file I/O | File I/O via `FileAccess`; workable but less direct |
| Build on GitHub Actions | Plain Gradle + Android SDK; fastest CI (~3–5 min with cache) | Same Gradle + SDK, plus one dependency download; ~same cost | Needs Godot binary + Android export templates (~1 GB downloads), slowest CI, cache-invalidation pain |
| APK size | Smallest (no engine) | +~5–8 MB | +~15–30 MB |
| Fit for a solo non-coder + AI | Most code to write by hand (loop, batching, camera math) | Least hand-rolled infrastructure; logic stays close to the original Java | Most paradigm shift; the simulation must be re-thought as scenes, hardest for AI-assisted vibe-coding to keep faithful |
| Test without a phone | Emulator only | **Desktop backend runs the same code on JVM** — CI can boot the game headless and take screenshots | Headless run is possible but heavier to set up |

### 1.2 Recommendation: **libGDX with Kotlin**

Reasons, specific to this game:

1. **It is a 2D tile game, and libGDX is built for exactly that.** Camera,
   zoom, batched sprite drawing, and gesture input are solved problems
   there; in raw Canvas they are all hand-rolled code the project has to
   maintain.
2. **The original code is Java; Kotlin interoperates with it
   conceptually.** The simulation logic (`b.java`, 5,805 lines) maps to
   Kotlin classes almost line-for-line in structure. GDScript would force a
   re-think of the whole simulation as nodes.
3. **The desktop backend is the test path.** The user has no PC, so builds
   and tests run on GitHub Actions and on the phone. libGDX's desktop
   backend lets CI run the game headlessly (the same trick already proven
   with freej2me + Xvfb in the repack work) and take screenshots — the
   Canvas route can only be tested on an emulator or a phone.
4. **CI cost is the same as the Canvas route** (Gradle + Android SDK,
   dependency cache), and far below Godot's.

Close second: Kotlin + Canvas. If libGDX ever becomes a problem, the
simulation modules (§2) are written against plain Kotlin interfaces, so the
renderer can be swapped without touching game logic. Godot is not
recommended for this port.

**Package / module name (suggestion, not final):**
`com.keitaro0104.blueberrytribes`, minSdk 26, targetSdk 35, Kotlin,
Gradle (Kotlin DSL). Same conventions as the sibling FreeSO Android
project, so the user already knows the build shape.

## 2. Architecture

### 2.1 Modules and their original counterparts

| Android module | Original | Responsibility |
|---|---|---|
| `GameLoop` | `f.run()` (f.java:485–540) | Fixed timestep: 50 ms/tick, 20 ticks/s. Each tick: pause/music check → update → draw → sleep remainder. Use an accumulator so a slow frame never fast-forwards the simulation. |
| `WorldSim` | `b.java` (5,805 lines) | The whole simulation: two terrain/occupancy grids, villagers, buildings, economy, combat, enemy AI, waves, scripted events, `ak()` win/lose. Owns the tick. |
| `Renderer` | `f.m()` + `paint()` | Draws the visible tile window, entities, selection rings, HUD. One `SpriteBatch` draw per frame; no per-tile object allocation in the hot path. |
| `ResourceLoader` | `e.java` (280 lines) | Loads base data (see §2.3) and mod data (§4). |
| `AudioPlayer` | `a.java` (118 lines) | Music. See §2.4. |
| `TextStore` | `c.java` (404 lines) | UI strings. Ship English strings from the decoded `s`/`t`/`d0` counts; full 5-language support is M5+ work. |
| `SaveManager` | RecordStores `t0`/`t1`/`t2` | App-private files; see §2.5. |
| `ModLoader` | — (new) | Scans the mods folder, validates, loads (§4). |
| `TouchInput` | `f.V()` + `keyPressed` | Gesture → command translation (§3). Replaces the D-pad code entirely. |

### 2.2 Data model — do not copy the original's memory layout

The original stores villagers as numbered slots in parallel `byte[]` arrays
(entity field *i* of villager *v* at `entity[i*101 + v]`, group-0 offsets in
file-`a`). That was J2ME memory frugality. On Android, use plain Kotlin
data classes — `Villager`, `Building`, `Tribe` — with named fields. The
simulation rules stay the same; only the storage changes. This is the
single biggest readability win of the port, and it is what makes the code
teachable to a non-coder.

Keep the original's **ordering guarantees** inside a tick, because behaviour
depends on them: `b.e()` processes both tribes in turn (player then enemy),
then `b.g()` processes buildings. Keep that order.

Keep the original's **fixed RNG seed** (`new Random(1L)`) for load-time
tile jitter (base tiles ≤ 8 get +0..2 at load) and for combat rolls, but
split it into two streams — one for deterministic load/gameplay, one for
cosmetic variation — so a bug fix in one does not shift the other.

### 2.3 Base data — "bring your own JAR"

**The port must not bundle the original game's data.** The 12 original maps,
the balance tables (`pd0`, file `/a`), the sprite packs (`pi0`/`pi8`/`pi9`),
the MIDI (`sa`) and the texts are THQ/Gear Games content. Shipping them in
an APK would be redistributing the game.

Design decision (same pattern as the sibling FreeSO project):

1. First run asks the user for their own copy of the original JAR
   (file picker, SAF — the same pattern already used in FreeSO).
2. The app extracts `ma`, `/a`, `pd0`, `pi0`/`pi8`/`pi9`, `sa`, `s`/`t`/`d0`
   and converts them **once, on device**, using the already-proven Python
   decoders ported to Kotlin (RLE in `MA-MAPS.md` §1, `/a` record layout in
   `DECODE-REMAINING.md` §2, concatenated-PNG split in `DECODE-REMAINING.md`
   §1) into app-private JSON/PNG assets.
3. After that the game runs from the converted assets; the JAR is never
   needed again.
4. What the port **does** ship: the engine, the Green Valley example mod
   (user-created content), the map editor's output format, and placeholder
   art for anything not yet converted. A fresh install with no JAR still
   opens and can play Green Valley — that is the M1 demo path and the
   legal-safe default.

### 2.4 Rendering

- Base tile size 22×16 px (original). The renderer scales by camera zoom;
  at zoom 1.0 the view shows ~11 tiles across, exactly like the original
  240 px screen (11 × 22 = 242). On a 1080 px-wide phone that means tiles
  of ~98 px — big, readable, tappable (see §3).
- Draw order per frame: terrain tiles in the camera window → spawn
  objects → buildings → villagers → projectiles → selection ring/HUD.
  This mirrors the original `f.m()` order.
- **Tile-ID → sprite-region mapping is an M1 prerequisite, not a given.**
  The decoded docs prove which tile IDs are blocked/walkable and which are
  spawns, but **not** which picture each of the ~200 tile graphics is
  (grass/water/forest/rock). Before M1 can render real terrain, someone
  must trace the tile blit in `f.java` (which image region a tile ID
  indexes) and render the atlases to match. M1 therefore ships with
  **coloured placeholder tiles** keyed only to proven classes
  (walkable / blocked / spawn / class-2), and swaps in real art once the
  mapping is proven. This is deliberate: M1 is not blocked on art.
- Fog of war: keep two boolean grids, `explored` (seen ever) and
  `visible` (seen now), rebuilt each tick the way `b.d()` rebuilds the
  original visibility bitmask. Renderer rule (observed in the repack
  work): unseen = black, seen = drawn. Whether explored-but-not-currently-
  visible tiles are drawn dimmed or black is **unproven** — M1 uses
  black for both, and the exact behaviour is a §6 item to verify against
  the original.
- The original double-buffered into a 264×304 off-screen image and blitted
  with offset (−11,−8). On Android there is no need for this: draw
  straight to the screen. Do not reproduce the buffer dance.

### 2.5 Saves

Original: RecordStores `t0` (settings + campaign progress, incl. `r` =
highest level unlocked), `t1` (campaign save), `t2` (custom save); one
record each, written in exact field order with `DataOutputStream`, delete-
then-create on overwrite, corrupt save deleted and retried.

Android mapping: app-private files `t0.bin`, `t1.bin`, `t2.bin`, keeping
the **same field order** so a save can be reasoned about against the
original format. Settings that are purely Android-side (music on/off,
zoom level, enabled mods) go in DataStore, not in `t0`. Keep the
original's no-autosave rule for M1–M4 (manual save + save after a
mission ends); autosave is optional polish later.

### 2.6 Audio

Original: class `a` plays MIDI only — 5 songs concatenated in `/sa`
(lengths 8014/6315/5648/3405/3234), picked at random, checked every tick.
Android has no MIDlet MIDI player.

Plan: **M1–M4 ship muted** (a music toggle in settings that is wired but
plays nothing yet — labelled honestly in the UI). For M5, split `/sa`
into its 5 chunks at JAR-import time, verify each chunk is a valid
standard MIDI file, render each to OGG offline with a software synth
(FluidSynth/TimGM soundfont), and play with Android `MediaPlayer` /
libGDX audio. If a chunk is not valid SMF, fall back to silence and log
it — never crash on audio. No sound effects exist in the original
(no SFX class), so none are added.

## 3. Touch controls — Clash of Clans / Art of War style

### 3.1 The one rule

**The D-pad cursor is gone. There is no cursor.** In the original, a
cursor tile was moved with the D-pad and everything — select, command,
build — happened *at the cursor*. On Android, the player's finger *is*
the pointer. Nothing in the UI moves a cursor, and no code path needs
one. Every interaction below is a direct manipulation of the thing
touched.

### 3.2 The control scheme (5-line version)

1. **Tap** a villager or building to select it (bottom sheet: name, HP,
   role, actions); **tap** ground with a selection to order move/gather.
2. **Drag** with one finger to pan the camera; **pinch** to zoom
   (0.5×–3×); **double-tap** to centre on your tribe.
3. **Bottom bar:** Build, Groups, Pause, Menu — the only on-screen
   buttons; everything else is direct touch on the map.
4. **Tap vs drag:** a touch that moves < 12 dp and lifts within ~150 ms
   is a tap; beyond that it is a pan and the tap is cancelled.
5. **Zoom default shows ~11 tiles across** (the original framing), so a
   tile is ~98 px on a 1080 px phone and a 1×1 tower is still tappable.

### 3.3 In detail

| Gesture | Action | Original equivalent |
|---|---|---|
| Tap villager | Select it (task 105 "held" state). Bottom sheet: name, age, gender, HP, role, needs (happiness/hunger/tiredness), current task. Actions: assign role, send to building, dismiss. | D-pad to cursor + centre key |
| Tap building | Select it. Bottom sheet: type, level, HP, actions: upgrade, repair, demolish. Build requirements shown ("need resources!", "we need a cook…"). | Same, via cursor |
| Tap ground, with a villager selected | Command: move there / gather there / work there. Pathfinding is the original's: 8 directions, max 80 steps, try another direction if blocked. | Same, via cursor |
| Tap ground, nothing selected | Deselect. (No tile-info popup in M1; optional later.) | Right softkey / cancel |
| Tap enemy / wild animal, with a warrior selected | Attack command (melee or throwing by weapon/range). | Same, via cursor |
| One-finger drag | Pan camera. Smooth scroll, clamped to map edges. | D-pad held (scroll) |
| Pinch | Zoom 0.5× (about 22 tiles across, overview) to 3× (about 4 tiles across, detail). Zoom centres on the pinch midpoint. | No equivalent (new) |
| Double-tap | Centre camera on your tribe (chief position, falling back to the centroid of your villagers — the same centroid rule proven by the repack camera fix). | No equivalent (new) |
| Build button (bottom bar) | Opens the build menu (the original's left-softkey menu, `w=2`): 12 buildings + 3 traps, with cost and requirements. Tap a building, then tap the ground to place it. | Left softkey |
| Groups button / group chips | The original has numbered groups (keys 1/3/7/9/0; the `p[]` array holds a group's villager slots, and commands apply to the whole group). Android shows group chips (1–5) above the bottom bar: tap a chip to select that group, long-press a selected villager to assign it to a group. | Number keys |
| Pause button (top-right) | Pause screen (original Q 10/11): resume, save, load, quit. | Right softkey |
| Menu button | Main menu (original Q 14): play, help, options, about, exit. | System / softkey |

### 3.4 Tap-vs-drag disambiguation

Use libGDX `GestureDetector` plus a custom pan handler:

- On `touchDown`, record position + time. Do nothing yet.
- If the pointer moves more than **12 dp** before lifting, it is a pan:
  cancel any pending tap, move the camera with the drag delta.
- If it lifts within **~150 ms** and under 12 dp, it is a tap: pick the
  entity at that point (see §3.5) and act.
- Pinch (two pointers) cancels any pending tap and any in-progress pan;
  on pinch end, resume normal input. Double-tap is `GestureDetector`'s
  `tap` + `onDoubleTap` — a double-tap must not also fire two single
  taps (use the detector's double-tap timeout to defer single-tap
  handling by ~200 ms; this is standard and worth the tiny latency).

### 3.5 Small tiles and fat fingers

- At default zoom (11 tiles across on a 1080 px phone) a tile is ~98 px
  ≈ 50 dp — comfortably above Android's 48 dp minimum touch target.
  A 1×1 tower is therefore tappable at default zoom.
- At 0.5× zoom a tile is ~25 dp: too small to hit reliably. Picking
  therefore uses **nearest-entity within 24 dp** of the touch point,
  preferring villagers/buildings over bare ground, and the selection
  ring + bottom sheet confirm what was actually picked. If the wrong
  thing is picked, the next tap corrects it — no harm done.
- Buildings occupy up to 6×4 tiles, so they are easy targets at any zoom.
- The bottom sheet and bottom bar sit in a fixed UI layer; touches on
  them never reach the map. The map area is everything above the bar.

### 3.6 Multi-select — what the original has, and what is new

- **Original:** single-villager tap-select (task 105) **plus** numbered
  groups (`p[]` array; commands apply to the whole group). There is **no**
  drag-box multi-select in the original — confirmed by the code, which
  has no rectangle-selection path.
- **Android (M1–M4):** keep the original model — tap-select one, group
  chips for many. Do not add drag-box select: one-finger drag is already
  camera pan, and a box-select gesture would fight it.
- **Optional later (M5+ polish, not a faithful-port requirement):**
  a two-finger drag box-select, or a "Select mode" toggle that turns
  one-finger drag into a selection box instead of a pan. Only if the user
  asks for it — Clash of Clans itself is tap-only per unit, and that is
  the closer model for this game.

### 3.7 HUD

Top bar (always visible): food / wood / stone / bones counts, weapon
stock, villager count (n/50), building count (n/30), mission progress.
Do **not** reuse the original `pi0[25]` bitmap digit strip — native text
rendering is clearer and free. Keep the original's messages
("enemy sighted!", "we're under attack!", "building is lost!") as
transient toasts in the same wording.

## 4. Mod loading on Android (no repack)

### 4.1 Folder layout

```
<app files dir>/mods/
  green-valley/                 # example mod, ships with the app
    mod.json
    maps/green-valley.json
    buildings/large-hut.json
  <any other mod folder>/
    mod.json
    maps/*.json
    buildings/*.json
    sprites/*.png               # v0.1: referenced by name; loading rules §4.4
```

Concrete path on the phone (app-private external files, no root needed):
`Android/data/com.keitaro0104.blueberrytribes/files/mods/`. This is
reachable from a file manager and over USB, so the user can copy mod
folders in without any tool. In addition, the app offers **Import mod**
via the SAF folder picker (the same pattern already used in the FreeSO
project) for phones where the file manager cannot see the folder.

### 4.2 Load flow

1. At startup (and on "Rescan" in the Mods screen), scan `mods/` for
   folders containing `mod.json`.
2. Parse each manifest; reject (with a readable error shown in the list,
   never a crash) any mod whose `format_version` is not `"0.1"` or whose
   `game` is not `"prehistoric-tribes"`.
3. Validate every content file against `MOD-FORMAT.md` §7 (map size
   1–96, `tiles` exactly height×width, tile IDs 0–242, spawns match
   tiles 175–179, `player_start` on a walkable tile, `win_lose` flags
   consistent, building `base_type` 0–11, HP > 0, costs ≥ 0).
4. Valid mods appear in the Mods list with name/author/description and
   an enable toggle. Disabled mods are ignored. Invalid mods appear
   greyed out with their validation error.
5. Enabled mods' maps appear in the Custom Game list alongside the
   built-in maps; enabled building variants replace/extend the build
   menu (a variant *replaces* its `base_type`'s stats when enabled —
   the v0.1 rule from the format spec; stacking two variants of the
   same base type is an error shown in the list).
6. A map is loaded when selected: JSON → in-memory grid, with the
   original `aN()` post-processing reproduced (tiles 180–231 get
   marker −124, class-2 tiles get −125, border cells −126; +0..2 jitter
   on base tiles ≤ 8 from the seeded RNG). No conversion to binary, no
   rebuild, no restart: quitting to the map list and re-entering picks
   up an edited file.

### 4.3 Map-editor flow (end to end, no repack)

```
Map editor (web) → export green-valley.json (format 0.1)
  → copy into  mods/<mod-name>/maps/  (file manager, USB, or in-app Import)
  → open game → Mods → mod appears → enable
  → Custom Game → the new map is listed → play
```

The editor's JSON **is** the mod file — there is no conversion step
between editor and game. The only human step is copying a file, and
the in-app Import button removes even that. Compare with the J2ME
path (editor → JSON → Python encoder → repacked JAR → install), which
the editor flow replaces entirely.

### 4.4 Sprites in mods (v0.1: reference only)

`sprite_ref` (e.g. `"pi0[01]"`) is stored and displayed, but custom
sprite loading is **not** defined in format v0.1. A mod PNG in
`sprites/` is validated as a PNG and listed, but M5 does not yet swap
it into the game — that needs the tile-ID → sprite-region mapping
(§2.4) and a per-entity sprite index table, both open items (§6).
Do not promise sprite mods before M5.

### 4.5 Validation failures must be boring

A bad mod shows one line in the Mods list ("green-valley.json:
tiles row 3 has 39 columns, expected 40") and the game continues with
the other mods. A bad mod must never crash the game, never corrupt a
save, and never block startup. This is a design requirement, not
polish — a solo user will hit bad JSON often while learning.

## 5. Milestone plan (M1–M5, one PR each)

Each milestone is one branch + one PR, small enough to review, with a
concrete done-criterion that can be checked on the phone or in CI.

### M1 — Render Green Valley + camera + touch pan/zoom

- **Scope:** libGDX skeleton, `GameLoop` at 20 ticks/s, `Renderer`
  with placeholder tiles (proven classes only), `ResourceLoader`
  reading the bundled Green Valley JSON, camera (pan/zoom/double-tap
  centre), HUD shell (resource bar, no live values yet).
- **Done when:** the app opens to Green Valley rendered from its JSON;
  one-finger drag pans, pinch zooms 0.5×–3×, double-tap centres on
  the tribe; no crash on rotate/background; GitHub Actions build green.
- **Explicitly not in M1:** villagers, buildings, combat, real terrain
  art, audio, saves, mods folder.

### M2 — Villagers move and gather

- **Scope:** `WorldSim` villager model (position, age, gender, HP,
  needs, task codes), tap-select + bottom sheet, tap-ground command,
  8-direction pathfinding (max 80 steps, as original), gather tasks
  10–16 adding to stock, HUD stock counts live.
- **Done when:** tap a villager → its info sheet opens; tap ground →
  it walks there and arrives; send it to a resource → stock increases;
  villager count shows n/50.

### M3 — Buildings construct and upgrade

- **Scope:** build menu (12 types + costs from record 138 via the
  converted base data, or from the bundled Green Valley mod's
  building file), placement on tapped ground, construction, upgrade
  (HP/cost per level), repair, demolish, living-space rule (hut +4,
  cap 50), max 30 buildings enforced with the original "max buildings"
  message.
- **Done when:** a hut can be built (cost deducted), upgraded (HP
  rises per level), repaired and demolished; building count shows n/30;
  building without resources shows "need resources!".

### M4 — Combat, waves, win/lose

- **Scope:** enemy AI (build/upgrade/attack with the same systems),
  wave timer and growing attacker counts, tower/scout defence, traps,
  melee + parabolic throwing combat (records 102/124/159), wild
  animals, `b.ak()` win/lose with the 40-tick verdict and the
  mission-end screen (Q 24), campaign advance `q++` on win.
- **Done when:** an enemy wave arrives with the "enemy sighted!"
  warning, combat resolves with damage, and destroying all enemy
  buildings on a flags=3 map shows "hurrah! you've won!" after ~2 s
  while losing all villagers shows "you have lost!".
- **Known deviation to decide in M4:** the q=5 win anomaly (winning
  q=5 does not advance in `aq()` — bytecode-proven). Decision:
  **reproduce the original behaviour and note it in the UI**
  ("mission complete" without advance), rather than silently fixing
  it — the original is the reference, and a fix is a one-line change
  later if the user wants it.

### M5 — Mod loader + mod list UI

- **Scope:** `ModLoader` (§4), Mods screen (list, enable/disable,
  validation errors), Custom Game listing mod maps, building-variant
  override, in-app Import (SAF), rescan.
- **Done when:** a second map JSON dropped into the mods folder
  appears in Custom Game **without rebuilding the app**; an invalid
  mod shows its error and the game keeps working; the map editor's
  exported JSON loads end-to-end through this flow.

**After M5 (not in this plan):** campaign scripted events (21 events,
records 286–302) for missions 0/2/3/5 win conditions, real terrain art
once the tile mapping is proven, audio (MIDI→OGG), full 5-language
texts, drag-box multi-select (only if asked), autosave.

## 6. Risks and unknowns

| # | Risk / unknown | Impact | Mitigation |
|---|---|---|---|
| 1 | **Sprite format.** `pi0`/`pi8`/`pi9` are concatenated PNGs (2-byte BE length prefix, `0xFF` terminator) — the split is proven (`extract_pngs.py`, 45 PNGs). But **which picture each tile ID is** is unproven, and which atlas region each building/villager sprite uses is unproven. | M1 cannot render real terrain; M2–M3 cannot render real entities. | M1 uses placeholder tiles (proven classes only). Separate task before M2: trace the tile/entity blit in `f.java` and render the atlases to build the ID→region map. |
| 2 | **Fog-of-war radius unproven.** `b.d()` rebuilds a visibility bitmask, but its exact radius/shape is not decoded. | Renderer may reveal too much or too little vs the original. | M1: reveal = tiles the tribe has seen (observed behaviour). Verify against the original in an emulator side-by-side; tune the radius as a single constant. |
| 3 | **Spawn types 1–5 meanings unproven.** Tiles 175–179 register 5 kinds of map objects with args `[20,20,20,15,25]` (record 110); what each places (resource node? fishing spot?) needs the `b.java` consumers of the 50-slot object list. | Spawn tiles in mod maps may do nothing, or the wrong thing. | M2 task: trace the consumers before wiring spawns into gameplay. Until then, spawns render as markers and are inert. |
| 4 | **Audio / MIDI.** `/sa` is 5 concatenated chunks; whether each is valid standard MIDI is unproven, and Android has no MIDI player. | M1–M4 are silent (accepted, §2.6). | M5: split + validate chunks, render to OGG offline, `MediaPlayer`. Never crash on audio. |
| 5 | **Performance on low-end phones.** The simulation is tiny (96×96 grid, ≤100 villagers, ≤60 buildings, 20 ticks/s) — the risk is rendering, not logic. | Jank on old devices if drawing is naive. | `SpriteBatch` + no per-frame allocation; cull to the camera window (~200 tiles); profile on the user's vivo (Android 16) at M1. |
| 6 | **Scoped storage (Android 11+).** The mods folder must be reachable without root and without a PC. | User cannot install mods. | App-private external files dir + SAF import (§4.1); test the copy path on the real phone at M5, not in the emulator. |
| 7 | **CI build cost.** Gradle + Android SDK on GitHub Actions; libGDX adds a dependency download. | Slow PR feedback. | Cache Gradle + SDK + dependencies (the FreeSO project already does this); keep the app to one module. |
| 8 | **Campaign win conditions.** Missions 0, 2, 3, 5 have no destroy-to-win bit; their wins live in the 21 scripted events (records 286/287/296/297/298, handlers `b.v()`/`b.u()`), not yet fully decoded. Record-279 bit 4 (mission 3) is never tested in `ak()`. | M4 can only prove win/lose on flags=3 maps and wipe-out loss. Campaign is incomplete. | M4 scope is custom-game win/lose; campaign events are a named follow-up milestone (M6), not hidden inside M4. |
| 9 | **The q=5 win anomaly** (see M4). | A player winning mission 5 gets no advance — looks like a bug. | Reproduce + note it; fix later only on the user's decision. |
| 10 | **Multi-select expectation.** Players coming from CoC/Art of War may expect drag-box select; the original has none. | UX complaints, not a crash. | Documented in §3.6; group chips are the faithful answer; box-select only if the user asks. |
| 11 | **Balance data fidelity.** All costs/HP/damage live in `pd0` + file `/a` record 138; the decoded values are verified, but the wood/stone/bones → stock `[2]/[3]/[4]` order is **inferred, not proven**. | Costs could charge the wrong resource. | Keep the order as a single named constant in the loader; if the HUD-icon trace later proves it wrong, one constant changes, no mod files change. |

## 7. What this plan deliberately does not do

- **No emulation.** This is a native reimplementation, not a J2ME
  emulator wrapped in an app. No KEmulator/freej2me inside the APK.
- **No reuse of the original code.** The decompiled classes are
  obfuscated, CLDC-bound, and legally the game's code. The port
  reimplements the *rules* from the research; it does not copy the code.
- **No bundled original assets.** See §2.3 — bring your own JAR.
- **No D-pad, no cursor, no keypad.** The touch scheme (§3) replaces
  the entire input layer; no compatibility mode.
- **No change to the tick rate or the core rules** in M1–M5. The game
  is 20 ticks/s, two tribes, same caps (50/30), same win/lose. New
  rules (new building types 12+, new weapons, raised caps) are v0.2
  format work, not port work.
