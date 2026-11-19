#!/usr/bin/env python3
"""Repack the original Prehistoric Tribes J2ME JAR with a mod-format map.

Replaces level q=11 ("plot of land", custom-only, ma piece 9) with the
Green Valley example map (mods/example/example-map.json). See
mods/example/PROOF.md for the full reasoning and verification.

Why q=11 (proven from the decoded data, see MA-MAPS.md / DECODE-REMAINING.md):
- ma piece 0 is shared by q=0 (tutorial, 40x32, 43% of the piece) and
  q=1 (campaign mission 1, 64x48, 100% of the piece); replacing it
  would break campaign mission 1.
- ma piece 4 is shared by q=5 (64x96, 66%) and q=6 (96x96, 100%);
  replacing it would break campaign missions 5 and 6.
- Pieces 6-9 are used by exactly one level each (q=8..11, custom-only).
  Piece 9 (q=11) is the last piece, so replacing it cannot shift any
  other piece, and q=11 has no scripted mission events (those exist
  only for q=0..6) and no campaign role.

Changes made (all in-place, total file sizes unchanged):
- `ma`: piece 9 [39214..42381) replaced by the new RLE encoding
  (399 bytes for Green Valley) + zero padding to the original piece
  length (3167 bytes). Piece offsets are hardcoded in the game code,
  so the piece length must not change; bytes past the decoded stream
  are never read (decoding stops after w*h tiles).
- `/a` (18,842 bytes, segment layout unchanged):
  - segment 149, pair q=11: (64, 64) -> (40, 32)  [map dimensions]
  - segment 150, pair q=11: (14, 44) -> the centroid of the remapped
    PLAYER villagers (see below). This is the camera/cursor start.
    It is deliberately NOT the map's player_start: the game only draws
    terrain the player's tribe has "seen" (fog of war, a radius around
    the player's villagers/buildings, recorded in f.java's bit arrays
    and redrawn by the c()/o() dirty-tile loop), so the camera must
    start on top of the tribe or the opening view is mostly black.
    The original q=11 has its camera (14,44) right next to its tribe
    spawn (12-16, 42-45); our first repack put the camera at
    player_start (15,5) while the remapped tribe spawns at (7-10,
    21-22), and the opening view was a small wedge of terrain in a
    black viewport. Starting the camera on the tribe centroid fixes
    it (proven in the emulator: the map renders like the original).
    The JSON's player_start is still validated, but for the J2ME
    repack the tribe's position comes from the inherited q=11 setup
    table, so the camera follows the tribe, not player_start. A
    future loader that spawns the tribe at player_start can use it
    for the camera as well.
  - segment 261, the q=11 level-setup table (60 entries, 5 parallel
    arrays): every entry keeps its (v0, v1, v4) values and only its
    (x, y) coordinates are remapped into the 40x32 map by proportional
    scaling (x*40//64, y*32//64), then nudged to the nearest valid
    cell. Without this, all 60 starting villagers/buildings would
    spawn outside the new map (original coordinates reach x=58, y=52),
    leaving the player with no visible tribe and enemy buildings that
    can never be destroyed (the win condition). See PROOF.md.
  - segment 279 (win/lose flags) needs NO change: q=11 already has
    flags=3, exactly Green Valley's flags.
  - segment 248 (piece index) needs NO change: q=11 already uses
    piece 9.
- `0/s` (English text): "plot of land" -> "Green Valley" (both 12
  characters, so the file length is unchanged). Only q=11 displays
  name index s[91], so no other screen is affected. Cosmetic only.

Everything else in the JAR (all .class files, manifest, sprites,
music, other maps, other languages) is copied byte-for-byte.

Usage:
    python3 repack_jar.py --jar <original.jar> --map <map.json> \
        --out <repacked.jar> [--base-dir .] [--report report.json]
"""
import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

# ma piece offsets, hardcoded in the game code (e.h).
H = [0, 2545, 6965, 10649, 15487, 22633, 27261, 31708, 35466, 39214]
MA_SIZE = 42381
TARGET_Q = 11
TARGET_PIECE = 9  # seg248[11]

