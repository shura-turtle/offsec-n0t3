---
title: "39 Tools · Technique Map"
weight: 2
bookToc: true
---

# Existing Tools → Challenge Workflows

This map links your existing 39 [AJCBBC tool notes](../../ajcbbc_allow_tools/) to the new technique collections. It describes use, not an expanded competition allowlist. Optional dependencies/plugins remain subject to event rules.

## Decode, inspect, and prepare

| Tool | Start with it when | Workflow |
| --- | --- | --- |
| [CyberChef](../../ajcbbc_allow_tools/cyberchef/) | Encodings, XOR, compression, supplied crypto parameters | [Visual recipes](../cyberchef-cheatsheet/) |
| [Python 3](../../ajcbbc_allow_tools/python3/) | Repeat a byte transformation or decode structured data | [Snippet library](../python-library/) |
| [uv](../../ajcbbc_allow_tools/uv/) | Prepare a permitted isolated Python dependency environment | [Reversing helpers](../../reversing-expl/python-snippets/) |
| [WSL](../../ajcbbc_allow_tools/wsl/) | Run Linux CLI tools from Windows | All CLI workflows; mind Windows/WSL paths |
| [Notepad++](../../ajcbbc_allow_tools/notepad_plus_plus/) | Inspect text, encodings, line endings and regex matches | [Unicode/text](../../steganograph-expl/text-unicode/) |
| [HxD](../../ajcbbc_allow_tools/hxd/) | Inspect offsets, signatures, byte changes | [File triage](../../steganograph-expl/triage/) |
| [xxd](../../ajcbbc_allow_tools/xxd/) | Reversible byte/hex inspection | [Reversing strings](../../reversing-expl/strings-encodings/) |
| [strings](../../ajcbbc_allow_tools/strings/) | Fast ASCII/UTF-16 string triage | [Static analysis](../../reversing-expl/static-analysis/) |
| [xz](../../ajcbbc_allow_tools/xz/) | XZ/LZMA archive/container clue | [Archives/carving](../../steganograph-expl/archives-carving/) |

## Web

| Tool | Start with it when | Workflow |
| --- | --- | --- |
| [Chrome](../../ajcbbc_allow_tools/google_chrome/) | Inspect requests, DOM, JS, storage, WebSocket messages | [First 10 minutes](../../web-expl/methodology/) |
| [Burp Community](../../ajcbbc_allow_tools/burp_suite_community/) | Capture/replay exact HTTP parameters and compare responses | [Web payload index](../../web-expl/) |
| [jq](../../ajcbbc_allow_tools/jq/) | Inspect API JSON and structured exports | [GraphQL](../../web-expl/graphql/) / [NoSQL](../../web-expl/nosqli/) |

## Network and protocol analysis

| Tool | Start with it when | Workflow |
| --- | --- | --- |
| [OpenVPN Client](../../ajcbbc_allow_tools/openvpn_client/) | Challenge requires the supplied VPN | Establish access first; preserve route details |
| [Wireshark](../../ajcbbc_allow_tools/wireshark/) | Explore packet conversations and follow streams | [Packet triage](../../network-expl/packet-triage/) |
| [TShark](../../ajcbbc_allow_tools/tshark/) | Repeat filters, export fields/objects | [HTTP extraction](../../network-expl/http-streams/) |
| [Zeek](../../ajcbbc_allow_tools/zeek/) | Summarize PCAP sessions at scale | [Protocol overview](../../network-expl/protocols/) |
| [OpenSSL](../../ajcbbc_allow_tools/openssl/) | Inspect certs/keys or explicit crypto parameters | [TLS / SSH](../../network-expl/tls-ssh/) |
| [cannelloni](../../ajcbbc_allow_tools/cannelloni/) | Challenge provides a CAN-over-UDP tunnel | [CAN bus](../../network-expl/can-bus/) |
| [can-utils](../../ajcbbc_allow_tools/can_utils/) | Inspect/replay an authorized CAN interface/log | [CAN bus](../../network-expl/can-bus/) |

## Images, documents, archives

