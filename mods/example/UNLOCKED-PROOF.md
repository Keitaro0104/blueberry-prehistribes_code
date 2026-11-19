# Unlocked variant — proof note

**Verdict: PASS.** The Custom Game menu opens and Green Valley loads and plays
with zero tutorial progress, no seeded save, no cheat.

## 1. The gate (found in decompiled code)

Text `t[70]` = "pass the tutorial first!" (`extracted/0/t`, 72 strings, index 70).
The gate is `f.aw()` (decompiled with CFR 0.152, `decompiled-cfr/f.java:4839`):

```java
private void aw() {
    this.q = (byte)7;
    this.R = this.Q;
    if (this.W) {
        this.Q = (byte)3;
        this.Z = 0;
    } else if (this.r > 0 || this.af) {
        this.Q = (byte)13;   // Custom Game list
        this.Z = 1;
    } else {
        this.v = 70;         // "pass the tutorial first!"
        this.Q = (byte)21;   // message screen
        this.Z = 0;
    }
    this.aa = 1;
}
```

- `r` is the progress byte (`Field r:B` in `f.class`): fresh save = 0; it is only
  ever assigned `r = s` (highest unlocked level from the `t0` save, 0–7) or
  `r = 4` in the cheat path.
- `af` is a boolean flag (the cheat enabler); it is never set in this build,
  which is why the cheat sequence is dead.
- `aw()` is called when CUSTOM GAME is selected in the PLAY submenu.

## 2. The bytecode patch (one byte)

`javap -c -p f` disassembly of `aw()` before the patch:

```
34: aload_0
35: getfield      #361   // Field r:B
38: ifgt          48
41: aload_0
42: getfield      #193   // Field af:Z
45: ifeq          62
48: aload_0 ... Q = 13 ...
```

Patch (script: `repack-work/patch_unlock.py`, parses the class file, finds method
`aw`, verifies the surrounding bytes, patches in place):

- File offset 75082 = code offset 38 in `aw()`: `0x9D` (`ifgt`) → `0x9C` (`ifge`).
- Same instruction size (3 bytes), same branch target (48). `ifge` still pops
  the loaded value, so the operand-stack depth at every join point is
  unchanged. Since `r` is always 0–7 in practice, `r >= 0` is always true and
  the branch to the Custom Game list is always taken. The `af` check remains
  as a fallback.

**Failed first attempt (documented so nobody repeats it):** patching `ifgt`
to `goto` (`0xA7`) does NOT pop the value, so the branch target is reached
with one extra item on the stack. freej2me refused to load the class:

```
Exception in thread "Thread-1" java.lang.VerifyError:
  (class: f, method: aw signature: ()V) Stack size too large
```

## 3. The variant JAR

- `repack-work/prehistoric_tribes_green_valley_unlocked.jar` — **496,727 bytes**.
- Built from `repack-work/prehistoric_tribes_green_valley.jar` (the Green Valley
  repack) by replacing only `f.class` with the patched class (same size,
  100,293 bytes). Verified: same file list, manifest byte-identical, only
  `f.class` differs, valid zip (`testzip()` clean), patched class inside the
  JAR matches `f-patched.class`.

## 4. Emulator test

freej2me (built from source, `freej2me-src/build/freej2me.jar`) on Xvfb :99,
driven by `EmuDriver` (Robot key presses + screenshots). Keys: Q = left
softkey, W = right softkey, arrows = D-pad, ENTER = select.

**Control run (locked Green Valley JAR), same procedure:** language ENGLISH →
"PLAY MUSIC?" No → main menu → PLAY → CAMPAIGN / CUSTOM GAME → CUSTOM GAME →
**"PASS THE TUTORIAL FIRST!"** (`shots-locked/L06-gate.png`). The gate works.

**Unlocked run (variant JAR):** same steps → CUSTOM GAME opens the
**DIFFICULTY (EASY / HARD)** screen (`shots-unlocked/U05-custom.png`) → EASY →
Custom Game list shows GREAT LAKE, DESERT PASS, FOREST BELT, SLAUGHTER,
**GREEN VALLEY** (`shots-unlocked/U06-maplist.png`) → GREEN VALLEY loads and
plays: HUD 11/1, resources 10/20/10/5, tribe + chief + villagers + building
on Green Valley terrain (`shots-unlocked/U07-game.png`, `U08-game2.png`).
No exception in the emulator log; the game keeps ticking (villagers move
between the two screenshots).

**Fresh-profile note:** freej2me stores RecordStores under `./rms/<app>/`
relative to the *working directory* (`dataPath` defaults to `""`), not under
`user.home` — so the `-Duser.home` fresh profiles did not isolate the saves.
Both runs shared `repack-work/rms/Prehistoric Tribes/t0`, which is 6 bytes
`00 01 00 01 00 00` = version 1, nextid 1, **0 records** — an empty store,
created by the control run at startup. That means both runs had identical
zero-progress state (`r = 0`, no record at all), and the only difference
between them was the patched `f.class`. The test is valid; the shared empty
store actually strengthens it. (The previous agent's seeded `r = 1` saves
live in `shots-new/rms/` and `shots-orig/rms/` — different working
directories, never read by these runs.)

## 5. Limits / still untested

- Only the English text path was exercised; other languages still say
  "plot of land" for q=11 and would show their own "pass the tutorial"
  message if the gate were hit (it no longer is).
- Win/lose verdict on the modded map is still untested end-to-end.
- Real-phone test (J2ME Loader on Android) still needed — this variant is
  the JAR to hand the user for that test.
- The patch relies on `r >= 0`; a hand-crafted/corrupt save with a negative
  `r` would still hit the gate. The game itself never writes a negative `r`.
