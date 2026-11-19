# Main Flow of Prehistoric Tribes — from the Decompiled Code

Sources: tribes.java, d.java, f.java (6,680 lines), a.java, helped by e.java / c.java for the loaders. Class and field names were obfuscated to a–f.

## 1. Start flow: startApp → loading d → game f

- tribes.java:20-28, `startApp()`: if the game object `f` already exists, call `f.e()` (resume). If not, get `Display.getDisplay()`, create a new Thread from `tribes` itself, then `thread.start()`.
- tribes.java:42-65, `run()`: `new d(this)`, `d.a()`, `setCurrent(d)`. The numbers in this sequence are image numbers, not menu numbers. The proof is in `d.java`: `d.a()` draws `"/l" + this.a`.
  - a=0, shown for 1 second, then `d.a()` again, wait 2 seconds → `l0` = THQ Wireless logo (240x71)
  - a=1, `d.a()`, wait 2 seconds → `l1` = Gear Games logo (192x114)
  - a=2, `d.a()` → `l2` = Prehistoric Tribes title screen (240x321)
  - a=5 — not an image. In `d.a()`, images are only drawn when `a < 4`. So 5 means "finished, don't draw anything else".
- Total loading is about 5 seconds (1+2+2), then `new f(this)` and `f.a()`.
- `pauseApp()` / `destroyApp()` forward to `f.d()` (pause) and `f.b()` (exit / `notifyDestroyed()`).

d.java — loading screen:
- Constructor: `setFullScreenMode(true)`.
- `a()`: the first time, create a 264x352 image buffer, fill it white with `fillRect(11, 8, 240, 321)`, draw `/l0`–`/l2` in the centre (131, 168, anchor 3 = centre), then `repaint()`.
- `paint()`: draws that buffer to the screen at position (-11,-8).
- `keyPressed()` is empty — any key on the loading screen is ignored.

f.java:356-409 — constructor of `f` and `f.a()`:
- The constructor prepares the languages `{"en", "fr", "it", "de", "es"}`, calls `setFullScreenMode(true)`, and sets starting values (for example `U=5`, `V=4`).
- `f.a()` (line 406): creates a new Thread from `f` and runs it — this is where `f.run()` starts.

## 2. Game loop in f

f.java:485-540 — `run()`:
- Setup: `f()` (line 412) — create the world logic with `new b()`, the loader with `new e(this)`, then `setCurrent(this)` (the screen moves from `d` to `f`); `g()` (line 428) — allocate all map/unit arrays.
- Then try to read a save: `if (!this.d(0)) { this.d(1); this.d(2); }` — `d(n)` at line 6245 loads from RecordStore `"t"+n`. Slot 0 is read first (settings), and if there is none, slots 1 and 2 are tried.
- Starting values: `Q=14`, `v=0` (menu mode), `H=true`, `R=U`.
- Loop `while (this.b)`, each iteration:
  1. `l = f.a()` — `f.a()` at line 6539 is just `System.currentTimeMillis()`, so this is the start time of the iteration.
  2. `aS()` — check pause and music.
  3. `h()` — update logic.
  4. `m()` — draw to the off-screen buffer.
  5. `l()` — `repaint()` and wait until `paint()` finishes (`while (this.z && !this.Z) Thread.yield()`).
  6. If scrolling (`ad != 0 || ae != 0`), draw once more after sleeping for half a frame (`tribes.a(this.i / 2)`).
  7. Sleep for the remaining time: `l3 = this.i - (time already used)`, clamped to 0..`i`, then `tribes.a((int)l3)`.

How many ticks per second?
- `h()`, line 542: `this.i = this.c ? 50 : this.j`. So the target time per iteration is `i` milliseconds. If `i=50`, that is **20 ticks per second**. For the other mode (`j`), the exact value cannot be traced safely in the decompiled output because the field names collide (obfuscation). So what can be said is: about 20 times per second, with a target of 50 ms per tick when `c` is true.

