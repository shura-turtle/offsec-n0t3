#!/usr/bin/env python3
"""Invert the shipped VFP1 ruleset's twelve Feistel-style rounds."""

import argparse
import struct
import subprocess
from pathlib import Path

MASK = (1 << 64) - 1
GOLDEN_RATIO = 0x9E3779B97F4A7C15
EXPECTED = [
    0x372EDCC427080478,
    0xF0A9BDC7E4035851,
    0x3B5150DDAD266030,
    0xBA7BB8D6869F10D5,
]


def rol(value: int, bits: int) -> int:
    bits &= 63
    return ((value << bits) | (value >> ((64 - bits) & 63))) & MASK


def ror(value: int, bits: int) -> int:
    return rol(value, -bits)


def solve(binary: Path, rules: Path) -> bytes:
    elf = binary.read_bytes()
    blob = rules.read_bytes()
    assert blob[:4] == b"VFP1"
    assert len(blob) == 12 + 212 * 8
    sbox = elf[0x3020:0x3120]
    assert len(sbox) == 256 and len(set(sbox)) == 256

    def imm(index: int) -> int:
        return struct.unpack_from("<I", blob, 12 + 8 * index + 4)[0]

    keys = [imm(16 + 16 * i) | (imm(17 + 16 * i) << 32) for i in range(12)]

    def round_function(word: int, round_index: int) -> int:
        substituted = sum(sbox[(word >> (8 * j)) & 255] << (8 * j) for j in range(8))
        mixed = (substituted * GOLDEN_RATIO ^ ror(word, 29)) & MASK
        return rol(mixed, word.bit_count() + 7 * round_index) ^ keys[round_index]

    words = EXPECTED.copy()
    for i in reversed(range(12)):
        words[i % 4] ^= round_function(words[(i + 1) % 4], i)
    token = b"".join(word.to_bytes(8, "little") for word in words)
    assert len(token) == 32 and all(32 <= byte <= 126 for byte in token)
    return token


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("rules", type=Path)
    args = parser.parse_args()
    token = solve(args.binary, args.rules)
    result = subprocess.run(
        [str(args.binary.resolve()), str(args.rules.resolve())],
        input=token + b"\n",
        capture_output=True,
        check=True,
    )
    assert b"verdict: PASS" in result.stdout, result.stdout + result.stderr
    print(token.decode("ascii"))


if __name__ == "__main__":
    main()
