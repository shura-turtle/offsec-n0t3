---
title: "FlipVM"
date: 2026-10-24
weight: 1
bookToc: true
description: "Patch signed virtual bytecode so its built-in decryptor accepts the expected input."
---

# FlipVM

[Download solver](files/solve.py)

The handout contains a Linux x86-64 VM (`FlipVM`) and its signed bytecode (`code.flp`). The public repository also includes VM/compiler source and an official patch script. I ran that patch against the exact distributed bytecode and executed the patched program in the unmodified native VM. The valid input and flag are disclosed in the repository; the replay demonstrates the path through the distributed VM.

## 1. Check whether the prompt accepts input

`Source_Code/Compiler/flipvmcode.ptf` prints a prompt, then executes `SLEEP 0, 500000000`. Its development `MOV R0, <expected input>` instruction is commented out. It never reads stdin before hashing `R0`. An ordinary password typed at the prompt therefore cannot reach the comparison. This is visible in the source and confirmed by a normal handout run that displayed the banner and then the input-error branch.

The expected 31-byte input appears as a source comment:

```text
$?$__LeT_Th#_h@ck!ng_b3g1n__$?$
```

The VM's intended check mutates that value, compares it with a constant, and only then calls `FUN_DecryptFlag` with the original input. The supplied official `Solution/patch.py` places the input into `R0` just before the check, so the VM itself still performs the mutation and flag decryption.

## 2. Patch the bytecode and rebuild its header

The `.flp` header is 266 bytes: `FLP` (3), modulus (128), exponent (3), signature (128), and an XOR-encoded entrypoint (4). The official patch inserts `MODE 1` and `MOV R0, <expected input>` immediately before code offset `0xfa1`, then sets the new entrypoint to the start of those instructions. The injected MOV bytes begin `28 88 1f 24 3f 24` and end `5f 5f 24 3f 24`; the [solver](files/solve.py) contains the full 33-byte instruction.

Changing the code invalidates the header's hash/signature relationship. The patch recomputes the VM's variant FNV hash with seed `0x3140101438`: expand each byte into all eight lanes of a 64-bit word, multiply the rolling hash by `8675309`, XOR the expanded byte, then retain the low 64 bits. It computes `pow(hash, 0x10001, P*Q)` with the supplied factors and writes `(signature ^ entrypoint) & 0xffffffff` into the final header field. The modulus and exponent live in the editable file header; this is the VM's file check, not a signature under a separately trusted key.

The official patch only fits this handout version. Its SHA-1 is `130e5d13e04e853178598f844c2c3cd7979e1961`; the solver refuses a different file before changing any bytes.

## 3. Run the native VM

Save the linked solver as `solve.py`, then run it from a working directory containing the public challenge repository:

```bash
python3 solve.py \
  FlipVM/Handout/FlipVM FlipVM/Handout/code.flp \
  --out /tmp/flipvm-patched.flp
```

The wrapper saves the patched `.flp`, runs the native VM, prints its raw output as Python `repr`, and checks the recovered flag. My run produced the flag in pieces with occasional `0x10` bytes between them. The VM source's native `PRINT` passes a stack address as a C string; those extra bytes are output artifacts, so the solver displays the raw bytes before removing only `0x10` for its flag check. The repository's plaintext flag and the recovered printable bytes agree:

```text
CMO{<-*~-~*~-.1'm++In.-~*~-~*->}
```

**Flag:** `CMO{<-*~-~*~-.1'm++In.-~*~-~*->}`
