---
title: "Windows Subsystem for Linux (WSL)"
weight: 6
bookToc: true
---

**Use for:** running the tournament’s Linux CLI tools on Windows.  
**Run in:** PowerShell to manage WSL; Bash inside the installed distribution.

## Enter the supplied distribution

```powershell
wsl --status
wsl --list --verbose
wsl
# Or choose a name shown above
wsl -d Ubuntu
```

## Windows ↔ Linux paths

```bash
# WSL: replace Competitor with your Windows account
cd /mnt/c/Users/Competitor/Downloads
mkdir -p ~/ajcbbc/challenge01
cp challenge.bin ~/ajcbbc/challenge01/
cd ~/ajcbbc/challenge01

# Open the current WSL folder in Windows Explorer
explorer.exe .

# Convert path syntax
wslpath -w "$PWD"
wslpath -u 'C:\Users\Competitor\Downloads\challenge.bin'
```

Windows Explorer can access Linux files using `\\wsl$\<distribution>\home\<user>`.

## Basic workflow

```bash
pwd
ls -lah
command -v python3 gdb binwalk exiftool
sha256sum challenge.bin
mkdir -p out
```

## Gotchas

- Bash commands belong in WSL; PowerShell uses different quoting and syntax.
- Linux paths and filenames are case sensitive.
- Keep large processing jobs in the Linux filesystem for better performance.
- GUI tools need a functioning display/WSLg setup.
- SocketCAN and `vcan` depend on the supplied WSL kernel; installed can-utils alone is insufficient.
- VPN connectivity from Windows does not guarantee identical routing in WSL.

## Flags explained

| Command / flag | Meaning |
| --- | --- |
| `wsl --status` | Inspect default WSL settings/status |
| `wsl --list --verbose` | List installed distributions and their WSL versions |
| `wsl -d NAME` | Start the selected distribution |
| `wsl --exec COMMAND` | Run a Linux command directly |
| `wslpath -w PATH` | Convert Linux path to Windows form |
| `wslpath -u PATH` | Convert Windows path to Linux form |

In the earlier `ls -lah`, `-l` selects a long listing, `-a` includes dotfiles and `-h` formats sizes for humans. Those are Linux ls options, not WSL management options.

## CTF: run one Linux command from PowerShell

```powershell
wsl --exec python3 --version
wsl --exec python3 -c 'import sys; print(sys.executable)'
```

Arguments are interpreted across Windows and Linux boundaries. For longer pipelines or complicated quoting, enter the WSL terminal and run the Bash command there.

## CTF: preserve binary outputs

Run binary-generating commands in WSL and redirect there. For example:

```bash
xxd -r -p hex.txt > decoded.bin
sha256sum decoded.bin
explorer.exe .
```

Then open the same file from Windows Explorer. This avoids routing binary bytes through a text-oriented Windows pipeline.

## CTF: fix copied shell scripts with CRLF line endings

```bash
# Inspect whether lines end in CRLF
xxd -l 128 solve.sh

# Convert a copy using Python; preserve the original
python3 - <<'PY'
from pathlib import Path
data = Path('solve.sh').read_bytes()
Path('solve_unix.sh').write_bytes(data.replace(b'\r\n', b'\n'))
PY
bash solve_unix.sh
```

A `bad interpreter` message mentioning `^M` is a clue to CRLF, not necessarily a missing Bash installation.

## CTF: distinguish route problems from tool problems

```bash
ip route get 192.0.2.10
python3 - <<'PY'
import socket
with socket.create_connection(('192.0.2.10', 8080), timeout=5):
    print('TCP connection established')
PY
```

Use the assigned host/port. A successful TCP connection confirms only that connection, not HTTP correctness or exploit success. Compare with Windows `Test-NetConnection` when only WSL fails.

## Environment limits that matter in CTFs

CAN modules, live packet capture, GUI display, disk-device access and VPN routes depend on the provided host setup. Diagnose the missing capability explicitly. Restarting the whole WSL distribution can interrupt all live challenge sessions; preserve state before any restart.

References: [working across filesystems](https://learn.microsoft.com/en-us/windows/wsl/filesystems), [WSL configuration](https://learn.microsoft.com/en-us/windows/wsl/wsl-config).

## Related playbooks

- [Tool-to-technique map](../../tools-cheatsheet/approved-tools-map/)
- [Offline Python library](../../tools-cheatsheet/python-library/)
