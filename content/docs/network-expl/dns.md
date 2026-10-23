---
title: "03 · DNS / Encoded Labels"
weight: 3
bookToc: true
---

# DNS Analysis and Data Reconstruction

**Flow:** queries and answers → suspicious suffix → direction → sequence/retries → encoding → exact bytes.

**Tools:** [Wireshark](../../ajcbbc_allow_tools/wireshark/), [TShark](../../ajcbbc_allow_tools/tshark/), [CyberChef](../../ajcbbc_allow_tools/cyberchef/), [Python](../../ajcbbc_allow_tools/python3/).

## 1. Inventory names, types, and answers

```text
dns
dns.flags.response == 0
dns.flags.response == 1
dns.qry.type == 16
dns.qry.name contains "exfil.example"
```

Type 16 is TXT. Also inspect A, AAAA, CNAME, and unusual label lengths. DNS can carry data in query names or answer records.

```bash
tshark -r traffic.pcapng -Y 'dns' -T fields \
  -E header=y -E separator=/t \
  -e frame.number -e ip.src -e ip.dst -e dns.id \
  -e dns.flags.response -e dns.qry.name -e dns.qry.type \
  -e dns.a -e dns.aaaa -e dns.cname -e dns.txt > dns.tsv
```

Inspect repeated field values before parsing an export as one-record-per-line. One DNS message can contain multiple questions/answers; the simple reconstruction helper assumes one relevant query name per exported line.

## 2. Decide whether the content is suspicious

| Observation | Plausible explanation | Distinguishing check |
| --- | --- | --- |
| Long, high-variation subdomains | Encoded data or tracking identifiers | Stable suffix, recoverable structure |
| Many identical names | Retries or cache behavior | Transaction IDs, timestamps, source ports |
| TXT answers with readable text | Challenge data or legitimate DNS metadata | Follow the matching question |
| Repeated NXDOMAIN | Missing names or exfiltration channel | Inspect labels, not just status |
| A records with patterned bytes | Encoded responses or ordinary address allocation | Interpret in protocol/source context |

Do not infer a tunnel from entropy alone. CDN labels, anti-abuse tokens, and telemetry can be long and random.

## 3. Export only the relevant query direction

```bash
tshark -r traffic.pcapng \
  -Y 'dns.flags.response == 0 && dns.qry.name contains "exfil.example"' \
  -T fields -E separator=/t -E occurrence=f \
  -e frame.time_epoch -e dns.qry.name > queries.tsv
```

Inspect the suffix exactly. A `contains` filter can select unrelated names such as `notexfil.example.invalid`. The helper below checks whole suffix labels before accepting a chunk.

Do not use alphabetical sort on encoded names. It can destroy the transmission order.

## 4. Identify label layout

```text
0000.666c6167.exfil.example
0001.7b64656d6f7d.exfil.example
│    │        └─ fixed suffix
│    └────────── encoded payload
└─────────────── decimal sequence index
```

Join payload labels inside a query only when the protocol/source indicates they belong together. A client identifier or checksum label is not necessarily payload.

Check whether sequence numbers are decimal, hexadecimal, fixed-width text, or part of the encoded stream. The supplied helper's `--sequence` mode handles **decimal first labels only**.

## 5. Handle retries and missing chunks

- Same sequence number and same payload: one chunk with a retry.
- Same sequence number and different payload: conflict; investigate before decoding.
- Missing sequence number: incomplete result; do not silently concatenate across the gap.
- No sequence number: preserve capture order and retain repeated payloads unless retries are independently identified.
- A reset sequence counter can indicate a new transfer. Split sessions before reconstruction.

DNS names are case-insensitive semantically; an encoding relying on case-sensitive Base64 may be altered by DNS infrastructure. Preserve captured case, but prefer the encoding demonstrated by source or data, often hex or Base32.

## 6. Reconstruct using the offline helper

Download [dns_reconstruct.py](/snippets/network/dns_reconstruct.py).

```bash
python3 dns_reconstruct.py queries.tsv \
  --suffix exfil.example --sequence --start 0 \
  --encoding hex --out recovered.bin
```

The helper accepts a bare qname per line or TSV whose last field is the qname. It verifies suffix labels, orders decimal sequence IDs, rejects gaps/conflicts, and suppresses identical retransmitted sequence entries.

For one continuous Base32 stream split over queries:

```bash
python3 dns_reconstruct.py queries.tsv \
  --suffix exfil.example --sequence --encoding base32 --out recovered.bin
```

When each query is independently encoded, decode each chunk first:

```bash
python3 dns_reconstruct.py queries.tsv \
  --suffix exfil.example --sequence --encoding base64url \
  --per-chunk --out recovered.bin
```

Decoding individually versus after joining is significant: padding and partial encoding blocks can change the result. Follow the producer's encoding order.

## 7. Validate output bytes

```python
from pathlib import Path
import hashlib
blob = Path('recovered.bin').read_bytes()
print(len(blob), hashlib.sha256(blob).hexdigest(), blob[:32].hex())
```

Open with HxD or the appropriate file tool. If the result is another encoding layer, decode that layer explicitly. Do not discard undecodable characters with `errors='ignore'`.

## 8. Other DNS clues

- TXT data can have multiple character strings within one record; inspect the packet tree.
- CNAME chains can provide subdomains, file names, or a second channel.
- EDNS data is different from ordinary DNS labels.
- DNS over HTTPS/TLS hides ordinary DNS fields unless the transport can be decrypted.
- A UDP DNS response may be truncated and retried over TCP.

**Next:** [HTTP](../http-streams/) for DNS-over-HTTP application bodies or [TLS](../tls-ssh/) for encrypted channels.

References: [RFC 1035](https://www.rfc-editor.org/rfc/rfc1035) for DNS structure and [RFC 4648](https://www.rfc-editor.org/rfc/rfc4648) for Base encodings.
