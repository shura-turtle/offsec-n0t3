---
title: "04 · TLS / SSH"
weight: 4
bookToc: true
---

# TLS and SSH: Metadata Before Decryption

**Flow:** identify the session → inspect visible handshake → locate matching secrets → configure the correct decoder → verify plaintext.

**Tools:** [Wireshark](../../ajcbbc_allow_tools/wireshark/), [OpenSSL](../../ajcbbc_allow_tools/openssl/), [OpenSSH key recovery](../../ajcbbc_allow_tools/openssh_session_key_recovery/), [Volatility](../../ajcbbc_allow_tools/volatility3/).

## 1. What is actually visible?

```text
tls.handshake
tls.handshake.type == 1
tls.handshake.extensions_server_name
ssh
```

A ClientHello can reveal supported versions, cipher suites, and server name when not hidden by encrypted ClientHello. TLS 1.3 encrypts handshake messages after ServerHello, including the certificate. Do not assume a capture always exposes the certificate.

SSH identification strings and key-exchange negotiation precede encryption, but ordinary credentials and shell commands are encrypted.

| Evidence | You can usually determine |
| --- | --- |
| IP/port and packet sizes | Peers, timing, approximate transfer size |
| Visible TLS ClientHello | Offered protocol settings, possibly SNI |
| Certificate when available | Names, issuer, public key, validity |
| SSH identification | Claimed implementation/version |
| Matching session secrets | Potential traffic decryption, subject to decoder/session support |

A hostname or certificate name can be the next lead even without plaintext.

## 2. Inspect a supplied certificate offline

```bash
openssl x509 -in certificate.pem -noout -subject -issuer -dates
openssl x509 -in certificate.pem -noout -text
openssl x509 -inform DER -in certificate.der -out certificate.pem
```

Check Subject Alternative Names, unusual extension data, validity times, serial number, and public-key details. A certificate public key does not provide the server's private key.

If the challenge explicitly gives a live TLS endpoint, OpenSSL can inspect its presented certificate:

```bash
openssl s_client -connect 192.0.2.10:443 \
  -servername challenge.example -showcerts
```

Use the challenge hostname for SNI. A certificate verification failure and an inability to establish TCP are different outcomes.

## 3. Decide whether the key material is usable

| Material provided | Typical implication |
| --- | --- |
| TLS key log matching the session | Configure Wireshark TLS secrets file |
| RSA private key | May help older RSA key-exchange sessions; not modern ephemeral DH/ECDH |
| TLS certificate alone | Metadata, no general traffic decryption |
| Browser profile or memory | Search for key logs / relevant session secrets using supplied artifacts |
| SSH login private key | Authentication credential; generally not a passive session-decryption key |
| SSH process memory and matching PCAP | Investigate supported session-key recovery workflow |

Forward secrecy means possession of a long-term key does not automatically recover past session traffic. Match the negotiated cipher/key exchange and supplied evidence.

## 4. Configure a TLS secrets file

In Wireshark:

```text
Edit -> Preferences -> Protocols -> TLS
(Pre)-Master-Secret log filename -> supplied sslkeys.log
Apply -> inspect the matching stream
```

TShark example:

```bash
tshark -r encrypted.pcapng -o tls.keylog_file:sslkeys.log \
  -Y 'http || http2'
```

A key-log filename setting is not proof decryption succeeded. Verify that application protocol fields appear and that the resulting plaintext is coherent. For HTTP objects, continue with [HTTP extraction](../http-streams/).

Common blockers:

- Secrets belong to a different connection or process.
- Capture lacks key handshake records or application bytes.
- Wrong path, unreadable file, malformed key-log lines.
- Protocol/dissector version lacks needed support.
- An outer tunnel or another encrypted layer remains.

## 5. SSH is a different key schedule

A TLS key-log setting does not decrypt SSH. Inspect the [approved SSH recovery plugin](../../ajcbbc_allow_tools/openssh_session_key_recovery/) before choosing commands.

Its workflow needs the relevant Linux memory, supported OpenSSH structures, correct symbols/plugin installation, and matching connection evidence. The recovered cipher, keys, IVs, and process/session context must be interpreted with the right traffic direction and SSH framing.

A recovery plugin reporting candidate keys does not itself prove the PCAP has been decrypted. Confirm a coherent packet/message stream using the supplied supported workflow.

## 6. Use metadata when secrets are absent

```text
DNS query -> server IP -> TLS SNI -> downloaded filename in another flow
memory process -> remote address -> matching SSH conversation
certificate name -> HTTP Host in earlier plaintext redirect
```

Correlate timestamps carefully: wall-clock timezone, relative capture time, and memory acquisition time can differ. Preserve the original value alongside any conversion.

## 7. Avoid common false conclusions

- High-entropy bytes do not identify AES or any particular cipher.
- A successful `openssl x509` parse does not establish trust or key ownership.
- An expired certificate may still appear in a valid historical capture.
- Base64 is not decryption.
- `SSLKEYLOGFILE` must have been honored by the generating application; setting it after a capture does not recover old secrets.
- A TLS alert can explain an application failure before HTTP is ever sent.

## Completion checkpoint

Record the connection, secret source, negotiated protocol, configuration, and a small verified plaintext excerpt. Save recovered files separately from secrets. If decryption is impossible with the supplied material, use the visible metadata to find another evidence path.

References: [Wireshark TLS guidance](https://wiki.wireshark.org/TLS), [OpenSSL s_client](https://docs.openssl.org/3.0/man1/openssl-s_client/), [TLS 1.3 RFC](https://www.rfc-editor.org/rfc/rfc8446).
