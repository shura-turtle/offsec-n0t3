#!/usr/bin/env python3
"""Solve InvariantMaze with its bilinear invariant and angr's Claripy solver."""

import argparse
import hashlib
from pathlib import Path
import string
import subprocess
import time

from angr import claripy


MODULUS = 257
ALPHABET = string.ascii_uppercase + string.ascii_lowercase + string.digits + "_-"
EXPECTED_SHA256 = "14b091cff3667e2103f2af1b0c2031578f455908c1c92fb60f6463c6e37a15f3"
RECORDS = 62
INPUT_SIZE = 64


def read_u16(raw: bytes, offset: int) -> int:
    """Read one little-endian word at a binary file offset."""
    return int.from_bytes(raw[offset:offset + 2], "little")


def build_equations(raw: bytes) -> list[list[int]]:
    """Build 62 equations L[k]^T X R[k] = target[k] in GF(257)."""
    equations = []
    for k in range(RECORDS):
        left = [read_u16(raw, 0x4640 + 16*k + 2*i) for i in range(8)]
        right = [read_u16(raw, 0x4260 + 16*k + 2*j) for j in range(8)]
        coefficients = [left[i] * right[j] % MODULUS
                        for i in range(8) for j in range(8)]
        target = read_u16(raw, 0x41E0 + 2*k)
        equations.append(coefficients + [target])
    return equations


def eliminate(equations: list[list[int]]) -> tuple[list[list[int]], list[int], list[int]]:
    """Reduce the augmented matrix by Gaussian elimination modulo 257."""
    rows = [row.copy() for row in equations]
    rank = 0
    pivots = []
    for col in range(INPUT_SIZE):
        pivot = next((r for r in range(rank, RECORDS) if rows[r][col]), None)
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        scale = pow(rows[rank][col], -1, MODULUS)
        rows[rank] = [v * scale % MODULUS for v in rows[rank]]
        for r in range(RECORDS):
            if r != rank and rows[r][col]:
                factor = rows[r][col]
                rows[r] = [(a - factor*b) % MODULUS
                           for a, b in zip(rows[r], rows[rank])]
        pivots.append(col)
        rank += 1
        if rank == RECORDS:
            break

    if any(not any(row[:INPUT_SIZE]) and row[INPUT_SIZE] for row in rows):
        raise ValueError("The equations are inconsistent")
    free = [col for col in range(INPUT_SIZE) if col not in pivots]
    if rank != 60 or free != [9, 16, 23, 59]:
        raise ValueError(f"Unexpected rank {rank} and free positions {free}")
    return rows, pivots, free


def make_symbolic_indices(rows: list[list[int]], pivots: list[int],
                          free: list[int]) -> tuple[claripy.Solver, list, list]:
    """Express all 64 indices in four Claripy bitvectors and add input rules."""
    variables = [claripy.BVS(f"free_{i}", 32) for i in range(4)]
    solver = claripy.Solver()
    indices = [None] * INPUT_SIZE

    for i, col in enumerate(free):
        indices[col] = variables[i]
        solver.add(claripy.And(variables[i] >= 1, variables[i] <= 62))

    # The largest subtracted sum is 4*256*62 = 63488. Adding 257*256
    # prevents unsigned 32-bit wrap before reducing modulo 257.
    for r, col in enumerate(pivots):
        expression = claripy.BVV(rows[r][INPUT_SIZE] + MODULUS*256, 32)
        for i, free_col in enumerate(free):
            expression -= rows[r][free_col] * variables[i]
        indices[col] = expression % MODULUS
        solver.add(claripy.And(indices[col] >= 1, indices[col] <= 62))

    # Alphabet positions 53..62 are the ten digits. Positions 63 and 64
    # represent '_' and '-', which the validator forbids.
    digit_count = claripy.BVV(0, 32)
    for index in indices:
        digit_count += claripy.If(index >= 53, claripy.BVV(1, 32),
                                  claripy.BVV(0, 32))
    solver.add(digit_count == 13)
    return solver, variables, indices


def add_successor_rule(solver: claripy.Solver, indices: list) -> None:
    """Require the 64 successors in sub_21C0 to be pairwise distinct."""
    successors = [claripy.Extract(5, 0, indices[i] + i) for i in range(64)]
    for i in range(64):
        for j in range(i):
            solver.add(successors[i] != successors[j])


def is_full_cycle(indices: list[int]) -> bool:
    """Check every position is visited once and the walk returns to zero."""
    position = 0
    seen = set()
    for _ in range(INPUT_SIZE):
        if position in seen:
            return False
        seen.add(position)
        position = (position + indices[position]) & 63
    return len(seen) == INPUT_SIZE and position == 0


def verify_in_binary(binary: Path, license: str) -> str:
    """Require acceptance by the untouched executable and return its output."""
    result = subprocess.run([str(binary)], input=(license + "\n").encode(),
                            capture_output=True, check=True)
    output = result.stdout.decode(errors="replace")
    if "accepted\nflag: " not in output:
        raise ValueError(f"The original binary rejected {license!r}: {output!r}")
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", nargs="?", default="challenge")
    args = parser.parse_args()
    binary = Path(args.binary).resolve()
    raw = binary.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_SHA256:
        raise SystemExit("This solver expects the original InvariantMaze binary")

    rows, pivots, free = eliminate(build_equations(raw))
    print(f"linear rank={len(pivots)}; free positions={free}", flush=True)
    solver, variables, indices = make_symbolic_indices(rows, pivots, free)
    add_successor_rule(solver, indices)

    start = time.monotonic()
    models = 0
    while solver.satisfiable():
        # Evaluate all expressions in one model. Separate eval calls can
        # select different satisfying assignments.
        model = solver.batch_eval(variables + indices, 1)[0]
        free_values, concrete_indices = model[:4], model[4:]
        models += 1
        if is_full_cycle(concrete_indices):
            license = "".join(ALPHABET[value - 1]
                              for value in concrete_indices)
            output = verify_in_binary(binary, license)
            print(f"models={models} elapsed={time.monotonic()-start:.2f}s")
            print(f"license: {license}")
            print(output, end="")
            return
        solver.add(claripy.Or(*(variables[i] != free_values[i]
                                for i in range(4))))
    raise SystemExit("No license satisfying the complete check")


if __name__ == "__main__":
    main()
