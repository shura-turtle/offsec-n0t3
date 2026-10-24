---
title: "Matryoshka v2"
date: 2026-10-24
weight: 1
bookToc: true
description: "Invert fifty nested DLL license checks and run the recovered final checker."
---

# Matryoshka v2

[Download solver](files/solve.py) · [Recovered license keys](files/keys.json)

This challenge puts one Windows DLL inside another. Each outer DLL checks the next 32 bytes of a license, uses those bytes as an RC4 key, decrypts a DLL resource, and calls the new DLL with the remaining license. The large file is mostly encrypted inner layers, not one giant validation function.

The solution below recovers the keys from the validation code and checks them against the original shellcode before decrypting each resource. It does not patch the license checker to accept an arbitrary key: that would leave RC4 using the wrong bytes and produce an invalid inner image.

## 1. Identify the two handout files

From the public repository root:

```bash
file 'Matryoshka v2/Handout/LicenseChecker.exe' 'Matryoshka v2/Handout/Doll.dll'
sha256sum 'Matryoshka v2/Handout/LicenseChecker.exe' 'Matryoshka v2/Handout/Doll.dll'
```

Both files are native x86-64 Windows PE images. Their hashes are:

```text
68351b3fb7763805f11b99f80c938608767b4adc61f40646d73eab1b6e5a5505  LicenseChecker.exe
5142b746763e0a0d5bbe1b4f9fb896bb60d6218783e7da5d566960436b7c96b5  Doll.dll
```

`LicenseChecker.exe` is only 11,776 bytes. `Doll.dll` is 68,144,128 bytes. The DLL's `.text` section is only `0x2000` bytes on disk, while its resource section is about 68 MB. That points to embedded data rather than a large ordinary program.

## 2. Follow the executable into the DLL

Disassemble the small executable:

```bash
objdump -d -M intel 'Matryoshka v2/Handout/LicenseChecker.exe' > checker.asm
objdump -p 'Matryoshka v2/Handout/Doll.dll' > doll-headers.txt
```

The executable reads `license.bin`, loads `Doll.dll`, resolves `CheckPassword`, and calls the export with the license buffer. The relevant export in the outer DLL is:

```text
CheckPassword RVA 0x10f0
Preferred VA    0x1800010f0
```

A return value of 1 is treated as a correct license. Other values lead to the wrong-license path.

This gives two useful analysis boundaries: the DLL export controls the layers, and the license file is the only input that must be constructed.

## 3. Extract the two resource blobs

The outer DLL calls `FindResourceW` with resource type 10 (`RCDATA`) and two names:

```text
CHECK
MATRYOSHKA
```

In the original outer image:

| Resource | RVA | Size |
| --- | --- | --- |
| `CHECK` | `0x70f4` | 1,352,414 bytes |
| `MATRYOSHKA` | `0x1513d4` | 66,775,040 bytes |

The solver's small PE parser walks the resource directory and maps resource RVAs back to file offsets. It extracts resources by their actual directory entries rather than carving every `MZ` byte sequence.

The `CHECK` resource begins with a relative jump into a mass of conditional branches. `MATRYOSHKA` does not begin with `MZ`; it is encrypted.

The loader at `0x1800010f0` explains how they are used:

1. Copy the `CHECK` resource into executable memory.
2. Copy 32 license bytes into a local, NUL-terminated buffer.
3. Call the shellcode on that buffer.
4. If the check succeeds, copy `MATRYOSHKA` into writable memory.
5. Resolve `advapi32!SystemFunction033` and decrypt that buffer using 32 license bytes as its RC4 key.
6. Memory-load the decrypted PE, resolve its password-check export, and call it on `license + 32`.

`SystemFunction033` is resolved through `GetProcAddress`, so an ordinary import listing does not show its name as an imported function. Its literal name is present at RVA `0x3270`.

## 4. Separate the shellcode's work from its branch noise

The outer `CHECK` blob has SHA-256:

```text
56443a65dcd6dd2734fd3f06cb0bad77dc5ed3e360d691b2f8e4805adbcfc34a
```

It contains many complementary branch pairs separated by instructions that preserve the original state. For example:

```asm
jge target
push rax
mov rax, rdx
pop rax
jl target
```

Either signed condition reaches the same target. Other junk sequences wrap a comparison in `pushfq` and `popfq`; that comparison's flags are discarded, so it is not a real password condition.

I ran the shellcode in Unicorn rather than attempting to decompile all of these branches. The setup supplies only a code mapping, stack, license buffer, and a return address. No Windows API is needed inside `CHECK` itself.

A 32-byte dummy input showed the real structure:

- A length loop requires 32 bytes before the terminating NUL.
- Four eight-byte words are loaded from that input.
- Each word passes through the same 32-round transform.
- Four chains of bit-checking functions validate the transformed words.

The first input word is loaded at shellcode offset `0xfc1a5`. The transform call is at offset `0x4d2bf`. These offsets apply to the outer resource only; inner resources have differently arranged obfuscation.

## 5. Reconstruct the Feistel transform

After removing the state-preserving noise from a trace, the arithmetic is small. Split an input word into its high and low 32-bit halves:

```python
left = word >> 32
right = word & 0xffffffff
```

The four base round-key words in the first layer are:

```text
efb1957a 03baecf7 8c982983 781bcdb6
```

For round `i` from 0 through 31:

```python
round_key = base_keys[i % 4] ^ i
left, right = right, left ^ rol32(right, 7) ^ round_key
```

All arithmetic stays within 32 bits. The returned 64-bit result is:

```python
(left << 32) | right
```

