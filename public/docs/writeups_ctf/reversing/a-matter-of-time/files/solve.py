#!/usr/bin/env python3
"""Recover A Matter of Time's plaintext using PyCryptodome.

The username is evidenced by the PDB path and valid CBC suffix/padding.
The IV is reconstructed from the readable first block, not a captured run.
Use --verify-native to replay the unmodified binary AES code in Unicorn.
"""
import argparse
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

CIPHERTEXT = bytes.fromhex(
    '4c4635258cf6eca5d80b8e050a9e5b04'
    'f1a9c979bc55f3f4773971ed2f81a969'
    '67bb3569fa002f549cc970a18779b3a7'
)
KEY = b'nicetryboogeyman'
IV_VALUE = 537068053
IV = str(IV_VALUE).zfill(16).encode('ascii')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-native', action='store_true')
    args = parser.parse_args()
    padded = AES.new(KEY, AES.MODE_CBC, IV).decrypt(CIPHERTEXT)
    if args.verify_native:
        from verify_aes import verify
        assert verify(CIPHERTEXT, KEY, IV) == padded
    plaintext = unpad(padded, AES.block_size)
    assert plaintext.startswith(b'CMO{') and plaintext.endswith(b'}')
    assert AES.new(KEY, AES.MODE_CBC, IV).encrypt(padded) == CIPHERTEXT
    print(plaintext.decode('ascii'))

if __name__ == '__main__':
    main()
