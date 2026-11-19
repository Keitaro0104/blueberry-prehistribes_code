#!/usr/bin/env python3
"""Decode the `ma` map data of Prehistoric Tribes (J2ME, THQ/Gear Games 2008).

Reconstruction (proven from bytecode, see header comments):
- File /a is an indexed data file: 312 segments. Layout per segment:
  [u16 LE length][length bytes of data], repeated 312 times, then 5 groups of
  u16 LE shorts (122+121+6+24+12 = 285 shorts). Total file = 18,842 bytes.
  Segment k lives at blob offsets A[k]..A[k+1] where A is the cumulative
  sum of the 312 lengths (blob = 17,638 bytes). f.a:[S] is that A table
  (312 shorts); f.a:[B] is the blob (17,638 bytes).
- File /pd0: byte 0 = 11 (number of short tables). Then 11 big-endian short
  tables and 25 byte tables, lengths from the literal table in e.<init>:
  [119,1291,162,162,2782,144,1069,6903,823,1721,5492,
   119,1291,1291,1291,162,162,162,2782,2782,144,1069,1069,6903,6903,6903,
   823,1721,42,5492,5492,1810,1810,1810,1810,1810]. Total = 96,990 bytes.
- f.b = pd0 short tables (11), f.j = pd0 byte tables (25).
- f.h (e.h) = ma piece offsets {0,2545,6965,10649,15487,22633,27261,31708,
  35466,39214}; ma is 42,381 bytes, 10 pieces.
- Map geometry, f.aN(): w = blob[A[149]+2q], h = blob[A[149]+2q+1];
  q==0 forces 40x32; q==5 forces w -= 32.
- Map selection: piece = blob[A[248]+q] (segment 248, 12 bytes).
- RLE, f.aN(): stream = ma bytes from h[piece]; state n7=10, n6=0.
  Per tile (row-major): if n7 >= T[n6], read next stream byte n;
  if n >= 250: n7=0, n6=n-250, n=V[n6]. Then n7 += 1; tile = n.
  T[k] = blob[A[197]+k], V[k] = blob[A[197]+6+k], k = 0..5.
  So byte < 250 is a literal tile (one tile); byte 250+k repeats tile
  V[k] for T[k] consecutive tiles. Decoded T = [4,4,2,2,2,2],
  V = [3,0,43,6,3,0].
- Random jitter: if base tile <= 8, the game adds (nextInt() & 3) % 3
  (f.a(II)I), i.e. +0..2, at load time. The Random is seeded 1L but the
  number of prior random calls is not recoverable from ma alone, so the
  canonical decode below reports BASE tiles and counts jittered tiles.
- Tile properties (aN): b9 = f.b[9][tile]; blocked if tile >= 175 or
  (b9>>13)&1; j16 = f.j[16][tile]; (j16>>6)&3 == 2 marks c=-125;
  tiles 180..231 mark c=-124; tiles 175..179 trigger a spawn call;
  border tiles are forced c=-126.

Usage: python3 decode_ma.py [--q 0..11] [--ascii] [--out ma-maps.txt]
Reads only: extracted/ma, extracted/pd0, extracted/a, extracted/0/s.
Writes nothing except stdout / the optional --out dump.
"""
import argparse
import struct
import sys
from collections import Counter

BASE = "extracted"
H = [0, 2545, 6965, 10649, 15487, 22633, 27261, 31708, 35466, 39214]
MA_SIZE = 42381
# literal length table from e.<init> (36 shorts)
PD0_LENS = [119, 1291, 162, 162, 2782, 144, 1069, 6903, 823, 1721, 5492,
            119, 1291, 1291, 1291, 162, 162, 162, 2782, 2782, 144, 1069,
            1069, 6903, 6903, 6903, 823, 1721, 42, 5492, 5492, 1810, 1810,
            1810, 1810, 1810]


