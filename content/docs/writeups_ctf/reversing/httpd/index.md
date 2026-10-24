---
title: "httpd"
date: 2026-10-24
weight: 1
bookToc: true
description: "Reconstruct the ICMP-triggered AES decryptor from source and packet fields."
---

# HTTPD

[Download solver](files/solve.py)

The executable looks like a small HTTP server, but the flag does not come from a URL. A background packet-capture routine watches ICMP traffic, extracts selected bytes, and uses them as an AES key and IV.

Recovered flag:

```text
CMO{fUn_w1th_m4g1c_p4ck3t5}
```

This solve reproduces the packet checks and AES calculation offline using the supplied source and ciphertext extracted from the binary. The FreeBSD executable was not run under Linux, and no packets were sent to a live host.

## 1. Identify the executable

The handout is `httpd/handout/httpd` in the public challenge repository. Start with:

```bash
file httpd
sha256sum httpd
```

The relevant output is:

```text
ELF 64-bit LSB executable, x86-64, version 1 (FreeBSD), dynamically linked,
interpreter /libexec/ld-elf.so.1, for FreeBSD 14.3, with debug_info, not stripped
```

SHA-256:

```text
f30893ce8639f4a551206878db19c6a7f299ecad22ffb5e60ed90df4f47e89dc
```

The operating system matters here. This is a FreeBSD program requiring its runtime and packet-capture interface. Native Linux execution is not a useful test of the challenge logic.

The repository also supplies `httpd/source/httpd.go` and an official solution PDF. The steps below cross-check the source model against the embedded ciphertext rather than just copying the flag from a source comment.

## 2. Follow the background routine

The Go source starts an HTTP listener on port 8080. Its normal GET handler returns:

```text
Nothing to see here :{
```

More useful is the goroutine started beside it:

```go
go httpInit()
```

`httpInit` opens packet capture on interface `re0` and filters for ICMP:

```go
pcap.OpenLive("re0", 1600, true, pcap.BlockForever)
handle.SetBPFFilter("icmp")
```

The shipped binary's relevant symbol is named `net/http.init`. The source and binary naming differ, so follow its pcap and AES calls instead of relying only on a function name.

The routine slices bytes directly from the captured Ethernet frame. It does not use an IPv4 parser to account for optional headers. For this input we need Ethernet + a normal 20-byte IPv4 header + ICMP.

## 3. Translate the packet checks

These are offsets from the beginning of the Ethernet frame, not from the IP header:

| Frame offset | Field | Required interpretation |
| --- | --- | --- |
| `0x10:0x12` | IPv4 total length | Big-endian value `0x20` |
| `0x14:0x18` | IPv4 flags/fragment offset, TTL, protocol | Used as four key bytes |
| `0x22` | ICMP type | `8`, echo request |
| `0x24:0x26` | ICMP checksum | Used as key bytes and little-endian XOR operand |
| `0x26:0x28` | ICMP identifier | Little-endian value `0x1337` |
| `0x2a:0x2e` | Four bytes of ICMP payload | Little-endian value `0xe55fdec6` |

An IPv4 total length of 32 consists of a 20-byte IP header, an eight-byte ICMP header, and four payload bytes.

For the identifier, the raw bytes must be `37 13`. Interpreted little-endian, those are `0x1337`; interpreted as the network-order ICMP identifier, they are `0x3713`. Passing `0x1337` directly to a network-order packet builder would put the wrong bytes in the frame.

Similarly, the required payload bytes are:

```text
c6 de 5f e5
```

They are a fixed challenge value. There is no requirement to synchronize with the current clock.

## 4. Construct the ICMP checksum

Choose the ordinary echo-request sequence number 1. Before inserting the checksum, the 12-byte ICMP message is:

```text
08 00 00 00 37 13 00 01 c6 de 5f e5
```

Compute the one's-complement checksum by adding network-order 16-bit words, folding carries, and complementing the result:

```python
import struct

def checksum(data):
    if len(data) % 2:
        data += b"\0"
    value = sum(struct.unpack(">" + "H" * (len(data) // 2), data))
    while value >> 16:
        value = (value & 0xffff) + (value >> 16)
    return (~value) & 0xffff

message = bytes.fromhex("0800000037130001c6de5fe5")
print(f"{checksum(message):04x}")
```

Output:

