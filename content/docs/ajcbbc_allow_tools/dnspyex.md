---
title: "dnSpyEx (dnSpy)"
weight: 38
bookToc: true
---

**Use for:** decompiling/debugging managed .NET applications and assemblies.  
**Run in:** Windows portable build. The supplied list specifies the self-contained win64 package.

## Open an assembly

```powershell
# Run from the extracted dnSpy directory
.\dnSpy.exe 'C:\CTF\challenge.exe'
```

## Walkthrough: recover a .NET check

1. Open the EXE/DLL and expand the assembly tree.
2. Find the entry point or UI event handler, such as a button click.
3. Search strings for success/failure messages or the expected flag prefix.
4. Follow the check into its methods and inspect constants/resources.
5. Set a breakpoint before or after a transformation.
6. Start debugging through **Debug → Start** with the proper runtime/arguments.
7. Inspect locals, arguments and decoded arrays at the breakpoint.
8. Reproduce the algorithm or save the relevant decoded bytes.

## Places to inspect

| Location | Possible clue |
| --- | --- |
| `Main` / startup code | Argument checks, initialization |
| UI event handlers | Password/serial validation |
| Static constructors | Hidden constants, initialization routines |
| Resources | Embedded files and encrypted payloads |
| `Convert.FromBase64String` callers | Encoded values |
| Crypto API callers | Mode, key, IV and transformation |

## Editing a working copy

Use **Edit Method** or IL editing when available, then **Save Module** to a separate file. Record the original logic first.

## Gotchas

- Native binaries need Ghidra/x64dbg instead.
- Obfuscation can make decompiled C# misleading; inspect IL and runtime values.
- A forced success branch can bypass the computation needed for the real flag.
- Target runtime requirements are separate from the debugger’s own self-contained package.

## CTF: find the actual validator

Search for a message or UI control, then follow event subscriptions/callers. In a GUI challenge, `Main` may only create the window; the password check can be in `button_Click`, a callback or a helper class.

Create a small record of input normalization, length checks, transformations and final comparison. Check whether the comparison is text, byte sequence or hash.

## CTF: recover constants initialized at runtime

1. Find the type’s static constructor or initializer.
2. Set a breakpoint after its decode routine returns.
3. Start the correct target under the debugger.
4. Inspect static fields and relevant locals.
5. Save decoded byte-array values using the variable/memory controls.
6. Record the exact algorithm and key source.

A field displayed as encrypted data in the decompiler can become plain text only after initialization.

## CTF: resource extraction

Expand Resources and inspect names/types. Export a candidate resource, preserve its raw bytes and check its signature with HxD. Resource streams may be compressed, encrypted or custom-framed; use the loading function to determine the next decode step.

## CTF: translate .NET byte operations carefully

```csharp
// Example transform
output[i] = (byte)((input[i] + 7) ^ 0x55);
```

Equivalent forward/inverse operations in Python:

```python
forward = lambda b: ((b + 7) & 0xff) ^ 0x55
inverse = lambda b: ((b ^ 0x55) - 7) & 0xff
assert all(inverse(forward(b)) == b for b in range(256))
```

The cast truncates to a byte. Signed integers, `char` width and checked arithmetic can change behavior; preserve the original types.

## When C# decompilation is confusing

Switch to IL view for the exact operations and branch targets. Trace locals and stack effects around the critical routine. An obfuscator can produce code that is legal IL but misleading or awkward as reconstructed C#.

## Debugging checklist

| Observation | Next check |
| --- | --- |
| Cannot load as managed assembly | Native file, packing or corruption |
| Breakpoint not reached | Wrong handler/type, initialization already completed |
| Missing dependency | Target’s runtime/assembly search path |
| Byte array visible but text wrong | Encoding and postprocessing |
| Success after patch, rejected submitted flag | Recover computed value from the real path |

## Launcher arguments versus debugger controls

In `.\dnSpy.exe 'C:\CTF\challenge.exe'`, the path is a positional file argument. `.\` refers to the current Windows directory. Breakpoints and stepping are debugger actions, not Linux-style `-r`/`-d` flags.

Reference: [dnSpyEx project and debugger features](https://github.com/dnSpyEx/dnSpy).
