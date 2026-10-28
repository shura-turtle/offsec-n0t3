#!/usr/bin/env python3
"""Build the modular-invariant solver and verify its license against the binary."""

from pathlib import Path
import subprocess
import sys
import tempfile


here = Path(__file__).resolve().parent
binary = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else here / "challenge"
with tempfile.TemporaryDirectory(prefix="invariantmaze-") as tmp:
    solver = Path(tmp) / "solve_invariant"
    subprocess.run(
        ["g++", "-O3", "-std=c++17", str(here / "solve_invariant.cpp"), "-o", str(solver)],
        check=True,
    )
    recovered = subprocess.run([str(solver), str(binary)], capture_output=True, text=True, check=True)

lines = recovered.stdout.strip().splitlines()
assert lines[0] == "rank=60 free=4 9 16 23 59", lines
assert len(lines) == 2, lines
license = lines[1]
assert len(license) == 64
result = subprocess.run([str(binary)], input=(license + "\n").encode(), capture_output=True, check=True)
output = result.stdout.decode(errors="replace")
if "accepted\nflag: " not in output:
    raise SystemExit(f"Recovered license was rejected: {output!r}")
print(f"license: {license}")
print(output, end="")
