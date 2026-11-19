#!/usr/bin/env python3
"""Split Prehistoric Tribes J2ME sprite packs (pi0, pi8, pi9) into individual PNGs.

Format (proven from e.java d() and f.java c(byte)):
  Each pack is a concatenation of PNG files. Every PNG is prefixed by a
  2-byte big-endian length, EXCEPT the stream is terminated by a 0xFF byte
  (255) as the first byte of a length prefix (e.java d(): `if (by3 == 255)
  break`). The loader reads at most `by` images, where `by` is the
  expected count passed by the caller (e.java: pi0/pi9 via d() with
  this.a[this.a] -- the pack index; f.java c(byte): at most 12 images
  from pi8, stopping at 0xFF, and only the requested index is kept).
  In e.java d() the whole file is read into a fixed 62502-byte buffer
  (the size of pi0), and only the first 27 images are actually created
  (`if (by2 < 27)`).

Usage:
  python3 extract_pngs.py
  python3 extract_pngs.py --out sprites --list-only

Output: sprites/<pack>/<index:02d>.png  (index = order in the file)
Also writes sprites/<pack>/index.csv with offset, length, width, height.
"""
import argparse
import csv
import struct
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
EXTRACTED = BASE / "extracted"
PACKS = ("pi0", "pi8", "pi9")


def split_pack(data: bytes, name: str):
    """Yield (index, offset_of_length_prefix, length, png_bytes).

    Stops at a 0xFF terminator byte, at end of data, or on a truncated
    entry. Raises ValueError on a bad PNG magic (sanity check).
    """
    out = []
    pos = 0
    idx = 0
    while pos < len(data):
        first = data[pos]
        if first == 0xFF:
            break  # terminator, seen in e.java d()
        if pos + 2 > len(data):
            break
        length = struct.unpack(">H", data[pos:pos + 2])[0]
        png_start = pos + 2
        png_end = png_start + length
        if length == 0 or png_end > len(data):
            break  # truncated / corrupt entry
        png = data[png_start:png_end]
        if png[:8] != b"\x89PNG\r\n\x1a\n":
            raise ValueError(
                f"{name}[{idx}] at offset {pos}: bad PNG magic {png[:8]!r}"
            )
        out.append((idx, pos, length, png))
        pos = png_end
        idx += 1
    return out, pos


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="sprites", help="output directory")
    ap.add_argument("--list-only", action="store_true",
                    help="only list counts/dimensions, do not write PNGs")
    args = ap.parse_args()
    out_root = BASE / args.out
    try:
        from PIL import Image
    except ImportError:
        Image = None
        print("PIL not available: dimensions will be read from the IHDR chunk",
              file=sys.stderr)

    for name in PACKS:
        path = EXTRACTED / name
        data = path.read_bytes()
        try:
            entries, end_pos = split_pack(data, name)
        except ValueError as exc:
            print(f"{name}: ERROR {exc}", file=sys.stderr)
            continue
        print(f"{name}: {len(data)} bytes -> {len(entries)} PNGs, "
              f"consumed {end_pos} bytes, {len(data) - end_pos} trailing bytes")
        rows = []
        for idx, offset, length, png in entries:
            if Image is not None:
                import io
                with Image.open(io.BytesIO(png)) as im:
                    w, h = im.size
                    mode = im.mode
            else:
                w, h = struct.unpack(">II", png[16:24])
                mode = "?"
            rows.append((idx, offset, length, w, h, mode))
            print(f"  {name}[{idx:02d}] off={offset:6d} len={length:6d} "
                  f"{w}x{h} mode={mode}")
            if not args.list_only:
                dest = out_root / name
                dest.mkdir(parents=True, exist_ok=True)
                (dest / f"{idx:02d}.png").write_bytes(png)
        if not args.list_only:
            dest = out_root / name
            dest.mkdir(parents=True, exist_ok=True)
            with open(dest / "index.csv", "w", newline="") as fh:
                wr = csv.writer(fh)
                wr.writerow(["index", "offset", "length", "width", "height", "mode"])
                wr.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
