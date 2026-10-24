#!/usr/bin/env python3
"""Inspect escaped Unicode code points, or extract a two-symbol binary stream."""
import argparse
from collections import Counter
from pathlib import Path
import sys
import unicodedata


def codepoint(value):
    try:
        number = int(value.removeprefix("U+").removeprefix("u+"), 16)
        if not 0 <= number <= 0x10FFFF or 0xD800 <= number <= 0xDFFF:
            raise ValueError
        return chr(number)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("expected a scalar code point such as U+200B") from exc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--encoding", default="utf-8", help="strict input decoding; default UTF-8")
    parser.add_argument("--all", action="store_true", help="inspect ASCII printable characters too")
    parser.add_argument("--limit", type=int, default=200, help="maximum inspected rows")
    parser.add_argument("--zero", type=codepoint, help="zero-symbol code point; requires --one and --output")
    parser.add_argument("--one", type=codepoint)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--skip-bits", type=int, default=0)
    parser.add_argument("--pack", choices=["msb", "lsb"], default="msb")
    args = parser.parse_args()
    try:
        text = args.source.read_bytes().decode(args.encoding, errors="strict")
        if args.skip_bits < 0 or args.limit < 1:
            raise ValueError("skip-bits must be nonnegative and limit positive")
        print(f"characters={len(text)} unicode_database={unicodedata.unidata_version}", file=sys.stderr)
        extracting = any(v is not None for v in (args.zero, args.one, args.output))
        if extracting:
            if args.zero is None or args.one is None or args.output is None:
                raise ValueError("extraction requires --zero, --one and --output")
            if args.zero == args.one or args.output.resolve() == args.source.resolve():
                raise ValueError("symbols must differ and output must differ from source")
            bits = [(0 if char == args.zero else 1) for char in text if char in (args.zero, args.one)]
            bits = bits[args.skip_bits:]
            if len(bits) < 8:
                raise ValueError("fewer than eight selected bits remain")
            with args.output.open("xb") as output:
                for start in range(0, len(bits) - 7, 8):
                    group = bits[start:start + 8]
                    value = sum(bit << (7 - index if args.pack == "msb" else index) for index, bit in enumerate(group))
                    output.write(bytes([value]))
            print(f"selected_bits={len(bits)} bytes={len(bits)//8} discarded_bits={len(bits)%8}", file=sys.stderr)
            return
        counts = Counter(text)
        rows = 0
        for index, char in enumerate(text):
            if args.all or not (" " <= char <= "~"):
                name = unicodedata.name(char, "UNNAMED")
                print(f"index={index} U+{ord(char):04X} escaped={ascii(char)} category={unicodedata.category(char)} bidi={unicodedata.bidirectional(char)!r} name={name} total={counts[char]}")
                rows += 1
                if rows >= args.limit:
                    print("inspection row limit reached", file=sys.stderr)
                    break
    except (OSError, UnicodeError, ValueError, LookupError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    main()
