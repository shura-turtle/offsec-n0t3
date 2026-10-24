---
title: "Fatmike — JIT Decryption and Nanomites"
date: 2026-10-24
weight: 1
bookToc: true
description: "Decrypt the hidden code section, restore INT3 branches, and run the original serial validator."
---

# Fatmike — JIT Decryption and Nanomites

[Download solver](files/solve.py)

The serial is `D3FE-A7ED-BAAD-C0D3`. The repository's challenge README gives the flag as `CMO{byp4ss3d_f4tm1k3_2o26}`. I verified the serial by executing the handout's original decrypted validator: it returns `1`; changing the last digit to `4` returns `0`. The flag text below comes from that README, since the Windows GUI did not finish under Wine's breakpoint handling.

```text
CMO{byp4ss3d_f4tm1k3_2o26}
```

## 1. Identify the hidden code

Use `Fatmike/Handout/Crackme.exe` from the public repository. Its SHA-256 is:

```text
489dc223e8e0cf0dbce028e5dc8ce75036f0f5253289bd61a8faa479360d778e
```

It is a 32-bit Windows GUI program. PE section `.pc` starts at VA `0x40a000`, file offset `0x8e00`. The section has 0x5b9 meaningful bytes, padded to 0x600. Its on-disk bytes do not disassemble into the serial checker. The normal code calls `0x40a000` at `0x4030e4`, and then calls `0x40a025` at `0x4030f6`. Those calls identify `.pc` as code that must be unpacked before use.

The executable also has an RCDATA resource numbered `1111`, at file offset `0x75358`, size 24584. The first DWORD is `1536` (`0x600`). After the eight-byte header come 1536 records of four little-endian DWORDs:

```text
section RVA | condition ID | signed displacement | instruction length
```

There is one record for each byte in the padded `.pc` section. For example, the record at offset `0x35` describes RVA `0xa035`, condition `13`, displacement `14`, length `2`.

## 2. Decrypt `.pc` with the program's own routine

The code around `0x403fba` manages the decrypted section. It calls the cipher constructor at `0x401e39` and stream XOR routine at `0x401f4d`. I stopped the isolated Wine process before entering a serial and read the 32-byte key at VA `0x40d268`; a second run gave the same bytes:

```text
f630aa38d57297375d645559c334fd50
d55ca1d177d2655a042351cf69244bf2
```

The constructor receives that key and the eight-byte nonce `0a 0b 0c 0d 0e 0f 10 11`. The downloadable solver maps the executable's original `.text` into Unicorn, runs `0x401e39`, then runs `0x401f4d` on the 0x600 bytes from file offset `0x8e00`. This avoids guessing the cipher's custom constants or rewriting its rounds.

The decrypted bytes begin:

```text
c7 01 47 bb 5d 86 8b c1 c7 41 04 90 b1 6e 0a c7
```

They now decode as real x86. The function at `0x40a000` writes five expected DWORDs:

```text
865dbb47  0a6eb190  20476c33  1c8a7693  59febdfb
```

These are checkpoints for the serial validator at `0x40a025`.

## 3. Follow the nanomites

Plain disassembly of the decrypted section still breaks: executable paths contain `INT3` (`cc`) instead of branch instructions. The exception handler at `0x4045f3` looks up the record for the breakpoint address, evaluates its condition with the saved EFLAGS, then sets the resumed EIP to either `site + length` or `site + length + displacement`.

I ran the original condition dispatcher at `0x404166` over representative EFLAGS values. Its IDs include `13 = equal`, `1 = not equal`, and `2 = unconditional`. Two examples from the validator show the scheme:

| Breakpoint | Prior instruction | Resource record | Meaning |
| --- | --- | --- | --- |
| `0x40a035` | compare serial pointer with zero | ID 13, displacement 14, length 2 | Null input jumps to failure at `0x40a045` |
| `0x40a043` | compare `strlen(serial)` with 19 | ID 13, displacement 7, length 2 | A 19-byte input jumps to `0x40a04c`; otherwise fail |

Some `cc` bytes also appear inside junk or instruction operands. Replacing every `cc` with a jump corrupts code. The solver leaves decrypted bytes intact and handles interrupt 3 as the original exception handler does.

## 4. Check the serial

At `0x40a025` the validator rejects null input and strings whose length is not 19. It starts its hash state at `0xcafebabe`, reads each serial byte, and calls the updater at `0x40a1ce`. Every four bytes it compares its state against the next DWORD from `0x40a000`; it checks the final three bytes against the fifth DWORD. The path also changes the state between checkpoints, so hashing each four-character group independently from `0xcafebabe` gives the wrong later values.

For `D3FE-A7ED-BAAD-C0D3`, the original updater and validator produce:

| Consumed bytes | State | Expected |
| --- | --- | --- |
| `D3FE` | `865dbb47` | `865dbb47` |
| `-A7E` | `0a6eb190` | `0a6eb190` |
| `D-BA` | `20476c33` | `20476c33` |
| `AD-C` | `1c8a7693` | `1c8a7693` |
| `0D3` | `59febdfb` | `59febdfb` |

The group boundaries are byte offsets 4, 8, 12, 16, and 19, not the hyphens. Thus the hyphens are hashed as input bytes.

The solver executes the original function at `0x40a025`, dispatching 936 nanomite breakpoints for the valid serial. Three unrelated calls are stubbed: `strlen`, an object allocator, and its setup routine. The serial hash and comparisons are executed from the decrypted handout bytes.

```bash
python -m pip install unicorn
python solve.py /path/to/Crackme.exe
```

```text
decrypted .pc head: c70147bb5d868bc1c7410490b16e0ac7
serial: D3FE-A7ED-BAAD-C0D3 validator: 1 nanomites: 936
mutant: D3FE-A7ED-BAAD-C0D4 validator: 0 nanomites: 942
flag from repository README: CMO{byp4ss3d_f4tm1k3_2o26}
```

The serial and flag are disclosed in `Fatmike/README.md`; the native-code replay independently proves that this serial passes the handout's actual checker. It does not prove that Wine displayed the flag. Under Wine, the process entered its intentional breakpoint path and opened WineDbg instead of completing the GUI flow.
