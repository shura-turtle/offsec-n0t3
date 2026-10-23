---
title: "Volatility 3"
weight: 31
bookToc: true
---

**Use for:** processes, command lines, network state and files in memory dumps.  
**Run in:** WSL. Examples use `python3 vol.py` from the installed checkout; a packaged installation may provide `vol` instead.

## Discover plugins and identify Windows memory

```bash
python3 vol.py -h
python3 vol.py -f /path/to/memory.raw windows.info
```

Global options such as `-f`, `-o`, `-r`, `-p`, and `-s` go before the plugin name. Use absolute artifact paths if running from the tool directory.

## Windows CTF triage

```bash
# Active processes and parent relationships
python3 vol.py -f /path/to/memory.raw windows.pslist
python3 vol.py -f /path/to/memory.raw windows.pstree

# Scan for process objects and inspect command lines
python3 vol.py -f /path/to/memory.raw windows.psscan
python3 vol.py -f /path/to/memory.raw windows.cmdline

# Network objects and file objects
python3 vol.py -f /path/to/memory.raw windows.netscan
python3 vol.py -f /path/to/memory.raw windows.filescan
```

## Extract files associated with a process

```bash
mkdir -p /tmp/vol_out

# Replace 1234 with the PID found during triage
python3 vol.py -f /path/to/memory.raw -o /tmp/vol_out \
  windows.dumpfiles --pid 1234
```

## Export structured output

```bash
python3 vol.py -f /path/to/memory.raw -r json windows.pslist > processes.json
```

## Linux memory

```bash
python3 vol.py -f /path/to/linux.raw banners
python3 vol.py -f /path/to/linux.raw linux.pslist
python3 vol.py -f /path/to/linux.raw linux.pstree
```

Linux plugins require matching kernel symbols. Windows symbols can also need an available symbol cache or download access.

## Gotchas

- Plugin names/options vary; inspect `PLUGIN -h` on the supplied build.
- Volatility 2 profiles and commands are different from Volatility 3.
- Empty results can reflect unsupported symbols or missing pages.

## Flags explained: global versus plugin options

| Flag | Meaning | Position |
| --- | --- | --- |
| `-f FILE` | Input memory image | Before plugin name |
| `-o DIR` | Output directory for files emitted by a plugin | Before plugin name |
| `-r json` | Select JSON result renderer | Before plugin name |
| `-p DIR` | Additional plugin search directory | Before plugin name |
| `-s DIR` | Additional symbol search directory | Before plugin name |
| `-h` | Framework or selected plugin help | Use at the relevant level |
| `--pid N` | Select a process, when the plugin supports it | After plugin name |
| `--dump` | Ask a supporting plugin to write memory/files | After plugin name |
| `--key PATH` | Select registry key for printkey | After plugin name |

The same `-r` means result renderer in Volatility and input capture in TShark.

## CTF: investigate a suspicious process

```bash
# Process identity, parentage, command line and libraries
python3 vol.py -f /path/to/memory.raw windows.pstree
python3 vol.py -f /path/to/memory.raw windows.cmdline --pid 1234
python3 vol.py -f /path/to/memory.raw windows.dlllist --pid 1234

# Inspect the available memmap options, then dump mapped memory
python3 vol.py windows.memmap -h
python3 vol.py -f /path/to/memory.raw -o /tmp/vol_out \
  windows.memmap --pid 1234 --dump
```

Use the PID from your image. A process name is not unique identity; check creation time, parent, path and associated activity.

## CTF: search the emitted process memory

```bash
# Replace the filename with the actual dump name reported by memmap
strings -a -t x /tmp/vol_out/pid.1234.dmp > process_ascii.txt
strings -a -e l -t x /tmp/vol_out/pid.1234.dmp > process_wide.txt
grep -niE 'flag|password|secret|https?://' process_ascii.txt process_wide.txt
```

A dump-file offset is not automatically the original virtual address. Keep memmap’s mapping output for correlation.

## CTF: registry autorun clues

```bash
python3 vol.py -f /path/to/memory.raw windows.registry.hivelist
python3 vol.py -f /path/to/memory.raw windows.registry.printkey \
  --key 'Software\Microsoft\Windows\CurrentVersion\Run'
```

Inspect the plugin’s help to select a specific hive when necessary. A key can be absent from some hives or unavailable memory pages. Preserve the hive path and value data in your notes.

## CTF: scan for file objects, then recover a candidate

```bash
python3 vol.py -f /path/to/memory.raw windows.filescan > filescan.txt
grep -niE 'flag|secret|\.txt|\.zip' filescan.txt
python3 vol.py windows.dumpfiles -h
```

Use the plugin’s `--virtaddr` or `--physaddr` only after verifying which address type your source plugin returned. A wrong address kind can produce empty output without disproving that the file existed.

## Build a compact memory timeline

Join process start/exit times, command lines, network observations and recovered file content. Treat a scanned process object as possible historical evidence; `psscan` and active-list enumeration answer different questions.

## Troubleshooting symbol and plugin failures

| Error/outcome | Distinguish |
| --- | --- |
| Unsatisfied kernel/symbol requirement | Missing or mismatched symbols versus malformed image |
| Plugin not listed | Search path/import/API compatibility |
| Empty dump directory | Plugin did not emit bytes versus wrong output location |
| Process absent from pslist | Exited process, corruption or wrong image interpretation |
| Extracted file incomplete | Missing resident pages/cache state |

References: [Windows tutorial](https://volatility3.readthedocs.io/en/latest/getting-started-windows-tutorial.html), [Linux tutorial](https://volatility3.readthedocs.io/en/latest/getting-started-linux-tutorial.html), [dumpfiles](https://volatility3.readthedocs.io/en/latest/volatility3.plugins.windows.dumpfiles.html), [memmap](https://volatility3.readthedocs.io/en/latest/volatility3.plugins.windows.memmap.html), [registry printkey](https://volatility3.readthedocs.io/en/latest/volatility3.plugins.windows.registry.printkey.html).

## Related playbooks

- [Runtime evidence and memory](../../reversing-expl/dynamic-debugging/)
- [TLS/SSH secrets versus metadata](../../network-expl/tls-ssh/)