```text
9a27
```

Insert `9a 27` into the checksum field:

```text
08 00 9a 27 37 13 00 01 c6 de 5f e5
```

The checksum of this completed message is zero, which checks the construction independently of the AES output.

For the four IP-header bytes used in the key, choose Don't Fragment, fragment offset zero, TTL 64, and protocol ICMP:

```text
40 00 40 01
```

The sequence number, TTL, and flags are not all directly constrained by the program's success checks. These normal values are the ones that produce the meaningful decrypted flag. The synthetic packet built by the solver verifies all explicit checks before deriving the key.

## 5. Reproduce the key construction exactly

The source reads the payload and checksum as little-endian integers:

```python
ts = int.from_bytes(bytes.fromhex("c6de5fe5"), "little")
cs = int.from_bytes(bytes.fromhex("9a27"), "little")
high = (ts >> 16) ^ cs
low = (ts & 0xffff) ^ cs
```

The values are:

```text
ts   = e55fdec6
cs   = 279a
high = e55f XOR 279a = c2c5
low  = dec6 XOR 279a = f95c
```

It serializes the two XOR results big-endian and assembles the rest as raw packet bytes:

```text
high[2] || ip_fields[4] || checksum[2] || payload[4] || identifier[2] || low[2]
```

The resulting 16-byte key is:

```text
c2c5 40004001 9a27 c6de5fe5 3713 f95c
```

Without spaces:

```text
c2c5400040019a27c6de5fe53713f95c
```

The call to `cipher.NewCBCDecrypter` passes the same bytes as the IV. This is AES-128-CBC with `IV = key`.

## 6. Extract the ciphertext from machine code

The ciphertext is assembled by four `movabs` instructions, so a search for the complete 32-byte string in the file fails. Disassemble this range:

```bash
objdump -d -M intel --start-address=0x7484d2 \
  --stop-address=0x748509 httpd
```

The four constants are:

```asm
0x7484d2: movabs rcx, 0xc07edfb429a5f151
0x7484df: movabs rcx, 0xb34e3d248f2f3b2a
0x7484ed: movabs rcx, 0x8cdd9c0bcfb0ed5a
0x7484fb: movabs rcx, 0x0c64c43e9b0ee6cd
```

Each is stored as a little-endian 64-bit word. Concatenating their bytes gives:

```text
51f1a529b4df7ec02a3b2f8f243d4eb35aedb0cf0b9cdd8ccde60e9b3ec4640c
```

The accompanying solver reads those instruction bytes through the ELF `PT_LOAD` mappings. It checks each `48 b9` opcode and extracts the eight-byte immediate, so the ciphertext comes from the supplied binary rather than a copied plaintext comment.

## 7. Decrypt and check the result

```python
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

key = bytes.fromhex("c2c5400040019a27c6de5fe53713f95c")
ciphertext = bytes.fromhex(
    "51f1a529b4df7ec02a3b2f8f243d4eb3"
    "5aedb0cf0b9cdd8ccde60e9b3ec4640c"
)
padded = AES.new(key, AES.MODE_CBC, key).decrypt(ciphertext)
plaintext = unpad(padded, AES.block_size)
assert AES.new(key, AES.MODE_CBC, key).encrypt(padded) == ciphertext
print(plaintext.decode("ascii"))
```

Output:

```text
CMO{fUn_w1th_m4g1c_p4ck3t5}
```

## 8. Run the complete offline solver

Install PyCryptodome and point `solve.py` at the handout:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install pycryptodome
python solve.py /path/to/ctf-2026-challenges-public/httpd/handout/httpd
```

Recorded output:

```text
ICMP checksum: 9a27
ICMP bytes: 08009a2737130001c6de5fe5
Key and IV: c2c5400040019a27c6de5fe53713f95c
Ciphertext: 51f1a529b4df7ec02a3b2f8f243d4eb35aedb0cf0b9cdd8ccde60e9b3ec4640c
CMO{fUn_w1th_m4g1c_p4ck3t5}
```

The script constructs a synthetic Ethernet/IP/ICMP frame in memory, checks the source's field predicates, derives the key from those frame offsets, extracts the encrypted bytes from the ELF, checks padding, and re-encrypts to the same ciphertext. This is static/source-model verification. Running the packet-capture service on FreeBSD and observing its output was not part of this replay.