def parse_a(path=f"{BASE}/a"):
    raw = open(path, "rb").read()
    off, lens, starts = 0, [], []
    for _ in range(312):
        n = struct.unpack_from("<H", raw, off)[0]
        off += 2
        lens.append(n)
        starts.append(off)
        off += n
    assert sum(lens) == 17638, sum(lens)
    blob = b"".join(raw[starts[k]:starts[k] + lens[k]] for k in range(312))
    assert len(blob) == 17638
    groups = []
    for _ in range(5):
        n = struct.unpack_from("<H", raw, off)[0]
        off += 2
        groups.append([struct.unpack_from("<H", raw, off + 2 * i)[0]
                       for i in range(n)])
        off += 2 * n
    assert off == len(raw) == 18842, (off, len(raw))
    A = [0]
    for L in lens:
        A.append(A[-1] + L)
    return lens, A, blob, groups


def parse_pd0(path=f"{BASE}/pd0"):
    pd = open(path, "rb").read()
    assert len(pd) == 96990 and pd[0] == 11
    off = 1
    shorts = []
    for i in range(11):
        n = PD0_LENS[i]
        shorts.append(list(struct.unpack_from(">" + "h" * n, pd, off)))
        off += 2 * n
    byt = []
    for i in range(25):
        n = PD0_LENS[11 + i]
        byt.append(list(pd[off:off + n]))
        off += n
    assert off == len(pd), off
    return shorts, byt


def seg(blob, A, k):
    return blob[A[k]:A[k + 1]]


def decode_map(q, ma, blob, A):
    """Return dict with base tile grid (list of rows), stats. Base tiles only."""
    w = blob[A[149] + 2 * q]
    h = blob[A[149] + 2 * q + 1]
    if q == 0:
        w, h = 40, 32
    elif q == 5:
        w -= 32
    piece = blob[A[248] + q]
    start = H[piece]
    end = H[piece + 1] if piece + 1 < len(H) else len(ma)
    stream = ma[start:end]
    T = list(blob[A[197]:A[197] + 6])
    V = list(blob[A[197] + 6:A[197] + 12])
    grid = []
    n5 = 0          # stream position
    n7 = 10         # run counter
    n6 = 0          # current run index
    n = 0           # current tile value (persists across iterations)
    literal_reads = 0
    run_reads = Counter()
    for _row in range(h):
        row = []
        for _col in range(w):
            if n7 >= T[n6]:
                if n5 >= len(stream):
                    raise ValueError(f"q={q}: stream exhausted at "
                                     f"tile {len(grid) * w + len(row)}")
                n = stream[n5]
                n5 += 1
                if n >= 250:
                    n7 = 0
                    n6 = n - 250
                    run_reads[n6] += 1
                    n = V[n6]
                else:
                    literal_reads += 1
            n7 += 1
            row.append(n)
        grid.append(row)
    return {"q": q, "w": w, "h": h, "piece": piece,
            "piece_start": start, "piece_end": end,
            "piece_len": end - start, "consumed": n5,
            "grid": grid, "T": T, "V": V,
            "literal_reads": literal_reads,
            "run_reads": dict(run_reads)}


def tile_props(tile, b9, j16):
    blocked = tile >= 175 or ((b9[tile] & 0xFFFF) >> 13 & 1) == 1
    kind = (j16[tile] & 0xFFFF) >> 6 & 3
    return blocked, kind


# ASCII legend, derived from aN() tile handling + pd0 property tables.
#   '.'  walkable low tile (base 0..5, jittered 0..7 in game)
#   'T'  blocked tile (b[9] bit13 set, e.g. base 6..8 -> game tiles 6..10)
#   '~'  j[16] class 2 (c=-125 in game)
#   'o'  tiles 180..231 (c=-124 in game)
#   'S'  tiles 175..179 (spawn points in game)
#   '#'  tiles >= 232 other than the above (incl. >=175 handled above)
#   '?'  any other tile value
def tile_char(t, b9, j16):
    if 175 <= t <= 179:
        return "S"
    if 180 <= t <= 231:
        return "o"
    blocked, kind = tile_props(t, b9, j16)
    if kind == 2:
        return "~"
    if blocked:
        return "T"
    if t <= 10:
        return "."
    return "?"


