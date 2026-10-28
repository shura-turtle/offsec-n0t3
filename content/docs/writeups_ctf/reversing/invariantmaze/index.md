---
title: "InvariantMaze"
date: 2026-10-28
weight: 1
bookToc: true
description: "Recover a 64-character license from a mod-257 bilinear invariant and a 64-position cycle, then verify the computed flag."
---

# InvariantMaze: solve the license through its invariant

[Download challenge](files/challenge) · [Download fast angr/Claripy solver](files/solve_angr_fast.py) · [Download exhaustive C++ solver](files/solve_invariant.cpp) · [Download C++ wrapper](files/solve.py)

The supplied `challenge` is a stripped Linux x86-64 executable. It reads a license, checks it, and prints a flag only after every check succeeds. The accepted license is 64 characters; the flag is computed from that license at runtime.

```text
license: JvjrOn1hr4huLM2SERgCi2oJXbKdy51oXiIqss4ekywkwP14oMU25KpLlPAF50oL
flag:    CSG_FLAG{Oops_we_forgot_to_buy_Ariadne_Threads}
```

This writeup derives the license from the original binary. The fast solver uses Claripy, angr's constraint engine, after reducing the validator to four symbolic indices. It then runs the unchanged executable to obtain the flag.

## 1. Check the handout and the first rejection

Use the supplied executable as `challenge`. The SHA-256 of the file analyzed here is:

```text
14b091cff3667e2103f2af1b0c2031578f455908c1c92fb60f6463c6e37a15f3
```

On Linux, start with:

```bash
file challenge
sha256sum challenge
printf 'A\n' | ./challenge
strings -a -t x challenge | grep -E 'license|invalid|accepted|flag:'
```

`file` identifies a 64-bit PIE ELF for x86-64. The short input produces `license> invalid`. The strings include `license> ` at file offset `0x4004`, `invalid` at `0x400e`, `accepted` at `0x4017`, and `flag: %s` at `0x4021`. The 64-byte alphabet at `0x4040` is:

```text
ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-
```

The addresses below are ELF virtual addresses relative to the PIE load base. In this binary's `.rodata`, the cited virtual addresses also equal file offsets. At runtime, add the process load base to an ELF address before setting a debugger breakpoint.

## 2. Follow the validation path

Disassemble `main` and the functions it calls:

```bash
objdump -d -Mintel --start-address=0x1090 --stop-address=0x1852 challenge
```

`main` starts at `0x1090`. Its `getc` loop stores at most 256 bytes and stops on newline or EOF. It rejects a zero byte within the stored input. At `0x1199`, it calls `0x12f0` to parse the license; at `0x11b9`, it calls `0x1410` to validate it. The `accepted` print at `0x11c6` is reached only when both calls return success.

| Address | Role | What to check in the disassembly |
| --- | --- | --- |
| `0x12f0` | Alphabet parser | Requires length `0x40`; searches the alphabet at `0x4040`; writes each matched position plus one as a 16-bit word. |
| `0x1410` | Main validator | Copies two 992-byte arrays, generates operations from the input indices, compares 62 checksums, checks character rules and a cycle, then calls `0x2210`. |
| `0x1e00` | Apply an operation to the 8 by 8 input-index matrix | Dispatches six operation types. |
| `0x1e90`, `0x1f40` | Apply the paired operation | Update one of the two 8-word vectors in every record. |
| `0x1d40` | Checksum | Computes a bilinear expression modulo 257. |
| `0x21c0` | Cycle test | Walks 64 positions, requiring one visit per position and a return to zero. |
| `0x2210` | Flag derivation and final check | Uses SHA-256 to derive a 47-byte flag and checks a 16-byte digest prefix. |

The parser uses **one-based** alphabet indices. For example, `A` becomes `1`, `a` becomes `27`, `0` becomes `53`, `_` becomes `63`, and `-` becomes `64`. Using ASCII bytes directly in the equations would produce the wrong matrix.

## 3. Read the apparent maze

`0x1410` treats the 64 parsed indices as an 8 by 8 matrix, which I call `X`. It copies 62 records of 16 bytes each from `0x4640` into one array and 62 records from `0x4260` into another. Each record contains eight little-endian 16-bit values. Call these record vectors `L[k]` and `R[k]`.

For input position `t`, the validator derives a series of operations from `X[t]`, the position, and a 251-byte table at `0x4080`. The number of operations for that character is `8 + (X[t] & 15)`. Each generated operation carries a type from 0 through 5, two 3-bit indices, and a nonzero scalar from 1 through 256. The operation parameters depend on the input, which makes direct symbolic execution expensive.

The six types have a simpler effect than the parameter-generation code suggests:

