---
title: "Archives & File Carving"
weight: 40
bookToc: true
---

# Archives, appended payloads and carving

**A signature gives a possible start. Format structure gives an extent. A successful parser/checksum gives confidence.**

## 1. Find candidate offsets

```sh
binwalk carrier.bin
strings -a -n 6 -t x carrier.bin
xxd -s 0x1000 -l 128 carrier.bin
python3 file_carver.py scan carrier.bin
python3 file_carver.py scan carrier.bin --magic 504b0304 --max-hits 20
```

Download [file_carver.py](/snippets/steganography/file_carver.py); it uses only Python's standard library. Its built-in signatures cover PNG, JPEG, ZIP local headers/end records, gzip, xz, PDF and RIFF. Scanning reports candidates and never auto-extracts.

`strings -t x` uses hex offsets; many other tools show both decimal and hex. Explicit `0x` avoids base mistakes.

## 2. Extract one justified interval

```sh
python3 file_carver.py extract carrier.bin candidate.zip --offset 0x1800 --length 4096
python3 file_carver.py extract carrier.bin trailer.bin --offset 0x1800 --to-eof
```

Replace both offsets/lengths with evidence from your file. The script refuses out-of-range intervals, source/output identity, existing outputs and more than 64 MiB unless `--max-bytes` is explicitly raised.

```sh
xxd -l 64 candidate.zip
python3 -m zipfile -l candidate.zip
```

Do not carve a ZIP only up to the next `PK` signature: ZIP files contain many local headers plus a central directory and end record. Removing the central directory commonly breaks normal ZIP readers.

## 3. List ZIP members and archive comments

```python
from pathlib import Path
import zipfile

with zipfile.ZipFile("candidate.zip") as z:
    print("archive comment:", repr(z.comment))
    for entry in z.infolist():
        print(repr(entry.filename), "size", entry.file_size,
              "compressed", entry.compress_size, "CRC", hex(entry.CRC),
              "encrypted", bool(entry.flag_bits & 1),
              "comment", repr(entry.comment))
```

An Office document is often a ZIP package: `[Content_Types].xml`, `word/`, `ppt/` or `xl/` give its role. Inspect directory names, member comments and extra fields before attempting passwords.

## 4. Targeted bounded extraction

This copies one named member into a filename you choose; it does not trust archive paths or extract every entry:

```python
from pathlib import Path
import shutil
import zipfile

limit = 8 * 1024 * 1024
member = "flag.txt"  # use exact listed name
with zipfile.ZipFile("candidate.zip") as z:
    entry = z.getinfo(member)
    if entry.file_size > limit:
        raise ValueError("declared member size exceeds limit")
    with z.open(entry) as source, Path("recovered-member.bin").open("xb") as output:
        remaining = limit
        while True:
            block = source.read(min(65536, remaining + 1))
            if not block:
                break
            if len(block) > remaining:
                raise ValueError("actual expanded data exceeds limit")
            output.write(block)
            remaining -= len(block)
```

Reading to EOF lets `zipfile` validate supported member CRCs. This is not a defense against every possible resource-intensive malformed archive; choose evidence-sized limits and list before expanding. The [Python ZIP documentation](https://docs.python.org/3/library/zipfile.html) covers supported compression/encryption methods.

## 5. Password and compatibility diagnostics

| Error | Interpretation / next step |
| --- | --- |
| Password required | Check metadata, visible hints, comments and previous-layer output |
| Wrong password | Preserve exact bytes/case; distinguish tool unsupported encryption |
| Unsupported compression/encryption | Installed parser lacks the method; not proof of corruption |
| Bad CRC after extraction | Wrong password in some implementations, damaged payload or wrong range |
| No central directory | Wrong extent, truncation, multipart ZIP or non-ZIP false positive |

Python's `zipfile` is not a general AES-encrypted ZIP solution. Use only an installed event-approved tool that supports the actual method. Do not rewrite encryption flags and treat that as successful decryption.

## 6. gzip and xz layers

```sh
xz --list payload.xz
xz --test payload.xz
xz --decompress --stdout payload.xz > decoded.bin
```

Choose a fresh output filename first: shell redirection can overwrite existing files. For small gzip evidence with a reasonable expected size:

```python
import gzip
from pathlib import Path

limit = 8 * 1024 * 1024
with gzip.open("payload.gz", "rb") as source:
    result = source.read(limit + 1)
if len(result) > limit:
    raise ValueError("expanded payload exceeds limit")
with Path("decoded.bin").open("xb") as output:
    output.write(result)
```

Extracted carrier bits may leave padding after the actual compressed member. Use format length/end records and checksums to choose the correct extent; do not silently discard arbitrary bytes until a decoder stops complaining.

## 7. Repeatable chain

```text
carrier hash → signature offset → justified byte extent
→ archive listing → selected member + CRC → nested format → full result
```

Tools: [binwalk](../../ajcbbc_allow_tools/binwalk/), [HxD](../../ajcbbc_allow_tools/hxd/), [xz](../../ajcbbc_allow_tools/xz/), [Python](../../ajcbbc_allow_tools/python3/).

Related: [PNG/JPEG boundaries](../png-jpeg/), [PDF attachments](../pdf-documents/).
