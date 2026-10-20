---
title: "llvm-mc (LLVM tools)"
weight: 27
bookToc: true
---

**Use for:** assembling instructions and decoding short byte sequences across architectures.  
**Run in:** WSL. Some distributions name the executable `llvm-mc-VERSION`.

## Inspect the installed targets

```bash
llvm-mc --version
llvm-mc --help
```

## x86-64: instruction → bytes

```bash
printf 'mov eax, 42\nret\n' | llvm-mc \
  --triple=x86_64-pc-linux-gnu --x86-asm-syntax=intel --show-encoding
```

Use this to confirm a candidate instruction’s encoding while reading a CTF binary.

## x86-64: bytes → instruction

```bash
printf '0x90 0xc3\n' | llvm-mc \
  --triple=x86_64-pc-linux-gnu --disassemble --output-asm-variant=1
```

The example decodes a NOP followed by RET. The disassembler input is textual hex bytes.

## AArch64 encoding

```bash
printf 'mov x0, #42\nret\n' | llvm-mc \
  --triple=aarch64-linux-gnu --show-encoding
```

## Write an object file

```bash
llvm-mc --triple=x86_64-pc-linux-gnu --filetype=obj input.s -o output.o
objdump -d -M intel output.o
```

## Gotchas

- An object file has headers and possibly relocations; it is not a raw byte blob.
- Match architecture, bitness, instruction mode and endianness.
- Some instructions need extra CPU features enabled.
- llvm-mc does not execute or emulate the instructions.

## Flags explained

| Flag | Meaning |
| --- | --- |
| `--triple=TARGET` | Select architecture/vendor/OS target |
| `--x86-asm-syntax=intel` | Parse Intel-style x86 input |
| `--show-encoding` | Print emitted instruction bytes |
| `--disassemble` | Interpret text byte values as machine instructions |
| `--output-asm-variant=1` | Select Intel-style output for x86 |
| `--filetype=obj` | Write a relocatable object file |
| `-o FILE` | Set the output filename |
| `--version` | Print version and available targets |

The target must match the challenge. Selecting x86-64 does not correctly decode a 32-bit instruction stream in every case.

## CTF: compare instruction encodings

```bash
printf 'xor eax, eax\nret\n' | llvm-mc \
  --triple=x86_64-pc-linux-gnu --x86-asm-syntax=intel --show-encoding
```

Use encoding output to check the bytes seen in a disassembler or to understand a small local patch. Replacing instructions also requires respecting their original total length and surrounding control flow.

## CTF: decode several candidate byte sequences

```bash
printf '0x31 0xc0 0xc3\n' | llvm-mc \
  --triple=x86_64-pc-linux-gnu --disassemble --output-asm-variant=1
```

This decodes `xor eax,eax; ret` in the specified mode. A valid decoding does not establish that those bytes execute in the target.

## CTF: translate syntax for reading

```bash
# AT&T input by default, Intel display variant for x86 output
printf 'movl $42, %%eax\nretq\n' | llvm-mc \
  --triple=x86_64-pc-linux-gnu --output-asm-variant=1
```

The doubled `%%` belongs to shell `printf`, which emits a literal `%`. Assembly source files would use `%eax` directly.

## Cross-architecture workflow

1. Identify architecture, bitness and endianness from the artifact.
2. Check that `llvm-mc --version` lists an appropriate target.
3. Assemble/decode a short known instruction first.
4. Inspect only a bounded suspect sequence.
5. Move to Ghidra or a supported debugger for control/data flow.

## Common failure causes

| Symptom | Likely check |
| --- | --- |
| Unknown instruction | Wrong syntax, target or missing CPU feature |
| Unexpected disassembly | Wrong bitness/endianness or decoding data |
| Object bytes include extra headers | Object output is not a raw shellcode blob |
| Address-relative instruction differs | Relocation/link context |

Reference: [LLVM llvm-mc manual](https://llvm.org/docs/CommandGuide/llvm-mc.html).
