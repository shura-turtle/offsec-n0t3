#!/usr/bin/env python3
"""Replay the supplied Connected payload and verify its checksum model."""
import argparse
from pathlib import Path
import subprocess
import zlib

BODY = b':"*$$*":'
DESTINATION = b'100.25.26.10'

def combined(data):
    a = b = 0
    for value in data:
        a = (a + value) % 255
        b = (b + a) % 255
    fletcher = (b << 8) | a
    return (zlib.adler32(data) ^ fletcher) ^ sum(value << i for i, value in enumerate(data))

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('binary', type=Path)
    args = p.parse_args()
    assert len(BODY) == 8 and BODY == BODY[::-1]
    assert all(32 < value < 127 and value % 2 == 0 for value in BODY)
    assert combined(BODY) == 100806214
    alphabet = 'abcdefghijklmnopqrstuvwxyz0123456789_'
    expected = 'CMO{secret_code_' + ''.join(alphabet[(value+i) % len(alphabet)] for i,value in enumerate(BODY)) + '}'
    r = subprocess.run([str(args.binary.resolve())], input=b'msg_'+BODY+b'\n'+DESTINATION+b'\n', capture_output=True, timeout=15)
    output = r.stdout + r.stderr
    assert r.returncode == 0 and expected.encode() in output, repr(output)
    print(expected)

if __name__ == '__main__': main()
