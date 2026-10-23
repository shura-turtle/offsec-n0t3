---
title: "x64dbg"
weight: 33
bookToc: true
---

**Use for:** native Windows executable debugging, comparisons and runtime decoding.  
**Run in:** Windows portable build. Use x64dbg for 64-bit, x32dbg for 32-bit targets.

## Launch with a target

```powershell
# Run from the extracted debugger folder; adjust the actual location
.\x64dbg.exe 'C:\CTF\challenge.exe'
```

## Useful controls

| Action | Default key |
| --- | --- |
| Open executable | F3 |
| Run / continue | F9 |
| Toggle breakpoint at selection | F2 |
| Step into | F7 |
| Step over | F8 |
| Execute until return | Ctrl+F9 |
| Restart | Ctrl+F2 |

## Walkthrough: find the check

1. Open the executable and run to its relevant code.
2. In the CPU disassembly, search the current module for string references.
3. Find the failure/success message and follow its references.
4. Set a breakpoint near the input comparison and run with a test value.
5. Inspect registers, stack and pointed-to memory.
6. Follow decoded strings or buffers in the dump view.
7. Record the transformation and reproduce it in Python.

## Debugger command bar examples

```text
bp kernel32.GetProcAddress
bp kernel32.LoadLibraryA
```

These help locate dynamically resolved APIs when the relevant exports are loaded and resolvable.

## Gotchas

- Windows x64 integer/pointer arguments normally begin in RCX, RDX, R8 and R9. Linux gdb examples often use a different ABI.
- A patched success branch may skip flag generation; recover the actual input/algorithm.
- ASLR changes runtime addresses; keep module-relative offsets.

## CTF: break on a comparison or decoded buffer

1. Find the validation function through a message reference or call trace.
2. Stop immediately before its compare routine.
3. Identify argument buffers using the correct calling convention.
4. Follow each pointer in Dump and inspect both hex and text.
5. Step across the comparison and inspect the return value/conditional branch.
6. Trace how the expected buffer was constructed, then recover the real input.

On Windows x64, `memcmp(a,b,n)` normally receives `a` in RCX, `b` in RDX and `n` in R8. A 32-bit target commonly passes arguments on the stack, but optimized/internal functions can differ.

## Debugger commands explained

```text
bp kernel32.GetProcAddress
bp kernel32.LoadLibraryA
```

`bp`/`bpx` sets a software breakpoint at an address or resolvable symbol. `kernel32.GetProcAddress` selects an exported API by module and name. The module must be loaded and the symbol must resolve; forwarded APIs can lead into another module.

At a GetProcAddress breakpoint on x64, inspect RDX as a possible function-name pointer or ordinal value. Do not interpret a small ordinal as a valid string address.

## CTF: distinguish runtime addresses from patch offsets

Record a code location as module name plus relative virtual address (RVA). To patch the file, map that RVA to its PE section’s raw-file offset. ASLR affects the loaded base, and section virtual/raw positions can differ.

## CTF: watch a small decrypted value

Select a known memory location in Dump and use the breakpoint menu for a hardware write/access breakpoint when appropriate. Continue until the watched value is touched. Hardware slots and supported sizes are limited; watching an entire large heap buffer this way is not practical.

## CTF: export a decoded region

After the decoding routine returns, confirm the buffer pointer and length. Select that region in Dump and use its binary save control. Verify the first bytes and length in HxD. A pointer followed by a NUL does not necessarily mark the full output buffer length.

## Exceptions and unpacking clues

An exception can be deliberate control flow. Record its address/code and whether the program’s own handler continues normally. For a packed executable, follow the transition into newly decoded executable memory and rebuild your understanding from the actual code reached.

## End-to-end investigation example

```text
Artifact: Windows PE password checker
Anchor: "Wrong password" string reference
Stop: comparison call before failure branch
Inspect: input pointer, expected pointer, compared length
Trace: XOR loop building the expected bytes
Recover: reverse loop in Python
Prove: enter recovered value in the unpatched application
```

## Common debugger mistakes

| Symptom | Check |
| --- | --- |
| Breakpoint belongs to another process/module | Target identity and module mapping |
| Wrong string at RCX | ABI, pointer lifetime and exact stop position |
| Patch works but no flag | Required computation was skipped |
| Data changes each run | Random seed, timestamps or session input |
| Stepping enters long library code | Use step over or a breakpoint after the call |

References: [GUI manual](https://help.x64dbg.com/en/latest/gui/index.html), [bp command](https://help.x64dbg.com/en/latest/commands/breakpoint-control/SetBPX.html).

## Related playbooks

- [Native runtime debugging](../../reversing-expl/dynamic-debugging/)
- [Native binary triage](../../reversing-expl/triage/)
