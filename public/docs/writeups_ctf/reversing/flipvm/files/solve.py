#!/usr/bin/env python3
"""Patch the supplied FlipVM bytecode and replay its native VM.

Patch construction follows FlipVM/Solution/patch.py in the public challenge repo.
"""
import argparse
import hashlib
from pathlib import Path
import subprocess

P = 4013756539255022581843
Q = 4032658848359024928157
N = P * Q
E = 0x10001
ENTRY_TARGET = 0xFA1
MODE = bytes.fromhex('580101')
MOV = bytes.fromhex('28881f243f245f5f4c65545f5468235f6840636b216e675f623367316e5f5f243f24')
EXPECTED_SHA1 = '130e5d13e04e853178598f844c2c3cd7979e1961'
FLAG = b"CMO{<-*~-~*~-.1'm++In.-~*~-~*->}"

def challenge_hash(code):
    value = 0x3140101438
    for byte in code:
        spread = sum(byte << (8 * i) for i in range(8))
        value = (value * 8675309) ^ spread
    return value & 0xffffffffffffffff

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('vm', type=Path)
    parser.add_argument('bytecode', type=Path)
    parser.add_argument('--out', type=Path, default=Path('patched.flp'))
    args = parser.parse_args()
    original = args.bytecode.read_bytes()
    assert hashlib.sha1(original).hexdigest() == EXPECTED_SHA1, 'This patch targets the published handout only'
    assert original[:3] == b'FLP'
    code = bytearray(original[266:])
    entry = ENTRY_TARGET - len(MODE) - len(MOV)
    code[entry:entry + len(MODE) + len(MOV)] = MODE + MOV
    signature = pow(challenge_hash(code), E, N)
    header = (b'FLP' + N.to_bytes(128, 'little') + E.to_bytes(3, 'little')
              + signature.to_bytes(128, 'little')
              + ((signature ^ entry) & 0xffffffff).to_bytes(4, 'little'))
    output = args.out.resolve()
    output.write_bytes(header + code)
    run = subprocess.run([str(args.vm.resolve()), str(output)], capture_output=True, timeout=20)
    raw = run.stdout + run.stderr
    # Native PRINT sometimes leaks DLE bytes between the human-readable chunks.
    # Keep the raw output visible; remove only those observed 0x10 separators.
    print(repr(raw))
    assert FLAG in raw.replace(b'\x10', b''), 'Expected flag absent from VM output'
    print(FLAG.decode())

if __name__ == '__main__':
    main()
