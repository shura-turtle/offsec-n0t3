---
title: "xxd"
weight: 28
bookToc: true
---

**Use for:** hex dumps, byte offsets, hex decoding and small binary edits.  
**Run in:** WSL; supplied with Vim tooling.

## Inspect a file header or region

```bash
xxd -l 64 challenge.bin                  # First 64 bytes
xxd -s 0x100 -l 64 challenge.bin         # Region at hex offset 0x100
xxd -g 1 challenge.bin                  # One byte per group
xxd -e -g 4 -l 64 challenge.bin          # Display little-endian 32-bit groups
```

## Convert bytes ↔ plain hex

```bash
xxd -p challenge.bin > plain_hex.txt
xxd -r -p plain_hex.txt > restored.bin

# Decode a short known hex string
printf '666c61677b64656d6f7d' | xxd -r -p
```

## Make a C-style byte array

```bash
xxd -i challenge.bin > challenge_array.h
```

## CTF: patch a working copy

```bash
cp challenge.bin patched.bin

# Write one 0x90 byte at offset 0x20 in the copy
printf '00000020: 90\n' | xxd -r - patched.bin

# Confirm the modified region
xxd -s 0x20 -l 16 patched.bin
```

## Gotchas

- Normal dump offsets are hex; do not confuse `0x20` with decimal 20.
- A patch uses a file offset, not a process virtual address.
- `xxd -r` can silently ignore text that is not valid dump data; confirm the resulting bytes.
- Use `-r -p` for plain hex and `-r` for an addressed xxd dump.

## Flags explained

| Flag | Meaning |
| --- | --- |
| `-l N` | Read at most N input bytes |
| `-s OFFSET` | Start at an input byte offset |
| `-g N` | Group N bytes together in the display |
| `-e` | Show groups in little-endian word order |
| `-p` | Produce plain hex without addresses/ASCII columns |
| `-r` | Reverse a hex dump into bytes |
| `-r -p` | Decode plain hex text |
| `-i` | Produce a C include-style byte array |
| `-c N` | Set bytes per output line |

`-r` means reverse conversion here. It does not mean recursive or read-PCAP.

## CTF: read a size field

```bash
# Four bytes at an example offset, displayed without ambiguity
xxd -s 0x10 -l 4 -g 1 challenge.bin
```

If those bytes are `78 56 34 12`, the little-endian integer is `0x12345678`. For arithmetic, parse them with Python rather than reversing text by eye.

```python
from pathlib import Path

data = Path("challenge.bin").read_bytes()
field = data[0x10:0x14]
assert len(field) == 4
print("little:", int.from_bytes(field, "little"))
print("big:", int.from_bytes(field, "big"))
```

## CTF: compare headers or patched bytes

```bash
xxd -g 1 -l 128 original.bin > original_header.txt
xxd -g 1 -l 128 modified.bin > modified_header.txt
diff -u original_header.txt modified_header.txt
```

A repaired header may reveal additional damage later in the file. Check the actual format parser after patching.

## CTF: inspect the end of a file

```bash
# Negative offset relative to EOF: inspect the final 64 bytes
xxd -s -64 challenge.bin
```

Useful for trailers, archive records and appended messages. A fixed trailer signature can occur inside ordinary payload bytes; validate its placement.

## CTF: build a raw byte fixture

```bash
printf '89504e470d0a1a0a' | xxd -r -p > png_signature.bin
xxd -g 1 png_signature.bin
```

This creates only an eight-byte signature, not a valid PNG. It is useful for comparing a suspected damaged header or testing your own parser’s signature check.

Reference: [xxd manual](https://github.com/vim/vim/blob/master/runtime/doc/xxd.1).

## Related playbooks

- [Binary strings and encodings](../../reversing-expl/strings-encodings/)
- [Bounded file carving](../../steganograph-expl/archives-carving/)