The inverse follows directly. Work backward through the round keys:

```python
for i in reversed(range(32)):
    left, right = right ^ rol32(left, 7) ^ (base_keys[i % 4] ^ i), left
```

There is no brute-force search here. Once the expected transformed word is known, the original eight input bytes are recovered exactly.

## 6. Read the expected output from the bit checks

Each validator checks the low bit, then calls the next function with the value shifted right by one. The first 63 functions mask the value with 1. The terminal function compares the remaining high bit directly.

A typical required-one condition is:

```asm
mov rax, [saved_argument]
and rax, 1
cmp rax, 1
```

A required-zero condition uses `test rax, rax` after the mask. The terminal function compares its saved argument against 0 or 1 without another mask.

To recover a complete target word, the solver temporarily steers those individual predicates toward success during an analysis run and records the bit each predicate requests. It ignores comparisons inside `pushfq`/`popfq` noise. This exposes the next predicate without requiring a correct input first.

The resulting target words for the outer layer are:

```text
fabbd91f04381f89
d13f557d1b36e7cc
501aeba922f2c44c
857a1bea6419ce73
```

Inverting the Feistel transform and packing each recovered word little-endian gives:

```text
M0Oo8zjHkcPSWFzCxmw6jrj1RgNPucTH
```

The solver then creates a fresh Unicorn instance, passes this exact key to `CHECK`, and runs the original instructions with no predicate hooks. It requires a return value of 1. This second run is the acceptance proof; the analysis run that forced predicates is not.

## 7. Decrypt and repeat

Use the accepted key to decrypt the resource:

```python
from Crypto.Cipher import ARC4
inner_dll = ARC4.new(key).decrypt(matryoshka_resource)
assert inner_dll.startswith(b"MZ")
```

The first inner DLL is 66,775,040 bytes and has SHA-256:

```text
cd979845f64a9d666e5e30b6533c331157da38e9214c06693bcfd4577438f5bf
```

Its loader has the same structure, but its checker and key differ. Repeating the procedure produces these first three keys:

```text
0  M0Oo8zjHkcPSWFzCxmw6jrj1RgNPucTH
1  nE0OSzTLiLdrMGsKxaP34YlM8LHyOVtB
2  41PDnuoUhyOZQKi3VX9VBpSN1BwNwGgx
```

Concatenate each accepted 32-byte key in order. That concatenation is the license prefix. A key from a later layer cannot be moved earlier: each DLL consumes the next 32 bytes and uses them to decrypt its own child.

The automated solver records each layer's input hash, key, round constants, and bit-check targets in `keys.json`. It checks both the untouched shellcode return and the decrypted `MZ` header before continuing.

## 8. Reach the terminal flag DLL

There are 50 encrypted wrapper layers. The final DLL is only 10,752 bytes and no longer contains `CHECK` and `MATRYOSHKA` resources. Its SHA-256 is:

```text
8a66b7aaa10fecf8c8837f31ecce82d0b0a41f0ed2442189923e718064e5392a
```

Its export is still named `CheckPassword`, now at RVA `0x1008`. The body does not validate another license segment:

```asm
sub rsp, 0x28
xor r9d, r9d
lea r8, [rip + ...]     ; L"Flag"
lea rdx, [rip + ...]    ; UTF-16 flag string at RVA 0x21b0
xor ecx, ecx
call [MessageBoxW]
mov eax, 1
add rsp, 0x28
ret
```

The 50 recovered keys therefore form the complete 1,600-byte license. No additional password suffix is required. The hint in the challenge description is not a replacement for any of these recovered RC4 keys.

The solver runs this final export in Unicorn. Its only external call is `MessageBoxW`; the hook records the UTF-16 string passed in `RDX`, returns from the message-box call, and lets the actual export return 1.

Captured output:

```text
CMO{1NsiD3_EV3RY_stOrY_lIe$_an0TH3r_s70Ry_WAITiNG_7o_bE_oPEn3d}
```

This matches the repository author's published flag. More importantly, it was extracted from the decrypted terminal DLL's live printing path, after all 50 wrapper keys had passed their untouched checks.

## 9. Run the solver

Install dependencies in a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install pycryptodome unicorn capstone
```

Save the supplied `solve.py`, then run:

```bash
python solve.py '/path/to/Matryoshka v2/Handout/Doll.dll' --out matryoshka-output
```

The full recovery takes a few minutes because it traces every obfuscated checker. The output directory contains:

```text
keys.json             # accepted keys, target words, round constants, layer hashes
license-prefix.bin    # progressively recovered bytes
license.bin           # completed 1600-byte license
final.dll             # decrypted terminal DLL
flag.txt              # captured MessageBoxW text
```

For a faster repeat using the already recovered `keys.json`:

```bash
python solve.py '/path/to/Matryoshka v2/Handout/Doll.dll' \
  --keys keys.json --out replay
```

This mode skips predicate discovery, but still checks each layer's hash, executes its original checker on the supplied key, decrypts the next layer, and executes the terminal flag export. It does not merely print the flag from a cached result.

On Windows, put the generated `license.bin` beside `LicenseChecker.exe` and the original `Doll.dll` to exercise the full application's loader chain. That full Windows UI path was not run during this Linux solve; the original checker shellcodes and final export were verified in Unicorn instead.

## What mattered

The resource names and the small DLL export exposed the structure before the obfuscated shellcode had to be understood. The password transform was invertible; only its expected output was hidden. Reading one expected bit at a time made the branch noise manageable, and replaying each recovered key without the analysis hooks prevented a forced-branch result from being mistaken for a real solve.
