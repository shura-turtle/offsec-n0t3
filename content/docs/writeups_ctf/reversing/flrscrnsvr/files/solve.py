#!/usr/bin/env python3
"""Invert and forward-check the official screensaver encoding model."""
import argparse
from pathlib import Path
import struct

ENCODED = [0x3c,0x51,0x6a,9,2,7,0x25,3,0x30,8,4,0x29,0x68,0x24,1,0x24,0x18,0x6b,0x77,0xf,0x70,0x36,2,0xe,0xb]
ALPHABET = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789}_{=-'
SUBSTITUTION = '-={_}9876543210ZYXWVUTSRQPONMLKJIHGFEDCBAzyxwvutsrqponmlkjihgfedcba'
KEY = 'FLARERALF'

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--binary',type=Path);args=p.parse_args()
    reverse=dict(zip(SUBSTITUTION,ALPHABET));forward=dict(zip(ALPHABET,SUBSTITUTION))
    flag=''.join(reverse[chr(value ^ (ord(KEY[i%len(KEY)])+i))] for i,value in enumerate(ENCODED[::-1]))
    encoded=[ord(forward[c]) ^ (ord(KEY[i%len(KEY)])+i) for i,c in enumerate(flag)][::-1]
    assert encoded == ENCODED and len(flag)==25
    if args.binary:
        data=args.binary.read_bytes()
        packed=struct.pack('<25H',*ENCODED)
        print('Encoded UTF-16 table file offset:',hex(data.index(packed)))
    print(flag)

if __name__=='__main__':main()
