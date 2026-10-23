---
title: "Triage · First Five Minutes"
weight: 1
bookToc: true
---

# Reversing triage

**Before decompiling: what format is it, what architecture, what runtime, and can this machine execute it?** Preserve an original and analyze a copy.

## 1. Identify the file

Linux/WSL examples, when these standard utilities are available:

```bash
sha256sum challenge
file challenge
xxd -l 64 challenge
strings -a -n 5 challenge
strings -a -e l -n 5 challenge
```

`-a` scans all bytes; `-n 5` sets minimum string length; GNU strings `-e l` selects 16-bit little-endian strings. A Windows strings implementation may use different flags. [strings guide](../../ajcbbc_allow_tools/strings/), [xxd guide](../../ajcbbc_allow_tools/xxd/).

| Header / structure | Interpretation |
| --- | --- |
| `7f 45 4c 46` | ELF; inspect class, endianness and machine |
| `4d 5a` plus valid PE header | Windows PE; may be native or managed |
| `cf fa ed fe` / related Mach-O magic | Apple binary; architecture from header |
| `50 4b 03 04` | ZIP container; possibly JAR/APK/Office/archive |
| `.pyc` magic / Python bundle | Version-specific bytecode/container analysis |
| No recognizable header | Raw blob, compressed/encrypted data or custom format |

A renamed extension is not format evidence. A PE file containing `.NET` strings is a hint; confirm the CLR runtime header/metadata in a managed-aware tool.

## 2. Inspect sections and imports

```bash
objdump -f challenge
objdump -h challenge
objdump -x challenge
objdump -d -M intel challenge
```

`-f`: file/architecture header; `-h`: section headers; `-x`: all available headers; `-d`: code sections. `-M intel` is for x86 syntax. GNU objdump supports formats compiled into that installation; don't expect it to read every Mach-O file. [objdump](../../ajcbbc_allow_tools/objdump/).

Useful import hints:

| Import / symbol | Lead |
| --- | --- |
| `strcmp`, `memcmp`, `strncmp` | Input/expected comparison; inspect length and preprocessing |
| `fgets`, `scanf`, `read`, `ReadFile` | Input acquisition and buffer layout |
| `CryptDecrypt`, EVP APIs | Crypto path; arguments/IV/mode matter |
| `VirtualAlloc`, `VirtualProtect`, `mprotect` | Runtime code or unpacking possible |
| `ptrace`, `IsDebuggerPresent` | Debugger detection candidate |
| `GetProcAddress`, `dlsym` | Runtime import resolution |

Imports can be absent in static/inlined code; their absence does not exclude a behavior.

## 3. Can you run it?

| Target | Suitable environment |
| --- | --- |
| Linux ELF x86-64 | Matching Linux runtime / WSL, subject to dependencies |
| Windows PE x64 | Matching Windows environment; x64dbg for native code |
| .NET assembly | Matching managed runtime and architecture; dnSpyEx for inspection |
| macOS Mach-O | Matching macOS/runtime; do static analysis elsewhere |
| ARM firmware/raw code | Correct loader/architecture; emulator needs memory/peripheral model |

An executable bit does not fix an architecture or OS mismatch. Missing `ld-linux` or libraries can look like “No such file” even when the binary exists. Runtime execution belongs in the challenge VM, not your everyday environment.

## 4. Search for anchors

Search success/failure text, prompts, file paths, format strings, alphabet tables and crypto constants. For every promising string:

```text
String location → all xrefs → printing caller → deciding branch → producer of compared value
```

A visible `flag{...}` might be a decoy. Determine whether a reachable path prints it and whether it matches the event's actual flag format.

## 5. Packed or encrypted?

Hints include a tiny import set, high-entropy data, an unusual entry stub and code written into an executable allocation. These are hints, not a definitive packer identification. Entropy alone cannot distinguish encryption from compression.

If Ghidra shows a short decoder followed by an indirect jump, inspect [dynamic debugging](../dynamic-debugging/) and dump the produced code/data after initialization. Wrong language or image base can also produce nonsense disassembly; rule that out first.

## 6. Stop triage when you can state the plan

```text
Native PE x64, checked flag.
Input from an edit box; failure string points to validate().
validate() compares 24 transformed bytes with a .rdata array.
Next: export that array and model byte arithmetic.
```

Do not read every startup function before identifying the challenge logic. Move to [Ghidra](../ghidra-cheatsheet/), [.NET](../dotnet/) or [static analysis](../static-analysis/) based on evidence.

## References

[GNU objdump](https://sourceware.org/binutils/docs/binutils/objdump.html), [GNU strings](https://sourceware.org/binutils/docs/binutils/strings.html), [Microsoft PE/COFF format](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format).
