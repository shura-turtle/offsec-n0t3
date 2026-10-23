---
title: "First 10 Minutes"
weight: 10
bookToc: true
---

# Steganography triage

**Do the cheap structural checks before broad guessing.** Preserve the original bytes; every transformation goes into a new file.

## 1. Record and classify

Standard-library Python works even when a dedicated `file`/hash utility is unavailable:

```python
from pathlib import Path
import hashlib

p = Path("challenge.bin")
h = hashlib.sha256()
with p.open("rb") as stream:
    head = stream.read(32)
    h.update(head)
    for block in iter(lambda: stream.read(1024 * 1024), b""):
        h.update(block)
print("size", p.stat().st_size, "head", head.hex(), "sha256", h.hexdigest())
```

| Starting bytes | Candidate |
| --- | --- |
| `89 50 4e 47 0d 0a 1a 0a` | PNG |
| `ff d8 ff` | JPEG |
| `47 49 46 38 37 61` / `47 49 46 38 39 61` | GIF |
| `42 4d` | BMP |
| `50 4b 03 04` | ZIP member; DOCX/PPTX/XLSX are ZIP containers too |
| `25 50 44 46 2d` | PDF |
| `52 49 46 46 .... 57 41 56 45` | RIFF/WAVE; confirm bytes 8–11 are `WAVE` |
| `1f 8b 08` | gzip candidate |
| `fd 37 7a 58 5a 00` | xz candidate |

A signature is not enough: confirm the format with a matching parser. Do not rename random bytes and call them an image repair.

## 2. Metadata, strings, signatures

```sh
exiftool -a -u -g1 challenge.png
strings -a -n 6 -t x challenge.png
xxd -l 128 challenge.png
binwalk challenge.png
```

`strings -t x` prints hexadecimal offsets. Keep number bases explicit when carving. Binwalk output depends on the installed major version; use its detection result as a hypothesis, then validate a selected payload instead of blindly recursively extracting everything.

Metadata fields worth reading: comments, author/artist, description, software, embedded thumbnails, GPS, custom tags, document properties and filenames. A password-looking value may unlock a later layer; preserve its exact case and punctuation.

## 3. Inspect what the carrier shows

| Carrier | Human inspection |
| --- | --- |
| Image | Full size, alpha/background, crop boundaries, suspicious color regions |
| Animation | All frames, frame order and timing |
| QR/barcode | Decode original first; retain quiet border when making a crop |
| Audio | Duration, left/right difference, repeated pulses, speech/tone clues |
| PDF | All pages, annotations, attachments, text on similar-colored backgrounds |
| Text | Line lengths, tabs vs spaces, invisible code points, capitalization |

Inspecting a screenshot cannot recover a hidden bitstream from the original image. Work on the supplied file, not a preview compressed by a chat service.

## 4. Pick the next branch from evidence

```text
Readable metadata hint? → follow that exact hint first
Appended/embedded signature? → carve and validate container
Lossless image + no structural clue? → inspect channels and LSB
JPEG + pixel LSB looks random? → metadata/trailer/coefficient hypothesis
Audio + tones/visual hint? → spectrogram
PDF + no visible text? → text extraction / objects / attachments
Text + unexplained length? → inspect code points and whitespace
```

No need to attempt every channel ordering before reading an obvious EXIF comment.

## 5. Extracted data: classify again

```sh
xxd -l 64 extracted.bin
strings -a -n 6 extracted.bin
binwalk extracted.bin
```

Common second layers: ZIP/gzip/xz, Base64/hex, a QR image, text containing a password, or XOR with a clue-derived key. Check alphabet and padding before Base64-decoding a random alphanumeric string. Keep raw bytes; invalid UTF-8 is common in a legitimate binary payload.

## 6. Controls that stop false positives

| Finding | Verification |
| --- | --- |
| zsteg says `file:` | Extract exact selector; check file structure and parser result |
| A few printable letters | Seek complete grammar, expected prefix or a valid next-layer header |
| Archive found | List entries and verify its CRC after bounded extraction |
| “Flag” in metadata | Confirm challenge format and whether it is a hint/decoy |
| Altered image reveals text | Save the transformation settings and visually confirm every character |

If you can only infer an ambiguous letter, keep it marked as uncertain until the source/frame or another layer resolves it.

Tools: [ExifTool](../../ajcbbc_allow_tools/exiftool/), [binwalk](../../ajcbbc_allow_tools/binwalk/), [strings](../../ajcbbc_allow_tools/strings/), [HxD](../../ajcbbc_allow_tools/hxd/), [xxd](../../ajcbbc_allow_tools/xxd/).

Next: [LSB](../images-lsb/), [container parsing](../png-jpeg/), [carving](../archives-carving/).
