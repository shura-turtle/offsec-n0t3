---
title: ".NET · dnSpyEx, Resources & IL"
weight: 8
bookToc: true
---

# .NET reversing

**Confirm managed metadata → find entry/event handler → read validation → inspect resources/static initialization → verify IL when C# is unclear.** A PE extension alone does not identify managed code.

## 1. Open the right thing

Use [dnSpyEx](../../ajcbbc_allow_tools/dnspyex/) for a managed executable or DLL. Check assembly/module metadata, references and namespaces. A native launcher may load a separate managed DLL; single-file or protected bundles may need extraction using the runtime's actual packaging format.

If dnSpyEx cannot load metadata and Ghidra shows normal native code, reconsider whether it is a native PE, NativeAOT build, mixed-mode assembly or packed container. Do not assume every C#-related filename retains decompilable IL.

## 2. Find the user-controlled path

| Application | Useful anchor |
| --- | --- |
| Console | Entry point / `Main` and input calls |
| WinForms | Button click handler, text box reads, designer event hookup |
| WPF | Event handlers / commands / XAML-associated classes |
| Library | Exports/public API used by provided harness |
| Async program | Generated state machine `MoveNext` |

Search distinctive success/failure strings. Use Analyze / references on the containing method. A name such as `CheckPassword` may be genuine, obfuscated or a decoy; follow actual call sites.

## 3. Record .NET text and numeric semantics

.NET `string` is UTF-16 code units; `s.Length` is not UTF-8 byte length and is not necessarily Unicode character count. `Encoding.UTF8.GetBytes` explicitly converts to bytes. `char` is 16-bit; `byte` is 8-bit.

```csharp
byte[] b = Encoding.UTF8.GetBytes(input);
for (int i = 0; i < b.Length; i++)
    b[i] = (byte)(b[i] ^ 0x23);
```

A matching Python model must encode input as UTF-8 before byte operations. For ASCII flags, code unit and byte values often coincide; that does not make them interchangeable for arbitrary Unicode.

## 4. Static constructors and resources

A field's apparent default value may be replaced by `.cctor` before validation. Inspect type initializers, `RuntimeHelpers.InitializeArray`, resource streams and helper decryptors.

Resource extraction route:

```text
Assembly tree → Resources → selected entry → save/export
```

Use the available context-menu action in your installed version. A `.resources` container can hold strings, byte arrays and serialized values; exporting it does not automatically decode every contained object. Confirm type/length before interpreting it as ciphertext.

A common path is `GetManifestResourceStream` → decompression → decryption → `Assembly.Load`. Capture the bytes at the stage relevant to your question. A decoded managed assembly can often be reopened in dnSpyEx.

## 5. Read IL when decompiled C# is misleading

| IL | Interpretation |
| --- | --- |
| `ldstr` | Load string literal |
| `ldc.i4` / `ldc.i8` | Load integer constant |
| `ldarg`, `ldloc`, `stloc` | Load argument/local, store local |
| `ldelem.u1` | Load array element as unsigned byte |
| `conv.u1` | Truncate/convert to unsigned byte |
| `xor`, `add`, `sub` | Width depends on stack types/conversions |
| `brtrue`, `brfalse` | Conditional branch on stack value |
| `ceq`, `cgt`, `clt` | Comparison result; unsigned variants matter |
| `call`, `callvirt` | Call target/dispatch and instance semantics |

Inspect the instruction before a branch and its target. An inverted C# `if` can be equivalent to the original flow. Overflow-checked operations and conversion variants can throw rather than wrap.

## 6. Debug managed checks

Set a breakpoint in the validator or immediately after decryption. Start with the appropriate CLR/runtime and bitness. Inspect Locals, Watch and call stack; step through until the compared byte array is populated. Save the array without converting arbitrary bytes through a lossy text encoding.

For a GUI app, input may be trimmed, normalized or transformed in the event handler before entering the check. Capture both original text and actual validator argument.

## 7. Editing is a hypothesis tool

Edit Method in C# or IL only in a copy. Save the modified module using the tool's module-save action and note any strong-name/signature implications. Recompile errors can come from unresolved references or decompiler reconstruction, not necessarily wrong logic; small IL edits sometimes fit better than rebuilding an entire method.

A patched return value can expose a later page, but may skip real state/key generation. The valid input and flag still need independent verification against the original program.

## 8. Obfuscation leads

- Renamed identifiers: follow string references and actual data flow.
- String decryptors: inspect one call and the returned string after initialization.
- Control-flow flattening: recover dispatcher state/transitions.
- Reflection: inspect method/type names and resolved target at runtime.
- Anti-tamper: static bytes may be decrypted/validated before use.

Do not execute unknown companion tools or install an old “universal deobfuscator” on the assumption it matches the protection. The supplied debugger often answers a narrow data question without a full deobfuscation pass.

## References

[dnSpyEx repository](https://github.com/dnSpyEx/dnSpy), [Microsoft IL opcode reference](https://learn.microsoft.com/en-us/dotnet/api/system.reflection.emit.opcodes), [Microsoft PE format](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format), [System.String](https://learn.microsoft.com/en-us/dotnet/api/system.string).
