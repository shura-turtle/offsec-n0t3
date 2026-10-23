---
title: "Ghidra"
weight: 22
bookToc: true
---

**Use for:** static disassembly, decompilation and validation logic.  
**Run in:** WSL GUI per the supplied list. **Listed version:** 12.1.4.

## Launch the supplied installation

```bash
# Run from the installed Ghidra directory
./ghidraRun
```

## Walkthrough: find the input check

1. **File → New Project → Non-Shared Project**.
2. Import the binary, inspect the detected format/architecture, then open it.
3. Accept auto analysis.
4. **Search → For Strings**; search for success/failure text.
5. Follow a string’s references to its caller.
6. Read the **Decompiler** alongside the assembly listing.
7. Identify input, transformations, constants and comparison length.
8. Rename functions/variables and save the project.

## Useful navigation

| Action | Common key/control |
| --- | --- |
| Go to address | G |
| Rename selected symbol | L |
| References to selected item | Right click → References |
| Follow function | Double click |
| Inspect imports/functions | Symbol Tree |
| Show raw bytes | Bytes field / Byte Viewer |

## CTF notes

- Translate the validation loop into Python and reproduce it on known input.
- Check array sizes, signedness and endianness in assembly.
- An entry function is not always `main`; follow startup calls.
- Apply meaningful names as you learn what a value does.

## Gotchas

- Decompiled C is an approximation; verify surprising logic in assembly.
- A wrong architecture or image base gives misleading results.
- Packed/encrypted code may need runtime analysis in gdb/x64dbg.

## CTF: work backward from a success string

1. Search for a distinctive success or rejection string.
2. List every cross-reference; one string can have several callers.
3. Find the branch deciding which message is printed.
4. Trace the compared buffer/value backward to its producer.
5. Record preprocessing: newline stripping, length checks, XOR, encoding or hashing.
6. Reproduce the exact operations in Python.
7. Confirm the generated candidate follows the binary’s full success path.

## CTF: translate a byte validation loop

```c
// Example logic recovered during analysis
for (i = 0; i < length; i++) {
    if ((input[i] ^ 0x23) != expected[i]) return 0;
}
```

The inverse is `input[i] = expected[i] ^ 0x23`. Export the actual array bytes, preserve the iteration count, and test the inverse by reapplying the forward transform.

```python
expected = bytes.fromhex("454f42445847464e4c5e")
candidate = bytes(b ^ 0x23 for b in expected)
assert bytes(b ^ 0x23 for b in candidate) == expected
print(candidate)
```

This produces the worked example `flag{demo}`. Real challenges can combine operations whose inverse order matters.

## Fix the analysis model

| Symptom | Useful correction |
| --- | --- |
| Bytes displayed as undefined data | Define data/code only after confirming the region |
| Buffer shown as scalar integers | Apply an array or pointer type |
| Function prototype looks wrong | Inspect calling convention and call sites |
| Missing string | Try encoded/wide strings or inspect raw data |
| Indirect call unresolved | Trace function pointer/table and verify at runtime |

Renaming and retyping improves readability, but a plausible type can hide a wrong assumption. Check the assembly at boundaries and casts.

## CTF: inspect an embedded resource

Find resource/section references, identify the length and extraction point, then export exactly that range. If the buffer is decrypted only at runtime, use gdb/x64dbg to dump it after the transformation. Static ciphertext will not decompile as the eventual payload.

## Use the Function Graph for branch-heavy checks

Open the graph for the validation function, mark the blocks leading to rejection, and inspect the conditions connecting them. Track constraints in a small table: input index, operation, constant and comparison. This is more reliable than reading a large decompiler expression as one sentence.

## GUI versus CLI

`./ghidraRun` is the GUI launcher. `./` means execute a file in the current directory; it is not an analysis flag. Headless analysis has a separate launcher and project/script arguments. For an interactive tournament solve, the GUI flow above preserves labels, types and references in a saved project.

Reference: [Ghidra beginner guide](https://ghidra.re/ghidra_docs/GhidraClass/Beginner/Introduction_to_Ghidra_Student_Guide.html).

## Related playbooks

- [Deep Ghidra cheatsheet](../../reversing-expl/ghidra-cheatsheet/)
- [Built-ins and optional extensions](../../reversing-expl/ghidra-plugins/)
- [Static analysis](../../reversing-expl/static-analysis/)
