---
title: "CyberChef"
weight: 1
bookToc: true
---

**Use for:** decoding, XOR, compression, hashes, quick crypto experiments.  
**Run in:** Chrome → [CyberChef](https://gchq.github.io/CyberChef/). Browser tool; no install.

## Quick start

1. Paste text into **Input**, or open a file with the input file button.
2. Search operations on the left and drag them into **Recipe**.
3. Read **Output**. Operations run from top to bottom.
4. Use the output download button for binary results.

## Recipes to remember

| Input clue | Recipe to try |
| --- | --- |
| Base64 text | From Base64 |
| Hex byte pairs | From Hex |
| `%7B`, `%2F` | URL Decode |
| `&#...;` or `&lt;` | From HTML Entity |
| Binary digits | From Binary |
| ROT13 clue | ROT13 |
| One byte XOR | XOR Brute Force |
| Known XOR key | XOR → set key format correctly |
| Compressed Base64 | From Base64 → Gunzip |
| Unknown encoding | Magic → inspect suggestions |

## Walkthrough: two encoding layers

```text
Input: 3636366336313637376236343635366436663764
Recipe:
  From Hex
  From Hex
Output: flag{demo}
```

For AES, select the stated mode, key encoding, IV encoding, input format and padding. A hex key must be interpreted as hex bytes.

## Gotchas

- Magic gives candidates; verify against the challenge format.
- Keep the original input and save the recipe so the steps are repeatable.
- Text copied from a binary output can lose bytes; download the result instead.

## CTF: choose a transform from the evidence

| Observation | Experiment | What confirms it |
| --- | --- | --- |
| Alphabet ends with `=` | From Base64 | Structured bytes/text after decoding |
| Only hex digits, even length | From Hex | Recognizable signature or coherent text |
| Many `%xx` escapes | URL Decode | A URL/query/string with valid syntax |
| Base64URL token sections | From Base64 using URL-safe alphabet | JSON header/payload for a JWT |
| Random-looking short bytes | XOR with known key / XOR Brute Force | Matching prefix plus meaningful remainder |
| `1F 8B` after decoding | Gunzip | Complete decompressed data |
| `78 9C` or `78 DA` clue | Zlib Inflate | Successful decompression and valid output |

These are hypotheses. For example, many ordinary strings fit the Base64 alphabet.

## CTF: decode a JWT without validating it

1. Split the token into its dot-separated sections.
2. Take the header or payload section.
3. Use **From Base64** with the URL-safe alphabet; handle omitted padding if required.
4. Inspect the JSON, including algorithm, expiry, role and identifiers.
5. Preserve the full original token for request reproduction.

Decoding a payload does not verify its signature or prove the server accepts changes.

## CTF: decrypt AES from explicit parameters

```text
Input: the challenge ciphertext
Recipe:
  From Base64                 # only when input is Base64 text
  AES Decrypt
    Key: supplied value, correct Hex/UTF8/Base64 representation
    IV: supplied value, correct representation
    Mode: CBC/CTR/etc. as specified
    Input: Raw after From Base64
    Output: Raw
```

AES-128 uses a 16-byte key; AES-256 uses 32 bytes. A 32-character hex string represents 16 bytes. CBC’s IV is 16 bytes. Password-derived keys require reproducing the given KDF rather than typing the password into a raw key field.

## CTF: repeating-key XOR

1. Load ciphertext as bytes, using **From Hex** or **From Base64** if needed.
2. Add **XOR** and enter the key in its actual format.
3. Inspect output as both text and hex.
4. Check the entire message or embedded file structure.

For a one-byte key, **XOR Brute Force** gives candidates. For a known plaintext prefix, use Python to calculate candidate key bytes and test repetition.

## Process many encoded lines

Use **Fork** around a per-line recipe when each input line is independent. Keep a small known example first. Applying a single Base64 decoder to several concatenated values can silently change boundaries.

## Recover binary output correctly

If output starts with `PK`, PNG magic or another file signature, download it as a file. Check the resulting bytes in xxd/HxD. Copy/pasting through a text field can alter NULs, line endings or encoding.

## When the output looks wrong

| Symptom | Likely next check |
| --- | --- |
| Readable prefix, broken remainder | Wrong XOR key length or truncation |
| AES error | Key/IV representation, mode, length or padding |
| Empty decompression | Wrong wrapper: gzip vs zlib vs raw DEFLATE |
| Unexpected extra layer | Continue one transformation at a time |
| Plausible but meaningless result | Check original clue; avoid unbounded random recipes |

Save the recipe and record which inputs are text versus raw bytes at each step.

Reference: [official project and usage](https://github.com/gchq/CyberChef).
