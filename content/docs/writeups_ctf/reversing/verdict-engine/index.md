---
title: "Verdict Engine"
date: 2026-10-26
lastmod: 2026-10-27
weight: 1
bookToc: true
description: "Disassemble a VFP1 rule program and reverse twelve Feistel-style updates to recover its accepted token."
---

# Verdict Engine

The handout contains `bpfgate`, a Linux x86-64 executable, and `rules/ingress.bpf`, its compiled access-control program. The engine accepts one 32-byte token. The task is to recover that token, not merely make the program print `PASS`.

[Download bpfgate](files/bpfgate) · [Download ingress.bpf](files/ingress.bpf) · [Download solve.py](files/solve.py)

I treated the rule file as a program: decode its instructions, identify the four comparisons at the end, then run its twelve reversible updates backward. The resulting token was accepted by the original executable.

## 1. Establish the input and file format

Run the supplied files on Linux:

```bash
chmod +x bpfgate
file bpfgate ingress.bpf
./bpfgate -i ingress.bpf
```

`bpfgate` is an unstripped 64-bit PIE ELF with debug information. Its symbol table names the VM and its helpers. The information command reports:

```text
container    : VFP1
flags        : 0x0001
header       : 12 bytes
instructions : 212 x 8 bytes
ctx window   : 64 bytes
```

The first twelve rule-file bytes are `56 46 50 31 0c 00 01 00 d4 00 00 00`: `VFP1`, a 12-byte header, flags `1`, and 212 instructions. Instruction *n* starts at file offset `0x0c + 8*n`. These are **rule-file offsets**, while the `0x1xxx` and `0x2xxx` addresses below are addresses in the PIE ELF relative to its load base.

`main` calls `load_ruleset` at ELF address `0x2317`. At `0x2479` it reads stdin with `getline`; `0x24db`–`0x2528` strip trailing CR or LF, and `0x252a` requires `0x20` bytes. It copies exactly 32 bytes into a 64-byte context at `0x25af`, then calls `vm_run` at `0x261e`. The final verdict is based on the VM's returned value: `0x2685`–`0x269c` print `PASS` only when the result equals 1. This establishes that the comparison logic is in `ingress.bpf`.

## 2. Decode the VM instructions

In `vm_run` at `0x1b87`, the instruction fetch at `0x1c2d`–`0x1c42` reads one eight-byte rule record. The decoder at `0x1c46`–`0x1c6a` takes the low opcode bits as the instruction class and splits the second byte into destination and source register nibbles. The important opcodes are:

| Opcode | Meaning here | Interpreter evidence |
| --- | --- | --- |
| `0x79` | Load 64 bits from `[src + signed_offset]` into `dst` | `vm_run` calls `mem_read` at `0x1d3f` |
| `0xbf` | Copy one 64-bit register to another | `exec_alu` handles MOV at `0x196c` |
| `0x85` | Call helper number in the immediate | `vm_run` calls `feistel_helper_dispatch` at `0x1ed5` |
| `0x7b` | Store 64 bits at `[dst + signed_offset]` | `vm_run` calls `mem_write` at `0x1dba` |
| `0x07` | Add a 32-bit immediate to a 64-bit register | `exec_alu` addition at `0x1857` |
| `0x18` | Load a 64-bit immediate from this and the next instruction | `vm_run` combines both halves at `0x1e72`–`0x1ea9` |
| `0xaf` | XOR a 64-bit destination with a source register | `exec_alu` XOR at `0x195e` |
| `0x5d` | Jump if two 64-bit registers differ | `cond_true` at `0x1b04`; branch at `0x1f90`–`0x2011` |
| `0xb7`, `0x95` | Set r0 to an immediate, then exit | exit handled at `0x1f54`–`0x1f67` |

The bytecode resembles eBPF, but the opcode meanings above are verified in this particular interpreter. `mem_read` at `0x15f4`–`0x1615` assembles bytes with shifts of `8*j`, so token words are little-endian. `vm_run` puts the context pointer in r1 and its stack top in r10. The first four rule instructions are:

