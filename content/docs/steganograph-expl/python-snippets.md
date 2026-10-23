---
title: "Offline Python Toolkit"
weight: 80
bookToc: true
---

# Offline Python steganography toolkit

**Download helpers before the event and rehearse with a known message.** These tools do not use network requests or AI. Whether prewritten scripts and optional packages are permitted is determined by your event's rules.

## 1. Downloadable helpers

| Helper | Dependencies | Purpose |
| --- | --- | --- |
| [file_carver.py](/snippets/steganography/file_carver.py) | Standard library | Signature candidate scan and explicit bounded-range extraction |
| [image_lsb.py](/snippets/steganography/image_lsb.py) | Optional Pillow | Channel/plane bit extraction and lossless visible bit-plane PNG |
| [text_unicode.py](/snippets/steganography/text_unicode.py) | Standard library | Escaped Unicode inspection and two-code-point bitstream extraction |

Use Python 3.9 or later. All three accept `--help`, preserve the source and refuse to overwrite an existing output. Work from downloaded local copies:

```sh
python3 file_carver.py --help
python3 image_lsb.py --help
python3 text_unicode.py --help
```

Pillow is imported after command-line parsing, so the image helper's help remains usable when Pillow is absent. The actual extraction prints a clear dependency error. No automatic installation occurs.

## 2. Carving recipes

```sh
python3 file_carver.py scan original.bin
python3 file_carver.py scan original.bin --magic 89504e470d0a1a0a
python3 file_carver.py extract original.bin selected.bin --offset 0x1000 --length 8192
python3 file_carver.py extract original.bin trailer.bin --offset 0x1000 --to-eof
```

The offsets and lengths above are examples. Defaults: at most 100 signature hits and at most 64 MiB copied. Use `--max-hits` or `--max-bytes` to change them deliberately. A signature scan does not validate file length or structure; choose the interval using the container format.

## 3. Image recipes

```sh
python3 image_lsb.py carrier.png red.bin --channels r --bit 0 --bytes 256
python3 image_lsb.py carrier.png rgb.bin --channels rgb --pack msb --order row --bytes 256
python3 image_lsb.py carrier.png shifted.bin --channels bgr --skip-bits 3 --bytes 256
python3 image_lsb.py carrier.png palette.bin --channels i --bytes 256
python3 image_lsb.py carrier.png alpha-plane.png --channels a --bit 0 --plane
```

`i` is allowed only for palette mode `P`; `a` only when the actual mode has alpha. No conversion happens silently. The default extraction cap is 1 MiB. An incomplete last byte is dropped and reported. `--bit 1` selects one sample bit plane, not two bits per sample.

See [image extraction settings](../images-lsb/) for traversal, byte packing, frame and channel definitions.

## 4. Text recipes

```sh
python3 text_unicode.py message.txt --limit 300
python3 text_unicode.py message.txt --all --limit 100
python3 text_unicode.py message.txt --encoding utf-16
python3 text_unicode.py message.txt --zero U+200B --one U+200C --output hidden.bin
python3 text_unicode.py message.txt --zero U+200B --one U+200C --pack lsb --skip-bits 1 --output alternative.bin
```

Code-point inspection never prints the original control characters directly. Input decoding is strict; no normalization, error-dropping or stripping occurs. Extraction selects only the two declared symbols and ignores other cover text.

## 5. Known-message image exercise

This creates a tiny lossless fixture containing `flag{lsb_demo}` in each red sample's low bit. Pillow is required. The first encoded bit is the MSB of the first output byte.

```python
from pathlib import Path
from PIL import Image

message = b"flag{lsb_demo}"
bits = [(byte >> shift) & 1 for byte in message for shift in range(7, -1, -1)]
image = Image.new("RGB", (len(bits), 1), (100, 100, 100))
for x, bit in enumerate(bits):
    image.putpixel((x, 0), (100 | bit, 100, 100))
with Path("demo-lsb.png").open("xb") as output:
    image.save(output, format="PNG")
```

```sh
python3 image_lsb.py demo-lsb.png demo-message.bin --channels r --bytes 14
```

Check exact bytes, not just a substring:

```python
from pathlib import Path
assert Path("demo-message.bin").read_bytes() == b"flag{lsb_demo}"
```

The message has 14 bytes. Using the wrong channel should yield a different stream and fail this assertion, which is a useful negative control.

## 6. Known-message Unicode exercise

```python
from pathlib import Path

message = b"flag{unicode_demo}"
symbols = "".join("\u200c" if (byte >> bit) & 1 else "\u200b"
                  for byte in message for bit in range(7, -1, -1))
with Path("demo-unicode.txt").open("xb") as output:
    output.write(("ordinary cover text" + symbols).encode("utf-8"))
```

```sh
python3 text_unicode.py demo-unicode.txt --zero U+200B --one U+200C --output demo-unicode.bin
```

```python
from pathlib import Path
assert Path("demo-unicode.bin").read_bytes() == b"flag{unicode_demo}"
```

## 7. Reproducible output record

```python
from pathlib import Path
import hashlib

p = Path("demo-message.bin")
data = p.read_bytes()
print("bytes", len(data), "sha256", hashlib.sha256(data).hexdigest())
print("preview", repr(data[:160]))
```

For large data, use the streaming hash from [triage](../triage/). `repr` avoids confusing embedded controls with terminal output. Keep binary outputs even if a text preview looks broken.

## 8. Common preparation failures

| Failure | Fix |
| --- | --- |
| `ModuleNotFoundError: PIL` | Pillow unavailable; use approved zsteg or prepare permitted dependency before the event |
| `File exists` | Choose a new output filename |
| Carver interval exceeds cap | Recheck extent before explicitly raising `--max-bytes` |
| Unsupported image mode | Determine sample representation instead of silently converting |
| Unicode decode error | Identify actual encoding from bytes/BOM |
| Output starts correctly then noise | Determine payload length/header rather than treating all carrier bits as text |

Related tool notes: [Python](../../ajcbbc_allow_tools/python3/), [zsteg](../../ajcbbc_allow_tools/zsteg/), [CyberChef](../../ajcbbc_allow_tools/cyberchef/).
