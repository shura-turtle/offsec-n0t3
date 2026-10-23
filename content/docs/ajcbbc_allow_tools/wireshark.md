---
title: "Wireshark"
weight: 2
bookToc: true
---

**Use for:** PCAP triage, conversations, file transfers, protocol inspection.  
**Run in:** Windows GUI. Use [TShark](../tshark/) for CLI extraction.

## First pass

1. **File → Open** the capture.
2. Check **Statistics → Protocol Hierarchy**, **Endpoints**, and **Conversations**.
3. Apply a display filter in the top bar.
4. Right click a relevant packet → **Follow → TCP Stream** or **UDP Stream**.
5. Record the stream number and packet numbers.

## Display filters

```text
http
http.request
http.request.method == "POST"
http.request.uri contains "flag"
dns
dns.qry.name contains "example"
ip.addr == 192.0.2.10
tcp.port == 8080
tcp.stream eq 0
udp.stream eq 0
frame contains "flag"
tls.handshake.extensions_server_name
```

`frame contains` searches packet bytes; reassembled content may require following the stream.

## Walkthrough: recover an HTTP download

1. Filter `http` and locate the request/response.
2. **File → Export Objects → HTTP**.
3. Select the object and save it into your output folder.
4. Inspect it with the appropriate approved tool.

For encrypted TLS, use **Preferences → Protocols → TLS → (Pre)-Master-Secret log filename** only when matching secrets are provided. A server private key alone does not generally decrypt modern TLS.

## Gotchas

- Capture filter: `host 192.0.2.10`. Display filter: `ip.addr == 192.0.2.10`.
- No HTTP results? Check the port and **Analyze → Decode As**.
- Missing packets or a truncated capture can prevent reassembly.

## CTF: reconstruct a plaintext conversation

1. Sort **Conversations** by bytes or duration to find candidates.
2. Select a packet and follow its stream.
3. Inspect both directions; requests and replies can contain separate clues.
4. Switch display between ASCII, hex and raw as needed.
5. Save the relevant stream, noting whether both directions or one direction was selected.
6. Decode embedded Base64/hex separately in CyberChef.

For file recovery, prefer **Export Objects** when a protocol exporter exists. A raw bidirectional stream can mix control messages and transferred bytes.

## CTF: DNS tunnel clues

```text
dns.flags.response == 0
dns.qry.type == 16
dns.qry.name contains "challenge.example"
```

Inspect long labels, repeated suffixes and response TXT data. Record timestamps and packet numbers. Labels may contain sequence counters, retransmissions and encoding chunks; concatenate only after establishing their format and order.

## CTF: nonstandard HTTP port

```text
tcp.port == 8081
```

If payload bytes look like HTTP but Wireshark does not decode it, select a packet → **Analyze → Decode As** → choose HTTP for the relevant port. Then retry `http.request` and object export. Do not force a decoder without inspecting the bytes.

## CTF: FTP and mail traffic

```text
ftp
ftp-data
smtp || pop || imap
```

Follow control sessions to identify login exchanges and transfer names. FTP data can be on a separate connection. MIME mail attachments can require content-transfer decoding after reconstructing the message.

## CTF: find TLS host clues

```text
tls.handshake.type == 1
tls.handshake.extensions_server_name
```

An observed ClientHello can reveal an SNI hostname. Missing SNI may reflect a partial capture, protocol changes or encrypted client hello; it does not prove no hostname exists.

## CTF: inspect missing/repeated data

```text
tcp.analysis.retransmission
tcp.analysis.out_of_order
tcp.analysis.lost_segment
tcp.flags.reset == 1
```

These are analysis indicators. Capture location and packet ordering can produce apparent anomalies. When bytes are missing, document that limitation before treating a recovered file as complete.

## Decode values from individual fields

Click a field in the packet details → inspect selected bytes → copy its value or bytes. A displayed decimal number, hex string and wire bytes can represent the same value differently. Use the protocol’s documented endianness.

## GUI filter syntax versus CLI flags

Wireshark’s filter bar takes expressions, not switches such as `-r`. Use [TShark](../tshark/) for command-line flags. In `tcp.stream eq 3`, `eq` means equality and `3` is the stream index. `&&` / `and` combines conditions; `||` / `or` accepts either condition.

## Suggested investigation record

```text
capture: traffic.pcapng
question: <what the challenge asks>
filter: <exact expression>
stream: <index and protocol>
frames: <relevant packet numbers>
recovered file: <path + hash>
decode steps: <ordered recipe>
remaining limitation: <missing packets / encryption / none known>
```

References: [Wireshark User’s Guide](https://www.wireshark.org/docs/wsug_html_chunked/), [TCP analysis](https://www.wireshark.org/docs/wsug_html_chunked/ChAdvTCPAnalysis.html).

## Related playbooks

- [Packet triage](../../network-expl/packet-triage/)
- [HTTP and stream recovery](../../network-expl/http-streams/)
- [Wi-Fi captures](../../network-expl/wifi/)