What is updated each tick — `h()`, lines 541-640:
- Animation counter `e`: rises each tick, resets at 8 (an 8-frame animation cycle). Counter `f`: resets at 120.
- If `v == 0` (menu): call `ak()` — update the menu.
- If `v == 1` (in game):
  - If `w == 2` or `4`: `ae()` (a specific mode, for example selecting).
  - Otherwise: `V()` (read player input, see section 4) and `k()` (find the nearest building/unit to the cursor).
  - Then counter `d`: every 6 ticks call `a(100, 0, 0, 0)` — a periodic trigger (probably resource / game-time accounting).
  - Then `j()` (line 636): calls `b.g()`, `b.e()`, `b.h()`, `b.i()` — these update the world in `b.java` (AI, movement, production). There is also mission-end logic: if `u` reaches 41 or 90, move to `v = 0, Q = 24`.
- If `o` reaches 3, call `i()` to reset all input flags.

## 3. States / game modes

There are two big modes, distinguished by field `v` in `f`:
- `v == 0` = menu / outside the game. `paint()` (line 768) draws the menu image `a[M]`.
- `v == 1` = inside the game. `paint()` (line 751) draws the map.

Screens/menus use the number **`Q`** (and `R` = the previous screen, for the "back" button). `Q` is a number from the data tables in `b`/`e`, not a name — so the labels must be treated with care:

| Q | Evidence | Meaning (as far as it can be proven) |
|---|---|---|
| 14 | `f.java:495`, start of `run()` | First screen after loading — the main menu. `G()` (line 2759) groups Q 14 together with 2, 3, 5, 9, 12, 13 as menu screens. |
| 10 / 11 | `f.java:3552`, in `W()` when the right key is pressed in game | Pause screen in game (chosen from `q < 7` and `t`). |
| 20 | `f.java:3302-3313`, method `a(byte, byte, byte)` | Info popup: `v = 0, Q = 20, v = 12 + by` — building/unit info dialog. |
| 22 / 23 | `f.java:4367`, `am()` | Load / result screen: `am()` handles `T = 0` (load level `g(q)`), `T = 1` (start game, `v = 1`), `T = 2` (load failed → go back). |
| 24 | `f.java:686-689`, in `j()` | Mission-end screen (reached when `u == 41` or `90`). |
| 25 | `f.java:568-571`, in `h()` when `v == 1` and the end condition is met | Exit from the game to screen 25, `R = 28`. The win/lose label is **not written** in the code. |
| 27 | `f.java:6584-6598` (`aS()`) and `4397-4412` (`al()`) | **System pause.** Not from a button, but from `hideNotify()` → `f.d()` (line 6551: `Y = true, Z = true`). When hidden, the old `Q` is saved to `R`, `Q` becomes 27, and the loop waits (`while (this.Y)`). When it returns (`showNotify()` → `f.e()`), `al()` restores `Q = R`. |
| 32 | `f.java:2736-2745`, in `F()` | Advert screen: draws `Image.createImage("/l3")` directly — the French Orange advert image seen earlier. |
| 15, 17, 18, 19 | `f.java:2699-2745`, dispatcher `F()` | Other screens (`J()`, `P()`, `K()`, `L()`). Their function names are not readable, so no labels are given here. |

Moving between states:
- Menu (`v == 0`): `ak()`, line 4364 — if `Q` is 22/23 → `am()`; if the right key (`m`) → `an()`; if a direction/select key → `ao()`; if up/down (`e`/`f`) → `aB()`/`aC()` (move the menu selection).
- Starting a game: `am()`, line 4413 — `T = 1` means start, `v = 1`, `R` is set to 10 or 11. There is a boundary `q < 7` vs `q >= 7` in several places (for example `am()`, lines 4436-4441): levels 0–6 are one group, 7 and above another group — this matches campaign vs custom game from the text, but the code itself does not write those words.
- From in-game back to the menu: `h()`, line 568 (`v = 0, Q = 25`) and `j()`, line 686 (`v = 0, Q = 24`).
- Save/load: `d(n)`, line 6245 (reads RecordStore `"t"+n`, slot 0 = settings, 1/2 = save games) and `e(n)`, line 6412 (writes, deleting first and then creating a new one). The save contents are complete: camera position, map, units, resources — read field by field at lines 6250-6400.

