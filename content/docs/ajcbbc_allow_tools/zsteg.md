---
title: "zsteg"
weight: 12
bookToc: true
---

**Use for:** bit plane and LSB steganography in PNG/BMP images.  
**Run in:** WSL; Ruby gem already supplied.

## Quick commands

```bash
zsteg --help                                  # Discover supported options
zsteg image.png                               # Run normal image stego checks
zsteg -a image.png > zsteg_results.txt         # Search all supported combinations
```

## Walkthrough: extract a detected channel

1. Run `zsteg image.png`.
2. Look for coherent text or a recognizable file signature.
3. Copy the exact channel selector from that result.
4. Extract it with `-E` and inspect the saved bytes.

```bash
# Example selector; replace it with the result from YOUR image
zsteg -E 'b1,rgb,lsb,xy' image.png > extracted.bin
xxd -l 64 extracted.bin
strings -a extracted.bin
```

## Read the selector

```text
b1,rgb,lsb,xy
│  │   │   └─ pixel traversal order
│  │   └───── least significant bit interpretation
│  └───────── selected color channels
└──────────── one bit per selected channel
```

## Gotchas

- `-a` is a broad search; false positives are common.
- JPEG is not this tool’s normal target format.
- Resizing or re-saving an image can destroy hidden bits; analyze the original.
- An extracted stream may need another decode/decompression step.

## CTF: narrow the search after the first scan

```bash
# Save broad results once rather than repeatedly scanning
zsteg -a image.png > scan.txt 2>&1
grep -niE 'flag|text:|file:' scan.txt

# Inspect only a specific bit count/channel combination
zsteg --bits 1 --channels r image.png
zsteg --bits 1 --channels rgb image.png
```

Use `zsteg --help` to confirm the installed selector switches. A channel finding should lead to extraction and verification.

## Flags explained

| Flag | Meaning |
| --- | --- |
| `-a` / `--all` | Try all known supported methods |
| `-E NAME` | Extract exactly the named payload selector |
| `--bits N` | Select the bit count/pattern to examine |
| `--channels LIST` | Choose channels and their order, such as `r` or `bgr` |
| `--order xy` | Choose pixel traversal order |
| `--lsb` / `--msb` | Select bit interpretation order |
| `--limit N` | Limit checked bytes; zero disables that limit |

Read the extracted selector literally. `b1,rgb,lsb,xy` combines choices that correspond to separate options; changing any component changes the recovered byte stream.

## CTF: follow a compressed payload

```bash
# Example detected selector: copy the exact value from your own result
zsteg -E 'b1,rgb,lsb,xy' image.png > payload.bin
xxd -l 32 payload.bin
binwalk payload.bin
strings -a payload.bin | head -n 30
```

If the extraction starts with gzip magic `1f 8b`, decompress with Python:

```python
from pathlib import Path
import gzip

raw = Path("payload.bin").read_bytes()
plain = gzip.decompress(raw)
Path("payload_decoded.bin").write_bytes(plain)
print(repr(plain[:200]))
```

Trailing carrier bits may follow the real payload. Use its format/length/checksum to identify the meaningful bytes before deciding extraction failed.

## Understand alternate pixel orders

`xy` versus `yx` changes traversal order. Channel orders such as `rgb` and `bgr` change how bits are joined. `lsb`/`msb` affects interpretation. Several plausible looking outputs can come from one image; trust a complete message or valid file structure.

## Inspect one channel independently with Python

If Pillow is installed as an allowed non-AI Python library, this example reads one low bit from each red-channel pixel, row by row, packing the first collected bit as the most significant bit of each output byte:

```python
from PIL import Image
from pathlib import Path

image = Image.open("image.png").convert("RGB")
bits = [r & 1 for r, g, b in image.getdata()]
packed = bytes(
    sum(bits[start + bit] << (7 - bit) for bit in range(8))
    for start in range(0, len(bits) - 7, 8)
)
Path("red_lsb.bin").write_bytes(packed)
print(repr(packed[:100]))
```

This is one explicit layout, not a decoder for every stego scheme. Palette indices, alpha channels and custom traversal require different handling.

## Decide the next tool

| Result | Next step |
| --- | --- |
| Readable flag-shaped text | Validate full value and prefix |
| Encoded text | CyberChef / Python decode |
| File signature | Save bytes; validate with the format’s parser |
| Many short English fragments | Treat as possible noise |
| No meaningful LSB result | Check metadata, appended data, visible channels and challenge hints |

Reference: [zsteg usage and extraction examples](https://github.com/zed-0xff/zsteg).

## Related playbooks

- [Explicit image LSB extraction](../../steganograph-expl/images-lsb/)
- [Image container analysis](../../steganograph-expl/png-jpeg/)
