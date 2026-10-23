---
title: "AJCBBC Allowed Tools"
weight: 2
bookCollapseSection: true
bookToc: true
---

Tournament tool notes: **what it is for → useful commands → CTF walkthrough → gotchas**. One Markdown page per entry in the supplied 39-tool Windows approved list. Sidebar order follows the original list.

Each page now includes deeper CTF workflows and worked examples. CLI pages explain their options in tables; GUI pages explain the corresponding controls and how to move useful evidence into CLI tools.

## Technique playbooks and visual guides

Use these when you know the artifact or suspected vulnerability and need the next test:

- [Web payloads and database fingerprints](../web-expl/)
- [Network captures and stateful protocols](../network-expl/)
- [Steganography, images, documents and audio](../steganograph-expl/)
- [Reversing, Ghidra and debugger workflows](../reversing-expl/)
- [Visual CyberChef recipes](../tools-cheatsheet/cyberchef-cheatsheet/)
- [All 39 tools mapped to techniques](../tools-cheatsheet/approved-tools-map/)
- [Prepared Python snippet library](../tools-cheatsheet/python-library/)

Each individual tool page also links back to relevant playbooks.

For encoding and cryptography code, use the [Python cookbook](python3/#cookbook-map): Base encodings, XOR, classical ciphers, hashes/KDFs, AES modes, ChaCha20/XChaCha20, authenticated encryption and RSA.

## Read a command before copying it

```bash
# TShark example for a WSL installation, if supplied
tshark -r traffic.pcapng -Y 'http.request' -T fields -e http.request.uri
```

| Piece | Meaning |
| --- | --- |
| `tshark` | Executable |
| `-r traffic.pcapng` | Input capture |
| `-Y 'http.request'` | Display filter selecting HTTP requests |
| `-T fields` | Output selected fields rather than packet summaries |
| `-e http.request.uri` | Choose the URI field to print |

Options are tool-specific. Learn the operation and the option's argument together:

| Flag | Different meanings across approved tools |
| --- | --- |
| `-r` | TShark/Zeek: read PCAP; xxd: reverse hex; fls/ExifTool: recurse; fsck.fat: repair; Volatility: renderer |
| `-d` | objdump: disassemble; xz/OpenSSL enc: decompress/decrypt; Zimmerman parsers: directory; cannelloni: debug categories |
| `-e` | binwalk: extract; TShark: output field; strings: encoding; RsaCtfTool: public exponent |
| `-l` | xz: list; xxd: byte limit; pdftotext: last page; cannelloni: local port |
| `-o` | Many tools: output; Sleuth Kit: filesystem sector offset; Volatility: output directory |

Uppercase/lowercase matters: `-R` and `-r` can be unrelated. Short flags can sometimes combine (`xz -dk` = `-d -k`), but do not assume every parser permits that.

## Shell syntax used throughout

| Syntax | Meaning |
| --- | --- |
| `>` | Redirect stdout to a file; replaces existing content |
| `>>` | Append stdout |
| `2>` | Redirect stderr |
| `2>&1` | Send stderr to the current stdout destination |
| `A \| B` | Pass A's stdout into B |
| `# note` | Comment in Bash/PowerShell examples |
| `\` at Bash line end | Continue the command on the next line |
| Backtick at PowerShell line end | Continue the command on the next line |
| `'single quotes'` | Keep argument text literal under the shell's quoting rules |

Keep binary output in binary-preserving paths. Text exporters can use text pipelines; packet captures, extracted streams and attachments need byte-exact handling.

## Supporting shell flags used in the examples

| Utility / flag | Meaning |
| --- | --- |
| `grep -i` | Ignore letter case |
| `grep -n` | Show matching text line numbers |
| `grep -E` | Use extended regular expressions |
| `grep -a` | Treat binary input as text for this search |
| `grep -C N` | Show N lines before/after each matching line |
| `sort -u` | Sort and remove duplicate lines; original order is lost |
| `diff -u` | Show differences with surrounding text |
| `head -n N` | Show only the first N lines |
| `mkdir -p DIR` | Create parent directories as needed; existing directory is accepted |
| `ls -l -a -h` | Detailed listing, including dotfiles, with readable sizes |
| `sha256sum FILE` | Hash the file's bytes with SHA-256 |

For `dd`, `if=` is input, `of=` is output, `bs=` is block size, `skip=` skips input blocks, and `count=` limits copied blocks. Multiply block counts by block size to get byte positions. Every example using these supporting utilities explains its immediate goal.

## Tournament setup

- **Windows:** GUI tools and TShark, as listed below.
- **WSL:** Linux CLI tools; Burp and Ghidra require a working GUI/display setup.
- **Browser:** CyberChef and browser-only exercises.
- **Library rule from the supplied list:** Python/uv may add libraries except AI/ML related packages. Installing AI related libraries or sub-tools is prohibited for extensible tools generally.
- Most versions are listed as “latest”; the actual PC’s `--help` and installed build determine available options. The supplied list specifies **Ghidra 12.1.4** and **Burp 2026.4.x**. These are listed versions, not a claim that they are current upstream releases.

## How to read the commands

`bash` blocks run inside WSL. `powershell` blocks run in Windows PowerShell. `text` blocks show GUI recipes, filters or debugger commands; their heading tells you where to enter them.

Paths such as `/path/to/`, `C:\CTF\`, sample offsets, PIDs and `192.0.2.10` are placeholders. Replace them with your challenge values. `flag{demo}` is an example, not a tournament result.

Common shell utilities in examples (`grep`, `dd`, `cp`, etc.) are supporting commands; the supplied list does not separately establish their competition approval or availability.

## Start from the challenge

| You received | Good starting tools |
| --- | --- |
| Encoded text / cipher clue | CyberChef → Python → OpenSSL / RsaCtfTool |
| PNG/BMP/JPEG | ExifTool → strings → binwalk → zsteg / ZBar |
| PDF | PDF Viewer → pdftotext → ExifTool → qpdf |
| PCAP | Wireshark → TShark → Zeek |
| CAN endpoint / CAN log | cannelloni → can-utils |
| Linux executable | strings → objdump → Ghidra → gdb |
| Native Windows executable | strings / HxD → Ghidra → x64dbg |
| .NET executable | dnSpyEx |
| Disk image | Autopsy / The Sleuth Kit; fsck.fat for FAT diagnosis |
| Memory image | Volatility 3; SSH recovery plugin for matching Linux/OpenSSH evidence |
| Windows forensic artifacts | Eric Zimmerman's Tools |
| Web app / API | Chrome → Burp → jq / Python |

## All 39 tool notes

Origin: **1** = TrendMicro proposed; **2** = participant requested. Locations and categories below come from the user-supplied tournament list.

| No. | Tool note | Origin | Location | Category |
| --- | --- | --- | --- | --- |
| 1 | [CyberChef](cyberchef/) | 1 | Browser | Forensic, Network, Crypto, Web |
| 2 | [Wireshark](wireshark/) | 1 | Windows | Network, Forensic |
| 3 | [PDF Viewer](pdf_viewer/) | 1 | Windows | Stegano |
| 4 | [OpenVPN Client](openvpn_client/) | 1 | Windows | MISC |
| 5 | [Google Chrome](google_chrome/) | 1 | Windows | All |
| 6 | [WSL](wsl/) | 1 | Windows | All |
| 7 | [Python 3](python3/) | 1 | WSL | OSINT, Stegano, Crypto, Reversing, Web, Forensic, MISC |
| 8 | [uv](uv/) | 1 | WSL | MISC |
| 9 | [gdb](gdb/) | 1 | WSL | MISC, Reversing |
| 10 | [objdump](objdump/) | 1 | WSL | MISC, Reversing |
| 11 | [strings](strings/) | 1 | WSL | Stegano |
| 12 | [zsteg](zsteg/) | 1 | WSL | Stegano, Crypto |
| 13 | [binwalk](binwalk/) | 1 | WSL | Stegano |
| 14 | [ExifTool](exiftool/) | 1 | WSL | OSINT |
| 15 | [pdftotext](pdftotext/) | 1 | WSL | OSINT |
| 16 | [can-utils](can_utils/) | 1 | WSL | Network |
| 17 | [cannelloni](cannelloni/) | 1 | WSL | Network |
| 18 | [Zeek](zeek/) | 1 | WSL | Network |
| 19 | [ZBar](zbar/) | 1 | WSL | Stegano |
| 20 | [Burp Suite Community](burp_suite_community/) | 1 | WSL GUI | Web |
| 21 | [jq](jq/) | 1 | WSL | MISC, Web |
| 22 | [Ghidra](ghidra/) | 1 | WSL GUI | Reversing |
| 23 | [The Sleuth Kit](sleuth_kit/) | 1 | WSL | Forensic, Reversing |
| 24 | [OpenSSL](openssl/) | 1 | WSL | Forensic, Network, OSINT, Crypto |
| 25 | [xz](xz/) | 1 | WSL | Forensic |
| 26 | [qpdf](qpdf/) | 1 | WSL | Stegano |
| 27 | [llvm-mc](llvm_mc/) | 1 | WSL | Reversing |
| 28 | [xxd](xxd/) | 1 | WSL | Reversing |
| 29 | [fsck.fat](fsck_fat/) | 1 | WSL | Reversing |
| 30 | [RsaCtfTool](rsactftool/) | 1 | WSL | Crypto |
| 31 | [Volatility 3](volatility3/) | 1 | WSL | Forensic |
| 32 | [OpenSSH-Session-Key-Recovery](openssh_session_key_recovery/) | 1 | Volatility 3 plugin | Not specified in supplied list |
| 33 | [x64dbg](x64dbg/) | 2 | Windows | Reversing |
| 34 | [Autopsy](autopsy/) | 2 | Windows | Forensic |
| 35 | [HxD](hxd/) | 2 | Windows | Forensic, Reversing, Stegano |
| 36 | [TShark](tshark/) | 2 | Windows | Network, Forensic |
| 37 | [Notepad++](notepad_plus_plus/) | 2 | Windows | Reversing |
| 38 | [dnSpyEx](dnspyex/) | 2 | Windows | Reversing |
| 39 | [Eric Zimmerman's Tools](eric_zimmerman_tools/) | 2 | Windows | Forensic |

## Before working on an artifact

```bash
# WSL: keep one directory per challenge and record the input hash
mkdir -p ~/ajcbbc/challenge01/out
cd ~/ajcbbc/challenge01
sha256sum challenge.bin > input_sha256.txt
```

Work on copies for patches/repairs. Record the exact command, input, useful output and next step. For stateful network challenges, keep the session alive until the objective’s final result appears.

Each tool page links to its official documentation or upstream project. Commands are reference examples; they have not been executed on the competition PCs.
