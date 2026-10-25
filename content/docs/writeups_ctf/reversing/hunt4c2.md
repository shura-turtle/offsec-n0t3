---
title: "Hunt 4 the C2"
date: 2026-10-26T01:53:00+06:30
bookToc: true
description: "Recover a Google Calendar C2 message from a memory dump and decode its AES key and IV."
---

# Hunt 4 the C2

## Original illustrated walkthrough

The pages below reproduce the supplied PDF in order, including every screenshot and code image. Select a page to open it at full size. [Download the original PDF](/writeups_ctf/reversing/hunt4c2/source.pdf).

### Page 1: Challenge setup, encoded AES values, and calendar event

[![hunt4c2 PDF page 1: Challenge setup, encoded AES values, and calendar event](/writeups_ctf/reversing/hunt4c2/page-1.jpg)](/writeups_ctf/reversing/hunt4c2/page-1.jpg)

### Page 2: Decoded key, IV, and decrypted message

[![hunt4c2 PDF page 2: Decoded key, IV, and decrypted message](/writeups_ctf/reversing/hunt4c2/page-2.jpg)](/writeups_ctf/reversing/hunt4c2/page-2.jpg)

## Searchable solve steps

The challenge supplies a process dump of a remote shell. The shell encrypts a message and stores it in a Google Calendar event dated **18 October 2025**. This PDF names the account, encoded key material, and final plaintext, but does not include the event ciphertext or the memory dump. A [separate detailed dump analysis](/docs/windows_rev/dmp_hunt4c2/) in these notes documents the memory and decryption workflow.

## 1. Locate the encrypted event

Inspect the dump for the remote-shell implementation, its Google Calendar account, and crypto fields. The PDF identifies the account as `schmit.19800206@gmail.com`. Its stated objective is the message sent to C2 through the calendar event. The full ciphertext must come from that event or the captured dump; it is not printed in this PDF.

## 2. Decode the AES parameters

The PDF gives a repeating XOR key, `simplekey`, and two hex strings:

```text
key: 1002284436093a572e2b19343d0227392b3e25272228363d26320d3e33283916
iv:  173c02430e092a121c3520172939025a3c1210100e215158
```

XOR each decoded hex byte with the corresponding repeating `simplekey` byte, then Base64-decode the result. The intermediate Base64 strings are `ckE4ZlQ2WXpYMnBRNGVNOXZXMWtMZEIz` and `dUo3blAweFIzYUg1YkcycQ==`. This locally checked script reproduces the parameters:

```python
import base64

xor_key = b"simplekey"

def decode(value: str) -> bytes:
    data = bytes.fromhex(value)
    encoded = bytes(byte ^ xor_key[i % len(xor_key)] for i, byte in enumerate(data))
    return base64.b64decode(encoded)

key = decode("1002284436093a572e2b19343d0227392b3e25272228363d26320d3e33283916")
iv = decode("173c02430e092a121c3520172939025a3c1210100e215158")
print(key.decode(), iv.decode())
```

```text
rA8fT6YzX2pQ4eM9vW1kLdB3 uJ7nP0xR3aH5bG2q
```

The 24-byte key selects AES-192; the IV is 16 bytes. The existing dump writeup shows the ciphertext retrieval and AES-CBC decryption steps. The PDF reports the decrypted message as:

```text
!aB3@dE5#fG7^hI9&jK1*lM2(nO4)pQ6-rS8_tU0+vW
```

This string is the PDF's **decrypted message**, not a `CSG_FLAG{...}` wrapper. I verified the parameter decoding locally; I did not independently decrypt the missing event ciphertext from this PDF.