| Type | Change to `X` | Paired change | Paired function |
| ---: | --- | --- | --- |
| 0 | Swap two rows | Swap the same components of every `L[k]` | `0x1e90` |
| 1 | Swap two columns | Swap the same components of every `R[k]` | `0x1f40` |
| 2 | Add a scalar multiple of one row to another | Apply the corresponding subtraction to every `L[k]` | `0x1e90` |
| 3 | Add a scalar multiple of one column to another | Apply the corresponding subtraction to every `R[k]` | `0x1f40` |
| 4 | Multiply a row by a nonzero scalar | Multiply the corresponding `L[k]` component by its inverse | `0x1e90` |
| 5 | Multiply a column by a nonzero scalar | Multiply the corresponding `R[k]` component by its inverse | `0x1f40` |

The arithmetic helpers at `0x2540`, `0x2560`, `0x2590`, `0x25d0`, and `0x2600` implement reduction, addition, subtraction, multiplication, and inversion modulo **257**. Because 257 is prime and the scalar is never zero, every scale operation has an inverse.

The decisive observation is the call at `0x16cc`: `0x1410` computes `0x1d40(L[k], X, R[k])` for each of the 62 records, XORs that result with a target word from `0x41e0`, and ORs all 62 differences. A zero aggregate means all 62 checksums match. This comparison is a better analysis target than the long operation generator.

## 4. Show why the checksum does not change

Reading `0x1d40` gives this expression for record `k`:

```text
H[k] = sum(i=0..7) sum(j=0..7)
       L[k][i] * X[i][j] * R[k][j]  (mod 257)
```

Equivalently, `H[k] = L[k]^T * X * R[k]` over the field modulo 257. Each generated operation updates `X` and one record vector together so that this product stays fixed. For a row addition, suppose row `a` becomes `row_a + c*row_b`. The paired vector update makes `L_b` become `L_b - c*L_a`. The two changed terms then cancel:

```text
L_a * (row_a + c*row_b) + (L_b - c*L_a) * row_b
= L_a * row_a + L_b * row_b
```

Row swaps and inverse scaling preserve the same product. The column operations do the symmetric update to `R`. This explains why the validator can perform many input-dependent mutations without changing any `H[k]`: it is testing an invariant.

The target words are at `0x41e0 + 2*k`. Therefore each target can be compared with the **initial** arrays. No operation sequence needs to be simulated. The initial arrays turn each target into a linear equation in the original input indices:

```text
sum(i=0..7) sum(j=0..7)
    (L[k][i] * R[k][j]) * X[i][j] = target[k]  (mod 257)
```

For example, record zero has `L[0] = [20,109,97,90,29,222,42,224]`, `R[0] = [9,52,168,196,122,232,232,100]`, and target `229`. Substituting the recovered indices into that equation gives `229 mod 257`. Record 61 gives `116`, matching its stored target as well.

## 5. Reduce 64 unknowns to four

Each record supplies one equation. Construct a 62 by 65 augmented matrix: 64 coefficients, followed by the target. Coefficient `8*i+j` in row `k` is `L[k][i] * R[k][j] mod 257`. The solver reads the words from the original ELF file, so it does not need hand-copied constants.

Gaussian elimination modulo 257 gives rank **60**. Four input indices remain free, at zero-based positions **9, 16, 23, and 59**. Every other input index is an expression in those four values. This is the point where symbolic solving becomes practical.

`0x1410` supplies useful range and character constraints. It requires exactly 13 digits, at least one uppercase and lowercase letter, no `_` or `-`, and at most four copies of any character. Because the parser is one-based, valid letter or digit indices are `1..62`, and digit indices are `53..62`. An exhaustive C++ version of this reduction found 79,968 assignments with all 64 indices in `1..62`; the cycle rule reduced those to one. The fast Claripy script adds the digit count and a necessary cycle constraint directly, so it does not enumerate all 79,968.

## 6. Translate the cycle check into a solver constraint

The function at `0x21c0` starts at position zero. It runs this update 64 times, tracking visited positions in a 64-bit mask:

```text
position = (position + X[position]) & 63
```

It accepts only if it visited every position exactly once and returned to zero. Define `successor[i] = (i + X[i]) & 63`. Every valid 64-position cycle must have 64 different successors. The script gives Claripy all 2,016 pairwise inequalities between those successors. This is a **necessary** condition, not a replacement for the full cycle test; the script checks the 64-step walk on each returned model.

With the linear equations, ranges, digit count, and distinct-successor constraints, Claripy returned one model in this run. Its indices map back through the alphabet to:

```text
JvjrOn1hr4huLM2SERgCi2oJXbKdy51oXiIqss4ekywkwP14oMU25KpLlPAF50oL
```

For this license, the walk visits all 64 positions, returns to zero, contains 13 digits, and has no character occurring more than four times.

## 7. Follow the flag derivation

The validator converts the accepted indices back to 64 ASCII characters at `0x13e0`. The final function at `0x2210` hashes `b"InvariantMaze/v1" + license`. It hashes that 32-byte digest with little-endian eight-byte counters 0 and 1 to obtain enough keystream bytes, then XORs the first 47 bytes with the blob at `0x41a0`. It finally hashes `b"flag-check" + flag` and compares the first 16 digest bytes with the constant at `0x4180`.

