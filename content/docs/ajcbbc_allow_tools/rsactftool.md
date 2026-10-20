---
title: "RsaCtfTool"
weight: 30
bookToc: true
---

**Use for:** weak RSA keys, known RSA attack patterns and private key recovery.  
**Run in:** WSL; Python based tool.

## Check the entry point first

```bash
# Current upstream CLI
RsaCtfTool --help

# Older supplied checkouts may instead use:
# python3 /path/to/RsaCtfTool.py --help
```

Use the installed version’s help. Recent upstream uses `--decryptfile`; older examples often use `--uncipherfile`.

## Inspect a public key

```bash
RsaCtfTool --dumpkey --key public.pem
openssl pkey -pubin -in public.pem -text -noout
```

## Try a relevant attack

```bash
# General weak-key recovery
RsaCtfTool --publickey public.pem --private

# Small private exponent candidate
RsaCtfTool --publickey public.pem --attack wiener --private

# Multiple supplied public keys
RsaCtfTool --publickey '*.pub' --private
```

## Decrypt challenge ciphertext

```bash
RsaCtfTool --publickey public.pem --decryptfile ciphertext.bin
```

Confirm whether the challenge ciphertext is raw bytes, hex, Base64 or an integer before supplying it.

## CTF notes

- Record `n`, `e`, ciphertext and any leaked factors/CRT values.
- Select an attack from the evidence rather than waiting indefinitely on all methods.
- Ordinary large RSA keys are not automatically breakable.
- Some attacks require optional dependencies or online services; availability and competition approval must be checked separately.
- Verify recovered plaintext bytes and padding; textbook RSA and OAEP differ.

## Flags explained

| Flag | Meaning |
| --- | --- |
| `--publickey FILE` | Select the target public key / supported key pattern |
| `--private` | Request recovered private key output |
| `--attack NAME` | Select a named supported attack |
| `--decryptfile FILE` | Read ciphertext bytes for decryption in current upstream |
| `--dumpkey` | Display key parameters |
| `--key FILE` | Supply the key inspected by dump/reconstruction modes |
| `--createpub` | Construct a public key using numeric parameters |
| `-n NUMBER` | RSA modulus n |
| `-e NUMBER` | RSA public exponent e |

`-e` means exponent here, while binwalk uses it for extraction. Confirm names with `--help`, especially on older supplied checkouts.

## Match the RSA weakness before selecting an attack

| Given clue | Candidate technique | Necessary check |
| --- | --- | --- |
| Two public keys share a prime | GCD between moduli | `1 < gcd(n1,n2) < n1` |
| `p` and `q` very close | Fermat factorization | Difference must be small enough |
| Unusually small private exponent | Wiener | Check recovered factors/private key |
| Tiny `e`, short unpadded plaintext | Exact integer root | The plaintext power must not wrap modulo n |
| Same message, small e, several moduli | Broadcast attack | Enough compatible ciphertexts/moduli |
| Leaked p/q/d/CRT values | Reconstruct key | Confirm `p*q == n` and valid exponents |
| Normal large random modulus | No obvious weakness | Search the challenge for leakage/implementation errors |

## CTF: shared-prime recovery without extra packages

```python
from math import gcd

# Worked example: both moduli share 61
n1, n2 = 3233, 2867
p = gcd(n1, n2)
assert 1 < p < n1
q = n1 // p
assert p * q == n1
print("factors:", p, q)
```

For many keys, inspect the supplied tool’s multi-key mode first. A GCD equal to the modulus can mean duplicate keys rather than a useful partial factor.

## Build a public key from decimal n and e

```bash
# Tiny worked values for syntax; use your challenge's full integers
RsaCtfTool --createpub -n 3233 -e 17 > example_public.pem
```

Confirm the file contains only a PEM block before using it. Some versions print diagnostics separately or use a different output option.

## Try close-prime factorization

```bash
# Use this only if the installed help lists the fermat attack
RsaCtfTool --publickey public.pem --attack fermat --private
```

A Fermat failure does not eliminate every RSA weakness. Decide the next technique from the challenge’s parameters and leaks.

## Convert a ciphertext integer to bytes

```python
from pathlib import Path

c = int(Path("cipher_integer.txt").read_text().strip(), 10)
raw = c.to_bytes(max(1, (c.bit_length() + 7) // 8), "big")
Path("ciphertext.bin").write_bytes(raw)
```

For fixed-width RSA blocks, use `(n.bit_length() + 7) // 8` as the width instead. If the input is hex text, use `int(text, 16)`; do not treat it as decimal.

## Check recovered textbook plaintext

```python
assert p * q == n
d = pow(e, -1, (p - 1) * (q - 1))
m = pow(c, d, n)
assert pow(m, e, n) == c % n
print(m.to_bytes(max(1, (m.bit_length() + 7) // 8), "big"))
```

Here `p`, `q`, `n`, `e` and `c` are the actual recovered/supplied integers. Verify the key mathematically before blaming text decoding.

## Keep attack dependencies separate

The approved tool may have attacks requiring SageMath or external factorization helpers. Its presence in a menu does not show the helper is installed. Record “dependency missing” separately from “attack ran and failed.” Online factor databases also depend on tournament network access.

References: [RsaCtfTool current CLI and examples](https://github.com/RsaCtfTool/RsaCtfTool), [Python integer operations](https://docs.python.org/3/library/stdtypes.html#numeric-types-int-float-complex).
