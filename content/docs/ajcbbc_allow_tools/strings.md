---
title: "strings"
weight: 11
bookToc: true
---

**Use for:** quick readable text triage in binaries, images and memory dumps.  
**Run in:** WSL; GNU Binutils.

## Quick commands

```bash
strings -a challenge.bin                       # Scan the whole artifact
strings -a -n 6 challenge.bin                  # Suppress strings shorter than six
strings -a -t x challenge.bin > strings_hex_offsets.txt  # Retain byte offsets
strings -a -e l challenge.bin > utf16le_strings.txt      # Windows-style wide text
strings -a -e b challenge.bin > utf16be_strings.txt      # Big-endian wide text
```

`-a`: whole file. `-n`: minimum length. `-t x`: hexadecimal offsets. `-e l`: 16-bit little endian, often useful for Windows text.

## Walkthrough: hunt a clue

```bash
strings -a -t x challenge.bin > strings.txt
grep -niE 'flag|password|secret|https?://' strings.txt

# Repeat for UTF-16LE
strings -a -e l -t x challenge.bin > wide_strings.txt
grep -niE 'flag|password|secret' wide_strings.txt
```

Use the reported hex offset to inspect nearby bytes:

```bash
# Replace 0x120 with the offset you found
xxd -s 0x120 -l 128 challenge.bin
```

## Gotchas

- No hit does not mean no flag; text may be encrypted, split or compressed.
- A hit may be a decoy or an unrelated string. Verify its context.
- `grep -n` reports the text output line number; `strings -t x` reports the binary offset.
- Huge dumps produce huge output files; start with targeted keywords and encoding choices.

## Flags explained

| Flag | Meaning | Why useful in a CTF |
| --- | --- | --- |
| `-a` | Scan the entire file | Includes data outside normally selected sections |
| `-n 6` | Require at least six printable characters | Reduce short accidental fragments |
| `-t x` | Prefix strings with hexadecimal file offsets | Jump to the original bytes |
| `-t d` | Use decimal offsets | Match tools reporting decimal positions |
| `-e l` | Scan 16-bit little-endian characters | Windows wide strings |
| `-e b` | Scan 16-bit big-endian characters | Big-endian wide text |

The accompanying `grep -n` means output line numbers, `-i` ignores case, and `-E` enables extended regex. Those are grep flags, not strings flags.

## CTF: inspect nearby messages

```bash
# Preserve nearby strings so you can see success/failure context
strings -a -t x challenge | grep -i -C 4 'correct'
strings -a -e l -t x challenge.exe | grep -i -C 4 'password'
```

Here grep’s `-C 4` includes four lines of context before/after each match. A nearby string may be unrelated in control flow; follow references in a disassembler to confirm usage.

## CTF: find endpoints and paths

```bash
strings -a artifact.bin > all_strings.txt
grep -nE 'https?://|/api/|[A-Za-z]:\\' all_strings.txt
```

Look for resource names, configuration paths, usernames and unusual filenames, not only the flag prefix. Use these as search terms in other artifacts.

## CTF: compare two versions

```bash
strings -a before.bin | sort -u > before_strings.txt
strings -a after.bin | sort -u > after_strings.txt
diff -u before_strings.txt after_strings.txt
```

`sort -u` deduplicates and loses original order; keep the offset-preserving files separately. `diff -u` displays the changed lines with context.

## CTF: search extracted memory

Scan a selected process dump from Volatility before the entire memory image. That makes attribution clearer. Search both ordinary and UTF-16LE strings, then return to the memory mapping or process context for a useful hit.

## Interpret the offset

```text
   12a0 Invalid password
```

`12a0` is a byte offset inside the scanned file when using `-t x`. It is not automatically a virtual address or a line number. For ELF/PE files, section mapping is needed to locate the corresponding runtime address.

Reference: [GNU strings manual](https://sourceware.org/binutils/docs/binutils/strings.html).
