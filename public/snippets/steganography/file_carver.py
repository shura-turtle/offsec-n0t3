#!/usr/bin/env python3
"""List signature candidates or copy an explicit bounded byte range; stdlib only."""
import argparse
import hashlib
import mmap
from pathlib import Path
import sys

MAGIC = {
    "png": bytes.fromhex("89504e470d0a1a0a"),
    "jpeg": bytes.fromhex("ffd8ff"),
    "zip-local": b"PK\x03\x04",
    "zip-eocd": b"PK\x05\x06",
    "gzip": bytes.fromhex("1f8b08"),
    "xz": bytes.fromhex("fd377a585a00"),
    "pdf": b"%PDF-",
    "riff": b"RIFF",
}


def number(value):
    try:
        result = int(value, 0)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("use decimal or 0x-prefixed hex") from exc
    if result < 0:
        raise argparse.ArgumentTypeError("must be nonnegative")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    scan = sub.add_parser("scan", help="list candidate offsets; no extraction")
    scan.add_argument("source", type=Path)
    scan.add_argument("--magic", help="custom hexadecimal signature")
    scan.add_argument("--max-hits", type=number, default=100)
    extract = sub.add_parser("extract", help="copy only the specified byte interval")
    extract.add_argument("source", type=Path)
    extract.add_argument("output", type=Path)
    extract.add_argument("--offset", type=number, required=True)
    extent = extract.add_mutually_exclusive_group(required=True)
    extent.add_argument("--length", type=number)
    extent.add_argument("--to-eof", action="store_true")
    extract.add_argument("--max-bytes", type=number, default=64 * 1024 * 1024)
    args = parser.parse_args()
    try:
        size = args.source.stat().st_size
        if not args.source.is_file():
            raise ValueError("source must be a regular file")
        if args.action == "scan":
            signatures = MAGIC
            if args.magic is not None:
                magic = bytes.fromhex(args.magic)
                if not magic:
                    raise ValueError("custom signature must not be empty")
                signatures = {"custom": magic}
            if args.max_hits == 0:
                raise ValueError("max-hits must be positive")
            if size == 0:
                return
            with args.source.open("rb") as src, mmap.mmap(src.fileno(), 0, access=mmap.ACCESS_READ) as view:
                hits = 0
                for label, signature in signatures.items():
                    position = view.find(signature)
                    while position != -1:
                        print(f"{label}\t{position}\t0x{position:x}")
                        hits += 1
                        if hits >= args.max_hits:
                            print("hit limit reached; candidates are not validated files", file=sys.stderr)
                            return
                        position = view.find(signature, position + 1)
            return
        if args.source.resolve() == args.output.resolve():
            raise ValueError("output must differ from source")
        length = size - args.offset if args.to_eof else args.length
        if args.offset > size or length <= 0 or length > size - args.offset:
            raise ValueError("requested interval is empty or outside the source")
        if length > args.max_bytes:
            raise ValueError("interval exceeds --max-bytes; choose a tighter range or raise the cap explicitly")
        digest = hashlib.sha256()
        with args.source.open("rb") as src, args.output.open("xb") as dst:
            src.seek(args.offset)
            remaining = length
            while remaining:
                block = src.read(min(1024 * 1024, remaining))
                if not block:
                    raise ValueError("source changed or was truncated during extraction")
                dst.write(block)
                digest.update(block)
                remaining -= len(block)
        print(f"offset={args.offset} length={length} sha256={digest.hexdigest()}")
    except (OSError, ValueError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    main()
