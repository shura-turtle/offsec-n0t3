---
title: "Python 3"
weight: 7
bookToc: true
---

**Use for:** byte manipulation, decoding, small solvers, artifact parsing.  
**Run in:** WSL. Exact Python 3.x version depends on the competition PC.

**Tournament rule:** additional libraries are allowed except AI/ML related libraries and tools.

## Choose the operation first

| Kind | Examples | Required information |
| --- | --- | --- |
| Text encoding | UTF-8, UTF-16LE, Latin-1 | Character encoding |
| Binary-to-text encoding | Hex, Base64, Base32, Base85 | Alphabet and framing; no secret key |
| Escaping | URL percent escapes, HTML entities | Escaping convention |
| Compression | gzip, zlib, bzip2, LZMA/XZ | Wrapper/format; usually no key |
| Classical cipher | Caesar, ROT13, Vigenère | Shift or keyword, alphabet rules |
| XOR | One byte, repeating key, stream XOR | Key/keystream or a recoverable weakness |
| Symmetric encryption | AES, ChaCha20, Salsa20 | Key plus mode-specific IV/nonce/counter |
| Authenticated encryption | AES-GCM/EAX, ChaCha20-Poly1305 | Key, nonce, ciphertext, tag, optional AAD |
| Public-key encryption | RSA / RSA-OAEP | Private key or a demonstrated weakness |
| Hash / MAC / KDF | SHA-256, HMAC, PBKDF2, scrypt | Exact input bytes and algorithm parameters |

Encoding is reversible without a secret. Hashes do not have a general decode/decrypt operation. A value that resembles hex could represent ciphertext, a hash, a key or ordinary bytes; identify its role from the challenge.

## Cookbook map

