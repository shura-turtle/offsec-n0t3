---
title: "FLRSCRNSVR"
date: 2026-10-24
weight: 1
bookToc: true
description: "Invert the screensaver registry-text encoding and verify its table in the handout."
---

# FLRSCRNSVR

[Download solver](files/solve.py)

The handout is a Windows screensaver executable in `FLRSCRNSVR/handout/FLRSCRNSVR.zip`; the archive password is `flare`. The repository includes its official solution, which identifies the registry value and encoding routine. I reproduced the inverse transformation against the encrypted table in the binary. This is an offline reconstruction, not a GUI acceptance test.

## 1. Locate the input and comparison

The screensaver's configuration path (`/c`) reads `Text` under `HKCU\Software\FLRSCRNSVR`. It requires 25 characters and transforms them before comparing the result to a 25-entry, little-endian UTF-16 table. The screensaver and preview paths (`/s`, `/p`) are display modes; they are not needed to recover the text.

The encoded values begin `003c 0051 006a 0009` and end `0002 000e 000b`. The complete array is in the [solver](files/solve.py). With the extracted executable, `--binary` also checks that the packed table exists in the handout at file offset `0x4cd0`.

## 2. Invert the character transform

The routine maps each candidate character through a fixed substitution alphabet, XORs it with `ord('FLARERALF'[i % 9]) + i`, then reverses the 25-element array. The alphabets, in corresponding order, are:

```text
abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789}_{=-
-={_}9876543210ZYXWVUTSRQPONMLKJIHGFEDCBAzyxwvutsrqponmlkjihgfedcba
```

So the inverse first reverses the stored table, XORs each value using its original position, and looks up that character in the second alphabet to find the matching character in the first. The solver also runs the forward transform on its result and requires an exact array match.

## 3. Reproduce

From the challenge repository root, after extracting the ZIP:

```bash
python3 solve.py \
  --binary /path/to/FLRSCRNSVR.SCR
```

It prints the table offset and `CMO{frogt4s7ic_r3vers1ng}`. The literal table match and forward encoding confirm the recovered string against this handout. The supplied source's stated flag agrees; I did not run the Windows configuration dialog.

**Flag:** `CMO{frogt4s7ic_r3vers1ng}`
