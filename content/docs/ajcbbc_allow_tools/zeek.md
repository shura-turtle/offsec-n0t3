---
title: "Zeek"
weight: 18
bookToc: true
---

**Use for:** turning PCAP traffic into connection, DNS, HTTP and TLS logs.  
**Run in:** WSL.

## Generate logs from a capture

```bash
# Logs are written into the current directory
mkdir -p zeek_out
cd zeek_out
zeek -r ../traffic.pcap
ls -lh
```

If checksum offloading prevents useful analysis, retry in a fresh output folder with `zeek -C -r ../traffic.pcap`. `-C` ignores checksum validation.

## Pick the useful log

| File | CTF use |
| --- | --- |
| `conn.log` | Who talked to whom, ports, timing and byte counts |
| `dns.log` | Queried domains and answers |
| `http.log` | Hosts, URIs, methods and status codes |
| `ssl.log` | TLS handshake metadata, when observed |
| `files.log` | Files observed by analyzers; not automatic file extraction |
| `weird.log` | Protocol anomalies |

## Extract columns from default TSV logs

```bash
zeek-cut id.orig_h id.resp_h service < conn.log
zeek-cut query answers < dns.log
zeek-cut host uri < http.log
```

## Generate JSON logs for jq

```bash
# Run separately from the TSV example
mkdir -p ../zeek_json
cd ../zeek_json
zeek -r ../traffic.pcap LogAscii::use_json=T
jq -r '[.host, .uri] | @tsv' http.log
```

## Gotchas

- Only observed protocols generate their associated logs.
- TLS application content remains encrypted without appropriate decryption elsewhere.
- Reuse the Zeek connection `uid` to correlate records across logs.

## Flags and log settings

| Syntax | Meaning |
| --- | --- |
| `-r FILE` | Read offline traffic from a PCAP |
| `-i INTERFACE` | Capture live traffic; appropriate privileges required |
| `-C` | Ignore checksum validation |
| `LogAscii::use_json=T` | Write JSON records instead of normal TSV logs |
| `zeek-cut FIELD...` | Select named columns from Zeek TSV logs |

`-r` reads an input capture; generated logs are written in your current working directory. Use a fresh directory for every run.

## CTF: correlate an HTTP request with its connection

```bash
# Default TSV logs: retain the uid that joins protocol records
zeek-cut uid id.orig_h id.resp_h service < conn.log > connections.tsv
zeek-cut uid host uri status_code < http.log > requests.tsv
grep 'REPLACE_WITH_UID' connections.tsv requests.tsv
```

The same connection UID connects an HTTP record to its transport metadata. A host or IP can appear in many unrelated sessions.

## CTF: identify unusual DNS labels in JSON output

```bash
# Sort domain observations by query length
jq -s 'sort_by(.query | length) | reverse | .[:20] |
  .[] | {ts, query, answers}' dns.log
```

Long names are candidates, not proof of tunneling. Check the suffix, encoding alphabet, sequence structure and repetition in the original capture.

## CTF: find large outgoing connections

```bash
# JSON output; missing byte counts are treated as zero
jq -s 'sort_by(.orig_bytes // 0) | reverse | .[:10] |
  .[] | {uid, orig: .["id.orig_h"], resp: .["id.resp_h"],
         orig_bytes, resp_bytes, service}' conn.log
```

Zeek JSON uses dotted keys such as `id.orig_h`; jq must address these with bracket access such as `.["id.orig_h"]`, as shown above. `.id.orig_h` instead looks for nested objects.

## CTF: search observed file metadata

```bash
jq -c '{fuid, mime_type, filename, seen_bytes, total_bytes}' files.log
```

A `files.log` entry records analyzer observations. Missing filename/length fields are normal for some protocols. Recovery still requires the original capture or a separately configured extraction policy.

## Interpret connection state carefully

Large byte counts, uncommon services and brief connections help prioritize. Combine direction, endpoints, time window and application evidence. Do not label a transfer as exfiltration from volume alone.

References: [Zeek quick start](https://docs.zeek.org/en/current/quickstart.html), [log reference](https://docs.zeek.org/en/current/reference/logs/index.html).
