import base64
import json
from pathlib import Path
import capstone

SEGMENTS = {int(a, 16): base64.b64decode(b) for a, b in json.loads(Path('ida_segments.json').read_text()).items()}
cs = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
cs.detail = True

def read(a, n=16):
    for s, data in SEGMENTS.items():
        if s <= a < s + len(data):
            return data[a-s:a-s+n]
    return b''

def decode(a):
    return next(cs.disasm(read(a), a, count=1), None)

def walk(root):
    pending = [root]
    seen = {}
    while pending:
        a = pending.pop()
        while a not in seen:
            i = decode(a)
            if not i:
                break
            seen[a] = i
            n = a + i.size
            if i.mnemonic.startswith('ret') or i.mnemonic in ('int3','ud2'):
                if i.mnemonic.startswith('ret'):
                    for p in seen.values():
                        if 0 < a-p.address < 14 and p.mnemonic == 'lea' and p.operands[1].type == capstone.x86.X86_OP_MEM and p.operands[1].mem.base == capstone.x86.X86_REG_RIP:
                            pending.append(p.address+p.size+p.operands[1].mem.disp)
                break
            if i.group(capstone.CS_GRP_JUMP):
                if i.operands[0].type != capstone.x86.X86_OP_IMM:
                    prev = [v for k,v in seen.items() if k < a and a-k<16]
                    for p in prev:
                        if p.mnemonic == 'lea' and p.operands[0].reg == i.operands[0].reg and p.operands[1].type == capstone.x86.X86_OP_MEM and p.operands[1].mem.base == capstone.x86.X86_REG_RIP:
                            pending.append(p.address+p.size+p.operands[1].mem.disp)
                    break
                target = i.operands[0].imm
                pending.append(target)
                if i.mnemonic == 'jmp':
                    break
                j = decode(n)
                # Complementary jccs consume both possible outcomes; junk after
                # the pair cannot execute. Preserve both target blocks.
                if j and j.group(capstone.CS_GRP_JUMP) and j.mnemonic != 'jmp':
                    first = i.bytes[1] if i.bytes[0] == 0x0f else i.bytes[0]
                    second = j.bytes[1] if j.bytes[0] == 0x0f else j.bytes[0]
                    if first ^ second == 1:
                        seen[n] = j
                        pending.append(j.operands[0].imm)
                        break
            a = n
    return seen

if __name__ == '__main__':
    import sys
    root = int(sys.argv[1], 0) if len(sys.argv)>1 else 0x140004290
    ins = walk(root)
    Path(f'cfg_{root:x}.json').write_text(json.dumps({hex(a):bytes(i.bytes).hex() for a,i in ins.items()}))
    for a, i in sorted(ins.items()):
        print(f'{a:x}: {i.mnemonic:8} {i.op_str}')
