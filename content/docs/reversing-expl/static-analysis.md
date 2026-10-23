---
title: "Static Analysis · Bytes, Types & Control Flow"
weight: 4
bookToc: true
---

# Static analysis

**Recover the exact computation, not just a readable-looking decompiler listing.** The details that usually decide a solve are length, integer width, signedness, byte order and the order of transformations.

## 1. Work backward from the decisive check

```text
Success message
  ← deciding branch
  ← comparison / aggregate result
  ← transformed input / expected table
  ← preprocessing and original input source
```

Trace all callers when preprocessing occurs outside the validator. `fgets` may preserve a newline; `scanf("%s")` stops at whitespace; `read` returns bytes and may not append NUL. A length check can reject an otherwise correct decoded string.

## 2. Native calling convention quick map

At a real function entry, before its prologue changes argument registers:

| ABI | First integer/pointer arguments | Return |
| --- | --- | --- |
| Linux/macOS x86-64 SysV | RDI, RSI, RDX, RCX, R8, R9 | RAX |
| Windows x64 | RCX, RDX, R8, R9; further args on stack | RAX |
| x86 common cdecl | Stack, usually right-to-left at caller | EAX |
| ARM64 common AAPCS64 | X0–X7; width-specific W registers | X0/W0 |

Floating/vector arguments and varargs have additional rules. Windows x64 has shadow space. Apple ARM64 varargs differ from a simplistic “all args in X registers” model. Verify ABI against imports and call sites.

## 3. Common assembly meanings

| Instruction pattern | Important interpretation |
| --- | --- |
| `movzx eax, byte ptr [...]` | Zero-extend an unsigned byte |
| `movsx eax, byte ptr [...]` | Sign-extend an 8-bit value |
| `xor eax,eax` | Zero a register; not evidence of encrypted data |
| `lea eax,[...]` | Address/arithmetic calculation without memory read |
| `test eax,eax` | Set flags from value; often zero/nonzero branch |
| `cmp a,b` + conditional jump | Compare widths and signed/unsigned jump |
| `ja/jb` | Unsigned comparisons |
| `jg/jl` | Signed comparisons |
| `shr` | Logical right shift |
| `sar` | Arithmetic right shift; sign propagation |
| `rol/ror` | Fixed-width bit rotation |

On x86-64, writing a 32-bit general-purpose register clears the high 32 bits of the corresponding 64-bit register. A one-byte write does not do that.

## 4. Fixed-width Python translation

```python
def u8(x): return x & 0xff
def u32(x): return x & 0xffffffff
def s8(x):
    x &= 0xff
    return x - 0x100 if x & 0x80 else x

def rol8(x, n):
    n %= 8
    return ((x << n) | (x >> ((8-n) % 8))) & 0xff
```

If native code stores a byte after addition, mask at that point. If it sign-extends before comparison, model the sign conversion. Do not mask every intermediate expression arbitrarily; use the recovered operand/storage width.

## 5. Invert in reverse order

Recovered transform:

```c
out[i] = rol8((input[i] ^ 0x23) + i, 3);
```

For a byte-valued intermediate, inverse:

```python
def ror8(x, n):
    return rol8(x, -n)
answer = bytes(((ror8(y,3) - i) & 255) ^ 0x23
               for i,y in enumerate(expected))
```

You must undo rotate, then index addition, then XOR. Reapplying forward transform to the recovered candidate is a necessary check. The supplied [constraint example](../python-snippets/) implements and verifies this exact model.

## 6. Compare length and data representation

`memcmp(a,b,n)` compares exactly n bytes, including NULs. `strcmp` compares until NUL. `strncmp` is NUL-sensitive and bounded; it is not identical to memcmp. A function name guessed from similarity may be wrong: inspect behavior/call arguments if the comparison seems inconsistent.

Expected arrays may be bytes, 16-bit words, 32-bit words, pointer tables, or signed integers. If a decompiler shows `0x67616c66`, little-endian memory bytes are `66 6c 61 67` (`flag`). Do not reverse the entire array when only each 32-bit word is little-endian.

## 7. Structures and state machines

For repeated field offsets, record a tentative structure:

```text
+0x00 score: uint32
+0x04 step: uint32
+0x08 hash: uint32
+0x10 buffer pointer: architecture-sized
```

Offsets alone do not establish types; verify access widths. In stateful/game checks, map each action to changes in score, counters, rolling hash and sequence state. A valid final score may still fail an independent ordering constraint.

## 8. Switch tables and custom VMs

For indirect dispatch:

1. Identify opcode fetch width and program-counter increments.
2. Find bounds checks and dispatch table entry encoding.
3. Record each opcode's operand width, stack effect and branch semantics.
4. Trace one tiny known sequence by hand before writing an interpreter.
5. Compare interpreter state at the same checkpoints as the original.

Relative dispatch entries must be added to the correct base. A table of signed 32-bit offsets is not a table of 64-bit absolute pointers.

## 9. Know when to switch to runtime

Static analysis is enough when the data and check are readable. Switch to [dynamic debugging](../dynamic-debugging/) when a key/table is initialized dynamically, code is unpacked, a call target is unresolved, or an anti-debug branch depends on environment.

Use a precise question: “What are the 16 bytes at the second comparison argument after initialization?” This leads to a useful breakpoint. “Run until something interesting” usually does not.

## Tools and references

[Ghidra](../../ajcbbc_allow_tools/ghidra/), [objdump](../../ajcbbc_allow_tools/objdump/), [LLVM MC](../../ajcbbc_allow_tools/llvm_mc/), [HxD](../../ajcbbc_allow_tools/hxd/). ABI sources: [Microsoft x64 calling convention](https://learn.microsoft.com/en-us/cpp/build/x64-calling-convention), [Arm ABI specifications](https://github.com/ARM-software/abi-aa), [Intel architecture manuals](https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html).
