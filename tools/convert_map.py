#!/usr/bin/env python3
"""Encode a mod-format v0.1 map (JSON) to the original `ma` RLE stream.

Prehistoric Tribes (J2ME, THQ/Gear Games 2008). This is the inverse of
`decode_ma.py`, which proved the RLE format from bytecode (`f.aN()`):

- Stream = bytes from `ma` starting at the piece offset `h[piece]`.
- Decoder state: n7 = 10, n6 = 0, n = 0.
- Per tile (row-major): if n7 >= T[n6], read the next stream byte;
  if it is >= 250, it is a run code 250+k: n7 = 0, n6 = k, tile = V[k].
  Otherwise the byte is one literal tile. Then n7 += 1; tile = n.
- Control table (file `/a`, segment 197): T = [4, 4, 2, 2, 2, 2],
  V = [3, 0, 43, 6, 3, 0].
- So byte < 250 = one literal tile; byte 250+k repeats tile V[k] for
  T[k] consecutive tiles. Tiles <= 8 get +0..2 random jitter at load in
  the real game, so the encoder works on BASE tiles, exactly like the
  canonical decode in `decode_ma.py`.

Encoder rule (greedy, always correct, near-minimal): whenever the
decoder would need a new stream byte, emit a run code if the next
T[k] tiles are all V[k] (preferring the longest run), otherwise emit
one literal byte for the current tile. Tiles that fall inside an
already-started run cost no bytes at all.

Usage:
    python3 convert_map.py --map mods/example/example-map.json \
        --out green-valley.ma-piece
    python3 convert_map.py --map mods/example/example-map.json --verify
    python3 convert_map.py --map mods/example/example-map.json \
        --out green-valley.ma-piece --verify --roundtrip

`--verify` decodes the encoded bytes with an independent re-implementation
of the decoder state machine and compares tile-for-tile with the input.
`--roundtrip` additionally cross-checks with `decode_ma.decode_map`
(the proven decoder) by building a synthetic `ma` + modified `/a` blob
for the chosen level slot (default q=11, piece 9).
"""
import argparse
import json
import struct
import sys
from pathlib import Path

# RLE control table, file /a segment 197 (proven, see decode_ma.py).
T = [4, 4, 2, 2, 2, 2]
V = [3, 0, 43, 6, 3, 0]

# ma piece offsets, hardcoded in the game code (e.h). Piece 9 is the
# last piece and is used only by level q=11 ("plot of land", custom-only).
H = [0, 2545, 6965, 10649, 15487, 22633, 27261, 31708, 35466, 39214]
MA_SIZE = 42381
# Level -> ma piece (file /a segment 248).
SEG248 = [0, 0, 1, 2, 3, 4, 4, 5, 6, 7, 8, 9]