# Original building types: (width, height) read from /a record 138
# rows 4/5 at run time; the table below is only a fallback for the
# validation message. The script reads the real values from the blob.
BUILDING_SIZE_FALLBACK = {
    0: (3, 2), 1: (5, 4), 2: (2, 2), 3: (4, 4), 4: (4, 3), 5: (6, 4),
    6: (3, 3), 7: (5, 4), 8: (3, 3), 9: (4, 4), 10: (4, 4), 11: (1, 1),
}


def parse_a_segments(raw):
    """Parse file /a into (lens, starts, blob). Same layout as decode_ma."""
    import struct
    off, lens, starts = 0, [], []
    for _ in range(312):
        n = struct.unpack_from("<H", raw, off)[0]
        off += 2
        lens.append(n)
        starts.append(off)
        off += n
    blob = b"".join(raw[starts[k]:starts[k] + lens[k]] for k in range(312))
    return lens, starts, blob


def rebuild_a(raw, blob):
    """Rebuild file /a from a modified blob (segment lengths unchanged).

    NOTE: segment data lives in the blob at cumulative offsets A[k],
    while `starts[k]` are offsets into the raw file (each segment is
    preceded by its 2-byte length prefix). Do not mix the two up.
    """
    lens, starts, _old = parse_a_segments(raw)
    A = [0]
    for L in lens:
        A.append(A[-1] + L)
    out = bytearray()
    for k in range(312):
        out += lens[k].to_bytes(2, "little")
        out += blob[A[k]:A[k + 1]]
    out += raw[len(out):]  # the 5 trailing short groups, untouched
    assert len(out) == len(raw) == 18842, (len(out), len(raw))
    return bytes(out)


def tile_blocked(tile, b9):
    """Blocked if tile >= 175 or pd0 table b[9] bit 13 set (aN rule)."""
    return tile >= 175 or ((b9[tile] & 0xFFFF) >> 13 & 1) == 1


def compute_occupancy(grid, w, h, b9):
    """Mirror aN()'s c-grid: 0 = free, -126 = border/blocked, else != 0.

    Green Valley uses only tiles 0, 3, 43, 175-179. Tile 43 is blocked,
    175-179 are spawn tiles (non-zero c), 0/3 are free. Border cells
    (first row, last row, last column) are forced -126 by aN().
    """
    occ = [[0] * w for _ in range(h)]
    for r in range(h):
        for c in range(w):
            t = grid[r][c]
            if r == 0 or r == h - 1 or c == w - 1 or tile_blocked(t, b9):
                occ[r][c] = -126
            elif 175 <= t <= 179:
                occ[r][c] = -61  # spawn tile: registered map object, not free
    return occ


def nearest_free(occ, w, h, x, y, max_radius=8):
    """Nearest cell (x, y order) with occ == 0, spiral search."""
    if 0 <= x < w and 0 <= y < h and occ[y][x] == 0:
        return x, y
    for radius in range(1, max_radius + 1):
        for dy in range(-radius, radius + 1):
            for dx in (-radius, radius):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and occ[ny][nx] == 0:
                    return nx, ny
        for dx in range(-radius + 1, radius):
            for dy in (-radius, radius):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and occ[ny][nx] == 0:
                    return nx, ny
    return None


def player_tribe_centroid(new_seg):
    """Centroid (col, row) of the remapped PLAYER villagers in a seg261.

    Segment layout: 5 parallel arrays of length `by` (60 for q=11),
    entry i = (v0, v1, v2, v3, v4); v1 == -1 (stored as 255) is a
    villager, v0 & 1 == 0 is the player's tribe.
    """
    by = len(new_seg) // 5
    arrs = [list(new_seg[k * by:(k + 1) * by]) for k in range(5)]
    px = py = n = 0
    for i in range(by):
        v0, v1, v2, v3, _v4 = (arrs[k][i] for k in range(5))
        v1s = v1 - 256 if v1 >= 128 else v1
        if v1s == -1 and (v0 & 1) == 0:
            px += v2
            py += v3
            n += 1
    assert n > 0, "no player villagers in the setup table"
    return px // n, py // n