| VM index | File offset | Decoded instruction | Effect |
| ---: | ---: | --- | --- |
| 0 | `0x000c` | `79 r6,[r1+0]` | token bytes 0–7 → r6 |
| 1 | `0x0014` | `79 r7,[r1+8]` | token bytes 8–15 → r7 |
| 2 | `0x001c` | `79 r8,[r1+16]` | token bytes 16–23 → r8 |
| 3 | `0x0024` | `79 r9,[r1+24]` | token bytes 24–31 → r9 |

`vm_run` clears r1–r5 after each helper call at `0x1f00`–`0x1f3b`; r6–r9 survive. This explains the repeated moves into argument registers and the temporary store at `[r10-8]`.

## 3. Follow one round instruction by instruction

The first update spans VM instructions 4–19, beginning at rule-file offset `0x002c`. The same shape repeats eleven times. Here is that block with each operation's role:

| VM index | Decoded operation | Meaning |
| ---: | --- | --- |
| 4–6 | `r1=r7; call 3; r1=r0` | Substitute each byte of r7; pass result as the first argument to the next helper. |
| 7–9 | `r2=r7; call 2; [r10-8]=r0` | Mix substituted r7 with the original r7; save the result across the next call. |
| 10–13 | `r1=r7; call 4; r2=r0; r2+=0` | Count set bits in r7; form this round's rotation count. |
| 14–15 | `r1=[r10-8]; call 1` | Rotate the saved mix left by the count in r2. |
| 16–17 | `lddw r1,0x9e3779b97f4a7c15` | Load the first round key, low 32 bits followed by high 32 bits. |
| 18–19 | `r0 ^= r1; r6 ^= r0` | Combine the key, then update r6. |

The helpers are native ELF functions called by `feistel_helper_dispatch` at `0x142a`:

| Helper ID | ELF address | Operation |
| ---: | ---: | --- |
| 1 | `0x1329` | `rol64(r1, r2 & 63)` |
| 2 | `0x135c` | `(r1 * 0x9e3779b97f4a7c15) XOR ror64(r2, 29)`, modulo 2⁶⁴ |
| 3 | `0x1390` | Replace each byte of r1 through the 256-byte S-box |
| 4 | `0x13f8` | Population count of r1 |

At `0x13c8`, the S-box routine addresses `g_feistel_sbox` at ELF address and file offset `0x3020`; at `0x13cf` it reads one table entry per input byte. The `ror` instruction in `feistel_mix` is at `0x1370`, the multiplication constant is loaded at `0x137c`, and the XOR is at `0x138a`. The table itself has 256 entries, so the solver can take `bpfgate[0x3020:0x3120]` directly.

Writing `S(x)` for independent byte substitution, the function added to a destination word in round `i` is:

```text
M(x)   = (S(x) * 0x9e3779b97f4a7c15) XOR ror64(x, 29)
F_i(x) = rol64(M(x), popcount(x) + 7*i) XOR key_i
```

All arithmetic is modulo 2⁶⁴ and rotation counts are reduced modulo 64. The first block calculates `r6 ^= F_0(r7)`. The next block begins at VM index 20 and calculates `r7 ^= F_1(r8)`. The destination/source pair cycles through `(r6,r7)`, `(r7,r8)`, `(r8,r9)`, `(r9,r6)` three times.

The complete round map also gives the file offset of each key's `lddw` instruction. The next instruction supplies its high 32 bits:

