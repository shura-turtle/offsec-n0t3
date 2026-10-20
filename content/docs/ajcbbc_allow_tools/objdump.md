---
title: "objdump"
weight: 10
bookToc: true
---

**Use for:** headers, sections, imports, symbols and disassembly.  
**Run in:** WSL; supplied by GNU Binutils.

## Quick commands

```bash
objdump -f challenge
objdump -h challenge
objdump -t challenge
objdump -T challenge
objdump -p challenge
objdump -d -M intel challenge > disassembly.txt
objdump -s -j .rodata challenge
```

| Option | Meaning |
| --- | --- |
| `-f` | File/architecture headers |
| `-h` | Section headers |
| `-t` / `-T` | Symbols / dynamic symbols |
| `-p` | Format specific headers, including PE import information |
| `-d` | Disassemble code sections |
| `-s -j NAME` | Dump a selected section |

## Walkthrough: find validation logic

```bash
objdump -d -M intel --disassemble=main challenge
objdump -d -M intel challenge > disassembly.txt
grep -n -E 'strcmp|memcmp|scanf|fgets' disassembly.txt
```

Read the surrounding calls, branches and referenced constants. Move into Ghidra or gdb for data flow and runtime values.

## Raw x86-64 bytes

```bash
objdump -D -b binary -m i386:x86-64 -M intel code.bin
```

## Gotchas

- File offsets and virtual addresses are different.
- `-D` can decode data as instructions; plausible assembly is not proof of code.
- `-M intel` is relevant to x86 targets.
- Supported architectures/formats depend on the installed Binutils build; inspect `objdump -i`.

## Additional flags explained

| Flag | Meaning |
| --- | --- |
| `-D` | Disassemble all sections, including sections that may be data |
| `-M intel` | Use Intel syntax for x86 disassembly |
| `-j NAME` | Select a named section |
| `--disassemble=NAME` | Disassemble a particular symbol |
| `--start-address=ADDR` | Begin output at a virtual/section address |
| `--stop-address=ADDR` | Stop at the specified address |
| `-b binary` | Treat input as a raw binary blob |
| `-m ARCH` | Select a machine architecture |
| `-i` | List supported formats and architectures |

`--start-address` is not a byte seek into the file. For raw blobs you choose the address model; for ELF/PE input follow its section addressing.

## CTF: inspect only a suspect code range

```bash
# Example addresses from an analysis session; replace them
objdump -d -M intel --start-address=0x401100 \
  --stop-address=0x401180 challenge
```

Read callers, constants and branch conditions around the comparison. Do not infer the expected input from one instruction without following the data flow.

## CTF: inspect read-only data and initialized globals

```bash
objdump -h challenge
objdump -s -j .rodata challenge
objdump -s -j .data challenge
```

Section names are not universal; PE often uses `.rdata` rather than `.rodata`. Use the names printed by `-h`.

## Convert section addresses to file offsets

If a section has VMA `0x402000`, file offset `0x2000`, and a referenced address is `0x402123`, the corresponding file offset is:

```text
file offset = 0x2000 + (0x402123 - 0x402000) = 0x2123
```

Apply this only inside that section’s file-backed range. Zero-initialized storage may have no equivalent input bytes. PIE runtime addresses require subtracting the correct load bias first.

## CTF: locate imported Windows APIs

```bash
objdump -p challenge.exe > pe_headers.txt
grep -niE 'DLL Name|GetProcAddress|LoadLibrary|VirtualAlloc' pe_headers.txt
```

Imports help choose investigation points. Their presence alone does not establish which execution path uses them.

## Recognize common validation patterns

| Pattern | What to trace |
| --- | --- |
| XOR/add/rotate inside a byte loop | Key, iteration count and output compare |
| Call to strcmp/memcmp | Both arguments and exact length |
| Length test before a loop | Required input bytes, newline handling |
| Table lookup | Index width and signedness |
| Several arithmetic checks | Constraints shared across input positions |

Reference: [GNU objdump manual](https://sourceware.org/binutils/docs/binutils/objdump.html).
