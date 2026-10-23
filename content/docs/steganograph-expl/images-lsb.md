---
title: "Images: LSB & Bit Planes"
weight: 20
bookToc: true
---

# Lossless image LSB and bit planes

**Determine the decoded image mode first.** RGB samples, RGBA alpha, grayscale values and palette indices are different carriers.

## 1. Inspect before extraction

```sh
exiftool -a -u -g1 image.png
zsteg image.png
```

If Pillow is already installed and allowed:

```python
from PIL import Image
with Image.open("image.png") as im:
    print(im.format, im.mode, im.size, getattr(im, "n_frames", 1))
    print("bands:", im.getbands(), "metadata keys:", sorted(im.info))
```

| Mode | What the helper reads |
| --- | --- |
| `RGB` | Red, green, blue 8-bit sample values |
| `RGBA` | RGB plus independent alpha values |
| `L` | Grayscale sample (`--channels l`) |
| `P` | Palette indices (`--channels i`), not converted RGB values |
| 16-bit / floating / other | Helper rejects; inspect sample depth before a separate explicit conversion |

Palette-to-RGB conversion can destroy an index-based message. Converting RGBA to RGB discards alpha. Read [Pillow mode concepts](https://pillow.readthedocs.io/en/stable/handbook/concepts.html) before making conversions.

## 2. zsteg: finding → exact extraction

```sh
zsteg -a image.png > zsteg-results.txt 2>&1
zsteg -E 'b1,rgb,lsb,xy' image.png > extracted.bin
xxd -l 64 extracted.bin
strings -a extracted.bin
```

The selector above is an example. Copy the exact selector from your result. A broad scan produces false positives; extraction plus a valid message/container is the proof. Options can differ across installed builds: consult `zsteg --help`. See the [upstream zsteg usage](https://github.com/zed-0xff/zsteg).

## 3. Manual bitstream extraction

Download [image_lsb.py](/snippets/steganography/image_lsb.py). It requires **optional Pillow**, never modifies the source and refuses to overwrite existing outputs.

```sh
python3 image_lsb.py image.png red.bin --channels r --bit 0 --bytes 128
python3 image_lsb.py image.png rgb.bin --channels rgb --bit 0 --bytes 128
python3 image_lsb.py image.png bgr.bin --channels bgr --bit 0 --bytes 128
python3 image_lsb.py image.png alpha.bin --channels a --bit 0 --bytes 128
```

`rgb` means R bit, G bit, B bit from pixel 0, followed by the same from pixel 1. It does not mean all red pixels followed by all green pixels.

## 4. Explicit interpretation settings

| Switch | Meaning |
| --- | --- |
| `--bit 0` | Extract each sample's bit zero, the least significant bit |
| `--bit 1` | Extract sample bit one; not “two bits per sample” |
| `--order row` | Left-to-right within each row, then top-to-bottom |
| `--order column` | Top-to-bottom within each column, then left-to-right |
| `--pack msb` | First collected bit becomes output byte bit seven |
| `--pack lsb` | First collected bit becomes output byte bit zero |
| `--skip-bits 3` | Discard the first three collected carrier bits before byte packing |
| `--bytes 64` | Stop at 64 complete output bytes |
| `--frame 2` | Select frame index two, if the format has it |

The helper's terminology is explicit and is **not a promise of exact equivalence to every zsteg selector**. zsteg may also support sample bit patterns, multiple bits/sample and other traversals.

```sh
python3 image_lsb.py image.png shifted.bin --channels rgb --skip-bits 3 --bytes 128
python3 image_lsb.py image.png reversed.bin --channels rgb --pack lsb --bytes 128
python3 image_lsb.py image.png column.bin --channels rgb --order column --bytes 128
```

## 5. Visual bit-plane extraction

```sh
python3 image_lsb.py image.png red-plane0.png --channels r --bit 0 --plane
python3 image_lsb.py image.png alpha-plane0.png --channels a --bit 0 --plane
```

Bit zero becomes black/white values in a new lossless PNG. A hidden QR or text may become visually obvious even when the same bits do not form byte-aligned text. Decode an extracted QR using [ZBar](../../ajcbbc_allow_tools/zbar/):

```sh
zbarimg --quiet --raw red-plane0.png
```

If necessary, make an explicit inverted/cropped working copy with permitted image tooling. Keep the quiet border around QR symbols. A failed QR decode does not disprove a visible symbol.

## 6. Capacity and controls

For width `W`, height `H`, `C` selected channels and one bit/sample:

```text
capacity_bits = W × H × C
capacity_bytes = floor((capacity_bits - skipped_bits) / 8)
```

Change one setting at a time. A real payload generally becomes coherent under a specific combination; random output that contains one short word is weak evidence. Check magic bytes, plausible length fields, decompression success and checksums.

## Troubleshooting

| Symptom | What to inspect |
| --- | --- |
| All alpha bits equal | Alpha may be uniformly opaque; try RGB with evidence |
| Plausible prefix, later noise | Wrong length, padding, changing channel layout or another encoding |
| Every channel is random | Revisit metadata/trailer; carrier may not use pixel LSB |
| Wrong after re-save | Original bits may have been changed; return to original |
| JPEG extraction looks random | JPEG coefficient methods need a different representation |
| Script reports existing output | Choose a new name; it intentionally refuses overwrites |

Next: [PNG/JPEG structures](../png-jpeg/), [compressed payloads](../archives-carving/), [downloadable scripts](../python-snippets/).