- [Encode/decode bytes and text](#encode-and-decode-text-without-losing-bytes)
- [Hex and Base encodings](#hex-encode-and-decode)
- [URL/HTML/escape layers](#url-and-html-encode-and-decode)
- [Classical ciphers](#rot13-caesar-and-atbash)
- [Compression wrappers](#compress-and-decompress-common-wrappers)
- [XOR recipes](#xor-helpers-with-explicit-length-rules)
- [Hashes, HMAC and key derivation](#hash-digest-bytes-versus-hex-text)
- [AES modes](#aes-choose-the-correct-mode)
- [ChaCha20 and related stream ciphers](#chacha20-encrypt-and-decrypt)
- [RSA-OAEP and weak-RSA recipes](#rsa-oaep-encrypt-and-decrypt)

The cookbook snippets are separate examples. Each crypto example imports what it uses; the XOR helper section explicitly defines shared functions for the following XOR recipes.

## Prepare non-AI crypto libraries

Python's standard library handles encodings, hashing, compression and basic modular arithmetic. The AES/ChaCha/RSA-OAEP examples below use **PyCryptodome**:

```bash
# --python chooses the existing interpreter; .venv is the environment directory
uv venv --python python3 .venv

# --python targets that exact environment; pycryptodome is the package name
uv pip install --python .venv/bin/python pycryptodome

# -c executes a short Python statement; Crypto is the import namespace
.venv/bin/python -c 'from Crypto.Cipher import AES, ChaCha20; print("crypto imports OK")'

# -u gives live/unbuffered output while running your saved solver
.venv/bin/python -u solve.py
```

These are usage examples; no package installation is performed by these notes. `pycryptodome` imports as `Crypto`; the alternative package `pycryptodomex` imports as `Cryptodome`. Use one consistent namespace and interpreter.

## Quick commands

```bash
python3 --version                          # Check the supplied interpreter
python3 solve.py                           # Run a saved CTF solver
python3 -m json.tool input.json             # Pretty print an API response
python3 -m zipfile -l archive.zip           # List ZIP members before extraction
python3 -m zipfile -e archive.zip out/      # Extract into a separate folder
python3 -m venv .venv                      # Create an isolated package environment
source .venv/bin/activate                  # Use that environment in this terminal
```

## Walkthrough: decode and inspect bytes

Save as `solve.py` and run `python3 solve.py`:

```python
from pathlib import Path
import base64
import hashlib
import re

encoded = Path("input.txt").read_text().strip()
data = base64.b64decode(encoded)
Path("decoded.bin").write_bytes(data)
print("length:", len(data))
print("sha256:", hashlib.sha256(data).hexdigest())
print(re.findall(rb"flag\{[^}\r\n]+\}", data))
```

## Byte recipes

```python
bytes.fromhex("666c6167")                  # Hex text → raw bytes
int.from_bytes(b"\x34\x12", "little")      # Decode a little-endian integer
(0x1234).to_bytes(2, "little")             # Encode an integer into two bytes

# Repeating-key XOR: use the challenge's actual data and key
data = b"example"
key = b"key"
result = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))

# Modular inverse, when e and phi are coprime
pow(65537, -1, 3120)
```

## Gotchas

- Use `read_bytes()` / `write_bytes()` for binary data.
- A Python `str` and `bytes` are different; specify encoding when converting.
- Do not use `eval()` to parse challenge input. Use `json.loads()` for JSON.
- Use [uv](../uv/) for approved dependency environments.

## Python command-line flags explained

| Flag | Meaning | Example |
| --- | --- | --- |
| `--version` | Print the interpreter version | `python3 --version` |
| `-m MODULE` | Run an installed module as a program | `python3 -m json.tool input.json` |
| `-c CODE` | Execute a short source string | `python3 -c 'print(123)'` |
| `-u` | Use unbuffered stdout/stderr | `python3 -u solve.py` for live logs |
| `-` | Read Python source from stdin | Used by heredoc examples |

In `python3 -m zipfile -l archive.zip`, `-m` belongs to Python and `-l` belongs to the zipfile module's CLI: it lists archive members. That module's `-e ARCHIVE DIR` extracts into DIR. `python3 -m venv DIR` creates an environment at the positional path DIR.

## CTF: try every single-byte XOR key

Save as `xor_one.py`. It searches raw ciphertext for a known prefix and prints the key with the candidate plaintext.

```python
from pathlib import Path

data = Path("cipher.bin").read_bytes()
for key in range(256):
    plain = bytes(byte ^ key for byte in data)
    if b"flag{" in plain.lower():
        print(f"key={key:#04x}", repr(plain))
```

For a repeating key, recover a candidate key segment with `cipher_byte ^ known_plain_byte`. Check the segment repeats across the ciphertext; one matching prefix is weak evidence.

## CTF: textbook RSA when factors are known

```python
from math import gcd

# Small worked example; replace with supplied integers
p, q, e, c = 61, 53, 17, 2790
n = p * q
phi = (p - 1) * (q - 1)
assert gcd(e, phi) == 1
d = pow(e, -1, phi)
m = pow(c, d, n)
plain = m.to_bytes(max(1, (m.bit_length() + 7) // 8), "big")
print("m:", m)                  # 65
print("bytes:", repr(plain))   # b'A'
assert pow(m, e, n) == c       # Verify by re-encrypting
```

This model assumes two distinct primes and textbook RSA. OAEP/PKCS#1 padding needs the correct decoder. A leading zero byte can matter when preserving a fixed-size encoded block.

## Encode and decode text without losing bytes

```python
text = "flag{demo}"
raw = text.encode("utf-8")             # str → bytes
restored = raw.decode("utf-8")         # bytes → str
print(raw, restored)

wide = text.encode("utf-16le")         # Explicit little endian; no automatic BOM
print(wide.hex())
print(wide.decode("utf-16le"))

all_bytes = bytes(range(256))
as_latin1 = all_bytes.decode("latin-1")
assert as_latin1.encode("latin-1") == all_bytes
```

Latin-1 provides a reversible byte-to-character mapping, not evidence that unknown bytes are actually Latin-1 text. `decode(errors="replace")` is useful for previewing, but replacement characters lose information. Keep the original bytes for further decoding/decryption.

### Literal escape text versus real bytes

```python
import codecs

escaped = r"\x66\x6c\x61\x67\x7b\x64\x65\x6d\x6f\x7d"
raw = codecs.escape_decode(escaped.encode("ascii"))[0]
print(raw)                            # b'flag{demo}'

# A JSON Unicode escape should be parsed as JSON
import json
print(json.loads(r'"\u0066\u006c\u0061\u0067"'))
```

Use escape decoding only when the challenge explicitly supplies escaped bytes. A filename with backslashes or literal `\n` text may not be an encoded byte stream. Never use `eval()` to interpret supplied source-like strings.

## Hex encode and decode

```python
raw = b"flag{demo}"
hex_text = raw.hex()                  # bytes → lowercase hex text
print(hex_text)
print(bytes.fromhex(hex_text))        # hex text → bytes
print(bytes.fromhex("66 6c 61 67"))   # Whitespace between byte pairs is accepted

# One integer value is different from a sequence of hex bytes
number = int("0x1234", 16)
print(number.to_bytes(2, "big"))      # b'\x12\x34'
```

Hex takes two characters per byte. `b"deadbeef"` is eight ASCII bytes; `bytes.fromhex("deadbeef")` is four bytes. Prefixes such as `0x` and delimiters such as commas must be handled according to the input format before `fromhex()`.

## Base64 encode and decode

```python
import base64

raw = b"flag{demo}"
encoded = base64.b64encode(raw)
print(encoded.decode("ascii"))
decoded = base64.b64decode(encoded, validate=True)
print(decoded)

# Remove only documented whitespace; validate the remaining alphabet
wrapped = b"ZmxhZ3tk\nZW1vfQ==\n"
compact = b"".join(wrapped.split())
print(base64.b64decode(compact, validate=True))
```

`validate=True` rejects unexpected characters rather than silently ignoring them. Do not remove arbitrary characters just to make a decoder accept damaged input.

### Base64URL and omitted padding

```python
import base64
import json

payload = json.dumps({"role": "user"}, separators=(",", ":")).encode()
token_part = base64.urlsafe_b64encode(payload).rstrip(b"=")

# Restore padding when the format deliberately omits it
padded = token_part + b"=" * (-len(token_part) % 4)
decoded = base64.b64decode(padded, altchars=b"-_", validate=True)
print(json.loads(decoded))
```

`altchars=b"-_"` selects the URL-safe replacements for `+` and `/`. A remainder of one character modulo four cannot represent valid ordinary Base64 data merely by adding padding. Decoding a JWT section does not validate its signature.

## Base32, Base16, Base85 and Ascii85

```python
import base64

raw = b"flag{demo}"
for name, encode, decode in [
    ("Base16", base64.b16encode, base64.b16decode),
    ("Base32", base64.b32encode, base64.b32decode),
    ("Base85", base64.b85encode, base64.b85decode),
    ("Ascii85", base64.a85encode, base64.a85decode),
]:
    encoded = encode(raw)
    print(name, encoded, decode(encoded))

# Accept lowercase letters only when that input convention is intended
print(base64.b32decode(base64.b32encode(raw).lower(), casefold=True))

# Adobe-style Ascii85 framing uses <~ ... ~>
adobe = base64.a85encode(raw, adobe=True)
print(base64.a85decode(adobe, adobe=True))
```

Base85 and Ascii85 use different alphabets. Standard-library Base85 is not a universal decoder for every format named “Base85”; Base58, Base62 and Z85 also require their particular alphabet/implementation.

## URL and HTML encode and decode

```python
import html
from urllib.parse import quote, unquote, quote_plus, unquote_plus, unquote_to_bytes

text = "flag{a+b c}"
escaped = quote(text, safe="")         # Percent-escape all non-unreserved characters
print(escaped, unquote(escaped))

form_value = quote_plus(text)         # Space becomes +; literal + becomes %2B
print(form_value, unquote_plus(form_value))

raw = unquote_to_bytes("%ff%00%41")   # Preserve bytes that are not UTF-8
print(raw.hex())

entity = html.escape("<flag>&demo")
print(entity, html.unescape(entity))
```

Use `unquote_plus()` for form-style values; it changes `+` to a space. Use `unquote()`/`unquote_to_bytes()` when a literal plus must survive. Decode one documented layer at a time: `%252f` becomes `%2f`, then `/` after a second pass.

## Binary digits, decimal bytes and integers

```python
# ASCII bytes → a bit string → bytes
raw = b"flag"
bits = "".join(f"{byte:08b}" for byte in raw)
assert len(bits) % 8 == 0
restored = bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))
print(bits, restored)

# Decimal byte list from a challenge
decimal_text = "102 108 97 103"
print(bytes(int(piece) for piece in decimal_text.split()))

# Integer-to-bytes: big endian is common in textbook RSA
number = int.from_bytes(raw, "big")
width = max(1, (number.bit_length() + 7) // 8)
print(number, number.to_bytes(width, "big"))
```

An integer does not preserve leading zero bytes. Use a known field/block length when the encoding is fixed width. Do not silently pad or drop partial bit groups without a format rule.

## ROT13, Caesar and Atbash

```python
import codecs

print(codecs.encode("flag{demo}", "rot_13"))
print(codecs.decode("synt{qrzb}", "rot_13"))

def caesar(text: str, shift: int) -> str:
    result = []
    for char in text:
        if "a" <= char <= "z":
            result.append(chr((ord(char) - ord("a") + shift) % 26 + ord("a")))
        elif "A" <= char <= "Z":
            result.append(chr((ord(char) - ord("A") + shift) % 26 + ord("A")))
        else:
            result.append(char)
    return "".join(result)

encrypted = caesar("flag{demo}", 3)
print(encrypted, caesar(encrypted, -3))
for shift in range(26):
    print(shift, caesar(encrypted, -shift))

alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
reversed_alphabet = "zyxwvutsrqponmlkjihgfedcbaZYXWVUTSRQPONMLKJIHGFEDCBA"
print("uozt{wvnl}".translate(str.maketrans(alphabet, reversed_alphabet)))
```

The Caesar helper shifts only ASCII letters and preserves punctuation. ROT13 and Atbash are self-inverse. These classical transforms are useful when the clue/alphabet supports them; they do not decrypt modern AES/RSA ciphertext.

### Vigenère: repeating keyword over letters

```python
def vigenere(text: str, keyword: str, decrypt: bool = False) -> str:
    if not keyword or any(not ("a" <= char <= "z") for char in keyword.lower()):
        raise ValueError("Keyword must contain ASCII letters only")
    shifts = [ord(char) - ord("a") for char in keyword.lower()]
    result, position = [], 0
    direction = -1 if decrypt else 1
    for char in text:
        if "a" <= char <= "z" or "A" <= char <= "Z":
            base = ord("a") if char.islower() else ord("A")
            shift = shifts[position % len(shifts)]
            result.append(chr((ord(char) - base + direction * shift) % 26 + base))
            position += 1
        else:
            result.append(char)
    return "".join(result)

encrypted = vigenere("flag{demo}", "key")
print(encrypted, vigenere(encrypted, "key", decrypt=True))
```

This convention advances the keyword only on ASCII letters. Some challenges advance it on every character or use a custom alphabet; reproduce the actual rule.

## Compress and decompress common wrappers

```python
import bz2
import gzip
import lzma
import zlib

raw = b"flag{demo}"
for name, compress, decompress in [
    ("gzip", gzip.compress, gzip.decompress),
    ("zlib", zlib.compress, zlib.decompress),
    ("bzip2", bz2.compress, bz2.decompress),
    ("xz", lzma.compress, lzma.decompress),
]:
    packed = compress(raw)
    print(name, packed[:12].hex(), decompress(packed))
```

### Raw DEFLATE is different from zlib-wrapped data

```python
import zlib

compressor = zlib.compressobj(wbits=-15)
packed = compressor.compress(b"flag{demo}") + compressor.flush()
print(zlib.decompress(packed, wbits=-15))
```

`wbits=-15` selects raw DEFLATE; ordinary zlib data normally includes its wrapper/checksum. An archive container and its compression stream are different layers. Save output as bytes before deciding that decompression “looks wrong.”

## XOR helpers with explicit length rules

```python
def xor_equal(left: bytes, right: bytes) -> bytes:
    """XOR equal-length byte strings without silently truncating."""
    if len(left) != len(right):
        raise ValueError("XOR inputs must have equal lengths")
    return bytes(a ^ b for a, b in zip(left, right))

def xor_repeat(data: bytes, key: bytes) -> bytes:
    """XOR with a repeating key; the same operation decrypts."""
    if not key:
        raise ValueError("Repeating XOR key must not be empty")
    return bytes(value ^ key[index % len(key)] for index, value in enumerate(data))

plain = b"flag{demo}"
cipher = xor_repeat(plain, b"key")
print(cipher.hex(), xor_repeat(cipher, b"key"))
```

Use these helper definitions before the following XOR snippets. Plain `zip()` truncates to the shorter input, which can hide a length error.

### XOR: recover a known plaintext keystream segment

```python
# Worked example; replace ciphertext and known bytes with challenge values
cipher = xor_repeat(b"flag{demo}", b"key")
known = b"flag{"
segment = xor_equal(cipher[:len(known)], known)
print("keystream prefix:", segment.hex(), repr(segment))
```

This recovers only the keystream bytes aligned with the known plaintext. If a repeating key is suspected, test a candidate period across the full ciphertext; the prefix alone does not reveal every possible key.

### XOR: reuse of the same stream at the same position

```python
key_stream = bytes.fromhex("00112233445566778899")
plain1, plain2 = b"flag{demo}", b"hello!!!!!"
cipher1 = xor_equal(plain1, key_stream)
cipher2 = xor_equal(plain2, key_stream)

# C1 XOR C2 = P1 XOR P2; knowing P1 recovers this part of P2
recovered = xor_equal(xor_equal(cipher1, cipher2), plain1)
print(recovered)
```

The messages must overlap at the same keystream position. Matching nonces do not suffice if keys, counters, offsets or protocols differ. This principle applies to reused XOR pads and some stream/CTR encryption mistakes; it does not directly recover the underlying cipher key.

## Hash: digest bytes versus hex text

```python
import hashlib

data = b"flag{demo}"
for name in ("md5", "sha1", "sha256", "sha512"):
    digest = hashlib.new(name, data)
    print(name, digest.hexdigest())

raw_digest = hashlib.sha256(data).digest()       # 32 bytes
hex_digest = hashlib.sha256(data).hexdigest()   # 64 hex characters
print(len(raw_digest), len(hex_digest))
```

MD5/SHA-1 appear in legacy CTFs. Hash matching requires exact input bytes, including newline, case and any salt placement. Encoding a hash as Base64/hex is not encryption and does not make it decryptable.

### Hash: compare a small supplied candidate list

```python
import hashlib

target = hashlib.sha256(b"demo").hexdigest()
for candidate in ("test", "demo", "example"):
    if hashlib.sha256(candidate.encode("utf-8")).hexdigest() == target:
        print("matching candidate:", candidate)
```

This is candidate checking, not a general reversal of SHA-256. Match any given salt/KDF before testing values.

## HMAC: create and verify a keyed digest

```python
import hashlib
import hmac

key = b"demo-hmac-key"
message = b"role=user"
tag = hmac.new(key, message, hashlib.sha256).digest()
expected_hex = tag.hex()
print(expected_hex)

candidate_tag = bytes.fromhex(expected_hex)
print(hmac.compare_digest(tag, candidate_tag))
```

HMAC uses a key and authenticates bytes; it does not encrypt them. `compare_digest()` compares equivalent representations. Do not compare raw tag bytes with their ASCII hex encoding.

## PBKDF2 and scrypt: password to key bytes

```python
import hashlib

password = "demo-password".encode("utf-8")
salt = bytes.fromhex("00112233445566778899aabbccddeeff")

# Example parameters only: reproduce the challenge's exact settings
pbkdf2_key = hashlib.pbkdf2_hmac("sha256", password, salt, 100_000, dklen=32)
scrypt_key = hashlib.scrypt(password, salt=salt, n=2**14, r=8, p=1, dklen=32)
print(pbkdf2_key.hex())
print(scrypt_key.hex())
```

| Argument | Meaning |
| --- | --- |
| `password` | Encoded password bytes, not automatically a raw AES key |
| `salt` | Salt bytes from the challenge/container |
| PBKDF2 hash and iterations | Pseudorandom function and work count |
| `dklen` | Derived output length in bytes |
| scrypt `n`, `r`, `p` | Cost parameters; required to reproduce the derived key |

Some Python/OpenSSL builds may not provide every KDF. An arbitrary KDF, salt or iteration count will not match the ciphertext just because the resulting key has a valid length.

Sources: [base encodings](https://docs.python.org/3/library/base64.html), [codecs](https://docs.python.org/3/library/codecs.html), [URL parsing](https://docs.python.org/3/library/urllib.parse.html), [compression](https://docs.python.org/3/library/archiving.html), [hashlib](https://docs.python.org/3/library/hashlib.html), [HMAC](https://docs.python.org/3/library/hmac.html).

## AES: choose the correct mode

AES always operates on 16-byte blocks internally. AES-128/192/256 describes the **key** length: 16/24/32 bytes. A 32-character hex key decodes to 16 bytes; it is not a 32-byte key.

| Mode | Inputs besides key/plaintext | Padding in these examples | CTF clue / common mistake |
| --- | --- | --- | --- |
| ECB | None | PKCS#7 for arbitrary length | Equal plaintext blocks give equal ciphertext blocks |
| CBC | 16-byte IV | PKCS#7 | IV, previous block and ciphertext alignment matter |
| CTR | Nonce and counter layout/start | None | Match nonce length, byte order and starting counter |
| CFB | 16-byte IV and segment size | None | CFB8 and CFB128 are different |
| OFB | 16-byte IV | None | Correct IV/state required |
| GCM | Nonce, authentication tag, optional AAD | None | Verify tag before using plaintext |
| EAX | Nonce, authentication tag, optional AAD | None | Similar interface does not mean compatible with GCM |

Each example creates fresh random parameters for a local round trip. **To decrypt a supplied artifact, use its actual key, mode, IV/nonce, ciphertext and other parameters. Generating new random values will not decrypt it.**

### AES-ECB: encrypt and decrypt

```python
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

key = get_random_bytes(16)             # 16 bytes selects AES-128
plain = b"flag{demo}"
ciphertext = AES.new(key, AES.MODE_ECB).encrypt(pad(plain, AES.block_size))
recovered = unpad(AES.new(key, AES.MODE_ECB).decrypt(ciphertext), AES.block_size)
print("key:", key.hex(), "ciphertext:", ciphertext.hex())
print(recovered)
```

`AES.block_size` is 16. `pad()` adds PKCS#7 padding; `unpad()` validates/removes it. If the challenge encrypts already-aligned raw blocks without padding, do not add/remove PKCS#7 automatically.

### CTF: find repeated 16-byte blocks

```python
from collections import Counter
from pathlib import Path

data = Path("cipher.bin").read_bytes()
blocks = [data[i:i + 16] for i in range(0, len(data) - 15, 16)]
print([(block.hex(), count) for block, count in Counter(blocks).items() if count > 1])
```

Repeats suggest ECB or repeated data at that alignment, but do not prove ECB. Remove known file headers before comparing the ciphertext area, and inspect different framing if the block boundary is offset.

### AES-CBC: encrypt and decrypt

```python
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

key = get_random_bytes(32)             # 32 bytes selects AES-256
iv = get_random_bytes(16)              # CBC IV remains 16 bytes
plain = b"flag{demo}"
ciphertext = AES.new(key, AES.MODE_CBC, iv=iv).encrypt(pad(plain, 16))

decrypted_blocks = AES.new(key, AES.MODE_CBC, iv=iv).decrypt(ciphertext)
recovered = unpad(decrypted_blocks, 16)
print("key:", key.hex(), "iv:", iv.hex(), "ct:", ciphertext.hex())
print(recovered)
```

CBC decryption follows `P[i] = AES_decrypt(C[i]) XOR previous_block`, where the previous block for `P[0]` is the IV. A wrong IV changes the first plaintext block; damaged ciphertext can affect more than one block. A padding error can also mean a wrong key, mode, length or padding convention.

### CTF: decrypt an IV-prefixed CBC file

```python
from pathlib import Path
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

# Example key only: replace with the challenge key
key = bytes.fromhex("00112233445566778899aabbccddeeff")
blob = Path("iv_then_ciphertext.bin").read_bytes()
iv, ciphertext = blob[:16], blob[16:]
if len(iv) != 16 or not ciphertext or len(ciphertext) % 16:
    raise ValueError("Not the expected IV + aligned CBC ciphertext layout")
plain = unpad(AES.new(key, AES.MODE_CBC, iv=iv).decrypt(ciphertext), 16)
Path("plain.bin").write_bytes(plain)
print(repr(plain[:200]))
```

This parser applies only when the container is documented as `16-byte IV || CBC ciphertext`. A salt, length field or tag changes where bytes must be split.

### AES-CTR: nonce and starting counter

```python
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

key = get_random_bytes(16)
nonce = get_random_bytes(8)
start = 1
plain = b"flag{demo}"
ciphertext = AES.new(key, AES.MODE_CTR, nonce=nonce, initial_value=start).encrypt(plain)
recovered = AES.new(key, AES.MODE_CTR, nonce=nonce, initial_value=start).decrypt(ciphertext)
print("key:", key.hex(), "nonce:", nonce.hex(), "counter:", start)
print(ciphertext.hex(), recovered)
```

For this layout, the 16-byte counter block contains an 8-byte nonce followed by an 8-byte big-endian counter. `initial_value` sets that counter's initial integer. Other protocols use other layouts. Use `Crypto.Util.Counter.new()` if a specified format requires a little-endian counter or a prefix/suffix.

### AES-CFB and OFB: no PKCS#7 padding

```python
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

key, iv = get_random_bytes(16), get_random_bytes(16)
plain = b"flag{demo}"

# Match segment_size to the challenge; PyCryptodome defaults to 8 bits
ct_cfb = AES.new(key, AES.MODE_CFB, iv=iv, segment_size=128).encrypt(plain)
pt_cfb = AES.new(key, AES.MODE_CFB, iv=iv, segment_size=128).decrypt(ct_cfb)
print("CFB128:", ct_cfb.hex(), pt_cfb)

# Use a separate IV for the separate encryption example
iv_ofb = get_random_bytes(16)
ct_ofb = AES.new(key, AES.MODE_OFB, iv=iv_ofb).encrypt(plain)
pt_ofb = AES.new(key, AES.MODE_OFB, iv=iv_ofb).decrypt(ct_ofb)
print("OFB:", ct_ofb.hex(), pt_ofb)
```

`segment_size=128` is measured in **bits**, not bytes. CFB8 ciphertext will not correctly decrypt with CFB128 even with the same key and IV.

### AES-GCM: authenticated encrypt and decrypt

```python
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

key = get_random_bytes(32)
nonce = get_random_bytes(12)           # Explicit 12-byte nonce for this format
aad = b"challenge-header"             # Authenticated, but not encrypted
plain = b"flag{demo}"

encryptor = AES.new(key, AES.MODE_GCM, nonce=nonce, mac_len=16)
encryptor.update(aad)
ciphertext, tag = encryptor.encrypt_and_digest(plain)

decryptor = AES.new(key, AES.MODE_GCM, nonce=nonce, mac_len=16)
decryptor.update(aad)
recovered = decryptor.decrypt_and_verify(ciphertext, tag)
print("nonce:", nonce.hex(), "ct:", ciphertext.hex(), "tag:", tag.hex())
print(recovered)
```

`update(aad)` supplies exactly the bytes authenticated as associated data. `mac_len=16` requests a 16-byte tag. A tag failure can reflect a wrong key, nonce, ciphertext, tag, AAD or container split. Do not print/use unauthenticated plaintext as a successful result.

### AES-EAX: authenticated encrypt and decrypt

```python
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

key, nonce = get_random_bytes(16), get_random_bytes(16)
aad, plain = b"header", b"flag{demo}"
encryptor = AES.new(key, AES.MODE_EAX, nonce=nonce)
encryptor.update(aad)
ciphertext, tag = encryptor.encrypt_and_digest(plain)

decryptor = AES.new(key, AES.MODE_EAX, nonce=nonce)
decryptor.update(aad)
print(decryptor.decrypt_and_verify(ciphertext, tag))
```

EAX and GCM have similar method names but are different constructions. Select the mode from the encryption source/protocol rather than trying a different mode until text happens to appear.

### Crypto arguments explained

| Argument / method | Meaning |
| --- | --- |
| `key` | Raw secret bytes, after any specified decoding/KDF |
| `iv` | Mode-specific initialization bytes; CBC/CFB/OFB use 16 bytes for AES |
| `nonce` | Per-message value used by CTR/GCM/EAX or a stream cipher |
| `initial_value` | Starting CTR counter integer |
| `segment_size` | CFB feedback size, measured in bits |
| `mac_len` | Requested authentication-tag length in bytes |
| `update(aad)` | Supply additional authenticated data, unchanged on both sides |
| `encrypt_and_digest()` | Return ciphertext plus authentication tag |
| `decrypt_and_verify()` | Decrypt and reject a mismatched tag |
| `pad(data, 16)` | Add PKCS#7 block padding by default |
| `unpad(data, 16)` | Validate/remove that padding |

Raw hex text, UTF-8 password bytes and KDF output are different key representations. For new encryption, use fresh IVs/nonces according to the mode's rules; reusing a stream/CTR/GCM nonce with the same key can break security.

Sources: [AES API](https://www.pycryptodome.org/src/cipher/aes), [classic modes](https://www.pycryptodome.org/src/cipher/classic), [authenticated modes](https://www.pycryptodome.org/src/cipher/modern), [padding and counter utilities](https://www.pycryptodome.org/src/util/util).

## ChaCha20: encrypt and decrypt

```python
from Crypto.Cipher import ChaCha20
from Crypto.Random import get_random_bytes

key = get_random_bytes(32)             # ChaCha20 key: 32 bytes
nonce = get_random_bytes(12)           # IETF-size nonce for this example
plain = b"flag{demo}"
ciphertext = ChaCha20.new(key=key, nonce=nonce).encrypt(plain)
recovered = ChaCha20.new(key=key, nonce=nonce).decrypt(ciphertext)
print("key:", key.hex(), "nonce:", nonce.hex(), "ct:", ciphertext.hex())
print(recovered)
```

ChaCha20 is a stream cipher: no PKCS#7 padding and no built-in authentication tag. Encryption and decryption consume the same keystream bytes, so create a fresh cipher object at the same starting position for the other direction.

### ChaCha nonce variants and counter position

| Variant in PyCryptodome | Nonce length | Required distinction |
| --- | --- | --- |
| Original ChaCha20 | 8 bytes | Different layout from the IETF variant |
| IETF ChaCha20 | 12 bytes | Counter/offset must match the protocol |
| XChaCha20 | 24 bytes | Extended nonce construction |

The raw cipher's `seek(N)` positions the keystream at **byte** offset N. A ChaCha block is 64 bytes; a protocol starting at block counter 1 requires position 64 relative to the zero-based raw stream.

```python
from Crypto.Cipher import ChaCha20
from Crypto.Random import get_random_bytes

key, nonce = get_random_bytes(32), get_random_bytes(12)
offset = 64                           # Byte offset, not block number
encryptor = ChaCha20.new(key=key, nonce=nonce)
encryptor.seek(offset)
ciphertext = encryptor.encrypt(b"flag{demo}")

decryptor = ChaCha20.new(key=key, nonce=nonce)
decryptor.seek(offset)
print(decryptor.decrypt(ciphertext))
```

Do not add this offset unless the challenge specifies that stream position. Library APIs can package counters/nonces differently; porting only the visible nonce bytes can still produce the wrong stream.

### XChaCha20 example

```python
from Crypto.Cipher import ChaCha20
from Crypto.Random import get_random_bytes

key, nonce = get_random_bytes(32), get_random_bytes(24)
ciphertext = ChaCha20.new(key=key, nonce=nonce).encrypt(b"flag{demo}")
print(ChaCha20.new(key=key, nonce=nonce).decrypt(ciphertext))
```

## ChaCha20-Poly1305: authenticated encryption

```python
from Crypto.Cipher import ChaCha20_Poly1305
from Crypto.Random import get_random_bytes

key, nonce = get_random_bytes(32), get_random_bytes(12)
aad, plain = b"challenge-header", b"flag{demo}"

encryptor = ChaCha20_Poly1305.new(key=key, nonce=nonce)
encryptor.update(aad)
ciphertext, tag = encryptor.encrypt_and_digest(plain)

decryptor = ChaCha20_Poly1305.new(key=key, nonce=nonce)
decryptor.update(aad)
recovered = decryptor.decrypt_and_verify(ciphertext, tag)
print("nonce:", nonce.hex(), "ct:", ciphertext.hex(), "tag:", tag.hex())
print(recovered)
```

Poly1305 adds authentication; the tag is 16 bytes for this API. This is not equivalent to running raw ChaCha20 from its default position and ignoring the tag. For XChaCha20-Poly1305, the API also supports a 24-byte nonce; the supplied challenge/library version must agree.

Sources: [ChaCha20/XChaCha20 and seek](https://www.pycryptodome.org/src/cipher/chacha20), [ChaCha20-Poly1305](https://www.pycryptodome.org/src/cipher/chacha20_poly1305).

## Salsa20, RC4 and 3DES in legacy CTFs

### Salsa20: 8-byte nonce

```python
from Crypto.Cipher import Salsa20
from Crypto.Random import get_random_bytes

key, nonce = get_random_bytes(32), get_random_bytes(8)
ciphertext = Salsa20.new(key=key, nonce=nonce).encrypt(b"flag{demo}")
print(Salsa20.new(key=key, nonce=nonce).decrypt(ciphertext))
```

Salsa20 and ChaCha20 are distinct ciphers; do not exchange their names just because both use XOR keystreams.

### RC4 / ARC4: match the dropped keystream prefix

```python
from Crypto.Cipher import ARC4
from Crypto.Random import get_random_bytes

key = get_random_bytes(16)
drop = 3072                          # Example only; challenge may use 0 or another value
ciphertext = ARC4.new(key, drop=drop).encrypt(b"flag{demo}")
print(ARC4.new(key, drop=drop).decrypt(ciphertext))
```

`drop` skips that many initial keystream **bytes**. A wrong drop count gives the wrong plaintext. RC4 is a legacy/weak cipher; use it here to reproduce a challenge's actual construction.

### 3DES-CBC: 8-byte blocks and IV

```python
from Crypto.Cipher import DES3
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

# Reproducible demonstration key with distinct DES components, not a real secret
key = DES3.adjust_key_parity(bytes.fromhex(
    "0123456789abcdeffedcba987654321089abcdef01234567"
))
iv = get_random_bytes(8)
ciphertext = DES3.new(key, DES3.MODE_CBC, iv=iv).encrypt(pad(b"flag{demo}", 8))
plain = unpad(DES3.new(key, DES3.MODE_CBC, iv=iv).decrypt(ciphertext), 8)
print(plain)
```

3DES has 8-byte blocks, unlike AES's 16-byte blocks. Accepted key sizes and parity rules are cipher-specific. These legacy recipes are for matching supplied CTF artifacts, not choosing a new encryption design.

Sources: [Salsa20](https://www.pycryptodome.org/src/cipher/salsa20), [ARC4](https://www.pycryptodome.org/src/cipher/arc4), [Triple DES](https://www.pycryptodome.org/src/cipher/des3).

## RSA-OAEP: encrypt and decrypt

```python
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA

private_key = RSA.generate(2048)       # Demonstration; not an attack on an existing key
public_key = private_key.public_key()
plain = b"flag{demo}"

encryptor = PKCS1_OAEP.new(public_key, hashAlgo=SHA256)
ciphertext = encryptor.encrypt(plain)
decryptor = PKCS1_OAEP.new(private_key, hashAlgo=SHA256)
print(decryptor.decrypt(ciphertext))
```

`hashAlgo=SHA256` chooses OAEP's hash. The `PKCS1_OAEP` compatibility API defaults to SHA-1 when omitted; newer builds also expose `Crypto.Cipher.oaep.new(key, hashmod=SHA256)`, which requires an explicit hash. The examples use the compatible `PKCS1_OAEP` interface with its hash stated explicitly.

The hash, MGF settings and optional label must match the original encryption. OAEP limits the plaintext size; a 2048-bit RSA key with SHA-256 accepts at most 190 message bytes.

### RSA-OAEP: use a supplied private key and ciphertext

```python
from pathlib import Path
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA

key = RSA.import_key(Path("private.pem").read_bytes())
ciphertext = Path("ciphertext.bin").read_bytes()
plain = PKCS1_OAEP.new(key, hashAlgo=SHA256).decrypt(ciphertext)
Path("plain.bin").write_bytes(plain)
print(repr(plain))
```

An encrypted PEM needs its supplied passphrase via `RSA.import_key(..., passphrase=...)`. A public key alone normally cannot decrypt OAEP ciphertext. For numeric `n/e/c` and leaked factors, use the textbook RSA recipe earlier on this page; do not apply OAEP unpadding to textbook ciphertext without evidence.

### RSA PKCS#1 v1.5: legacy padded encryption

```python
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes

key = RSA.generate(2048)
ciphertext = PKCS1_v1_5.new(key.public_key()).encrypt(b"flag{demo}")
sentinel = get_random_bytes(32)         # Returned if this API rejects the padding
plain = PKCS1_v1_5.new(key).decrypt(ciphertext, sentinel)
if plain == sentinel:
    raise ValueError("PKCS#1 v1.5 decryption failed")
print(plain)
```

This is encryption padding, not the similarly named signature scheme. OAEP, PKCS#1 v1.5 and textbook RSA are different encodings of the RSA message integer.

### RSA: shared prime from two public keys

```python
from math import gcd

n1, n2, e, c = 3233, 2867, 17, 2790  # Worked values only
p = gcd(n1, n2)
if not 1 < p < n1:
    raise ValueError("No useful partial factor from this pair")
q = n1 // p
d = pow(e, -1, (p - 1) * (q - 1))
m = pow(c, d, n1)
assert pow(m, e, n1) == c
print(m.to_bytes(max(1, (m.bit_length() + 7) // 8), "big"))
```

### RSA: small public exponent without modular wrap

```python
def integer_root(value: int, exponent: int) -> tuple[int, bool]:
    """Return floor(value ** (1/exponent)) and whether it is exact."""
    if value < 0 or exponent < 1:
        raise ValueError("Expected a nonnegative value and positive exponent")
    low, high = 0, 1 << ((value.bit_length() + exponent - 1) // exponent)
    while low < high:
        middle = (low + high + 1) // 2
        if middle ** exponent <= value:
            low = middle
        else:
            high = middle - 1
    return low, low ** exponent == value

m = int.from_bytes(b"flag", "big")
c = m ** 3                           # Constructed example: no modular reduction
root, exact = integer_root(c, 3)
if exact:
    print(root.to_bytes(max(1, (root.bit_length() + 7) // 8), "big"))
```

For real RSA, verify `m**e < n` or otherwise justify the no-wrap assumption. A small exponent alone is insufficient, and floating-point cube roots lose precision on large integers. For other weaknesses and attack selection see [RsaCtfTool](../rsactftool/).

Sources: [RSA keys](https://www.pycryptodome.org/src/public_key/rsa), [OAEP](https://www.pycryptodome.org/src/cipher/oaep), [PKCS1_OAEP compatibility API](https://github.com/Legrandin/pycryptodome/blob/master/lib/Crypto/Cipher/PKCS1_OAEP.py), [PKCS#1 v1.5 encryption](https://www.pycryptodome.org/src/cipher/pkcs1_v1_5).

## Save a ciphertext with its required metadata

```python
import base64
import json
from pathlib import Path
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

key, nonce = get_random_bytes(32), get_random_bytes(12)
aad = b"demo-header"
encryptor = AES.new(key, AES.MODE_GCM, nonce=nonce)
encryptor.update(aad)
ciphertext, tag = encryptor.encrypt_and_digest(b"flag{demo}")

def encode(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")

record = {"algorithm": "AES-256-GCM", "encoding": "base64",
          "nonce": encode(nonce), "aad": encode(aad),
          "ciphertext": encode(ciphertext), "tag": encode(tag)}
Path("encrypted.json").write_text(json.dumps(record, indent=2), encoding="utf-8")

# Local round-trip example: key remains in this process; store/manage it separately
loaded = json.loads(Path("encrypted.json").read_text(encoding="utf-8"))
def decode(field: str) -> bytes:
    return base64.b64decode(loaded[field], validate=True)

decryptor = AES.new(key, AES.MODE_GCM, nonce=decode("nonce"))
decryptor.update(decode("aad"))
print(decryptor.decrypt_and_verify(decode("ciphertext"), decode("tag")))
```

For an unknown challenge format, first identify which bytes/fields represent metadata. Do not assume a universal `nonce || ciphertext || tag` order or that a JSON key named `iv` has the length your chosen mode expects.

## Crypto troubleshooting by symptom

| Symptom | Inspect before changing the algorithm |
| --- | --- |
| Incorrect AES key length | Hex/Base64 decoding, password versus KDF output |
| CBC data not block aligned | Input wrapper, truncated file, IV/header split |
| PKCS#7 padding error | Key, IV, mode, ciphertext completeness and padding convention |
| CTR/ChaCha gives random-looking bytes | Key/nonce/counter layout and stream offset |
| GCM/EAX/Poly1305 tag failure | All authenticated inputs, tag bytes/length and AAD |
| RSA OAEP decryption error | Private key, ciphertext width, hash/MGF/label and padding type |
| Plausible prefix but broken remainder | Key period, offset, partial corruption or false positive |
| UnicodeDecodeError after decrypting | Plaintext may be binary or use another encoding |
| Correct result only with errors ignored | Original bytes may have been corrupted or misinterpreted |

Keep intermediate values in hex and record their byte lengths. A successful authenticated verification or exact mathematical reconstruction is stronger evidence than a few readable characters.

## CTF: parse a binary record without guessing endianness

```python
import struct

record = bytes.fromhex("341278563412")
kind, value = struct.unpack("<HI", record)
print(hex(kind), hex(value))  # 0x1234 0x12345678
```

`<` = little endian, `>` = big endian, `H` = unsigned 16-bit, `I` = unsigned 32-bit. Use `struct.calcsize()` before reading records. Check a real sample against the documented protocol.

## CTF: make an authenticated HTTP request

Standard library example; replace the URL, cookie and body with values captured from your challenge.

```python
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError

body = json.dumps({"id": 7}).encode()
req = Request(
    "http://192.0.2.10:8080/api/item",
    data=body,
    headers={"Content-Type": "application/json", "Cookie": "session=REPLACE"},
    method="POST",
)
try:
    with urlopen(req, timeout=10) as response:
        print(response.status, response.read().decode(errors="replace"))
except HTTPError as error:
    print(error.code, error.read().decode(errors="replace"))
```

A `403` body is useful evidence; do not discard it. Change one request field at a time and preserve the original request.

## CTF: receive a stateful TCP response

This passive reader connects and saves received bytes. Replace the endpoint. Send protocol messages only after decoding the protocol and required setup actions.

```python
from pathlib import Path
import socket
import time

received = bytearray()
deadline = time.monotonic() + 30
with socket.create_connection(("192.0.2.10", 31337), timeout=5) as sock:
    sock.settimeout(2)
    while time.monotonic() < deadline:
        try:
            chunk = sock.recv(65536)
        except socket.timeout:
            print("receive timeout; connection may still be open")
            continue
        if chunk == b"":
            print("peer closed connection (EOF)")
            break
        received.extend(chunk)
        print(repr(chunk), flush=True)
Path("session.bin").write_bytes(received)
```

TCP reads are not message boundaries. Buffer data until a delimiter or documented length is complete. For interactive challenges, keep the same socket for setup, commands and asynchronous success messages.

## Handle common solver failures

| Symptom | Inspect next |
| --- | --- |
| UnicodeDecodeError | Keep bytes; identify encoding before decoding |
| Incorrect padding in Base64 | Check alphabet, truncation and expected padding |
| Wrong integer/plaintext | Confirm hex vs decimal and byte order |
| ModuleNotFoundError | Check the active interpreter and environment |
| ConnectionRefusedError | Endpoint/port availability |
| Timeout after receiving a banner | Required prompt, newline or protocol state |
| EOF | Peer closed; preserve all bytes received before closure |

References: [Python standard library](https://docs.python.org/3/library/index.html), [socket](https://docs.python.org/3/library/socket.html), [struct](https://docs.python.org/3/library/struct.html), [urllib.request](https://docs.python.org/3/library/urllib.request.html).

## Related playbooks

- [Offline Python snippet library](../../tools-cheatsheet/python-library/)
