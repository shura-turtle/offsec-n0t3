---
title: "05 · TCP / UDP Sessions"
weight: 5
bookToc: true
---

# TCP and UDP: Framing, State, and Exact Bytes

**Flow:** establish liveness → identify framing → read banner → send exact message → interpret reply → keep the session through success.

**Tools:** [Wireshark](../../ajcbbc_allow_tools/wireshark/), [TShark](../../ajcbbc_allow_tools/tshark/), [Python](../../ajcbbc_allow_tools/python3/), [HxD](../../ajcbbc_allow_tools/hxd/).

## 1. Separate transport failure from payload failure

| Observation | Meaning | Next action |
| --- | --- | --- |
| Connection refused | No listener / explicit rejection on that address | Verify current endpoint |
| Connect timeout | Routing/filtering/unresponsive endpoint | One minimal liveness check |
| TCP connected, no bytes | May be waiting for client message | Read protocol/source before sending |
| `recv()` returns `b''` | TCP peer closed its sending side | Preserve bytes already read; classify EOF |
| Socket timeout | No bytes within the chosen deadline | Not equivalent to EOF or malformed payload |
| UDP receive timeout | No datagram observed | No proof of open/closed port or valid message |

If the user supplies a complete solver and a current endpoint, run that artifact before re-deriving it. If an instance expired, retry unchanged against the refreshed endpoint before changing the protocol assumptions.

## 2. TCP is a byte stream

One `sendall()` can arrive in several reads. Several sends can arrive in one read. Do not assume `recv(1024)` returns a whole message.

Common framing:

| Protocol shape | Correct receive strategy |
| --- | --- |
| Newline-delimited text | Buffer until the exact line delimiter |
| Prompt ending `> ` | Buffer until those bytes; retain any surplus |
| Fixed-size header | Read exactly the header length, then parse |
| Length prefix | Parse length with correct width/endianness; read that many bytes |
| Connection-close body | Read until EOF; timeout is a separate state |
| Stateful binary protocol | Parse message ID/length/checksum according to the dialect |

Use `sendall`, bytes literals, explicit delimiters, and bounded reads. If the service expects CRLF, `b'\n'` alone may fail.

## 3. Minimal exact-length reader

```python
import time

def read_exact(sock, size, timeout=5):
    deadline = time.monotonic() + timeout
    data = bytearray()
    while len(data) < size:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError(f'{len(data)}/{size} bytes before deadline')
        sock.settimeout(remaining)
        part = sock.recv(size - len(data))
        if not part:
            raise EOFError(f'{len(data)}/{size} bytes before EOF')
        data.extend(part)
    return bytes(data)
```

A per-read timeout alone can allow a peer to keep you waiting indefinitely by sending one byte before each timeout. The absolute deadline bounds the entire operation.

For a 32-bit network-order length header:

```python
import struct
length, = struct.unpack('!I', read_exact(sock, 4))
if length > 8 * 1024 * 1024:
    raise ValueError('unexpected message size')
body = read_exact(sock, length)
```

Only use this layout when the protocol defines it. Little-endian is `<I`; network order is big-endian.

## 4. Reuse one connection for the whole protocol

Download [session_client.py](/snippets/network/session_client.py). It preserves delimiter over-read bytes and emits a byte-exact JSONL transcript.

Example `plan.json`:

```json
[
  {"read_until_hex": "3e20"},
  {"send_text": "STATUS\r\n"},
  {"read_until_hex": "3e20"},
  {"send_hex": "50494e470d0a"},
  {"read_for": 3}
]
```

```bash
python3 session_client.py 192.0.2.10 31337 plan.json \
  --timeout 5 --transcript session.jsonl
```

`3e20` is `> `; `50494e470d0a` is `PING\r\n`. These are illustrative commands, not a universal challenge protocol. Replace them with documented messages.

For binary payload files, use `{"send_file":"payload.bin"}`. Relative payload paths are resolved beside the plan file. No newline is added automatically.

## 5. ACK is an intermediate event

```text
read initial state
-> set required mode
-> authenticate / arm / enable if protocol requires it
-> send objective command
-> parse ACK
-> keep reading asynchronous telemetry / status
-> verify objective or final flag
```

Decode numeric command IDs before naming them. A transport ACK only confirms receipt; an application ACK may confirm acceptance but still precede a delayed state transition.

Keep required heartbeats/tunnel processes running. The generic plan helper does not automatically synthesize heartbeat messages or interpret binary message IDs; use the actual protocol definition.

## 6. Analyze recorded TCP correctly

Wireshark **Follow TCP Stream** handles sequencing more appropriately than concatenating `tcp.payload` in frame order. Retransmissions and overlapping segments can otherwise duplicate bytes; out-of-order arrival can scramble them.

```text
tcp.stream eq 7
tcp.analysis.retransmission
tcp.analysis.out_of_order
tcp.analysis.lost_segment
```

A followed stream can still be incomplete. Check capture truncation and gaps. Separate client and server directions before treating bytes as a file.

## 7. UDP preserves datagrams, not reliability

```python
import socket
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
    sock.settimeout(3)
    sock.sendto(bytes.fromhex('01020304'), ('192.0.2.10', 20000))
    try:
        payload, sender = sock.recvfrom(65535)
        print(sender, payload.hex())
    except socket.timeout:
        print('no datagram within 3 seconds')
```

Use the service's expected local binding and transaction ID where required. The first datagram received may be unsolicited or belong to a different request. UDP can lose, duplicate, and reorder messages; match source, sequence, and protocol state.

## Final check

Record exact transmitted bytes, response bytes, connection lifetime, timeout/EOF distinction, and the service's final outcome. Do not reopen a new connection in the middle of a protocol unless the specification says sessions are stateless.

Reference: [Python socket documentation](https://docs.python.org/3/library/socket.html) for send/receive and timeout semantics.
