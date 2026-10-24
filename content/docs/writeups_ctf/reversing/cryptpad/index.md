---
title: "cryptpad"
date: 2026-10-24
weight: 1
bookToc: true
description: "Read an RC4 key from a file trailer, decrypt the flag, and compare the result with the original x86 routine."
---

# cryptpad

[Download solver](files/solve.py)

The handout contains a small Windows text editor and an encrypted file. The editor generates a random RC4 key for each saved file, then appends the key to that same file. Recovering the flag therefore requires understanding the file layout, not brute-forcing RC4.

```text
CMO{r0ll_y0ur_0wn_b4d_c0d3}
```

The Python implementation below agrees with the original x86 decryption routine executed in Unicorn. This solve does not require starting the GUI or contacting a service.

## 1. Identify the handout

The files are under `cryptpad/handout/` in the public repository:

```text
cryptpad.exe  11776 bytes
flag.enc        64 bytes
```

Run:

```bash
file cryptpad.exe
sha256sum cryptpad.exe flag.enc
xxd flag.enc
```

Recorded hashes:

```text
353ca1edc7a79a8c222f414346c6a9113b1f943c0cc7c345abb320b88eb35a66  cryptpad.exe
035883e1caa959e32fd906ba4026d36f82266e76a7b929e7100466ee69567235  flag.enc
```

`cryptpad.exe` is a native PE32 GUI executable for Intel i386, with an image base of `0x400000`. Its code is only `0x791` bytes long. No managed-code decompiler is needed.

The end of the encrypted file is particularly useful:

```text
00000030: 16f6 b41c 0000 00e8 171b f450 3f3d 7008
```

The final `08` is not ordinary padding. The decryption routine uses it as the appended key length.

## 2. Follow the file-saving path

Disassemble the program:

```bash
objdump -d -M intel cryptpad.exe > cryptpad.asm
objdump -x cryptpad.exe
```

Relevant imports include `CreateFileA`, `WriteFile`, `GetWindowTextA`, and `SystemFunction036`. The last function is the random-byte generator used for both padding and key bytes. Its indirect-call wrapper is at `0x40166b`.

The save path starts at `0x4013bd`. It obtains the editor text length, adds one byte for the NUL terminator, allocates a buffer, and rounds the output size up to a multiple of `0x40` bytes. It fills the extra space with random data and generates eight random key bytes at `0x4024c5`.

The call at `0x401490` invokes the transform at `0x4014eb` with three stack arguments:

```text
buffer pointer
plaintext length, including NUL
mode = 1
```

The returned size is passed to `WriteFile`. This is enough to establish that the encrypted file includes more than just encrypted text.

## 3. Read the trailer-writing code

After the cipher operations, the mode-one branch writes metadata near the end of the allocated file buffer:

```asm
401637  mov     edi, [ebp+8]
40163a  mov     eax, [ebp+0xc]
40163d  add     edi, eax
40163f  add     edi, [0x403581]
401645  sub     edi, 0xd
401648  mov     eax, [ebp+0xc]
40164b  mov     [edi], eax
40164d  add     edi, 4
401650  mov     ecx, 8
401655  mov     esi, 0x4024c5
40165a  rep movsb
40165c  mov     byte ptr [edi], 8
```

The metadata occupies 13 bytes:

```text
... encrypted text ... random filler ... | length:u32le | key:8 bytes | 08
```

For this 64-byte file, the trailer starts at `64 - 13 = 51`, or `0x33`:

| File offset | Bytes | Meaning |
| --- | --- | --- |
| `0x00`–`0x1b` | 28 bytes | Ciphertext for text and NUL |
| `0x1c`–`0x32` | 23 bytes | Filler, not required for decryption |
| `0x33`–`0x36` | `1c 00 00 00` | Plaintext length, 28 |
| `0x37`–`0x3e` | `e8 17 1b f4 50 3f 3d 70` | RC4 key |
| `0x3f` | `08` | Key length |

