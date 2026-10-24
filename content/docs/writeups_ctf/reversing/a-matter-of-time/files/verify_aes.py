"""Run the challenge's unmodified AES-CBC routine in Unicorn."""
import struct
from unicorn import Uc, UC_ARCH_X86, UC_MODE_64, UC_HOOK_CODE
from unicorn.x86_const import *
import base64
import json
from pathlib import Path

SEGMENTS = {int(a, 16): base64.b64decode(b)
            for a, b in json.loads(Path("ida_segments.json").read_text()).items()}

def verify(ciphertext, key, iv):
    u = Uc(UC_ARCH_X86, UC_MODE_64)
    u.mem_map(0x140000000, 0x30000)
    u.mem_map(0x100000, 0x40000)
    for address, data in SEGMENTS.items():
        u.mem_write(address, data)
    def q(address):
        return struct.unpack('<Q', u.mem_read(address, 8))[0]
    def putq(address, value):
        u.mem_write(address, struct.pack('<Q', value))
    def ret(value=0):
        sp = u.reg_read(UC_X86_REG_RSP)
        u.reg_write(UC_X86_REG_RAX, value)
        u.reg_write(UC_X86_REG_RIP, q(sp))
        u.reg_write(UC_X86_REG_RSP, sp+8)
    u.mem_write(0x120000, ciphertext)
    u.mem_write(0x121000, key)
    u.mem_write(0x122000, iv)
    for vector, data, size in [(0x123000,0x120000,len(ciphertext)),(0x123020,0x121000,16),(0x123040,0x122000,16)]:
        u.mem_write(vector,struct.pack('<QQQ', data,data+size,data+size))
    def hook(u, a, size, data):
        if a == 0x140007e08:
            dest=u.reg_read(UC_X86_REG_RCX)
            size=u.reg_read(UC_X86_REG_RDX)
            u.mem_write(dest,struct.pack('<QQQ',0x124000,0x124000,0x124000+size))
            ret(dest)
        elif a == 0x140009fb1:
            dest=u.reg_read(UC_X86_REG_RCX)
            u.mem_write(dest,bytes([u.reg_read(UC_X86_REG_RDX)&255])*u.reg_read(UC_X86_REG_R8))
            ret(dest)
        elif a in (0x140008ef4,0x140008c50):
            ret()
    u.hook_add(UC_HOOK_CODE, hook)
    u.reg_write(UC_X86_REG_RSP,0x110008)
    putq(0x110008,0x100000)
    u.reg_write(UC_X86_REG_RCX,0x123000)
    u.reg_write(UC_X86_REG_RDX,0x123020)
    u.reg_write(UC_X86_REG_R8,0x123040)
    u.emu_start(0x14000326c,0x100000,count=2000000)
    assert u.reg_read(UC_X86_REG_RIP)==0x100000, 'instruction budget exhausted'
    return bytes(u.mem_read(0x120000,len(ciphertext)))

if __name__=='__main__':
    from pathlib import Path
    ct=bytes.fromhex(Path('ciphertext.hex').read_text())
    print(verify(ct,b'nicetryboogeyman',b'0000000537068053'))
