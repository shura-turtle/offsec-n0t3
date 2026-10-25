---
title: "Gorilla Is Not Godzilla"
date: 2026-10-26T01:53:00+06:30
bookToc: true
description: "Decrypt a Gorillabot C2 log and rank the targets of DISCORD attacks by IP address."
---

# Gorilla Is Not Godzilla

## Original illustrated walkthrough

The pages below reproduce the supplied PDF in order, including every screenshot and code image. Select a page to open it at full size. [Download the original PDF](/writeups_ctf/reversing/gorillabot/source.pdf).

### Page 1: Challenge setup, safety context, and flag format

[![gorillabot PDF page 1: Challenge setup, safety context, and flag format](/writeups_ctf/reversing/gorillabot/page-1.jpg)](/writeups_ctf/reversing/gorillabot/page-1.jpg)

### Page 2: Cipher analysis and decryption screenshots

[![gorillabot PDF page 2: Cipher analysis and decryption screenshots](/writeups_ctf/reversing/gorillabot/page-2.jpg)](/writeups_ctf/reversing/gorillabot/page-2.jpg)

### Page 3: Eight-byte block decryption screenshot

[![gorillabot PDF page 3: Eight-byte block decryption screenshot](/writeups_ctf/reversing/gorillabot/page-3.jpg)](/writeups_ctf/reversing/gorillabot/page-3.jpg)

### Page 4: Attack type 18, IP ranking, and flags for N = 1–20

[![gorillabot PDF page 4: Attack type 18, IP ranking, and flags for N = 1–20](/writeups_ctf/reversing/gorillabot/page-4.jpg)](/writeups_ctf/reversing/gorillabot/page-4.jpg)

## Searchable solve steps

The challenge supplies a defanged Gorillabot binary and `message.log`; the archive password is `virus`. The binary is described as malware and the PDF recommends static analysis in an isolated environment. Neither binary nor log was included with the PDF here, so the decryption routine and table below are documented from that source, not freshly replayed.

## 1. Identify and decrypt C2 messages

Each log entry contains a time and binary message. Static analysis of the provided executable reveals the key derivation and a custom XTEA-like cipher. The PDF points to a byte substitution table, a decrypt-all routine, and an eight-byte block routine in its screenshots. Those screenshots do not provide a copyable complete implementation in the extracted text, so a runnable decoder cannot be reconstructed reliably from this PDF alone.

Decrypt each message, identify the attack type, and retain records with attack number **18**, labeled `attack_udp_discord` in the PDF. Extract their target IPv4 addresses.

## 2. Rank targets numerically

For each distinct target, convert the four octets into a 32-bit integer and sort descending. The PDF illustrates this with `8.8.8.8 = 0x08080808` and `127.0.0.1 = 0x7f000001`. With decrypted targets in `discord_ips`, the ranking step is:

```python
from ipaddress import IPv4Address

ranked = sorted(set(discord_ips), key=lambda ip: int(IPv4Address(ip)), reverse=True)
for rank, ip in enumerate(ranked, 1):
    print(rank, f"CSG_FLAG{{{ip}}}")
```

The challenge requires the **N-th** target; the PDF does not supply a single value of `N`. Its published rank-to-flag table is:

| N | Flag | N | Flag |
| ---: | --- | ---: | --- |
| 1 | `CSG_FLAG{221.158.149.212}` | 11 | `CSG_FLAG{162.159.135.234}` |
| 2 | `CSG_FLAG{218.152.242.38}` | 12 | `CSG_FLAG{162.159.135.232}` |
| 3 | `CSG_FLAG{211.205.207.35}` | 13 | `CSG_FLAG{162.159.130.234}` |
| 4 | `CSG_FLAG{188.53.61.89}` | 14 | `CSG_FLAG{162.159.128.235}` |
| 5 | `CSG_FLAG{182.248.0.34}` | 15 | `CSG_FLAG{162.159.61.3}` |
| 6 | `CSG_FLAG{182.214.214.106}` | 16 | `CSG_FLAG{159.0.61.35}` |
| 7 | `CSG_FLAG{175.197.164.45}` | 17 | `CSG_FLAG{146.103.26.136}` |
| 8 | `CSG_FLAG{175.197.124.124}` | 18 | `CSG_FLAG{135.125.166.29}` |
| 9 | `CSG_FLAG{172.104.62.47}` | 19 | `CSG_FLAG{128.116.44.102}` |
| 10 | `CSG_FLAG{162.159.136.234}` | 20 | `CSG_FLAG{128.116.13.33}` |

Choose the row matching the `N` given to your instance. The table is sourced from the PDF; without `message.log`, its entries cannot be independently checked here.