This explains the recognizable little-endian integer in an otherwise random-looking tail.

## 4. Confirm that mode zero reads the same layout

The beginning of `0x4014eb` checks its mode argument. Mode zero selects the file-decoding path.

It computes the last-byte address from `buffer + file_size - 1`, reads the key length, moves backward by that length, and copies the key into `0x4024c5`. It then reads the preceding DWORD as the number of bytes to transform.

The code uses a DWORD load at the last-byte address, even though only one byte belongs to the file. In the recorded zero-initialized model, the following bytes are zero and the value is eight. The standalone parser reads one byte explicitly and validates the trailer bounds instead of reproducing that out-of-bounds load.

There are a few overlapping instruction boundaries in a linear `objdump` listing. In particular, follow the actual branch to `0x401549`; the byte there is `push edx`. Decoding from the preceding junk byte produces a misleading `jne`. The branch target determines the instruction boundary.

## 5. Recognize RC4 and account for both XOR passes

The transform has three stages:

```text
XOR with bytes beginning at the key buffer
RC4
XOR with bytes beginning at the same key buffer
```

The two outer passes use the same byte sequence and offsets. The RC4 operation between them is also a bytewise XOR with a keystream. Therefore:

```text
((plaintext XOR outer_mask) XOR rc4_stream) XOR outer_mask
    = plaintext XOR rc4_stream
```

For the supplied file, this reduces to standard RC4 with the appended eight-byte key.

The RC4 identification comes from the full algorithm, not only the 256-byte table: `0x401570` initializes the state permutation; `0x4015b7` performs the key-scheduling swaps; and `0x4015e2` begins the keystream-generation loop with two changing indices and state swaps.

## 6. Decrypt the file

The key and length can be extracted using only the trailer:

```python
from pathlib import Path
import struct
from Crypto.Cipher import ARC4

encrypted = Path("flag.enc").read_bytes()
key_length = encrypted[-1]
trailer = len(encrypted) - key_length - 5
length = struct.unpack_from("<I", encrypted, trailer)[0]
key = encrypted[trailer + 4:-1]
plaintext = ARC4.new(key).decrypt(encrypted[:length])

print(key.hex())
print(repr(plaintext))
```

Output:

```text
e8171bf4503f3d70
b'CMO{r0ll_y0ur_0wn_b4d_c0d3}\x00'
```

The final byte is the text editor's NUL terminator. Remove that one byte when displaying the flag.

The accompanying `solve.py` implements RC4 directly with the standard library, so ordinary decryption needs no third-party package:

```bash
python solve.py flag.enc --details
```

Output:

```text
File bytes: 64
Trailer offset: 0x33
Plaintext bytes including NUL: 28
RC4 key: e8171bf4503f3d70
CMO{r0ll_y0ur_0wn_b4d_c0d3}
```

## 7. Compare against the original machine code

Install Unicorn for the optional verification:

```bash
python -m pip install unicorn
python solve.py flag.enc --verify-native cryptpad.exe
```

The verifier maps the original PE sections at their preferred addresses and enters `0x4014eb` with a mode-zero call. The stack contains:

```text
return address = 0x300000
buffer         = 0x200000
file length    = 64
mode           = 0
```

It initializes the file-length global at `0x40357d`, then lets the original x86 routine parse the trailer, run its XOR passes, execute RC4, and return. No API hooks or instruction patches are required because that routine calls no external functions.

Both implementations produce the same 28 bytes, including the NUL terminator. The solver also runs RC4 over the recovered plaintext again and confirms that it reconstructs the original 28 ciphertext bytes.

The failure is in the file format: the randomly generated key is stored beside the data it is meant to protect. The extra random filler and XOR passes do not change that fact.

## Source

[Public challenge handout](https://github.com/crackmesone/ctf-2026-challenges-public/tree/5f8857cf3556e4e36d7e7fc4650044ae682701b8/cryptpad/handout).
