---
title: "Corrupted"
date: 2026-10-26T01:53:00+06:30
bookToc: true
description: "Remove ten prefixed bytes and repair the MZ signature of a damaged PE executable."
---

# Corrupted

## Original illustrated walkthrough

The pages below reproduce the supplied PDF in order, including every screenshot and code image. Select a page to open it at full size. [Download the original PDF](/writeups_ctf/reversing/corrupted/source.pdf).

### Page 1: Malformed PE header, repair steps, and flag

[![corrupted PDF page 1: Malformed PE header, repair steps, and flag](/writeups_ctf/reversing/corrupted/page-1.jpg)](/writeups_ctf/reversing/corrupted/page-1.jpg)

## Searchable solve steps

The challenge asks for `corrupted.exe` to be repaired and run without arguments. Only its PDF walkthrough was available here; the executable was not included for a fresh run.

## 1. Inspect the first bytes

The PDF shows the damaged header beginning:

```text
00000000: 00 04 99 01 40 01 B1 A3 00 00 5A 5A ...
```

The first ten bytes are extra data. After removing them, the file begins `5A 5A` (`ZZ`), while a PE file must begin `4D 5A` (`MZ`).

## 2. Repair and run

This script performs exactly those two edits and preserves the rest of the file:

```python
from pathlib import Path

data = bytearray(Path("corrupted.exe").read_bytes())
assert data[:12] == bytes.fromhex("00 04 99 01 40 01 b1 a3 00 00 5a 5a")
repaired = data[10:]
repaired[0] = 0x4D
Path("repaired.exe").write_bytes(repaired)
```

Run `repaired.exe` with no arguments on a Windows analysis system. The PDF reports that it prints:

```text
CSG_FLAG{finding_the_magic_now!}
```

The repaired executable is also used by the [Flag Encoder](flag-encoder/) challenge.

