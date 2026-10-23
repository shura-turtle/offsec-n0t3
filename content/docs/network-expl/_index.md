---
title: "Network Exploitation"
weight: -9
bookCollapseSection: true
bookToc: true
description: "Offline packet analysis, protocol sessions, wireless captures, CAN workflows, and reusable Python helpers."
---

# Network Field Notes

**Flow:** identify the transport → identify the application → reconstruct the conversation → extract the actual object → verify the result.

Use the supplied capture, service description, source, memory dump, or protocol specification as your starting evidence. A port number is a hint; the bytes and negotiated protocol determine the next action.

## Choose your starting point

| What the challenge provides | Start here | First useful result |
| --- | --- | --- |
| PCAP / PCAPNG with no context | [Packet triage](packet-triage/) | Hosts, times, protocols, candidate streams |
| Web requests, uploads, downloads | [HTTP and streams](http-streams/) | Correct request/response and saved object |
| Many DNS queries / odd hostnames | [DNS](dns/) | Ordered labels and decoded bytes |
| TLS / HTTPS / SSH | [TLS and SSH](tls-ssh/) | Metadata; determine whether matching secrets exist |
| A TCP/UDP host and port | [TCP/UDP sessions](tcp-udp/) | Exact framing, status semantics, persistent session |
| 802.11 / radiotap / EAPOL | [Wi-Fi](wifi/) | SSID, station/AP pair, security mode, usable handshake |
| CAN log / cannelloni endpoint | [CAN bus](can-bus/) | IDs, frame changes, protocol-defined state transition |
| FTP / mail / ICMP / SMB | [Other protocols](protocols/) | Transfer channel, messages, attachments, or file objects |
| Need a ready offline helper | [Python snippets](python-snippets/) | TCP conversation or ordered DNS reconstruction |

## Approved tool route

These links point to this notebook's supplied tournament tool list. Actual event rules still control which features and existing snippets you can use.

| Task | Approved tool page | Practical operation |
| --- | --- | --- |
| Visual packet inspection | [Wireshark](../ajcbbc_allow_tools/wireshark/) | Follow stream, protocol tree, export objects |
| Repeatable packet extraction | [TShark](../ajcbbc_allow_tools/tshark/) | Display filters, field export, conversation statistics |
| Connection / application summaries | [Zeek](../ajcbbc_allow_tools/zeek/) | Offline logs for capture triage |
| Encoding and byte inspection | [CyberChef](../ajcbbc_allow_tools/cyberchef/), [HxD](../ajcbbc_allow_tools/hxd/), [xxd](../ajcbbc_allow_tools/xxd/) | Decode only the selected payload bytes |
| Script a known protocol | [Python 3](../ajcbbc_allow_tools/python3/) | Standard-library sockets, struct, base64, hashlib |
| Certificate / TLS checks | [OpenSSL](../ajcbbc_allow_tools/openssl/) | Parse certificates, inspect supplied endpoint TLS |
| SSH keys in memory | [OpenSSH recovery](../ajcbbc_allow_tools/openssh_session_key_recovery/) | Match memory-derived key material to the connection |
| CAN frames over IP | [cannelloni](../ajcbbc_allow_tools/cannelloni/) | Preserve tunnel and local receiving path |
| Local CAN observe / replay | [can-utils](../ajcbbc_allow_tools/can_utils/) | candump, cansend, canplayer |
| Linux command environment | [WSL](../ajcbbc_allow_tools/wsl/) | Run supplied CLI tools; kernel/network constraints apply |

No aircrack suite, unrestricted scanner, or extra packet library is assumed by these pages.

## First five minutes

1. Keep the original capture unchanged. Record its name, byte size, and hash.
2. Open it in Wireshark; check **Statistics → Protocol Hierarchy** and **Conversations**.
3. Check capture time span, interfaces, dropped/truncated packet clues, and link-layer type.
4. Select one candidate stream and follow both directions.
5. Decide whether you have plaintext, an encoded application field, encrypted transport, or an incomplete capture.
6. Export the smallest relevant object while preserving the original stream/packet references.

A capture containing no plaintext flag can still disclose a filename, hostname, session identity, request ID, key-log hint, or archive password.

## Keep an evidence record

```text
Input: challenge.pcapng
SHA-256: ...
Candidate: tcp.stream 7
Packet range: 140–188
Client/server: 192.0.2.10:51514 -> 192.0.2.20:8080
Why selected: POST /upload followed by binary response
Saved artifact: objects/payload.zip
Next check: file signature, archive contents, password source
Verified result: ...
```

Stream numbers belong to the particular capture and dissector processing. Preserve the input when citing them.

## Distinguish the layers

```text
Ethernet / 802.11
  -> IPv4 / IPv6
     -> TCP stream / UDP datagrams
        -> TLS or application framing
           -> HTTP / DNS / FTP / custom protocol
              -> Base64 / compression / archive / file
```

Base64 decoding a TLS record does not decrypt it. Concatenating TCP payloads does not automatically reconstruct HTTP bodies. A UDP packet boundary can be an application boundary, but a protocol may split its own message across several datagrams.

## When the obvious attempt fails

| Observation | Check before changing the payload |
| --- | --- |
| No HTTP dissector output | Correct port, Decode As, TLS, HTTP/2, capture completeness |
| Exported file corrupt | Direction, transfer framing, reassembly, compression, missing bytes |
| DNS reconstruction garbled | Retry handling, sequence labels, encoding, suffix stripping |
| Service responds once then stops | Protocol state, message framing, authentication, EOF vs timeout |
| ACK but no flag | Required setup, message semantics, asynchronous status |
| CAN tunnel sends but receives nothing | Local interface, UDP return port, VPN/WSL routing |
| Wi-Fi key known but traffic unreadable | Correct AP/SSID, handshake, cipher support, session key material |

## Final verification

- Reopen exported artifacts using an appropriate approved tool.
- Confirm magic bytes and length rather than trusting an extension.
- Decode a candidate value and compare it with its source field.
- For live stateful tasks, keep the same connection/tunnel alive until the service reports the objective.
- Record the final flag/result immediately; avoid extra speculative actions after success.

**Next:** [Packet triage](packet-triage/) or [TCP/UDP sessions](tcp-udp/).
