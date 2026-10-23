---
title: "08 · FTP / Mail / ICMP / SMB"
weight: 8
bookToc: true
---

# Other Protocols: Find the Data Channel

**Flow:** identify protocol → match control to data → reconstruct the correct direction → decode protocol content → verify the artifact.

**Tools:** [Wireshark](../../ajcbbc_allow_tools/wireshark/), [TShark](../../ajcbbc_allow_tools/tshark/), [Zeek](../../ajcbbc_allow_tools/zeek/), [Python](../../ajcbbc_allow_tools/python3/), [CyberChef](../../ajcbbc_allow_tools/cyberchef/), [xxd](../../ajcbbc_allow_tools/xxd/).

## 1. FTP: control and file data are separate

```text
ftp
ftp-data
ftp.request.command == "USER"
ftp.request.command == "PASS"
ftp.request.command == "RETR"
ftp.request.command == "STOR"
```

1. Follow the control stream and inspect login/status codes.
2. Record the requested file and transfer direction.
3. Inspect `PORT` / `EPRT` or `PASV` / `EPSV` setup.
4. Identify the corresponding data connection.
5. Save the data-channel direction containing the file, then inspect its bytes.

A directory listing is not a downloaded archive. The first FTP stream may contain credentials while a later connection carries the actual artifact.

```text
227 Entering Passive Mode (192,0,2,20,195,80)
```

For this classic PASV example, data port = `195*256 + 80 = 50000`. An advertised private/NAT address may differ from the actual flow; correlate packet endpoints.

FTP plaintext passwords are visible only if login is not protected by TLS. SFTP is an SSH subsystem, a different protocol; it is not parsed as ordinary FTP data.

## 2. SMTP: reconstruct the message

```text
smtp
smtp.req.command == "AUTH"
smtp.req.command == "DATA"
```

Follow the relevant stream. Find envelope addresses, `DATA`, message headers, MIME boundaries, attachments, and transfer encodings. A `250` after a command indicates an SMTP response, not necessarily the challenge objective.

`AUTH LOGIN` / `AUTH PLAIN` values may be Base64-encoded. `AUTH PLAIN` has NUL-separated fields; decoding to text with ignored errors can conceal them. Inspect bytes in CyberChef/HxD.

For an extracted `.eml` message, Python's standard library can decode MIME parts:

```python
from email import policy
from email.parser import BytesParser
from pathlib import Path

message = BytesParser(policy=policy.default).parsebytes(Path('mail.eml').read_bytes())
output = Path('mail-parts')
output.mkdir(exist_ok=True)
for index, part in enumerate(message.walk()):
    if part.is_multipart():
        continue
    payload = part.get_payload(decode=True)
    if payload is None:
        continue
    destination = output / f'part-{index:03d}.bin'
    destination.write_bytes(payload)
    print(destination, part.get_content_type(), repr(part.get_filename()))
```

The fixed generated filenames avoid trusting attachment names as filesystem paths. Determine file types from headers/magic, then inspect with the relevant approved tool.

If carving SMTP DATA manually, handle its terminator and dot-stuffing; network framing bytes are not part of the email message. Prefer a dissector/exporter when available.

## 3. POP and IMAP

```text
pop
imap
```

Look for message retrieval rather than only login. POP `RETR` responses can contain complete mail messages; IMAP literals have explicit byte counts and can span packets. Follow the stream and preserve exact literal bytes before using the MIME parser.

Ports are hints: POP/IMAP may use TLS from connection start or upgrade with a protocol command. If encrypted, continue to [TLS/SSH](../tls-ssh/).

## 4. ICMP / ping payloads

```text
icmp
icmp.type == 8
icmp.type == 0
icmpv6
```

Inspect one request/reply pair. Identify ICMP identifier, sequence, payload, and direction. Echo replies often repeat the request data; concatenating both directions duplicates the content.

```bash
tshark -r traffic.pcapng -Y 'icmp.type == 8 && data.data' \
  -T fields -E separator=/t \
  -e frame.number -e icmp.ident -e icmp.seq -e data.data > icmp.tsv
```

The `data.data` field appears when payload is left to the generic Data dissector. If empty, inspect the packet tree and choose the actual decoded payload field. Some ping tools place their own timestamp/pattern in the payload; remove bytes only when the sender format proves they are metadata.

Match retransmissions and sequence rollover. Preserve the raw export before decoding; a repeated payload chunk may be real content rather than a duplicate.

## 5. SMB: files and authentication are different evidence

```text
smb2
smb2.filename
ntlmssp
```

Inspect share paths, opened file names, read/write operations, file IDs, and response status. TCP streams can multiplex several SMB operations and files; a whole-stream raw save is not one clean file.

Where supported:

```text
File -> Export Objects -> SMB
```

TShark object export names vary by installed exporter. Discover them before selecting an exporter:

```bash
tshark --export-objects help
```

SMB signing does not itself encrypt file contents. SMB encryption can hide them. An NTLM challenge/response is not a plaintext password; do not label it as recovered credentials without the appropriate verification.

## 6. RDP, databases, and custom protocols

Use Protocol Hierarchy and **Decode As** only when bytes support the choice. Inspect negotiation, usernames, database names, result rows, or filenames when visible. Database protocols can carry their own authentication and TLS upgrades.

A binary field displaying readable ASCII is a useful lead, but avoid treating every printable run as a complete message. Validate framing and lengths.

## 7. UDP tunnels / unknown ports

Use **Follow UDP Stream** to inspect a candidate exchange, then examine each datagram boundary. Look for sequence, length, checksum, and message type. A custom protocol may require application reassembly even though UDP datagrams remain distinct.

Do not replay an arbitrary packet until you identify the service context and whether the message is stateless. [TCP/UDP sessions](../tcp-udp/) covers persistent protocol clients and outcome verification.

## Export checklist

| Check | Why |
| --- | --- |
| Correct direction | Requests can duplicate responses or contain control text |
| Correct channel | FTP control differs from FTP data |
| Reassembled bytes | Packet boundaries differ from protocol messages |
| Protocol framing removed | SMTP terminators / MIME boundaries / length prefixes |
| Missing bytes identified | A corrupt export may reflect a capture gap |
| Original references kept | Frame/stream evidence makes recovery reproducible |

References: [FTP RFC 959](https://www.rfc-editor.org/rfc/rfc959), [SMTP RFC 5321](https://www.rfc-editor.org/rfc/rfc5321), [Python email parser](https://docs.python.org/3/library/email.parser.html), [Wireshark guide](https://www.wireshark.org/docs/wsug_html_chunked/).
