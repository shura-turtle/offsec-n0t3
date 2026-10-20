---
title: "Arc4 Decrypt"
weight: 1
# bookFlatSection: false
# bookToc: true
# bookHidden: false
# bookCollapseSection: false
# bookComments: false
# bookSearchExclude: false
# bookHref: ''
# bookIcon: ''
---

ida-pattern
```
  for ( i = 0; i < 256; ++i )
    v44[i] = i;
  v8 = a6;
  v9 = 0;
  for ( j = 0; j < 256; ++j )
  {
    if ( v8 <= j % v8 )
      sub_401710();
    p_Block = &Block;
    v12 = v44[j];
    if ( a7 >= 0x10 )
      p_Block = (_DWORD **)Block;
    v9 = (v12 + *((char *)p_Block + j % v8) + v9) % 256;
    v44[j] = v44[v9];
    v44[v9] = v12;
  }
```

```python
import struct
from Crypto.Cipher import ARC4

v36 = [0] * 11
v36[0] = 0x33122A35
v36[1] = 0xB2645787
v36[2] = 0x34A6EF00
v36[3] = 0x3EDEE001
v36[4] = 0x40EC2101
v36[5] = 0xB0691D26
v36[6] = 0x7BB269B0
v36[7] = 0x6EB2256
v36[8] = 0xCB5DF2BE
v36[9] = 0x512B0F79
v36[10] = 0x55

ciphertext = b"".join(struct.pack('<I', x) for x in v36)

cipher = ARC4.new(b'LLURULDUL')
print(cipher.decrypt(ciphertext).decode('utf-8'))
```
