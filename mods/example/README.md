# Example mod — Green Valley + Large Hut (format v0.1)

## What this is

A working example of the mod format v0.1 (see `../format/MOD-FORMAT.md`).
It contains one map and one building variant, nothing else.

- `example-map.json` — "Green Valley", a 40x32 map in the style of the
  tutorial map (level q0, "outside"). Mostly open ground (tile 0), with
  open-ground variant patches (tile 3), blocked rock clusters and a
  blocked border (tile 43), and five spawn points (tiles 175-179,
  types 1-5). Win/lose flags value 3: win by destroying all enemy
  buildings, lose if the key building is destroyed; losing by tribe
  wipe-out always applies.
- `example-building.json` — "Large Hut", a variant of the Hut (base
  type 2). Base values are the decoded Hut values (HP 25/40/90, build
  cost 5/10/0, upgrade cost 15/5/0, mood 0/2/0, worker capacity 3,
  living space +4). This variant is cheaper (build 3/6/0, upgrade
  12/4/0) but has about 20% less HP (20/32/72).

## How to read it

- A map is a grid of tile IDs: `tiles[row][col]`, row 0 is the top.
  Tile 0 is open ground, tile 3 is an open-ground variant, tile 43 is
  a blocked obstacle, tiles 175-179 are spawn points.
- A building is a JSON object with its size, HP per level, costs,
  mood bonus, worker capacity, and the original type it is based on
  (`base_type`).

## What a loader would do with it

1. Validate both files against the rules in `MOD-FORMAT.md` section 7
   (sizes, tile IDs, spawn positions, win/lose flags, HP > 0, costs >= 0).
2. Encode the map grid with the original RLE format (record 197) into a
   new `ma` piece, write its size into record 149 and its win/lose flags
   into record 279.
3. Write the Large Hut's values into record 138 (over the Hut's columns
   for a replacement, or into a free slot for an addition — see
   `MOD-FORMAT.md` section 9).

## Status

**Format-only for now: no loader exists yet.** These files are valid
v0.1 mods to design and test against, but nothing can load them into the
game yet. Building the loader (J2ME repacker and/or Android loader) is
the next step after the format.

No game assets are included here: no PNG, no JAR, no extracted files,
no decompiled Java.