The derived values for the accepted license are:

```text
SHA256("InvariantMaze/v1" || license)
= 0ee7d18dc306df80c3f1936a22912a235f2715bdba6ae968bb5a4d2a24de40d9

SHA256("flag-check" || flag)[:16]
= 2cfbbd74076355a26d1db727a1b27081

stored check at 0x4180
= 2cfbbd74076355a26d1db727a1b27081
```

The `CSG_FLAG{` prefix is a useful sanity check, but it is not a practical way to invert the hash. The invariant and cycle rule recover the license before the hash is involved.

## 8. Read the fast solver function by function

The complete runnable code is `solve_angr_fast.py`. It needs Python 3 and angr; the tested local version was angr 10.0.5. Run it next to the supplied binary:

```bash
python3 -m pip install angr
python3 solve_angr_fast.py ./challenge
```

The script imports `claripy` **from `angr`**. This matters in the tested environment because a separately installed `claripy` module produced AST objects that this angr build did not accept.

| Script function | Why it exists |
| --- | --- |
| `read_u16` | Reads one little-endian field element from the ELF. |
| `build_equations` | Extracts `L`, `R`, and target words and constructs all 62 linear rows. |
| `eliminate` | Performs modular Gaussian elimination and identifies the four free positions. |
| `make_symbolic_indices` | Creates four Claripy bitvectors and expresses the other 60 indices as modular functions of them. |
| `add_successor_rule` | Adds the necessary distinct-successor condition from `0x21c0`. |
| `is_full_cycle` | Checks the exact walk after Claripy returns a concrete model. |
| `verify_in_binary` | Submits the resulting license to the original executable and requires `accepted`. |
| `main` | Checks the binary hash, runs the stages in order, and prints the verified result. |

### `build_equations`: take coefficients from the binary

For each record, the relevant lines read eight words from each embedded array, multiply every left word by every right word, and append the stored target:

```python
left = [read_u16(raw, 0x4640 + 16*k + 2*i) for i in range(8)]
right = [read_u16(raw, 0x4260 + 16*k + 2*j) for j in range(8)]
coefficients = [left[i] * right[j] % 257
                for i in range(8) for j in range(8)]
target = read_u16(raw, 0x41E0 + 2*k)
```

The nested `i, j` order matches `X[8*i+j]`, the way the parser laid out the 64 indices. The SHA-256 guard in `main` prevents these fixed offsets from being applied silently to a different executable.

### `eliminate`: work in the same field as the program

Every row operation is reduced modulo 257. To make a pivot equal to one, the code uses `pow(pivot, -1, 257)`, Python's modular inverse. It then subtracts that pivot row from all other rows. The function checks for inconsistent equations and confirms the measured rank and free positions. Ordinary integer or floating-point elimination would not model the validator's arithmetic.

### `make_symbolic_indices`: keep only four symbolic values

The four free positions become 32-bit Claripy bitvectors. Each pivot row gives its original index as:

```text
X[pivot] = (target - sum(coeff[free_j] * free_j)) mod 257
```

The code adds a positive multiple of 257 before subtraction. This prevents a 32-bit unsigned bitvector from wrapping modulo `2^32` before the intended reduction modulo 257. Since each free value is at most 62 and each coefficient is at most 256, `257*256` exceeds the largest possible subtracted sum. It then constrains every recovered index to `1..62` and requires exactly 13 indices in `53..62`.

### `add_successor_rule` and `is_full_cycle`: two levels of checking

`add_successor_rule` forms each six-bit successor with `claripy.Extract(5, 0, X[i] + i)`. Six bits implement the binary's `& 63`. It adds one inequality for each pair of the 64 successors. `is_full_cycle` then performs the original walk on a concrete model and checks both the visited set and the final position.

### `main`: one model, then native proof

`main` calls `solver.batch_eval(variables + indices, 1)` so all 68 values come from the **same** satisfying model. Separate `eval` calls could choose different models. If a candidate fails the exact cycle, it blocks that four-variable assignment and asks for another. For a valid cycle, `verify_in_binary` runs the untouched `challenge` and requires the `accepted` line before reporting the flag.

The tested run was:

```text
linear rank=60; free positions=[9, 16, 23, 59]
models=1 elapsed=0.08s
license: JvjrOn1hr4huLM2SERgCi2oJXbKdy51oXiIqss4ekywkwP14oMU25KpLlPAF50oL
license> accepted
flag: CSG_FLAG{Oops_we_forgot_to_buy_Ariadne_Threads}
```

The complete script took about 1.5 seconds in that run, including Python startup and native verification. A direct angr attempt with all 64 input bytes symbolic hit a 5 GB memory cap after 89 seconds while still searching the alphabet, before the matrix check. Reducing the mathematics first is the practical difference.

## 9. Result

The original executable, without patches, accepted the recovered license and printed:

```text
CSG_FLAG{Oops_we_forgot_to_buy_Ariadne_Threads}
```
