#!/usr/bin/env python3
"""Compare MSDC debug-mux dumps: u-boot (serial msdcbg) vs android (adb devmem).
Usage: compare_dbgmux.py uboot.txt android.txt
Format: "sel out" lines (hex), e.g. "007 00000001".
Prints sels where values differ (and equal-with-bit-info).
"""
import sys


def load(path):
    d = {}
    with open(path) as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 2:
                try:
                    sel, out = int(parts[0], 16), int(parts[1], 16)
                except ValueError:
                    continue
                d[sel] = out
    return d


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 1
    u, a = load(sys.argv[1]), load(sys.argv[2])
    sels = sorted(set(u) | set(a))
    print(f"{'sel':>5} {'uboot':>10} {'android':>10} diff_bits")
    for s in sels:
        uv, av = u.get(s, 0), a.get(s, 0)
        if uv != av:
            print(f"{s:05x} {uv:010x} {av:010x} {(uv ^ av):010x}")
    eq = sum(1 for s in sels if u.get(s, 0) == a.get(s, 0) and (u.get(s) or a.get(s)))
    print(f"\nsels with identical nonzero values: {eq}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
