---
title: "01 · Packet Triage"
weight: 1
bookToc: true
---

# Packet Triage

**Flow:** capture health → protocol hierarchy → conversations → candidate stream → exported evidence.

**Tools:** [Wireshark](../../ajcbbc_allow_tools/wireshark/), [TShark](../../ajcbbc_allow_tools/tshark/), [Zeek](../../ajcbbc_allow_tools/zeek/), [Python](../../ajcbbc_allow_tools/python3/).

## 1. Preserve the input and establish scale

```python
from pathlib import Path
import hashlib
p = Path('traffic.pcapng')
h = hashlib.sha256()
with p.open('rb') as source:
    for chunk in iter(lambda: source.read(1024 * 1024), b''):
        h.update(chunk)
print(p.name, p.stat().st_size, h.hexdigest())
```

Do not hash text output from `tshark`; hash the actual input bytes.

In Wireshark, open **Statistics → Capture File Properties**. Note interfaces, encapsulation, capture length, time range, and packet count. A snap length that cuts off application data limits extraction even if TCP headers are present.

## 2. Inventory protocols and conversations

Commands below use a shell with TShark on PATH. The [Windows tool page](../../ajcbbc_allow_tools/tshark/) shows the full executable path.

```bash
tshark -r traffic.pcapng -q -z io,phs
tshark -r traffic.pcapng -q -z conv,tcp
tshark -r traffic.pcapng -q -z conv,udp
tshark -r traffic.pcapng -q -z endpoints,ip
```

| Output | What to prioritize |
| --- | --- |
| A rare protocol | Inspect decoded fields before assuming a tunnel |
| One very large TCP flow | File transfer, video, encrypted bulk traffic |
| Many small DNS queries | DNS label content, retries, TXT answers |
| Short repeated connections | Polling, retries, authentication, application heartbeats |
| UDP with changing binary fields | Datagram framing / custom telemetry |

Large traffic volume does not guarantee relevance. A small request can contain the only password.

## 3. Look for evidence-bearing protocols

Wireshark display filters:

```text
http.request
http.response
dns
ftp || ftp-data
smtp || imap || pop
smb2
icmp || icmpv6
tls.handshake
ssh
```

If a field or protocol name is rejected, use the installed display-filter autocomplete or packet tree. Dissector field names can differ between versions.

```bash
tshark -G protocols
tshark -G fields
```

These enumerate local capabilities; they do not read the challenge capture.

## 4. Export a compact timeline

```bash
tshark -r traffic.pcapng -T fields -E header=y -E separator=/t \
  -e frame.number -e frame.time_relative \
  -e ip.src -e ipv6.src -e tcp.srcport -e udp.srcport \
  -e ip.dst -e ipv6.dst -e tcp.dstport -e udp.dstport \
  -e _ws.col.Protocol -e _ws.col.Info > timeline.tsv
```

`-r` reads a capture; `-T fields` exports selected decoded fields; `-e` selects one field; `-E` controls text output. `separator=/t` requests a tab separator.

Do not treat an exported field table as a packet capture. It can omit payloads, retransmissions, repeated field values, and interface metadata.

## 5. Inspect one stream

```text
ip.addr == 192.0.2.10
tcp.stream eq 7
udp.stream eq 2
```

```bash
tshark -r traffic.pcapng -q -z follow,tcp,ascii,7
tshark -r traffic.pcapng -Y 'tcp.stream eq 7' -w stream7.pcapng
```

The first command prints a human-readable followed stream. The second saves selected packets as a new capture. Neither is automatically a clean application file.

For an exact binary object, use protocol export or the correct directional **Follow Stream → Show data as Raw → Save As** workflow. Keep framing bytes in mind.

## 6. Search carefully

```text
frame contains "flag"
tcp contains "password"
http.request.uri contains "download"
dns.qry.name contains "challenge"
```

A packet-byte search can miss strings split across packets, compressed content, or encrypted records. Compare it with stream follow and object export. Check headers, cookies, URLs, request bodies, response bodies, filenames, and metadata.

A literal flag-like string can be a decoy or an example. Trace it to the actual challenge objective.

## 7. Use Zeek for a second view

```bash
zeek -r traffic.pcapng
```

Run in a separate output directory: Zeek writes logs into the working directory. Inspect `conn.log`, then protocol logs actually produced, such as `http.log` or `dns.log`. Absent logs can mean encryption, missing handshake, unsupported encapsulation, or a missing analyzer.

Zeek summaries and Wireshark dissections can disagree because they reconstruct and classify traffic differently. Return to the packets to resolve the discrepancy.

## 8. Health checks before trusting extraction

```text
frame.cap_len < frame.len
tcp.analysis.retransmission
tcp.analysis.lost_segment
tcp.analysis.out_of_order
```

These are investigation clues. Outbound checksum failures can be capture-offload artifacts; a “previous segment not captured” warning can arise from starting midstream. Do not discard a stream solely because Expert Information reports a warning.

## Decision checkpoint

| Result | Next page |
| --- | --- |
| Web object / request | [HTTP](../http-streams/) |
| Suspicious DNS names | [DNS](../dns/) |
| Encrypted traffic | [TLS/SSH](../tls-ssh/) |
| Unknown binary/text stream | [TCP/UDP](../tcp-udp/) |
| Mail/file-share/ping | [Protocols](../protocols/) |

Reference: [TShark manual](https://www.wireshark.org/docs/man-pages/tshark.html) for local field and statistics options.
