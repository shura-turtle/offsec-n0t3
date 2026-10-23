#!/usr/bin/env python3
"""Extract an explicit image bitstream or save a visible plane. Pillow required."""
import argparse
from pathlib import Path
import sys


def nonnegative(text):
    try:
        value = int(text, 0)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("expected decimal or 0x-prefixed integer") from exc
    if value < 0:
        raise argparse.ArgumentTypeError("must be nonnegative")
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path, help="new binary output, or PNG with --plane")
    parser.add_argument("--channels", help="ordered channel letters: rgb, bgr, r, a, l or i (palette index)")
    parser.add_argument("--bit", type=int, choices=range(8), default=0, help="bit plane; zero is the LSB")
    parser.add_argument("--order", choices=["row", "column"], default="row")
    parser.add_argument("--skip-bits", type=nonnegative, default=0)
    parser.add_argument("--pack", choices=["msb", "lsb"], default="msb", help="significance of first collected bit in each output byte")
    parser.add_argument("--bytes", type=nonnegative, default=1024 * 1024, help="maximum extracted bytes; default 1 MiB")
    parser.add_argument("--frame", type=nonnegative, default=0)
    parser.add_argument("--plane", action="store_true", help="save one channel bit plane as lossless black/white PNG")
    args = parser.parse_args()
    try:
        from PIL import Image
    except ImportError:
        parser.exit(2, "error: Pillow is optional and not installed; use supplied zsteg or an event-approved installation\n")
    try:
        if args.source.resolve() == args.output.resolve():
            raise ValueError("output must differ from source")
        with Image.open(args.source) as image:
            image.seek(args.frame)
            image.load()
            modes = {"RGB": "rgb", "RGBA": "rgba", "L": "l", "P": "i"}
            if image.mode not in modes:
                raise ValueError(f"mode {image.mode!r} unsupported; no implicit color/depth conversion is performed")
            available = modes[image.mode]
            channels = args.channels or ("rgb" if "r" in available else available)
            if not channels or len(set(channels)) != len(channels) or any(c not in available for c in channels):
                raise ValueError(f"channels must be unique letters from {available!r}")
            positions = [available.index(c) for c in channels]
            width, height = image.size
            pixels = image.load()
            print(f"mode={image.mode} size={width}x{height} frame={args.frame} channels={channels} bit={args.bit}", file=sys.stderr)
            if args.plane:
                if len(channels) != 1 or args.skip_bits:
                    raise ValueError("--plane needs exactly one channel and --skip-bits 0")
                if args.output.suffix.lower() != ".png":
                    raise ValueError("plane output must end in .png (lossless)")
                plane = Image.new("L", image.size)
                target = plane.load()
                for y in range(height):
                    for x in range(width):
                        pixel = pixels[x, y]
                        value = pixel[positions[0]] if isinstance(pixel, tuple) else pixel
                        target[x, y] = 255 * ((value >> args.bit) & 1)
                with args.output.open("xb") as dst:
                    plane.save(dst, format="PNG")
                return
            capacity = width * height * len(positions)
            if args.skip_bits >= capacity or args.bytes == 0:
                raise ValueError("skip-bits must be below capacity and --bytes must be positive")
            coordinates = ((x, y) for y in range(height) for x in range(width)) if args.order == "row" else ((x, y) for x in range(width) for y in range(height))
            skip, pending, count, written = args.skip_bits, 0, 0, 0
            with args.output.open("xb") as dst:
                for x, y in coordinates:
                    pixel = pixels[x, y]
                    values = pixel if isinstance(pixel, tuple) else (pixel,)
                    for position in positions:
                        if skip:
                            skip -= 1
                            continue
                        bit = (values[position] >> args.bit) & 1
                        pending |= bit << (7 - count if args.pack == "msb" else count)
                        count += 1
                        if count == 8:
                            dst.write(bytes([pending]))
                            written += 1
                            pending, count = 0, 0
                            if written >= args.bytes:
                                print(f"wrote {written} bytes (requested limit reached)", file=sys.stderr)
                                return
            print(f"wrote {written} bytes; discarded {count} trailing incomplete bits", file=sys.stderr)
    except (OSError, ValueError, EOFError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    main()