## 4. Input

Loading screen (`d.java`): `keyPressed()` is empty — no key works.

In game (`f.java:3326-3450`):
- All keys except `-10` are accepted (`a(n)`, line 3456: `return n != -10`).
- **Left/right softkeys:** `static int a = -6; static int b = -7;` (lines 30-31). In `keyPressed()`: `n == -6` (or 6) or `*` (42) → flag `l = true` (left); `n == -7` (or 7) or `#` (35) → flag `m = true` (right).
- **Number keys 1/3/7/9:** `49 ('1') → i = 1`, `51 ('3') → i = 3`, `55 ('7') → i = 7`, `57 ('9') → i = 9`, `48 ('0') → i = 0`. These are used in `aG()`/`aH()` (lines 5060-5099) to change groups: `i == 7` → group 2, `i == 9` → group 3.
- **`getGameAction(n)`** is called at line 3381 (on press) and 3425 (on release), wrapped in try/catch — if it fails, `m = 666`. The result is mapped together with the number keys (so either the D-pad or the numbers can be used):
  - `m == 1` (UP) or `50 ('2')` → `e = true` (up)
  - `m == 6` (DOWN) or `56 ('8')` → `f = true` (down)
  - `m == 2` (LEFT) or `52 ('4')` → `g = true` (left)
  - `m == 5` (RIGHT) or `54 ('6')` → `h = true` (right)
  - `m == 8` (FIRE/centre) or `53 ('5')` → `i = true, t = true` (select/action)
- **`keyReleased()` (line 3413):** turns off the same direction flags (`e/f/g/h = false`), and if the centre key is released quickly (`E < 4`) → `v = true` (treated as a select tap, not a hold).
- **Cheat code:** `m(int n)`, lines 6595-6680 — the key sequence is stored and compared with `j = {56, 55, 51, 57, 49}` (keys `8, 7, 3, 9, 1`). If the first 5 keys match, the 6th key decides: `49 ('1')` → `af = true`, `51 ('3')` → `ag = true`, `55 ('7')` → add 100 to the first 5 resources, `57 ('9')` → `u = 1`. This matches the `MIDlet` property `Cheat-Support: on` in the manifest.
- **What those flags do — `V()`, lines 3487-3550:**
  - If selecting an area (`u && i`): `aF()` — gather the units in the selected area.
  - If the centre key is held (`t`): `aE()` — held for more than 4 ticks → select a group.
  - If the cursor is on a building (`w == 1` and `W` 51–100): move the camera to that building.
  - Otherwise: `d(by)` (open info / select a building), `X()` (build), or `f(-by)` (order a unit).
  - Smooth scrolling: `ad = af * 11; ae = ag * 8` (lines 3528-3529) — half a tile.
- **Softkeys in game — `W()`, lines 3536-3555:** `l` (left) → open the build menu (`w = 2`); `m` (right) → if in the build menu, close it; if selecting units, cancel; otherwise open the pause screen `Q = 10/11`.

## 5. Rendering

