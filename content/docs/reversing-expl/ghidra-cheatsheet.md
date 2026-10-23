---
title: "Ghidra Cheatsheet · From Strings to Check"
weight: 2
bookToc: true
---

# Ghidra cheatsheet

**One useful route: import → confirm processor → analyze → success/failure string → xrefs → validator → types/constants → verified input.** Menus and shortcuts can differ by release/keymap; use the action's context menu or Help if a shortcut differs.

![Annotated schematic of Ghidra CodeBrowser: Symbol Tree, Listing, Decompiler, Data Type Manager and Console](/images/reversing/ghidra-layout.svg)

**Annotated layout diagram, not a captured screenshot.** Panels are conceptual and can be docked differently in your installation.

## 1. Import correctly

1. Launch the supplied Ghidra installation and create a **Non-Shared Project**.
2. Import a working copy of the binary. Confirm loader, language, bitness and byte order in the import summary.
3. Open it in CodeBrowser; run Auto Analyze with sensible defaults.
4. Save the project after analysis and as meaningful annotations accumulate.

For a raw blob, Ghidra cannot infer the intended load address/processor reliably. Select the documented architecture and base from the challenge/device model. A wrong choice can produce plausible-looking nonsense.

## 2. Know the panels

| Panel | Use |
| --- | --- |
| Listing | Address, bytes, assembly, data and xrefs; source of truth for instructions |
| Decompiler | Approximate C-like representation of the selected function |
| Symbol Tree / Symbol Table | Functions, imports, exports and labels |
| Data Type Manager | Structures, enums, arrays and imported type archives |
| Function Graph | Basic-block branches in current function |
| Function Call Tree | Callers/callees; indirect calls may be incomplete |
| Defined Strings | Strings already identified as data |
| Byte Viewer | Exact selected bytes and alternate representations |
| Bookmarks | Analysis errors and your investigation markers |
| Console / Script Manager | Script output and installed local scripts |

Open missing panels from **Window**. Double-click addresses/functions to follow them and use navigation history to return. Windows being closed does not erase the underlying program annotations.

## 3. Fast navigation

| Task | Action |
| --- | --- |
| Jump to address/symbol | `G` / Go To |
| Rename label/function | `L` in Listing or context-menu Rename |
| Inspect references | Right click selected item → References → Show References To |
| Open decompiler | Window → Decompiler |
| Show graph | Window → Function Graph |
| Search already defined strings | Window → Defined Strings |
| Discover additional strings | Search → For Strings |
| Search literal/byte pattern | Search → Memory; choose appropriate format |
| Create instruction | Disassemble action, commonly `D` in Listing |
| Clear incorrect code/data | Clear Code Bytes action; check scope before applying |
| Create function | Function → Create Function after correct disassembly |
| Add evidence comment | Context-menu Comments; use repeatable address-linked notes |

Avoid memorizing a key without knowing its focused panel. The same key can have different meaning in the decompiler, listing and table filter.

## 4. Find main when symbols are stripped

- Check Symbol Tree for `main`, `WinMain`, exported handlers and language-specific entry routines.
- If absent, start from input prompts and success/failure string references.
- ELF entry `_start` often hands a main-function pointer to runtime startup; inspect the actual call arguments rather than assuming entry is main.
- Windows entry includes runtime setup; GUI checks may live in message handlers/callbacks, not main.
- Go/Rust/C++ runtimes can contribute thousands of functions. Work from challenge-specific strings and reachable callers.

Record the validator address even before naming it. Rename `FUN_...` to `validate_input` only after its role is established.

## 5. Follow strings to logic

1. Search for a distinctive prompt or rejection message.
2. Select the string's start and show **all** references.
3. Open each referencing function; check if the reference is data, direct code, or a pointer table.
4. Identify the conditional branch choosing success vs failure.
5. Trace the compared value backward to input and expected constants.
6. Follow callers to find length checks and preprocessing outside the validator.

No xrefs may mean pointers are built dynamically, references are missed, or the string is unused/decoy data. A shared message may have several unrelated callers.

## 6. Make the decompiler useful

Typical improvements:

```text
param_1 → input
param_2 → input_len
local_28 → transformed
DAT_... → expected_bytes
FUN_... → decode_table
```

Then retype evidence-backed values:

| Misleading display | Correct after inspection |
| --- | --- |
| `undefined8` receiving a pointer | `char *`, `uint8_t *`, struct pointer |
| Repeated scalar locals form a buffer | Fixed-size byte array |
| Sign-extended byte arithmetic | `int8_t`/`uint8_t` as assembly requires |
| Integer bit flags | Named enum/mask |
| Pointer plus repeated offsets | Structure with field offsets |

Right-click a variable in Decompiler for Rename/Retype. Edit Function Signature for parameters, return type and calling convention. Use Data Type Manager for arrays/structs; apply them in the Listing. A guessed type can hide errors, so verify at loads, stores, casts and call boundaries.

## 7. Export expected arrays

If bytes are displayed as undefined or individual scalars, determine range and width from references/loop bounds. Apply an array type only after confirming the region.

Example evidence:

```c
for (i = 0; i < 9; i++) {
    if ((input[i] ^ 0x23) != expected[i]) return 0;
}
```

Select exactly 9 bytes at `expected`; use Byte Viewer / Copy Special byte export or an available binary export action. Verify exported length and starting byte. Display formatting and export options vary; plain copy may include addresses/text instead of raw bytes.

```python
expected = bytes.fromhex('454f42445847464e4c')
answer = bytes(b ^ 0x23 for b in expected)
assert bytes(b ^ 0x23 for b in answer) == expected
print(answer)  # b'flag{demo'
```

This fixture is intentionally 9 bytes and lacks `}`; **length is evidence**, not a reason to invent a missing byte. The 10-byte complete demo is `454f42445847464e4c5e`.

If exporting by file offset externally, map VA/RVA to file offset correctly. Uninitialized data and runtime-decrypted buffers may have no corresponding disk bytes. [Strings/encodings](../strings-encodings/) explains address mapping.

## 8. Read control flow and data flow

Use Function Graph to mark rejection blocks and identify constraints. A branch condition in decompiled C can be inverted relative to the success path. Check the actual jump destination.

For indirect calls/jump tables, inspect table base, entry width, relative-vs-absolute interpretation and bounds. Do not create functions at arbitrary table contents without validating executable memory targets.

For byte operations, record **where truncation occurs**. `(uint8_t)(a+b)` is not equivalent to an unlimited Python integer if later shifts/comparisons use that byte. [Static analysis](../static-analysis/) has width/ABI tables.

## 9. Patch carefully and export separately

Use **Patch Instruction** or patch bytes in a project copy to test a hypothesis. Record original bytes, patched bytes and why the change helps. Patching a branch can reveal downstream code; it may skip state/key setup necessary to decrypt the real flag.

Saving the Ghidra project saves its database, **not necessarily a rewritten executable**. File → Export Program offers exporters whose capabilities differ. An original-file-format exporter may support selected changes; a raw binary exporter is not a complete ELF/PE reconstruction. Reopen exported output, inspect changed bytes and execute only in the challenge environment.

## 10. Useful built-in analysis

Use known library signatures / Function ID to reduce runtime noise, call trees for call-site relationships, and Version Tracking for annotations across two matching builds. BSim similarity needs an appropriate function corpus; it does not infer a flag automatically. [Plugin notes](../ghidra-plugins/) distinguish these from external extensions.

## 11. Troubleshooting

| Symptom | Check |
| --- | --- |
| Every function looks wrong | Language, bitness, byte order, image base and loader |
| Large `unaff_...` / missing arguments | Calling convention, prototype, function boundary |
| Constant shown negative | Signedness and operand width |
| Missing function | Correct entry disassembly, reachability, indirect reference |
| String missing | Wide strings, short length, untyped data, runtime decode |
| Pseudocode contradicts runtime | Assembly, initialized state, relocation and packing |
| Exported file not runnable | Exporter format, missing headers/sections, patch offset |

## Tool links and references

[Supplied Ghidra page](../../ajcbbc_allow_tools/ghidra/), [GDB](../../ajcbbc_allow_tools/gdb/), [HxD](../../ajcbbc_allow_tools/hxd/), [LLVM MC](../../ajcbbc_allow_tools/llvm_mc/). Official learning: [Ghidra beginner guide](https://ghidra.re/ghidra_docs/GhidraClass/Beginner/Introduction_to_Ghidra_Student_Guide.html), [Ghidra repository and installation documentation](https://github.com/NationalSecurityAgency/ghidra).
