---
title: "binwalk"
weight: 13
bookToc: true
---

**Use for:** embedded file signatures, firmware and appended data.  
**Run in:** WSL. The approved list says latest; CLI details differ between v2 and v3.

## Quick commands

```bash
binwalk --help                                # Check this version's switches
binwalk firmware.bin                          # Locate embedded file signatures
binwalk -e firmware.bin                       # Extract recognized embedded content
binwalk -Me firmware.bin                      # Recursively extract nested content
```

Check the installed help for extraction options. The current upstream tool is a Rust rewrite; older online examples may target Python based v2.

## Walkthrough: inspect an embedded file

1. Scan the original file.
2. Record the offset and identified signature.
3. Try extraction and note the output directory printed by the tool.
4. Inspect extracted files; a signature hit alone can be accidental.

```bash
# Example: carve from decimal offset 4096 to EOF
# Replace 4096 with a confirmed offset from the scan
dd if=firmware.bin of=carved.bin bs=1 skip=4096 status=none
xxd -l 64 carved.bin
```

If the embedded object has a known length, add `count=LENGTH` to `dd`.

## Gotchas

- Extraction may require external extractors that are absent on the PC.
- Recursive extraction can produce large output; start with a normal scan.
- High entropy suggests compression or encryption but does not distinguish them.
- Keep the source untouched and write recovered files separately.

## Flags explained

| Flag | Meaning |
| --- | --- |
| `--help` | Show supported options for the installed version |
| `-e` | Extract supported embedded content |
| `-M` | Enable recursive/matryoshka analysis/extraction |
| `-Me` | Combine recursive mode and extraction |
| `-E` on builds supporting it | Entropy analysis; confirm in local help |

Without extraction switches, `binwalk FILE` scans for signatures. Extraction helpers, destination switches and recursion behavior differ by version. `-d` is not a universal “decode” flag across tools; use this build’s documented option for the intended task.

## Read the scan correctly

```text
DECIMAL       HEXADECIMAL     DESCRIPTION
4096          0x1000          ...embedded format...
```

The decimal and hex values describe the same offset. Record the input filename too: an offset inside an extracted child belongs to that child, not the original container.

## CTF: carve an exact range

```python
from pathlib import Path

# Replace with a validated start and length
start, length = 0x1000, 0x2000
data = Path("container.bin").read_bytes()
assert 0 <= start <= start + length <= len(data)
Path("out/embedded.bin").write_bytes(data[start:start + length])
```

Create `out/` first. An adjacent signature is a clue to an end boundary, not proof that two objects are contiguous or independent.

## CTF: analyze a misleading image extension

1. `xxd -l 32 image.jpg`: check the actual header.
2. `exiftool image.jpg`: compare detected type and metadata.
3. `binwalk image.jpg`: identify candidate embedded streams.
4. Carve or extract the strongest candidate.
5. Open the extracted object with its parser and look for a complete structure.
6. Record source offset, length and child hash.

## Entropy as a secondary clue

Some builds expose an entropy mode, often `-E`; confirm it in `--help` before using it. A compressed archive, encrypted block and ordinary media payload can all have high entropy. An entropy change helps choose where to inspect bytes; it does not identify the algorithm.

## Extraction failed: classify the reason

| Output/problem | Meaning / next action |
| --- | --- |
| Signature found, extractor missing | Carve and use an available approved parser |
| Extracted file is truncated | Revisit the boundary and source capture/image |
| Repeated nested results | Compare sizes/hashes; check recursion growth |
| Random signature inside compressed bytes | Validate before spending more time |
| Tool syntax rejected | v2/v3 option mismatch; read installed help |

## Keep a small extraction manifest

```text
source: challenge.png
sha256: <source hash>
offset: 4096 / 0x1000
length: <validated length or "to EOF">
candidate format: <scan result>
output: out/payload.bin
validation: <parser result / checksum / recovered content>
```

This makes nested firmware/archive challenges reproducible and avoids confusing offsets from different layers.

Reference: [official Binwalk project](https://github.com/ReFirmLabs/binwalk).
