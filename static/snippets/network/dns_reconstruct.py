#!/usr/bin/env python3
"""Reconstruct encoded query-name chunks from a TShark export; offline stdlib."""
import argparse
import base64
import binascii
import re
import sys
from pathlib import Path


def reconstruct(lines, suffix, encoding, sequence, per_chunk, start):
    """Input order is kept unless explicit decimal sequence labels are selected."""
    suffix_labels = suffix.rstrip('.').lower().split('.')
    chunks = []
    sequenced = {}
    duplicates = 0
    for line_number, line in enumerate(lines, 1):
        # Accept a bare qname or TSV where qname is the final field.
        name = line.rstrip('\r\n').split('\t')[-1].strip().rstrip('.')
        if not name or name.startswith('#'):
            continue
        labels = name.split('.')
        if len(labels) <= len(suffix_labels) or [part.lower() for part in labels[-len(suffix_labels):]] != suffix_labels:
            continue
        labels = labels[:-len(suffix_labels)]
        if sequence:
            if len(labels) < 2 or not re.fullmatch(r'[0-9]+', labels[0]):
                raise ValueError(f'line {line_number}: first payload label is not a decimal sequence number')
            number = int(labels.pop(0), 10)
            chunk = ''.join(labels)
            if number in sequenced:
                if sequenced[number] != chunk:
                    raise ValueError(f'conflicting payload for sequence {number}')
                duplicates += 1
            sequenced[number] = chunk
        else:
            chunks.append(''.join(labels))
    if sequence:
        numbers = sorted(sequenced)
        if numbers:
            expected = start
            for number in numbers:
                if number != expected:
                    raise ValueError(f'missing or unexpected sequence number: expected {expected}, got {number}')
                expected += 1
        chunks = [sequenced[number] for number in numbers]
    if not chunks:
        raise ValueError('no matching payload qnames found')

    def decode(value):
        raw = value.encode('ascii')
        if encoding == 'hex':
            if len(value) % 2 or not re.fullmatch(r'[0-9a-fA-F]*', value):
                raise ValueError('hex payload must contain an even number of hex digits')
            return bytes.fromhex(value)
        if encoding == 'base32':
            return base64.b32decode(raw + b'=' * (-len(raw) % 8), casefold=True)
        if encoding in {'base64', 'base64url'}:
            padded = raw + b'=' * (-len(raw) % 4)
            return base64.b64decode(padded, altchars=b'-_' if encoding == 'base64url' else None, validate=True)
        return raw

    data = b''.join(decode(chunk) for chunk in chunks) if per_chunk else decode(''.join(chunks))
    return data, len(chunks), duplicates


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path, help='bare query names or TSV; final field is qname')
    parser.add_argument('--suffix', required=True, help='fixed DNS suffix to strip, e.g. exfil.example')
    parser.add_argument('--encoding', choices=['hex','base32','base64','base64url','ascii'], required=True)
    parser.add_argument('--sequence', action='store_true', help='first payload label is decimal; order and deduplicate by it')
    parser.add_argument('--start', type=int, default=0, help='first expected sequence number (default 0)')
    parser.add_argument('--per-chunk', action='store_true', help='decode each qname separately, then join bytes')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if not args.suffix.rstrip('.') or args.start < 0:
        parser.error('suffix must be nonempty and start must be nonnegative')
    try:
        lines = args.input.read_text(encoding='utf-8').splitlines()
        data, count, duplicates = reconstruct(lines, args.suffix, args.encoding, args.sequence, args.per_chunk, args.start)
        args.out.write_bytes(data)
    except (OSError, ValueError, UnicodeError, binascii.Error) as exc:
        parser.error(str(exc))
    print(f'wrote {len(data)} bytes from {count} chunks; suppressed {duplicates} identical sequence retries', file=sys.stderr)


if __name__ == '__main__':
    main()
