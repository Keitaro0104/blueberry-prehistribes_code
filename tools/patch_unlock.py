#!/usr/bin/env python3
"""Patch f.class so the Custom Game gate in f.aw() always passes.

Gate (decompiled with CFR 0.152, f.java aw()):
    private void aw() {
        this.q = (byte)7;
        this.R = this.Q;
        if (this.W) { ... Q=3 ... }
        else if (this.r > 0 || this.af) { Q = 13; Z = 1; }  // custom game list
        else { this.v = 70; Q = 21; Z = 0; }               // "pass the tutorial first!"
        this.aa = 1;
    }

javap bytecode of aw():
    34: aload_0
    35: getfield      r:B
    38: ifgt          48        <- opcode 0x9D, 3 bytes, branch offset +10
    41: aload_0
    42: getfield      af:Z
    45: ifeq          62
    48: aload_0 ... Q=13 ...

Patch: single byte at code offset 38, 0x9D (ifgt) -> 0x9C (ifge).
Same instruction size (3 bytes), same branch target (48), and ifge still
POPS the loaded value, so the stack depth at every join point is unchanged
(no VerifyError). The progress byte `r` is only ever assigned 0..7 by the
game itself (fresh save = 0; `r = s` where s is the highest unlocked level;
`r = 4` in the cheat path), so `r >= 0` is always true in practice and the
branch to the Custom Game list (Q=13) is always taken. The `af` check at
41-45 remains as a fallback.
NOTE: an earlier attempt used 0xA7 (goto) here, which does NOT pop the
value and failed with "VerifyError: Stack size too large" — do not use goto.
"""
import struct
import sys


def parse_class(data):
    """Return (methods, ) — minimal class-file parser locating method Code attrs."""
    assert data[:4] == b"\xca\xfe\xba\xbe", "not a class file"
    p = 8
    cp_count = struct.unpack(">H", data[p:p + 2])[0]
    p += 2
    cp = [None] * cp_count  # 1-based
    i = 1
    while i < cp_count:
        tag = data[p]
        if tag == 1:  # Utf8
            ln = struct.unpack(">H", data[p + 1:p + 3])[0]
            cp[i] = data[p + 3:p + 3 + ln].decode("utf-8", "replace")
            p += 3 + ln
        elif tag in (7, 8, 16, 19, 20):  # Class, String, MethodType, Module, Package
            p += 3
        elif tag in (15,):  # MethodHandle
            p += 4
        elif tag in (3, 4, 9, 10, 11, 12, 17, 18):
            p += 5
        elif tag in (5, 6):  # Long, Double: two slots
            p += 9
            i += 1
        else:
            raise ValueError(f"unknown constant pool tag {tag} at {p}")
        i += 1
    p += 6  # access_flags, this_class, super_class
    # interfaces
    n = struct.unpack(">H", data[p:p + 2])[0]
    p += 2 + 2 * n
    # fields
    n = struct.unpack(">H", data[p:p + 2])[0]
    p += 2
    for _ in range(n):
        p += 6
        na = struct.unpack(">H", data[p:p + 2])[0]
        p += 2
        for _ in range(na):
            alen = struct.unpack(">I", data[p + 2:p + 6])[0]
            p += 6 + alen
    # methods
    n = struct.unpack(">H", data[p:p + 2])[0]
    p += 2
    methods = []
    for _ in range(n):
        access, name_idx, desc_idx = struct.unpack(">HHH", data[p:p + 6])
        p += 6
        na = struct.unpack(">H", data[p:p + 2])[0]
        p += 2
        code_off = None
        code_len = None
        for _ in range(na):
            aname = cp[struct.unpack(">H", data[p:p + 2])[0]]
            alen = struct.unpack(">I", data[p + 2:p + 6])[0]
            if aname == "Code":
                # attr header is 6 bytes; then max_stack(2), max_locals(2),
                # code_length(4), code[code_length]
                code_len = struct.unpack(">I", data[p + 6 + 4:p + 6 + 8])[0]
                code_off = p + 6 + 8
            p += 6 + alen
        methods.append((cp[name_idx], cp[desc_idx], code_off, code_len))
    return methods


def main(src, dst):
    data = bytearray(open(src, "rb").read())
    methods = parse_class(bytes(data))
    target = [m for m in methods if m[0] == "aw"]
    assert len(target) == 1, f"aw method count: {len(target)}"
    name, desc, code_off, code_len = target[0]
    print(f"method aw {desc}: code at file offset {code_off}, len {code_len}")
    code = data[code_off:code_off + code_len]
    # Verify expected bytes around the gate:
    # offset 34: aload_0 (0x2A), 35: getfield (0xB4 xx xx), 38: ifgt (0x9D 0x00 0x0A)
    # offset 41: aload_0, 42: getfield af, 45: ifeq (0x99 0x00 0x11), 48: aload_0
    assert code[34] == 0x2A and code[35] == 0xB4, f"unexpected bytes at 34: {code[34]:02x} {code[35]:02x}"
    assert code[38] == 0x9D and code[39] == 0x00 and code[40] == 0x0A, \
        f"ifgt not found at 38: {code[38]:02x} {code[39]:02x} {code[40]:02x}"
    assert code[41] == 0x2A and code[42] == 0xB4, "af getfield not found at 41"
    assert code[45] == 0x99 and code[46] == 0x00 and code[47] == 0x11, \
        f"ifeq not found at 45: {code[45]:02x} {code[46]:02x} {code[47]:02x}"
    assert code[48] == 0x2A, "expected aload_0 at 48"
    data[code_off + 38] = 0x9C  # ifgt -> ifge (r >= 0 always true; keeps the pop)
    open(dst, "wb").write(bytes(data))
    print(f"patched byte at file offset {code_off + 38}: 0x9D (ifgt) -> 0x9C (ifge)")
    print(f"wrote {dst} ({len(data)} bytes, same size as input)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