| Round | VM block | Block file offset | Update | Key VM index / file offset | 64-bit key |
| ---: | ---: | ---: | --- | ---: | --- |
| 0 | 4–19 | `0x002c` | `r6 ^= F_0(r7)` | 16 / `0x008c` | `0x9e3779b97f4a7c15` |
| 1 | 20–35 | `0x00ac` | `r7 ^= F_1(r8)` | 32 / `0x010c` | `0x3c6ef372fe94f82a` |
| 2 | 36–51 | `0x012c` | `r8 ^= F_2(r9)` | 48 / `0x018c` | `0xdaa66d2c7ddf743f` |
| 3 | 52–67 | `0x01ac` | `r9 ^= F_3(r6)` | 64 / `0x020c` | `0x78dde6e5fd29f054` |
| 4 | 68–83 | `0x022c` | `r6 ^= F_4(r7)` | 80 / `0x028c` | `0x1715609f7c746c69` |
| 5 | 84–99 | `0x02ac` | `r7 ^= F_5(r8)` | 96 / `0x030c` | `0xb54cda58fbbee87e` |
| 6 | 100–115 | `0x032c` | `r8 ^= F_6(r9)` | 112 / `0x038c` | `0x538454127b096493` |
| 7 | 116–131 | `0x03ac` | `r9 ^= F_7(r6)` | 128 / `0x040c` | `0xf1bbcdcbfa53e0a8` |
| 8 | 132–147 | `0x042c` | `r6 ^= F_8(r7)` | 144 / `0x048c` | `0x8ff34785799e5cbd` |
| 9 | 148–163 | `0x04ac` | `r7 ^= F_9(r8)` | 160 / `0x050c` | `0x2e2ac13ef8e8d8d2` |
| 10 | 164–179 | `0x052c` | `r8 ^= F_10(r9)` | 176 / `0x058c` | `0xcc623af8783354e7` |
| 11 | 180–195 | `0x05ac` | `r9 ^= F_11(r6)` | 192 / `0x060c` | `0x6a99b4b1f77dd0fc` |

## 4. Read the acceptance gate

Four `lddw`/`0x5d` pairs follow the rounds. `0x5d` means jump **when unequal**, so any failed comparison reaches VM index 210, which sets r0 to 0 and exits at 211. If all match, index 208 sets r0 to 1 and exits at 209.

| Checked register | Constant `lddw` at VM index / file offset | Jump at VM index / file offset | Required value |
| --- | --- | --- | --- |
| r6 | 196 / `0x062c` | 198 / `0x063c` | `0x372edcc427080478` |
| r7 | 199 / `0x0644` | 201 / `0x0654` | `0xf0a9bdc7e4035851` |
| r8 | 202 / `0x065c` | 204 / `0x066c` | `0x3b5150ddad266030` |
| r9 | 205 / `0x0674` | 207 / `0x0684` | `0xba7bb8d6869f10d5` |

For example, index 198 has jump offset 11. `vm_run` advances past that instruction before applying the offset, so `199 + 11 = 210`, the DROP return. The later offsets 8, 5, and 2 reach that same index. `main` receives the VM result at `0x261e` and prints `PASS` at `0x269c` only for result 1.

## 5. Undo the rounds and verify the token

Each round changes one word with XOR and leaves its source word untouched. XORing the same `F_i(source)` again restores the destination. Start with the four comparison constants and undo rounds 11 down to 0:

```python
words = [target_r6, target_r7, target_r8, target_r9]
for i in reversed(range(12)):
    words[i % 4] ^= F_i(words[(i + 1) % 4])
token = b''.join(word.to_bytes(8, 'little') for word in words)
```

The recovered input words are:

| Input register | Little-endian word | Eight token bytes |
| --- | --- | --- |
| r6 | `0x47414c465f475343` | `CSG_FLAG` |
| r7 | `0x746331647233767b` | `{v3rd1ct` |
| r8 | `0x625f6e315f73315f` | `_1s_1n_b` |
| r9 | `0x7d33643063333779` | `y73c0d3}` |

The [complete solver](files/solve.py) extracts the S-box from the ELF and keys from the rule file, performs this reversal, asserts 32 printable bytes, and sends the result to the unmodified program. It needs only Python's standard library. Run it from the directory containing the three downloads:

```bash
python3 solve.py ./bpfgate ./ingress.bpf
```

Output:

```text
CSG_FLAG{v3rd1ct_1s_1n_by73c0d3}
```

For an independent native check:

```bash
printf '%s\n' 'CSG_FLAG{v3rd1ct_1s_1n_by73c0d3}' | ./bpfgate ingress.bpf
```

The original engine prints `verdict: PASS`. The key distinction is that `0xaf` is XOR, confirmed at ELF address `0x195e`; treating it as multiplication fails to recover printable input. Reversing the XOR updates works without inverting the S-box or guessing any token bytes.

**Flag:** `CSG_FLAG{v3rd1ct_1s_1n_by73c0d3}`
