---
title: "Python Snippets · Byte Workbench & Check Models"
weight: 9
bookToc: true
---

# Offline Python reversing snippets

**Download before the event, keep the model explicit and verify the forward transform.** These command-line scripts use Python 3 standard library by default and make no network requests. They are separate from Ghidra's script runtimes.

## Downloads

- [byte_workbench.py](/snippets/reversing/byte_workbench.py): explicit input bytes, slicing, XOR, all single-byte candidates, byte rotates/add/subtract, word swaps, Base64/hex and ROT13.
- [solve_constraints.py](/snippets/reversing/solve_constraints.py): a documented reversible validator example with a forward assertion; optional `--z3` solves the same model if that separate package is permitted and installed.

These tools implement stated transformations; they do not automatically infer an unknown algorithm or solve arbitrary binaries. Local `--output` paths write binary files and may replace an existing file, so choose distinct output names.

## 1. CLI structure

```bash
python byte_workbench.py --help
python byte_workbench.py --hex 454f42445847464e4c5e xor --key-hex 23
python byte_workbench.py --text 'flag{demo}' xor --key-hex 112233
python byte_workbench.py --file blob.bin xor-scan
```

Global input/output/slice options go **before** the operation. Operation arguments follow its name. Hex input accepts whitespace. `--text` uses UTF-8, while `--file` preserves raw bytes. Default output is a hex line plus Python byte representation; `--output` writes raw bytes only.

The single-byte demo prints:

```text
666c61677b64656d6f7d
b'flag{demo}'
```

`xor-scan` prints all 256 keys with printable ratio; it does not rank a guaranteed answer. Inspect actual binary logic and expected flag format.

## 2. Chain exact operations with files

```bash
python byte_workbench.py --file encrypted.bin --output step1.bin ror 3
python byte_workbench.py --file step1.bin --output step2.bin sub 7
python byte_workbench.py --file step2.bin --output decoded.bin xor --key-hex 23
```

Only use this chain if those are the recovered inverse operations. Index-dependent subtraction is not the same as `sub 7`; implement the actual model in a short Python expression or the supplied template.

## 3. Slice / endianness / rotations

```bash
python byte_workbench.py --file blob.bin --offset 0x20 --length 16 --output swapped.bin swap 4
python byte_workbench.py --hex 01020304 reverse
python byte_workbench.py --hex 01020304 rol 3
python byte_workbench.py --hex 01020304 add 0x20
```

`swap 4` reverses bytes inside each 4-byte word and requires divisible length. `reverse` reverses the complete sequence. `rol`/`ror` rotate each individual **8-bit byte**, not one large integer. Counts normalize modulo 8; addition/subtraction wrap modulo 256.

## 4. Encoding helpers

```bash
python byte_workbench.py --text 'flag{demo}' b64encode
python byte_workbench.py --text 'ZmxhZ3tkZW1vfQ==' b64decode
python byte_workbench.py --text '666c6167' hexdecode
python byte_workbench.py --text 'synt{qrzb}' rot13
```

Base64 decoder accepts the standard alphabet and removes whitespace, but deliberately rejects invalid characters or missing padding. Base64url requires explicit handling; see [strings/encodings](../strings-encodings/). ROT13 accepts ASCII text; it is not a transform for arbitrary binary bytes.

## 5. Validator model demo

The supplied constraint example models exactly:

```text
y[i] = ROL8(((x[i] XOR key) + i) mod 256, rotation)
```

```bash
python solve_constraints.py
python solve_constraints.py --encode-text 'flag{demo}'
python solve_constraints.py --target-hex YOUR_EXTRACTED_HEX --key 0x23 --rotation 3
```

Default target is a built-in synthetic fixture for `flag{demo}`. Custom target is extracted data from a matching model. The script decodes it and asserts that applying the forward transform reproduces every target byte. That assertion validates consistency with the model; running the candidate through the actual program validates the model itself.

## 6. Optional Z3 mode

```bash
python solve_constraints.py --z3
```

This imports `z3-solver` only on request. It is **not a standard-library dependency or an established approved tournament tool**. If unavailable, the direct inverse still works for this bijective demo.

For a real cross-byte model, replace the constraints with the exact recovered operations and widths. Example shape:

```python
# Optional external package, not needed by the normal downloads.
from z3 import BitVec, Solver, ULT, LShR
x = BitVec('x', 32)
s = Solver()
s.add(ULT(x, 1000))
s.add(LShR(x, 3) == 42)
```

This example has multiple solutions; it does not produce a unique challenge key. Add all actual constraints, inspect satisfiability and verify candidates in the original binary.

## 7. Small reusable extraction / packing

```python
from pathlib import Path
import struct
raw = Path('challenge').read_bytes()
offset, length = 0x100, 16
assert 0 <= offset <= len(raw) and offset+length <= len(raw)
blob = raw[offset:offset+length]
words = struct.unpack('<4I', blob)
assert struct.pack('<4I', *words) == blob
```

`<4I` is four unsigned little-endian 32-bit integers. Replace with the actual recovered representation. A 16-byte raw buffer is not automatically four meaningful integers.

## 8. Error interpretation

| Error | Fix |
| --- | --- |
| Invalid hex | Remove address labels/punctuation; provide byte pairs |
| Slice extends past input | Correct file offset and length |
| Empty XOR key | Supply actual nonempty hex key |
| Swap length mismatch | Use correct region or word width |
| Base64 padding error | Check alphabet and original format before repairing |
| Unknown CLI arguments | Put global options before operation |
| Z3 import error | Use stdlib inverse or prepare permitted optional package |

## Tool links and references

[Python tool cookbook](../../ajcbbc_allow_tools/python3/), [CyberChef](../../ajcbbc_allow_tools/cyberchef/), [Ghidra bytes/export](../ghidra-cheatsheet/). APIs: [argparse](https://docs.python.org/3/library/argparse.html), [struct](https://docs.python.org/3/library/struct.html), [base64](https://docs.python.org/3/library/base64.html), [Z3 Python](https://z3prover.github.io/api/html/namespacez3py.html).
