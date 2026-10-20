---
title: "ZBar"
weight: 19
bookToc: true
---

**Use for:** decoding QR codes and supported barcodes from images.  
**Run in:** WSL; the image CLI is `zbarimg`.

## Decode a QR image

```bash
# Shows barcode type plus decoded value
zbarimg code.png

# Write only the decoded payload
zbarimg --quiet --raw code.png > decoded.txt
```

## Scan several images

```bash
# Normal output retains image/scan context better than raw payload alone
zbarimg *.png

# Raw output for a known single image
zbarimg --raw frame_001.png
```

## CTF walkthrough

1. Save the original QR/barcode image.
2. Run `zbarimg` and keep the decoded value.
3. Check whether it is a URL, Base64, hex, or plain text.
4. Continue in CyberChef or Python if another encoding is present.

## If it does not decode

- Check whether the whole code and its surrounding quiet border are visible.
- Try a clearer supplied frame or image when available.
- A stylized, damaged or incomplete code may need reconstruction first.
- No result does not prove the image contains no hidden data; use zsteg/binwalk for other image clues.

Check the installed build’s supported formats and options with `zbarimg --help`.

## Flags explained

| Flag | Meaning |
| --- | --- |
| `--raw` | Emit decoded data without normal barcode-type formatting |
| `--quiet` | Reduce normal status/summary output |
| `--help` | Print supported options for the installed build |

`--raw` changes output formatting; it does not reconstruct a damaged barcode or guarantee arbitrary binary payloads survive a text pipeline.

## CTF: keep decoded values associated with filenames

```bash
mkdir -p qr_results
for image in frames/*.png; do
  printf '\nFILE: %s\n' "$image"
  zbarimg "$image"
done > qr_results/scans.txt 2> qr_results/errors.txt
```

This helps when each frame contains one part of a message. Keep decode errors separately so you can revisit unreadable frames.

## CTF: assemble ordered fragments

If each code contains a sequence index such as `03:PAYLOAD`, parse that index and sort numerically. Do not sort the payload text itself. Deduplicate only when both the index and contents agree.

```python
parts = ["02:demo}", "01:flag{"]  # Example decoded records
records = {}
for part in parts:
    index, payload = part.split(":", 1)
    number = int(index)
    if number in records and records[number] != payload:
        raise ValueError("conflicting fragment")
    records[number] = payload
print("".join(records[i] for i in sorted(records)))
```

Check for missing sequence numbers before submitting the result.

## CTF: separate visible QR data from image steganography

A valid QR can decode to a hint while the PNG itself contains another payload. Record the QR result, then inspect original metadata, appended data and bit planes if the clue indicates another layer.

## Interpret common outcomes

| Result | Meaning |
| --- | --- |
| Valid URL | Treat as a clue and follow competition scope |
| Base64/hex-looking text | Preserve exact payload and decode separately |
| Many repeated identical reads | Same visible code across frames |
| No decode | Visibility, contrast, geometry, supported symbology or damage |

Reference: [ZBar upstream project](https://github.com/mchehab/zbar).
