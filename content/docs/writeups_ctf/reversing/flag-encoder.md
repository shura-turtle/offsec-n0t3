---
title: "Flag Encoder"
date: 2026-10-26T01:53:00+06:30
bookToc: true
description: "Reverse a repeating XOR layer and custom Base64 alphabet to recover the encoded flag."
---

# Flag Encoder

## Original illustrated walkthrough

The pages below reproduce the supplied PDF in order, including every screenshot and code image. Select a page to open it at full size. [Download the original PDF](/writeups_ctf/reversing/flag-encoder/source.pdf).

### Page 1: Challenge string, argument branch, and IDA graph

[![flag-encoder PDF page 1: Challenge string, argument branch, and IDA graph](/writeups_ctf/reversing/flag-encoder/page-1.jpg)](/writeups_ctf/reversing/flag-encoder/page-1.jpg)

### Page 2: Encoder call and processing loop

[![flag-encoder PDF page 2: Encoder call and processing loop](/writeups_ctf/reversing/flag-encoder/page-2.jpg)](/writeups_ctf/reversing/flag-encoder/page-2.jpg)

### Page 3: XOR loop and key bytes in the hex view

[![flag-encoder PDF page 3: XOR loop and key bytes in the hex view](/writeups_ctf/reversing/flag-encoder/page-3.jpg)](/writeups_ctf/reversing/flag-encoder/page-3.jpg)

### Page 4: Custom Base64 routine and alphabet

[![flag-encoder PDF page 4: Custom Base64 routine and alphabet](/writeups_ctf/reversing/flag-encoder/page-4.jpg)](/writeups_ctf/reversing/flag-encoder/page-4.jpg)

### Page 5: Continuation of the Base64 table screenshot

[![flag-encoder PDF page 5: Continuation of the Base64 table screenshot](/writeups_ctf/reversing/flag-encoder/page-5.jpg)](/writeups_ctf/reversing/flag-encoder/page-5.jpg)

### Page 6: Full inverse procedure and recovered flag

[![flag-encoder PDF page 6: Full inverse procedure and recovered flag](/writeups_ctf/reversing/flag-encoder/page-6.jpg)](/writeups_ctf/reversing/flag-encoder/page-6.jpg)

## Searchable solve steps

The [repaired executable from Corrupted](corrupted/) accepts a command-line argument and prints an encoded form. This challenge supplies the encoded string:

```text
lBaY4gCyygnZ3YFweaCbCfnGm1JcSiNpzE8mjZGCcRA=
```

The PDF includes the reverse-engineering observations; the executable itself was not available in this workspace. The decoder below was checked against the supplied string and recovers the PDF's flag.

## 1. Trace the encoder

In IDA, the argument-count branch reaches a usage message for one argument and the encoding path for two. The latter calls `sub_401180` before printing `Obfuscated: %s`. Inside that function, a loop XORs the input using bytes at `byte_414380`. The next routine, `sub_401000`, uses Base64-style shifts and `0x3f` masks with a custom table at `byte_414348`.

The PDF text extraction puts a space before the XOR key, but the decoded data confirms the key **starts with `y`**, with no leading space:

```text
yC3NvR8qNHynjusu
```

The 64-character alphabet and padding character are:

```text
CatS4vesTh3WorldbcfgijkmnpquwxyzABDEFGHIJKLMNOPQRUVXYZ01256789+/=
```

## 2. Invert the layers

Translate the custom alphabet to the standard Base64 alphabet, decode, then apply the same repeating XOR:

```python
import base64

custom = "CatS4vesTh3WorldbcfgijkmnpquwxyzABDEFGHIJKLMNOPQRUVXYZ01256789+/="
standard = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
encoded = "lBaY4gCyygnZ3YFweaCbCfnGm1JcSiNpzE8mjZGCcRA="
key = b"yC3NvR8qNHynjusu"

raw = base64.b64decode(encoded.translate(str.maketrans(custom, standard)))
flag = bytes(byte ^ key[i % len(key)] for i, byte in enumerate(raw))
print(flag.decode())
```

Locally reproduced output:

```text
CSG_FLAG{c0rrect_fl4g_sh0wn9354}
```

