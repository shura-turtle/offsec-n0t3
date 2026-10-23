---
title: "Steganography"
weight: -8
bookCollapseSection: true
bookToc: true
description: "Offline steganography workflows: inspect the carrier, identify the channel, recover exact bytes."
---

# Steganography field notes

**Inspect the container before guessing the hidden algorithm.** A file can hold a message in metadata, trailing bytes, pixels, sound samples, document objects or text code points.

These notes use tools already covered in the [approved-tool reference](../ajcbbc_allow_tools/). Optional Python packages are explicitly marked: Python being available does not mean Pillow, NumPy or Matplotlib is installed or allowed by your event.

## Pick the evidence you have

| Evidence / clue | Read next | First useful action |
| --- | --- | --- |
| Unknown artifact or misleading extension | [Triage](triage/) | Magic, metadata, strings, dimensions, embedded signatures |
| Lossless image, “least significant” hint | [Image LSB and bit planes](images-lsb/) | Identify actual image mode and test one channel |
| PNG/JPEG with odd size or broken structure | [Image containers](png-jpeg/) | Parse chunks/markers; distinguish pixels from compressed coefficients |
| Appended ZIP, archive inside image | [Archives and carving](archives-carving/) | Establish offset and length, list entries before extraction |
| WAV, repeating tones, strange noise | [Audio](audio/) | Channels/sample format, waveform, spectrogram, sample bits |
| PDF, DOCX, presentation | [PDF and documents](pdf-documents/) | Visible text, metadata, attachments, XML/media members |
| Invisible characters, odd spacing | [Text and Unicode](text-unicode/) | Escaped code points and symbol counts |
| Need reusable offline extraction tools | [Python snippets](python-snippets/) | Download helpers and choose explicit extraction settings |

## Ordered route

```text
Original file + hash
  → inspect metadata / strings / format
  → inspect visible content or listen at a comfortable level
  → identify a specific hidden channel
  → extract exact bytes to a new file
  → classify the extracted payload
  → decode / decompress only the indicated layer
  → verify full message, checksum or valid nested format
```

## Fast toolbox map

| Task | Existing notes |
| --- | --- |
| Metadata and thumbnails | [ExifTool](../ajcbbc_allow_tools/exiftool/) |
| Readable data and byte offsets | [strings](../ajcbbc_allow_tools/strings/), [xxd](../ajcbbc_allow_tools/xxd/) |
| Hex inspection / precise selection | [HxD](../ajcbbc_allow_tools/hxd/) |
| Embedded format candidates | [binwalk](../ajcbbc_allow_tools/binwalk/) |
| PNG/BMP bitstream candidates | [zsteg](../ajcbbc_allow_tools/zsteg/) |
| QR / barcode | [ZBar](../ajcbbc_allow_tools/zbar/) |
| PDF text / internals | [pdftotext](../ajcbbc_allow_tools/pdftotext/), [qpdf](../ajcbbc_allow_tools/qpdf/) |
| Decompression / custom extraction | [xz](../ajcbbc_allow_tools/xz/), [Python](../ajcbbc_allow_tools/python3/) |
| Encodings / XOR / visual decode | [CyberChef](../ajcbbc_allow_tools/cyberchef/) |

## Keep these distinctions clear

- A ZIP signature is a candidate offset, not a validated archive.
- A decoder finding a short printable word in random bits is not a confirmed message.
- PNG compressed file bytes are not the image's decoded pixel bytes.
- JPEG coefficient hiding is different from PNG pixel-LSB hiding.
- A visually hidden object may still be ordinary document text.
- A QR may give a hint while a different layer contains the result.

## Extraction record

```text
Original filename and SHA-256:
Container / dimensions / encoding:
Clue:
Tool and version:
Offset / member / channel / bit plane:
Pixel or sample order / packing / skip:
Extracted filename and SHA-256:
Next layer:
Verified full message:
```

Write down the exact settings that worked. “LSB” alone is insufficient to reproduce a result.
