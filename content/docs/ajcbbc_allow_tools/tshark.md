---
title: "TShark"
weight: 36
bookToc: true
---

**Use for:** repeatable PCAP filtering, field extraction and stream recovery.  
**Run in:** Windows PowerShell; included with the approved Wireshark installation.

## Set the executable path

```powershell
$Tshark = 'C:\Program Files\Wireshark\tshark.exe'
& $Tshark --version
```

If already on PATH, replace `& $Tshark` with `tshark`. These commands also work with a supplied WSL binary after adapting shell syntax.

## Triage protocols and conversations

```powershell
& $Tshark -r .\traffic.pcapng -q -z io,phs
& $Tshark -r .\traffic.pcapng -q -z conv,tcp
& $Tshark -r .\traffic.pcapng -q -z endpoints,ip
```

## Extract DNS and HTTP fields

```powershell
& $Tshark -r .\traffic.pcapng -Y 'dns.flags.response == 0' `
  -T fields -e frame.number -e ip.src -e dns.qry.name

& $Tshark -r .\traffic.pcapng -Y 'http.request' `
  -T fields -e tcp.stream -e http.host -e http.request.uri
```

## Read a stream or save selected packets

```powershell
# Replace 0 with the relevant stream index
& $Tshark -r .\traffic.pcapng -q -z 'follow,tcp,ascii,0'

& $Tshark -r .\traffic.pcapng -Y 'tcp.stream eq 0' -w .\stream0.pcapng
```

## Export HTTP objects

```powershell
New-Item -ItemType Directory -Force .\http_objects | Out-Null
& $Tshark -r .\traffic.pcapng --export-objects 'http,http_objects'
```

## CTF gotchas

- `-Y` is a display filter; `-f` is a capture filter.
- `-w` saves packets, not decoded text.
- Live capture needs an appropriate interface/driver; offline `-r` does not.
- PowerShell continuation uses a backtick at line end, with no trailing space.

## Flags used on this page

| Flag | Meaning | Example |
| --- | --- | --- |
| `-r FILE` | Read an existing capture | `-r traffic.pcapng` |
| `-Y EXPR` | Select decoded packets with a display filter | `-Y 'dns'` |
| `-f EXPR` | Apply capture filter during live capture | `-f 'tcp port 80'` |
| `-T fields` | Emit selected protocol fields | Pair with `-e` |
| `-e FIELD` | Add one output field; repeat it | `-e ip.src` |
| `-E KEY=VALUE` | Configure fields formatting | `-E header=y` |
| `-q` | Suppress ordinary packet summaries | Useful with `-z` |
| `-z STAT` | Generate statistics or follow a stream | `-z conv,tcp` |
| `-w FILE` | Save packets in capture format | Not a text report |
| `-V` | Show full decoded packet details | Useful for one filtered frame |
| `-x` | Include a hex/ASCII byte dump | Inspect wire bytes |
| `-d RULE` | Force protocol decode for a port | `tcp.port==8081,http` |
| `-G fields` | List recognized field names | Resolve version differences |
| `--export-objects TYPE,DIR` | Save supported reassembled objects | `http,http_objects` |

## CTF: produce a CSV of HTTP requests

```powershell
& $Tshark -r .\traffic.pcapng -Y 'http.request' `
  -T fields -E header=y -E separator=, -E quote=d `
  -e frame.number -e ip.src -e tcp.stream -e http.host -e http.request.uri |
  Set-Content -Encoding utf8 .\http_requests.csv
```

`header=y` prints names, `separator=,` chooses commas, and `quote=d` quotes fields with double quotes. This is a text export; shell text encoding is appropriate here.

## CTF: enumerate DNS query values

```powershell
& $Tshark -r .\traffic.pcapng -Y 'dns.flags.response == 0' `
  -T fields -e frame.time_epoch -e dns.qry.name |
  Set-Content -Encoding utf8 .\dns_queries.tsv
```

Inspect sequence markers and duplicates before assembling encoded subdomains. Capture order alone may include retransmissions.

## CTF: inspect a suspicious packet deeply

```powershell
# Replace 120 with the frame number found during triage
& $Tshark -r .\traffic.pcapng -Y 'frame.number == 120' -V -x
```

Compare decoded fields with raw bytes when a protocol command ID, length or integer matters.

## CTF: force HTTP decoding on a custom port

```powershell
& $Tshark -r .\traffic.pcapng -d 'tcp.port==8081,http' `
  -Y 'http.request' -T fields -e http.request.uri
```

## CTF: recover one UDP conversation

```powershell
& $Tshark -r .\traffic.pcapng -Y 'udp' -T fields -e udp.stream
& $Tshark -r .\traffic.pcapng -q -z 'follow,udp,hex,0'
```

The follow report contains framing/labels around payloads; it is not a raw binary file. Use protocol object export or a careful parser for exact byte recovery.

## Find a field name before using it

```powershell
& $Tshark -G fields | Select-String 'dns.txt|http.file_data|tcp.payload'
```

A field can be absent because the installed version differs, the traffic was not decoded, or that packet has no such field.

Reference: [TShark manual](https://www.wireshark.org/docs/man-pages/tshark.html).
