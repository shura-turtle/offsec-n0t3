#!/usr/bin/env python3
"""Recover two stack strings from the supplied IDA segment snapshot."""
import base64
import json
from pathlib import Path

from unicorn import Uc, UC_ARCH_X86, UC_MODE_64, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_RDX, UC_X86_REG_R8, UC_X86_REG_R13, UC_X86_REG_RSP


def extract(root, stop, read_value):
    segments = json.loads(Path('ida_segments.json').read_text())
    uc = Uc(UC_ARCH_X86, UC_MODE_64)
    uc.mem_map(0x140000000, 0x30000)
    uc.mem_map(0x100000, 0x20000)
    for address, data in segments.items():
        uc.mem_write(int(address, 16), base64.b64decode(data))
    uc.reg_write(UC_X86_REG_RSP, 0x110008)
    result = []

    def hook(uc, address, size, user_data):
        if address == stop:
            result.append(read_value(uc))
            uc.emu_stop()

    uc.hook_add(UC_HOOK_CODE, hook)
    uc.emu_start(root, 0, count=100000)
    if not result:
        raise RuntimeError(f'Did not reach extraction point {stop:#x}')
    return result[0]


def main():
    ciphertext_hex = extract(
        0x140001000,
        0x140007bc4,
        lambda uc: bytes(uc.mem_read(
            uc.reg_read(UC_X86_REG_RDX), uc.reg_read(UC_X86_REG_R8)
        )),
    ).decode('ascii')
    assert len(ciphertext_hex) == 96
    ciphertext = bytes.fromhex(ciphertext_hex)
    Path('ciphertext.hex').write_text(ciphertext_hex + '\n')
    path = extract(
        0x140003750,
        0x140009a80,
        lambda uc: bytes(uc.mem_read(uc.reg_read(UC_X86_REG_R13), 128)).split(b'\0', 1)[0],
    ).decode('ascii')
    print('Ciphertext hex:', ciphertext_hex)
    print('Ciphertext bytes:', len(ciphertext))
    print('Time source:', path)


if __name__ == '__main__':
    main()
