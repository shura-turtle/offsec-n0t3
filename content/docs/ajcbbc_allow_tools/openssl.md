---
title: "OpenSSL"
weight: 24
bookToc: true
---

**Use for:** Base64, hashes, certificate/key inspection and known-parameter decryption.  
**Run in:** WSL; listed as OpenSSL 3.x.

## Decode or hash a file

```bash
openssl version
openssl base64 -d -in encoded.txt -out decoded.bin
openssl base64 -d -A -in single_line_base64.txt -out decoded.bin
openssl dgst -sha256 challenge.bin
```

`-A` is useful for Base64 supplied as one unwrapped line.

## Inspect keys and certificates

```bash
# Certificate subject, issuer and validity dates
openssl x509 -in certificate.pem -noout -subject -issuer -dates

# All certificate fields
openssl x509 -in certificate.pem -noout -text

# Public/private key parameters
openssl pkey -pubin -in public.pem -text -noout
openssl pkey -in private.pem -text -noout

# ASN.1 structure
openssl asn1parse -in certificate.pem
```

Add `-inform DER` for binary DER input where the command supports it.

## CTF: decrypt AES with raw key and IV

```bash
# Example AES-128-CBC values; replace with challenge parameters
openssl enc -d -aes-128-cbc -in ciphertext.bin -out plaintext.bin \
  -K 00112233445566778899aabbccddeeff \
  -iv 000102030405060708090a0b0c0d0e0f
```

`-K` and `-iv` accept hex bytes. Password derived encryption uses different parameters:

```bash
# Prompts for a password; only correct if encryption used these parameters
openssl enc -d -aes-256-cbc -pbkdf2 -iter 10000 \
  -in encrypted.bin -out plaintext.bin
```

## Gotchas

- Match mode, padding, salt, digest and KDF exactly.
- `bad decrypt` can indicate several parameter mismatches.
- `enc` does not support AEAD modes such as GCM.

## Flags explained by OpenSSL subcommand

| Flag / context | Meaning |
| --- | --- |
| `-in FILE`, `-out FILE` | Read/write the selected file |
| `base64 -d` / `enc -d` | Decode Base64 / decrypt encrypted data |
| `base64 -A` | Process Base64 without the normal newline wrapping assumptions |
| `enc -aes-128-cbc` | Choose AES-128 in CBC mode |
| `enc -K HEX` | Supply raw encryption-key bytes as hex |
| `enc -iv HEX` | Supply IV bytes as hex |
| `enc -pbkdf2 -iter N` | Derive key/IV using PBKDF2 with N iterations |
| `-pubin` | Interpret the key input as public rather than private |
| `-inform DER`, `-outform DER` | Select binary DER input/output representation |
| `-text` | Print decoded structure/details |
| `-noout` | Suppress the usual encoded object output |
| `x509 -subject -issuer -dates` | Display certificate identity and validity fields |
| `rsa -modulus` | Print the RSA modulus |
| `pkeyutl -decrypt -inkey FILE` | Decrypt with the chosen private key |
| `-pkeyopt NAME:VALUE` | Set an algorithm/padding-specific parameter |
| `s_client -connect HOST:PORT` | Connect to a TLS service |
| `s_client -servername NAME` | Send the TLS SNI hostname |
| `s_client -showcerts` | Print the certificate chain sent by the peer |
| `s_client -CAfile FILE` | Load trusted CA certificates for verification |
| `asn1parse -i` | Indent ASN.1 structure by nesting depth |
| `dgst -sha256` | Select SHA-256 hashing |
| `dgst -verify KEY -signature FILE` | Verify the supplied signature using that key |

Read each flag with its subcommand. OpenSSL is a collection of commands and the meaning/availability of options is not global.

## CTF: inspect RSA modulus and exponent

```bash
openssl rsa -pubin -in public.pem -text -noout
openssl rsa -pubin -in public.pem -modulus -noout
```

Use the modulus/exponent to choose a weak-RSA technique. A key printed successfully only confirms parsing, not weakness.

## CTF: RSA decrypt with a recovered private key

```bash
# OAEP example: this digest must match how the challenge encrypted
openssl pkeyutl -decrypt -inkey recovered_private.pem \
  -in ciphertext.bin -out plaintext.bin \
  -pkeyopt rsa_padding_mode:oaep -pkeyopt rsa_oaep_md:sha256

# PKCS#1 v1.5 encryption padding, when explicitly required
openssl pkeyutl -decrypt -inkey recovered_private.pem \
  -in ciphertext.bin -out plaintext.bin -pkeyopt rsa_padding_mode:pkcs1
```

Different padding modes are not interchangeable. For textbook RSA, Python integer modular exponentiation is often easier to inspect and verify.

## CTF: connect to a TLS challenge service

```bash
# Inspect the handshake and presented certificates
openssl s_client -connect 192.0.2.10:443 -servername challenge.example -showcerts
```

SNI (`-servername`) can determine which virtual host/certificate you receive. This does not automatically make certificate verification succeed. For a challenge with a supplied CA, pass `-CAfile challenge_ca.pem` as appropriate.

## Convert formats before another tool parses them

```bash
# DER certificate → PEM
openssl x509 -inform DER -in cert.der -out cert.pem

# PEM public key → DER
openssl pkey -pubin -in public.pem -outform DER -out public.der
```

## Inspect ASN.1 and certificate extensions

```bash
openssl asn1parse -inform DER -in blob.der -i
openssl x509 -in cert.pem -noout -text > certificate_details.txt
```

Look for alternate names, custom extensions and unexpected strings. ASN.1 offsets describe the parsed input; do not assume they are offsets in another file/container.

## Verify a supplied signature

```bash
# For a signature created using a matching SHA-256 signing scheme
openssl dgst -sha256 -verify public.pem \
  -signature signature.bin message.bin
```

The digest and signing scheme must match. A failed verification can mean changed message bytes, a wrong key, or wrong scheme parameters.

## Troubleshoot raw AES parameters

| Problem | Inspect |
| --- | --- |
| Key too short / padded with zeroes | Count decoded key bytes; choose the right AES size |
| First block wrong, later blocks plausible in CBC | Check IV |
| Every block wrong | Check key, mode and input decoding |
| Last block/padding error | Check truncation, padding and all parameters |
| `Salted__` prefix | Determine OpenSSL password derivation parameters |
| Algorithm unavailable | OpenSSL 3 provider configuration and build support |

References: [enc](https://docs.openssl.org/3.0/man1/openssl-enc/), [pkeyutl](https://docs.openssl.org/3.0/man1/openssl-pkeyutl/), [s_client](https://docs.openssl.org/3.0/man1/openssl-s_client/), [x509](https://docs.openssl.org/3.0/man1/openssl-x509/).
