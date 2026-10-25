#!/usr/bin/env python3
"""Extract nested DLL resources, recover shellcode-checked RC4 keys, and decode the final flag."""
from pathlib import Path
import argparse,struct,json,re,hashlib
from Crypto.Cipher import ARC4
from unicorn import Uc,UC_ARCH_X86,UC_MODE_64,UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_RCX,UC_X86_REG_RSP,UC_X86_REG_RAX,UC_X86_REG_RIP,UC_X86_REG_RDX,UC_X86_REG_R8
from capstone import Cs,CS_ARCH_X86,CS_MODE_64

class PE:
 def __init__(self,data):
  self.data=data;p=struct.unpack_from('<I',data,60)[0];n=struct.unpack_from('<H',data,p+6)[0];optsz=struct.unpack_from('<H',data,p+20)[0];self.sections=[]
  for k in range(n):
   q=p+24+optsz+40*k;v,va,rs,off=struct.unpack_from('<4I',data,q+8);self.sections.append((va,v,off,rs))
  self.rsrc=struct.unpack_from('<I',data,p+24+112+2*8)[0]
 def off(self,a):
  for va,v,o,rs in self.sections:
   if va<=a<va+max(v,rs):return o+a-va
  raise ValueError(f'RVA {a:x} unmapped')
 def resources(self):
  b=self.data;base=self.off(self.rsrc);out={}
  def walk(a,path):
   nd,ni=struct.unpack_from('<HH',b,base+a+12)
   for k in range(nd+ni):
    name,dst=struct.unpack_from('<II',b,base+a+16+8*k)
    if name&0x80000000:
     x=base+(name&0x7fffffff);cnt=struct.unpack_from('<H',b,x)[0];name=b[x+2:x+2+cnt*2].decode('utf-16le')
    if dst&0x80000000:walk(dst&0x7fffffff,path+[name])
    else:
     rva,sz,_,_=struct.unpack_from('<4I',b,base+dst);out[tuple(path+[name])]=b[self.off(rva):self.off(rva)+sz]
  walk(0,[]);return out

def checker(code,pw,force=False):
 cs=Cs(CS_ARCH_X86,CS_MODE_64);u=Uc(UC_ARCH_X86,UC_MODE_64)
 code_size=(len(code)+4095)&~4095
 u.mem_map(0x100000,code_size);u.mem_write(0x100000,code);u.mem_map(0x800000,0x20000);u.mem_map(0x900000,0x10000)
 u.mem_write(0x900000,pw+b'\0');u.reg_write(UC_X86_REG_RCX,0x900000);u.reg_write(UC_X86_REG_RSP,0x810008);u.mem_write(0x810008,(0x800000).to_bytes(8,'little'))
 bits=[];constants=[];cache={};state={'guard':0,'pending':False}
 def hook(u,a,n,d):
  if a not in cache:
   i=next(cs.disasm(u.mem_read(a,n),a));cache[a]=(i.mnemonic,i.op_str)
  mn,op=cache[a]
  if mn=='pushfq':state['guard']+=1
  elif mn=='popfq':state['guard']-=1
  elif mn=='movabs' and op.startswith('rax, '):
   v=int(op.split(', ')[1],0)
   if v not in constants:constants.append(v)
  elif force and state['guard']==0 and mn=='cmp' and op.startswith('qword ptr [rsp + 8], '):
   wanted=int(op.rsplit(', ',1)[1],0);bits.append(wanted);u.mem_write(u.reg_read(UC_X86_REG_RSP)+8,wanted.to_bytes(8,'little'))
  elif mn=='and' and op=='rax, 1':state['pending']=True
  elif force and state['pending'] and state['guard']==0 and ((mn=='cmp' and op=='rax, 1') or (mn=='test' and op=='rax, rax')):
   wanted=1 if mn=='cmp' else 0;bits.append(wanted);u.reg_write(UC_X86_REG_RAX,wanted);state['pending']=False
 if force:u.hook_add(UC_HOOK_CODE,hook)
 u.emu_start(0x100000,0x800000,count=5000000)
 assert u.reg_read(UC_X86_REG_RIP)==0x800000,'checker instruction budget exhausted'
 return u.reg_read(UC_X86_REG_RAX)&255,bits,constants

def rol32(x):return ((x<<7)|(x>>25))&0xffffffff

