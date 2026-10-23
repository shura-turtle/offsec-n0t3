---
title: "Strings & Encodings · Preserve the Bytes"
weight: 6
bookToc: true
---

# Strings and encodings

**Find the bytes, record their offset/length, decode the right layer, then confirm where the result is used.** Readable output is a lead, not proof of the flag.

## 1. ASCII and wide strings

```bash
strings -a -n 4 -t x challenge
strings -a -e l -n 4 -t x challenge
strings -a -e b -n 4 -t x challenge
```

GNU strings: `-t x` prints file offsets in hex, `-e l` scans 16-bit little-endian characters, `-e b` 16-bit big-endian. Check implementation support before using flags. UTF-16LE strings commonly appear as `66 00 6c 00 61 00 67 00`.

Short strings may be missed by minimum-length settings. Stack-built strings are assembled by instructions and may never exist contiguously in the file. Follow the code that writes the buffer or dump memory after construction.

## 2. Disk offset, VA and RVA

| Term | Meaning |
| --- | --- |
| File offset | Position in bytes on disk |
| VA | Virtual address in a loaded or static memory layout |
| RVA | Offset relative to an image base |
| Runtime base | Actual load address, potentially changed by ASLR |

For a PE section containing a VA, after validating bounds:

```text
RVA = VA - ImageBase
file_offset = RVA - section.VirtualAddress + section.PointerToRawData
```

This applies only to bytes backed by the section's raw disk range. Uninitialized tails have memory bytes without corresponding file bytes. For ELF, use the containing load segment's virtual/file offsets; do not apply the PE formula with guessed section values.

A strings tool's file offset is not a runtime breakpoint address. In Ghidra, inspect Memory Map and references to correlate addresses; validate with known bytes.

## 3. Extract exact bytes

Using the supplied Python helper:

```bash
python byte_workbench.py --file challenge --offset 0x2400 --length 32 --output blob.bin reverse
```

That example **reverses** the selected 32 bytes. For a byte-exact slice with no transform, use:

```python
from pathlib import Path
raw = Path('challenge').read_bytes()
offset, length = 0x2400, 32
assert 0 <= offset <= len(raw) and offset + length <= len(raw)
Path('blob.bin').write_bytes(raw[offset:offset+length])
```

A transform helper doing a slice plus reverse is not a pure extraction command. Keep the operation explicit. [HxD](../../ajcbbc_allow_tools/hxd/) selection/export and [xxd](../../ajcbbc_allow_tools/xxd/) can inspect the same range.

## 4. Recognize a likely encoding

| Data shape | Candidate | Verification |
| --- | --- | --- |
| Hex digits, even count | Hex | Decode then inspect bytes/use site |
| Base64 alphabet/padding | Base64 | Strict decode and re-encode canonical form |
| URL-safe `-_` | Base64url | Explicit alphabet/padding rules |
| `%41%42` | Percent encoding | Decode one layer at a time |
| `\\x41` text | Escaped byte representation | Distinguish literal backslash bytes from display notation |
| Many zero bytes alternating ASCII | UTF-16 | Decode with correct byte order |
| Readable only after XOR | Repeated/single key | Reapply key and verify original ciphertext |

Base64 is an encoding, not encryption. A cryptographic hash is not a reversible encoding; knowing its hexadecimal digest does not reveal an arbitrary input.

## 5. Python byte recipes

```python
import base64
raw = bytes.fromhex('666c61677b64656d6f7d')
assert raw == b'flag{demo}'
assert base64.b64decode(base64.b64encode(raw), validate=True) == raw
wide = raw.decode('ascii').encode('utf-16le')
assert wide.decode('utf-16le') == 'flag{demo}'
```

For Base64url whose format permits omitted padding:

```python
encoded = b'ZmxhZ3tkZW1vfQ'
assert len(encoded) % 4 != 1
raw = base64.b64decode(encoded + b'='*((-len(encoded))%4), altchars=b'-_', validate=True)
```

Only add padding when the format really is unpadded Base64url. Repairing arbitrary corrupt text until it decodes can hide a wrong hypothesis.

## 6. Endianness and words

```python
import struct
word = 0x67616c66
assert struct.pack('<I', word) == b'flag'
assert struct.pack('>I', word) == b'galf'
```

For an array of little-endian 32-bit words, pack **each word**, preserving array order. Reversing the full blob reverses both word order and byte order.

## 7. XOR known-plaintext check

If ciphertext C and a confirmed plaintext prefix P align, candidate key bytes are `C XOR P`. For repeating-key XOR, verify the derived key period across more bytes.

```python
cipher = bytes.fromhex('454f42445847464e4c5e')
prefix = b'flag{'
key_prefix = bytes(c ^ p for c,p in zip(cipher,prefix))
print(key_prefix)  # b'#####': supports a 0x23 single-byte key here
```

A printable single-byte XOR candidate is not sufficient. Verify expected syntax, the rest of the data and the binary's actual transform. Ciphertexts may include a header before the encoded string.

## 8. Troubleshooting

| Symptom | Check |
| --- | --- |
| Text looks reversed in groups | Word endianness |
| One plausible prefix, garbage rest | Wrong key period, stateful transform or false prefix |
| Missing last character | Array length, NUL terminator, text export truncation |
| Decode error on high bytes | Wrong character encoding; inspect hex first |
| Visible `\\x00` instead of NUL | Escaped text needs parsing, not direct byte use |
| String never referenced | Dead data/decoy or dynamic reference |

Use [CyberChef](../../ajcbbc_allow_tools/cyberchef/) for visual pipelines, but record operation order and input/output encoding so the recipe can be reproduced in Python.

## References

[GNU strings](https://sourceware.org/binutils/docs/binutils/strings.html), [Python struct](https://docs.python.org/3/library/struct.html), [Python base64](https://docs.python.org/3/library/base64.html), [PE format](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format).
