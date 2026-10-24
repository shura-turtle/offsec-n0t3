#!/usr/bin/env python3
"""Derive HTTPD's ICMP AES key and decrypt its embedded ciphertext offline.

Usage: python solve.py /path/to/httpd/handout/httpd
Requires PyCryptodome. No raw sockets or FreeBSD execution are used.
"""
import argparse
from pathlib import Path
import struct

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad


def checksum(data):
    if len(data) % 2:
        data += b'\0'
    value = sum(struct.unpack('>' + 'H' * (len(data) // 2), data))
    while value >> 16:
        value = (value & 0xffff) + (value >> 16)
    return (~value) & 0xffff


def elf_read_va(binary, address, size):
    assert binary[:6] == b'\x7fELF\x02\x01', 'Expected ELF64 little-endian input'
    phoff = struct.unpack_from('<Q', binary, 32)[0]
    phentsize, phnum = struct.unpack_from('<HH', binary, 54)
    for index in range(phnum):
        kind, _, offset, va, _, file_size, _, _ = struct.unpack_from('<IIQQQQQQ', binary, phoff + index * phentsize)
        if kind == 1 and va <= address and address + size <= va + file_size:
            start = offset + address - va
            return binary[start:start + size]
    raise ValueError(f'Address {address:#x} not found in file-backed PT_LOAD segment')


def embedded_ciphertext(binary):
    # Four MOVABS RCX, imm64 instructions build the 32-byte ciphertext.
    result = bytearray()
    for va in (0x7484d2, 0x7484df, 0x7484ed, 0x7484fb):
        instruction = elf_read_va(binary, va, 10)
        assert instruction[:2] == b'\x48\xb9', f'Unexpected instruction at {va:#x}'
        result += instruction[2:]
    return bytes(result)


def key_from_frame(frame):
    assert int.from_bytes(frame[0x26:0x28], 'little') == 0x1337
    assert int.from_bytes(frame[0x10:0x12], 'big') == 0x20
    assert int.from_bytes(frame[0x2a:0x2e], 'little') == 0xe55fdec6
    assert frame[0x22] == 8
    protocol_fields = frame[0x14:0x18]
    icmp_checksum = frame[0x24:0x26]
    identifier = frame[0x26:0x28]
    timestamp = frame[0x2a:0x2e]
    ts = int.from_bytes(timestamp, 'little')
    cs = int.from_bytes(icmp_checksum, 'little')
    a = struct.pack('>H', (ts >> 16) ^ cs)
    b = struct.pack('>H', (ts & 0xffff) ^ cs)
    return a + protocol_fields + icmp_checksum + timestamp + identifier + b


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary', type=Path)
    args = parser.parse_args()
    payload = bytes.fromhex('c6de5fe5')
    header = struct.pack('>BBHHH', 8, 0, 0, 0x3713, 1)
    cs = checksum(header + payload)
    icmp = struct.pack('>BBHHH', 8, 0, cs, 0x3713, 1) + payload
    assert checksum(icmp) == 0
    ip = bytearray(20)
    ip[0] = 0x45
    ip[2:4] = struct.pack('>H', 20 + len(icmp))
    ip[6:8] = b'\x40\0'  # Don't-fragment, fragment offset zero.
    ip[8:10] = b'\x40\x01'  # TTL=64, protocol=ICMP.
    ip[12:16] = b'\x01\x02\x03\x04'
    ip[16:20] = b'\x05\x06\x07\x08'
    ip[10:12] = struct.pack('>H', checksum(bytes(ip)))
    ethernet = b'\0' * 12 + b'\x08\0'
    frame = ethernet + ip + icmp
    key = key_from_frame(frame)
    ciphertext = embedded_ciphertext(args.binary.read_bytes())
    padded = AES.new(key, AES.MODE_CBC, key).decrypt(ciphertext)
    plaintext = unpad(padded, 16)
    assert AES.new(key, AES.MODE_CBC, key).encrypt(padded) == ciphertext
    print(f'ICMP checksum: {cs:04x}')
    print('ICMP bytes:', icmp.hex())
    print('Key and IV:', key.hex())
    print('Ciphertext:', ciphertext.hex())
    print(plaintext.decode('ascii'))


if __name__ == '__main__':
    main()
