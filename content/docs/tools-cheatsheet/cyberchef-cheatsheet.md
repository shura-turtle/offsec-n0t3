---
title: "CyberChef · Visual Recipes"
weight: 1
bookToc: true
---

# CyberChef Visual Cheatsheet

**Input bytes → ordered recipe → inspect output → save exact bytes.** Start with one transformation suggested by the data. Magic is a hypothesis generator, not proof of a correct decode.

[Existing CyberChef tool note](../../ajcbbc_allow_tools/cyberchef/) · [Official app](https://gchq.github.io/CyberChef/) · [Official project / offline release](https://github.com/gchq/CyberChef).

## 1. Know the four panels

![Real CyberChef screenshot: From Base64 transforms ZmxhZ3tkZW1vfQ== into flag{demo}](/images/tools/cyberchef-base64.png)

*Actual browser screenshot captured during this update, using only synthetic demo input. UI layout may differ on the tournament's installed build.*

| Area | What to do | What to watch |
| --- | --- | --- |
| Operations, left | Search operation name, drag it into Recipe | Similar names can mean different formats |
| Recipe, middle | Arrange operations top to bottom | Each operation consumes the previous output |
| Input, top right | Paste text or load a file | Raw file bytes differ from text spelling of hex |
| Output, bottom right | Inspect text/hex, download output | Copying binary as text may alter bytes |

Use **Step** to inspect one stage at a time. Disable/enable a recipe operation to locate where data stops making sense. Save the recipe before trying a different hypothesis.

## 2. Choose the first operation

| Input clue | First operation | Control / verification |
| --- | --- | --- |
| Even count of hex digits, optional separators | From Hex | Re-encode with To Hex; compare bytes |
| Base64 alphabet, possible `=` padding | From Base64 | Valid bytes / expected file signature, not alphabet alone |
| `-` / `_` in JWT sections | From Base64, URL-safe alphabet | Header/payload should parse as JSON |
| `%xx` | URL Decode | Identify percent encoding vs form `+` rules |
| `&#...;`, `&lt;` | From HTML Entity | Check resulting browser/text context |
| `01000110...` | From Binary | Confirm grouping and bit order |
| Decimal byte values | From Decimal | Confirm separator and 0–255 byte interpretation |
| Letter-only substitution clue | ROT13 / ROT47 as appropriate | Coherent full output, not one matching word |
| Repeating XOR clue | XOR / XOR Brute Force | Correct key encoding and known prefix |
| Decoded `1f 8b` | Gunzip | Complete decompression with valid output |
| Decoded zlib wrapper | Zlib Inflate | Correct wrapper and full output |
| Raw DEFLATE bytes | Raw Inflate | No gzip/zlib header expected |

## 3. Base64, hex, and multiple layers

### One Base64 layer

```text
Input: ZmxhZ3tkZW1vfQ==
Recipe: From Base64
Output: flag{demo}
```

### One hex layer

```text
Input: 666c61677b64656d6f7d
Recipe: From Hex
Output: flag{demo}
```

### Two hex layers

```text
Input: 3636366336313637376236343635366436663764
Recipe:
  From Hex
  From Hex
Output: flag{demo}
```

At the intermediate stage the output is the ASCII text `666c61677b64656d6f7d`. It is not already the decoded flag bytes. This distinction matters when chaining AES, XOR, and decompression.

### Reproducible Python control

```python
import base64

assert base64.b64decode('ZmxhZ3tkZW1vfQ==') == b'flag{demo}'
layered = '3636366336313637376236343635366436663764'
assert bytes.fromhex(bytes.fromhex(layered).decode()) == b'flag{demo}'
```

## 4. XOR: specify bytes, not appearances

```text
Input: 242e23253926272f2d3f
Recipe:
  From Hex
  XOR
    Key format: Hex
    Key: 42
Output: flag{demo}
```

`42` in Hex mode is one byte `0x42`. `42` in UTF-8 mode is two bytes `0x34 0x32`. A key of `ICE` in UTF-8 mode is the same bytes as `494345` in Hex mode.

For repeating-key XOR:

```text
known plaintext prefix + ciphertext prefix
  → XOR the two byte sequences
  → candidate key bytes
  → test candidate repetition against whole ciphertext
```

For single-byte XOR, **XOR Brute Force** enumerates a one-byte keyspace. It does not solve an arbitrary AES key or a long repeating XOR key. Score full structure and save the actual key, not just the most readable preview.

## 5. Compression: identify the wrapper

```text
Base64 text → From Base64 → inspect magic → Gunzip / Zlib Inflate / Raw Inflate
Hex text    → From Hex    → inspect magic → correct decompressor
```

Do not feed ASCII hex into a decompressor. `1f 8b` is a gzip clue; zlib headers include common `78 01`, `78 9c`, `78 da` combinations but header validation is stronger than matching two bytes. A ZIP container needs archive extraction, not simply Gunzip.

If decompression fails, verify whether the stream is truncated, begins at a nonzero offset, has a password/container layer, or is not compressed at all. Keep binary output as a download.

## 6. AES: a parameter checklist

| Parameter | What you need |
| --- | --- |
| Key | Actual bytes or an explicitly specified KDF/password derivation |
| Mode | ECB, CBC, CTR, GCM, etc.; modes are not interchangeable |
| IV / nonce | Correct length and bytes for that mode |
| Ciphertext representation | Raw / Hex / Base64 |
| Padding | PKCS#7, none, or another specified scheme |
| GCM tag / AAD | Required authenticated inputs where applicable |
| Output representation | Raw bytes first, then display as needed |

Example workflow when the challenge explicitly supplies a CBC key and IV:

```text
From Base64               # if ciphertext input is Base64 text
AES Decrypt
  Key: actual key, with correct Hex/UTF8 representation
  IV: actual IV, with correct representation
  Mode: CBC
  Input: Raw (because From Base64 already decoded it)
  Padding: the challenge's actual padding
```

AES-128/192/256 keys have 16/24/32 bytes. A 32-character hex string encodes **16 bytes**. CBC has a 16-byte IV. A readable first block does not prove the whole decrypt is correct; check all plaintext, padding and any authentication tag.

CyberChef versions expose crypto parameters differently. If the needed mode/tag/derivation is not supported in your build, use the event-permitted [Python cookbook](../../ajcbbc_allow_tools/python3/#cookbook-map) and exact parameters rather than substituting a different mode.

## 7. JWT inspection

1. Preserve the full token.
2. Split its three JWS sections at `.`.
3. Decode the first and second with Base64URL alphabet and compatible padding.
4. Parse JSON and read `alg`, `kid`, `sub`, role, audience, issuer, and time claims.
5. Do not modify/re-sign until the application's verification behavior is understood.

A five-part encrypted token is a different structure. Decoding a token is not signature verification. Continue with [JWT testing](../../web-expl/jwt/).

## 8. Per-line transforms with Fork

```text
Input:
ZmxhZw==
e2RlbW99

Recipe:
  Fork (split by newline)
    From Base64
```

Expected decoded lines: `flag` and `{demo}`. Keep each original record boundary unless the challenge says to concatenate. Applying one decoder to a concatenation of separately padded Base64 strings can discard or misinterpret later records.

## 9. Regex and extraction

Use **Regular expression** to extract an evidence-supported format, for example:

```regex
flag\{[^}\r\n]+\}
```

The event's actual flag prefix may differ. Regex over binary may hide NULs or line-ending details. For a PCAP stream, first reconstruct the correct stream and direction with [TShark](../../ajcbbc_allow_tools/tshark/), then transform the extracted application data.

## 10. Save a reproducible recipe

- Save/export the recipe and record input format, key format, mode, and intermediate result.
- A deep link may embed the entire input and recipe in the URL. Avoid sharing live tokens/keys in links; use the synthetic sample when taking screenshots.
- Download CyberChef's offline release before the event if permitted. Verify the downloaded package opens without network access; a bookmarked online tab alone is not an offline copy.
- Preserve binary output using the download button. Confirm its hash/length in Python, HxD, or xxd.

## Troubleshooting

| Wrong output | Check next |
| --- | --- |
| Decoder error | Alphabet, omitted padding, truncation, copy artifacts |
| Coherent prefix, wrong suffix | Incorrect key length/alignment, partial bytes, wrong mode |
| AES padding error | Key/IV bytes, CBC mode, full ciphertext, real padding |
| Decompression error | Wrapper, start offset, complete stream |
| Output looks like another encoding | Inspect then add one justified stage |
| Magic offers many candidates | Validate clue, signature, full message and round-trip |
| Download differs from copied text | Binary/text conversion; use exact download bytes |

References: [official CyberChef getting started](https://github.com/gchq/CyberChef/wiki/Getting-started), [official operation source](https://github.com/gchq/CyberChef/tree/master/src/core/operations).
