---
title: "gdb"
weight: 9
bookToc: true
---

**Use for:** debugging Linux binaries, registers, memory and comparisons.  
**Run in:** WSL. Use x64dbg for native Windows PE debugging.

## Start

```bash
gdb -q ./challenge                         # Open a binary with less startup text
gdb -q --args ./challenge demo             # Also supply its command-line arguments
```

## Useful commands

```text
set pagination off
set disassembly-flavor intel
info files
info functions
break main
run
disassemble main
info registers
x/12i $pc
x/32bx $rsp
x/s $rdi
si
ni
finish
continue
bt
info breakpoints
delete 1
quit
```

| Commands | Purpose |
| --- | --- |
| `break main`, `run` | Stop when main starts |
| `info files`, `info functions` | Find entry points, sections and symbols |
| `disassemble main`, `x/12i $pc` | Read function/current instructions |
| `info registers`, `x/32bx $rsp` | Inspect CPU state and stack bytes |
| `x/s $rdi` | Read a string at the address in a register |
| `si`, `ni` | Step one instruction into / over calls |
| `finish`, `continue` | Run until return / next stop |
| `bt` | Show the call stack |
| `info breakpoints`, `delete 1` | List / remove breakpoints |

Register examples above assume x86-64.

## Walkthrough: inspect a comparison

```text
break strcmp
run
x/s $rdi
x/s $rsi
bt
finish
print $eax
```

This example assumes a dynamically linked Linux x86-64 binary using the System V ABI: the first two pointer arguments are in `rdi` and `rsi`. For `memcmp`, also inspect the byte length in `rdx`; bytes may include NULs.

## Gotchas

- A stripped binary may have no `main` symbol; use `starti`, `info files`, and instruction addresses.
- PIE addresses vary with the load address; derive runtime locations.
- Optimized/inlined comparisons may never call `strcmp`.
- `run < input.txt` supplies stdin from a file.

## Launch flags and memory display syntax

| Syntax | Meaning |
| --- | --- |
| `-q` | Suppress startup banner |
| `--args PROGRAM ARGS...` | Pass remaining arguments to the program |
| `-ex 'COMMAND'` | Execute one debugger command at startup; repeatable |
| `-batch` | Run scripted debugger commands then exit |
| `x/32bx ADDRESS` | Examine 32 units, byte size, hexadecimal format |
| `x/8gx ADDRESS` | Examine eight giant words, hexadecimal; each is eight bytes |
| `x/s ADDRESS` | Interpret memory as a NUL-terminated string |
| `x/10i ADDRESS` | Decode ten instructions |

In `x/32bx`, `32` is count, `b` is byte size and `x` is hex format. These letters belong to GDB’s examine command, not shell flags.

## CTF: find the true entry point in a stripped binary

```text
starti
info files
info proc mappings
x/16i $pc
```

`starti` stops at the first instruction actually executed; for a dynamic binary it may be in the loader. Use module mappings and `info files` to distinguish the loader from the executable.

## CTF: break at a runtime code address

```text
break *0x555555555234
continue
x/12i $pc
```

Replace the address with the observed runtime location. For PIE, relate a disassembler offset to the correct loaded segment; the first mapping address is not always the required ELF load bias.

## CTF: inspect binary compare arguments

```text
break memcmp
run
print $rdx
x/32bx $rdi
x/32bx $rsi
finish
print $eax
```

This is Linux x86-64 System V. `rdx` gives the compared length. Do not use `x/s` alone for buffers that can contain NULs. For Windows x64, the first three arguments normally use RCX/RDX/R8.

## CTF: detect when decoded bytes are written

```text
# First identify an actual writable address during this run
watch *(unsigned int *)0x555555558040
continue
bt
x/32bx 0x555555558040
```

Replace the example address. A watchpoint stops when the watched value changes; hardware slots and supported sizes are limited. Set it after the relevant storage exists and before the transformation executes.

## CTF: search a known mapped region

```text
# Replace both bounds using info proc mappings
find /b 0x555555558000, 0x555555559000, 0x66, 0x6c, 0x61, 0x67, 0x7b
```

The byte pattern is `flag{`. Search a readable range, then inspect each hit. Unmapped gaps can interrupt searching; narrow the region.

## Save decoded memory to a file

```text
dump binary memory decoded.bin 0x555555558100 0x555555558180
```

The stop address is excluded; the example saves `0x80` bytes. Use the actual runtime buffer address and validated length.

## Reproduce stdin and collect a short debugger report

```bash
gdb -q -batch \
  -ex 'set pagination off' \
  -ex 'run < input.txt' \
  -ex 'bt' \
  -ex 'info registers' ./challenge > debug_report.txt 2>&1
```

`-batch` is suitable for a bounded reproducible stop/crash. Interactive protocols may need a live session instead.

## Interpret a failed run

| Observation | Next step |
| --- | --- |
| Breakpoint never hits | Check path, inlining, symbols and runtime address |
| SIGSEGV | Record PC, backtrace, registers and faulting instruction |
| Correct comparison but rejected input | Check later checks and complete success path |
| Different behavior under debugger | Timing, environment, ASLR or debugger checks |
| Program waiting | Inspect expected stdin/protocol rather than assuming a crash |

References: [stepping](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Continuing-and-Stepping.html), [memory search](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Searching-Memory.html), [dumping memory](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Dump_002fRestore-Files.html).