def ascii_preview(grid, b9, j16, max_rows=48, max_cols=96):
    lines = []
    step_r = max(1, len(grid) // max_rows)
    step_c = max(1, len(grid[0]) // max_cols)
    for r in range(0, len(grid), step_r):
        lines.append("".join(tile_char(grid[r][c], b9, j16)
                             for c in range(0, len(grid[0]), step_c)))
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--q", type=int, default=None)
    ap.add_argument("--ascii", action="store_true")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    lens, A, blob, _groups = parse_a()
    shorts, byt = parse_pd0()
    b9, j16 = shorts[9], byt[16]
    ma = open(f"{BASE}/ma", "rb").read()
    assert len(ma) == MA_SIZE
    names = open(f"{BASE}/0/s", encoding="utf-8", errors="replace") \
        .read().split("|")
    out = []

    def emit(s=""):
        out.append(s)
        print(s)

    emit("Prehistoric Tribes — ma map decode")
    emit("RLE control segment 197: T=%s V=%s" %
         (list(blob[A[197]:A[197] + 6]), list(blob[A[197] + 6:A[197] + 12])))
    emit("seg149 (w,h) pairs q=0..11: %s" %
         ([(blob[A[149] + 2 * q], blob[A[149] + 2 * q + 1])
           for q in range(12)]))
    emit("seg248 mapIdx q=0..11: %s" % list(blob[A[248]:A[249]]))
    emit("seg249 custom list: %s" % list(blob[A[249]:A[250]]))
    emit("seg150 spawn (x,y) pairs q=0..11: %s" %
         ([(blob[A[150] + 2 * q], blob[A[150] + 2 * q + 1])
           for q in range(12)]))
    emit("")
    qs = [args.q] if args.q is not None else list(range(12))
    for q in qs:
        d = decode_map(q, ma, blob, A)
        grid, w, h = d["grid"], d["w"], d["h"]
        flat = [t for row in grid for t in row]
        hist = Counter(flat)
        jitter = sum(1 for t in flat if t <= 8)
        # name per f.java:2348: 82 + (21 if q==7 else mapIdx[q]); mapIdx here
        # is the ma-piece index only if it equals seg248[q]; note seg248 IS
        # the mapIdx table, so name = s[82+seg248[q]] except q==7 -> s[103].
        map_idx = blob[A[248] + q]
        name = names[103] if q == 7 else names[82 + map_idx]
        emit(f"--- q={q} name={name!r} (mapIdx={map_idx}) "
             f"piece={d['piece']} [{d['piece_start']}..{d['piece_end']}) ---")
        emit(f"size: {w}x{h} = {w * h} tiles; "
             f"piece len {d['piece_len']} bytes, stream consumed "
             f"{d['consumed']} bytes ({d['consumed'] / d['piece_len']:.1%}), "
             f"unused tail {d['piece_len'] - d['consumed']} bytes")
        emit(f"literal code reads: {d['literal_reads']}, "
             f"run code reads by k: {d['run_reads']}")
        emit(f"distinct base tiles: {len(hist)}; "
             f"tiles<=8 (random +0..2 jitter at load): {jitter}")
        emit("histogram (base tile: count): %s" % dict(sorted(hist.items())))
        # property summary
        blocked = sum(1 for t in flat if tile_props(t, b9, j16)[0])
        cls2 = sum(1 for t in flat if tile_props(t, b9, j16)[1] == 2)
        spawn = sum(1 for t in flat if 175 <= t <= 179)
        mid = sum(1 for t in flat if 180 <= t <= 231)
        emit(f"blocked (b[9] bit13 or >=175): {blocked}; "
             f"j[16] class 2 (c=-125): {cls2}; "
             f"spawn tiles 175-179: {spawn}; tiles 180-231 (c=-124): {mid}")
        if args.ascii:
            emit("ASCII preview ('.'=walkable '.'/'T'=blocked '~'=class2 "
                 "'o'=180-231 'S'=spawn 175-179 '#'/ '?'=other):")
            for line in ascii_preview(grid, b9, j16):
                emit(line)
        emit("")
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write("\n".join(out) + "\n")
        print(f"[dump written to {args.out}]", file=sys.stderr)


if __name__ == "__main__":
    main()
