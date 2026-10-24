#!/usr/bin/env python3
"""Decrypt cryptpad's self-describing RC4 file; optionally replay its x86 code."""
import argparse
from pathlib import Path
import struct


def rc4(key, data):
    if not key:
        raise ValueError('RC4 key is empty')
    state = list(range(256))
    j = 0
    for i in range(256):
        j = (j + state[i] + key[i % len(key)]) & 255
        state[i], state[j] = state[j], state[i]
    i = j = 0
    output = bytearray()
    for byte in data:
        i = (i + 1) & 255
        j = (j + state[i]) & 255
        state[i], state[j] = state[j], state[i]
        output.append(byte ^ state[(state[i] + state[j]) & 255])
    return bytes(output)


def parse(data):
    if len(data) < 6:
        raise ValueError('File too short for trailer')
    key_size = data[-1]
    trailer_start = len(data) - key_size - 5
    if key_size != 8 or trailer_start < 0:
        raise ValueError('Expected the binary\'s eight-byte key trailer')
    length = struct.unpack_from('<I', data, trailer_start)[0]
    if not 0 < length <= trailer_start:
        raise ValueError('Invalid plaintext length')
    key = data[trailer_start + 4:-1]
    return data[:length], key, length, trailer_start


def native_decrypt(executable, encrypted):
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
    from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EIP

    image = Path(executable).read_bytes()
    nt = struct.unpack_from('<I', image, 0x3c)[0]
    count = struct.unpack_from('<H', image, nt + 6)[0]
    optional_size = struct.unpack_from('<H', image, nt + 20)[0]
    optional = nt + 24
    image_base = struct.unpack_from('<I', image, optional + 28)[0]
    if image_base != 0x400000:
        raise ValueError('Wrong image base for recorded cryptpad binary')

    uc = Uc(UC_ARCH_X86, UC_MODE_32)
    uc.mem_map(0x400000, 0x6000)
    uc.mem_write(0x400000, image[:0x400])
    for index in range(count):
        section = optional + optional_size + index * 40
        _, rva, raw_size, raw_offset = struct.unpack_from('<IIII', image, section + 8)
        uc.mem_write(image_base + rva, image[raw_offset:raw_offset + raw_size])
    uc.mem_map(0x100000, 0x10000)
    uc.mem_map(0x200000, 0x10000)
    uc.mem_map(0x300000, 0x1000)
    uc.mem_write(0x200000, encrypted)
    uc.mem_write(0x40357d, struct.pack('<I', len(encrypted)))
    uc.mem_write(0x108000, struct.pack('<IIII', 0x300000, 0x200000, len(encrypted), 0))
    uc.reg_write(UC_X86_REG_ESP, 0x108000)
    uc.emu_start(0x4014eb, 0x300000, count=1000000)
    if uc.reg_read(UC_X86_REG_EIP) != 0x300000:
        raise RuntimeError('Native decryption did not return before instruction limit')
    _, _, length, _ = parse(encrypted)
    return bytes(uc.mem_read(0x200000, length))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('encrypted', nargs='?', type=Path, default=Path(__file__).with_name('flag.enc'))
    parser.add_argument('--verify-native', type=Path, metavar='CRYPTPAD_EXE')
    parser.add_argument('--details', action='store_true')
    args = parser.parse_args()
    encrypted = args.encrypted.read_bytes()
    ciphertext, key, length, trailer = parse(encrypted)
    plaintext = rc4(key, ciphertext)
    assert rc4(key, plaintext) == ciphertext
    if args.verify_native:
        assert native_decrypt(args.verify_native, encrypted) == plaintext
    if not plaintext.startswith(b'CMO{') or not plaintext.endswith(b'}\0'):
        raise ValueError(f'Unexpected decrypted bytes: {plaintext!r}')
    if args.details:
        print(f'File bytes: {len(encrypted)}')
        print(f'Trailer offset: {trailer:#x}')
        print(f'Plaintext bytes including NUL: {length}')
        print(f'RC4 key: {key.hex()}')
    print(plaintext[:-1].decode('ascii'))


if __name__ == '__main__':
    main()