def remap_setup_table(blob, A, grid, w, h, b9, building_size):
    """Remap the q=11 setup table (segment 261) into the new map.

    Entry i (5 parallel arrays of length 60):
      v0, v1, v2, v3, v4 with v1 == -1 -> villager at (x=v2, y=v3),
      v1 >= 0 -> building of type v1 at (x=v2, y=v3), level v4.
    Only (v2, v3) change; (v0, v1, v4) are kept byte-for-byte.
    Returns (new_segment_bytes, report_dict).
    """
    import struct
    seg = list(blob[A[261]:A[262]])
    by = list(blob[A[262]:A[263]])[TARGET_Q]
    assert len(seg) == 5 * by == 300, len(seg)
    arrs = [seg[i * by:(i + 1) * by] for i in range(5)]
    entries = [tuple(arrs[k][i] for k in range(5)) for i in range(by)]
    occ = compute_occupancy(grid, w, h, b9)
    new_entries = []
    report = {"total": by, "villagers": 0, "buildings": 0,
              "nudged": [], "unplaceable": []}
    for i, (v0, v1, v2, v3, v4) in enumerate(entries):
        # Stored bytes are unsigned; v1 == 255 means -1 (signed).
        v1s = v1 - 256 if v1 >= 128 else v1
        nx, ny = v2 * w // 64, v3 * h // 64  # scale from the 64x64 map
        if v1s == -1:
            report["villagers"] += 1
            spot = nearest_free(occ, w, h, nx, ny)
            if spot is None:
                report["unplaceable"].append(
                    {"entry": i, "kind": "villager",
                     "scaled": [nx, ny], "original": [v2, v3]})
                new_entries.append((v0, v1, nx, ny, v4))
            else:
                if spot != (nx, ny):
                    report["nudged"].append(
                        {"entry": i, "kind": "villager",
                         "from": [nx, ny], "to": list(spot)})
                new_entries.append((v0, v1, spot[0], spot[1], v4))
        elif v1s >= 0:
            report["buildings"] += 1
            bw, bh = building_size.get(v1s, BUILDING_SIZE_FALLBACK[v1s])

            def footprint_ok(x, y):
                if not (0 <= x < w and 0 <= y < h):
                    return False
                if x + bw > w or y + bh > h:
                    return False
                return all(occ[y + dy][x + dx] == 0
                           for dy in range(bh) for dx in range(bw))

            placed = None
            if footprint_ok(nx, ny):
                placed = (nx, ny)
            else:
                for radius in range(1, 9):
                    found = False
                    for dy in range(-radius, radius + 1):
                        for dx in range(-radius, radius + 1):
                            if max(abs(dx), abs(dy)) != radius:
                                continue
                            if footprint_ok(nx + dx, ny + dy):
                                placed = (nx + dx, ny + dy)
                                found = True
                                break
                        if found:
                            break
                    if found:
                        break
            if placed is None:
                report["unplaceable"].append(
                    {"entry": i, "kind": "building", "type": v1s,
                     "scaled": [nx, ny], "original": [v2, v3]})
                new_entries.append((v0, v1, nx, ny, v4))
            else:
                if placed != (nx, ny):
                    report["nudged"].append(
                        {"entry": i, "kind": "building", "type": v1s,
                         "from": [nx, ny], "to": list(placed)})
                for dy in range(bh):
                    for dx in range(bw):
                        occ[placed[1] + dy][placed[0] + dx] = -125
                new_entries.append((v0, v1, placed[0], placed[1], v4))
        else:  # v1 == -2 (trap placement): no such entries for q=11.
            new_entries.append((v0, v1, nx, ny, v4))
    new_seg = bytearray(300)
    for k in range(5):
        for i in range(by):
            new_seg[k * by + i] = new_entries[i][k] & 0xFF
    return bytes(new_seg), report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--jar", required=True, help="original JAR")
    ap.add_argument("--map", required=True, help="mod map JSON file")
    ap.add_argument("--out", required=True, help="repacked JAR to write")
    ap.add_argument("--base-dir", default=".",
                    help="directory holding extracted/ and decode_ma.py")
    ap.add_argument("--report", default=None, help="JSON report to write")
    args = ap.parse_args()
    base = Path(args.base_dir)
    sys.path.insert(0, str(base.resolve()))
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import convert_map
    import decode_ma

    # --- 1. Encode the map ---------------------------------------------
    data, w, h, flat = convert_map.load_map(args.map)
    stream = convert_map.encode(flat, w, h)
    grid = [flat[i * w:(i + 1) * w] for i in range(h)]
    print(f"map {data['id']!r}: {w}x{h}, encoded {len(stream)} bytes")

    # --- 2. Read the original JAR --------------------------------------
    zin = zipfile.ZipFile(args.jar)
    names = zin.namelist()
    orig = {n: zin.read(n) for n in names}
    infos = {n: zin.getinfo(n) for n in names}
    orig_ma = orig["ma"]
    orig_a = orig["a"]
    assert len(orig_ma) == MA_SIZE, len(orig_ma)
    assert len(orig_a) == 18842, len(orig_a)

    # --- 3. New ma: replace piece 9, pad with zeroes -------------------
    start = H[TARGET_PIECE]
    end = H[TARGET_PIECE + 1] if TARGET_PIECE + 1 < len(H) else MA_SIZE
    if len(stream) > end - start:
        raise ValueError(f"encoded map ({len(stream)} bytes) does not fit "
                         f"in piece {TARGET_PIECE} ({end - start} bytes)")
    new_ma = bytearray(orig_ma)
    new_ma[start:start + len(stream)] = stream
    for i in range(start + len(stream), end):
        new_ma[i] = 0
    new_ma = bytes(new_ma)

    # --- 4. New /a: dimensions, cursor, setup table --------------------
    lens, starts, blob = parse_a_segments(orig_a)
    # Cumulative offsets A[] (decode_ma.parse_a gives the same table).
    _l, A, _b, _g = decode_ma.parse_a(str(base / "extracted" / "a"))
    blob = bytearray(blob)
    old_dims = (blob[A[149] + 2 * TARGET_Q], blob[A[149] + 2 * TARGET_Q + 1])
    blob[A[149] + 2 * TARGET_Q] = w
    blob[A[149] + 2 * TARGET_Q + 1] = h
    old_cursor = (blob[A[150] + 2 * TARGET_Q],
                  blob[A[150] + 2 * TARGET_Q + 1])
    flags = list(blob[A[279]:A[280]])[TARGET_Q]
    assert flags == int(data["win_lose"]["flags"]), (
        f"record 279 q={TARGET_Q} is {flags}, map wants "
        f"{data['win_lose']['flags']} (would need a flags change)")
    # Building footprints from record 138 (rows 4/5, 26 columns each).
    _shorts, byt = decode_ma.parse_pd0(str(base / "extracted" / "pd0"))
    b9 = _shorts[9]
    building_size = {}
    for t in range(12):
        building_size[t] = (blob[A[138] + 4 * 26 + t],
                            blob[A[138] + 5 * 26 + t])
    new_seg261, setup_report = remap_setup_table(
        bytes(blob), A, grid, w, h, b9, building_size)
    blob[A[261]:A[262]] = new_seg261
    # Camera/cursor start: the remapped player tribe's centroid (see
    # the docstring for why the map's player_start is not used here).
    cam_x, cam_y = player_tribe_centroid(new_seg261)
    blob[A[150] + 2 * TARGET_Q] = cam_x
    blob[A[150] + 2 * TARGET_Q + 1] = cam_y
    new_a = rebuild_a(orig_a, bytes(blob))
    print(f"/a: seg149 q11 {old_dims} -> ({w}, {h}); "
          f"seg150 q11 {old_cursor} -> ({cam_x}, {cam_y}) "
          f"[player tribe centroid; player_start "
          f"({data['player_start']['col']}, {data['player_start']['row']}) "
          f"not used, see docstring]; "
          f"seg279 q11 = {flags} (unchanged); "
          f"seg261 remapped: {setup_report['villagers']} villagers, "
          f"{setup_report['buildings']} buildings, "
          f"{len(setup_report['nudged'])} nudged, "
          f"{len(setup_report['unplaceable'])} unplaceable")

    # --- 5. New 0/s: rename the map in the English text ----------------
    text_s = orig["0/s"]
    old_name, new_name = b"plot of land", b"Green Valley"
    assert len(old_name) == len(new_name) == 12
    assert text_s.count(old_name) == 1, text_s.count(old_name)
    new_s = text_s.replace(old_name, new_name)

    # --- 6. Write the repacked JAR -------------------------------------
    replaced = {"ma": new_ma, "a": new_a, "0/s": new_s}
    with zipfile.ZipFile(args.out, "w", zipfile.ZIP_DEFLATED) as zout:
        for name in names:
            info = infos[name]
            zout.writestr(info, replaced.get(name, orig[name]))
    print(f"[wrote {args.out}]")

    # --- 7. Verify ------------------------------------------------------
    zcheck = zipfile.ZipFile(args.out)
    assert zcheck.testzip() is None, "zip integrity check failed"
    new = {n: zcheck.read(n) for n in zcheck.namelist()}
    assert zcheck.namelist() == names, "entry list changed"
    assert new["META-INF/MANIFEST.MF"] == orig["META-INF/MANIFEST.MF"], \
        "manifest changed"
    for n in names:
        if n in replaced:
            continue
        assert new[n] == orig[n], f"unrelated file changed: {n}"
    for n in ("a.class", "b.class", "c.class", "d.class", "e.class",
              "f.class", "tribes.class"):
        assert hashlib.sha256(new[n]).hexdigest() == \
            hashlib.sha256(orig[n]).hexdigest(), f"class changed: {n}"
    assert len(new["ma"]) == MA_SIZE and len(new["a"]) == 18842
    # The proven decoder must reproduce Green Valley from the new files,
    # and every other level must decode exactly as before.
    # parse_a() only reads from a path, so decode the new /a by hand:
    import struct
    off, lens2, starts2 = 0, [], []
    raw = new["a"]
    for _ in range(312):
        n = struct.unpack_from("<H", raw, off)[0]
        off += 2
        lens2.append(n)
        starts2.append(off)
        off += n
    blob2 = b"".join(raw[starts2[k]:starts2[k] + lens2[k]]
                     for k in range(312))
    A2 = [0]
    for L in lens2:
        A2.append(A2[-1] + L)
    d11 = decode_ma.decode_map(TARGET_Q, new["ma"], blob2, A2)
    assert d11["grid"] == grid, "new ma does NOT decode to Green Valley"
    for q in range(12):
        if q == TARGET_Q:
            continue
        d_old = decode_ma.decode_map(q, orig_ma, blob, A)
        d_new = decode_ma.decode_map(q, new["ma"], blob2, A2)
        assert d_new["grid"] == d_old["grid"], \
            f"collateral damage: level q={q} changed!"
    print("verification: zip OK; manifest OK; all .class files unchanged; "
          "all other files byte-identical; q=11 decodes to Green Valley; "
          "q=0..10 decode exactly as before")

    report = {
        "target_q": TARGET_Q, "target_piece": TARGET_PIECE,
        "map": {"id": data["id"], "name": data["name"], "size": [w, h]},
        "encoded_bytes": len(stream),
        "piece_bytes": end - start,
        "changed_files": {
            "ma": {"old_size": len(orig_ma), "new_size": len(new_ma)},
            "a": {"old_size": len(orig_a), "new_size": len(new_a)},
            "0/s": {"old_size": len(text_s), "new_size": len(new_s)},
        },
        "a_changes": {
            "seg149_q11": {"old": list(old_dims), "new": [w, h]},
            "seg150_q11": {"old": list(old_cursor),
                           "new": [cam_x, cam_y],
                           "note": "player tribe centroid, not "
                                   "player_start (see docstring)"},
            "seg279_q11": flags,
            "seg248_q11": 9,
        },
        "setup_table": setup_report,
        "jar": {"original_size": Path(args.jar).stat().st_size,
                "repacked_size": Path(args.out).stat().st_size},
    }
    if args.report:
        Path(args.report).write_text(json.dumps(report, indent=2) + "\n",
                                     encoding="utf-8")
        print(f"[wrote {args.report}]")
    return report


if __name__ == "__main__":
    main()
