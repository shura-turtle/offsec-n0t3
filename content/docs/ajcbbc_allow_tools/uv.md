---
title: "uv"
weight: 8
bookToc: true
---

**Use for:** Python virtual environments and approved dependencies.  
**Run in:** WSL.

**Tournament rule:** do not install AI/ML related packages or tools. The same restriction applies to Python and other extensible tools.

## Quick start

```bash
uv --version
uv venv --python python3
source .venv/bin/activate
uv pip list
python solve.py
```

## Walkthrough: prepare a solver environment

```bash
mkdir -p ~/ajcbbc/solver
cd ~/ajcbbc/solver
uv venv --python python3
source .venv/bin/activate

# Non-AI libraries; install only what your solver needs
uv pip install requests pycryptodome
uv pip freeze > requirements.txt
python solve.py
```

## Existing requirements

```bash
source .venv/bin/activate
uv pip install -r requirements.txt
uv pip show pycryptodome
deactivate
```

Inspect a supplied requirements file before installation to ensure it follows the tournament rule.

## Gotchas

- Activate the environment in each new terminal or use its Python path explicitly.
- `Crypto` is the import namespace provided by `pycryptodome`.
- Package download access may be unavailable during the tournament.
- `uv run` can resolve dependencies; use the prepared environment’s Python when you want to run exactly what is already installed.

## Flags and subcommands explained

| Syntax | Meaning |
| --- | --- |
| `uv venv DIR` | Create a virtual environment at DIR; default is `.venv` |
| `--python python3` | Choose the existing interpreter for environment creation |
| `uv pip install PACKAGE` | Install into the selected/detected environment |
| `-r requirements.txt` | Read package requirements from that file |
| `--python PATH` on uv pip | Target a specific Python environment |
| `--offline` | Avoid network access; cached/local packages must suffice |
| `uv pip freeze` | Print installed package versions as requirements |
| `uv pip check` | Inspect installed dependency compatibility |

`uv pip` is uv’s package interface; it does not require invoking a separate `pip` executable. The environment’s interpreter still determines which packages a solver imports.

## CTF: run with an explicit interpreter

```bash
uv venv --python python3 .venv
uv pip install --python .venv/bin/python requests pycryptodome
.venv/bin/python solve.py
```

This removes ambiguity when several terminals or environments are open. The packages are non-AI examples; install only the dependencies needed by your challenge.

## CTF: recover from an interpreter mismatch

```bash
python3 -c 'import sys; print(sys.executable)'
.venv/bin/python -c 'import sys; print(sys.executable)'
uv pip list --python .venv/bin/python
```

If installation succeeded but import fails, compare these paths before reinstalling packages globally.

## CTF: use a supplied offline requirements set

```bash
# Works only if the required distributions are already cached/available
uv pip install --offline --python .venv/bin/python -r requirements.txt
uv pip check --python .venv/bin/python
```

A cache miss is an availability problem. Do not interpret it as proof that the solver or dependency name is wrong.

## Preserve a reproducible solver environment

```bash
uv pip freeze --python .venv/bin/python > solver_requirements.txt
.venv/bin/python --version > python_version.txt
```

Record the solver script, interpreter and required input artifacts together. A frozen requirements file documents your environment but does not bundle offline wheels or system libraries.

Reference: [uv environment guide](https://docs.astral.sh/uv/pip/environments/), [CLI reference](https://docs.astral.sh/uv/reference/cli/).

## Related playbooks

- [Offline Python snippet library](../../tools-cheatsheet/python-library/)
