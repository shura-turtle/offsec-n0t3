---
title: "Python · Offline Snippet Library"
weight: 3
bookToc: true
---

# Offline Python Snippet Library

Ready-to-save helpers are grouped by artifact. Each guide explains inputs, command examples, output and limits; each script has `--help`. Keep a local copy of the notes and the referenced `.py` files before the event.

| Category | Guide | Examples |
| --- | --- | --- |
| Web | [Web helpers](../../web-expl/python-snippets/) | Byte encodings, JWT decode/sign with known key, boolean SQL extraction |
| Network | [Network helpers](../../network-expl/python-snippets/) | Persistent protocol session, DNS reconstruction |
| Steganography | [Stego helpers](../../steganograph-expl/python-snippets/) | Bounded carving, explicit image LSB extraction, Unicode inspection |
| Reversing | [Reversing helpers](../../reversing-expl/python-snippets/) | Byte transforms, XOR, endianness, reversible checker templates |
| Crypto reference | [Existing Python cookbook](../../ajcbbc_allow_tools/python3/#cookbook-map) | Base encodings, classical ciphers, AES, ChaCha, hashes, RSA |

## Check your local environment once

```bash
python --version
python web_helpers.py --help
```

Some Windows setups use `py -3` or `python3`; substitute the actual installed command. Standard-library helpers do not need `pip`. Optional package scripts clearly state the dependency, such as Pillow for decoded image pixels.

## Small byte primitives

```python
from pathlib import Path

data = Path('sample.bin').read_bytes()
print('length:', len(data))
print('first 16:', data[:16].hex())
print('u32 LE:', int.from_bytes(data[:4], 'little'))
print('u32 BE:', int.from_bytes(data[:4], 'big'))
```

```python
def xor_repeat(data, key):
    if not key:
        raise ValueError('empty XOR key')
    return bytes(byte ^ key[i % len(key)] for i, byte in enumerate(data))

original = b'flag{demo}'
cipher = xor_repeat(original, b'ICE')
assert xor_repeat(cipher, b'ICE') == original
```

```python
import hashlib
from pathlib import Path

digest = hashlib.sha256()
with Path('sample.bin').open('rb') as source:
    for chunk in iter(lambda: source.read(1024 * 1024), b''):
        digest.update(chunk)
print(digest.hexdigest())
```

## Before adapting a snippet

1. Record the input type: text, hex spelling, raw bytes, or decoded image pixels.
2. Reproduce the supplied small sample before substituting challenge data.
3. Change only the known format/key/offset/endianness/field mapping.
4. Save binary output with `write_bytes`, not a lossy text conversion.
5. Verify a round-trip, known plaintext, valid parser output, or exact target comparison.

A helper implements the assumptions you supply; it does not establish those assumptions. Read the technique page first.
