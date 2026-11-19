#!/usr/bin/env python3
"""Decode Prehistoric Tribes (J2ME, THQ 2008) packed data files.

Proven layout (from decompiled e.java, CFR 0.152, --renamedupmembers):

/pd0 (96,990 bytes) — balance tables, read by e.b():
  - byte 0: discarded (value 0x0b = 11, the number of short tables)
  - then 11 short tables (big-endian DataInputStream.readShort),
    then 25 byte tables (readByte), in order.
  - table lengths come from e's own field:
      short[] SIZES = {119,1291,162,162,2782,144,1069,6903,823,1721,5492,
                       119,1291,1291,1291,162,162,162,2782,2782,144,
                       1069,1069,6903,6903,6903,823,1721,42,5492,5492,
                       1810,1810,1810,1810,1810}
    indices 0..10  -> short tables b[0..10]
    indices 11..35 -> byte  tables j[0..24]   (j[i] length = SIZES[11+i])

/a (18,842 bytes) — packed record container, read by e.f():
  - INTERLEAVED: 312 x [LE u16 record length][that many blob bytes].
    Record n lives at blob[cum[n] .. cum[n]+len[n]], cum[0]=0.
    (f.var_short_arr_a = cum offsets, f.var_byte_arr_a = blob.)
  - then 5 x [LE u16 group length][that many BE u16 values]
    (f.var_short_arr_b, capacity 570).
  Game code indexes game data as blob[ cum[REC] + offset ].
  Key records (proven by use in b.java / f.java):
    138 = building data table, 26-byte rows
    248 = level -> map number
    195, 219, 296, 298, 305, 306, 99, 1, 41, 42, 139, 140, 142, 145 = misc

Usage: python3 decode_pd0.py [--dump-all]
Writes pd0-tables.txt (and prints a summary).
"""
import struct
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
SIZES = [119, 1291, 162, 162, 2782, 144, 1069, 6903, 823, 1721, 5492,
         119, 1291, 1291, 1291, 162, 162, 162, 2782, 2782, 144,
         1069, 1069, 6903, 6903, 6903, 823, 1721, 42, 5492, 5492,
         1810, 1810, 1810, 1810, 1810]


def parse_pd0(path):
    data = Path(path).read_bytes()
    assert len(data) == 96990, len(data)
    assert data[0] == 0x0B, hex(data[0])  # discarded byte = 11 short tables
    off = 1
    shorts = []
    for i in range(11):
        n = SIZES[i]
        vals = list(struct.unpack_from(f">{n}h", data, off))
        off += 2 * n
        shorts.append(vals)
    byte_tables = []
    for i in range(25):
        n = SIZES[11 + i]
        vals = list(data[off:off + n])
        off += n
        byte_tables.append(vals)
    assert off == len(data), (off, len(data))
    return shorts, byte_tables


def parse_a(path):
    """File /a is INTERLEAVED: [LE u16 len][len blob bytes] x312,
    then 5x [LE u16 group len][group len BE u16 values].
    var_short_arr_a[n] = cumulative blob offset of record n."""
    data = Path(path).read_bytes()
    assert len(data) == 18842, len(data)
    pos = 0
    lens, cum, blob = [], [0], bytearray()
    for _ in range(312):
        (n,) = struct.unpack_from("<H", data, pos)
        pos += 2
        lens.append(n)
        blob += data[pos:pos + n]
        pos += n
        cum.append(len(blob))
    assert len(blob) == 17638, len(blob)
    glens, groups = [], []
    for _ in range(5):
        (g,) = struct.unpack_from("<H", data, pos)
        pos += 2
        glens.append(g)
        vals = list(struct.unpack_from(f">{g}H", data, pos))
        pos += 2 * g
        groups.append(vals)
    assert pos == len(data), (pos, len(data))
    return lens, cum, bytes(blob), glens, groups


def fmt_short_table(vals, per_line=20):
    lines = []
    for i in range(0, len(vals), per_line):
        chunk = vals[i:i + per_line]
        lines.append(f"  [{i:5d}] " + " ".join(f"{v:6d}" for v in chunk))
    return "\n".join(lines)


def fmt_byte_table(vals, per_line=32):
    lines = []
    for i in range(0, len(vals), per_line):
        chunk = vals[i:i + per_line]
        lines.append(f"  [{i:5d}] " + " ".join(f"{v:3d}" for v in chunk))
    return "\n".join(lines)


def main():
    shorts, byte_tables = parse_pd0(BASE / "extracted" / "pd0")
    lens, cum, blob, glens, groups = parse_a(BASE / "extracted" / "a")
    out = []
    out.append("=" * 78)
    out.append("PREHISTORIC TRIBES — pd0 + a DECODE")
    out.append("pd0: 96,990 bytes = 1 header byte + 11 short tables "
               f"({sum(SIZES[:11])} shorts = {2 * sum(SIZES[:11])} bytes) + "
               f"25 byte tables ({sum(SIZES[11:])} bytes)")
    out.append("a:   18,842 bytes = 312 LE u16 lengths + 17,638-byte blob + "
               f"5 groups ({sum(glens)} u16 values)")
    out.append("=" * 78)

    out.append("\n### /pd0 SHORT tables b[0..10] (big-endian signed short)\n")
    for i, vals in enumerate(shorts):
        out.append(f"--- b[{i}] len={len(vals)} min={min(vals)} max={max(vals)} "
                   f"first={vals[:8]}")
        out.append(fmt_short_table(vals))
    out.append("\n### /pd0 BYTE tables j[0..24] (unsigned byte)\n")
    for i, vals in enumerate(byte_tables):
        out.append(f"--- j[{i}] len={len(vals)} min={min(vals)} max={max(vals)} "
                   f"first={vals[:16]}")
        out.append(fmt_byte_table(vals))

    out.append("\n### /a RECORD lengths (312 records, LE u16) — nonzero only\n")
    for i, L in enumerate(lens):
        if L:
            out.append(f"  rec[{i:3d}] len={L:5d} cum_off={cum[i]:5d}")
    out.append(f"\n  total blob bytes used: {cum[-1]} / 17638; "
               f"zero-length records: {sum(1 for L in lens if L == 0)}")
    out.append("\n### /a GROUPS (5 groups, BE u16)\n")
    for i, g in enumerate(groups):
        out.append(f"--- group[{i}] len={len(g)} values={g}")

    out.append("\n### /a KEY RECORDS (raw bytes)\n")
    for rec in [1, 41, 42, 99, 138, 139, 140, 142, 145, 195, 219, 248,
                296, 298, 305, 306]:
        s, e = cum[rec], cum[rec + 1]
        out.append(f"--- rec[{rec}] len={e - s} off={s} bytes={list(blob[s:e])}")

    text = "\n".join(out) + "\n"
    (BASE / "pd0-tables.txt").write_text(text)
    print(text[:4000])
    print(f"\n... full dump written to {BASE / 'pd0-tables.txt'} "
          f"({len(text)} chars)")


if __name__ == "__main__":
    main()
