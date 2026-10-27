from pathlib import Path
import struct, zlib, hashlib
ROOT=Path.cwd()
IMG=ROOT/'HDS-USB01.dd'
EXE=ROOT/'work/prnupd.exe'
MASK=(1<<64)-1
IV0=0xa2de40f113e09aa5
IV1=0x3b008f876c3f3b4d
FINAL=0x07c8f4142d06dd90

def recover_executable():
    """Follow the orphaned PRN_DRV.BIN FAT chain and decrypt its LKD1 payload."""
    fat_base=1048576+32*512
    data_base=(2048+2074)*512
    cluster=43
    seen=set()
    chunks=[]
    with IMG.open('rb') as f:
        while cluster<0x0ffffff8:
            if cluster in seen:raise ValueError('FAT loop')
            seen.add(cluster)
            f.seek(data_base+(cluster-2)*4096)
            chunks.append(f.read(4096))
            f.seek(fat_base+cluster*4)
            cluster=struct.unpack('<I',f.read(4))[0]&0x0fffffff
    wrapped=b''.join(chunks)[:106528]
    if wrapped[:4]!=b'LKD1':raise ValueError('staging header missing')
    length=struct.unpack_from('<I',wrapped,4)[0]
    key=wrapped[16:32]
    s=list(range(256));j=0
    for i in range(256):
        j=(j+s[i]+key[i%16])&255
        s[i],s[j]=s[j],s[i]
    x=y=0;result=bytearray()
    for c in wrapped[32:32+length]:
        x=(x+1)&255;y=(y+s[x])&255;s[x],s[y]=s[y],s[x]
        result.append(c^s[(s[x]+s[y])&255])
    executable=bytes(result)
    if not executable.startswith(b'MZ') or hashlib.sha256(executable).hexdigest()!='7ab789767b932f4d2f425ddb96476356cc031e50d9960afaa858c58b6466f7b5':
        raise ValueError('recovered executable failed integrity check')
    EXE.parent.mkdir(exist_ok=True)
    EXE.write_bytes(executable)
    return executable

_exe=recover_executable()
_pe=struct.unpack_from('<I',_exe,0x3c)[0]
_timestamp=struct.unpack_from('<I',_exe,_pe+8)[0]
_obfuscated=struct.unpack_from('<22I',_exe,0x17a00)
_state=_timestamp
_round_constants=[]
for _c in _obfuscated:
    _state=(_state*0x19660d+0x3c6ef35f)&0xffffffff
    _round_constants.append(_c^_state)
CONSTS=_round_constants[:21]

def ror(x,n):return ((x>>n)|(x<<(64-n)))&MASK
def rol(x,n):return ((x<<n)|(x>>(64-n)))&MASK

def keys(block):
    k,l=struct.unpack('<QQ',block)
    out=[k]
    for c in CONSTS:
        l=((ror(l,8)+k)&MASK)^c
        k=ror(k,61)^l
        out.append(k)
    return out

def encrypt_block(block,key):
    x,y=struct.unpack('<QQ',block)
    for k in keys(key):
        x=((ror(x,8)+y)&MASK)^k
        y=ror(y,61)^x
    return struct.pack('<QQ',x,y)

def decrypt_block(block,key):
    x,y=struct.unpack('<QQ',block)
    for k in reversed(keys(key)):
        y=rol(y^x,61)
        x=rol(((x^k)-y)&MASK,8)
    return struct.pack('<QQ',x,y)

def hash128(data):
    x,y=IV0,IV1
    def compress(x,y,block):
        b=encrypt_block(struct.pack('<QQ',x,y),block)
        a,c=struct.unpack('<QQ',b)
        return x^a,y^c
    n=len(data)
    for i in range(0,n//16*16,16): x,y=compress(x,y,data[i:i+16])
    tail=data[n//16*16:]
    x,y=compress(x,y,(tail+b'\x80').ljust(16,b'\0'))
    x,y=compress(x,y,struct.pack('<QQ',n,FINAL))
    return struct.pack('<QQ',x,y)

def restore(sealed,key):
    raw=sealed.read_bytes()
    tag,ver,prefix,size,crc,digest=struct.unpack('<4sIIQI16s',raw[-40:])
    assert tag==b'LKD7' and ver==1 and size==len(raw)-40
    assert prefix%16==0 and prefix<=size
    original_name=sealed.name.split('_Desktop_')[-1].split('_Branding_')[-1].removesuffix('.lockd')
    assert hash128(struct.pack('<Q',size)+original_name.upper().encode())==digest
    data=bytearray(raw[:-40]);previous=digest
    for i in range(0,prefix,16):
        c=bytes(data[i:i+16]); d=decrypt_block(c,key)
        data[i:i+16]=bytes(a^b for a,b in zip(d,previous))
        previous=c
    print(sealed.name,'CRC',hex(zlib.crc32(data)),hex(crc),'iv',digest.hex(),'first',data[:16].hex())
    assert zlib.crc32(data)==crc
    output=ROOT/'work'/sealed.name.removesuffix('.lockd')
    output.write_bytes(data)
    return output

if __name__=='__main__':
    img=IMG.read_bytes(); exe=EXE.read_bytes()
    device_seed=img[512+8:512+24]
    volid=img[1048576+0x43:1048576+0x47]
    executable_digest=hash128(exe)
    campaign=b'NX7-2R8QF4KD9T'
    key=hash128(device_seed+volid+executable_digest+campaign)
    print('exe hash',executable_digest.hex(),'key',key.hex())
    for sealed in sorted((ROOT/'victim').glob('*.lockd')):restore(sealed,key)
