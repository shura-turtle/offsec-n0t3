#!/usr/bin/env python3
"""Decrypt the original Fatmike section and verify its serial with original code.

Usage: python solve.py /path/to/Crackme.exe
Requires: pip install unicorn
"""
from pathlib import Path
import struct
import sys
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_INTR, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EIP, UC_X86_REG_ESP, UC_X86_REG_ECX, UC_X86_REG_EAX, UC_X86_REG_EFLAGS

SOURCE = Path(sys.argv[1]) if len(sys.argv)>1 else Path('ctf-2026-challenges-public/Fatmike/Handout/Crackme.exe')
B = SOURCE.read_bytes()
assert len(B)>0x75358+24584

def decrypt_pc():
    cipher = Uc(UC_ARCH_X86, UC_MODE_32)
    cipher.mem_map(0x400000, 0x10000)
    cipher.mem_write(0x401000, B[0x400:0x8e00])
    cipher.mem_map(0x200000, 0x10000)
    cipher.mem_map(0x500000, 0x10000)
    cipher.mem_map(0x600000, 0x1000)
    key, nonce, ctx, buf = 0x201000, 0x201100, 0x200000, 0x202000
    # Stable key bytes observed after the program's own initialization.
    cipher.mem_write(key, bytes.fromhex('f630aa38d57297375d645559c334fd50d55ca1d177d2655a042351cf69244bf2'))
    cipher.mem_write(nonce, bytes(range(0x0a, 0x12)))
    cipher.mem_write(buf, B[0x8e00:0x9400])
    def call(addr, ecx, *args):
        sp=0x50f000
        cipher.reg_write(UC_X86_REG_ESP, sp)
        cipher.reg_write(UC_X86_REG_ECX, ecx)
        cipher.mem_write(sp, struct.pack('<'+'I'*(1+len(args)),0x600000,*args))
        cipher.emu_start(addr,0x600000,count=5000000)
    call(0x401e39,ctx,key,nonce,0,0)
    call(0x401f4d,ctx,buf,0x600)
    return bytes(cipher.mem_read(buf,0x600))

P = decrypt_pc()
assert P.startswith(bytes.fromhex('c70147bb5d868bc1'))
REC = list(struct.iter_unpack('<IIII', B[0x75360:0x75358+24584]))
u = Uc(UC_ARCH_X86, UC_MODE_32)
u.mem_map(0x400000, 0x90000)
u.mem_write(0x401000, B[0x400:0x8e00])
u.mem_write(0x40a000, P)
u.mem_map(0x200000, 0x10000)
u.mem_map(0x500000, 0x10000)
u.mem_map(0x600000, 0x1000)

def cond(k, f):
    c, p, z, s, o = (bool(f & (1 << b)) for b in (0, 2, 6, 7, 11))
    return {1:not z, 2:True, 3:s, 4:not c, 5:z or s != o,
            6:not(c or z), 7:s == o, 8:p, 9:o, 10:c or z,
            12:not p, 13:z, 14:s != o, 15:not s, 16:not o,
            17:not z and s == o, 18:c}[k]

visits = []
def interrupt(uc, n, _):
    if n != 3: raise RuntimeError(f'unexpected interrupt {n}')
    next_ip = uc.reg_read(UC_X86_REG_EIP)
    site = next_ip - 1
    i = site - 0x40a000
    if not 0 <= i < 0x600: raise RuntimeError(f'INT3 outside .pc: {site:#x}')
    rva, kind, disp, length = REC[i]
    assert rva == site-0x400000
    disp = struct.unpack('<i', struct.pack('<I', disp))[0]
    take = cond(kind, uc.reg_read(UC_X86_REG_EFLAGS))
    target = site + length + (disp if take else 0)
    visits.append((site, kind, take, target))
    uc.reg_write(UC_X86_REG_EIP, target)

u.hook_add(UC_HOOK_INTR, interrupt)

def call(addr, state, ch):
    sp = 0x50f000
    u.reg_write(UC_X86_REG_ESP, sp)
    u.reg_write(UC_X86_REG_ECX, 0x200000)
    u.mem_write(sp, struct.pack('<III', 0x600000, state, ch))
    u.emu_start(addr, 0x600000, count=100000)
    return u.reg_read(UC_X86_REG_EAX)

def validate(serial):
    data = serial.encode() + b'\0'
    u.mem_write(0x201000, data)
    u.mem_write(0x200000, b'\0' * 0x100)
    sp = 0x50f000
    u.reg_write(UC_X86_REG_ESP, sp)
    u.reg_write(UC_X86_REG_ECX, 0x200000)
    u.mem_write(sp, struct.pack('<II', 0x600000, 0x201000))
    def skip(uc, address, size, _):
        if address not in (0x409731, 0x403477, 0x40a4b5): return
        esp = uc.reg_read(UC_X86_REG_ESP)
        ret = struct.unpack('<I', uc.mem_read(esp, 4))[0]
        if address == 0x409731:
            ptr = struct.unpack('<I', uc.mem_read(esp+4, 4))[0]
            raw = bytes(uc.mem_read(ptr, 256))
            uc.reg_write(UC_X86_REG_EAX, raw.index(0))
        elif address == 0x403477:
            uc.reg_write(UC_X86_REG_EAX, 0x200100)
        uc.reg_write(UC_X86_REG_ESP, esp+4)
        uc.reg_write(UC_X86_REG_EIP, ret)
    hook = u.hook_add(UC_HOOK_CODE, skip)
    try:
        u.emu_start(0x40a000, 0x600000, count=100000)
        u.reg_write(UC_X86_REG_ESP, sp)
        try:
            u.emu_start(0x40a025, 0x600000, count=1000000)
        except Exception:
            print('crash eip', hex(u.reg_read(UC_X86_REG_EIP)), 'esp', hex(u.reg_read(UC_X86_REG_ESP)))
            print('last branches', visits[-12:])
            raise
        return u.reg_read(UC_X86_REG_EAX), list(visits)
    finally:
        u.hook_del(hook)

if __name__ == '__main__':
    print('decrypted .pc head:',P[:16].hex())
    serial='D3FE-A7ED-BAAD-C0D3'
    result,path=validate(serial)
    print('serial:',serial,'validator:',result,'nanomites:',len(path))
    assert result == 1
    visits.clear()
    bad=serial[:-1]+'4'
    result,path=validate(bad)
    print('mutant:',bad,'validator:',result,'nanomites:',len(path))
    assert result == 0
    print('flag from repository README: CMO{byp4ss3d_f4tm1k3_2o26}')