def recover_key(code):
 result,bits,constants=checker(code,b'A'*32,True)
 assert result==1 and len(bits)==256,(result,len(bits))
 assert len(constants)==2,constants
 keys=[constants[0]>>32,constants[0]&0xffffffff,constants[1]>>32,constants[1]&0xffffffff]
 targets=[sum(bit<<k for k,bit in enumerate(bits[i:i+64])) for i in range(0,256,64)]
 out=bytearray()
 for v in targets:
  left,right=v>>32,v&0xffffffff
  for i in reversed(range(32)):left,right=right^rol32(left)^(keys[i%4]^i),left
  out.extend(((left<<32)|right).to_bytes(8,'little'))
 out=bytes(out);assert checker(code,out)[0]==1,'recovered key fails untouched checker'
 return out,{'constants':[hex(x) for x in constants],'targets':[hex(x) for x in targets]}

def terminal_flag(data):
 pe=PE(data);u=Uc(UC_ARCH_X86,UC_MODE_64);base=0x180000000
 u.mem_map(base,0x10000)
 for va,v,off,rs in pe.sections:u.mem_write(base+va,data[off:off+rs])
 u.mem_map(0xa00000,0x10000);u.mem_map(0xb00000,0x20000)
 u.mem_write(base+0x2078,(0xa00000).to_bytes(8,'little'))
 u.reg_write(UC_X86_REG_RSP,0xb10008);u.mem_write(0xb10008,(0xb00000).to_bytes(8,'little'))
 captured=[]
 def hook(u,a,n,d):
  if a==0xa00000:
   ptr=u.reg_read(UC_X86_REG_RDX);raw=bytearray()
   for k in range(256):
    pair=bytes(u.mem_read(ptr+2*k,2))
    if pair==b'\0\0':break
    raw.extend(pair)
   captured.append(raw.decode('utf-16le'))
   sp=u.reg_read(UC_X86_REG_RSP);ret=int.from_bytes(u.mem_read(sp,8),'little');u.reg_write(UC_X86_REG_RSP,sp+8);u.reg_write(UC_X86_REG_RIP,ret);u.reg_write(UC_X86_REG_RAX,1)
 u.hook_add(UC_HOOK_CODE,hook);u.emu_start(base+0x1008,0xb00000,count=1000)
 assert u.reg_read(UC_X86_REG_RAX)==1 and len(captured)==1
 assert captured[0].startswith('CMO{') and captured[0].endswith('}')
 return captured[0]

def main():
 ap=argparse.ArgumentParser();ap.add_argument('dll',type=Path);ap.add_argument('--out',type=Path,default=Path('matryoshka-output'));ap.add_argument('--keys',type=Path,help='replay recovered keys while validating every untouched checker');args=ap.parse_args();args.out.mkdir(exist_ok=True,parents=True)
 data=args.dll.read_bytes();records=[];license_data=b'';cached=json.loads(args.keys.read_text()) if args.keys else None
 for depth in range(100):
  print(f'Layer {depth}: {len(data)} bytes SHA256={hashlib.sha256(data).hexdigest()}',flush=True)
  res=PE(data).resources();named={path[1]:v for path,v in res.items() if path[0]==10}
  if not {'CHECK','MATRYOSHKA'}<=named.keys():
   (args.out/'final.dll').write_bytes(data);(args.out/'final-resources.json').write_text(json.dumps({str(k):len(v) for k,v in res.items()}));print('Terminal resources',[(p,len(v)) for p,v in res.items()],flush=True)
   flag=terminal_flag(data);(args.out/'flag.txt').write_text(flag+'\n');(args.out/'license.bin').write_bytes(license_data);print(flag,flush=True)
   break
  if cached is None:key,info=recover_key(named['CHECK'])
  else:
   record=cached[depth];assert record['sha256']==hashlib.sha256(data).hexdigest();key=record['key'].encode('ascii');assert checker(named['CHECK'],key)[0]==1;info={k:record[k] for k in ('constants','targets')}
  license_data+=key;records.append({'depth':depth,'key':key.decode('ascii'),'sha256':hashlib.sha256(data).hexdigest(),**info})
  print('  accepted key:',key.decode('ascii'),flush=True)
  data=ARC4.new(key).decrypt(named['MATRYOSHKA']);assert data[:2]==b'MZ','next layer is not a PE'
  (args.out/'keys.json').write_text(json.dumps(records,indent=2));(args.out/'license-prefix.bin').write_bytes(license_data)
 else:raise RuntimeError('layer budget exhausted')

if __name__=='__main__':main()
