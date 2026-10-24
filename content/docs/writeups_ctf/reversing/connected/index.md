---
title: "Connected"
date: 2026-10-24
weight: 1
bookToc: true
description: "Simulated packet forwarding, checksum constraints, and a native flag replay."
---

# Connected

[Download solver](files/solve.py)

The handout is a Linux executable with C++ source in `connected/source_code`. The README also discloses the intended packet path and final flag. The useful reversing exercise is to explain why one particular message reaches PC1, then replay it against the unmodified executable. No outside host is contacted: the PCs, switches, and routers are simulated inside the process.

## 1. Follow the input through the simulated network

`src/main.cpp` prompts for `what` and `where`. The target address is `100.25.26.10`. It accepts a packet from the user only when the message starts with `msg_`, then strips those four bytes. Sending directly to PC1 does not work because PC1's handler rejects a packet whose sender is the user.

The target sends the stripped body through PC9 (`83.48.92.8`), which XORs every byte with `0x42`. PC3, PC4, and PC7 send it through PC9 again before checking it. Because XOR is its own inverse, all three ultimately test the original eight-byte body. Their returned values control whether the target forwards that body to PC1.

## 2. Satisfy the three checks

PC3 (`64.14.3.25`) requires body length eight. PC7 (`100.25.26.15`) requires each byte to be printable and have an even numeric value. PC4 (`64.14.3.29`) requires a palindrome and checks this combined value:

```python
adler = zlib.adler32(body)
fletcher = (b << 8) | a  # a,b updated modulo 255 over each byte
positional = sum(byte << index for index, byte in enumerate(body))
combined = (adler ^ fletcher) ^ positional
```

The comparison value in the target is `100806214`. The supplied author solution gives `b':"*$$*":'`: it is eight bytes, reads the same backward, and each byte passes PC7. The [solver](files/solve.py) recomputes the checksum rather than assuming that the string is valid.

The complete first input is `msg_:"*$$*":`; the second is `100.25.26.10`. Keep the dollar signs literal. A quoted Python byte string avoids shell expansion.

## 3. Confirm the forwarded response

Save the linked solver as `solve.py`, then run it from a working directory containing the public challenge repository:

```bash
python3 solve.py connected/handout/connected
```

Use the actual handout path if its case differs on your copy. The solver sends both lines to the native process and asserts the resulting flag appears in its output. PC1 formats the forwarded body using its alphanumeric/underscore alphabet and `(byte + position) % 37`. My native replay printed:

```text
received: CMO{secret_code_v9hcdkd2}
```

**Flag:** `CMO{secret_code_v9hcdkd2}`
