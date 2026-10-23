---
title: "PNG & JPEG Structure"
weight: 30
bookToc: true
---

# PNG and JPEG container clues

**Separate container bytes, metadata and decoded samples.** Each offers a different hiding place.

## 1. PNG chunk layout

```text
8-byte PNG signature
repeated:
    4-byte big-endian data length
    4-byte ASCII chunk type
    N bytes of data
    4-byte CRC over type + data
```

| Chunk | What to inspect |
| --- | --- |
| `IHDR` | Width, height, bit depth, color type, interlace |
| `PLTE` | Palette entries; index patterns may be meaningful |
| `IDAT` | Parts of the compressed image datastream, not plaintext pixel rows |
| `tEXt`, `zTXt`, `iTXt` | Textual metadata, sometimes compressed |
| `tRNS` | Transparency information for relevant color types |
| `IEND` | End of the PNG datastream |
| Unknown ancillary chunk | Inspect type, length, contents and CRC; unknown does not automatically mean malicious |

PNG compression and per-row filters must be decoded before interpreting pixel LSB. The [PNG specification](https://www.w3.org/TR/png-3/) defines chunk CRCs, image filtering and datastream boundaries.

## 2. Bounded chunk/CRC inspection

Standard-library parser; it does not repair or overwrite the source:

```python
from pathlib import Path
import struct
import zlib

data = Path("image.png").read_bytes()
if data[:8] != b"\x89PNG\r\n\x1a\n":
    raise ValueError("wrong PNG signature")
pos = 8
while pos + 12 <= len(data):
    length = struct.unpack_from(">I", data, pos)[0]
    end = pos + 12 + length
    if end > len(data):
        raise ValueError(f"truncated chunk at {pos:#x}")
    kind = data[pos+4:pos+8]
    body = data[pos+8:pos+8+length]
    stored = struct.unpack_from(">I", data, pos+8+length)[0]
    actual = zlib.crc32(kind + body) & 0xffffffff
    print(hex(pos), repr(kind), length, "CRC_OK" if stored == actual else "CRC_BAD")
    pos = end
    if kind == b"IEND":
        if length != 0:
            raise ValueError("invalid nonempty IEND")
        print("end", hex(pos), "trailing bytes", len(data)-pos)
        break
else:
    raise ValueError("no complete IEND found")
```

This reports structural boundaries; it is not a full PNG conformance checker. A CRC failure tells you bytes differ from the declared checksum, not which bytes should be changed.

## 3. Appended data after IEND

Take the parser's printed `end` offset, then inspect/carve exactly that range:

```sh
python3 file_carver.py scan image.png
python3 file_carver.py extract image.png trailer.bin --offset 0x1234 --to-eof
xxd -l 64 trailer.bin
```

`0x1234` is a placeholder, not a universal PNG endpoint. A PNG with trailing ZIP bytes may still display normally. Validate the ZIP independently; compressed image bytes can accidentally contain short signature matches.

## 4. PNG dimensions and intentional corruption

Unusual dimensions, truncated display or a bad IHDR CRC can be challenge clues. Inspect IHDR and compare expected decompressed row lengths before editing. Changing width/height affects scanline interpretation and can produce deceptive partial images.

Make a new copy for experiments. If you alter chunk data, recompute that chunk's CRC over its **type plus data**. Merely changing the CRC to match corrupted dimensions does not prove the repaired image reflects the intended hidden content.

## 5. JPEG: different representation

```text
SOI ff d8 → marker segments / scan headers → compressed scan data → EOI ff d9
```

JPEG may include comments, EXIF, XMP, thumbnails and multiple scan segments. Entropy-coded scan data uses byte stuffing and restart markers; a naive “every `ff` begins a length-prefixed segment” parser is wrong inside a scan.

First inspect:

```sh
exiftool -a -u -g1 image.jpg
strings -a -n 6 -t x image.jpg
binwalk image.jpg
```

Use the actual JPEG endpoint from a structure-aware inspection. The **first** `ff d9` byte pair found anywhere can occur inside an embedded thumbnail or segment payload, so it is not a universal trailer boundary.

## 6. Pixel LSB versus coefficient steganography

| Method | Carrier | Practical consequence |
| --- | --- | --- |
| PNG/BMP pixel LSB | Decoded integer sample bits | zsteg/Pillow bit extraction may work |
| JPEG coefficient hiding | Quantized transform coefficients | RGB pixels from Pillow do not expose the same bits |
| JPEG metadata/trailer | Container bytes | ExifTool, hex tools and precise carving can work |
| Spatial LSB then saved as JPEG | Original sample bits altered by lossy coding | Exact original bit recovery may be impossible |

Do not convert JPEG to PNG and expect it to restore original pre-compression LSBs. Likewise, zsteg is not a universal JPEG coefficient extractor. If the event's approved toolbox lacks a dedicated coefficient decoder, first exhaust metadata, trailers and source/clue-directed formats; do not claim absence of a hidden coefficient payload from a failed pixel scan.

## 7. Alpha, palettes and animations

Transparency may hide visible RGB values, or alpha itself may carry a bit plane. Palette indexes may encode a message even when palette colors look normal. Animated formats may place fragments across frames; record frame index and disposal/compositing behavior when extracting.

Different decoders may return composited frames instead of raw frame rectangles. Record the library/tool and frame handling used to reproduce your result.

Tools: [ExifTool](../../ajcbbc_allow_tools/exiftool/), [HxD](../../ajcbbc_allow_tools/hxd/), [xxd](../../ajcbbc_allow_tools/xxd/), [binwalk](../../ajcbbc_allow_tools/binwalk/).

Next: [bit-plane extraction](../images-lsb/), [bounded carving](../archives-carving/).
