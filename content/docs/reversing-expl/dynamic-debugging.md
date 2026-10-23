---
title: "Dynamic Debugging · Break, Inspect, Dump"
weight: 5
bookToc: true
---

# Dynamic debugging

**Ask a narrow question, stop at the relevant instruction, inspect exact bytes, then verify the original program.** Use the challenge VM/runtime and keep an unmodified executable copy.

## 1. Choose the debugger

| Binary | Tool |
| --- | --- |
| Native Linux ELF | [GDB](../../ajcbbc_allow_tools/gdb/) |
| Native Windows PE | [x64dbg / x32dbg](../../ajcbbc_allow_tools/x64dbg/) matching bitness |
| Managed .NET | [dnSpyEx](../../ajcbbc_allow_tools/dnspyex/) |
| Cross-platform Ghidra mapping | [Ghidra Debugger / optional sync](../ghidra-plugins/) with supported backend |

A native debugger can inspect CLR runtime code, but dnSpyEx exposes managed methods, metadata and locals more directly. A decompiled address is not automatically a runtime address under ASLR.

## 2. GDB first session

```text
gdb -q ./challenge
set pagination off
set disassembly-flavor intel
starti
info files
info proc mappings
x/12i $pc
info registers
```

`starti` stops at an initial instruction; this may be in the dynamic loader. If symbols exist, `break main` then `run` is more direct. `info proc mappings` is platform-dependent, especially outside Linux. `set disassembly-flavor intel` is x86-specific.

## 3. Stable breakpoints under PIE/ASLR

With symbols:

```text
break validate_input
run
```

Without symbols, determine the loaded module's base and translate a known RVA:

```text
set $base = 0xACTUAL_MODULE_BASE
break *($base + 0xVALIDATOR_RVA)
continue
```

The uppercase placeholders are not valid numeric GDB commands; replace them. RVA is static address minus the static image base. Do not copy the lowest mapping address blindly when an ELF segment has a nonzero file/virtual offset. Check one instruction's bytes against the static listing.

## 4. Stop at comparison arguments

For a Linux x86-64 SysV program using memcmp:

```text
break memcmp
run
x/32bx $rdi
x/32bx $rsi
p/x $rdx
bt
```

At function entry, RDI/RSI point to buffers, RDX is length. For Windows x64 use RCX/RDX/R8. For `strcmp`, use `x/s` only after checking pointers are readable and actually NUL-terminated.

Library breakpoints may hit unrelated startup comparisons or optimized implementations. Use call-site breakpoints in the validator to remove that noise. Inlined comparisons have no imported call to break on.

## 5. Step and inspect

```text
x/10i $pc
si
ni
finish
p/x $rax
x/16bx $rsp
bt
```

`si` steps one machine instruction including calls; `ni` steps over calls; `finish` runs until the current function returns. When stopped after a comparison, inspect the deciding branch rather than assuming zero/nonzero means success in this application.

Hardware watchpoints can identify a writer:

```text
watch *(unsigned char *)0xACTUAL_BUFFER_ADDRESS
continue
```

Use a verified address and appropriate width. Hardware watchpoints are limited; large ranges may not be supported.

## 6. Dump a decoded buffer

After locating a real buffer and length:

```text
set $buf = $rsi
set $len = 32
x/32bx $buf
dump binary memory decoded.bin $buf ($buf+$len)
```

That example uses RSI only if your current stop actually has the decoded buffer there. Memory dump end is exclusive. Do not use `x/s` to export binary data with embedded NULs. Refetch a pointer after reallocations; old stack/register values may no longer refer to the decoded bytes.

## 7. x64dbg manual flow

1. Open the target in x64dbg for 64-bit or x32dbg for 32-bit code.
2. Run past system/entry breakpoints into the module; confirm current module/address.
3. Use module view and Symbols to find imports, or navigate to module base + validator RVA.
4. Set a breakpoint on the validator/call site, run with controlled input and inspect Registers.
5. Follow argument pointers in Dump; use matching ASCII/Unicode/hex view.
6. Step past decode/check routines and inspect the output buffer.
7. Select the exact Dump range and save binary data through the available dump/save action.

Common default keys: F2 breakpoint, F7 step into, F8 step over, F9 run. Confirm your installed keymap. Patches are managed separately from ordinary memory display; saving a debug database is not automatically a patched executable.

## 8. dnSpyEx managed flow

Open assembly, locate entry point or button handler, set a managed method/line breakpoint and start with the appropriate runtime. Inspect locals/arguments and step into the check/decrypt function. Compiler-generated async state machines may move logic into `MoveNext`; follow call sites and actual IL when C# looks odd.

Read [the .NET page](../dotnet/) for resources, static constructors, IL widths and edited assemblies.

## 9. Anti-debug and self-modifying code

If execution diverges under a debugger, identify the exact predicate rather than disabling everything. Compare normal vs debug path, return value and state changes. Timing checks, process inspection and exception behavior can each matter.

A temporary local branch/return patch can help observe later code; log the original bytes and expected side effects. If the flag key depends on the skipped branch's state, a success banner can accompany invalid output. After runtime unpacking, dump the relevant code/data and reanalyze with correct base/relocations.

## 10. Reproduce cleanly

Save the input bytes, breakpoint addresses as RVAs, initialization prerequisites, decoded buffer length and model result. Restart the original program with the recovered candidate. If input includes binary bytes, preserve them in a file rather than relying on shell quoting.

## References

[GDB machine instructions](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Machine-Code.html), [GDB memory](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Memory.html), [x64dbg manual](https://help.x64dbg.com/en/latest/), [dnSpyEx](https://github.com/dnSpyEx/dnSpy).
