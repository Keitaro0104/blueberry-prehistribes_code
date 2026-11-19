# blueberry-prehistribes_code

Reverse-engineering research on the J2ME game **Prehistoric Tribes** (THQ Wireless / Gear Games, 2008, MIDP-2.0, 240x320) using REA + CFR.

This repo contains **our own analysis notes**, not game files.

## What's in this repo

- `PETA-SISTEM.md` — a complete system map in English: main flow, game loop, world, buildings, villagers, combat, languages, levels, save/load, music, and open questions.
- `ANALISIS-alur-utama.md` — a detailed report on the main flow (start, loading, game loop at about 20 ticks per second, input, rendering, MIDI music).

## What's NOT in this repo

- The original `.jar` game file
- Files extracted from the JAR (images, MIDI music, text, binary data)
- Raw decompiled Java files

They are deliberately not uploaded to this public repo because the game is still copyrighted (THQ, 2008). "Abandonware" is not a legal status — no recent news does not mean there is no rights holder.

## How to reproduce the analysis

1. Prepare a copy of the game's JAR file that you own yourself.
2. Unzip the JAR, then decompile the Java classes with CFR 0.152 (requires Java 17).
3. Compare your results with the map in `PETA-SISTEM.md`.

## Summary of findings

- 7 classes, 13,418 lines of decompiled output: `tribes` (entry point), `f` (main game, 6,680 lines), `b` (world logic, 5,805 lines), `e` (resource loader), `c` (text loader), `d` (splash), `a` (MIDI player).
- Real-time village strategy: 2 tribes, up to 50 villagers + 30 buildings per tribe, a grid map up to 96x96, 10 maps, 12 building types, 4 resources (food, wood, stones, bones) + weapons.
- 5 languages (EN/FR/IT/DE/ES), 7 campaign missions (the tutorial must be passed first), 3 RecordStore save slots (`t0`/`t1`/`t2`), 5 MIDI songs in a single file.
- All balance numbers (costs, HP, damage) live in the `pd0` data table, not in the code — the next step is to decode `pd0`.

## License / disclaimer

The analysis in this repo is our own written work, for learning and research. The game Prehistoric Tribes © 2008 THQ Wireless Inc., developed by Gear Games, Ltd. Do not use this repo to redistribute game files.