| Tool | Start with it when | Workflow |
| --- | --- | --- |
| [ExifTool](../../ajcbbc_allow_tools/exiftool/) | Metadata, embedded comments, file-type mismatch | [Stego triage](../../steganograph-expl/triage/) |
| [binwalk](../../ajcbbc_allow_tools/binwalk/) | Embedded data signatures / container offsets | [Archives/carving](../../steganograph-expl/archives-carving/) |
| [zsteg](../../ajcbbc_allow_tools/zsteg/) | PNG/BMP low-bit data candidates | [Image LSB](../../steganograph-expl/images-lsb/) |
| [ZBar](../../ajcbbc_allow_tools/zbar/) | Barcode/QR clue | [Image formats](../../steganograph-expl/png-jpeg/) |
| [PDF Viewer](../../ajcbbc_allow_tools/pdf_viewer/) | Layers, visible text, annotation clue | [PDF/documents](../../steganograph-expl/pdf-documents/) |
| [pdftotext](../../ajcbbc_allow_tools/pdftotext/) | Extract PDF text for searching | [PDF/documents](../../steganograph-expl/pdf-documents/) |
| [qpdf](../../ajcbbc_allow_tools/qpdf/) | Inspect PDF structure, streams, attachments | [PDF/documents](../../steganograph-expl/pdf-documents/) |

## Disk and memory forensics

| Tool | Start with it when | Next step |
| --- | --- | --- |
| [Autopsy](../../ajcbbc_allow_tools/autopsy/) | Filesystem image and timeline | Identify partition/filesystem → browse/recover artifacts |
| [The Sleuth Kit](../../ajcbbc_allow_tools/sleuth_kit/) | Need reproducible partition/file extraction | Correct sector offset → list entries → extract exact inode |
| [fsck.fat](../../ajcbbc_allow_tools/fsck_fat/) | FAT corruption clue | Diagnose a copy before any repair |
| [Volatility 3](../../ajcbbc_allow_tools/volatility3/) | Memory image | Identify OS/process → relevant plugin → export evidence |
| [OpenSSH key recovery](../../ajcbbc_allow_tools/openssh_session_key_recovery/) | Matching Linux/OpenSSH memory evidence | Validate plugin/version/process preconditions |
| [Eric Zimmerman's Tools](../../ajcbbc_allow_tools/eric_zimmerman_tools/) | Windows event/artifact evidence | Choose parser matching artifact → correlate timestamp/context |

## Reversing and cryptography

| Tool | Start with it when | Workflow |
| --- | --- | --- |
| [Ghidra](../../ajcbbc_allow_tools/ghidra/) | Native executable, data flow and decompilation | [Ghidra cheatsheet](../../reversing-expl/ghidra-cheatsheet/) |
| [gdb](../../ajcbbc_allow_tools/gdb/) | Linux runtime registers/memory/checker | [Dynamic debugging](../../reversing-expl/dynamic-debugging/) |
| [objdump](../../ajcbbc_allow_tools/objdump/) | Fast disassembly and section/import view | [Static analysis](../../reversing-expl/static-analysis/) |
| [llvm-mc](../../ajcbbc_allow_tools/llvm_mc/) | Encode/decode an instruction for a known architecture | [Static analysis](../../reversing-expl/static-analysis/) |
| [x64dbg](../../ajcbbc_allow_tools/x64dbg/) | Native Windows executable at runtime | [Dynamic debugging](../../reversing-expl/dynamic-debugging/) |
| [dnSpyEx](../../ajcbbc_allow_tools/dnspyex/) | .NET assembly, managed metadata and IL | [.NET reversing](../../reversing-expl/dotnet/) |
| [RsaCtfTool](../../ajcbbc_allow_tools/rsactftool/) | RSA key/ciphertext with exploitable conditions | [Python crypto cookbook](../../ajcbbc_allow_tools/python3/#cookbook-map) |

## One complete example

```text
PCAP
  → Wireshark protocol hierarchy
  → TShark HTTP object/stream extraction
  → identify exported file bytes
  → CyberChef decode only if evidence supports it
  → Ghidra for a native executable, zsteg for a suitable lossless image
  → Python helper reproduces the confirmed transform
```

Tool output is a lead, not the final answer. Preserve the originating packet/file offset, exact operation, and verification result.
