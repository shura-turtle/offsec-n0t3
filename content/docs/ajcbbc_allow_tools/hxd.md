---
title: "HxD"
weight: 35
bookToc: true
---

**Use for:** raw byte inspection, file signatures, offsets and small patches.  
**Run in:** Windows GUI; installer or portable build.

## Walkthrough: inspect a suspicious file

1. **File → Open** the artifact.
2. Compare the first bytes with its claimed format.
3. **Search → Find** → choose **Text-string** or **Hex-values**.
4. Use **Search → Goto** to jump to a known offset.
5. Inspect the data interpreter for selected integer/float values.
6. Save edits as a separate working copy.

## File signatures to recognize

| Format | Leading bytes |
| --- | --- |
| PNG | `89 50 4E 47 0D 0A 1A 0A` |
| JPEG | `FF D8 FF` |
| ZIP local header | `50 4B 03 04` |
| PDF | `25 50 44 46 2D` (`%PDF-`) |
| ELF | `7F 45 4C 46` |
| Windows executable | `4D 5A` (`MZ`); verify the later PE header |

## CTF: repair a known bad header

Compare with the expected format → select the exact damaged bytes → overwrite in a copy → reopen with the relevant viewer/parser. A matching signature alone does not prove the rest of the file is valid.

## Extract a byte range

Use **Edit → Select block** to enter an offset and length, copy the selected bytes into a new file, then save with an appropriate name.

## Gotchas

- Insert mode shifts later offsets; overwrite mode preserves file length.
- Distinguish hexadecimal and decimal offsets in dialogs.
- Endianness matters when interpreting multi-byte numbers.
- Changing PNG data can also require updating checksums.

## CTF: recover an appended object

1. Search for a suspected embedded header using **Hex-values**.
2. Note the offset of every hit.
3. Inspect whether a full structure follows that header.
4. Use **Select block** with a validated start/length.
5. Copy into a new file and save it separately.
6. Open it with the relevant approved parser.

A ZIP signature can appear inside ordinary compressed data. For a ZIP candidate, a parser that lists valid members is stronger evidence than the first four bytes alone.

## CTF: repair a file without shifting its body

Use overwrite mode for a damaged signature. Insert mode adds bytes and moves every later offset. Save a copy and compare its size and changed region with the original.

```text
before: ?? 50 4E 47 0D 0A 1A 0A ...
after:  89 50 4E 47 0D 0A 1A 0A ...
```

This repairs only the first byte in the example. If internal lengths/checksums are wrong, the image may still fail to open.

## CTF: interpret a numeric field

Select exactly the bytes for the field and compare little/big-endian interpretations in the data interpreter. Validate the result against file size or another structural constraint. A decoded length larger than the entire file is a reason to revisit endianness, offset or field width.

## CTF: inspect UTF-16 text

When ASCII bytes alternate with zeroes, try a Unicode text search or inspect with `strings -e l` in WSL. Some Unicode characters use nonzero high bytes, so “every second byte is zero” is only a clue.

## CTF: compare a known-good reference

Open both files and use file comparison. Record changes by offset and length. Compare equivalent structures rather than assuming two different files must have identical headers beyond their format signature.

## GUI equivalents of common CLI tasks

| CLI concept | HxD operation |
| --- | --- |
| `xxd -s OFFSET` | Goto offset |
| `xxd -l LENGTH` | Select a block of the desired length |
| `xxd -r` patch | Overwrite selected bytes in a copy |
| `strings` clue search | Text-string search with correct encoding |
| Carve a range | Select block → copy to new file |

HxD’s menus are not switches to append to a shell command. For repeatable scripting, use xxd/Python and record the exact offsets.

Reference: [HxD features and usage](https://mh-nexus.de/en/hxd/).
