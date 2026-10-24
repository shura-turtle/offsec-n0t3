#!/usr/bin/env python3
"""Recover RecordPlayer's flag from its WAV and reproduce both playback fixes."""
import argparse
import hashlib
import io
from pathlib import Path
import struct
import wave

BASE = 0x140000000
EXPECTED_SHA256 = 'c0846e7b630e3d307ed795378b5346b90cc524a508d35a118979f85938d0f5a3'
PATCH_RVAS = (0x392d, 0x3938)


def sections(image):
    nt = struct.unpack_from('<I', image, 0x3c)[0]
    count = struct.unpack_from('<H', image, nt + 6)[0]
    optional_size = struct.unpack_from('<H', image, nt + 20)[0]
    for i in range(count):
        p = nt + 24 + optional_size + i * 40
        virtual_size, rva, raw_size, raw_offset = struct.unpack_from('<IIII', image, p + 8)
        yield rva, virtual_size, raw_size, raw_offset


def offset(image, rva):
    for start, virtual_size, raw_size, raw_offset in sections(image):
        if start <= rva < start + raw_size:
            return raw_offset + rva - start
    raise ValueError(f'RVA {rva:#x} is not backed by the file')


def extract(image):
    cipher = bytearray()
    for rva in (0x17b6, 0x17bd, 0x17c4, 0x17cb, 0x17d2):
        p = offset(image, rva)
        assert image[p:p+2] == b'\xc7\x45'
        cipher.extend(image[p+3:p+7])
    p = offset(image, 0x17d9)
    assert image[p:p+3] == b'\x66\xc7\x45'
    cipher.extend(image[p+4:p+6])
    p = offset(image, 0x17df)
    assert image[p:p+2] == b'\xc6\x45'
    cipher.append(image[p+3])
    p = offset(image, 0x183f)
    assert image[p:p+6] == b'\xc7\x87\x50\x01\x00\x00'
    target = struct.unpack_from('<I', image, p+6)[0]
    candidates = []
    start = 0
    while True:
        p = image.find(b'RIFF', start)
        if p < 0:
            break
        start = p + 4
        if image[p+8:p+12] == b'WAVE':
            size = struct.unpack_from('<I', image, p+4)[0] + 8
            candidates.append((p, image[p:p+size]))
    if len(candidates) != 1:
        raise ValueError(f'Expected one WAV resource, found {len(candidates)}')
    raw_offset, wav_bytes = candidates[0]
    with wave.open(io.BytesIO(wav_bytes)) as wav:
        if (wav.getnchannels(), wav.getsampwidth()) != (1, 1):
            raise ValueError('Expected mono unsigned 8-bit PCM')
        rate = wav.getframerate()
        samples = wav.readframes(wav.getnframes())
    return bytes(cipher), target, raw_offset, wav_bytes, rate, samples


def fnv1a(data):
    value = 0x811c9dc5
    for byte in data:
        value = ((value ^ byte) * 0x1000193) & 0xffffffff
    return value


def recover(cipher, target, samples):
    hits = []
    for start in range(len(samples) - len(cipher) + 1):
        candidate = bytearray()
        value = 0x811c9dc5
        for j, byte in enumerate(cipher):
            decoded = byte ^ samples[start+j]
            if not 32 <= decoded < 127:
                break
            candidate.append(decoded)
            value = ((value ^ decoded) * 0x1000193) & 0xffffffff
        else:
            if value == target:
                hits.append((start, bytes(candidate)))
    if len(hits) != 1:
        raise ValueError(f'Expected one printable hash match; got {len(hits)}')
    return hits[0]


def make_patched(image):
    patched = bytearray(image)
    for rva in PATCH_RVAS:
        p = offset(image, rva)
        assert image[p:p+2] == b'\xb2\x01'
        patched[p+1] = 0
    return bytes(patched)


def native_verify(image, plaintext, target):
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_64
    from unicorn.x86_const import UC_X86_REG_RCX, UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_RAX, UC_X86_REG_RBX, UC_X86_REG_RSP

    def machine(binary):
        uc = Uc(UC_ARCH_X86, UC_MODE_64)
        uc.mem_map(BASE, 0x130000)
        for rva, _, size, p in sections(binary):
            uc.mem_write(BASE+rva, binary[p:p+size])
        uc.mem_map(0x100000, 0x10000)
        uc.mem_map(0x200000, 0x10000)
        return uc

    uc = machine(image)
    uc.mem_write(0x200000, plaintext)
    uc.reg_write(UC_X86_REG_RDX, 0x200000)
    uc.reg_write(UC_X86_REG_R8, len(plaintext))
    uc.mem_write(0x108008, struct.pack('<Q', 0x100000))
    uc.reg_write(UC_X86_REG_RSP, 0x108008)
    uc.emu_start(BASE+0x1030, 0x100000, count=10000)
    assert uc.reg_read(UC_X86_REG_RAX) == target

    for binary, expected_step, expected_pitch in [(image,-1,1),(make_patched(image),1,0)]:
        uc = machine(binary)
        uc.mem_write(0x200050, struct.pack('<Q',0x201000))
        uc.reg_write(UC_X86_REG_RBX,0x200000)
        uc.reg_write(UC_X86_REG_RSP,0x108008)
        # Execute the two call sites and original setters; stop before playback starts.
        uc.emu_start(BASE+0x392d,BASE+0x3943,count=1000)
        step = struct.unpack('<i',uc.mem_read(0x201018,4))[0]
        pitch = bytes(uc.mem_read(0x20101d,1))[0]
        assert (step,pitch) == (expected_step,expected_pitch)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable',type=Path)
    parser.add_argument('--patch-output',type=Path)
    parser.add_argument('--extract-audio',type=Path)
    parser.add_argument('--verify-native',action='store_true')
    parser.add_argument('--details',action='store_true')
    args=parser.parse_args()
    image=args.executable.read_bytes()
    if hashlib.sha256(image).hexdigest()!=EXPECTED_SHA256:
        raise ValueError('Executable differs from the recorded public handout')
    cipher,target,raw,wav,rate,samples=extract(image)
    start,plaintext=recover(cipher,target,samples)
    assert bytes(a^b for a,b in zip(plaintext,samples[start:start+len(cipher)]))==cipher
    if args.verify_native:
        native_verify(image,plaintext,target)
    if args.patch_output:
        if args.patch_output.resolve()==args.executable.resolve():
            raise ValueError('Choose a different patch output path')
        args.patch_output.write_bytes(make_patched(image))
    if args.extract_audio:
        args.extract_audio.write_bytes(wav)
    if args.details:
        print(f'WAV raw offset: {raw:#x}')
        print(f'Audio: {rate} Hz, mono 8-bit, {len(samples)} samples')
        print(f'Encrypted bytes: {cipher.hex()}')
        print(f'FNV-1a target: {target:#x}')
        print(f'Matching sample: {start} ({start/rate:.1f} seconds)')
        print('Patch VA/file offsets: 0x14000392d/0x2d2d and 0x140003938/0x2d38')
    print(plaintext.decode('ascii'))


if __name__=='__main__':
    main()
