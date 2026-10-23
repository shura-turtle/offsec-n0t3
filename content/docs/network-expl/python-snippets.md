---
title: "09 · Python / Ready Helpers"
weight: 9
bookToc: true
---

# Network Python Helpers

**Tools:** [Python 3](../../ajcbbc_allow_tools/python3/) for scripts; [TShark](../../ajcbbc_allow_tools/tshark/) for packet parsing; [CyberChef](../../ajcbbc_allow_tools/cyberchef/) for visual encoding checks. Both downloads use Python's standard library only.

Use an existing snippet only if the event permits prepared code. Keep the source offline alongside your notes and adapt endpoint/protocol values explicitly.

## 1. Downloads

| Helper | Purpose | Input |
| --- | --- | --- |
| [session_client.py](/snippets/network/session_client.py) | One persistent TCP conversation; exact send bytes; bounded buffered receive | Host, port, JSON operation plan |
| [dns_reconstruct.py](/snippets/network/dns_reconstruct.py) | Suffix-aware, ordered DNS data reconstruction | Bare qnames or final-column qname TSV |

Save the `.py` files locally. A browser may display the source; use Save As or copy the full file. They do not require an online API, AI library, or packet parsing package.

```bash
python3 session_client.py --help
python3 dns_reconstruct.py --help
```

## 2. TCP plan operations

```json
[
  {"read_until_hex": "3e20", "timeout": 5},
  {"send_text": "STATUS\r\n"},
  {"read_until_hex": "3e20"},
  {"send_file": "payload.bin"},
  {"read_for": 10}
]
```

| Operation | Behavior |
| --- | --- |
| `send_text` | Encode the exact string using UTF-8, or the action's `encoding` |
| `send_hex` | Decode hex to bytes and send exactly those bytes |
| `send_file` | Send the file bytes; relative paths are beside the plan |
| `read_until_hex` | Read through delimiter; retain surplus for the next read |
| `read_for` | Collect incoming bytes for a total number of seconds or until EOF |
| `shutdown_write` | Half-close TCP sending; only for protocols expecting it |

For a half-close action, write `{"shutdown_write": true}`. Do not use it just to “flush” a connection; it tells the peer no further bytes will be sent.

```bash
python3 session_client.py 192.0.2.10 31337 plan.json \
  --timeout 5 --max-bytes 8388608 --transcript session.jsonl
```

No newline is automatically added. `"\r\n"` in JSON becomes CRLF; `"\\r\\n"` would send literal backslash characters. Use `send_hex` when escape handling is uncertain.

## 3. Interpret TCP results correctly

Every operation prints JSON with status, byte length, hex, and a text preview. Hex is authoritative for binary data. JSON text displays escaped control bytes intentionally.

| Status | Interpretation |
| --- | --- |
| `connected` | TCP connection established |
| `sent` | Bytes handed to socket; no proof application accepted them |
| `delimiter` | Exact expected byte delimiter received |
| `timeout` | Delimiter not reached before deadline |
| `deadline` | `read_for` collection period ended |
| `eof` | Peer closed its sending side |
| `limit` | Receive size cap reached; session stops |
| `connection_error` / `error` | Transport or plan operation failed |

On `read_until_hex` timeout, buffered data is retained. Its record has `buffered_preview: true`; this preview is not a newly consumed message. Repeated preview records can contain the same bytes.

To explicitly continue after that timeout:

```json
{"read_until_hex":"0a", "timeout":2, "allow_timeout":true}
```

Normally a missing prompt should stop the plan so a subsequent payload is not sent in the wrong state. EOF before a required delimiter stops it as well. The script does not infer objective completion from ACK text.

Exit status 0 means the plan completed, not that a flag was obtained. Status 2 is a connection/operation error, 3 is timeout/size-limit stop, and 4 is premature EOF.

## 4. DNS helper layouts

Input:

```text
1700000000.000000	0000.666c6167.exfil.example
1700000000.100000	0001.7b64656d6f7d.exfil.example
```

Use actual tabs in TSV. Bare query names also work.

```bash
python3 dns_reconstruct.py queries.tsv --suffix exfil.example \
  --sequence --start 0 --encoding hex --out recovered.bin
```

Expected bytes for those payload labels: `flag{demo}`.

`--sequence` recognizes a decimal first label and rejects missing/conflicting indices. Without it, capture order and duplicates are kept. `--start 1` supports transfers starting at 1; split separate transfers before decoding.

`--encoding` supports `hex`, `base32`, `base64`, `base64url`, and `ascii`. Missing terminal padding is restored for Base32/Base64. Invalid alphabets are rejected rather than silently removed.

## 5. Decide when to decode chunks

```text
continuous encoded stream -> split into DNS chunks -> join chunks -> decode once
individual raw chunks -> encode each independently -> decode chunks -> join bytes
```

The default is join then decode. Add `--per-chunk` for independently encoded query payloads. Applying the wrong order can corrupt data even when the alphabet looks valid.

The helper strips only the configured suffix and optional numeric sequence label. If the protocol adds client IDs, checksums, or length labels, isolate them first based on source/evidence.

## 6. Byte operations worth keeping

```python
import base64
import struct
from urllib.parse import unquote_to_bytes

print(bytes.fromhex('666c6167'))
print(base64.b64decode('ZmxhZw==', validate=True))
print(unquote_to_bytes('%66%6c%61%67'))
print(struct.unpack('!H', bytes.fromhex('1234'))[0])
print(int.from_bytes(bytes.fromhex('3412'), 'little'))
```

Use a file's raw bytes with `Path(...).read_bytes()`. Avoid newline conversion and lossy decoding. `bytes.fromhex` accepts whitespace; if whitespace is part of the protocol's alphabet, first decide whether it is framing or data.

## 7. Capture parsing belongs to the packet tool

Use TShark/Wireshark to handle PCAPNG interfaces, link-layer formats, IP fragmentation, and TCP reassembly. A tiny script that assumes every packet has a 14-byte Ethernet header will break on many real captures.

Export a well-defined field/object, preserve its frame/stream references, then feed those bytes into the helper. Neither supplied script reads PCAP directly.

**Related:** [DNS workflow](../dns/) · [TCP/UDP protocol workflow](../tcp-udp/) · [Packet triage](../packet-triage/).

References: [socket](https://docs.python.org/3/library/socket.html), [base64](https://docs.python.org/3/library/base64.html), [struct](https://docs.python.org/3/library/struct.html).
