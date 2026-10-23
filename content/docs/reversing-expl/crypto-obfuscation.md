---
title: "Crypto & Obfuscation · Identify, Model, Verify"
weight: 7
bookToc: true
---

# Crypto and obfuscation in reversing

**Identify the actual operation from code and constants.** A familiar constant is a clue; a complete state update and data flow make the identification credible.

## 1. Quick recognition

| Pattern | Candidate | What to record |
| --- | --- | --- |
| XOR same byte / periodic table | Single/repeating XOR | Key bytes, starting offset, period |
| Add/subtract index | Position-dependent transform | Truncation width, index origin |
| Rotate + XOR/add | Custom byte/word mixing | Width, count, order |
| `0x811c9dc5`, multiply `0x01000193` | FNV-1a 32-bit candidate | XOR-before-multiply vs after, width, seed |
| `0x9e3779b9` with paired word rounds | TEA/XTEA-like candidate | Exact round equations and endian |
| 256-element permutation + swaps | RC4-like state | KSA/PRGA, drop count, key |
| `expand 32-byte k` + add/xor/rotate | ChaCha/Salsa family | Variant, nonce/counter layout |
| S-box/table rounds | AES or custom substitution | Match full structure, mode/key/IV |
| Dispatch loop and bytecode PC | Custom VM | Opcode widths, state, semantics |

Standard crypto can also be hidden behind library calls. Inspect call arguments before reimplementing it. The [Python cookbook](../../ajcbbc_allow_tools/python3/) covers library-backed crypto where permitted; the downloads here use stdlib byte transforms.

## 2. Reversible byte transforms

```python
def rol8(x,n):
    n %= 8
    return ((x << n) | (x >> ((8-n)%8))) & 255

def encode(data,key=0x23):
    return bytes(rol8(((b ^ key)+i)&255,3) for i,b in enumerate(data))

def decode(data,key=0x23):
    return bytes(((rol8(b,-3)-i)&255)^key for i,b in enumerate(data))

assert decode(encode(b'flag{demo}')) == b'flag{demo}'
```

Addition/subtraction invert modulo 256. XOR is self-inverse. Rotation inverts by rotating the other direction with the same width. Byte reversal and swapping each word are different operations.

## 3. Multiplication modulo a power of two

For `y = a*x + b mod 256`, an inverse exists for all bytes only when `a` is odd:

```python
a,b = 7,19
ainv = pow(a,-1,256)
y = (a*123+b)&255
x = ((y-b)*ainv)&255
assert x == 123
```

If `a` is even, information may be lost; enumerate the 256 possible byte values or solve constraints. Python's modular inverse raises an error when gcd is not 1.

## 4. Hashes and checksums

FNV-1a example, after identifying this exact variant:

```python
def fnv1a32(data):
    h=0x811c9dc5
    for b in data:
        h=((h^b)*0x01000193)&0xffffffff
    return h
```

A known final hash does not identify a unique string. Length/alphabet/prefix constraints determine whether bounded search is feasible. A small checksum can have many collisions, but a collision accepted by one gate may fail other checks or produce a different decryption key.

For a known final byte and reversible odd multiplier, a rolling step can be inverted. For many unknown bytes, meet-in-the-middle can reduce a finite search at the cost of memory. Do not describe arbitrary SHA-256 recovery as decryption.

## 5. Genuine encryption

Before decrypting, obtain:

```text
Algorithm and exact variant:
Key bytes / derivation inputs:
Mode:
IV or nonce:
Counter layout/start:
Ciphertext range:
Padding:
Authentication tag / associated data:
Byte order and text encoding:
```

Correct AES key plus wrong mode/IV can produce misleading partial output. Authentication failure means the inputs/format/model need investigation; ignoring the tag is not a valid verified decryption. CBC padding success alone is also weak evidence.

## 6. Stateful flag computation

A game or sequence challenge may hash every action and use that hash to decrypt a final blob. Map state transitions explicitly:

| Action | State effect | Evidence |
| --- | --- | --- |
| `talk(text)` | Adds length and updates rolling hash | Loop and length check |
| `move(id)` | Updates sequence tag | Switch/transition table |
| `finish()` | Checks counters and decrypts | Success branch |

Patching only `finish()` may leave the wrong key. Reach the correct state or reproduce all state-dependent key derivation in the model.

## 7. VM and control-flow obfuscation

Separate dispatcher noise from opcode semantics. Recover one opcode at a time with a tiny trace. Record stack underflow behavior, integer widths, signed branches, operand endianness and PC updates. A generic `eval` of unknown bytecode is not a VM implementation.

Opaque predicates and flattened control flow can be simplified after identifying the state variable and transitions. Confirm any assumed invariant dynamically at multiple inputs before discarding a branch as unreachable.

## 8. Constraints vs direct inversion

Use direct inversion for bijective independent byte transforms. Use bounded enumeration for a tiny finite key. Use an optional constraint solver when cross-byte equations, carries and branches make manual inversion awkward.

Z3 bitvectors model wraparound, but signed comparisons and arithmetic shift differ from unsigned comparison/logical shift. Use `ULT/ULE/UGT/UGE` and `LShR` when the native operation is unsigned. See [downloadable model](../python-snippets/) for an explicit small example and its dependency boundary.

## Finish

Compare forward-model bytes with a known debugger trace, recover a candidate, then run it through the original unpatched validator. Save intermediate states so a one-byte discrepancy can be located rather than guessed away.

## References

[Python modular pow](https://docs.python.org/3/library/functions.html#pow), [Z3 Python API](https://z3prover.github.io/api/html/namespacez3py.html), [Intel instruction references](https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html), [NIST AES specification](https://csrc.nist.gov/pubs/fips/197/final).
