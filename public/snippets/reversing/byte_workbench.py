#!/usr/bin/env python3
"""Offline byte transforms. Binary input/output; no network or third-party modules."""
import argparse
import base64
import binascii
import codecs
from pathlib import Path
import sys


def integer(value):
    try:
        return int(value, 0)
    except ValueError as exc:
        raise argparse.ArgumentTypeError('use decimal or 0x-prefixed hex') from exc


def xor(data, key):
    if not key:
        raise ValueError('XOR key must not be empty')
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def rotate(data, count, right=False):
    count %= 8
    if right:
        count = (-count) % 8
    return bytes(((b << count) | (b >> ((8-count) % 8))) & 255 for b in data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--file', type=Path, help='input bytes from file')
    source.add_argument('--hex', help='input bytes as hexadecimal')
    source.add_argument('--text', help='UTF-8 input text')
    parser.add_argument('--offset', type=integer, default=0)
    parser.add_argument('--length', type=integer, help='slice length; default to end')
    parser.add_argument('--output', type=Path, help='write raw bytes; default print hex and repr')
    ops = parser.add_subparsers(dest='operation', required=True)
    xp = ops.add_parser('xor', help='single-byte or repeating-key XOR')
    xp.add_argument('--key-hex', required=True)
    ops.add_parser('xor-scan', help='print all 256 single-byte XOR candidates')
    for name in ('rol', 'ror', 'add', 'sub'):
        p = ops.add_parser(name)
        p.add_argument('count', type=integer)
    ops.add_parser('reverse', help='reverse byte sequence')
    sw = ops.add_parser('swap', help='reverse each fixed-width word')
    sw.add_argument('width', type=integer, choices=(2, 4, 8))
    for op in ('b64decode', 'b64encode', 'hexdecode', 'hexencode', 'rot13'):
        ops.add_parser(op)
    ns = parser.parse_args()
    try:
        data = ns.file.read_bytes() if ns.file else bytes.fromhex(ns.hex) if ns.hex is not None else ns.text.encode('utf-8')
        if ns.offset < 0 or ns.offset > len(data) or (ns.length is not None and ns.length < 0):
            raise ValueError('slice offset/length outside input range')
        end = None if ns.length is None else ns.offset + ns.length
        if end is not None and end > len(data):
            raise ValueError('slice length extends past input')
        data = data[ns.offset:end]
        op = ns.operation
        if op == 'xor-scan':
            if ns.output:
                raise ValueError('xor-scan produces candidate text; omit --output')
            for key in range(256):
                candidate = xor(data, bytes([key]))
                score = sum(32 <= b < 127 or b in (9,10,13) for b in candidate) / max(len(candidate), 1)
                print(f'{key:02x} printable={score:.2f} {candidate!r}')
            return
        if op == 'xor':
            result = xor(data, bytes.fromhex(ns.key_hex))
        elif op in ('rol', 'ror'):
            result = rotate(data, ns.count, right=op == 'ror')
        elif op in ('add', 'sub'):
            delta = ns.count if op == 'add' else -ns.count
            result = bytes((b + delta) & 255 for b in data)
        elif op == 'reverse':
            result = data[::-1]
        elif op == 'swap':
            if len(data) % ns.width:
                raise ValueError('input length must be divisible by swap width')
            result = b''.join(data[i:i+ns.width][::-1] for i in range(0,len(data),ns.width))
        elif op == 'b64decode':
            # Standard alphabet, optional whitespace; deliberately no silent padding repair.
            result = base64.b64decode(b''.join(data.split()), validate=True)
        elif op == 'b64encode':
            result = base64.b64encode(data)
        elif op == 'hexdecode':
            result = bytes.fromhex(data.decode('ascii'))
        elif op == 'hexencode':
            result = data.hex().encode('ascii')
        elif op == 'rot13':
            result = codecs.encode(data.decode('ascii'), 'rot_13').encode('ascii')
        else:
            raise ValueError('unknown operation')
        if ns.output:
            ns.output.write_bytes(result)
        else:
            print(result.hex())
            print(repr(result))
    except (ValueError, OSError, UnicodeError, binascii.Error) as exc:
        parser.exit(2, f'error: {exc}\n')


if __name__ == '__main__':
    main()