- Double buffering: `f.java` has `static Image[] a` and `static Graphics[] a` (4 slots). `e.c()`, lines 107-112, creates buffer `a[1]` 264x304, `a[3]` 264x304, and one small 79x63 buffer. `d.a()` creates `a[0]` 264x352 for loading.
- Flow: `m()` (line 779) first draws to the off-screen buffer — the map (`n()`), units, and menu (`F()` if `v == 0`). Then `l()` (line 745) calls `repaint()`, and `paint()` (line 750) copies the buffer to the screen with `drawRegion`.
- Size: the game is designed for 240x320, but the buffer is 264x352. When copied, it is shifted by (-11,-8) — see `d.paint()` (`drawImage(f.a[0], -11, -8, 0)`) and `f.paint()` (lines 753, 768: `this.a - 11`, `this.b - 8`). So there is an 11 px frame on the left and an 8 px frame on top.
- In game (`v == 1`, `paint()`, lines 751-766): draw the map from buffer `a[c[1]]` or `a[3]` (when scrolling), then a loop of 20 overlay slots (unit/building icons, arrows, and so on).
- Menu (`v != 1`, lines 767-774): draw `a[M]`, 251x328, plus two black bars at the top/bottom when scrolling text is running (`s && aP < 0`).
- Camera / scrolling: the map is a grid of **22x16 pixel** tiles — evidence in `n()`, lines 827-829 (`aj = -af * 22; ak = -ag * 16`) and `m()`, lines 795-796 (`c(y * 22 - ad, A * 16 - ae)`). `y`/`A` = the camera's origin tile position, `I`/`K` = the cursor position on screen, `O = 11` columns and `P = 18` rows visible (from `e.c()`, lines 100-104). Smooth scrolling is done in half-tile steps (11 px horizontal, 8 px vertical), then `aK()` (line 5196) clamps the cursor so it cannot leave the map.

## 6. Music / sound

- There is only one player, class `a.java`, and it is MIDI. There is no separate sound-effects class.
- **Music data:** `e.g()` (in `e.java`, around line 234) reads file `/sa` (26,616 bytes) into `f.w`. The tables in `f.java` / `e.g()`: `f.e = {8014, 6315, 5648, 3405, 3234}` (lengths) and `f.f = {0, 8014, 14329, 19977, 23382}` (start positions) — so **there are 5 MIDI songs** in one file.
- **`a.java` — how the player works:**
  - Constructor (around line 30): `Manager.createPlayer(new ByteArrayInputStream(f.w, f.f[f.f], f.e[f.f]), "audio/midi")`, then `realize()` and `addPlayerListener()`. So the song is chosen from the table above.
  - `a(int n)` (volume): get the `VolumeControl`; if `n != 0`, play (`c()`) and `setLevel(n * 20)`; if `n == 0`, stop.
  - `c()` (start): if the state is 300, stop first; if not yet 400 (started), `prefetch()` then `start()`.
  - `a()` (stop): if the state is 400, `setMediaTime(0)` then `stop()`. `b()` (close): `close()`.
  - `playerUpdate()`: if `deviceUnavailable` → stop; if `deviceAvailable` → start again.
- **When it plays — `f.aQ()`, lines 6565-6577, and `f.aS()`, lines 6604-6606:**
  - `aQ()` picks a random song from table `b` (`f = b[h*2 + random 0-1]`); if there is no player yet or the song is different, stop the old one (`aR()`) and create a `new a("audio/midi")`, then set the volume.
  - `aS()` is called **every tick** from `run()`. There: if `Q != 27` (not paused) and `e == 2` and (there is no player or the player is not running), call `aQ()`. Field `e == 2` has no clear name in the decompiled output, so it cannot be claimed with certainty that this is "the music-on setting" — what is certain is: music is checked every tick, and if nothing is playing, a random song is played again. During system pause (`Q = 27`), music is not started again.

## What cannot be determined from this code alone

- The exact labels for each `Q` number (15, 17, 18, 19, and so on) and whether Q 24/25 mean win or lose — the names were lost to obfuscation; only the numbers and data tables remain.
- The value of `j` (the tick interval of the second mode) and the exact meaning of field `e == 2` for music — the field names collide in the CFR output.
- The world logic in `b.java` (5,805 lines: enemy AI, production, combat) — that is the next dissection step if wanted, not part of this main-flow report.