def load_map(path):
    """Load and validate a mod-format v0.1 map JSON (MOD-FORMAT.md section 7)."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("format_version") != "0.1":
        raise ValueError("format_version must be '0.1'")
    if data.get("kind") != "map":
        raise ValueError("kind must be 'map'")
    w, h = int(data["width"]), int(data["height"])
    if not (1 <= w <= 96 and 1 <= h <= 96):
        raise ValueError(f"map size {w}x{h} outside 1..96")
    tiles = data["tiles"]
    if len(tiles) != h or any(len(row) != w for row in tiles):
        raise ValueError(f"tiles must be exactly {h} rows of {w} integers")
    flat = [t for row in tiles for t in row]
    if any(not isinstance(t, int) or t < 0 or t > 242 for t in flat):
        raise ValueError("every tile ID must be an integer in 0..242")
    for sp in data.get("spawns", []):
        t = sp["type"]
        if not (1 <= t <= 5):
            raise ValueError(f"spawn type {t} outside 1..5")
        r, c = sp["row"], sp["col"]
        if not (0 <= r < h and 0 <= c < w):
            raise ValueError(f"spawn at ({r},{c}) outside the map")
        if tiles[r][c] != 174 + t:
            raise ValueError(
                f"spawn type {t} at ({r},{c}) but tile there is "
                f"{tiles[r][c]}, expected {174 + t}")
    ps = data.get("player_start")
    if ps is not None:
        r, c = ps["row"], ps["col"]
        if not (0 <= r < h and 0 <= c < w):
            raise ValueError("player_start outside the map")
    wl = data["win_lose"]
    flags = int(wl["flags"])
    if not (0 <= flags <= 7):
        raise ValueError("win_lose.flags outside 0..7")
    if bool(wl["win_by_destroying_enemy_buildings"]) != bool(flags & 1):
        raise ValueError("win_by_destroying_enemy_buildings != flags & 1")
    if bool(wl["lose_if_key_building_destroyed"]) != bool(flags & 2):
        raise ValueError("lose_if_key_building_destroyed != flags & 2")
    return data, w, h, flat


def encode(tiles, w, h):
    """Encode a flat row-major tile list to an ma RLE byte stream.

    Simulates the decoder state machine and emits a byte exactly when
    the decoder would read one.
    """
    out = bytearray()
    n7, n6 = 10, 0  # decoder start state (see module docstring)
    i = 0
    total = w * h
    while i < total:
        if n7 >= T[n6]:
            # The decoder reads a new byte here. Prefer a run code.
            emitted = None
            # Longest runs first: k=0 (4x tile 3) and k=1 (4x tile 0),
            # then the 2-tile runs k=2..5.
            for k in (0, 1, 2, 3, 4, 5):
                run = T[k]
                if i + run <= total and all(tiles[i + j] == V[k]
                                            for j in range(run)):
                    emitted = k
                    break
            if emitted is not None:
                out.append(250 + emitted)
                n7, n6 = 0, emitted
            else:
                tile = tiles[i]
                if tile >= 250:
                    raise ValueError(f"tile {tile} cannot be a literal "
                                     "(>= 250)")
                out.append(tile)
                # n6 is unchanged; the literal is one tile.
            n7 += 1
            i += 1
        else:
            # Inside a run: the decoder emits V[n6] without reading.
            if tiles[i] != V[n6]:
                raise AssertionError(
                    f"encoder bug at tile {i}: inside run k={n6} "
                    f"(value {V[n6]}) but tile is {tiles[i]}")
            n7 += 1
            i += 1
    return bytes(out)


def decode_stream(stream, w, h):
    """Decode an ma RLE byte stream to a flat tile list (decoder mirror)."""
    tiles = []
    n7, n6, n = 10, 0, 0
    pos = 0
    for _ in range(w * h):
        if n7 >= T[n6]:
            if pos >= len(stream):
                raise ValueError("stream exhausted before the map was full")
            n = stream[pos]
            pos += 1
            if n >= 250:
                n7 = 0
                n6 = n - 250
                n = V[n6]
        n7 += 1
        tiles.append(n)
    return tiles, pos


def verify_roundtrip(tiles, w, h, stream):
    """Decode our own encoding and compare tile-for-tile. Returns stats."""
    decoded, consumed = decode_stream(stream, w, h)
    if decoded != tiles:
        bad = [i for i, (a, b) in enumerate(zip(decoded, tiles)) if a != b]
        raise ValueError(f"round-trip mismatch at {len(bad)} tiles, "
                         f"first at index {bad[0]}")
    return {"encoded_bytes": len(stream), "stream_consumed": consumed,
            "tiles": w * h}


def cross_check_with_proven_decoder(stream, q, base_dir):
    """Cross-check with decode_ma.decode_map (the proven decoder).

    Builds a synthetic `ma` (original bytes with the target piece
    replaced by `stream`, padded with zeroes to the piece length) and a
    modified `/a` blob whose segment 149 entry for q is (w, h) taken
    from the map JSON, then runs the proven decoder for q.
    """
    sys.path.insert(0, str(base_dir))
    import decode_ma  # noqa: E402  (local decoder, our own analysis code)

    piece = SEG248[q]
    start = H[piece]
    end = H[piece + 1] if piece + 1 < len(H) else MA_SIZE
    ma = bytearray(open(base_dir / "extracted" / "ma", "rb").read())
    assert len(ma) == MA_SIZE
    if len(stream) > end - start:
        raise ValueError(f"encoded stream ({len(stream)} bytes) is longer "
                         f"than piece {piece} ({end - start} bytes)")
    ma[start:start + len(stream)] = stream
    for i in range(start + len(stream), end):
        ma[i] = 0  # padding is never read: decoding stops after w*h tiles
    _lens, A, blob, _groups = decode_ma.parse_a(
        str(base_dir / "extracted" / "a"))
    return bytes(ma), blob, A, piece, start, end


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--map", required=True, help="mod map JSON file")
    ap.add_argument("--out", default=None,
                    help="write the encoded piece to this file")
    ap.add_argument("--verify", action="store_true",
                    help="round-trip verify the encoding")
    ap.add_argument("--roundtrip", action="store_true",
                    help="also cross-check with decode_ma.decode_map")
    ap.add_argument("--q", type=int, default=11,
                    help="level slot the piece is for (default 11)")
    ap.add_argument("--base-dir", default=".",
                    help="directory holding extracted/ and decode_ma.py")
    args = ap.parse_args()

    data, w, h, flat = load_map(args.map)
    stream = encode(flat, w, h)
    print(f"map {data['id']!r} ({data['name']!r}): {w}x{h} = {w * h} tiles")
    print(f"encoded: {len(stream)} bytes "
          f"({len(stream) / (w * h):.2f} bytes/tile)")
    if args.out:
        Path(args.out).write_bytes(stream)
        print(f"[wrote {args.out}]")
    if args.verify or args.roundtrip:
        stats = verify_roundtrip(flat, w, h, stream)
        print(f"round-trip: OK, {stats['tiles']} tiles identical, "
              f"stream consumed {stats['stream_consumed']} bytes")
    if args.roundtrip:
        sys.path.insert(0, str(Path(args.base_dir).resolve()))
        import decode_ma
        ma, blob, A, piece, start, end = cross_check_with_proven_decoder(
            stream, args.q, Path(args.base_dir))
        blob2 = bytearray(blob)
        blob2[A[149] + 2 * args.q] = w
        blob2[A[149] + 2 * args.q + 1] = h
        d = decode_ma.decode_map(args.q, bytes(ma), bytes(blob2), A)
        if d["grid"] != [flat[i * w:(i + 1) * w] for i in range(h)]:
            raise ValueError("proven-decoder cross-check FAILED: "
                             "decoded grid != input grid")
        print(f"proven-decoder cross-check: OK (q={args.q}, piece={piece}, "
              f"[{start}..{end}), consumed {d['consumed']} bytes, "
              f"{d['consumed'] / d['piece_len']:.1%} of the piece)")


if __name__ == "__main__":
    main()
